"""
主画面状态识别。

首版优先固定 ROI + 颜色规则，模板匹配作为可选增强。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import numpy as np

from core.config import MainViewConfig, TemplateMatchConfig
from core.types import MainViewState, ROI

try:
    import cv2
except ImportError:  # pragma: no cover - 运行环境可选依赖
    cv2 = None


class MainViewReader:
    """读取主画面状态。"""

    def __init__(self, config: MainViewConfig) -> None:
        self.config = config
        self._stable_state = MainViewState.UNKNOWN
        self._candidate_state = MainViewState.UNKNOWN
        self._candidate_count = 0
        self._templates: Dict[str, Optional[np.ndarray]] = {
            "transition": self._load_template(config.transition_template),
            "clear": self._load_template(config.clear_template),
            "boss": self._load_template(config.boss_template),
            "finish": self._load_template(config.finish_template),
        }
        self.last_metrics: Dict[str, float] = {}

    def read(self, frame: np.ndarray) -> MainViewState:
        """返回当前主画面状态。"""
        raw_state = self._detect_raw_state(frame)
        if raw_state == self._candidate_state:
            self._candidate_count += 1
        else:
            self._candidate_state = raw_state
            self._candidate_count = 1

        if self._stable_state == MainViewState.UNKNOWN:
            self._stable_state = raw_state
        elif self._candidate_count >= max(1, self.config.stable_frames):
            self._stable_state = raw_state

        return self._stable_state

    def _detect_raw_state(self, frame: np.ndarray) -> MainViewState:
        finish_region = self._extract_roi(frame, self.config.finish_roi)
        transition_region = self._extract_roi(frame, self.config.transition_roi)
        boss_region = self._extract_roi(frame, self.config.boss_roi)
        clear_region = self._extract_roi(frame, self.config.clear_roi)

        finish_green = self._dominant_ratio(finish_region, 1)
        transition_dark = self._mean_intensity(transition_region)
        boss_red = self._dominant_ratio(boss_region, 2)
        clear_blue = self._dominant_ratio(clear_region, 0)

        self.last_metrics = {
            "finish_green_ratio": finish_green,
            "transition_mean_intensity": transition_dark,
            "boss_red_ratio": boss_red,
            "clear_blue_ratio": clear_blue,
        }

        if self._template_hit(finish_region, self.config.finish_template, "finish"):
            return MainViewState.RUN_FINISHED
        if finish_green >= self.config.finish_green_ratio_threshold and self._mean_intensity(finish_region) >= 80:
            return MainViewState.RUN_FINISHED

        if self._template_hit(transition_region, self.config.transition_template, "transition"):
            return MainViewState.TRANSITION
        if transition_dark <= self.config.transition_dark_threshold:
            return MainViewState.TRANSITION

        if self._template_hit(boss_region, self.config.boss_template, "boss"):
            return MainViewState.BOSS_ROOM
        if boss_red >= self.config.boss_red_ratio_threshold and self._mean_intensity(boss_region) >= 70:
            return MainViewState.BOSS_ROOM

        if self._template_hit(clear_region, self.config.clear_template, "clear"):
            return MainViewState.CLEAR_ROOM
        if clear_blue >= self.config.clear_blue_ratio_threshold and self._mean_intensity(clear_region) >= 70:
            return MainViewState.CLEAR_ROOM

        return MainViewState.COMBAT_ROOM

    @staticmethod
    def _extract_roi(frame: np.ndarray, roi: ROI) -> np.ndarray:
        h, w = frame.shape[:2]
        x1 = max(0, min(roi.x, w))
        y1 = max(0, min(roi.y, h))
        x2 = max(x1, min(roi.x2, w))
        y2 = max(y1, min(roi.y2, h))
        return frame[y1:y2, x1:x2]

    @staticmethod
    def _mean_intensity(region: np.ndarray) -> float:
        if region.size == 0:
            return 0.0
        return float(region.mean())

    @staticmethod
    def _dominant_ratio(region: np.ndarray, channel_index: int) -> float:
        if region.size == 0:
            return 0.0
        channel_means = region.mean(axis=(0, 1))
        total = float(channel_means.sum())
        if total <= 1e-6:
            return 0.0
        return float(channel_means[channel_index] / total)

    @staticmethod
    def _load_template(config: TemplateMatchConfig) -> Optional[np.ndarray]:
        if cv2 is None or not config.path:
            return None
        template_path = Path(config.path)
        if not template_path.exists():
            return None
        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        return template

    def _template_hit(
        self,
        region: np.ndarray,
        config: TemplateMatchConfig,
        template_name: str,
    ) -> bool:
        if cv2 is None or region.size == 0 or not config.path:
            return False

        template = self._templates.get(template_name)
        if template is None:
            return False

        if region.shape[0] < template.shape[0] or region.shape[1] < template.shape[1]:
            return False

        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        score = float(result.max()) if result.size else 0.0
        self.last_metrics[f"{template_name}_template_score"] = score
        return score >= config.threshold

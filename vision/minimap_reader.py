"""
小地图状态读取。

小地图只负责校验，不直接驱动动作。
"""

from __future__ import annotations

import time
from typing import Dict

import numpy as np

from core.config import MinimapConfig
from core.types import MinimapPathState, MinimapSpecialState, ROI


class MinimapReader:
    """读取小地图推进状态与特殊房间状态。"""

    def __init__(self, config: MinimapConfig) -> None:
        self.config = config
        self._stable_path_state = MinimapPathState.UNKNOWN
        self._candidate_path_state = MinimapPathState.UNKNOWN
        self._candidate_count = 0
        self._candidate_since = 0.0
        self.last_metrics: Dict[str, float] = {}

    def read(
        self,
        frame: np.ndarray,
        expected_room_index: int,
        is_last_normal_room: bool,
    ) -> tuple[MinimapPathState, MinimapSpecialState]:
        """读取当前小地图状态。"""
        del expected_room_index, is_last_normal_room  # 当前版本只保留接口，不直接参与判定

        neighbor_region = self._extract_roi(frame, self.config.neighbor_roi)
        special_region = self._extract_roi(frame, self.config.special_roi)

        mean_intensity = self._mean_intensity(neighbor_region)
        red_ratio = self._dominant_ratio(neighbor_region, 2)
        green_ratio = self._dominant_ratio(special_region, 1)

        self.last_metrics = {
            "neighbor_mean_intensity": mean_intensity,
            "neighbor_red_ratio": red_ratio,
            "special_green_ratio": green_ratio,
        }

        raw_state = self._detect_path_state(mean_intensity, red_ratio)
        stable_state = self._debounce(raw_state)
        special_state = (
            MinimapSpecialState.ABYSS_ROOM_PRESENT
            if green_ratio >= self.config.special_green_ratio_threshold
            else MinimapSpecialState.NONE
        )
        return stable_state, special_state

    def _detect_path_state(
        self,
        mean_intensity: float,
        red_ratio: float,
    ) -> MinimapPathState:
        if mean_intensity <= self.config.dark_threshold:
            return MinimapPathState.NEIGHBOR_DARK
        if red_ratio >= self.config.boss_red_ratio_threshold and mean_intensity >= 120:
            return MinimapPathState.BOSS_ONLY_READY
        if mean_intensity >= self.config.flash_brightness_threshold:
            return MinimapPathState.NEIGHBOR_FLASH_QMARK
        return MinimapPathState.NEIGHBOR_DARK

    def _debounce(self, raw_state: MinimapPathState) -> MinimapPathState:
        now = time.time()
        if raw_state == self._candidate_path_state:
            self._candidate_count += 1
        else:
            self._candidate_path_state = raw_state
            self._candidate_count = 1
            self._candidate_since = now

        if self._stable_path_state == MinimapPathState.UNKNOWN:
            self._stable_path_state = raw_state
            return raw_state

        if raw_state == self._stable_path_state:
            return self._stable_path_state

        elapsed_ms = (now - self._candidate_since) * 1000
        if (
            self._candidate_count >= max(1, self.config.stable_frames)
            or elapsed_ms >= self.config.pending_timeout_ms
        ):
            self._stable_path_state = raw_state
            return raw_state

        return MinimapPathState.CLEAR_PENDING

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

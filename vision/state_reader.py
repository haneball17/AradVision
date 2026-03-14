"""
UI 状态读取。

首版只实现固定 ROI 的 HP/MP、维护触发信号与药水可用性读取。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.config import UIRoisConfig
from core.types import PlayerState, ROI


@dataclass
class StateReadResult:
    """状态读取结果。"""
    player_state: PlayerState
    inventory_weight_ratio: float
    free_slots: int
    vendor_ui_open: bool
    potion_cd_ready: bool
    potion_stock_available: bool


class StateReader:
    """读取 HP/MP 等固定 UI 状态。"""

    def __init__(self, config: UIRoisConfig) -> None:
        self.config = config

    def read(self, frame: np.ndarray) -> StateReadResult:
        """读取当前 UI 状态。"""
        hp_bar = self._extract_roi(frame, self.config.hp_bar)
        mp_bar = self._extract_roi(frame, self.config.mp_bar)
        inventory_flag = self._extract_roi(frame, self.config.inventory_flag)
        weight_bar = self._extract_roi(frame, self.config.inventory_weight_bar)
        vendor_flag = self._extract_roi(frame, self.config.vendor_flag)
        potion_flag = self._extract_roi(frame, self.config.potion_flag)

        player_state = PlayerState(
            hp_percent=self._bar_fill_ratio(hp_bar, 2),
            mp_percent=self._bar_fill_ratio(mp_bar, 0),
            skill_cds={},
        )

        inventory_ui_open = self._dark_ratio(inventory_flag, 50) >= 0.50
        vendor_ui_open = (
            self._dominant_ratio(vendor_flag, 0) >= 0.35
            and self._mean_intensity(vendor_flag) >= 60
        )
        if inventory_ui_open or vendor_ui_open:
            inventory_weight_ratio = self._bar_fill_ratio(weight_bar, 2)
        else:
            inventory_weight_ratio = 0.0

        potion_bright_ratio = self._bright_ratio(potion_flag, 110)
        potion_signal = self._mean_intensity(potion_flag)

        return StateReadResult(
            player_state=player_state,
            inventory_weight_ratio=inventory_weight_ratio,
            free_slots=999,
            vendor_ui_open=vendor_ui_open,
            potion_cd_ready=potion_bright_ratio >= 0.30,
            potion_stock_available=potion_signal >= 45,
        )

    @staticmethod
    def _extract_roi(frame: np.ndarray, roi: ROI) -> np.ndarray:
        h, w = frame.shape[:2]
        x1 = max(0, min(roi.x, w))
        y1 = max(0, min(roi.y, h))
        x2 = max(x1, min(roi.x2, w))
        y2 = max(y1, min(roi.y2, h))
        return frame[y1:y2, x1:x2]

    def _bar_fill_ratio(self, region: np.ndarray, channel_index: int) -> float:
        if region.size == 0:
            return 1.0
        if region.ndim != 3 or region.shape[1] == 0:
            return 1.0

        columns = region.mean(axis=0)
        totals = columns.sum(axis=1)
        dominant = columns[:, channel_index]
        valid = totals > 1.0
        if not np.any(valid):
            return 1.0

        ratios = np.zeros_like(dominant, dtype=float)
        ratios[valid] = dominant[valid] / totals[valid]
        filled = ratios >= 0.45
        return float(filled.mean())

    def _brightness_fill_ratio(self, region: np.ndarray) -> float:
        if region.size == 0:
            return 0.0
        columns = region.mean(axis=0)
        brightness = columns.mean(axis=1)
        return float((brightness >= 40).mean())

    @staticmethod
    def _bright_ratio(region: np.ndarray, threshold: float) -> float:
        if region.size == 0:
            return 0.0
        gray = region.mean(axis=2)
        return float((gray >= threshold).mean())

    @staticmethod
    def _dark_ratio(region: np.ndarray, threshold: float) -> float:
        if region.size == 0:
            return 0.0
        gray = region.mean(axis=2)
        return float((gray < threshold).mean())

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

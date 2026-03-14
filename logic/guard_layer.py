"""
副本内守护层。
"""

from __future__ import annotations

import time

from core.config import ClassProfileConfig, GuardThresholdsConfig, KeyBindingsConfig
from core.types import GameContext, GuardAction, GuardDecision, MainViewState


class GuardLayer:
    """HP/MP 与药水守护层。"""

    def __init__(
        self,
        thresholds: GuardThresholdsConfig,
        class_profile: ClassProfileConfig,
        key_bindings: KeyBindingsConfig,
    ) -> None:
        self.thresholds = thresholds
        self.class_profile = class_profile
        self.key_bindings = key_bindings
        self._last_action_at = 0.0

    def evaluate(self, context: GameContext) -> GuardDecision:
        """基于当前上下文输出守护层决策。"""
        now = time.time()
        if context.main_view_state == MainViewState.TRANSITION:
            return GuardDecision(action=GuardAction.NONE, pause_room_logic=False, reason="transition")

        cooldown_ready = (now - self._last_action_at) * 1000 >= self.thresholds.potion_cooldown_ms
        if not cooldown_ready or not context.potion_cd_ready:
            return GuardDecision(action=GuardAction.NONE, pause_room_logic=False, reason="cooldown")

        hp_ratio = context.player_state.hp_percent
        mp_ratio = context.player_state.mp_percent

        if hp_ratio < self.thresholds.hp_critical_threshold:
            if not context.potion_stock_available:
                return GuardDecision(
                    action=GuardAction.ABORT_RUN,
                    pause_room_logic=True,
                    reason="hp_critical_without_potion",
                )
            return self._use_hp_potion(reason="hp_critical")

        if hp_ratio < self.thresholds.hp_low_threshold and context.potion_stock_available:
            return self._use_hp_potion(reason="hp_low")

        if (
            self.class_profile.requires_mp
            and mp_ratio < self.thresholds.mp_low_threshold
            and context.potion_stock_available
        ):
            return self._use_mp_potion(reason="mp_low")

        return GuardDecision(action=GuardAction.NONE, pause_room_logic=False, reason="stable")

    def _use_hp_potion(self, reason: str) -> GuardDecision:
        self._last_action_at = time.time()
        return GuardDecision(
            action=GuardAction.USE_HP_POTION,
            pause_room_logic=True,
            key_code=self.key_bindings.potion_1,
            reason=reason,
        )

    def _use_mp_potion(self, reason: str) -> GuardDecision:
        self._last_action_at = time.time()
        return GuardDecision(
            action=GuardAction.USE_MP_POTION,
            pause_room_logic=True,
            key_code=self.key_bindings.potion_2,
            reason=reason,
        )

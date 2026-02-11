"""
有限状态机（FSM）实现。

职责：
1. 根据 GameContext 进行状态转换；
2. 委派 CombatLogic 处理战斗细节；
3. 输出统一 Command 给输入层执行。
"""

from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Dict, List, Optional

from core.types import Command, CommandType, GameContext, GameObject
from logic.combat import CombatLogic


class BotState(Enum):
    """机器人状态枚举。"""

    IDLE = 0
    COMBAT = 1
    LOOT = 2
    NAVIGATE = 3
    RECOVERY = 4


class BotFSM:
    """
    机器人有限状态机。

    线程安全说明：
    - 状态读写受 RLock 保护；
    - update() 可被多线程调用，但建议主循环单线程驱动。
    """

    def __init__(
        self,
        y_align_tolerance: int = 15,
        attack_range_x: int = 120,
        hp_potion_threshold: float = 0.3,
        pickup_key: str = "z",
        potion_key: str = "1",
    ) -> None:
        self._lock = threading.RLock()
        self._state: BotState = BotState.IDLE
        self._state_entered_at = time.time()
        self._state_history: List[BotState] = [self._state]
        self._durations: Dict[BotState, float] = {state: 0.0 for state in BotState}

        self.hp_potion_threshold = hp_potion_threshold
        self.pickup_key = pickup_key
        self.potion_key = potion_key

        self._combat_logic = CombatLogic(
            y_align_tolerance=y_align_tolerance,
            attack_range_x=attack_range_x,
        )

    @property
    def current_state(self) -> BotState:
        """返回当前状态。"""
        with self._lock:
            return self._state

    @property
    def state_history(self) -> List[BotState]:
        """返回状态历史（拷贝）。"""
        with self._lock:
            return self._state_history.copy()

    def update(self, ctx: GameContext) -> Command:
        """
        状态机主入口（每帧调用）。
        """
        with self._lock:
            # 优先处理低血恢复逻辑
            if ctx.player_state.hp_percent < self.hp_potion_threshold:
                self.transition_to(BotState.RECOVERY)
                return self._handle_recovery(ctx)

            self._transition_state(ctx)

            if self._state == BotState.COMBAT:
                return self._handle_combat(ctx)
            if self._state == BotState.LOOT:
                return self._handle_loot(ctx)
            if self._state == BotState.NAVIGATE:
                return self._handle_navigate(ctx)
            if self._state == BotState.RECOVERY:
                return self._handle_recovery(ctx)
            return self._handle_idle(ctx)

    def transition_to(self, new_state: BotState) -> None:
        """
        执行状态切换并累计停留时长。
        """
        with self._lock:
            if new_state == self._state:
                return

            now = time.time()
            self._durations[self._state] += now - self._state_entered_at
            self._state = new_state
            self._state_entered_at = now
            self._state_history.append(new_state)

    def get_state_durations(self) -> Dict[BotState, float]:
        """
        获取状态停留时长统计（秒）。
        """
        with self._lock:
            snapshot = self._durations.copy()
            snapshot[self._state] += time.time() - self._state_entered_at
            return snapshot

    def _transition_state(self, ctx: GameContext) -> None:
        """
        根据上下文进行状态流转。
        """
        if ctx.monsters:
            self.transition_to(BotState.COMBAT)
            return
        if ctx.items:
            self.transition_to(BotState.LOOT)
            return
        if ctx.room_cleared and ctx.doors:
            self.transition_to(BotState.NAVIGATE)
            return
        self.transition_to(BotState.IDLE)

    def _handle_idle(self, _ctx: GameContext) -> Command:
        """
        待机状态：无动作。
        """
        return Command(action_type=CommandType.STOP, metadata={"state": "idle"})

    def _handle_combat(self, ctx: GameContext) -> Command:
        """
        战斗状态：委托 CombatLogic。
        """
        if ctx.hero is None:
            return Command(action_type=CommandType.STOP, metadata={"state": "combat_no_hero"})
        return self._combat_logic.decide_action(
            hero=ctx.hero,
            monsters=ctx.monsters,
            skill_cds=ctx.player_state.skill_cds,
        )

    def _handle_loot(self, ctx: GameContext) -> Command:
        """
        拾取状态：先走到最近物品，再执行拾取。
        """
        if ctx.hero is None or not ctx.items:
            return Command(action_type=CommandType.STOP, metadata={"state": "loot_no_item"})

        target = self._select_nearest(ctx.hero, ctx.items)
        if target is None:
            return Command(action_type=CommandType.STOP, metadata={"state": "loot_no_target"})

        dx = target.foot_point[0] - ctx.hero.foot_point[0]
        dy = target.foot_point[1] - ctx.hero.foot_point[1]

        if abs(dy) > 10:
            return Command(
                action_type=CommandType.MOVE,
                direction=(0, 1) if dy > 0 else (0, -1),
                duration=0.08,
                metadata={"state": "loot", "phase": "y_align"},
            )

        if abs(dx) > 80:
            return Command(
                action_type=CommandType.MOVE,
                direction=(1, 0) if dx > 0 else (-1, 0),
                duration=0.08,
                metadata={"state": "loot", "phase": "x_approach"},
            )

        return Command(
            action_type=CommandType.PICKUP,
            key_code=self.pickup_key,
            metadata={"state": "loot", "phase": "pickup"},
        )

    def _handle_navigate(self, ctx: GameContext) -> Command:
        """
        导航状态：移动到最近门对象。
        """
        if ctx.hero is None or not ctx.doors:
            return Command(action_type=CommandType.STOP, metadata={"state": "navigate_no_door"})

        target = self._select_nearest(ctx.hero, ctx.doors)
        if target is None:
            return Command(action_type=CommandType.STOP, metadata={"state": "navigate_no_target"})

        dx = target.foot_point[0] - ctx.hero.foot_point[0]
        dy = target.foot_point[1] - ctx.hero.foot_point[1]

        if abs(dy) > 12:
            return Command(
                action_type=CommandType.MOVE,
                direction=(0, 1) if dy > 0 else (0, -1),
                duration=0.1,
                metadata={"state": "navigate", "phase": "y_align"},
            )

        if abs(dx) > 20:
            return Command(
                action_type=CommandType.MOVE,
                direction=(1, 0) if dx > 0 else (-1, 0),
                duration=0.12,
                metadata={"state": "navigate", "phase": "x_move"},
            )

        return Command(action_type=CommandType.STOP, metadata={"state": "navigate", "phase": "arrived"})

    def _handle_recovery(self, _ctx: GameContext) -> Command:
        """
        恢复状态：优先使用药水。
        """
        return Command(
            action_type=CommandType.SKILL,
            key_code=self.potion_key,
            metadata={"state": "recovery", "action": "potion"},
        )

    @staticmethod
    def _select_nearest(hero: GameObject, objects: List[GameObject]) -> Optional[GameObject]:
        """选择与 hero 距离最近的对象。"""
        if not objects:
            return None
        return min(objects, key=lambda obj: hero.distance_to(obj))

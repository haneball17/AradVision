"""
路径规划模块（简化版）。

当前阶段目标：
- 提供稳定、可测试的“先 Y 后 X”移动策略；
- 为后续复杂寻路（避障/A*）预留接口。
"""

from __future__ import annotations

from typing import Optional

from core.types import Command, CommandType, GameObject


class PathPlanner:
    """
    简化路径规划器。

    策略：
    1. 优先对齐 Y 轴（2.5D 命中机制要求）；
    2. 再逼近 X 轴；
    3. 足够接近后输出 STOP。
    """

    def __init__(
        self,
        y_align_tolerance: int = 12,
        x_reach_threshold: int = 20,
        move_duration: float = 0.1,
    ) -> None:
        if y_align_tolerance < 0:
            raise ValueError("y_align_tolerance 不能为负数")
        if x_reach_threshold < 0:
            raise ValueError("x_reach_threshold 不能为负数")
        if move_duration <= 0:
            raise ValueError("move_duration 必须大于 0")

        self.y_align_tolerance = y_align_tolerance
        self.x_reach_threshold = x_reach_threshold
        self.move_duration = move_duration

    def plan_to_target(self, hero: GameObject, target: GameObject) -> Command:
        """
        规划从 hero 到 target 的一步移动指令。
        """
        dx = target.foot_point[0] - hero.foot_point[0]
        dy = target.foot_point[1] - hero.foot_point[1]

        if abs(dy) > self.y_align_tolerance:
            return Command(
                action_type=CommandType.MOVE,
                direction=(0, 1) if dy > 0 else (0, -1),
                duration=self.move_duration,
                metadata={"phase": "y_align"},
            )

        if abs(dx) > self.x_reach_threshold:
            return Command(
                action_type=CommandType.MOVE,
                direction=(1, 0) if dx > 0 else (-1, 0),
                duration=self.move_duration,
                metadata={"phase": "x_move"},
            )

        return Command(action_type=CommandType.STOP, metadata={"phase": "arrived"})

    def plan_to_nearest(self, hero: GameObject, candidates: list[GameObject]) -> Command:
        """
        规划到最近候选目标的移动动作。
        """
        target = self._nearest(hero, candidates)
        if target is None:
            return Command(action_type=CommandType.STOP, metadata={"reason": "no_candidate"})
        return self.plan_to_target(hero, target)

    @staticmethod
    def _nearest(hero: GameObject, candidates: list[GameObject]) -> Optional[GameObject]:
        if not candidates:
            return None
        return min(candidates, key=lambda obj: hero.distance_to(obj))

"""
战斗逻辑模块。

职责：
1. 选择战斗目标（最近怪）；
2. 进行 2.5D 轴对齐（先 Y 后 X）；
3. 在可攻击距离内输出攻击/技能指令。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from core.types import Command, CommandType, GameObject


class CombatLogic:
    """
    无状态战斗决策器。

    说明：
    - 该类不持有跨帧状态，天然线程安全；
    - 所有阈值可通过初始化参数注入。
    """

    def __init__(
        self,
        y_align_tolerance: int = 15,
        attack_range_x: int = 120,
        move_duration: float = 0.1,
        attack_key: str = "x",
        skill_priority: Optional[List[str]] = None,
    ) -> None:
        if y_align_tolerance < 0:
            raise ValueError("y_align_tolerance 不能为负数")
        if attack_range_x < 0:
            raise ValueError("attack_range_x 不能为负数")
        if move_duration <= 0:
            raise ValueError("move_duration 必须大于 0")

        self.y_align_tolerance = y_align_tolerance
        self.attack_range_x = attack_range_x
        self.move_duration = move_duration
        self.attack_key = attack_key
        self.skill_priority = skill_priority if skill_priority is not None else ["a", "s"]

    def decide_action(
        self,
        hero: GameObject,
        monsters: List[GameObject],
        skill_cds: Optional[Dict[str, float]] = None,
    ) -> Command:
        """
        计算战斗动作。

        流程：
        1. 选最近怪；
        2. Y 轴未对齐则上下移动；
        3. Y 对齐后若 X 距离过大则左右逼近；
        4. 进入攻击距离后优先放可用技能，否则普攻。
        """
        if not monsters:
            return Command(action_type=CommandType.STOP, metadata={"reason": "no_monster"})

        target = self.select_target(hero, monsters)
        if target is None:
            return Command(action_type=CommandType.STOP, metadata={"reason": "no_target"})

        dx = target.foot_point[0] - hero.foot_point[0]
        dy = target.foot_point[1] - hero.foot_point[1]

        # 1) 优先 Y 轴对齐
        if abs(dy) > self.y_align_tolerance:
            direction = (0, 1) if dy > 0 else (0, -1)
            return Command(
                action_type=CommandType.MOVE,
                direction=direction,
                duration=self.move_duration,
                metadata={"target_id": target.id, "phase": "y_align"},
            )

        # 2) Y 轴对齐后逼近 X 轴
        if abs(dx) > self.attack_range_x:
            direction = (1, 0) if dx > 0 else (-1, 0)
            return Command(
                action_type=CommandType.MOVE,
                direction=direction,
                duration=self.move_duration,
                metadata={"target_id": target.id, "phase": "x_approach"},
            )

        # 3) 进入攻击距离后优先技能
        skill_key = self._pick_available_skill(skill_cds or {})
        if skill_key is not None:
            return Command(
                action_type=CommandType.SKILL,
                key_code=skill_key,
                metadata={"target_id": target.id, "phase": "skill"},
            )

        return Command(
            action_type=CommandType.ATTACK,
            key_code=self.attack_key,
            metadata={"target_id": target.id, "phase": "attack"},
        )

    @staticmethod
    def select_target(hero: GameObject, monsters: List[GameObject]) -> Optional[GameObject]:
        """
        选择最近怪物作为目标。
        """
        if not monsters:
            return None
        return min(monsters, key=lambda m: hero.distance_to(m))

    def _pick_available_skill(self, skill_cds: Dict[str, float]) -> Optional[str]:
        """
        按优先级选择可释放技能（CD <= 0 视为可用）。
        """
        for skill in self.skill_priority:
            if skill_cds.get(skill, 0.0) <= 0:
                return skill
        return None

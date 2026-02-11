"""
CombatLogic 单元测试
"""

from core.types import BBox, CommandType, GameObject
from logic.combat import CombatLogic


def _build_object(obj_id: int, cls_name: str, x1: int, y1: int, x2: int, y2: int) -> GameObject:
    cls_id_map = {"monster": 0, "hero": 1, "item": 2, "gate": 3}
    return GameObject(
        id=obj_id,
        cls_id=cls_id_map.get(cls_name, 0),
        cls_name=cls_name,
        conf=0.9,
        bbox=BBox(x1=x1, y1=y1, x2=x2, y2=y2),
    )


def test_should_move_for_y_axis_align():
    """Y 轴未对齐时应先上下移动。"""
    logic = CombatLogic(y_align_tolerance=10, attack_range_x=120)
    hero = _build_object(1, "hero", 100, 100, 150, 180)
    monster = _build_object(2, "monster", 200, 300, 260, 380)

    cmd = logic.decide_action(hero, [monster], skill_cds={})
    assert cmd.action_type == CommandType.MOVE
    assert cmd.direction in [(0, 1), (0, -1)]
    assert cmd.metadata["phase"] == "y_align"


def test_should_move_for_x_axis_approach():
    """Y 轴已对齐且距离过远时应左右逼近。"""
    logic = CombatLogic(y_align_tolerance=20, attack_range_x=40)
    hero = _build_object(1, "hero", 100, 200, 150, 280)
    monster = _build_object(2, "monster", 500, 200, 560, 280)

    cmd = logic.decide_action(hero, [monster], skill_cds={})
    assert cmd.action_type == CommandType.MOVE
    assert cmd.direction == (1, 0)
    assert cmd.metadata["phase"] == "x_approach"


def test_should_use_skill_when_in_range_and_skill_ready():
    """进入攻击距离后优先使用可用技能。"""
    logic = CombatLogic(y_align_tolerance=20, attack_range_x=300, skill_priority=["a", "s"])
    hero = _build_object(1, "hero", 100, 200, 150, 280)
    monster = _build_object(2, "monster", 180, 200, 240, 280)

    cmd = logic.decide_action(hero, [monster], skill_cds={"a": 0.0, "s": 3.0})
    assert cmd.action_type == CommandType.SKILL
    assert cmd.key_code == "a"
    assert cmd.metadata["phase"] == "skill"


def test_should_fallback_to_attack_when_skill_on_cooldown():
    """技能不可用时应回退到普攻。"""
    logic = CombatLogic(y_align_tolerance=20, attack_range_x=300, attack_key="x")
    hero = _build_object(1, "hero", 100, 200, 150, 280)
    monster = _build_object(2, "monster", 180, 200, 240, 280)

    cmd = logic.decide_action(hero, [monster], skill_cds={"a": 2.0, "s": 1.0})
    assert cmd.action_type == CommandType.ATTACK
    assert cmd.key_code == "x"
    assert cmd.metadata["phase"] == "attack"


def test_select_target_should_choose_nearest_monster():
    """目标选择应返回最近怪物。"""
    logic = CombatLogic()
    hero = _build_object(1, "hero", 100, 100, 150, 180)
    near = _build_object(2, "monster", 160, 100, 210, 180)
    far = _build_object(3, "monster", 600, 100, 660, 180)

    target = logic.select_target(hero, [far, near])
    assert target is near

"""
PathPlanner 单元测试
"""

from core.types import BBox, CommandType, GameObject
from logic.path_planner import PathPlanner


def _obj(obj_id: int, cls_name: str, box: tuple[int, int, int, int]) -> GameObject:
    cls_id_map = {"monster": 0, "hero": 1, "item": 2, "gate": 3}
    return GameObject(
        id=obj_id,
        cls_id=cls_id_map.get(cls_name, 0),
        cls_name=cls_name,
        conf=0.9,
        bbox=BBox(*box),
    )


def test_plan_should_align_y_first():
    """Y 轴误差较大时应先上下移动。"""
    planner = PathPlanner(y_align_tolerance=10, x_reach_threshold=20)
    hero = _obj(1, "hero", (100, 100, 150, 180))
    target = _obj(2, "gate", (300, 260, 360, 340))

    cmd = planner.plan_to_target(hero, target)
    assert cmd.action_type == CommandType.MOVE
    assert cmd.direction in [(0, 1), (0, -1)]
    assert cmd.metadata["phase"] == "y_align"


def test_plan_should_move_x_after_y_aligned():
    """Y 轴对齐后应沿 X 轴移动。"""
    planner = PathPlanner(y_align_tolerance=20, x_reach_threshold=30)
    hero = _obj(1, "hero", (100, 200, 150, 280))
    target = _obj(2, "gate", (400, 200, 450, 280))

    cmd = planner.plan_to_target(hero, target)
    assert cmd.action_type == CommandType.MOVE
    assert cmd.direction == (1, 0)
    assert cmd.metadata["phase"] == "x_move"


def test_plan_should_stop_when_arrived():
    """到达阈值范围内时应返回 STOP。"""
    planner = PathPlanner(y_align_tolerance=20, x_reach_threshold=80)
    hero = _obj(1, "hero", (100, 200, 150, 280))
    target = _obj(2, "gate", (160, 200, 210, 280))

    cmd = planner.plan_to_target(hero, target)
    assert cmd.action_type == CommandType.STOP
    assert cmd.metadata["phase"] == "arrived"

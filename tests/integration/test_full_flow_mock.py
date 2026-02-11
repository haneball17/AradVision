"""
全 Mock 集成测试

链路：
MockYoloDetector -> GameContext -> BotFSM -> MockInputDriver
"""

import time

from core.types import GameContext, PlayerState
from input.mock_driver import MockInputDriver
from logic.bot_fsm import BotFSM
from vision.mock_detector import MockYoloDetector


def test_full_flow_with_mock_components(sample_frame):
    """验证全 Mock 场景下数据流可连通。"""
    detector = MockYoloDetector(mock_mode="fixed")
    fsm = BotFSM()
    driver = MockInputDriver()

    objects = detector.detect(sample_frame)
    hero = next((obj for obj in objects if obj.cls_name == "hero"), None)
    monsters = [obj for obj in objects if obj.cls_name == "monster"]
    items = [obj for obj in objects if obj.cls_name == "item"]
    doors = [obj for obj in objects if obj.cls_name == "gate"]

    ctx = GameContext(
        frame_index=1,
        timestamp=time.time(),
        hero=hero,
        monsters=monsters,
        items=items,
        doors=doors,
        player_state=PlayerState(hp_percent=1.0, mp_percent=1.0, skill_cds={"a": 0.0}),
        room_cleared=False,
    )

    cmd = fsm.update(ctx)
    ok = driver.execute(cmd)

    assert ok is True
    assert driver.get_command_count() == 1
    # 固定场景中英雄与怪物通常存在 Y 轴偏差，优先输出 MOVE
    assert cmd.action_type.value in {"move", "skill", "attack"}

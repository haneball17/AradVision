"""
BotFSM 单元测试
"""

import time

from core.types import BBox, CommandType, GameContext, GameObject, PlayerState
from logic.bot_fsm import BotFSM, BotState


def _obj(obj_id: int, cls_name: str, bbox: tuple[int, int, int, int]) -> GameObject:
    cls_id_map = {"monster": 0, "hero": 1, "item": 2, "gate": 3}
    return GameObject(
        id=obj_id,
        cls_id=cls_id_map.get(cls_name, 0),
        cls_name=cls_name,
        conf=0.9,
        bbox=BBox(*bbox),
    )


def _ctx(
    hero: GameObject | None,
    monsters: list[GameObject] | None = None,
    items: list[GameObject] | None = None,
    doors: list[GameObject] | None = None,
    hp_percent: float = 1.0,
    room_cleared: bool = False,
) -> GameContext:
    return GameContext(
        frame_index=1,
        timestamp=time.time(),
        hero=hero,
        monsters=monsters or [],
        items=items or [],
        doors=doors or [],
        player_state=PlayerState(hp_percent=hp_percent, mp_percent=1.0, skill_cds={"a": 0.0}),
        room_cleared=room_cleared,
    )


def test_should_enter_recovery_when_hp_low():
    """低血时应进入恢复状态并使用药水键。"""
    fsm = BotFSM(hp_potion_threshold=0.3, potion_key="1")
    hero = _obj(1, "hero", (100, 100, 150, 180))
    ctx = _ctx(hero=hero, hp_percent=0.2)

    cmd = fsm.update(ctx)
    assert fsm.current_state == BotState.RECOVERY
    assert cmd.action_type == CommandType.SKILL
    assert cmd.key_code == "1"


def test_should_enter_combat_when_monsters_exist():
    """存在怪物时应进入 COMBAT。"""
    fsm = BotFSM()
    hero = _obj(1, "hero", (100, 200, 150, 280))
    monster = _obj(2, "monster", (400, 200, 460, 280))
    ctx = _ctx(hero=hero, monsters=[monster])

    cmd = fsm.update(ctx)
    assert fsm.current_state == BotState.COMBAT
    assert cmd.action_type in (CommandType.MOVE, CommandType.SKILL, CommandType.ATTACK)


def test_should_enter_loot_when_items_exist_and_no_monster():
    """无怪有物品时应进入 LOOT。"""
    fsm = BotFSM(pickup_key="z")
    hero = _obj(1, "hero", (100, 200, 150, 280))
    item = _obj(2, "item", (160, 200, 190, 230))
    ctx = _ctx(hero=hero, items=[item])

    cmd = fsm.update(ctx)
    assert fsm.current_state == BotState.LOOT
    assert cmd.action_type in (CommandType.MOVE, CommandType.PICKUP)


def test_should_enter_navigate_when_room_cleared_and_doors_exist():
    """房间清空且存在门时应进入 NAVIGATE。"""
    fsm = BotFSM()
    hero = _obj(1, "hero", (100, 200, 150, 280))
    door = _obj(2, "gate", (600, 200, 650, 280))
    ctx = _ctx(hero=hero, doors=[door], room_cleared=True)

    cmd = fsm.update(ctx)
    assert fsm.current_state == BotState.NAVIGATE
    assert cmd.action_type in (CommandType.MOVE, CommandType.STOP)


def test_should_stay_idle_when_no_target():
    """无怪物无物品无门时应待机。"""
    fsm = BotFSM()
    hero = _obj(1, "hero", (100, 200, 150, 280))
    ctx = _ctx(hero=hero)

    cmd = fsm.update(ctx)
    assert fsm.current_state == BotState.IDLE
    assert cmd.action_type == CommandType.STOP


def test_get_state_durations_should_return_all_states():
    """状态时长统计应包含全部状态键。"""
    fsm = BotFSM()
    hero = _obj(1, "hero", (100, 200, 150, 280))
    fsm.update(_ctx(hero=hero))
    durations = fsm.get_state_durations()
    assert set(durations.keys()) == set(BotState)

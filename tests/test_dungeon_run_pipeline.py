"""固定路线 MVP 管线测试。"""

from __future__ import annotations

import time

import numpy as np
import pytest

from core.config import (
    AppConfig,
    ClassProfileConfig,
    DungeonRunConfig,
    GuardThresholdsConfig,
    MainViewConfig,
    MaintenanceConfig,
    MinimapConfig,
    RoomScriptConfig,
    UIRoisConfig,
)
from core.types import (
    GameContext,
    GuardAction,
    MainViewState,
    MaintenanceState,
    MinimapPathState,
    MinimapSpecialState,
    PlayerState,
    ROI,
)
from logic.fixed_route_pipeline import FixedRoutePipeline
from logic.guard_layer import GuardLayer
from logic.route_run_controller import RouteRunController
from vision.main_view_reader import MainViewReader
from vision.minimap_reader import MinimapReader


def _make_config() -> AppConfig:
    return AppConfig(
        dungeon_run=DungeonRunConfig(
            start_room_index=1,
            main_view=MainViewConfig(
                transition_roi=ROI(10, 10, 10, 10),
                clear_roi=ROI(30, 10, 10, 10),
                boss_roi=ROI(50, 10, 10, 10),
                finish_roi=ROI(70, 10, 10, 10),
                transition_dark_threshold=10.0,
                clear_blue_ratio_threshold=0.50,
                boss_red_ratio_threshold=0.50,
                finish_green_ratio_threshold=0.50,
                stable_frames=1,
            ),
            minimap=MinimapConfig(
                outer=ROI(0, 60, 50, 30),
                inner=ROI(0, 60, 50, 30),
                neighbor_roi=ROI(10, 70, 10, 10),
                special_roi=ROI(30, 70, 10, 10),
                resize_scale=1,
                dark_threshold=20.0,
                flash_brightness_threshold=220.0,
                boss_red_ratio_threshold=0.50,
                special_green_ratio_threshold=0.50,
                stable_frames=1,
                pending_timeout_ms=0,
            ),
            ui_rois=UIRoisConfig(
                hp_bar=ROI(10, 90, 20, 4),
                mp_bar=ROI(40, 90, 20, 4),
                inventory_weight_bar=ROI(70, 90, 20, 4),
                vendor_flag=ROI(85, 10, 10, 10),
                potion_flag=ROI(85, 25, 10, 10),
            ),
            guard_thresholds=GuardThresholdsConfig(
                hp_critical_threshold=0.25,
                hp_low_threshold=0.45,
                mp_low_threshold=0.2,
                potion_cooldown_ms=0,
            ),
            class_profile=ClassProfileConfig(
                name="test_class",
                requires_mp=True,
                primary_combat_skill=3,
                combat_interval_ms=0,
            ),
            maintenance=MaintenanceConfig(
                sell_dry_run=True,
                max_weight_ratio=0.85,
                min_free_slots=8,
                min_potion_stock=1,
            ),
            room_scripts=[
                RoomScriptConfig(
                    room_idx=1,
                    room_type="normal",
                    expected_exit_direction="RIGHT",
                    exit_action_template="move_right_hold_100",
                    transition_timeout_ms=100,
                    is_last_normal_room=True,
                ),
                RoomScriptConfig(
                    room_idx=2,
                    room_type="boss",
                    expected_exit_direction="STOP",
                    exit_action_template="none",
                    transition_timeout_ms=100,
                    next_step="stop_after_finish",
                ),
            ],
        ),
    )


def _base_frame() -> np.ndarray:
    frame = np.full((100, 100, 3), 120, dtype=np.uint8)
    frame[10:20, 10:20] = (50, 50, 50)   # transition ROI
    frame[10:20, 30:40] = (80, 80, 80)   # clear ROI
    frame[10:20, 50:60] = (80, 80, 80)   # boss ROI
    frame[10:20, 70:80] = (80, 80, 80)   # finish ROI
    frame[70:80, 10:20] = (0, 0, 0)      # minimap neighbor
    frame[70:80, 30:40] = (0, 0, 0)      # minimap special
    frame[90:94, 10:30] = (0, 0, 255)    # HP 满血
    frame[90:94, 40:60] = (255, 0, 0)    # MP 满蓝
    frame[90:94, 70:90] = (30, 30, 30)   # 背包重量低
    frame[25:35, 85:95] = (255, 255, 255)  # 药水可用
    return frame


def _frame_for(state: str) -> np.ndarray:
    frame = _base_frame()
    if state == "combat":
        return frame
    if state == "clear":
        frame[10:20, 30:40] = (255, 0, 0)
        return frame
    if state == "boss":
        frame[10:20, 50:60] = (0, 0, 255)
        return frame
    if state == "finish":
        frame[10:20, 70:80] = (0, 255, 0)
        return frame
    if state == "transition":
        frame[10:20, 10:20] = (0, 0, 0)
        return frame
    raise ValueError(state)


def _apply_minimap(frame: np.ndarray, state: str, special: bool = False) -> np.ndarray:
    updated = frame.copy()
    if state == "dark":
        updated[70:80, 10:20] = (0, 0, 0)
    elif state == "flash":
        updated[70:80, 10:20] = (255, 255, 255)
    elif state == "boss":
        updated[70:80, 10:20] = (120, 120, 255)
    else:
        raise ValueError(state)

    if special:
        updated[70:80, 30:40] = (0, 255, 0)
    return updated


def _apply_hp(frame: np.ndarray, hp_ratio: float) -> np.ndarray:
    updated = frame.copy()
    updated[90:94, 10:30] = (0, 0, 0)
    filled = max(0, min(20, int(round(20 * hp_ratio))))
    if filled > 0:
        updated[90:94, 10:10 + filled] = (0, 0, 255)
    return updated


def test_main_view_reader_should_classify_states():
    reader = MainViewReader(_make_config().dungeon_run.main_view)

    assert reader.read(_frame_for("combat")) == MainViewState.COMBAT_ROOM
    assert reader.read(_frame_for("clear")) == MainViewState.CLEAR_ROOM
    assert reader.read(_frame_for("boss")) == MainViewState.BOSS_ROOM
    assert reader.read(_frame_for("finish")) == MainViewState.RUN_FINISHED
    assert reader.read(_frame_for("transition")) == MainViewState.TRANSITION


def test_minimap_reader_should_output_path_and_special_state():
    reader = MinimapReader(_make_config().dungeon_run.minimap)

    state, special = reader.read(_apply_minimap(_frame_for("combat"), "flash", special=True), 1, False)

    assert state == MinimapPathState.NEIGHBOR_FLASH_QMARK
    assert special == MinimapSpecialState.ABYSS_ROOM_PRESENT


def test_guard_layer_should_use_hp_potion_and_abort_when_empty():
    config = _make_config()
    guard = GuardLayer(
        config.dungeon_run.guard_thresholds,
        config.dungeon_run.class_profile,
        config.input.key_bindings,
    )

    ctx = GameContext(
        frame_index=1,
        timestamp=time.time(),
        hero=None,
        player_state=PlayerState(hp_percent=0.2, mp_percent=1.0),
        main_view_state=MainViewState.COMBAT_ROOM,
        potion_cd_ready=True,
        potion_stock_available=True,
    )
    decision = guard.evaluate(ctx)
    assert decision.action == GuardAction.USE_HP_POTION
    assert decision.key_code == "1"

    ctx.potion_stock_available = False
    decision = guard.evaluate(ctx)
    assert decision.action == GuardAction.ABORT_RUN


def test_route_run_controller_should_block_boss_before_last_room():
    config = _make_config()
    controller = RouteRunController(
        room_scripts=[
            RoomScriptConfig(room_idx=1, is_last_normal_room=False),
            RoomScriptConfig(room_idx=2, room_type="normal", is_last_normal_room=True),
            RoomScriptConfig(room_idx=3, room_type="boss", expected_exit_direction="STOP", exit_action_template="none"),
        ],
        class_profile=config.dungeon_run.class_profile,
        start_room_index=1,
    )
    ctx = GameContext(
        frame_index=1,
        timestamp=time.time(),
        hero=None,
        player_state=PlayerState(),
        main_view_state=MainViewState.CLEAR_ROOM,
        minimap_path_state=MinimapPathState.BOSS_ONLY_READY,
    )

    cmd = controller.update(ctx)

    assert cmd.metadata["state"] == "route_error"


def test_fixed_route_pipeline_should_progress_to_boss_and_then_enter_maintenance():
    pipeline = FixedRoutePipeline(_make_config())

    context, cmd = pipeline.process_frame(_apply_minimap(_frame_for("combat"), "dark"))
    assert context.expected_room_index == 1
    assert cmd.skill_index == 3

    context, cmd = pipeline.process_frame(_apply_minimap(_frame_for("clear"), "boss"))
    assert context.main_view_state == MainViewState.CLEAR_ROOM
    assert cmd.action_type.value == "move"
    assert cmd.direction == (1, 0)

    context, cmd = pipeline.process_frame(_apply_minimap(_frame_for("transition"), "boss"))
    assert context.main_view_state == MainViewState.TRANSITION
    assert context.expected_room_index == 1
    assert cmd.action_type.value == "stop"

    context, cmd = pipeline.process_frame(_apply_minimap(_frame_for("boss"), "dark"))
    assert context.expected_room_index == 2
    assert context.main_view_state == MainViewState.BOSS_ROOM
    assert cmd.skill_index == 3

    finish_frame = _apply_minimap(_frame_for("finish"), "dark")
    finish_frame[90:94, 70:90] = (255, 255, 255)  # 高负重也会触发维护
    context, cmd = pipeline.process_frame(finish_frame)
    assert context.main_view_state == MainViewState.RUN_FINISHED
    assert context.maintenance_state == MaintenanceState.CHECK_INVENTORY
    assert cmd.metadata["state"] == "maintenance"


def test_pipeline_should_prioritize_guard_action_before_room_logic():
    pipeline = FixedRoutePipeline(_make_config())

    low_hp_frame = _apply_hp(_apply_minimap(_frame_for("combat"), "dark"), 0.2)
    context, cmd = pipeline.process_frame(low_hp_frame)

    assert context.guard_decision.action == GuardAction.USE_HP_POTION
    assert cmd.action_type.value == "skill"
    assert cmd.key_code == "1"

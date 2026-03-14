"""
固定路线 MVP 运行管线。
"""

from __future__ import annotations

import time
from typing import List, Optional

import numpy as np

from core.config import AppConfig
from core.types import (
    Command,
    GameContext,
    GameObject,
    GuardDecision,
    MainViewState,
    MinimapPathState,
    ObjectType,
)
from logic.guard_layer import GuardLayer
from logic.maintenance_controller import MaintenanceController
from logic.route_run_controller import RouteRunController
from vision.main_view_reader import MainViewReader
from vision.minimap_reader import MinimapReader
from vision.state_reader import StateReader


class FixedRoutePipeline:
    """封装固定路线 MVP 的整帧处理流程。"""

    def __init__(self, config: AppConfig, detector: Optional[object] = None) -> None:
        self.config = config
        self.detector = detector
        self.main_view_reader = MainViewReader(config.dungeon_run.main_view)
        self.minimap_reader = MinimapReader(config.dungeon_run.minimap)
        self.state_reader = StateReader(config.dungeon_run.ui_rois)
        self.guard_layer = GuardLayer(
            config.dungeon_run.guard_thresholds,
            config.dungeon_run.class_profile,
            config.input.key_bindings,
        )
        self.route_controller = RouteRunController(
            room_scripts=config.dungeon_run.room_scripts,
            class_profile=config.dungeon_run.class_profile,
            start_room_index=config.dungeon_run.start_room_index,
        )
        self.maintenance_controller = MaintenanceController(config.dungeon_run.maintenance)
        self._frame_index = 0

    def process_frame(self, frame: np.ndarray) -> tuple[GameContext, Command]:
        """处理一帧并返回上下文与指令。"""
        self._frame_index += 1
        detections = self._detect_objects(frame)
        hero, monsters, items, doors = self._classify_objects(detections)

        main_view_state = self.main_view_reader.read(frame)
        state_read = self.state_reader.read(frame)
        minimap_path_state, minimap_special_state = self.minimap_reader.read(
            frame,
            expected_room_index=self.route_controller.current_room_index,
            is_last_normal_room=self.route_controller.is_last_normal_room,
        )

        context = GameContext(
            frame_index=self._frame_index,
            timestamp=time.time(),
            hero=hero,
            monsters=monsters,
            items=items,
            doors=doors,
            player_state=state_read.player_state,
            room_cleared=main_view_state == MainViewState.CLEAR_ROOM
            or minimap_path_state in {
                MinimapPathState.NEIGHBOR_FLASH_QMARK,
                MinimapPathState.BOSS_ONLY_READY,
            },
            main_view_state=main_view_state,
            minimap_path_state=minimap_path_state,
            minimap_special_state=minimap_special_state,
            expected_room_index=self.route_controller.current_room_index,
            is_last_normal_room=self.route_controller.is_last_normal_room,
            inventory_weight_ratio=state_read.inventory_weight_ratio,
            free_slots=state_read.free_slots,
            vendor_ui_open=state_read.vendor_ui_open,
            potion_cd_ready=state_read.potion_cd_ready,
            potion_stock_available=state_read.potion_stock_available,
            guard_decision=GuardDecision(),
        )

        context.guard_decision = self.guard_layer.evaluate(context)
        if self.maintenance_controller.should_enter(context):
            command = self.maintenance_controller.update(context)
        else:
            command = self.route_controller.update(context)

        context.expected_room_index = self.route_controller.current_room_index
        context.is_last_normal_room = self.route_controller.is_last_normal_room
        return context, command

    def _detect_objects(self, frame: np.ndarray) -> List[GameObject]:
        if self.detector is None:
            return []
        try:
            return list(self.detector.detect(frame))
        except Exception:
            return []

    @staticmethod
    def _classify_objects(
        detections: List[GameObject],
    ) -> tuple[Optional[GameObject], List[GameObject], List[GameObject], List[GameObject]]:
        hero: Optional[GameObject] = None
        monsters: List[GameObject] = []
        items: List[GameObject] = []
        doors: List[GameObject] = []

        for obj in detections:
            if obj.object_type == ObjectType.HERO:
                if hero is None or obj.conf > hero.conf:
                    hero = obj
            elif obj.object_type in {ObjectType.MONSTER, ObjectType.BOSS}:
                monsters.append(obj)
            elif obj.object_type == ObjectType.ITEM:
                items.append(obj)
            elif obj.object_type == ObjectType.GATE:
                doors.append(obj)

        return hero, monsters, items, doors

"""
固定路线副本控制器。
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict, List, Optional

from core.config import ClassProfileConfig, RoomScriptConfig
from core.types import (
    Command,
    CommandType,
    GameContext,
    GuardAction,
    MainViewState,
    MinimapPathState,
)


class RouteRunController:
    """《歼灭追击战》固定路线控制器。"""

    def __init__(
        self,
        room_scripts: List[RoomScriptConfig],
        class_profile: ClassProfileConfig,
        start_room_index: int = 1,
    ) -> None:
        self._room_scripts: Dict[int, RoomScriptConfig] = {
            room.room_idx: room for room in sorted(room_scripts, key=lambda item: item.room_idx)
        }
        self._ordered_room_indices = sorted(self._room_scripts)
        self._current_room_index = start_room_index if start_room_index in self._room_scripts else self._ordered_room_indices[0]
        self._class_profile = class_profile
        self._active_exit_commands: Deque[Command] = deque()
        self._exit_in_progress = False
        self._exit_started_at = 0.0
        self._exit_retry_count = 0
        self._transition_seen = False
        self._transition_started_at = 0.0
        self._pending_room_advance = False
        self._last_combat_at = 0.0

    @property
    def current_room_index(self) -> int:
        """当前预期房间索引。"""
        return self._current_room_index

    @property
    def is_last_normal_room(self) -> bool:
        """当前是否为最后一个普通房。"""
        return self.current_room_script.is_last_normal_room

    @property
    def current_room_script(self) -> RoomScriptConfig:
        """当前房间脚本。"""
        return self._room_scripts[self._current_room_index]

    def update(self, context: GameContext) -> Command:
        """根据上下文输出当前动作。"""
        self._sync_transition(context)
        context.expected_room_index = self._current_room_index
        context.is_last_normal_room = self.is_last_normal_room

        if context.guard_decision.action == GuardAction.ABORT_RUN:
            return Command(
                action_type=CommandType.STOP,
                metadata={"state": "abort_run", "reason": context.guard_decision.reason},
            )

        if context.guard_decision.action in {GuardAction.USE_HP_POTION, GuardAction.USE_MP_POTION}:
            return Command(
                action_type=CommandType.SKILL,
                key_code=context.guard_decision.key_code,
                metadata={"state": "guard", "reason": context.guard_decision.reason},
            )

        if context.main_view_state == MainViewState.RUN_FINISHED:
            return Command(
                action_type=CommandType.STOP,
                metadata={"state": "run_finished"},
            )

        if context.main_view_state == MainViewState.TRANSITION:
            return Command(
                action_type=CommandType.STOP,
                metadata={"state": "transition", "room_idx": self._current_room_index},
            )

        if self._exit_in_progress:
            return self._drive_exit_sequence(context)

        if (
            context.minimap_path_state == MinimapPathState.BOSS_ONLY_READY
            and not self.is_last_normal_room
        ):
            return Command(
                action_type=CommandType.STOP,
                metadata={
                    "state": "route_error",
                    "reason": "boss_ready_before_last_room",
                    "room_idx": self._current_room_index,
                },
            )

        if self._should_start_exit(context):
            self._start_exit_sequence()
            return self._drive_exit_sequence(context)

        if context.main_view_state in {MainViewState.COMBAT_ROOM, MainViewState.BOSS_ROOM}:
            return self._build_combat_command(context)

        if context.main_view_state == MainViewState.CLEAR_ROOM:
            return Command(
                action_type=CommandType.STOP,
                metadata={"state": "clear_room", "room_idx": self._current_room_index},
            )

        return Command(
            action_type=CommandType.STOP,
            metadata={"state": "idle", "room_idx": self._current_room_index},
        )

    def _sync_transition(self, context: GameContext) -> None:
        now = time.time()
        if context.main_view_state == MainViewState.TRANSITION:
            if not self._transition_seen:
                self._transition_seen = True
                self._transition_started_at = now
                self._pending_room_advance = True
                self._last_combat_at = 0.0
            context.transition_elapsed_ms = int((now - self._transition_started_at) * 1000)
            self._exit_in_progress = False
            self._active_exit_commands.clear()
            return

        if self._transition_seen:
            context.transition_elapsed_ms = int((now - self._transition_started_at) * 1000)
            if self._pending_room_advance and context.main_view_state != MainViewState.RUN_FINISHED:
                self._advance_room_index()
            self._transition_seen = False
            self._pending_room_advance = False
            self._transition_started_at = 0.0
            self._exit_retry_count = 0
            self._exit_in_progress = False
            self._active_exit_commands.clear()
            self._last_combat_at = 0.0
        else:
            context.transition_elapsed_ms = 0

    def _advance_room_index(self) -> None:
        try:
            current_pos = self._ordered_room_indices.index(self._current_room_index)
        except ValueError:
            current_pos = 0

        if current_pos + 1 < len(self._ordered_room_indices):
            self._current_room_index = self._ordered_room_indices[current_pos + 1]

    def _should_start_exit(self, context: GameContext) -> bool:
        if context.minimap_path_state == MinimapPathState.CLEAR_PENDING:
            return False
        if context.minimap_path_state == MinimapPathState.NEIGHBOR_FLASH_QMARK:
            return True
        if self.is_last_normal_room and context.minimap_path_state == MinimapPathState.BOSS_ONLY_READY:
            return True
        return False

    def _start_exit_sequence(self) -> None:
        self._active_exit_commands = deque(self._build_exit_template(self.current_room_script.exit_action_template))
        self._exit_in_progress = True
        self._exit_started_at = time.time()
        self._exit_retry_count = 0

    def _drive_exit_sequence(self, context: GameContext) -> Command:
        if self._active_exit_commands:
            return self._active_exit_commands.popleft()

        elapsed_ms = int((time.time() - self._exit_started_at) * 1000)
        if elapsed_ms < self.current_room_script.transition_timeout_ms:
            return Command(
                action_type=CommandType.STOP,
                metadata={
                    "state": "wait_transition",
                    "room_idx": self._current_room_index,
                    "elapsed_ms": elapsed_ms,
                },
            )

        if self._exit_retry_count < 1:
            self._exit_retry_count += 1
            self._active_exit_commands = deque(
                self._build_exit_template(self.current_room_script.exit_action_template)
            )
            self._exit_started_at = time.time()
            return Command(
                action_type=CommandType.STOP,
                metadata={
                    "state": "retry_exit",
                    "room_idx": self._current_room_index,
                    "retry": self._exit_retry_count,
                },
            )

        self._exit_in_progress = False
        return Command(
            action_type=CommandType.STOP,
            metadata={
                "state": "exit_timeout",
                "room_idx": self._current_room_index,
                "reason": "transition_not_detected",
            },
        )

    def _build_combat_command(self, context: GameContext) -> Command:
        now = time.time()
        interval_s = max(0.05, self._class_profile.combat_interval_ms / 1000.0)
        if now - self._last_combat_at < interval_s:
            return Command(
                action_type=CommandType.STOP,
                metadata={"state": "combat_cooldown", "room_idx": self._current_room_index},
            )

        self._last_combat_at = now
        return Command(
            action_type=CommandType.SKILL,
            skill_index=self._class_profile.primary_combat_skill,
            metadata={
                "state": "combat_room",
                "room_idx": self._current_room_index,
                "phase": context.main_view_state.value,
            },
        )

    @staticmethod
    def _build_exit_template(template_name: str) -> List[Command]:
        if template_name == "none":
            return [Command(action_type=CommandType.STOP, metadata={"phase": "no_exit"})]

        if template_name.startswith("move_right_hold_"):
            duration_ms = RouteRunController._parse_duration_ms(template_name, default=1200)
            commands = [
                Command(
                    action_type=CommandType.MOVE,
                    direction=(1, 0),
                    duration=duration_ms / 1000.0,
                    metadata={"phase": "exit_move_right"},
                )
            ]
            if template_name.endswith("_then_jump"):
                commands.append(
                    Command(action_type=CommandType.JUMP, duration=0.0, metadata={"phase": "exit_jump"})
                )
            return commands

        if template_name.startswith("move_left_hold_"):
            duration_ms = RouteRunController._parse_duration_ms(template_name, default=1000)
            return [
                Command(
                    action_type=CommandType.MOVE,
                    direction=(-1, 0),
                    duration=duration_ms / 1000.0,
                    metadata={"phase": "exit_move_left"},
                )
            ]

        if template_name == "move_up_platform_then_right":
            return [
                Command(
                    action_type=CommandType.MOVE,
                    direction=(0, -1),
                    duration=0.35,
                    metadata={"phase": "exit_up"},
                ),
                Command(action_type=CommandType.JUMP, duration=0.0, metadata={"phase": "platform_jump"}),
                Command(
                    action_type=CommandType.MOVE,
                    direction=(1, 0),
                    duration=0.80,
                    metadata={"phase": "exit_right"},
                ),
            ]

        if template_name == "move_down_drop_then_left":
            return [
                Command(
                    action_type=CommandType.MOVE,
                    direction=(0, 1),
                    duration=0.25,
                    metadata={"phase": "drop_down"},
                ),
                Command(
                    action_type=CommandType.MOVE,
                    direction=(-1, 0),
                    duration=0.80,
                    metadata={"phase": "exit_left"},
                ),
            ]

        return [Command(action_type=CommandType.STOP, metadata={"phase": "unknown_exit_template"})]

    @staticmethod
    def _parse_duration_ms(template_name: str, default: int) -> int:
        digits = "".join(ch if ch.isdigit() else " " for ch in template_name).split()
        if not digits:
            return default
        return int(digits[-1])

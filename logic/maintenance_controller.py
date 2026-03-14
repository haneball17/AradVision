"""
副本结束后的维护流程控制器。
"""

from __future__ import annotations

from core.config import MaintenanceConfig
from core.types import Command, CommandType, GameContext, MainViewState, MaintenanceState


class MaintenanceController:
    """维护流程控制器。"""

    def __init__(self, config: MaintenanceConfig) -> None:
        self.config = config

    def should_enter(self, context: GameContext) -> bool:
        """是否应进入维护流程。"""
        return (
            context.main_view_state == MainViewState.RUN_FINISHED
            or context.inventory_weight_ratio >= self.config.max_weight_ratio
            or context.free_slots < self.config.min_free_slots
        )

    def update(self, context: GameContext) -> Command:
        """更新维护状态并返回当前动作。"""
        if context.main_view_state == MainViewState.RUN_FINISHED:
            context.maintenance_state = MaintenanceState.CHECK_INVENTORY
        elif context.vendor_ui_open:
            context.maintenance_state = (
                MaintenanceState.SELL_DRY_RUN if self.config.sell_dry_run else MaintenanceState.OPEN_VENDOR
            )
        else:
            context.maintenance_state = MaintenanceState.OPEN_VENDOR

        return Command(
            action_type=CommandType.STOP,
            metadata={
                "state": "maintenance",
                "maintenance_state": context.maintenance_state.value,
                "sell_dry_run": self.config.sell_dry_run,
            },
        )

"""
Mock输入驱动实现

用于开发测试，记录指令但不实际发送。

Author: yangmq17
Date: Day 1 下午
Priority: P0
Dependencies: input/base_driver.py, core/types.py
"""

import time
import random
from typing import List
from input.base_driver import BaseInputDriver
from core.types import Command, CommandType


class MockInputDriver(BaseInputDriver):
    """
    Mock输入驱动

    记录所有指令到历史，不实际发送硬件信号
    """

    def __init__(self):
        """初始化Mock输入驱动"""
        self.command_history: List[Command] = []
        self.is_running = True

    def execute(self, command: Command) -> bool:
        """
        执行指令（Mock实现 - 仅记录）

        Args:
            command: 要执行的指令

        Returns:
            总是返回True
        """
        # 记录到历史
        self.command_history.append(command)

        # 模拟执行延迟
        if command.duration > 0:
            time.sleep(command.duration)

        return True

    def tap(self, key: str) -> bool:
        """
        短按按键（Mock实现）

        Args:
            key: 按键码

        Returns:
            True
        """
        command = Command(
            action_type=CommandType.ATTACK,
            key_code=key,
            duration=0.0
        )
        return self.execute(command)

    def hold(self, key: str, duration: float) -> bool:
        """
        长按按键（Mock实现）

        Args:
            key: 按键码
            duration: 持续时间

        Returns:
            True
        """
        # 添加随机抖动（反检测）
        actual_duration = duration + random.gauss(0, 0.02)
        actual_duration = max(0.05, actual_duration)  # 最小50ms

        command = Command(
            action_type=CommandType.MOVE,
            key_code=key,
            duration=actual_duration
        )
        return self.execute(command)

    def stop_all(self) -> bool:
        """
        停止所有输入

        Returns:
            True
        """
        self.is_running = False
        return True

    def get_history(self) -> List[Command]:
        """
        获取指令历史

        Returns:
            指令列表
        """
        return self.command_history.copy()

    def clear_history(self):
        """清空历史记录"""
        self.command_history.clear()

    def get_command_count(self, command_type: CommandType = None) -> int:
        """
        获取特定类型指令的数量

        Args:
            command_type: 指令类型，None表示统计所有

        Returns:
            指令数量
        """
        if command_type is None:
            return len(self.command_history)
        return sum(1 for cmd in self.command_history if cmd.action_type == command_type)

    def __repr__(self) -> str:
        return f"MockInputDriver(commands_executed={len(self.command_history)})"

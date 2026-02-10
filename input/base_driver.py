"""
输入驱动抽象基类

Author: yangmq17
Date: Day 1 下午
Priority: P0
Dependencies: core/types.py
"""

from abc import ABC, abstractmethod
from core.types import Command


class BaseInputDriver(ABC):
    """
    输入驱动抽象基类

    定义了输入驱动的统一接口，支持真实驱动和Mock驱动
    """

    @abstractmethod
    def execute(self, command: Command) -> bool:
        """
        执行指令

        Args:
            command: 要执行的指令

        Returns:
            是否执行成功
        """
        pass

    @abstractmethod
    def tap(self, key: str) -> bool:
        """
        短按按键

        Args:
            key: 按键码 (如 "x", "a", "space")

        Returns:
            是否执行成功
        """
        pass

    @abstractmethod
    def hold(self, key: str, duration: float) -> bool:
        """
        长按按键

        Args:
            key: 按键码
            duration: 持续时间 (秒)

        Returns:
            是否执行成功
        """
        pass

    @abstractmethod
    def stop_all(self) -> bool:
        """
        停止所有输入（紧急停止）

        Returns:
            是否成功
        """
        pass

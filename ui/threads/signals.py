"""
引擎信号定义

定义引擎线程与主窗口之间的通信信号。

Author: haneball17
Date: 2026-02-11
"""

from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
from typing import Dict, Any


class EngineSignals(QObject):
    """
    引擎信号类

    定义引擎线程发送的所有信号。
    """

    # 帧信号 (30 FPS) - 携带 OpenCV 图像数据
    frame_ready = Signal(np.ndarray)

    # 状态信号 (5 Hz) - 携带状态字典
    status_update = Signal(dict)

    # 日志信号 - 携带日志级别和消息
    log_message = Signal(str, str)  # (level, message)

    # 错误信号 - 携带错误信息
    error_occurred = Signal(str)

    # 系统状态信号
    system_started = Signal()
    system_stopped = Signal()
    system_paused = Signal()
    system_resumed = Signal()

    # 参数更新信号
    params_updated = Signal(dict)


class StatusData:
    """
    状态数据类

    定义状态数据的结构。
    """

    def __init__(
        self,
        fps: float = 0.0,
        state: str = "STOPPED",
        latency: float = 0.0,
        frame_count: int = 0,
        run_time: float = 0.0,
        monsters: int = 0,
        items: int = 0,
        doors: int = 0,
        room_cleared: bool = False,
        hero_detected: bool = False
    ):
        self.fps = fps
        self.state = state
        self.latency = latency
        self.frame_count = frame_count
        self.run_time = run_time
        self.monsters = monsters
        self.items = items
        self.doors = doors
        self.room_cleared = room_cleared
        self.hero_detected = hero_detected

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "fps": self.fps,
            "state": self.state,
            "latency": self.latency,
            "frame_count": self.frame_count,
            "run_time": self.run_time,
            "monsters": self.monsters,
            "items": self.items,
            "doors": self.doors,
            "room_cleared": self.room_cleared,
            "hero_detected": self.hero_detected
        }

"""
屏幕捕获引擎

使用 MSS 库实现高性能跨平台屏幕捕获。
支持窗口标题/句柄捕获，目标 FPS ≥ 30。

Author: haneball17
Date: Day 1 下午
Priority: P0
Dependencies: mss, numpy, core/config.py, core/logger.py
"""

import time
import threading
from typing import Optional, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path

# 可选导入依赖
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

try:
    import mss
    import mss.tools
    import cv2
    HAS_CAPTURE_DEPS = True
except ImportError:
    HAS_CAPTURE_DEPS = False
    mss = None  # type: ignore
    cv2 = None  # type: ignore

from core.config import CaptureConfig
from core.logger import logger
from core.exceptions import CaptureError, WindowNotFoundError


@dataclass
class CaptureStats:
    """捕获统计信息"""
    fps: float = 0.0
    avg_latency: float = 0.0  # 平均延迟（毫秒）
    frame_count: int = 0
    drop_count: int = 0
    total_bytes: int = 0


class CaptureEngine:
    """
    屏幕捕获引擎

    使用 MSS 实现高性能截图，支持窗口捕获和性能监控。

    Examples:
        >>> capture = CaptureEngine(config)
        >>> capture.start()
        >>> frame = capture.get_frame()
        >>> capture.stop()

    Attributes:
        config: 截图配置
        is_running: 是否正在运行
        stats: 捕获统计信息
    """

    def __init__(self, config: CaptureConfig):
        """
        初始化捕获引擎

        Args:
            config: 截图配置
        """
        self.config = config
        self.is_running = False
        self.stats = CaptureStats()

        # MSS 实例
        self._sct: Optional[mss.mss] = None

        # 窗口句柄
        self._hwnd: Optional[int] = None
        self._monitor: Optional[dict] = None

        # 帧缓存
        self._current_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()

        # 性能监控
        self._last_frame_time: float = 0.0
        self._frame_times: list = []

        logger.info(f"CaptureEngine 初始化完成 (target_fps={config.target_fps})")

    def start(self) -> None:
        """
        启动捕获引擎

        Raises:
            CaptureError: 启动失败
            WindowNotFoundError: 找不到目标窗口
        """
        if self.is_running:
            logger.warning("CaptureEngine 已在运行中")
            return

        try:
            # 初始化 MSS
            self._sct = mss.mss()

            # 查找目标窗口
            self._find_window()

            # 设置捕获区域
            self._setup_monitor()

            self.is_running = True
            self.stats.frame_count = 0
            self.stats.drop_count = 0

            logger.info(f"CaptureEngine 启动成功 (window={self.config.window_title})")

        except WindowNotFoundError:
            raise
        except Exception as e:
            raise CaptureError(f"启动捕获引擎失败: {e}")

    def stop(self) -> None:
        """停止捕获引擎"""
        if not self.is_running:
            return

        self.is_running = False

        if self._sct:
            self._sct.close()
            self._sct = None

        logger.info(f"CaptureEngine 停止 (stats={self.stats})")

    def get_frame(self) -> np.ndarray:
        """
        获取当前帧（阻塞式）

        Returns:
            OpenCV 图像矩阵 (BGR 格式, shape: [H, W, 3])

        Raises:
            CaptureError: 捕获失败
        """
        if not self.is_running:
            raise CaptureError("CaptureEngine 未启动")

        try:
            start_time = time.perf_counter()

            # 使用 MSS 捕获
            screenshot = self._sct.grab(self._monitor)

            # 转换为 NumPy 数组
            frame = np.array(screenshot)

            # MSS 返回的是 BGRA 格式，需要转为 BGR
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            elif frame.shape[2] == 1:  # 灰度图
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            # 更新缓存
            with self._frame_lock:
                self._current_frame = frame

            # 性能监控
            latency = (time.perf_counter() - start_time) * 1000  # 转换为毫秒
            self._update_stats(latency, frame.size)

            return frame

        except Exception as e:
            self.stats.drop_count += 1
            raise CaptureError(f"帧捕获失败: {e}")

    def get_frame_cached(self) -> Optional[np.ndarray]:
        """
        获取缓存的当前帧（非阻塞）

        Returns:
            缓存的帧，如果没有则返回 None
        """
        with self._frame_lock:
            if self._current_frame is None:
                return None
            return self._current_frame.copy()

    def _find_window(self) -> None:
        """
        查找目标窗口

        Raises:
            WindowNotFoundError: 找不到窗口
        """
        import win32gui
        import win32con

        def enum_windows_callback(hwnd, windows):
            """枚举窗口回调"""
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.config.window_title in title:
                    windows.append(hwnd)
            return True

        windows = []
        try:
            win32gui.EnumWindows(enum_windows_callback, windows)
        except Exception as e:
            logger.warning(f"窗口枚举失败: {e}，使用主显示器")

        if windows:
            # 使用第一个匹配的窗口
            self._hwnd = windows[0]
            logger.debug(f"找到窗口: hwnd={self._hwnd}")
        else:
            # 未找到窗口，使用主显示器
            logger.warning(f"未找到窗口 '{self.config.window_title}'，使用主显示器")
            self._hwnd = None

    def _setup_monitor(self) -> None:
        """设置捕获区域"""
        if self._hwnd is not None:
            # 窗口捕获（Windows 平台）
            import win32gui

            try:
                left, top, right, bottom = win32gui.GetWindowRect(self._hwnd)
                width = right - left
                height = bottom - top

                self._monitor = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }
                logger.debug(f"窗口捕获区域: {self._monitor}")
                return
            except Exception as e:
                logger.warning(f"无法获取窗口位置: {e}，使用主显示器")

        # 使用主显示器
        monitors = self._sct.monitors
        if len(monitors) > 1:
            # monitors[0] 是所有显示器的组合，monitors[1] 是主显示器
            self._monitor = monitors[1] if self.config.monitor_index == 0 else monitors[min(self.config.monitor_index, len(monitors) - 1)]
        else:
            self._monitor = monitors[0]

        logger.debug(f"显示器捕获区域: {self._monitor}")

    def _update_stats(self, latency: float, frame_size: int) -> None:
        """
        更新统计信息

        Args:
            latency: 捕获延迟（毫秒）
            frame_size: 帧大小（字节）
        """
        self.stats.frame_count += 1
        self.stats.total_bytes += frame_size

        # 更新延迟
        self._frame_times.append(latency)
        if len(self._frame_times) > 100:  # 保留最近 100 帧
            self._frame_times.pop(0)

        self.stats.avg_latency = sum(self._frame_times) / len(self._frame_times)

        # 计算 FPS
        now = time.perf_counter()
        if self._last_frame_time > 0:
            delta = now - self._last_frame_time
            if delta > 0:
                instant_fps = 1.0 / delta
                # 指数移动平均
                if self.stats.fps == 0:
                    self.stats.fps = instant_fps
                else:
                    self.stats.fps = 0.9 * self.stats.fps + 0.1 * instant_fps

        self._last_frame_time = now

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = CaptureStats()
        self._frame_times.clear()
        self._last_frame_time = 0.0
        logger.debug("统计信息已重置")

    def get_stats(self) -> CaptureStats:
        """
        获取捕获统计信息

        Returns:
            统计信息对象
        """
        return self.stats

    def __repr__(self) -> str:
        return (
            f"CaptureEngine("
            f"running={self.is_running}, "
            f"fps={self.stats.fps:.1f}, "
            f"latency={self.stats.avg_latency:.1f}ms, "
            f"frames={self.stats.frame_count}"
            f")"
        )


# ==================== 工厂函数 ====================

class MockCaptureEngine:
    """
    Mock 捕获引擎（用于测试）

    生成随机图像帧，无需 mss/cv2 依赖。
    """

    def __init__(self, config: Optional[CaptureConfig] = None):
        """初始化 Mock 捕获引擎"""
        self.config = config or CaptureConfig()
        self.is_running = False
        self.stats = CaptureStats()
        self._frame_count = 0

    def start(self) -> None:
        """启动 Mock 捕获引擎"""
        self.is_running = True
        logger.info("Mock 捕获引擎启动（生成随机图像帧）")

    def stop(self) -> None:
        """停止 Mock 捕获引擎"""
        self.is_running = False
        logger.info("Mock 捕获引擎已停止")

    def get_frame(self) -> Optional[np.ndarray]:
        """
        生成随机图像帧

        Returns:
            随机生成的 BGR 图像（1920x1080x3）
        """
        if not self.is_running:
            return None

        # 模拟捕获延迟
        latency = 5.0  # 5ms 模拟延迟
        time.sleep(latency / 1000.0)

        # 生成随机图像
        if HAS_NUMPY:
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        else:
            frame = None

        # 更新统计信息
        self._frame_count += 1
        self.stats.frame_count = self._frame_count
        self.stats.avg_latency = latency
        self.stats.fps = 30.0  # 模拟 30 FPS

        return frame

    def get_stats(self) -> CaptureStats:
        """获取统计信息"""
        return self.stats

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = CaptureStats()
        self._frame_count = 0

    def __repr__(self) -> str:
        return f"MockCaptureEngine(running={self.is_running}, frames={self._frame_count})"


def create_capture_engine(
    config: Optional[CaptureConfig] = None,
    use_mock: bool = False
) -> "CaptureEngine":
    """
    创建捕获引擎实例（工厂函数）

    Args:
        config: 截图配置，None 则使用默认配置
        use_mock: 是否使用 Mock 引擎（用于测试）

    Returns:
        CaptureEngine 或 MockCaptureEngine 实例

    Examples:
        >>> from core.capture import create_capture_engine
        >>> capture = create_capture_engine()
        >>> capture.start()
    """
    if config is None:
        from core.config import get_config
        config = get_config().capture

    # 检查依赖是否可用
    if use_mock or not HAS_CAPTURE_DEPS:
        logger.info("使用 Mock 捕获引擎（无需 mss/cv2）")
        return MockCaptureEngine(config)

    # 使用真实捕获引擎
    if not HAS_NUMPY:
        logger.warning("numpy 不可用，使用 Mock 捕获引擎")
        return MockCaptureEngine(config)

    return CaptureEngine(config)


__all__ = [
    "CaptureEngine",
    "CaptureStats",
    "MockCaptureEngine",
    "create_capture_engine"
]

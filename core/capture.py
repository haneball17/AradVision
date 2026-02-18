"""
屏幕捕获引擎

支持多后端捕获：
- mss: 基于屏幕区域抓取（兼容旧实现）
- wgc: Windows Graphics Capture 窗口级捕获（目标窗口被遮挡时仍可采集）

设计目标：
1. 保持外部接口稳定（start/get_frame/stop/get_stats）。
2. 支持 backend=auto/wgc/mss 的配置选择。
3. WGC 失败时自动降级到 MSS，保证主流程不中断。
"""

from __future__ import annotations

import inspect
import platform
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

# 可选导入依赖
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

try:
    import mss
    import cv2

    HAS_CAPTURE_DEPS = True
except ImportError:
    HAS_CAPTURE_DEPS = False
    mss = None  # type: ignore
    cv2 = None  # type: ignore

from core.config import CaptureConfig
from core.exceptions import CaptureError
from core.logger import logger


@dataclass
class CaptureStats:
    """捕获统计信息。"""

    fps: float = 0.0
    avg_latency: float = 0.0  # 平均延迟（毫秒）
    frame_count: int = 0
    drop_count: int = 0
    total_bytes: int = 0


class BaseCaptureBackend(ABC):
    """捕获后端抽象基类。"""

    backend_name: str = "base"

    def __init__(self, config: CaptureConfig):
        self.config = config
        self.stats = CaptureStats()
        self.is_running = False
        self._last_frame_time = 0.0
        self._frame_times: list[float] = []

    @abstractmethod
    def start(self) -> None:
        """启动后端。"""

    @abstractmethod
    def stop(self) -> None:
        """停止后端。"""

    @abstractmethod
    def get_frame(self) -> "np.ndarray":
        """获取一帧图像（BGR）。"""

    def get_stats(self) -> CaptureStats:
        """返回统计信息。"""
        return self.stats

    def reset_stats(self) -> None:
        """重置统计信息。"""
        self.stats = CaptureStats()
        self._frame_times.clear()
        self._last_frame_time = 0.0

    def _update_stats(self, latency_ms: float, frame_size: int) -> None:
        """更新统计信息（所有后端共用）。"""
        self.stats.frame_count += 1
        self.stats.total_bytes += frame_size

        self._frame_times.append(latency_ms)
        if len(self._frame_times) > 100:
            self._frame_times.pop(0)
        self.stats.avg_latency = sum(self._frame_times) / len(self._frame_times)

        now = time.perf_counter()
        if self._last_frame_time > 0:
            delta = now - self._last_frame_time
            if delta > 0:
                instant_fps = 1.0 / delta
                if self.stats.fps == 0:
                    self.stats.fps = instant_fps
                else:
                    self.stats.fps = 0.9 * self.stats.fps + 0.1 * instant_fps
        self._last_frame_time = now


class MSSCaptureBackend(BaseCaptureBackend):
    """MSS 捕获后端（屏幕区域抓取）。"""

    backend_name = "mss"

    def __init__(self, config: CaptureConfig):
        super().__init__(config)
        self._sct: Optional[mss.mss] = None
        self._hwnd: Optional[int] = None
        self._monitor: Optional[dict] = None

    def start(self) -> None:
        if self.is_running:
            return

        if not HAS_CAPTURE_DEPS:
            raise CaptureError("MSS 后端不可用：缺少 mss/cv2 依赖")
        if not HAS_NUMPY:
            raise CaptureError("MSS 后端不可用：缺少 numpy 依赖")

        try:
            self._sct = mss.mss()
            self._find_window()
            self._setup_monitor()
            self.is_running = True
            self.reset_stats()
            logger.info(f"MSS 后端启动成功 (window={self.config.window_title})")
        except Exception as exc:
            raise CaptureError(f"MSS 后端启动失败: {exc}") from exc

    def stop(self) -> None:
        if not self.is_running:
            return

        self.is_running = False
        if self._sct is not None:
            self._sct.close()
            self._sct = None

    def get_frame(self) -> "np.ndarray":
        if not self.is_running:
            raise CaptureError("MSS 后端未启动")

        try:
            start_time = time.perf_counter()
            screenshot = self._sct.grab(self._monitor)
            frame = np.array(screenshot)

            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            elif frame.ndim == 3 and frame.shape[2] == 1:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_stats(latency_ms, int(frame.size))
            return frame
        except Exception as exc:
            self.stats.drop_count += 1
            raise CaptureError(f"MSS 帧捕获失败: {exc}") from exc

    def _find_window(self) -> None:
        """按标题查找窗口句柄。"""
        try:
            import win32gui
        except ImportError:
            logger.warning("win32gui 不可用，MSS 后端回退到显示器捕获")
            self._hwnd = None
            return

        windows: list[int] = []

        def enum_windows_callback(hwnd: int, found: list[int]) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.config.window_title in title:
                    found.append(hwnd)
            return True

        win32gui.EnumWindows(enum_windows_callback, windows)
        self._hwnd = windows[0] if windows else None
        if self._hwnd is None:
            logger.warning(f"未找到窗口 '{self.config.window_title}'，MSS 后端将使用显示器捕获")

    def _setup_monitor(self) -> None:
        """根据窗口句柄或显示器配置设置抓取区域。"""
        if self._sct is None:
            raise CaptureError("MSS 对象未初始化")

        if self._hwnd is not None:
            try:
                import win32gui

                left, top, right, bottom = win32gui.GetWindowRect(self._hwnd)
                self._monitor = {
                    "left": left,
                    "top": top,
                    "width": right - left,
                    "height": bottom - top,
                }
                logger.info(f"MSS 窗口捕获区域: {self._monitor}")
                return
            except Exception as exc:
                logger.warning(f"获取窗口位置失败，回退显示器捕获: {exc}")

        monitors = self._sct.monitors
        if len(monitors) > 1:
            idx = self.config.monitor_index
            self._monitor = monitors[1] if idx == 0 else monitors[min(idx, len(monitors) - 1)]
        else:
            self._monitor = monitors[0]
        logger.info(f"MSS 显示器捕获区域: {self._monitor}")


class WGCCaptureBackend(BaseCaptureBackend):
    """WGC 捕获后端（Windows Graphics Capture 封装）。

    说明：
    - 依赖第三方 `windows-capture` 包。
    - 该后端在非 Windows 或依赖缺失时会启动失败，交由上层降级到 MSS。
    """

    backend_name = "wgc"

    def __init__(self, config: CaptureConfig):
        super().__init__(config)
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._frame_ready = threading.Event()
        self._closed = threading.Event()
        self._capture_thread: Optional[threading.Thread] = None
        self._capture_obj: Optional[Any] = None
        self._capture_control: Optional[Any] = None
        self._last_error: Optional[Exception] = None

    def start(self) -> None:
        if self.is_running:
            return

        if platform.system().lower() != "windows":
            raise CaptureError("WGC 后端仅支持 Windows")
        if not HAS_NUMPY:
            raise CaptureError("WGC 后端不可用：缺少 numpy")

        self._capture_obj = self._create_capture_object()
        self._register_events(self._capture_obj)

        self._capture_thread = threading.Thread(
            target=self._run_capture_loop,
            name="WGCCaptureThread",
            daemon=True,
        )
        self._capture_thread.start()

        # 等待首帧，避免上层启动后立刻取帧为空。
        if not self._frame_ready.wait(timeout=3.0):
            self.stop()
            if self._last_error is not None:
                raise CaptureError(f"WGC 启动失败: {self._last_error}") from self._last_error
            raise CaptureError("WGC 启动超时：未收到首帧")

        self.is_running = True
        self.reset_stats()
        logger.info(f"WGC 后端启动成功 (window={self.config.window_title})")

    def stop(self) -> None:
        if not self.is_running and self._capture_thread is None:
            return

        self.is_running = False
        self._closed.set()

        # 尽量优雅停止底层捕获。
        if self._capture_control is not None and hasattr(self._capture_control, "stop"):
            try:
                self._capture_control.stop()
            except Exception:
                pass

        if self._capture_obj is not None and hasattr(self._capture_obj, "stop"):
            try:
                self._capture_obj.stop()
            except Exception:
                pass

        if self._capture_thread is not None and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)

        self._capture_thread = None
        self._capture_obj = None
        self._capture_control = None

    def get_frame(self) -> "np.ndarray":
        if not self.is_running:
            raise CaptureError("WGC 后端未启动")

        start_time = time.perf_counter()
        if not self._frame_ready.wait(timeout=1.0):
            self.stats.drop_count += 1
            raise CaptureError("WGC 获取帧超时")

        with self._frame_lock:
            if self._latest_frame is None:
                self.stats.drop_count += 1
                raise CaptureError("WGC 当前无可用帧")
            frame = self._latest_frame.copy()

        latency_ms = (time.perf_counter() - start_time) * 1000
        self._update_stats(latency_ms, int(frame.size))
        return frame

    def _create_capture_object(self) -> Any:
        """创建 windows-capture 对象，并兼容不同参数命名。"""
        try:
            from windows_capture import WindowsCapture
        except Exception as exc:
            raise CaptureError(
                "WGC 依赖缺失：请在 Windows 环境安装 windows-capture"
            ) from exc

        kwargs: Dict[str, Any] = {}
        sig = inspect.signature(WindowsCapture)
        params = sig.parameters

        if "cursor_capture" in params:
            kwargs["cursor_capture"] = bool(getattr(self.config, "wgc_show_cursor", False))
        if "draw_border" in params:
            kwargs["draw_border"] = not bool(getattr(self.config, "wgc_force_borderless", False))
        if "window_name" in params:
            kwargs["window_name"] = self.config.window_title
        elif "window_title" in params:
            kwargs["window_title"] = self.config.window_title

        try:
            return WindowsCapture(**kwargs)
        except TypeError:
            # 参数签名变化时尝试最小参数构造，降低版本差异影响。
            return WindowsCapture()

    def _register_events(self, capture_obj: Any) -> None:
        """注册 frame 回调，将底层帧统一转为 BGR ndarray。"""
        if not hasattr(capture_obj, "event"):
            raise CaptureError("windows-capture 版本不兼容：缺少 event 装饰器")

        @capture_obj.event
        def on_frame_arrived(frame: Any, capture_control: Any) -> None:
            self._capture_control = capture_control
            parsed = self._parse_frame(frame)
            if parsed is None:
                return
            with self._frame_lock:
                self._latest_frame = parsed
            self._frame_ready.set()

        @capture_obj.event
        def on_closed() -> None:
            self._closed.set()

    def _run_capture_loop(self) -> None:
        try:
            self._capture_obj.start()
        except Exception as exc:
            self._last_error = exc
            self._closed.set()

    def _parse_frame(self, raw_frame: Any) -> Optional["np.ndarray"]:
        """将底层 frame 转换为 BGR ndarray。"""
        frame_array = None

        if HAS_NUMPY and isinstance(raw_frame, np.ndarray):
            frame_array = raw_frame
        elif hasattr(raw_frame, "frame_buffer"):
            try:
                frame_array = np.asarray(raw_frame.frame_buffer)
            except Exception:
                frame_array = None
        elif hasattr(raw_frame, "to_ndarray"):
            try:
                frame_array = raw_frame.to_ndarray()
            except Exception:
                frame_array = None

        if frame_array is None:
            return None

        if frame_array.ndim != 3:
            return None

        if frame_array.shape[2] == 4:
            if cv2 is not None:
                frame_array = cv2.cvtColor(frame_array, cv2.COLOR_BGRA2BGR)
            else:
                frame_array = frame_array[:, :, :3]
        elif frame_array.shape[2] == 1:
            if cv2 is not None:
                frame_array = cv2.cvtColor(frame_array, cv2.COLOR_GRAY2BGR)
            else:
                frame_array = np.repeat(frame_array, 3, axis=2)

        return frame_array


class CaptureEngine:
    """捕获引擎门面，负责后端选择与自动降级。"""

    VALID_BACKENDS = {"auto", "wgc", "mss"}

    def __init__(
        self,
        config: CaptureConfig,
        backend: str = "auto",
        allow_fallback: bool = True,
    ):
        self.config = config
        self.requested_backend = self._normalize_backend(backend)
        self.allow_fallback = allow_fallback
        self.is_running = False
        self.active_backend = "none"
        self._backend: Optional[BaseCaptureBackend] = None
        self._frame_lock = threading.Lock()
        self._current_frame: Optional[np.ndarray] = None

    @staticmethod
    def _normalize_backend(backend: Optional[str]) -> str:
        value = (backend or "auto").strip().lower()
        if value not in CaptureEngine.VALID_BACKENDS:
            logger.warning(f"未知 capture.backend='{backend}'，回退为 auto")
            return "auto"
        return value

    def start(self) -> None:
        if self.is_running:
            return

        backend_order = self._resolve_backend_order()
        errors: list[str] = []

        for backend_name in backend_order:
            try:
                backend = self._create_backend(backend_name)
                backend.start()
                self._backend = backend
                self.active_backend = backend.backend_name
                self.is_running = True
                logger.info(
                    f"CaptureEngine 启动成功: requested={self.requested_backend}, "
                    f"active={self.active_backend}"
                )
                if self.active_backend != self.requested_backend and self.requested_backend != "auto":
                    logger.warning(
                        f"CaptureEngine 已降级: requested={self.requested_backend}, "
                        f"active={self.active_backend}"
                    )
                return
            except Exception as exc:
                errors.append(f"{backend_name}: {exc}")
                logger.warning(f"捕获后端启动失败 ({backend_name}): {exc}")

        raise CaptureError("; ".join(["所有捕获后端均启动失败"] + errors))

    def stop(self) -> None:
        if self._backend is not None:
            self._backend.stop()
        self._backend = None
        self.active_backend = "none"
        self.is_running = False

    def get_frame(self) -> "np.ndarray":
        if not self.is_running or self._backend is None:
            raise CaptureError("CaptureEngine 未启动")

        frame = self._backend.get_frame()
        with self._frame_lock:
            self._current_frame = frame
        return frame

    def get_frame_cached(self) -> Optional["np.ndarray"]:
        with self._frame_lock:
            if self._current_frame is None:
                return None
            return self._current_frame.copy()

    def get_stats(self) -> CaptureStats:
        if self._backend is None:
            return CaptureStats()
        return self._backend.get_stats()

    def reset_stats(self) -> None:
        if self._backend is not None:
            self._backend.reset_stats()

    def _resolve_backend_order(self) -> list[str]:
        if self.requested_backend == "mss":
            return ["mss"]

        if self.requested_backend == "wgc":
            if self.allow_fallback:
                return ["wgc", "mss"]
            return ["wgc"]

        # auto：Windows 优先 WGC，其他平台直接 MSS
        if platform.system().lower() == "windows":
            return ["wgc", "mss"]
        return ["mss"]

    def _create_backend(self, backend_name: str) -> BaseCaptureBackend:
        if backend_name == "mss":
            return MSSCaptureBackend(self.config)
        if backend_name == "wgc":
            return WGCCaptureBackend(self.config)
        raise CaptureError(f"不支持的捕获后端: {backend_name}")

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"CaptureEngine(requested={self.requested_backend}, active={self.active_backend}, "
            f"fps={stats.fps:.1f}, latency={stats.avg_latency:.1f}ms, frames={stats.frame_count})"
        )


class MockCaptureEngine:
    """Mock 捕获引擎（用于测试）。"""

    def __init__(self, config: Optional[CaptureConfig] = None):
        self.config = config or CaptureConfig()
        self.is_running = False
        self.stats = CaptureStats()
        self.active_backend = "mock"
        self._frame_count = 0

    def start(self) -> None:
        self.is_running = True
        logger.info("Mock 捕获引擎启动（生成随机图像帧）")

    def stop(self) -> None:
        self.is_running = False
        logger.info("Mock 捕获引擎已停止")

    def get_frame(self) -> Optional["np.ndarray"]:
        if not self.is_running:
            return None

        latency = 5.0
        time.sleep(latency / 1000.0)

        if HAS_NUMPY:
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        else:
            frame = None

        self._frame_count += 1
        self.stats.frame_count = self._frame_count
        self.stats.avg_latency = latency
        self.stats.fps = 30.0

        return frame

    def get_stats(self) -> CaptureStats:
        return self.stats

    def reset_stats(self) -> None:
        self.stats = CaptureStats()
        self._frame_count = 0

    def __repr__(self) -> str:
        return f"MockCaptureEngine(running={self.is_running}, frames={self._frame_count})"


def create_capture_engine(
    config: Optional[CaptureConfig] = None,
    use_mock: bool = False,
    backend: Optional[str] = None,
    allow_fallback: bool = True,
) -> "CaptureEngine | MockCaptureEngine":
    """创建捕获引擎实例（工厂函数）。"""
    if config is None:
        from core.config import get_config

        config = get_config().capture

    if use_mock:
        logger.info("使用 Mock 捕获引擎（命令行或配置指定）")
        return MockCaptureEngine(config)

    if not HAS_NUMPY:
        logger.warning("numpy 不可用，回退到 Mock 捕获引擎")
        return MockCaptureEngine(config)

    selected_backend = backend or getattr(config, "backend", "auto")
    engine = CaptureEngine(
        config=config,
        backend=selected_backend,
        allow_fallback=allow_fallback,
    )
    return engine


__all__ = [
    "CaptureEngine",
    "CaptureStats",
    "MockCaptureEngine",
    "MSSCaptureBackend",
    "WGCCaptureBackend",
    "create_capture_engine",
]

"""
紧急熔断监听器（KillSwitch）。

用途：
- 独立线程监听紧急停止键（默认 F12）；
- 检测到按键后立即执行回调（通常是 input_driver.stop_all）。
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

try:
    from core.logger import get_logger

    logger = get_logger(__name__)
except Exception:  # pragma: no cover - 日志模块不可用时降级
    import logging

    logger = logging.getLogger(__name__)


class KillSwitch:
    """
    紧急停止监听器。

    线程安全说明：
    - start/stop 使用内部锁，避免重复启动或重复停止；
    - 监听线程仅做“检测 + 触发回调”，不承担复杂业务逻辑。
    """

    def __init__(
        self,
        on_trigger: Callable[[], None],
        kill_key: str = "F12",
        poll_interval: float = 0.05,
        key_checker: Optional[Callable[[str], bool]] = None,
    ) -> None:
        """
        初始化熔断监听器。

        Args:
            on_trigger: 触发后执行的回调函数
            kill_key: 紧急停止键
            poll_interval: 轮询间隔（秒）
            key_checker: 可注入按键检测函数（用于测试）
        """
        if poll_interval <= 0:
            raise ValueError("poll_interval 必须大于 0")

        self._on_trigger = on_trigger
        self._kill_key = kill_key
        self._poll_interval = poll_interval
        self._key_checker = key_checker if key_checker is not None else self._build_default_checker()

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._triggered = False
        self._running = False
        self._last_error: Optional[Exception] = None

    @property
    def is_running(self) -> bool:
        """当前监听线程是否在运行。"""
        with self._lock:
            return self._running

    @property
    def triggered(self) -> bool:
        """是否已触发过熔断。"""
        with self._lock:
            return self._triggered

    @property
    def last_error(self) -> Optional[Exception]:
        """监听过程中最后一次异常。"""
        with self._lock:
            return self._last_error

    def start(self) -> bool:
        """
        启动监听线程。

        Returns:
            bool: 成功启动返回 True；若已经运行则直接返回 True。
        """
        with self._lock:
            if self._running:
                return True

            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, name="KillSwitchListener", daemon=True)
            self._thread.start()
            self._running = True
            logger.info(f"KillSwitch 已启动，监听按键: {self._kill_key}")
            return True

    def stop(self, join_timeout: float = 1.0) -> None:
        """
        停止监听线程。

        Args:
            join_timeout: 等待线程退出的超时时间（秒）
        """
        with self._lock:
            self._stop_event.set()
            thread = self._thread

        if thread is not None and thread.is_alive():
            thread.join(timeout=join_timeout)

        with self._lock:
            self._running = False
            self._thread = None
            logger.info("KillSwitch 已停止")

    def _run(self) -> None:
        """
        监听循环。

        触发逻辑：
        - 检测到 kill_key 被按下 -> 标记 triggered -> 调用回调 -> 自动退出监听线程。
        """
        try:
            while not self._stop_event.is_set():
                try:
                    if self._key_checker(self._kill_key):
                        with self._lock:
                            self._triggered = True
                        logger.warning(f"检测到紧急停止按键: {self._kill_key}")
                        self._on_trigger()
                        break
                except Exception as exc:
                    # 不让单次检测异常直接炸掉线程，记录后继续监听
                    with self._lock:
                        self._last_error = exc
                    logger.error(f"KillSwitch 按键检测异常: {exc}")

                time.sleep(self._poll_interval)
        finally:
            with self._lock:
                self._running = False
                self._thread = None

    @staticmethod
    def _build_default_checker() -> Callable[[str], bool]:
        """
        构建默认按键检测函数。

        说明：默认依赖 keyboard 库；若不可用会抛出 RuntimeError，
        避免“看似启动成功但永远无法触发”的隐性故障。
        """
        try:
            import keyboard
        except Exception as exc:  # pragma: no cover - 依赖缺失由运行环境决定
            raise RuntimeError("未安装 keyboard 库，无法使用默认 KillSwitch 检测器") from exc

        return keyboard.is_pressed

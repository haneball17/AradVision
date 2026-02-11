"""
真实输入驱动实现

职责：
1. 将逻辑层 Command 转换为底层按键行为；
2. 提供线程安全的 tap/hold/stop_all 接口；
3. 在不依赖真实系统输入环境时，支持注入测试后端。
"""

from __future__ import annotations

import random
import threading
import time
from typing import Dict, Optional, Protocol, Set, Tuple

from core.exceptions import InputError, InvalidKeyError
from core.types import Command, CommandType
from input.base_driver import BaseInputDriver

try:
    from core.logger import get_logger

    logger = get_logger(__name__)
except Exception:  # pragma: no cover - 日志模块不可用时降级
    import logging

    logger = logging.getLogger(__name__)


class InputBackend(Protocol):
    """输入后端协议，便于在测试中注入替身。"""

    def key_down(self, key: str) -> None:
        """按下按键。"""

    def key_up(self, key: str) -> None:
        """弹起按键。"""


class _PyDirectInputBackend:
    """
    pydirectinput 后端实现。

    说明：仅在本机安装了 pydirectinput 时可用。
    """

    def __init__(self) -> None:
        try:
            import pydirectinput  # 延迟导入，避免测试环境硬依赖
        except Exception as exc:
            raise InputError("未安装 pydirectinput，无法使用真实输入后端") from exc
        self._pydirectinput = pydirectinput

    def key_down(self, key: str) -> None:
        self._pydirectinput.keyDown(key)

    def key_up(self, key: str) -> None:
        self._pydirectinput.keyUp(key)


class InputDriver(BaseInputDriver):
    """
    输入驱动器（线程安全）。

    设计要点：
    - 通过内部锁序列化输入操作，避免多线程竞争；
    - 通过后端注入实现可测试性；
    - 支持紧急停止后阻断后续输入。
    """

    # 支持的按键集合（统一为小写）
    VALID_KEYS: Set[str] = {
        "up",
        "down",
        "left",
        "right",
        "space",
        "enter",
        "escape",
        "x",
        "a",
        "s",
        "d",
        "f",
        "z",
        "1",
        "2",
        "3",
        "4",
        "5",
    }

    # 常见别名映射（输入层对外兼容大小写与缩写）
    KEY_ALIASES: Dict[str, str] = {
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
        "SPACE": "space",
        "ESC": "escape",
        "RETURN": "enter",
    }

    DIRECTION_TO_KEY: Dict[Tuple[int, int], str] = {
        (0, -1): "up",
        (0, 1): "down",
        (-1, 0): "left",
        (1, 0): "right",
    }

    def __init__(
        self,
        enable_jitter: bool = True,
        jitter_mean: float = 0.1,
        jitter_std: float = 0.02,
        backend: Optional[InputBackend] = None,
    ) -> None:
        """
        初始化输入驱动。

        Args:
            enable_jitter: 是否启用随机延迟（反检测）
            jitter_mean: 随机延迟均值（秒）
            jitter_std: 随机延迟标准差（秒）
            backend: 可选输入后端；未提供时自动使用 pydirectinput
        """
        if jitter_mean <= 0:
            raise ValueError("jitter_mean 必须大于 0")
        if jitter_std < 0:
            raise ValueError("jitter_std 不能为负数")

        self.enable_jitter = enable_jitter
        self.jitter_mean = jitter_mean
        self.jitter_std = jitter_std

        self._backend: InputBackend = backend if backend is not None else _PyDirectInputBackend()
        self._lock = threading.RLock()
        self._pressed_keys: Set[str] = set()
        self.is_running = True

    def execute(self, command: Command) -> bool:
        """
        执行动作指令。

        Returns:
            bool: 执行成功返回 True；紧急停止状态返回 False。
        """
        with self._lock:
            if not self.is_running:
                logger.warning("输入驱动已停止，忽略 execute 调用")
                return False

        action = command.action_type
        if action == CommandType.STOP:
            return self.stop_all()

        if action == CommandType.MOVE:
            return self._execute_move(command)

        if action in (CommandType.ATTACK, CommandType.SKILL, CommandType.PICKUP, CommandType.JUMP, CommandType.DASH):
            if not command.key_code:
                raise InputError(f"{action.value} 指令缺少 key_code")
            return self.tap(command.key_code) if command.duration <= 0 else self.hold(
                command.key_code,
                command.duration,
            )

        raise InputError(f"不支持的指令类型: {action}")

    def tap(self, key: str) -> bool:
        """
        短按按键（按下 -> 等待 -> 弹起）。
        """
        normalized = self._normalize_key(key)
        with self._lock:
            if not self.is_running:
                logger.warning(f"输入驱动已停止，忽略 tap({normalized})")
                return False
            self._press_unlocked(normalized)

        sleep_time = self._resolve_tap_duration()
        time.sleep(sleep_time)

        with self._lock:
            self._release_unlocked(normalized)
        return True

    def hold(self, key: str, duration: float) -> bool:
        """
        长按按键（按下 -> 等待 duration -> 弹起）。
        """
        if duration < 0:
            raise InputError("hold 持续时间不能为负数")

        normalized = self._normalize_key(key)
        with self._lock:
            if not self.is_running:
                logger.warning(f"输入驱动已停止，忽略 hold({normalized}, {duration:.3f})")
                return False
            self._press_unlocked(normalized)

        time.sleep(self._resolve_hold_duration(duration))

        with self._lock:
            self._release_unlocked(normalized)
        return True

    def stop_all(self) -> bool:
        """
        紧急停止：释放全部已按下按键，并阻断后续输入。
        """
        with self._lock:
            for key in list(self._pressed_keys):
                try:
                    self._backend.key_up(key)
                finally:
                    self._pressed_keys.discard(key)
            self.is_running = False
            logger.warning("触发 stop_all，已释放所有按键并停止输入驱动")
        return True

    def emergency_stop(self) -> bool:
        """
        对齐文档命名：紧急停止等价于 stop_all。
        """
        return self.stop_all()

    def resume(self) -> None:
        """
        解除停止状态（用于测试或手动恢复）。
        """
        with self._lock:
            self.is_running = True

    def _execute_move(self, command: Command) -> bool:
        """
        执行移动指令。

        规则：
        - 优先使用 direction 解析方向键；
        - 若 direction 不可用，回退到 key_code。
        """
        if command.direction is not None:
            key = self.DIRECTION_TO_KEY.get(command.direction)
            if key is None:
                raise InputError(f"无效方向向量: {command.direction}")
        elif command.key_code:
            key = self._normalize_key(command.key_code)
        else:
            raise InputError("MOVE 指令缺少 direction 或 key_code")

        if command.duration <= 0:
            return self.tap(key)
        return self.hold(key, command.duration)

    def _normalize_key(self, key: str) -> str:
        """
        归一化按键并做合法性校验。
        """
        if not key:
            raise InvalidKeyError("按键不能为空")

        # 先按文档兼容常见大写别名，再统一小写
        normalized = self.KEY_ALIASES.get(key, key).lower()
        if normalized not in self.VALID_KEYS:
            raise InvalidKeyError(f"不支持的按键: {key}")
        return normalized

    def _press_unlocked(self, key: str) -> None:
        """
        在已持锁状态下按下按键。
        """
        try:
            self._backend.key_down(key)
        except Exception as exc:
            raise InputError(f"按下按键失败: {key}") from exc
        self._pressed_keys.add(key)

    def _release_unlocked(self, key: str) -> None:
        """
        在已持锁状态下弹起按键。
        """
        try:
            self._backend.key_up(key)
        except Exception as exc:
            raise InputError(f"弹起按键失败: {key}") from exc
        self._pressed_keys.discard(key)

    def _resolve_tap_duration(self) -> float:
        """
        计算 tap 默认持续时间。

        返回值做了硬边界限制，避免异常值导致过长阻塞。
        """
        if not self.enable_jitter:
            return max(0.01, self.jitter_mean)

        value = random.gauss(self.jitter_mean, self.jitter_std)
        return min(0.3, max(0.03, value))

    def _resolve_hold_duration(self, duration: float) -> float:
        """
        计算 hold 持续时间（可加入轻微抖动）。
        """
        if not self.enable_jitter:
            return duration

        value = duration + random.gauss(0, self.jitter_std)
        return max(0.01, value)

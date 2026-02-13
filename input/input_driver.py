"""
真实输入驱动实现

职责：
1. 将逻辑层 Command 转换为底层按键行为；
2. 提供线程安全的 tap/hold/stop_all 接口；
3. 从配置加载按键映射，实现动作与按键解耦；
4. 窗口焦点管理，确保输入发送到正确的窗口。

Author: haneball17, yangmq17
Date: 2026-02-13
"""

from __future__ import annotations

import random
import threading
import time
from typing import Dict, Optional, Protocol, Set

from core.exceptions import InputError, InvalidKeyError
from core.types import Command, CommandType
from input.base_driver import BaseInputDriver

try:
    from core.logger import get_logger
    logger = get_logger(__name__)
except Exception:  # pragma: no cover
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


class WindowManager:
    """
    游戏窗口管理器

    职责：
    - 检测游戏窗口是否在前台
    - 自动激活游戏窗口（使用 AttachThreadInput 机制）

    Windows 前台锁定机制说明：
    - Windows 2000+ 阻止后台进程调用 SetForegroundWindow
    - 解决方案：使用 AttachThreadInput 附加到目标线程
    - 这样系统认为输入来自"用户线程"，允许激活窗口
    """

    def __init__(self, window_title: str):
        self.target_title = window_title.lower()
        logger.info(f"[WindowManager] 初始化，目标窗口: '{window_title}'")
        logger.info(f"[WindowManager] 查找模式: 包含匹配（title 包含 '{window_title}'）")
        logger.info(f"[WindowManager] 激活机制: AttachThreadInput (Microsoft 推荐方式)")

    def is_focused(self) -> bool:
        """
        检查游戏窗口是否在前台

        使用精确 hwnd 匹配而非子串匹配，避免误判：
        - 错误方式：检查 "DNF" 是否在前台窗口标题中
        - 正确方式：检查前台窗口的 hwnd 是否就是游戏窗口的 hwnd

        Returns:
            游戏窗口是否为前台窗口
        """
        try:
            import win32gui

            # 获取当前前台窗口的 hwnd
            foreground_hwnd = win32gui.GetForegroundWindow()
            foreground_title = win32gui.GetWindowText(foreground_hwnd)

            # 获取目标游戏窗口的 hwnd（精确匹配）
            target_hwnd = self.get_hwnd()

            logger.info(f"[WindowManager.is_focused] ===== 焦点检查 =====")
            logger.info(f"[WindowManager.is_focused] 前台窗口: hwnd={foreground_hwnd}, title='{foreground_title}'")
            logger.info(f"[WindowManager.is_focused] 目标游戏: hwnd={target_hwnd}")

            if target_hwnd is None:
                # 找不到目标窗口，假设未聚焦
                logger.warning(f"[WindowManager.is_focused] 找不到目标窗口，返回 False")
                return False

            # 精确比较：当前前台窗口就是目标窗口？
            is_focused = (foreground_hwnd == target_hwnd)

            logger.info(f"[WindowManager.is_focused] hwnd 比较: {foreground_hwnd} == {target_hwnd} = {is_focused}")
            logger.info(f"[WindowManager.is_focused] 结果: {'游戏窗口在前台' if is_focused else '游戏窗口不在前台'}")
            logger.info(f"[WindowManager.is_focused] =======================")

            return is_focused
        except ImportError:
            logger.warning("[WindowManager.is_focused] win32gui 不可用，非 Windows 平台")
            return True
        except Exception as e:
            logger.warning(f"[WindowManager.is_focused] 窗口焦点检测失败: {e}")
            return True

    def get_hwnd(self) -> Optional[int]:
        """
        获取游戏窗口句柄

        Returns:
            窗口句柄，未找到返回 None
        """
        try:
            import win32gui

            # 枚举所有窗口查找匹配
            matching_windows = []

            def enum_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and self.target_title in title.lower():
                        windows.append((hwnd, title))
                return True

            win32gui.EnumWindows(enum_callback, matching_windows)

            if matching_windows:
                logger.info(f"[WindowManager.get_hwnd] 找到 {len(matching_windows)} 个匹配窗口:")
                for hwnd, title in matching_windows:
                    logger.info(f"  - hwnd={hwnd}, title='{title}'")
                return matching_windows[0][0]  # 返回第一个匹配
            else:
                logger.warning(f"[WindowManager.get_hwnd] 未找到包含 '{self.target_title}' 的窗口")
                logger.info("[WindowManager.get_hwnd] 尝试列出所有可见窗口标题:")
                all_titles = []
                def enum_all(hwnd, titles):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            titles.append(title)
                    return True
                win32gui.EnumWindows(enum_all, all_titles)
                for title in all_titles[:20]:  # 只显示前 20 个
                    logger.info(f"  - '{title}'")
                if len(all_titles) > 20:
                    logger.info(f"  ... 还有 {len(all_titles) - 20} 个窗口")
                return None

        except ImportError:
            logger.warning("[WindowManager.get_hwnd] win32gui 不可用")
            return None
        except Exception as e:
            logger.warning(f"[WindowManager.get_hwnd] 获取窗口句柄失败: {e}")
            return None

    def bring_to_front(self) -> bool:
        """
        激活游戏窗口到前台

        使用 AttachThreadInput 机制（Microsoft 推荐方式）：
        1. 获取目标窗口的线程 ID
        2. 将当前线程附加到目标线程
        3. 调用 SetForegroundWindow（现在会成功）
        4. 分离线程

        Returns:
            是否成功激活
        """
        max_retries = 3
        delay = 0.1  # 每次尝试间隔（秒）

        logger.info(f"[WindowManager.bring_to_front] ========== 开始窗口激活流程 ==========")

        for attempt in range(max_retries):
            try:
                import win32gui
                import win32process
                import win32con
                import win32api

                logger.info(f"[WindowManager.bring_to_front] --- 尝试 {attempt + 1}/{max_retries} ---")

                # 获取窗口句柄
                hwnd = self.get_hwnd()
                if not hwnd:
                    logger.warning(f"[WindowManager.bring_to_front] 无法获取窗口句柄，激活失败")
                    return False

                logger.info(f"[WindowManager.bring_to_front] 目标窗口句柄: {hwnd}")

                # 记录当前前台窗口
                current_hwnd = win32gui.GetForegroundWindow()
                current_title = win32gui.GetWindowText(current_hwnd)
                logger.info(f"[WindowManager.bring_to_front] 当前前台窗口: hwnd={current_hwnd}, title='{current_title}'")

                # 检查是否已经是前台
                if current_hwnd == hwnd:
                    logger.info(f"✓ [WindowManager.bring_to_front] 窗口已在前台，无需激活")
                    return True

                # ========== 关键：使用 AttachThreadInput 绕过 Windows 限制 ==========
                # 获取目标窗口的线程 ID 和进程 ID
                target_thread_id, target_process_id = win32process.GetWindowThreadProcessId(hwnd)
                logger.debug(f"[WindowManager.bring_to_front] 目标窗口: thread_id={target_thread_id}, process_id={target_process_id}")

                # 获取当前线程 ID
                current_thread_id = win32api.GetCurrentThreadId()
                logger.debug(f"[WindowManager.bring_to_front] 当前线程: thread_id={current_thread_id}")

                # 如果是同一线程，直接激活即可
                if current_thread_id == target_thread_id:
                    logger.debug(f"[WindowManager.bring_to_front] 同一线程，直接激活")
                    win32gui.SetForegroundWindow(hwnd)
                else:
                    # ========== AttachThreadInput 机制 ==========
                    # 将当前线程的输入处理附加到目标线程
                    # 这使系统认为我们的输入来自该线程（"用户输入"）
                    logger.debug(f"[WindowManager.bring_to_front] 调用 AttachThreadInput 附加线程")
                    attach_result = win32process.AttachThreadInput(
                        current_thread_id,
                        target_thread_id
                    )
                    logger.debug(f"[WindowManager.bring_to_front] AttachThreadInput 返回: {attach_result}")

                    if attach_result:
                        # 现在可以成功激活窗口
                        win32gui.SetForegroundWindow(hwnd)
                        time.sleep(delay)

                        # 验证是否成功
                        new_hwnd = win32gui.GetForegroundWindow()
                        if new_hwnd == hwnd:
                            new_title = win32gui.GetWindowText(new_hwnd)
                            logger.info(f"✓ [WindowManager.bring_to_front] 窗口激活成功! (hwnd={new_hwnd}, title='{new_title}')")

                            # 确保窗口可见并恢复（如果最小化）
                            if win32gui.IsIconic(hwnd):
                                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                logger.debug(f"[WindowManager.bring_to_front] 窗口已从最小化恢复")
                        else:
                            new_title = win32gui.GetWindowText(new_hwnd)
                            logger.warning(f"[WindowManager.bring_to_front] 激活后前台: hwnd={new_hwnd}, title='{new_title}'")

                        # 分离线程（必须！否则目标线程无法接收真实用户输入）
                        win32process.AttachThreadInput(current_thread_id, target_thread_id, False)
                        logger.debug(f"[WindowManager.bring_to_front] 线程已分离")

                        if new_hwnd == hwnd:
                            return True
                    else:
                        logger.warning(f"[WindowManager.bring_to_front] AttachThreadInput 失败")

                time.sleep(delay)

            except ImportError:
                logger.warning("[WindowManager.bring_to_front] win32 模块不可用，非 Windows 平台")
                return True
            except Exception as e:
                logger.error(f"[WindowManager.bring_to_front] 窗口激活异常: {type(e).__name__}: {e}")
                import traceback
                logger.debug(f"[WindowManager.bring_to_front] 异常详情: {traceback.format_exc()}")
                time.sleep(delay)

        logger.warning(f"[WindowManager.bring_to_front] 经过 {max_retries} 次尝试，窗口激活失败")
        logger.info(f"[WindowManager.bring_to_front] ========== 窗口激活流程结束 ==========")
        return False


class InputDriver(BaseInputDriver):
    """
    输入驱动器（线程安全）

    设计要点：
    - 通过配置文件驱动按键映射，实现动作与按键解耦
    - 集成窗口焦点管理，确保输入发送到正确的窗口
    - 通过内部锁序列化输入操作，避免多线程竞争
    - 支持紧急停止阻断后续输入
    - 支持技能栏索引（1-8）
    """

    def __init__(
        self,
        enable_jitter: bool = True,
        jitter_mean: float = 0.1,
        jitter_std: float = 0.02,
        backend: Optional[InputBackend] = None,
        key_bindings: Optional[Dict[str, str]] = None,
        window_title: Optional[str] = None,
        check_focus: bool = True,
        auto_activate: bool = False,
    ) -> None:
        """
        初始化输入驱动

        Args:
            enable_jitter: 是否启用随机延迟（反检测）
            jitter_mean: 随机延迟均值（秒）
            jitter_std: 随机延迟标准差（秒）
            backend: 可选输入后端；未提供时自动使用 pydirectinput
            key_bindings: 按键映射字典 {action_name: key_name}
            window_title: 游戏窗口标题
            check_focus: 是否检查窗口焦点
            auto_activate: 是否自动激活游戏窗口
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

        # ========== 窗口管理器配置（详细日志）==========
        logger.info(f"[InputDriver.__init__] ========== 输入驱动初始化 ==========")
        logger.info(f"[InputDriver.__init__] window_title: {window_title}")
        logger.info(f"[InputDriver.__init__] check_focus: {check_focus}")
        logger.info(f"[InputDriver.__init__] auto_activate: {auto_activate}")

        # 窗口管理器
        self._window_manager: Optional[WindowManager] = None
        if window_title and check_focus:
            logger.info(f"[InputDriver.__init__] 创建 WindowManager (window_title='{window_title}', check_focus=True)")
            self._window_manager = WindowManager(window_title)
            self._check_focus = check_focus
            self._auto_activate = auto_activate
            logger.info(f"[InputDriver.__init__] ✓ 窗口管理器已创建")
            logger.info(f"[InputDriver.__init__] ✓ 将检查窗口焦点: {self._check_focus}")
            logger.info(f"[InputDriver.__init__] ✓ 自动激活窗口: {self._auto_activate}")
        else:
            reason = []
            if not window_title:
                reason.append("window_title=None")
            if not check_focus:
                reason.append("check_focus=False")
            logger.warning(f"[InputDriver.__init__] 窗口管理器未创建，原因: {', '.join(reason)}")
            self._check_focus = False
            self._auto_activate = False

        # 按键映射：动作名 -> 按键名
        self._action_to_key: Dict[CommandType, str] = {}
        self._build_key_mapping(key_bindings)
        logger.info(f"[InputDriver.__init__] ========================================")

    def _build_key_mapping(self, key_bindings: Optional[Dict[str, str]]) -> None:
        """
        构建动作到按键的映射表

        如果提供了 key_bindings，使用自定义映射；否则使用默认映射

        默认映射（符合 DNF 习惯）：
        - 移动：方向键 up/down/left/right
        - 攻击：x 键
        - 拾取：x 键（与攻击共用）
        - 技能：z 键
        - 跳跃：c 键
        - 技能栏：1-8 数字键
        """
        if key_bindings:
            # 使用自定义映射
            self._action_to_key = {
                CommandType.ATTACK: key_bindings.get("attack", "x"),
                CommandType.PICKUP: key_bindings.get("pick_up", "x"),  # 拾取与攻击共用
                CommandType.SKILL: key_bindings.get("skill", "z"),
                CommandType.JUMP: key_bindings.get("jump", "c"),
            }
            # 技能栏（通过 skill_index 映射）
            for i in range(1, 9):
                self._action_to_key[f"skill_{i}"] = key_bindings.get(f"skill_{i}", str(i))
            logger.info("使用自定义按键映射")
        else:
            # 使用默认映射
            self._action_to_key = {
                CommandType.ATTACK: "x",
                CommandType.PICKUP: "x",  # 拾取与攻击共用
                CommandType.SKILL: "z",
                CommandType.JUMP: "c",
            }
            # 技能栏默认映射到数字键
            for i in range(1, 9):
                self._action_to_key[f"skill_{i}"] = str(i)
            logger.info("使用默认按键映射")

        logger.debug(f"按键映射: {self._action_to_key}")

    def execute(self, command: Command) -> bool:
        """
        执行动作指令

        Args:
            command: 要执行的指令

        Returns:
            是否执行成功
        """
        with self._lock:
            if not self.is_running:
                logger.warning("输入驱动已停止，忽略 execute 调用")
                return False

            # ========== 窗口焦点检查（详细日志）==========
            logger.debug(f"[InputDriver.execute] ==================== 输入前检查 ====================")
            logger.debug(f"[InputDriver.execute] 动作类型: {command.action_type.value}")
            logger.debug(f"[InputDriver.execute] _check_focus: {self._check_focus}")
            logger.debug(f"[InputDriver.execute] _window_manager 存在: {self._window_manager is not None}")

            if self._check_focus and self._window_manager:
                is_focused = self._window_manager.is_focused()
                logger.debug(f"[InputDriver.execute] 窗口焦点状态: {is_focused}")

                if not is_focused:
                    logger.warning("[InputDriver.execute] ⚠ 游戏窗口不在前台！")
                    # 只有在 auto_activate=True 时才激活窗口
                    if self._auto_activate:
                        logger.info("[InputDriver.execute] auto_activate=True，开始激活窗口...")
                        success = self._window_manager.bring_to_front()
                        if not success:
                            # 激活失败，记录警告但继续执行
                            logger.warning("[InputDriver.execute] ✓ 窗口激活失败，输入可能无效")
                        else:
                            logger.info("[InputDriver.execute] ✓ 窗口激活成功")
                    else:
                        logger.warning("[InputDriver.execute] auto_activate=False，跳过窗口激活，输入可能无效")
                else:
                    logger.info("[InputDriver.execute] ✓ 游戏窗口在前台")

            logger.debug(f"[InputDriver.execute] ==================================================")

            action = command.action_type

            # 处理 STOP 命令
            if action == CommandType.STOP:
                return self.stop_all()

            # 处理移动指令
            if action == CommandType.MOVE:
                return self._execute_move(command)

            # 处理技能栏指令（通过 skill_index）
            if action == CommandType.SKILL and command.skill_index:
                key = self._action_to_key.get(f"skill_{command.skill_index}")
                if not key:
                    logger.warning(f"技能栏位 {command.skill_index} 未配置按键")
                    return False
                return self.tap(key)

            # 处理其他动作指令（ATTACK, 无 skill_index 的 SKILL, JUMP, PICKUP）
            if action in (CommandType.ATTACK, CommandType.JUMP, CommandType.PICKUP):
                key = self._action_to_key.get(action)
                if not key:
                    logger.warning(f"动作 {action.value} 未配置按键")
                    return False
                return self.tap(key) if command.duration <= 0 else self.hold(
                    key, command.duration,
                )
            # 处理 PICKUP（单独处理，因为可能与 ATTACK 共用按键）
            if action == CommandType.PICKUP:
                key = self._action_to_key.get(action)
                return self.tap(key)

            logger.warning(f"不支持的指令类型: {action}")
            return False

    def tap(self, key: str) -> bool:
        """
        短按按键（按下 -> 等待 -> 弹起）

        Args:
            key: 按键码

        Returns:
            是否执行成功
        """
        normalized = self._normalize_key(key)
        if not normalized:
            return False

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
        长按按键（按下 -> 等待 duration -> 弹起）

        Args:
            key: 按键码
            duration: 持续时间 (秒)

        Returns:
            是否执行成功
        """
        if duration < 0:
            raise InputError("hold 持续时间不能为负数")

        normalized = self._normalize_key(key)
        if not normalized:
            return False

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
        紧急停止：释放全部已按下按键，并阻断后续输入

        Returns:
            是否成功
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
        对齐文档命名：紧急停止等价于 stop_all
        """
        return self.stop_all()

    def resume(self) -> None:
        """
        解除停止状态（用于测试或手动恢复）
        """
        with self._lock:
            self.is_running = True

    def _execute_move(self, command: Command) -> bool:
        """
        执行移动指令

        优先使用 direction 解析方向键；
        若 direction 不可用，回退到 key_code。
        """
        key = None
        duration = command.duration

        if command.direction is not None:
            # 从方向向量解析按键
            dx, dy = command.direction
            if dy < 0:
                key = "up"
            elif dy > 0:
                key = "down"
            elif dx < 0:
                key = "left"
            elif dx > 0:
                key = "right"
            else:
                logger.warning(f"无效方向向量: {command.direction}")
                return False
        elif command.key_code:
            # 兼容旧的 key_code 参数
            key = self._normalize_key(command.key_code)
        else:
            logger.error("MOVE 指令缺少 direction 或 key_code")
            return False

        if not key:
            return False

        return self.tap(key) if duration <= 0 else self.hold(key, duration)

    def _parse_direction(self, key: str) -> Optional[tuple[int, int]]:
        """
        解析方向键名为 (dx, dy) 向量

        Args:
            key: 按键名称

        Returns:
            (dx, dy) 方量，或 None（非方向键）
        """
        direction_map = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }
        return direction_map.get(key.lower())

    def _normalize_key(self, key: str) -> Optional[str]:
        """
        归一化按键并做合法性校验

        支持的按键：方向键、x/c/z、数字键 1-8
        """
        if not key:
            raise InvalidKeyError("按键不能为空")

        normalized = key.lower()
        valid_keys = {
            "up", "down", "left", "right",  # 方向键
            "x",  # 攻击/拾取
            "z",  # 技能
            "c",  # 跳跃
            "1", "2", "3", "4", "5", "6", "7", "8",  # 技能栏
        }

        if normalized not in valid_keys:
            logger.warning(f"不支持的按键: {key}")
            return None
        return normalized

    def _press_unlocked(self, key: str) -> None:
        """
        在已持锁状态下按下按键
        """
        try:
            self._backend.key_down(key)
        except Exception as exc:
            raise InputError(f"按下按键失败: {key}") from exc
        self._pressed_keys.add(key)

    def _release_unlocked(self, key: str) -> None:
        """
        在已持锁状态下弹起按键
        """
        try:
            self._backend.key_up(key)
        except Exception as exc:
            raise InputError(f"弹起按键失败: {key}") from exc
        self._pressed_keys.discard(key)

    def _resolve_tap_duration(self) -> float:
        """
        计算 tap 默认持续时间

        返回值做了硬边界限制，避免异常值导致过长阻塞
        """
        if not self.enable_jitter:
            return max(0.01, self.jitter_mean)

        value = random.gauss(self.jitter_mean, self.jitter_std)
        return min(0.3, max(0.03, value))

    def _resolve_hold_duration(self, duration: float) -> float:
        """
        计算 hold 持续时间（可加入轻微抖动）
        """
        if not self.enable_jitter:
            return duration

        value = duration + random.gauss(0, self.jitter_std)
        return max(0.01, value)

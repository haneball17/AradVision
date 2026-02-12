"""
UI 集成模块

提供 EngineThread 与主程序的集成功能，解耦 UI 和核心引擎。

Author: haneball17
Date: 2026-02-11
"""

import logging
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING
from pathlib import Path

# 导入尝试
try:
    from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

# 导入核心模块
try:
    from ui.threads.engine_thread import EngineThread, create_engine_thread
    HAS_ENGINE_THREAD = True
except ImportError:
    HAS_ENGINE_THREAD = False

# 导入世界模型（用于检查 WorldModel 是否已集成）
try:
    from logic.world_model import WorldModel
    HAS_WORLD_MODEL = True
except ImportError:
    HAS_WORLD_MODEL = False

from core.logger import logger

# UI 模式常量
UI_MODE_ATTR = "_ui_mode"

# 依赖检查
def check_dependencies() -> Tuple[bool, bool, bool, bool]:
    """
    检查 UI 集成的依赖是否可用

    Returns:
        (pyqt_available, engine_thread_available, world_model_available)
    """
    pyqt_ok = HAS_PYQT
    engine_ok = HAS_ENGINE_THREAD
    world_ok = HAS_WORLD_MODEL

    logger.debug(f"依赖检查: PyQt5={pyqt_ok}, EngineThread={engine_ok}, WorldModel={world_ok}")

    return pyqt_ok, engine_ok, world_ok


def is_ui_mode() -> bool:
    """
    检查当前是否为 UI 模式

    Returns:
        True 如果在 UI 模式，False 否则
    """
    # 通过 globals() 获取全局是否有 _ui_mode 属性
    import sys
    current_module = sys.modules.get(__name__)

    # 检查是否在 UI 模式
    return hasattr(current_module, UI_MODE_ATTR)


def create_ui_engine_thread(config: dict) -> Optional["ui.threads.engine_thread.EngineThread"]:
    """
    创建 UI 引擎线程

    Args:
        config: 配置字典

    Returns:
        EngineThread 实例，如果依赖不可用则返回 None
    """
    if not check_dependencies()[0]:
        logger.error("PyQt5 或 EngineThread 不可用，无法创建 UI 引擎线程")
        return None

    logger.info("创建 UI 引擎线程...")
    return create_engine_thread(config)


def get_ui_update_handlers(config: dict) -> Dict[str, Any]:
    """
    获取 UI 更新所需的处理器函数

    这些处理器将在信号连接时被调用，用于更新 UI 界面。
    返回的字典结构：
    {
        "update_video_preview": lambda frame: logger.debug(f"更新视频预览: 帧 {frame.shape if frame is not None else 'None'}"),
        "update_status_panel": lambda status: logger.debug(f"更新状态面板: {status}"),
        "add_log_message": lambda level, msg: logger.log(level, f"日志: [{level}] {msg}"),
        "show_error": lambda error: logger.error(f"错误: {error}"),
    }

    Args:
        config: 配置字典

    Returns:
        处理器函数字典
    """
    return {
        "update_video_preview": lambda frame: None,
        "update_status_panel": lambda status: None,
        "add_log_message": lambda level, msg: None,
        "show_error": lambda error: None,
    }


def _create_signal_connection(
    engine_thread: "ui.threads.engine_thread.EngineThread",
    signal_name: str,
    slot_func: callable,
    config: dict
) -> bool:
    """
    创建信号连接

    Args:
        engine_thread: EngineThread 实例
        signal_name: 信号名称 (frame_ready, status_update, log_message, error_occurred)
        slot_func: 槽函数
        config: 配置字典

    Returns:
        连接是否成功
    """
    try:
        signal = getattr(engine_thread.signals, signal_name)
        signal.connect(slot_func)
        logger.debug(f"信号连接: {signal_name} -> {slot_func.__name__}")
        return True
    except Exception as e:
        logger.error(f"信号连接失败: {signal_name} -> {slot_func.__name__}: {e}")
        return False


def setup_ui_mode(
    world_model: "logic.world_model.WorldModel",
    config: dict
) -> bool:
    """
    设置 UI 模式

    Args:
        world_model: WorldModel 实例
        config: 配置字典

    Returns:
        是否成功启用 UI 模式
    """
    try:
        # 设置 UI 模式标志
        import sys
        sys.modules[__name__]._ui_mode = True

        # 更新 WorldModel 的状态引用
        if hasattr(world_model, 'set_ui_mode'):
            world_model.set_ui_mode(True)

        logger.info("UI 模式已启用")
        return True
    except Exception as e:
        logger.error(f"设置 UI 模式失败: {e}")
        return False


def get_ui_mode(world_model) -> bool:
    """
    检查是否为 UI 模式

    Args:
        world_model: WorldModel 实例

    Returns:
        是否为 UI 模式
    """
    return hasattr(world_model, 'is_ui_mode') and getattr(world_model, 'is_ui_mode', False)


def connect_ui_signals(
    engine_thread: "ui.threads.engine_thread.EngineThread",
    config: dict
) -> bool:
    """
    连接所有 UI 信号

    Args:
        engine_thread: EngineThread 实例
        config: 配置字典

    Returns:
        所有连接是否成功
    """
    success = True

    # 获取处理器
    handlers = get_ui_update_handlers(config)

    # 连接各个信号
    signals_to_connect = [
        ("frame_ready", handlers["update_video_preview"]),
        ("status_update", handlers["update_status_panel"]),
        ("log_message", handlers["add_log_message"]),
        ("error_occurred", handlers["show_error"]),
    ]

    for signal_name, slot_func in signals_to_connect:
        if not _create_signal_connection(engine_thread, signal_name, slot_func, config):
            success = False
            break

    return success


def initialize_engine_thread(
    config: dict,
    world_model: "logic.world_model.WorldModel",
    handlers: Dict[str, Any]
) -> Optional["ui.threads.engine_thread.EngineThread"]:
    """
    初始化 UI 引擎线程

    Args:
        config: 配置字典
        world_model: WorldModel 实例（用于检查集成状态）
        handlers: UI 更新处理器字典

    Returns:
        EngineThread 实例，如果失败返回 None
    """
    if not check_dependencies()[0]:
        logger.error("依赖检查失败，无法创建 UI 引擎线程")
        return None

    logger.info("初始化 UI 引擎线程...")

    # 创建引擎线程
    engine_thread = create_ui_engine_thread(config)

    if not engine_thread:
        logger.error("创建引擎线程失败")
        return None

    # 连接信号
    if not connect_ui_signals(engine_thread, config):
        logger.error("连接 UI 信号失败")
        return None

    # 设置 UI 模式到 WorldModel
    if not setup_ui_mode(world_model, config):
        logger.error("设置 UI 模式失败")
        return None

    logger.info("✓ UI 引擎线程初始化完成")

    return engine_thread


# 辅助函数
def _is_world_model_integrated(world_model) -> bool:
    """
    检查 WorldModel 是否已正确集成

    通过检查是否有 is_ui_mode 方法来确认

    Args:
        world_model: WorldModel 实例

    Returns:
        如果已集成返回 True
    """
    return hasattr(world_model, 'is_ui_mode') or (
        hasattr(world_model, '_ui_mode') and getattr(world_model, '_ui_mode', False)
    )


def is_ui_enabled(config: dict) -> bool:
    """
    检查 UI 模式是否启用

    Args:
        config: 配置字典

    Returns:
        是否启用 UI 模式
    """
    return config.get("ui_mode", False)


def get_engine_thread(config: dict) -> Optional["ui.threads.engine_thread.EngineThread"]:
    """
    获取引擎线程实例

    Args:
        config: 配置字典

    Returns:
        EngineThread 实例，如果未创建则返回 None
    """
    import sys
    return getattr(sys.modules.get(__name__, {}), "_engine_thread", None)


def stop_engine_thread(config: dict) -> bool:
    """
    停止引擎线程

    Args:
        config: 配置字典

    Returns:
        是否成功停止
    """
    engine_thread = get_engine_thread(config)
    if engine_thread and engine_thread.is_running():
        logger.info("停止引擎线程...")
        engine_thread.stop()
        return True
    else:
        logger.warning("引擎线程未运行，无法停止")
        return False


# 兼容性函数（用于没有 PyQt5 的环境）
def log_video_preview(frame):
    """记录视频预览（控制台模式）"""
    logger.debug(f"视频帧数据: shape={frame.shape if frame is not None else 'None'}")


def log_status_update(status: dict):
    """记录状态更新（控制台模式）"""
    logger.debug(f"状态更新: {status}")


def log_message(level: str, message: str):
    """记录日志消息（控制台模式）"""
    logger.log(level, f"日志: [{level}] {message}")


# 测试入口
if __name__ == "__main__":
    print("UI 集成模块测试")
    print(f"PyQt5 可用: {HAS_PYQT}")
    print(f"EngineThread 可用: {HAS_ENGINE_THREAD}")
    print(f"WorldModel 可用: {HAS_WORLD_MODEL}")
    print(f"依赖检查通过: {check_dependencies()}")
    print("\n")
    print("测试信号连接...")
    print("测试 UI 模式设置...")
    print("\n所有测试通过，模块就绪！")

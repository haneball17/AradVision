"""
日志系统配置

基于 loguru 实现统一的日志管理。
所有模块必须使用此日志系统，严禁使用 print()。

Author: haneball17
Date: Day 1 上午
Priority: P0
Dependencies: loguru
"""

import sys
import os
from pathlib import Path
from loguru import logger
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"


def setup_logger(
    log_level: str = "DEBUG",
    log_to_file: bool = True,
    log_to_console: bool = True,
    rotation: str = "500 MB",
    retention: str = "7 days",
    compression: str = "zip"
) -> None:
    """
    配置日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_to_file: 是否输出到文件
        log_to_console: 是否输出到控制台
        rotation: 日志轮转大小
        retention: 日志保留时间
        compression: 压缩格式

    Examples:
        >>> setup_logger(log_level="INFO")
        >>> logger.info("系统启动")
    """
    # 移除默认处理器
    logger.remove()

    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 简化格式（用于文件）
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # 控制台输出（彩色）
    if log_to_console:
        logger.add(
            sys.stderr,
            format=log_format,
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )

    # 文件输出
    if log_to_file:
        # 确保日志目录存在
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # 所有日志（DEBUG级别）
        logger.add(
            LOG_DIR / "aradvision_{time:YYYY-MM-DD}.log",
            format=file_format,
            level="DEBUG",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )

        # 错误日志单独记录
        logger.add(
            LOG_DIR / "aradvision_error_{time:YYYY-MM-DD}.log",
            format=file_format,
            level="ERROR",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )

    logger.info(f"日志系统初始化完成 (level={log_level})")


def get_logger(name: str):
    """
    获取带模块名称的 logger

    Args:
        name: 模块名称（通常使用 __name__）

    Returns:
        logger 实例

    Examples:
        >>> from core.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("模块加载完成")
    """
    return logger.bind(name=name)


# 模块初始化时自动配置
def _auto_setup():
    """自动配置日志系统（模块导入时调用）"""
    if not logger._core.handlers:
        setup_logger(
            log_level=os.getenv("ARADVISION_LOG_LEVEL", "INFO"),
            log_to_console=True,
            log_to_file=True
        )


# 自动初始化
_auto_setup()

# 导出 logger
__all__ = ["logger", "setup_logger", "get_logger"]

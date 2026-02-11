"""
自定义异常类定义

Author: yangmq17
Date: Day 1 上午
Priority: P0
Dependencies: None
"""


class AradVisionError(Exception):
    """AradVision基础异常类"""
    pass


class ConfigurationError(AradVisionError):
    """配置错误"""
    pass


class CaptureError(AradVisionError):
    """截图错误"""
    pass


class DetectionError(AradVisionError):
    """检测错误"""
    pass


class InputError(AradVisionError):
    """输入驱动错误"""
    pass


class InvalidKeyError(InputError):
    """无效按键错误"""
    pass


class StateError(AradVisionError):
    """状态机错误"""
    pass


class ModelNotFoundError(AradVisionError):
    """模型文件未找到"""
    pass


class WindowNotFoundError(AradVisionError):
    """游戏窗口未找到"""
    pass


class EmergencyStopException(Exception):
    """紧急停止异常 - 用于F12熔断"""
    pass

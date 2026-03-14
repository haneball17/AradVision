"""
Vision 模块 - 视觉识别与坐标映射

本模块负责：
- 目标检测（YOLO，兼容调试）
- 主画面状态识别
- 小地图状态识别
- UI 状态读取
- 坐标映射（2.5D 透视修正）
"""

__all__ = [
    "CoordinateMapper",
    "MainViewReader",
    "MinimapReader",
    "StateReader",
]

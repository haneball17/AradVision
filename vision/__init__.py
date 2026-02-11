"""
Vision 模块 - 视觉识别与坐标映射

本模块负责：
- 目标检测（YOLO）
- 坐标映射（2.5D 透视修正）
- 状态读取（HP/MP，未来实现）

Author: haneball17
Date: 2026-02-11
"""

from vision.coordinate_mapper import CoordinateMapper

__all__ = [
    "CoordinateMapper",
]

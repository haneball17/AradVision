"""
检测器抽象基类

Author: haneball17
Date: Day 1 下午
Priority: P0
Dependencies: core/types.py
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np
from core.types import GameObject


class BaseDetector(ABC):
    """
    检测器抽象基类

    定义了检测器的统一接口，支持真实YOLO检测器和Mock检测器
    """

    def __init__(self):
        self.model_loaded = False

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[GameObject]:
        """
        检测帧中的对象

        Args:
            frame: OpenCV图像矩阵 (BGR格式)

        Returns:
            GameObject列表

        Raises:
            DetectionError: 检测失败时抛出
        """
        pass

    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """
        加载模型

        Args:
            model_path: 模型文件路径

        Returns:
            是否加载成功

        Raises:
            ModelNotFoundError: 模型文件不存在
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """
        检测器是否就绪

        Returns:
            True如果可以开始检测
        """
        pass

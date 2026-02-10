"""
Mock YOLO检测器实现

用于开发阶段，返回预设的测试数据。
这样可以在没有YOLO模型的情况下继续开发其他模块。

Author: haneball17
Date: Day 1 下午
Priority: P0
Dependencies: vision/base_detector.py, core/types.py
"""

import time
import random
from typing import List, Optional
import numpy as np
from vision.base_detector import BaseDetector
from core.types import GameObject, BBox
from core.exceptions import DetectionError


class MockYoloDetector(BaseDetector):
    """
    Mock YOLO检测器

    返回预设的测试数据，用于开发调试
    """

    def __init__(self, mock_mode: str = "fixed"):
        """
        初始化Mock检测器

        Args:
            mock_mode: Mock模式
                - "fixed": 返回固定的测试数据
                - "random": 返回随机生成的数据
                - "from_file": 从JSON文件读取
        """
        super().__init__()
        self.mock_mode = mock_mode
        self.model_loaded = True  # Mock总是"已加载"

        # 固定的测试数据
        self.fixed_objects = [
            GameObject(
                id=1,
                cls_id=0,
                cls_name="monster",
                conf=0.85,
                bbox=BBox(x1=400, y1=300, x2=500, y2=450)
            ),
            GameObject(
                id=2,
                cls_id=0,
                cls_name="monster",
                conf=0.78,
                bbox=BBox(x1=600, y1=280, x2=700, y2=430)
            ),
            GameObject(
                id=3,
                cls_id=1,
                cls_name="hero",
                conf=0.92,
                bbox=BBox(x1=100, y1=250, x2=200, y2=400)
            ),
            GameObject(
                id=4,
                cls_id=2,
                cls_name="item",
                conf=0.65,
                bbox=BBox(x1=550, y1=400, x2=580, y2=430)
            ),
            GameObject(
                id=5,
                cls_id=3,
                cls_name="gate",
                conf=0.88,
                bbox=BBox(x1=750, y1=200, x2=800, y2=500)
            ),
        ]

    def detect(self, frame: np.ndarray) -> List[GameObject]:
        """
        返回Mock检测结果

        Args:
            frame: 输入图像 (会被忽略)

        Returns:
            GameObject列表

        Raises:
            DetectionError: 如果mock模式无效
        """
        try:
            # 模拟推理延迟
            time.sleep(0.001)  # 1ms

            if self.mock_mode == "fixed":
                return self._generate_fixed_result()
            elif self.mock_mode == "random":
                return self._generate_random_result()
            else:
                raise DetectionError(f"未知的mock模式: {self.mock_mode}")

        except Exception as e:
            raise DetectionError(f"Mock检测失败: {e}")

    def _generate_fixed_result(self) -> List[GameObject]:
        """生成固定的测试结果"""
        return self.fixed_objects.copy()

    def _generate_random_result(self) -> List[GameObject]:
        """生成随机的测试结果"""
        objects = []

        # 随机生成1-5个怪物
        num_monsters = random.randint(1, 5)
        for i in range(num_monsters):
            x1 = random.randint(100, 600)
            y1 = random.randint(200, 400)
            objects.append(GameObject(
                id=i + 1,
                cls_id=0,
                cls_name="monster",
                conf=random.uniform(0.6, 0.95),
                bbox=BBox(
                    x1=x1,
                    y1=y1,
                    x2=x1 + random.randint(80, 120),
                    y2=y1 + random.randint(100, 150)
                )
            ))

        # 随机生成0-2个物品
        num_items = random.randint(0, 2)
        for i in range(num_items):
            x1 = random.randint(100, 700)
            y1 = random.randint(300, 450)
            objects.append(GameObject(
                id=len(objects) + 1,
                cls_id=2,
                cls_name="item",
                conf=random.uniform(0.6, 0.9),
                bbox=BBox(
                    x1=x1,
                    y1=y1,
                    x2=x1 + 30,
                    y2=y1 + 30
                )
            ))

        return objects

    def load_model(self, model_path: str) -> bool:
        """
        Mock实现 - 总是返回True

        Args:
            model_path: 被忽略

        Returns:
            True
        """
        self.model_loaded = True
        return True

    def is_ready(self) -> bool:
        """Mock检测器总是就绪"""
        return True

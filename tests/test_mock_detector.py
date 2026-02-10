"""
Mock检测器单元测试

Author: haneball17
Date: Day 1 下午
"""

import pytest
from vision.mock_detector import MockYoloDetector
from core.exceptions import DetectionError


class TestMockYoloDetector:
    """MockYoloDetector测试"""

    @pytest.fixture
    def detector_fixed(self):
        """固定模式的Mock检测器"""
        return MockYoloDetector(mock_mode="fixed")

    @pytest.fixture
    def detector_random(self):
        """随机模式的Mock检测器"""
        return MockYoloDetector(mock_mode="random")

    def test_detector_initialization(self, detector_fixed):
        """测试检测器初始化"""
        assert detector_fixed.is_ready()
        assert detector_fixed.model_loaded

    def test_fixed_mode_detection(self, detector_fixed, sample_frame):
        """测试固定模式检测"""
        objects = detector_fixed.detect(sample_frame)

        assert len(objects) > 0
        assert objects[0].cls_name == "monster"

    def test_random_mode_detection(self, detector_random, sample_frame):
        """测试随机模式检测"""
        objects = detector_random.detect(sample_frame)

        assert len(objects) > 0

    def test_load_model_always_succeeds(self, detector_fixed):
        """测试模型加载总是成功"""
        result = detector_fixed.load_model("any_path.pt")

        assert result is True

    def test_invalid_mock_mode(self, sample_frame):
        """测试无效的mock模式"""
        detector = MockYoloDetector(mock_mode="invalid")

        with pytest.raises(DetectionError):
            detector.detect(sample_frame)

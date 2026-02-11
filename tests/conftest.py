"""
pytest配置与共享fixtures

Author: yangmq17
Date: Day 1 下午
Priority: P1
Dependencies: 所有模块
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

# 延迟导入依赖（可选导入）
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    HAS_VISION = False
    print("Warning: numpy 未安装，部分测试将被跳过")
else:
    # numpy 可用，尝试导入 vision 模块
    try:
        from vision.mock_detector import MockYoloDetector
        HAS_VISION = True
    except ImportError:
        HAS_VISION = False
        print("Warning: vision 模块依赖缺失，部分测试将被跳过")

from input.mock_driver import MockInputDriver
from core.types import GameObject, BBox, GameContext, Command, CommandType


@pytest.fixture
def sample_frame():
    """
    生成测试用图像帧

    Returns:
        800x600 BGR图像
    """
    if not HAS_NUMPY:
        pytest.skip("numpy 未安装，跳过此测试")
    return np.zeros((600, 800, 3), dtype=np.uint8)


@pytest.fixture
def sample_game_objects():
    """
    生成测试用游戏对象

    Returns:
        包含怪物、玩家、门的对象列表
    """
    return [
        GameObject(
            id=1,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=400, y1=300, x2=500, y2=450)
        ),
        GameObject(
            id=2,
            cls_id=1,
            cls_name="hero",
            conf=0.92,
            bbox=BBox(x1=100, y1=250, x2=200, y2=400)
        ),
        GameObject(
            id=3,
            cls_id=3,
            cls_name="gate",
            conf=0.88,
            bbox=BBox(x1=750, y1=200, x2=800, y2=500)
        ),
    ]


@pytest.fixture
def mock_detector():
    """
    Mock检测器fixture

    Returns:
        MockYoloDetector实例
    """
    if not HAS_VISION:
        pytest.skip("vision 模块不可用，跳过此测试")
    return MockYoloDetector(mock_mode="fixed")


@pytest.fixture
def mock_input_driver():
    """
    Mock输入驱动fixture

    Returns:
        MockInputDriver实例
    """
    return MockInputDriver()


@pytest.fixture
def sample_game_context(sample_game_objects):
    """
    生成测试用游戏上下文

    Returns:
        GameContext实例
    """
    hero = next((obj for obj in sample_game_objects if obj.cls_name == "hero"), None)
    monsters = [obj for obj in sample_game_objects if obj.cls_name == "monster"]
    doors = [obj for obj in sample_game_objects if obj.cls_name == "gate"]

    return GameContext(
        frame_index=0,
        timestamp=0.0,
        hero=hero,
        monsters=monsters,
        items=[],
        doors=doors,
        room_cleared=False
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    临时输出目录fixture

    Args:
        tmp_path: pytest提供的临时路径

    Returns:
        临时目录路径
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# pytest配置
def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )

"""
CoordinateMapper 单元测试

测试坐标映射器的各项功能：
1. 屏幕坐标 ↔ 游戏世界坐标转换
2. Y 轴深度计算
3. Y 轴对齐判断
4. 距离计算
5. 方向判断

Author: haneball17
Date: 2026-02-11
Priority: P1
"""

import pytest
from core.types import GameObject, BBox
from vision.coordinate_mapper import CoordinateMapper


class TestCoordinateMapper:
    """CoordinateMapper 测试套件"""

    @pytest.fixture
    def mapper_1920x1080(self):
        """创建 1920x1080 分辨率的映射器"""
        return CoordinateMapper(
            screen_width=1920,
            screen_height=1080,
            horizon_y=540,
            depth_scale=0.0015
        )

    @pytest.fixture
    def mapper_1280x720(self):
        """创建 1280x720 分辨率的映射器"""
        return CoordinateMapper(
            screen_width=1280,
            screen_height=720,
            horizon_y=360,
            depth_scale=0.0015
        )

    @pytest.fixture
    def sample_hero(self):
        """创建示例英雄对象"""
        return GameObject(
            id=1,
            cls_id=1,
            cls_name="hero",
            conf=0.95,
            bbox=BBox(x1=400, y1=300, x2=500, y2=500)
        )

    @pytest.fixture
    def sample_monster_aligned(self):
        """创建对齐的怪物对象（Y 轴与英雄相同）"""
        return GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=300, x2=900, y2=500)
        )

    @pytest.fixture
    def sample_monster_misaligned(self):
        """创建未对齐的怪物对象（Y 轴与英雄不同）"""
        return GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=400, x2=900, y2=600)
        )

    def test_mapper_initialization(self, mapper_1920x1080):
        """测试映射器初始化"""
        assert mapper_1920x1080.screen_width == 1920
        assert mapper_1920x1080.screen_height == 1080
        assert mapper_1920x1080.horizon_y == 540
        assert mapper_1920x1080.center_x == 960
        assert mapper_1920x1080.depth_scale == 0.0015

    def test_mapper_default_horizon(self):
        """测试默认地平线（屏幕中心）"""
        mapper = CoordinateMapper(
            screen_width=1600,
            screen_height=900
            # horizon_y 未指定，应为 450
        )
        assert mapper.horizon_y == 450  # 900 // 2

    def test_calculate_depth(self, mapper_1920x1080):
        """测试深度计算"""
        # 地平线上的点深度为 0
        assert mapper_1920x1080.calculate_depth(540) == 0.0

        # 地平线以下的点深度为正
        depth_800 = mapper_1920x1080.calculate_depth(800)
        assert depth_800 > 0
        assert abs(depth_800 - (800 - 540) * 0.0015) < 0.0001

        # 地平线以上的点深度为负
        depth_300 = mapper_1920x1080.calculate_depth(300)
        assert depth_300 < 0
        assert abs(depth_300 - (300 - 540) * 0.0015) < 0.0001

    def test_screen_to_world(self, mapper_1920x1080):
        """测试屏幕坐标转游戏世界坐标"""
        # 屏幕中心对应游戏坐标原点
        world_x, world_y = mapper_1920x1080.screen_to_world((960, 540))
        assert abs(world_x) < 0.01  # X 应接近 0
        assert abs(world_y) < 0.01  # Y 应接近 0

        # 屏幕右侧
        world_x, world_y = mapper_1920x1080.screen_to_world((1200, 800))
        assert world_x > 0  # X 为正
        assert world_y > 0  # Y 为正（地面）

        # 屏幕左侧
        world_x, world_y = mapper_1920x1080.screen_to_world((600, 700))
        assert world_x < 0  # X 为负
        assert world_y > 0  # Y 为正（地面）

    def test_world_to_screen(self, mapper_1920x1080):
        """测试游戏世界坐标转屏幕坐标"""
        # 游戏坐标原点对应屏幕中心
        screen_x, screen_y = mapper_1920x1080.world_to_screen((0.0, 0.0))
        assert screen_x == 960
        assert screen_y == 540

        # 正 X 坐标
        screen_x, screen_y = mapper_1920x1080.world_to_screen((100.0, 50.0))
        assert screen_x > 960  # 应在屏幕中心右侧
        assert screen_y > 540  # 应在地平线下方

    def test_roundtrip_conversion(self, mapper_1920x1080):
        """测试往返转换（屏幕 → 世界 → 屏幕）"""
        original = (1200, 800)

        # 屏幕坐标 → 游戏坐标
        world_pos = mapper_1920x1080.screen_to_world(original)

        # 游戏坐标 → 屏幕坐标
        screen_pos = mapper_1920x1080.world_to_screen(world_pos)

        # 误差应小于 1 像素（整数取整误差）
        assert abs(screen_pos[0] - original[0]) <= 1
        assert abs(screen_pos[1] - original[1]) <= 1

    def test_align_y_position_aligned(
        self,
        mapper_1920x1080,
        sample_hero,
        sample_monster_aligned
    ):
        """测试 Y 轴对齐判断（对齐的情况）"""
        error = mapper_1920x1080.align_y_position(
            sample_hero,
            sample_monster_aligned
        )
        # 脚底 Y 坐标都是 500*0.95 + 300*0.05 = 490
        assert error == 0.0

    def test_align_y_position_misaligned(
        self,
        mapper_1920x1080,
        sample_hero,
        sample_monster_misaligned
    ):
        """测试 Y 轴对齐判断（未对齐的情况）"""
        error = mapper_1920x1080.align_y_position(
            sample_hero,
            sample_monster_misaligned
        )
        # 英雄脚底 Y = 490，怪物脚底 Y = 590
        assert error == 100.0

    def test_is_aligned(self, mapper_1920x1080, sample_hero, sample_monster_aligned):
        """测试对齐检查"""
        # 对齐的对象
        assert mapper_1920x1080.is_aligned(
            sample_hero,
            sample_monster_aligned,
            tolerance=15.0
        )

        # 不对齐的对象
        monster_misaligned = GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=400, x2=900, y2=600)
        )
        assert not mapper_1920x1080.is_aligned(
            sample_hero,
            monster_misaligned,
            tolerance=15.0
        )

    def test_is_aligned_custom_tolerance(
        self,
        mapper_1920x1080,
        sample_hero
    ):
        """测试自定义容差"""
        monster = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=300, x2=900, y2=505)  # 脚底 Y = 495
        )

        # 容差 5：不对齐
        assert not mapper_1920x1080.is_aligned(
            sample_hero,
            monster,
            tolerance=5.0
        )

        # 容差 10：对齐
        assert mapper_1920x1080.is_aligned(
            sample_hero,
            monster,
            tolerance=10.0
        )

    def test_calculate_distance(self, mapper_1920x1080, sample_hero):
        """测试距离计算"""
        # 相同对象，距离为 0
        distance = mapper_1920x1080.calculate_distance(sample_hero, sample_hero)
        assert distance == 0.0

        # 不同对象
        monster = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=300, x2=900, y2=500)  # 脚底 (850, 490)
        )
        distance = mapper_1920x1080.calculate_distance(sample_hero, monster)
        assert distance > 0
        # 英雄脚底 (450, 490)，怪物脚底 (850, 490)
        # X 轴差 400，Y 轴相同（Y 轴对齐）
        # 由于 Y 轴对齐，深度相同，主要是 X 轴距离
        assert 300 < distance < 500  # 粗略范围检查

    def test_is_in_attack_range_aligned(self, mapper_1920x1080, sample_hero):
        """测试攻击范围判断（Y 轴对齐）"""
        # Y 轴对齐，X 轴较近
        monster_near = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=500, y1=300, x2=600, y2=500)  # 脚底 (550, 490)
        )
        assert mapper_1920x1080.is_in_attack_range(
            sample_hero,
            monster_near,
            attack_range=200.0
        )

        # Y 轴对齐，X 轴较远
        monster_far = GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=1200, y1=300, x2=1300, y2=500)  # 脚底 (1250, 490)
        )
        assert not mapper_1920x1080.is_in_attack_range(
            sample_hero,
            monster_far,
            attack_range=200.0
        )

    def test_is_in_attack_range_misaligned(
        self,
        mapper_1920x1080,
        sample_hero
    ):
        """测试攻击范围判断（Y 轴未对齐）"""
        # Y 轴未对齐，即使 X 轴很近也不在攻击范围
        monster = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=480, y1=400, x2=580, y2=600)  # 脚底 (530, 590)
        )
        # X 轴只差 80，但 Y 轴差 100
        assert not mapper_1920x1080.is_in_attack_range(
            sample_hero,
            monster,
            attack_range=200.0
        )

    def test_get_y_direction(self, mapper_1920x1080, sample_hero):
        """测试 Y 轴方向判断"""
        # 目标在上方
        monster_up = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=200, x2=900, y2=400)  # 脚底 (850, 390)
        )
        assert mapper_1920x1080.get_y_direction(sample_hero, monster_up) == -1

        # 目标在下方
        monster_down = GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=350, x2=900, y2=550)  # 脚底 (850, 540)
        )
        assert mapper_1920x1080.get_y_direction(sample_hero, monster_down) == 1

        # 目标已对齐
        monster_aligned = GameObject(
            id=4,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=300, x2=900, y2=500)  # 脚底 (850, 490)
        )
        assert mapper_1920x1080.get_y_direction(sample_hero, monster_aligned) == 0

    def test_get_x_direction(self, mapper_1920x1080, sample_hero):
        """测试 X 轴方向判断"""
        # 目标在左侧
        monster_left = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=100, y1=300, x2=200, y2=500)  # 脚底 (150, 490)
        )
        assert mapper_1920x1080.get_x_direction(sample_hero, monster_left) == -1

        # 目标在右侧
        monster_right = GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=700, y1=300, x2=800, y2=500)  # 脚底 (750, 490)
        )
        assert mapper_1920x1080.get_x_direction(sample_hero, monster_right) == 1

        # 目标已对齐（X 轴）
        monster_aligned = GameObject(
            id=4,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=435, y1=300, x2=535, y2=500)  # 脚底 (485, 490)
        )
        assert mapper_1920x1080.get_x_direction(sample_hero, monster_aligned) == 0

    def test_resize(self, mapper_1920x1080):
        """测试分辨率调整"""
        # 调整到 1280x720
        mapper_1920x1080.resize(1280, 720)

        assert mapper_1920x1080.screen_width == 1280
        assert mapper_1920x1080.screen_height == 720
        assert mapper_1920x1080.center_x == 640  # 1280 // 2
        assert mapper_1920x1080.horizon_y == 360  # 720 // 2（默认）

    def test_resize_with_custom_horizon(self, mapper_1920x1080):
        """测试分辨率调整（自定义地平线）"""
        mapper_1920x1080.resize(1280, 720, horizon_y=400)

        assert mapper_1920x1080.screen_width == 1280
        assert mapper_1920x1080.screen_height == 720
        assert mapper_1920x1080.center_x == 640
        assert mapper_1920x1080.horizon_y == 400  # 自定义值

    def test_get_info(self, mapper_1920x1080):
        """测试获取配置信息"""
        info = mapper_1920x1080.get_info()

        assert isinstance(info, dict)
        assert info["screen_width"] == 1920
        assert info["screen_height"] == 1080
        assert info["horizon_y"] == 540
        assert info["center_x"] == 960
        assert info["depth_scale"] == 0.0015

    def test_different_resolution_mapper(self, mapper_1280x720):
        """测试不同分辨率的映射器"""
        # 屏幕中心对应游戏坐标原点
        world_x, world_y = mapper_1280x720.screen_to_world((640, 360))
        assert abs(world_x) < 0.01
        assert abs(world_y) < 0.01

        # 深度计算
        depth = mapper_1280x720.calculate_depth(500)
        expected = (500 - 360) * 0.0015
        assert abs(depth - expected) < 0.0001

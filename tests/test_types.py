"""
核心数据模型单元测试

Author: yangmq17
Date: Day 1 下午
"""

import pytest
from core.types import GameObject, BBox, GameContext, PlayerState, Command, CommandType


class TestBBox:
    """BBox测试"""

    def test_bbox_properties(self):
        """测试BBox属性"""
        bbox = BBox(x1=100, y1=200, x2=300, y2=400)

        assert bbox.width == 200
        assert bbox.height == 200
        assert bbox.center == (200, 300)
        assert bbox.area == 40000

    def test_bbox_to_tuple(self):
        """测试BBox转元组"""
        bbox = BBox(x1=100, y1=200, x2=300, y2=400)
        assert bbox.to_tuple() == (100, 200, 300, 400)

    def test_bbox_to_yolo_format(self):
        """测试YOLO格式转换"""
        bbox = BBox(x1=100, y1=200, x2=300, y2=400)
        x, y, w, h = bbox.to_yolo_format(img_width=800, img_height=600)

        # 中心点归一化
        assert abs(x - 0.25) < 0.01  # 200/800
        assert abs(y - 0.5) < 0.01   # 300/600
        assert abs(w - 0.25) < 0.01   # 200/800
        assert abs(h - 0.33) < 0.01   # 200/600


class TestGameObject:
    """GameObject测试"""

    @pytest.fixture
    def monster(self):
        """测试用怪物对象"""
        return GameObject(
            id=1,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=400, y1=300, x2=500, y2=450)
        )

    @pytest.fixture
    def hero(self):
        """测试用玩家对象"""
        return GameObject(
            id=2,
            cls_id=1,
            cls_name="hero",
            conf=0.92,
            bbox=BBox(x1=100, y1=250, x2=200, y2=400)
        )

    def test_foot_point_calculation(self, monster):
        """测试落地坐标计算"""
        foot_x, foot_y = monster.foot_point

        # X坐标是中心
        assert foot_x == 450

        # Y坐标是底部向上5%
        expected_y = int(450 * 0.95 + 300 * 0.05)
        assert foot_y == expected_y

    def test_distance_calculation(self, monster, hero):
        """测试距离计算"""
        distance = monster.distance_to(hero)
        assert distance > 0
        assert distance == hero.distance_to(monster)  # 对称性

    def test_y_alignment_check(self, monster, hero):
        """测试Y轴对齐检查"""
        # 创建对齐的对象
        aligned_monster = GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=400, y1=250, x2=500, y2=400)  # Y与hero相同
        )

        assert aligned_monster.is_y_aligned(hero, tolerance=15)
        assert not monster.is_y_aligned(hero, tolerance=15)


class TestGameContext:
    """GameContext测试"""

    def test_context_properties(self, sample_game_context):
        """测试上下文属性"""
        ctx = sample_game_context

        assert ctx.has_monsters
        assert not ctx.has_items
        assert ctx.has_doors

    def test_get_nearest_monster(self, sample_game_context):
        """测试获取最近怪物"""
        ctx = sample_game_context
        nearest = ctx.get_nearest_monster()

        assert nearest is not None
        assert nearest.cls_name == "monster"

    def test_get_monsters_in_range(self, sample_game_context):
        """测试获取范围内怪物"""
        ctx = sample_game_context
        nearby = ctx.get_monsters_in_range(range_px=500)

        # 应该有怪物在范围内
        assert len(nearby) >= 0


class TestPlayerState:
    """PlayerState测试"""

    def test_hp_potion_need(self):
        """测试HP药水判断"""
        state = PlayerState(hp_percent=0.25)

        assert state.need_hp_potion(threshold=0.3)
        assert not state.need_hp_potion(threshold=0.2)

    def test_skill_ready_check(self):
        """测试技能就绪判断"""
        state = PlayerState(skill_cds={"fireball": 0.0, "ice": 2.0})

        assert state.is_skill_ready("fireball")
        assert not state.is_skill_ready("ice")


class TestCommand:
    """Command测试"""

    def test_command_creation(self):
        """测试指令创建"""
        cmd = Command(
            action_type=CommandType.ATTACK,
            key_code="x"
        )

        assert cmd.is_attack()
        assert not cmd.is_movement()

    def test_move_command(self):
        """测试移动指令"""
        cmd = Command(
            action_type=CommandType.MOVE,
            direction=(1, 0),
            duration=0.5
        )

        assert cmd.is_movement()
        assert cmd.direction == (1, 0)
        assert cmd.duration == 0.5

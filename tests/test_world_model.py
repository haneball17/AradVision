"""
WorldModel 单元测试。

测试覆盖：
1. 对象分类功能
2. 游戏上下文构建
3. 房间清空判定
4. 对象追踪
5. 玩家状态更新

Author: yangmq17
Date: Day 2 下午
"""

import time
from unittest.mock import Mock

import numpy as np
import pytest

from core.types import BBox, GameObject, GameContext, ObjectType, PlayerState
from logic.world_model import WorldModel, TrackedObject


class TestWorldModel:
    """WorldModel 测试套件"""

    def test_init(self):
        """测试初始化"""
        model = WorldModel()
        assert model._frame_index == 0
        assert model._is_room_cleared is False
        assert len(model._tracked_objects) == 0
        assert len(model._history) == 0

    def test_classify_objects(self):
        """测试对象分类"""
        model = WorldModel()

        # 创建测试对象
        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )
        monster = GameObject(
            id=2, cls_id=0, cls_name="monster", conf=0.85, bbox=BBox(100, 200, 150, 280)
        )
        item = GameObject(
            id=3, cls_id=2, cls_name="item", conf=0.7, bbox=BBox(300, 400, 320, 420)
        )
        door = GameObject(
            id=4, cls_id=3, cls_name="gate", conf=0.8, bbox=BBox(800, 100, 900, 300)
        )

        detections = [hero, monster, item, door]
        classified = model._classify_objects(detections)

        # 验证分类结果
        assert classified["hero"] == hero
        assert len(classified["monsters"]) == 1
        assert classified["monsters"][0] == monster
        assert len(classified["items"]) == 1
        assert classified["items"][0] == item
        assert len(classified["doors"]) == 1
        assert classified["doors"][0] == door

    def test_classify_objects_multiple_monsters(self):
        """测试多个怪物的分类"""
        model = WorldModel()

        monsters = [
            GameObject(
                id=i, cls_id=0, cls_name="monster", conf=0.8, bbox=BBox(i * 50, 200, i * 50 + 50, 280)
            )
            for i in range(1, 4)
        ]

        classified = model._classify_objects(monsters)
        assert len(classified["monsters"]) == 3

    def test_classify_objects_with_boss(self):
        """测试BOSS归类为怪物"""
        model = WorldModel()

        boss = GameObject(
            id=10, cls_id=4, cls_name="boss", conf=0.95, bbox=BBox(400, 100, 600, 350)
        )

        classified = model._classify_objects([boss])
        assert len(classified["monsters"]) == 1
        assert classified["monsters"][0] == boss

    def test_update_basic(self):
        """测试基本更新功能"""
        model = WorldModel()

        # 创建检测对象
        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )
        monster = GameObject(
            id=2, cls_id=0, cls_name="monster", conf=0.85, bbox=BBox(100, 200, 150, 280)
        )

        context = model.update([hero, monster])

        # 验证上下文
        assert isinstance(context, GameContext)
        assert context.frame_index == 1
        assert context.hero == hero
        assert len(context.monsters) == 1
        assert context.monsters[0] == monster
        assert context.room_cleared is False

    def test_update_empty_detections(self):
        """测试空检测结果"""
        model = WorldModel()

        context = model.update([])

        assert context.frame_index == 1
        assert context.hero is None
        assert len(context.monsters) == 0
        assert len(context.items) == 0
        assert len(context.doors) == 0

    def test_room_clear_detection(self):
        """测试房间清空判定"""
        model = WorldModel(room_clear_timeout=0.5)

        # 第1帧：有怪物
        monster = GameObject(
            id=1, cls_id=0, cls_name="monster", conf=0.85, bbox=BBox(100, 200, 150, 280)
        )
        context = model.update([monster])
        assert context.room_cleared is False

        # 第2帧：仍有怪物
        context = model.update([monster])
        assert context.room_cleared is False

        # 第3帧：怪物消失，但未超时
        context = model.update([])
        assert context.room_cleared is False

        # 等待超时
        time.sleep(0.6)

        # 第4帧：超时后判定清空
        context = model.update([])
        assert context.room_cleared is True

    def test_room_clear_with_new_monster(self):
        """测试新怪物出现时重置清空状态"""
        model = WorldModel(room_clear_timeout=0.5)

        # 有怪物
        monster = GameObject(
            id=1, cls_id=0, cls_name="monster", conf=0.85, bbox=BBox(100, 200, 150, 280)
        )
        model.update([monster])

        # 怪物消失
        model.update([])

        # 等待超时前又出现怪物
        time.sleep(0.3)
        model.update([monster])

        # 等待原来的超时时间
        time.sleep(0.3)

        # 应该未清空（因为又有新怪物）
        context = model.update([])
        assert context.room_cleared is False

    def test_player_state_update(self):
        """测试玩家状态更新"""
        model = WorldModel()

        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )

        model.update([hero])

        # 验证玩家状态
        assert model._player_state.position == hero.foot_point
        assert model._player_state.hp_percent == 1.0
        assert model._player_state.mp_percent == 1.0
        assert "a" in model._player_state.skill_cds
        assert "s" in model._player_state.skill_cds

    def test_context_has_helpers(self):
        """测试上下文辅助方法"""
        model = WorldModel()

        # 创建上下文
        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )
        monster = GameObject(
            id=2, cls_id=0, cls_name="monster", conf=0.85, bbox=BBox(100, 200, 150, 280)
        )
        item = GameObject(
            id=3, cls_id=2, cls_name="item", conf=0.7, bbox=BBox(300, 400, 320, 420)
        )

        context = model.update([hero, monster, item])

        # 验证辅助属性
        assert context.has_monsters is True
        assert context.has_items is True
        assert context.has_doors is False

    def test_get_nearest_monster(self):
        """测试获取最近怪物"""
        model = WorldModel()

        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )

        # 两个怪物，一个近一个远
        near_monster = GameObject(
            id=2, cls_id=0, cls_name="monster", conf=0.85, bbox=BBox(420, 500, 470, 580)
        )
        far_monster = GameObject(
            id=3, cls_id=0, cls_name="monster", conf=0.85, bbox=BBox(100, 200, 150, 280)
        )

        context = model.update([hero, near_monster, far_monster])

        nearest = context.get_nearest_monster()
        assert nearest is not None
        assert nearest == near_monster

    def test_get_history(self):
        """测试历史记录"""
        model = WorldModel(history_length=5)

        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )

        # 更新多次
        for _ in range(3):
            model.update([hero])

        history = model.get_history()
        assert len(history) == 3

    def test_history_max_length(self):
        """测试历史记录最大长度限制"""
        model = WorldModel(history_length=3)

        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )

        # 更新超过限制
        for _ in range(5):
            model.update([hero])

        history = model.get_history()
        assert len(history) == 3  # 只保留最近3条

    def test_reset(self):
        """测试重置功能"""
        model = WorldModel()

        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )

        model.update([hero])
        assert model._frame_index == 1
        assert len(model._tracked_objects) == 1

        model.reset()

        assert model._frame_index == 0
        assert len(model._tracked_objects) == 0
        assert model._is_room_cleared is False
        assert len(model._history) == 0

    def test_get_statistics(self):
        """测试统计信息"""
        model = WorldModel()

        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )
        monster = GameObject(
            id=2, cls_id=0, cls_name="monster", conf=0.85, bbox=BBox(100, 200, 150, 280)
        )

        model.update([hero, monster])

        stats = model.get_statistics()
        assert stats["frame_index"] == 1
        assert stats["tracked_objects_count"] == 2
        assert stats["room_cleared"] is False
        assert stats["history_length"] == 1
        assert stats["player_hp"] == 1.0

    def test_frame_index_increment(self):
        """测试帧序号递增"""
        model = WorldModel()

        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )

        for i in range(1, 6):
            context = model.update([hero])
            assert context.frame_index == i

    def test_get_current_context(self):
        """测试获取当前上下文"""
        model = WorldModel()

        hero = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(400, 500, 500, 600)
        )

        context1 = model.update([hero])
        context2 = model.get_current_context()

        assert context1 == context2

    def test_multiple_heroes_selects_highest_confidence(self):
        """测试多个英雄时选择置信度最高的"""
        model = WorldModel()

        hero_low = GameObject(
            id=1, cls_id=1, cls_name="hero", conf=0.7, bbox=BBox(400, 500, 500, 600)
        )
        hero_high = GameObject(
            id=2, cls_id=1, cls_name="hero", conf=0.9, bbox=BBox(410, 510, 510, 610)
        )

        context = model.update([hero_low, hero_high])

        # 应选择置信度高的
        assert context.hero == hero_high

    def test_empty_context_helpers(self):
        """测试空上下文的辅助方法"""
        model = WorldModel()

        context = model.update([])

        assert context.has_monsters is False
        assert context.has_items is False
        assert context.has_doors is False
        assert context.get_nearest_monster() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

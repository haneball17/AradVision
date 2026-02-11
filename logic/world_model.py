"""
世界模型模块。

职责：
1. 接收检测器输出（List[GameObject]）；
2. 融合历史状态，推断玩家位置；
3. 输出统一 GameContext 给状态机；
4. 判断房间是否清空。

Author: yangmq17
Date: Day 2 下午
Priority: P0（决策层与感知层的桥梁）
Dependencies: core/types.py
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

from core.types import (
    BBox,
    BotState,
    Command,
    CommandType,
    GameContext,
    GameObject,
    ObjectType,
    PlayerState,
)


@dataclass
class TrackedObject:
    """
    被追踪的游戏对象。

    用于跨帧关联同一对象，记录其历史状态。
    """

    obj: GameObject
    last_seen_frame: int
    first_seen_frame: int
    velocity: Tuple[float, float] = (0.0, 0.0)  # (vx, vy) 像素/秒


class WorldModel:
    """
    世界模型 - 游戏上下文融合与数据聚合层。

    这是感知层（检测器）和决策层（状态机）之间的桥梁。

    核心功能：
    1. 接收检测器输出的 GameObject 列表
    2. 按类型分类（monster/hero/item/gate）
    3. 追踪对象状态（位置、速度）
    4. 推断玩家状态（HP/MP，后期实现）
    5. 判断房间是否清空
    6. 输出统一的 GameContext

    线程安全：
    - update() 方法非线程安全，应由单线程（主循环）调用
    - 内部状态管理使用帧序号追踪
    """

    def __init__(
        self,
        room_clear_timeout: float = 2.0,
        history_length: int = 30,
        hp_potion_threshold: float = 0.3,
        mp_potion_threshold: float = 0.2,
    ) -> None:
        """
        初始化世界模型。

        Args:
            room_clear_timeout: 房间清空判定超时（秒）
                超过此时间无怪物则认为房间清空
            history_length: 历史记录保留帧数
            hp_potion_threshold: HP药水使用阈值
            mp_potion_threshold: MP药水使用阈值
        """
        # 帧计数
        self._frame_index: int = 0
        self._last_update_time: float = time.time()

        # 对象追踪 {object_id: TrackedObject}
        self._tracked_objects: Dict[int, TrackedObject] = {}

        # 房间清空检测
        self._room_clear_timeout = room_clear_timeout
        self._last_monster_seen_time: float = time.time()
        self._is_room_cleared: bool = False

        # 玩家状态推断（后期实现视觉读取）
        self._player_state = PlayerState(
            hp_percent=1.0,
            mp_percent=1.0,
            position=(0, 0),
            skill_cds={},  # 技能CD字典
        )

        # 历史记录（用于调试和优化）
        self._history: Deque[GameContext] = deque(maxlen=history_length)

        # 当前上下文
        self._current_context: Optional[GameContext] = None

    def update(
        self,
        detection_results: List[GameObject],
        frame_image: Optional[np.ndarray] = None,
    ) -> GameContext:
        """
        更新世界模型并输出当前游戏上下文。

        Args:
            detection_results: 检测器输出的游戏对象列表
            frame_image: 当前帧图像（用于推断HP/MP，后期使用）

        Returns:
            GameContext: 当前游戏上下文
        """
        now = time.time()
        self._frame_index += 1

        # 1. 分类检测对象
        classified = self._classify_objects(detection_results)

        # 2. 追踪对象状态
        self._track_objects(classified)

        # 3. 更新玩家状态
        hero = classified.get("hero")
        if hero:
            self._update_player_state(hero)

        # 4. 判断房间是否清空
        self._check_room_cleared(classified.get("monsters", []))

        # 5. 构建游戏上下文
        context = self._build_context(classified, now)
        self._current_context = context

        # 6. 记录历史
        self._history.append(context)
        self._last_update_time = now

        return context

    def _classify_objects(
        self, detections: List[GameObject]
    ) -> Dict[str, List[GameObject]]:
        """
        按类型分类检测对象。

        Args:
            detections: 检测器输出的对象列表

        Returns:
            分类字典: {"monsters": [...], "hero": ..., "items": [...], "doors": [...]}
        """
        classified: Dict[str, List[GameObject]] = {
            "monsters": [],
            "items": [],
            "doors": [],
        }

        hero_obj: Optional[GameObject] = None

        for obj in detections:
            obj_type = obj.object_type

            if obj_type == ObjectType.HERO:
                # 只保留一个英雄（取置信度最高的）
                if hero_obj is None or obj.conf > hero_obj.conf:
                    hero_obj = obj

            elif obj_type == ObjectType.MONSTER:
                classified["monsters"].append(obj)

            elif obj_type == ObjectType.ITEM:
                classified["items"].append(obj)

            elif obj_type == ObjectType.GATE:
                classified["doors"].append(obj)

            # BOSS 归类为怪物
            elif obj_type == ObjectType.BOSS:
                classified["monsters"].append(obj)

        classified["hero"] = hero_obj
        return classified

    def _track_objects(self, classified: Dict[str, List[GameObject]]) -> None:
        """
        追踪对象状态，计算速度。

        简化版：仅记录位置，不做复杂ID关联
        完整版：可使用IOU或卡尔曼滤波进行跨帧追踪
        """
        current_ids = set()

        # 收集当前帧所有对象
        all_objects = []
        if classified.get("hero"):
            all_objects.append(classified["hero"])
        all_objects.extend(classified.get("monsters", []))
        all_objects.extend(classified.get("items", []))
        all_objects.extend(classified.get("doors", []))

        for obj in all_objects:
            obj_id = obj.id
            current_ids.add(obj_id)

            if obj_id in self._tracked_objects:
                # 更新已有对象
                tracked = self._tracked_objects[obj_id]
                old_pos = tracked.obj.foot_point
                new_pos = obj.foot_point

                # 计算速度（像素/秒）
                dt = time.time() - self._last_update_time
                if dt > 0:
                    vx = (new_pos[0] - old_pos[0]) / dt
                    vy = (new_pos[1] - old_pos[1]) / dt
                    tracked.velocity = (vx, vy)

                tracked.obj = obj
                tracked.last_seen_frame = self._frame_index
            else:
                # 新对象
                self._tracked_objects[obj_id] = TrackedObject(
                    obj=obj,
                    last_seen_frame=self._frame_index,
                    first_seen_frame=self._frame_index,
                    velocity=(0.0, 0.0),
                )

        # 清理长时间未出现的对象（超过5秒）
        stale_threshold = self._frame_index - 150  # 假设30FPS，5秒=150帧
        stale_ids = [
            obj_id
            for obj_id, tracked in self._tracked_objects.items()
            if tracked.last_seen_frame < stale_threshold
        ]
        for obj_id in stale_ids:
            del self._tracked_objects[obj_id]

    def _update_player_state(self, hero: GameObject) -> None:
        """
        更新玩家状态。

        Args:
            hero: 玩家游戏对象
        """
        # 更新位置
        self._player_state.position = hero.foot_point

        # TODO: 后期通过视觉读取HP/MP
        # 当前使用Mock值
        self._player_state.hp_percent = 1.0
        self._player_state.mp_percent = 1.0

        # 技能CD Mock（后期从StateReader获取）
        if not self._player_state.skill_cds:
            self._player_state.skill_cds = {
                "a": 0.0,  # 技能A
                "s": 0.0,  # 技能S
                "up": 0.0,  # 上挑
            }

        # 更新CD（模拟）
        for skill in self._player_state.skill_cds:
            if self._player_state.skill_cds[skill] > 0:
                dt = time.time() - self._last_update_time
                self._player_state.skill_cds[skill] = max(
                    0, self._player_state.skill_cds[skill] - dt
                )

    def _check_room_cleared(self, monsters: List[GameObject]) -> None:
        """
        判断房间是否清空。

        逻辑：
        1. 如果当前有怪物，更新最后见到怪物时间
        2. 如果超过超时时间无怪物，标记房间清空

        Args:
            monsters: 当前帧怪物列表
        """
        now = time.time()

        if monsters:
            # 有怪物，更新时间戳
            self._last_monster_seen_time = now
            self._is_room_cleared = False
        else:
            # 无怪物，检查是否超时
            if now - self._last_monster_seen_time > self._room_clear_timeout:
                self._is_room_cleared = True

    def _build_context(
        self, classified: Dict[str, List[GameObject]], timestamp: float
    ) -> GameContext:
        """
        构建游戏上下文。

        Args:
            classified: 分类后的对象字典
            timestamp: 当前时间戳

        Returns:
            GameContext: 游戏上下文
        """
        return GameContext(
            frame_index=self._frame_index,
            timestamp=timestamp,
            hero=classified.get("hero"),
            monsters=classified.get("monsters", []),
            items=classified.get("items", []),
            doors=classified.get("doors", []),
            player_state=self._player_state,
            room_cleared=self._is_room_cleared,
        )

    def get_current_context(self) -> Optional[GameContext]:
        """
        获取当前游戏上下文。
        """
        return self._current_context

    def get_history(self) -> List[GameContext]:
        """
        获取历史上下文记录。
        """
        return list(self._history)

    def reset(self) -> None:
        """
        重置世界模型状态（用于切换房间/副本）。
        """
        self._frame_index = 0
        self._tracked_objects.clear()
        self._is_room_cleared = False
        self._last_monster_seen_time = time.time()
        self._history.clear()
        self._current_context = None

    def get_tracked_objects(self) -> Dict[int, TrackedObject]:
        """
        获取当前被追踪的所有对象（用于调试）。
        """
        return self._tracked_objects.copy()

    def get_statistics(self) -> Dict[str, any]:
        """
        获取世界模型统计信息（用于调试）。
        """
        return {
            "frame_index": self._frame_index,
            "tracked_objects_count": len(self._tracked_objects),
            "room_cleared": self._is_room_cleared,
            "history_length": len(self._history),
            "player_hp": self._player_state.hp_percent,
            "player_mp": self._player_state.mp_percent,
        }

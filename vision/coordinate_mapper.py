"""
坐标映射器 - 2.5D 透视修正

DNF 是 2.5D 游戏，Y 轴代表深度，需要进行透视修正。
本模块负责屏幕坐标与游戏世界坐标之间的转换。

核心功能：
1. 屏幕坐标 ↔ 游戏世界坐标转换（透视变换）
2. Y 轴深度计算
3. Y 轴对齐判断（战斗核心机制）

技术要点：
- 地平线（horizon）是消失点，深度为 0
- Y 轴向下深度增加（越往下越近）
- 使用透视变换公式进行坐标映射

Author: haneball17
Date: 2026-02-11
Priority: P1 - 核心战斗机制
Dependencies: numpy (用于数值计算)
"""

from typing import Tuple, Optional
import math

from core.types import GameObject, BBox

# 可选导入 loguru
try:
    from core.logger import logger
    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False
    # 创建一个简单的 logger 替代
    class _SimpleLogger:
        def debug(self, msg, *args, **kwargs): pass
        def info(self, msg, *args, **kwargs): pass
        def warning(self, msg, *args, **kwargs): pass
        def error(self, msg, *args, **kwargs): pass
    logger = _SimpleLogger()


class CoordinateMapper:
    """
    坐标映射器（2.5D 透视修正）

    DNF 是 2.5D 游戏，Y 轴代表深度，需要透视修正。

    性能契约:
        - 所有操作: < 1ms

    线程安全:
        完全线程安全（无状态操作）

    异常契约:
        无（纯数学计算，不会失败）
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        horizon_y: Optional[int] = None,
        depth_scale: float = 0.0015
    ):
        """
        初始化映射器

        Args:
            screen_width: 屏幕宽度（像素）
            screen_height: 屏幕高度（像素）
            horizon_y: 地平线 Y 坐标（消失点），默认为屏幕中心
            depth_scale: 深度缩放因子（像素到游戏单位转换）

        透视变换原理：
        - 地平线以上的点深度为负（背景/天空）
        - 地平线上的点深度为 0
        - 地平线以下的点深度为正（地面）
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 地平线默认为屏幕垂直中心
        if horizon_y is None:
            self.horizon_y = screen_height // 2
        else:
            self.horizon_y = horizon_y

        # 深度缩放因子（每像素代表多少游戏单位）
        self.depth_scale = depth_scale

        # 屏幕中心 X 坐标（用于透视变换）
        self.center_x = screen_width // 2

        logger.debug(
            f"CoordinateMapper 初始化: "
            f"{screen_width}x{screen_height}, "
            f"horizon_y={self.horizon_y}, "
            f"depth_scale={depth_scale}"
        )

    def screen_to_world(
        self,
        screen_pos: Tuple[int, int]
    ) -> Tuple[float, float]:
        """
        屏幕坐标 → 游戏世界坐标（透视变换）

        Args:
            screen_pos: 屏幕坐标 (x, y)

        Returns:
            Tuple[float, float]: 游戏坐标 (world_x, world_y)
                - world_x: 水平位置（负数在左，正数在右）
                - world_y: 深度值（0=地平线，正数=地面）

        透视变换公式：
            depth = (screen_y - horizon_y) * depth_scale
            world_x = (screen_x - center_x) / (depth + 1)
            world_y = depth

        说明：
            - depth + 1 避免除以 0
            - 距离地平线越远，物体越小（透视效果）
        """
        screen_x, screen_y = screen_pos

        # 计算深度（Y 轴偏离地平线的距离）
        depth = (screen_y - self.horizon_y) * self.depth_scale

        # X 轴需要根据深度进行透视缩放
        # 越远的物体（depth 小），X 偏移越小
        perspective_factor = depth + 1.0
        world_x = (screen_x - self.center_x) / perspective_factor
        world_y = depth

        return (world_x, world_y)

    def world_to_screen(
        self,
        world_pos: Tuple[float, float]
    ) -> Tuple[int, int]:
        """
        游戏世界坐标 → 屏幕坐标（逆透视变换）

        Args:
            world_pos: 游戏坐标 (world_x, world_y)

        Returns:
            Tuple[int, int]: 屏幕坐标 (x, y)

        逆透视变换公式：
            depth = world_y
            screen_x = center_x + world_x * (depth + 1)
            screen_y = horizon_y + depth / depth_scale
        """
        world_x, world_y = world_pos
        depth = world_y

        # 反向透视变换
        perspective_factor = depth + 1.0
        screen_x = int(self.center_x + world_x * perspective_factor)
        screen_y = int(self.horizon_y + depth / self.depth_scale)

        return (screen_x, screen_y)

    def calculate_depth(self, screen_y: int) -> float:
        """
        计算 Y 坐标对应的深度

        Args:
            screen_y: 屏幕 Y 坐标

        Returns:
            float: 深度值（游戏单位）
            - 负数：地平线以上（背景/天空）
            - 0：地平线
            - 正数：地面（越大越近）

        公式：
            depth = (screen_y - horizon_y) * depth_scale
        """
        return (screen_y - self.horizon_y) * self.depth_scale

    def align_y_position(
        self,
        obj1: GameObject,
        obj2: GameObject
    ) -> float:
        """
        计算两个对象的 Y 轴对齐误差

        Args:
            obj1: 对象 1
            obj2: 对象 2

        Returns:
            float: Y 轴误差（像素），0 表示完美对齐

        实现逻辑：
            使用对象的 foot_point（落地坐标）而非 center
            因为 DNF 的 Y 轴对齐是基于脚底位置判断的
        """
        # 获取两个对象的脚底坐标
        _, foot_y1 = obj1.foot_point
        _, foot_y2 = obj2.foot_point

        # 计算绝对差值
        error = abs(foot_y1 - foot_y2)

        return float(error)

    def is_aligned(
        self,
        obj1: GameObject,
        obj2: GameObject,
        tolerance: float = 15.0
    ) -> bool:
        """
        判断两个对象是否 Y 轴对齐

        Args:
            obj1: 对象 1
            obj2: 对象 2
            tolerance: 容差（像素），默认 15 像素

        Returns:
            bool: 是否对齐

        使用场景：
            - 战斗前判断是否需要调整位置
            - 技能释放前的预检查
        """
        error = self.align_y_position(obj1, obj2)
        return error <= tolerance

    def calculate_distance(
        self,
        obj1: GameObject,
        obj2: GameObject
    ) -> float:
        """
        计算两个对象之间的欧氏距离（游戏单位）

        Args:
            obj1: 对象 1
            obj2: 对象 2

        Returns:
            float: 距离（游戏单位）

        实现逻辑：
            1. 将两个对象的脚底坐标转换为游戏世界坐标
            2. 计算欧氏距离
            3. 考虑透视变换，使得远处的物体距离计算更准确
        """
        # 获取脚底坐标
        foot1 = obj1.foot_point
        foot2 = obj2.foot_point

        # 转换为游戏世界坐标
        world_x1, world_y1 = self.screen_to_world(foot1)
        world_x2, world_y2 = self.screen_to_world(foot2)

        # 计算欧氏距离
        dx = world_x2 - world_x1
        dy = world_y2 - world_y1
        distance = math.sqrt(dx * dx + dy * dy)

        return distance

    def is_in_attack_range(
        self,
        attacker: GameObject,
        target: GameObject,
        attack_range: float = 100.0
    ) -> bool:
        """
        判断目标是否在攻击范围内

        Args:
            attacker: 攻击者对象
            target: 目标对象
            attack_range: 攻击范围（游戏单位），默认 100

        Returns:
            bool: 是否在攻击范围内

        实现逻辑：
            1. 检查 Y 轴是否对齐（容差 15 像素）
            2. 检查距离是否在攻击范围内
        """
        # 首先检查 Y 轴对齐
        if not self.is_aligned(attacker, target):
            return False

        # 检查距离
        distance = self.calculate_distance(attacker, target)
        return distance <= attack_range

    def get_y_direction(
        self,
        source: GameObject,
        target: GameObject
    ) -> int:
        """
        获取从 source 到 target 的 Y 轴移动方向

        Args:
            source: 源对象
            target: 目标对象

        Returns:
            int: -1（向上），0（已对齐），1（向下）

        使用场景：
            - 自动战斗时判断需要向上还是向下移动
        """
        _, source_y = source.foot_point
        _, target_y = target.foot_point

        delta = target_y - source_y

        if abs(delta) <= 15:  # 在容差范围内
            return 0
        elif delta < 0:
            return -1  # 需要向上移动
        else:
            return 1   # 需要向下移动

    def get_x_direction(
        self,
        source: GameObject,
        target: GameObject
    ) -> int:
        """
        获取从 source 到 target 的 X 轴移动方向

        Args:
            source: 源对象
            target: 目标对象

        Returns:
            int: -1（向左），0（已对齐），1（向右）
        """
        source_x, _ = source.foot_point
        target_x, _ = target.foot_point

        delta = target_x - source_x

        if abs(delta) <= 15:  # 在容差范围内
            return 0
        elif delta < 0:
            return -1  # 需要向左移动
        else:
            return 1   # 需要向右移动

    def resize(
        self,
        new_width: int,
        new_height: int,
        horizon_y: Optional[int] = None
    ) -> None:
        """
        调整映射器（分辨率改变时调用）

        Args:
            new_width: 新宽度
            new_height: 新高度
            horizon_y: 新地平线 Y 坐标（可选，默认为屏幕中心）
        """
        old_width = self.screen_width
        old_height = self.screen_height

        self.screen_width = new_width
        self.screen_height = new_height

        # 更新中心 X 坐标
        self.center_x = new_width // 2

        # 更新地平线 Y 坐标
        if horizon_y is not None:
            self.horizon_y = horizon_y
        else:
            self.horizon_y = new_height // 2

        logger.info(
            f"CoordinateMapper 分辨率调整: "
            f"{old_width}x{old_height} → {new_width}x{new_height}, "
            f"horizon_y={self.horizon_y}"
        )

    def get_info(self) -> dict:
        """
        获取映射器配置信息（用于调试）

        Returns:
            dict: 配置信息字典
        """
        return {
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "horizon_y": self.horizon_y,
            "center_x": self.center_x,
            "depth_scale": self.depth_scale
        }

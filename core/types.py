"""
核心数据模型定义

Author: yangmq17
Date: Day 1 上午
Priority: P0 (必须最先完成)
Dependencies: None
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CommandType(Enum):
    """指令类型枚举"""
    MOVE = "move"
    ATTACK = "attack"
    SKILL = "skill"
    PICKUP = "pickup"
    STOP = "stop"
    JUMP = "jump"
    DASH = "dash"


class BotState(Enum):
    """机器人状态枚举"""
    IDLE = 0          # 待机
    COMBAT = 1        # 战斗中
    LOOT = 2          # 拾取物品
    NAVIGATE = 3      # 寻路过图
    RECOVERY = 4      # 异常恢复


class MainViewState(Enum):
    """主画面状态。"""
    COMBAT_ROOM = "combat_room"
    CLEAR_ROOM = "clear_room"
    TRANSITION = "transition"
    BOSS_ROOM = "boss_room"
    RUN_FINISHED = "run_finished"
    UNKNOWN = "unknown"


class MinimapPathState(Enum):
    """小地图清房推进状态。"""
    NEIGHBOR_DARK = "MINIMAP_NEIGHBOR_DARK"
    NEIGHBOR_FLASH_QMARK = "MINIMAP_NEIGHBOR_FLASH_QMARK"
    BOSS_ONLY_READY = "MINIMAP_BOSS_ONLY_READY"
    CLEAR_PENDING = "CLEAR_PENDING"
    UNKNOWN = "UNKNOWN"


class MinimapSpecialState(Enum):
    """小地图特殊房间状态。"""
    NONE = "NONE"
    ABYSS_ROOM_PRESENT = "ABYSS_ROOM_PRESENT"


class GuardAction(Enum):
    """守护层动作。"""
    NONE = "none"
    USE_HP_POTION = "use_hp_potion"
    USE_MP_POTION = "use_mp_potion"
    ABORT_RUN = "abort_run"


class MaintenanceState(Enum):
    """副本后维护流程状态。"""
    IDLE = "idle"
    CHECK_INVENTORY = "check_inventory"
    OPEN_VENDOR = "open_vendor"
    SELL_DRY_RUN = "sell_dry_run"
    REPAIR_AND_RESTOCK = "repair_and_restock"
    READY_NEXT_RUN = "ready_next_run"


class ObjectType(Enum):
    """游戏对象类型"""
    MONSTER = 0
    HERO = 1
    ITEM = 2
    GATE = 3
    BOSS = 4


@dataclass
class ROI:
    """
    感兴趣区域配置。

    Attributes:
        x: 左上角 X
        y: 左上角 Y
        w: 宽度
        h: 高度
    """
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        """右下角 X。"""
        return self.x + self.w

    @property
    def y2(self) -> int:
        """右下角 Y。"""
        return self.y + self.h

    def to_tuple(self) -> Tuple[int, int, int, int]:
        """转换为 `(x, y, w, h)`。"""
        return (self.x, self.y, self.w, self.h)


@dataclass
class BBox:
    """
    边界框 (Bounding Box)

    Attributes:
        x1: 左上角X坐标
        y1: 左上角Y坐标
        x2: 右下角X坐标
        y2: 右下角Y坐标
    """
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        """宽度"""
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        """高度"""
        return self.y2 - self.y1

    @property
    def center(self) -> Tuple[int, int]:
        """几何中心 (cx, cy)"""
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @property
    def area(self) -> int:
        """面积"""
        return self.width * self.height

    def to_tuple(self) -> Tuple[int, int, int, int]:
        """转换为元组 (x1, y1, x2, y2)"""
        return (self.x1, self.y1, self.x2, self.y2)

    def to_yolo_format(self, img_width: int, img_height: int) -> Tuple[float, float, float, float]:
        """
        转换为YOLO格式 (x_center, y_center, width, height) 归一化

        Args:
            img_width: 图像宽度
            img_height: 图像高度

        Returns:
            (x_center, y_center, width, height) 范围 [0, 1]
        """
        cx, cy = self.center
        return (
            cx / img_width,
            cy / img_height,
            self.width / img_width,
            self.height / img_height
        )


@dataclass
class GameObject:
    """
    游戏对象

    Attributes:
        id: 对象唯一ID
        cls_id: 类别ID (0-4对应ObjectType)
        cls_name: 类别名称
        conf: 置信度 [0.0, 1.0]
        bbox: 边界框
    """
    id: int
    cls_id: int
    cls_name: str
    conf: float
    bbox: BBox

    @property
    def center(self) -> Tuple[int, int]:
        """几何中心"""
        return self.bbox.center

    @property
    def foot_point(self) -> Tuple[int, int]:
        """
        落地坐标 - Y轴对齐的关键

        逻辑: 取bbox底部中心，向上修正5%避免判定点过低
        """
        cx, _ = self.center
        fy = int(self.bbox.y2 * 0.95 + self.bbox.y1 * 0.05)
        return (cx, fy)

    @property
    def object_type(self) -> ObjectType:
        """对象类型枚举"""
        return ObjectType(self.cls_id)

    def distance_to(self, other: 'GameObject') -> float:
        """计算到另一个对象的欧氏距离"""
        x1, y1 = self.foot_point
        x2, y2 = other.foot_point
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def is_y_aligned(self, other: 'GameObject', tolerance: int = 15) -> bool:
        """
        判断是否与另一个对象Y轴对齐

        Args:
            other: 另一个游戏对象
            tolerance: 允许的像素误差

        Returns:
            是否对齐
        """
        _, y1 = self.foot_point
        _, y2 = other.foot_point
        return abs(y1 - y2) <= tolerance


@dataclass
class PlayerState:
    """
    玩家状态信息

    Attributes:
        hp_percent: HP百分比 [0.0, 1.0]
        mp_percent: MP百分比 [0.0, 1.0]
        level: 等级
        position: 当前位置 (x, y)
        facing_direction: 朝向 (-1左, 1右)
        buffs: 当前buff列表
        skill_cds: 技能冷却字典 {skill_name: remaining_time}
    """
    hp_percent: float = 1.0
    mp_percent: float = 1.0
    level: int = 1
    position: Tuple[int, int] = (0, 0)
    facing_direction: int = 1
    buffs: List[str] = field(default_factory=list)
    skill_cds: Dict[str, float] = field(default_factory=dict)

    def is_alive(self) -> bool:
        """是否存活"""
        return self.hp_percent > 0

    def need_hp_potion(self, threshold: float = 0.3) -> bool:
        """是否需要HP药水"""
        return self.hp_percent < threshold

    def need_mp_potion(self, threshold: float = 0.2) -> bool:
        """是否需要MP药水"""
        return self.mp_percent < threshold

    def is_skill_ready(self, skill_name: str) -> bool:
        """技能是否就绪"""
        return self.skill_cds.get(skill_name, 0) <= 0


@dataclass
class GuardDecision:
    """
    守护层决策。

    Attributes:
        action: 守护层动作
        pause_room_logic: 是否暂停房间逻辑
        key_code: 要触发的按键
        reason: 决策原因
    """
    action: GuardAction = GuardAction.NONE
    pause_room_logic: bool = False
    key_code: Optional[str] = None
    reason: str = ""

    @property
    def should_abort(self) -> bool:
        """是否应终止本次运行。"""
        return self.action == GuardAction.ABORT_RUN


@dataclass
class GameContext:
    """
    游戏上下文 - 每帧状态快照

    这是模块间传递的核心数据结构

    Attributes:
        frame_index: 帧序号
        timestamp: 时间戳
        hero: 玩家对象 (如果检测到)
        monsters: 怪物列表
        items: 物品列表
        doors: 门/传送阵列表
        player_state: 玩家状态
        room_cleared: 当前房间是否清空
    """
    frame_index: int
    timestamp: float
    hero: Optional[GameObject]
    monsters: List[GameObject] = field(default_factory=list)
    items: List[GameObject] = field(default_factory=list)
    doors: List[GameObject] = field(default_factory=list)
    player_state: PlayerState = field(default_factory=PlayerState)
    room_cleared: bool = False
    main_view_state: MainViewState = MainViewState.UNKNOWN
    minimap_path_state: MinimapPathState = MinimapPathState.UNKNOWN
    minimap_special_state: MinimapSpecialState = MinimapSpecialState.NONE
    expected_room_index: int = 1
    is_last_normal_room: bool = False
    transition_elapsed_ms: int = 0
    inventory_weight_ratio: float = 0.0
    free_slots: int = 999
    vendor_ui_open: bool = False
    potion_cd_ready: bool = True
    potion_stock_available: bool = True
    guard_decision: GuardDecision = field(default_factory=GuardDecision)
    maintenance_state: MaintenanceState = MaintenanceState.IDLE

    @property
    def has_monsters(self) -> bool:
        """是否有怪物"""
        return len(self.monsters) > 0

    @property
    def has_items(self) -> bool:
        """是否有物品"""
        return len(self.items) > 0

    @property
    def has_doors(self) -> bool:
        """是否有门"""
        return len(self.doors) > 0

    def get_nearest_monster(self) -> Optional[GameObject]:
        """获取最近的怪物"""
        if not self.has_monsters:
            return None
        if not self.hero:
            return self.monsters[0]

        return min(self.monsters, key=lambda m: self.hero.distance_to(m))

    def get_monsters_in_range(self, range_px: int) -> List[GameObject]:
        """获取攻击范围内的怪物"""
        if not self.hero:
            return []
        return [m for m in self.monsters if self.hero.distance_to(m) <= range_px]

    @property
    def is_transitioning(self) -> bool:
        """是否处于过图状态。"""
        return self.main_view_state == MainViewState.TRANSITION


@dataclass(init=False)
class Command:
    """
    动作指令

    设计原则：
    - 上层模块只描述动作，不关心具体按键
    - 按键映射由 InputDriver 根据配置决定

    Attributes:
        action_type: 指令类型
        direction: 移动方向 (dx, dy)，None表示不移动
        key_code: 按键码 (如 "x", "a", "space") - 已废弃，保留兼容
        duration: 持续时间 (秒)
        skill_index: 技能栏索引 (1-8)，用于 SKILL 命令
        metadata: 附加元数据
    """
    action_type: CommandType
    direction: Optional[Tuple[int, int]]
    key_code: Optional[str]  # 已废弃，保留兼容性
    duration: float
    skill_index: Optional[int] = None  # 技能栏索引
    metadata: Dict[str, Any]

    def __init__(
        self,
        action_type: Optional[CommandType] = None,
        direction: Optional[Tuple[int, int]] = None,
        key_code: Optional[str] = None,
        duration: float = 0.0,
        skill_index: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cmd_type: Optional[CommandType] = None,
    ) -> None:
        """
        初始化动作指令。

        为了兼容不同模块的命名约定，构造时同时支持：
        - action_type（当前项目主命名）
        - cmd_type（接口契约中的命名）
        """
        if action_type is None and cmd_type is None:
            raise ValueError("必须提供 action_type 或 cmd_type")

        if (
            action_type is not None
            and cmd_type is not None
            and action_type != cmd_type
        ):
            raise ValueError("action_type 与 cmd_type 不一致，无法判定真实指令类型")

        resolved_action_type = action_type if action_type is not None else cmd_type
        if resolved_action_type is None:
            raise ValueError("指令类型解析失败")

        if duration < 0:
            raise ValueError("duration 不能为负数")

        self.action_type = resolved_action_type
        self.direction = direction
        self.key_code = key_code
        self.duration = duration
        self.skill_index = skill_index
        self.metadata = metadata.copy() if metadata is not None else {}

    @property
    def cmd_type(self) -> CommandType:
        """
        兼容属性：cmd_type 等价于 action_type。

        目的：避免后续模块按接口文档使用 `cmd_type` 时触发属性错误。
        """
        return self.action_type

    @cmd_type.setter
    def cmd_type(self, value: CommandType) -> None:
        """兼容写入：允许通过 cmd_type 更新指令类型。"""
        self.action_type = value

    def is_movement(self) -> bool:
        """是否为移动指令"""
        return self.action_type == CommandType.MOVE

    def is_attack(self) -> bool:
        """是否为攻击指令"""
        return self.action_type in (CommandType.ATTACK, CommandType.SKILL)

    def __repr__(self) -> str:
        return f"Command({self.action_type.value}, key={self.key_code}, dir={self.direction})"


# 类型别名
DetectionResult = List[GameObject]

"""
配置加载器

支持 YAML 格式配置文件的加载、验证和热加载。
使用单例模式确保全局唯一配置实例。

Author: haneball17
Date: Day 1 上午
Priority: P0
Dependencies: pyyaml, core/exceptions.py, core/logger.py
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

import yaml

from core.exceptions import ConfigurationError
from core.logger import logger
from core.types import ROI

T = TypeVar('T')


# ==================== 配置数据类 ====================

@dataclass
class DetectorConfig:
    """检测器配置"""
    type: str = "mock"  # mock, yolo
    model_path: str = "models/yolov8n_dnf.pt"
    confidence_threshold: float = 0.6
    nms_threshold: float = 0.45
    input_size: tuple = (640, 640)
    use_gpu: bool = True


@dataclass
class CaptureConfig:
    """截图配置"""
    window_title: str = "地下城与勇士"
    window_class: str = "D3D Window"
    target_fps: int = 30
    width: int = 960
    height: int = 720
    monitor_index: int = 1
    use_mock: bool = False  # 是否使用 Mock 捕获引擎
    backend: str = "auto"  # auto, wgc, mss
    allow_fallback: bool = True  # 后端失败时是否允许降级（如 wgc -> mss）
    wgc_show_cursor: bool = False  # WGC 是否包含鼠标光标
    wgc_force_borderless: bool = False  # WGC 是否关闭捕获边框


@dataclass
class KeyBindingsConfig:
    """按键绑定配置

    设计说明：
    - 动作名与 Command.CommandType 对应
    - 按键值为 pydirectinput 支持的按键名
    - 用户可通过配置文件自定义按键
    """
    # 移动
    move_up: str = "up"         # 方向键上 ↑
    move_down: str = "down"      # 方向键下 ↓
    move_left: str = "left"      # 方向键左 ←
    move_right: str = "right"    # 方向键右 →

    # 动作
    attack: str = "x"            # 普通攻击
    skill: str = "z"             # 通用技能
    jump: str = "c"              # 跳跃
    pick_up: str = "x"           # 拾取物品（与攻击共用）

    # 技能栏
    skill_1: str = "1"
    skill_2: str = "2"
    skill_3: str = "3"
    skill_4: str = "4"
    skill_5: str = "5"
    skill_6: str = "6"
    skill_7: str = "7"
    skill_8: str = "8"

    # 道具栏
    potion_1: str = "1"
    potion_2: str = "2"
    potion_3: str = "3"
    potion_4: str = "4"
    potion_5: str = "5"
    potion_6: str = "6"


@dataclass
class InputConfig:
    """输入配置"""
    type: str = "mock"  # mock, real
    delay_min: float = 0.05
    delay_max: float = 0.15
    randomization: bool = True

    # 按键绑定（新增）
    key_bindings: KeyBindingsConfig = field(default_factory=KeyBindingsConfig)

    # 窗口管理（新增）
    check_focus: bool = True       # 是否检查窗口焦点
    auto_activate: bool = False    # 是否自动激活游戏窗口


@dataclass
class CombatConfig:
    """战斗配置"""
    y_tolerance: int = 15  # Y轴对齐容差（像素）
    attack_range: int = 150  # 攻击距离（像素）
    move_speed: float = 1.0  # 移动速度倍率
    attack_interval: float = 0.3  # 攻击间隔（秒）


@dataclass
class SystemConfig:
    """系统配置"""
    debug_mode: bool = False
    log_level: str = "INFO"
    enable_overlay: bool = False
    kill_switch_key: str = "F12"


@dataclass
class TemplateMatchConfig:
    """模板匹配配置。"""
    path: str = ""
    threshold: float = 0.92


@dataclass
class MainViewConfig:
    """主画面状态识别配置。"""
    transition_roi: ROI = field(default_factory=lambda: ROI(390, 300, 180, 120))
    clear_roi: ROI = field(default_factory=lambda: ROI(360, 95, 240, 90))
    boss_roi: ROI = field(default_factory=lambda: ROI(600, 0, 340, 80))
    finish_roi: ROI = field(default_factory=lambda: ROI(610, 520, 230, 120))
    transition_dark_threshold: float = 40.0
    clear_blue_ratio_threshold: float = 0.42
    boss_red_ratio_threshold: float = 0.42
    finish_green_ratio_threshold: float = 0.42
    stable_frames: int = 3
    transition_template: TemplateMatchConfig = field(default_factory=TemplateMatchConfig)
    clear_template: TemplateMatchConfig = field(default_factory=TemplateMatchConfig)
    boss_template: TemplateMatchConfig = field(default_factory=TemplateMatchConfig)
    finish_template: TemplateMatchConfig = field(default_factory=TemplateMatchConfig)


@dataclass
class MinimapConfig:
    """小地图识别配置。"""
    outer: ROI = field(default_factory=lambda: ROI(719, 39, 201, 110))
    inner: ROI = field(default_factory=lambda: ROI(742, 60, 132, 35))
    neighbor_roi: ROI = field(default_factory=lambda: ROI(740, 58, 155, 48))
    special_roi: ROI = field(default_factory=lambda: ROI(880, 58, 26, 26))
    resize_scale: int = 2
    dark_threshold: float = 55.0
    flash_brightness_threshold: float = 200.0
    boss_red_ratio_threshold: float = 0.44
    special_green_ratio_threshold: float = 0.44
    stable_frames: int = 8
    pending_timeout_ms: int = 400


@dataclass
class UIRoisConfig:
    """UI 固定 ROI 配置。"""
    hp_bar: ROI = field(default_factory=lambda: ROI(31, 680, 145, 14))
    mp_bar: ROI = field(default_factory=lambda: ROI(784, 680, 145, 14))
    inventory_flag: ROI = field(default_factory=lambda: ROI(540, 58, 250, 24))
    inventory_weight_bar: ROI = field(default_factory=lambda: ROI(523, 546, 160, 20))
    vendor_flag: ROI = field(default_factory=lambda: ROI(84, 606, 372, 46))
    potion_flag: ROI = field(default_factory=lambda: ROI(130, 632, 48, 42))


@dataclass
class GuardThresholdsConfig:
    """守护层阈值配置。"""
    hp_critical_threshold: float = 0.25
    hp_low_threshold: float = 0.45
    mp_low_threshold: float = 0.20
    potion_cooldown_ms: int = 1200


@dataclass
class ClassProfileConfig:
    """职业配置。"""
    name: str = "map_wide_attack_current_class"
    requires_mp: bool = False
    primary_combat_skill: int = 1
    combat_interval_ms: int = 450


@dataclass
class RoomScriptConfig:
    """固定路线房间脚本。"""
    room_idx: int
    room_type: str = "normal"
    expected_exit_direction: str = "RIGHT"
    exit_action_template: str = "move_right_hold_1200"
    door_confirmation_roi: ROI = field(default_factory=lambda: ROI(640, 220, 180, 180))
    transition_timeout_ms: int = 1800
    is_last_normal_room: bool = False
    route_policy_tag: str = "fixed_full_clear"
    room_feature_tag: str = "normal"
    next_step: str = "go_next_normal"


@dataclass
class MaintenanceConfig:
    """维护流程配置。"""
    sell_dry_run: bool = True
    sell_rarity_threshold: str = "uncommon"
    max_weight_ratio: float = 0.85
    min_free_slots: int = 8
    min_potion_stock: int = 3


@dataclass
class DungeonRunConfig:
    """固定路线副本配置。"""
    enabled: bool = True
    dungeon_id: str = "jmzjz"
    route_policy_tag: str = "fixed_full_clear"
    start_room_index: int = 1
    main_view: MainViewConfig = field(default_factory=MainViewConfig)
    minimap: MinimapConfig = field(default_factory=MinimapConfig)
    ui_rois: UIRoisConfig = field(default_factory=UIRoisConfig)
    guard_thresholds: GuardThresholdsConfig = field(default_factory=GuardThresholdsConfig)
    class_profile: ClassProfileConfig = field(default_factory=ClassProfileConfig)
    maintenance: MaintenanceConfig = field(default_factory=MaintenanceConfig)
    room_scripts: List[RoomScriptConfig] = field(
        default_factory=lambda: [
            RoomScriptConfig(room_idx=1),
            RoomScriptConfig(
                room_idx=2,
                room_type="boss",
                expected_exit_direction="STOP",
                exit_action_template="none",
                transition_timeout_ms=1800,
                next_step="stop_after_finish",
            ),
        ]
    )


@dataclass
class AppConfig:
    """应用配置（根配置）"""
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    input: InputConfig = field(default_factory=InputConfig)
    combat: CombatConfig = field(default_factory=CombatConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    dungeon_run: DungeonRunConfig = field(default_factory=DungeonRunConfig)


# ==================== 配置加载器 ====================

class ConfigLoader:
    """
    配置加载器（单例模式）

    负责加载、验证和管理应用配置。

    Examples:
        >>> config = ConfigLoader.instance()
        >>> print(config.detector.model_path)
        >>> config.reload()  # 重新加载配置
    """

    _instance: Optional['ConfigLoader'] = None
    _config: Optional[AppConfig] = None
    _config_path: Optional[Path] = None

    def __new__(cls) -> 'ConfigLoader':
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化配置加载器"""
        if self._initialized:
            return

        self._initialized = True
        self._config_path = None
        self._config = AppConfig()
        logger.debug("ConfigLoader 初始化完成")

    @classmethod
    def instance(cls) -> 'ConfigLoader':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self, config_path: str = "configs/config.yaml") -> AppConfig:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            应用配置对象

        Raises:
            ConfigurationError: 配置文件不存在或格式错误
        """
        config_file = Path(config_path)

        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            self._create_default_config(config_file)
            self._config_path = config_file
            return self._config

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            # 每次加载都从默认配置重新开始，避免单例跨测试残留状态。
            self._config = AppConfig()
            self._parse_config(data)
            self._config_path = config_file
            self._validate_config()

            logger.info(f"配置加载成功: {config_path}")
            return self._config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"YAML解析错误: {e}")
        except Exception as e:
            raise ConfigurationError(f"配置加载失败: {e}")

    def _parse_config(self, data: Dict[str, Any]) -> None:
        """解析配置数据"""
        # 解析 detector 配置
        if 'detector' in data:
            detector_data = data['detector']
            self._config.detector = DetectorConfig(
                type=detector_data.get('type', 'mock'),
                model_path=detector_data.get('model_path', 'models/yolov8n_dnf.pt'),
                confidence_threshold=detector_data.get('confidence_threshold', 0.6),
                nms_threshold=detector_data.get('nms_threshold', 0.45),
                input_size=tuple(detector_data.get('input_size', [640, 640])),
                use_gpu=detector_data.get('use_gpu', True)
            )

        # 解析 capture 配置
        if 'capture' in data:
            capture_data = data['capture']
            self._config.capture = CaptureConfig(
                window_title=capture_data.get('window_title', '地下城与勇士'),
                window_class=capture_data.get('window_class', 'D3D Window'),
                target_fps=capture_data.get('target_fps', 30),
                width=capture_data.get('width', 960),
                height=capture_data.get('height', 720),
                monitor_index=capture_data.get('monitor_index', 1),
                use_mock=capture_data.get('use_mock', False),
                backend=capture_data.get('backend', 'auto'),
                allow_fallback=capture_data.get('allow_fallback', True),
                wgc_show_cursor=capture_data.get('wgc_show_cursor', False),
                wgc_force_borderless=capture_data.get('wgc_force_borderless', False),
            )

        # 解析 input 配置
        if 'input' in data:
            input_data = data['input']
            self._config.input = InputConfig(
                type=input_data.get('type', 'mock'),
                delay_min=input_data.get('delay_min', 0.05),
                delay_max=input_data.get('delay_max', 0.15),
                randomization=input_data.get('randomization', True),
                # 解析按键绑定
                key_bindings=self._parse_key_bindings(input_data.get('key_bindings', {})),
                # 解析窗口配置
                check_focus=input_data.get('window', {}).get('check_focus', True),
                auto_activate=input_data.get('window', {}).get('auto_activate', False)
            )

        # 解析 combat 配置
        if 'combat' in data:
            combat_data = data['combat']
            self._config.combat = CombatConfig(
                y_tolerance=combat_data.get('y_tolerance', 15),
                attack_range=combat_data.get('attack_range', 150),
                move_speed=combat_data.get('move_speed', 1.0),
                attack_interval=combat_data.get('attack_interval', 0.3)
            )

        # 解析 system 配置
        if 'system' in data:
            system_data = data['system']
            self._config.system = SystemConfig(
                debug_mode=system_data.get('debug_mode', False),
                log_level=system_data.get('log_level', 'INFO'),
                enable_overlay=system_data.get('enable_overlay', False),
                kill_switch_key=system_data.get('kill_switch_key', 'F12')
            )

        # 解析固定路线副本配置
        if 'dungeon_run' in data:
            self._config.dungeon_run = self._parse_dungeon_run(data['dungeon_run'])

    def _parse_key_bindings(self, key_bindings_data: Dict[str, Any]) -> KeyBindingsConfig:
        """
        解析按键绑定配置

        Args:
            key_bindings_data: YAML 中的 key_bindings 字段

        Returns:
            KeyBindingsConfig 对象
        """
        return KeyBindingsConfig(
            # 移动
            move_up=key_bindings_data.get('move_up', 'up'),
            move_down=key_bindings_data.get('move_down', 'down'),
            move_left=key_bindings_data.get('move_left', 'left'),
            move_right=key_bindings_data.get('move_right', 'right'),
            # 动作
            attack=key_bindings_data.get('attack', 'x'),
            skill=key_bindings_data.get('skill', 'z'),
            jump=key_bindings_data.get('jump', 'c'),
            pick_up=key_bindings_data.get('pick_up', 'x'),
            # 技能栏
            skill_1=key_bindings_data.get('skill_1', '1'),
            skill_2=key_bindings_data.get('skill_2', '2'),
            skill_3=key_bindings_data.get('skill_3', '3'),
            skill_4=key_bindings_data.get('skill_4', '4'),
            skill_5=key_bindings_data.get('skill_5', '5'),
            skill_6=key_bindings_data.get('skill_6', '6'),
            skill_7=key_bindings_data.get('skill_7', '7'),
            skill_8=key_bindings_data.get('skill_8', '8'),
            # 道具栏
            potion_1=key_bindings_data.get('potion_1', '1'),
            potion_2=key_bindings_data.get('potion_2', '2'),
            potion_3=key_bindings_data.get('potion_3', '3'),
            potion_4=key_bindings_data.get('potion_4', '4'),
            potion_5=key_bindings_data.get('potion_5', '5'),
            potion_6=key_bindings_data.get('potion_6', '6'),
        )

    @staticmethod
    def _parse_roi(roi_data: Any, default: ROI) -> ROI:
        """解析 ROI 配置。"""
        if roi_data is None:
            return default
        if isinstance(roi_data, ROI):
            return roi_data
        if isinstance(roi_data, (list, tuple)) and len(roi_data) == 4:
            return ROI(int(roi_data[0]), int(roi_data[1]), int(roi_data[2]), int(roi_data[3]))
        if isinstance(roi_data, dict):
            return ROI(
                int(roi_data.get('x', default.x)),
                int(roi_data.get('y', default.y)),
                int(roi_data.get('w', default.w)),
                int(roi_data.get('h', default.h)),
            )
        raise ConfigurationError(f"无法解析 ROI 配置: {roi_data}")

    @staticmethod
    def _parse_template(template_data: Optional[Dict[str, Any]]) -> TemplateMatchConfig:
        """解析模板匹配配置。"""
        if not template_data:
            return TemplateMatchConfig()
        return TemplateMatchConfig(
            path=str(template_data.get('path', '')),
            threshold=float(template_data.get('threshold', 0.92)),
        )

    def _parse_main_view(self, data: Dict[str, Any]) -> MainViewConfig:
        """解析主画面状态配置。"""
        default = MainViewConfig()
        return MainViewConfig(
            transition_roi=self._parse_roi(data.get('transition_roi'), default.transition_roi),
            clear_roi=self._parse_roi(data.get('clear_roi'), default.clear_roi),
            boss_roi=self._parse_roi(data.get('boss_roi'), default.boss_roi),
            finish_roi=self._parse_roi(data.get('finish_roi'), default.finish_roi),
            transition_dark_threshold=float(
                data.get('transition_dark_threshold', default.transition_dark_threshold)
            ),
            clear_blue_ratio_threshold=float(
                data.get('clear_blue_ratio_threshold', default.clear_blue_ratio_threshold)
            ),
            boss_red_ratio_threshold=float(
                data.get('boss_red_ratio_threshold', default.boss_red_ratio_threshold)
            ),
            finish_green_ratio_threshold=float(
                data.get('finish_green_ratio_threshold', default.finish_green_ratio_threshold)
            ),
            stable_frames=int(data.get('stable_frames', default.stable_frames)),
            transition_template=self._parse_template(data.get('transition_template')),
            clear_template=self._parse_template(data.get('clear_template')),
            boss_template=self._parse_template(data.get('boss_template')),
            finish_template=self._parse_template(data.get('finish_template')),
        )

    def _parse_minimap(self, data: Dict[str, Any]) -> MinimapConfig:
        """解析小地图配置。"""
        default = MinimapConfig()
        return MinimapConfig(
            outer=self._parse_roi(data.get('outer'), default.outer),
            inner=self._parse_roi(data.get('inner'), default.inner),
            neighbor_roi=self._parse_roi(data.get('neighbor_roi'), default.neighbor_roi),
            special_roi=self._parse_roi(data.get('special_roi'), default.special_roi),
            resize_scale=int(data.get('resize_scale', default.resize_scale)),
            dark_threshold=float(data.get('dark_threshold', default.dark_threshold)),
            flash_brightness_threshold=float(
                data.get('flash_brightness_threshold', default.flash_brightness_threshold)
            ),
            boss_red_ratio_threshold=float(
                data.get('boss_red_ratio_threshold', default.boss_red_ratio_threshold)
            ),
            special_green_ratio_threshold=float(
                data.get('special_green_ratio_threshold', default.special_green_ratio_threshold)
            ),
            stable_frames=int(data.get('stable_frames', default.stable_frames)),
            pending_timeout_ms=int(data.get('pending_timeout_ms', default.pending_timeout_ms)),
        )

    def _parse_ui_rois(self, data: Dict[str, Any]) -> UIRoisConfig:
        """解析 UI ROI 配置。"""
        default = UIRoisConfig()
        return UIRoisConfig(
            hp_bar=self._parse_roi(data.get('hp_bar'), default.hp_bar),
            mp_bar=self._parse_roi(data.get('mp_bar'), default.mp_bar),
            inventory_flag=self._parse_roi(data.get('inventory_flag'), default.inventory_flag),
            inventory_weight_bar=self._parse_roi(
                data.get('inventory_weight_bar'),
                default.inventory_weight_bar,
            ),
            vendor_flag=self._parse_roi(data.get('vendor_flag'), default.vendor_flag),
            potion_flag=self._parse_roi(data.get('potion_flag'), default.potion_flag),
        )

    @staticmethod
    def _parse_guard_thresholds(data: Dict[str, Any]) -> GuardThresholdsConfig:
        """解析守护层阈值配置。"""
        default = GuardThresholdsConfig()
        return GuardThresholdsConfig(
            hp_critical_threshold=float(
                data.get('hp_critical_threshold', default.hp_critical_threshold)
            ),
            hp_low_threshold=float(data.get('hp_low_threshold', default.hp_low_threshold)),
            mp_low_threshold=float(data.get('mp_low_threshold', default.mp_low_threshold)),
            potion_cooldown_ms=int(data.get('potion_cooldown_ms', default.potion_cooldown_ms)),
        )

    @staticmethod
    def _parse_class_profile(data: Dict[str, Any]) -> ClassProfileConfig:
        """解析职业配置。"""
        default = ClassProfileConfig()
        return ClassProfileConfig(
            name=str(data.get('name', default.name)),
            requires_mp=bool(data.get('requires_mp', default.requires_mp)),
            primary_combat_skill=int(
                data.get('primary_combat_skill', default.primary_combat_skill)
            ),
            combat_interval_ms=int(
                data.get('combat_interval_ms', default.combat_interval_ms)
            ),
        )

    def _parse_room_script(self, data: Dict[str, Any]) -> RoomScriptConfig:
        """解析单个房间脚本。"""
        default = RoomScriptConfig(room_idx=int(data.get('room_idx', 1)))
        return RoomScriptConfig(
            room_idx=int(data.get('room_idx', 1)),
            room_type=str(data.get('room_type', default.room_type)),
            expected_exit_direction=str(
                data.get('expected_exit_direction', default.expected_exit_direction)
            ),
            exit_action_template=str(
                data.get('exit_action_template', default.exit_action_template)
            ),
            door_confirmation_roi=self._parse_roi(
                data.get('door_confirmation_roi'),
                default.door_confirmation_roi,
            ),
            transition_timeout_ms=int(
                data.get('transition_timeout_ms', default.transition_timeout_ms)
            ),
            is_last_normal_room=bool(
                data.get('is_last_normal_room', default.is_last_normal_room)
            ),
            route_policy_tag=str(data.get('route_policy_tag', default.route_policy_tag)),
            room_feature_tag=str(data.get('room_feature_tag', default.room_feature_tag)),
            next_step=str(data.get('next_step', default.next_step)),
        )

    @staticmethod
    def _parse_maintenance(data: Dict[str, Any]) -> MaintenanceConfig:
        """解析维护配置。"""
        default = MaintenanceConfig()
        return MaintenanceConfig(
            sell_dry_run=bool(data.get('sell_dry_run', default.sell_dry_run)),
            sell_rarity_threshold=str(
                data.get('sell_rarity_threshold', default.sell_rarity_threshold)
            ),
            max_weight_ratio=float(data.get('max_weight_ratio', default.max_weight_ratio)),
            min_free_slots=int(data.get('min_free_slots', default.min_free_slots)),
            min_potion_stock=int(data.get('min_potion_stock', default.min_potion_stock)),
        )

    def _parse_dungeon_run(self, data: Dict[str, Any]) -> DungeonRunConfig:
        """解析固定路线副本配置。"""
        default = DungeonRunConfig()
        room_scripts = data.get('room_scripts', [])
        parsed_room_scripts = [self._parse_room_script(item) for item in room_scripts]
        if not parsed_room_scripts:
            parsed_room_scripts = default.room_scripts

        return DungeonRunConfig(
            enabled=bool(data.get('enabled', default.enabled)),
            dungeon_id=str(data.get('dungeon_id', default.dungeon_id)),
            route_policy_tag=str(data.get('route_policy_tag', default.route_policy_tag)),
            start_room_index=int(data.get('start_room_index', default.start_room_index)),
            main_view=self._parse_main_view(data.get('main_view', {})),
            minimap=self._parse_minimap(data.get('minimap', {})),
            ui_rois=self._parse_ui_rois(data.get('ui_rois', {})),
            guard_thresholds=self._parse_guard_thresholds(data.get('guard_thresholds', {})),
            class_profile=self._parse_class_profile(data.get('class_profile', {})),
            maintenance=self._parse_maintenance(data.get('maintenance', {})),
            room_scripts=parsed_room_scripts,
        )

    def _validate_config(self) -> None:
        """验证配置有效性"""
        # 验证检测器配置
        if self._config.detector.confidence_threshold < 0 or self._config.detector.confidence_threshold > 1:
            raise ConfigurationError("检测器置信度阈值必须在 [0, 1] 范围内")

        if self._config.detector.nms_threshold < 0 or self._config.detector.nms_threshold > 1:
            raise ConfigurationError("NMS 阈值必须在 [0, 1] 范围内")

        # 验证截图配置
        if self._config.capture.target_fps <= 0:
            raise ConfigurationError("目标 FPS 必须大于 0")
        if self._config.capture.width <= 0 or self._config.capture.height <= 0:
            raise ConfigurationError("capture.width 和 capture.height 必须大于 0")
        if self._config.capture.backend not in {"auto", "wgc", "mss"}:
            raise ConfigurationError("capture.backend 必须是 auto/wgc/mss")

        # 验证战斗配置
        if self._config.combat.y_tolerance < 0:
            raise ConfigurationError("Y 轴容差不能为负数")

        if self._config.combat.attack_range <= 0:
            raise ConfigurationError("攻击距离必须大于 0")

        if not 0 <= self._config.dungeon_run.guard_thresholds.hp_critical_threshold <= 1:
            raise ConfigurationError("hp_critical_threshold 必须在 [0, 1] 范围内")
        if not 0 <= self._config.dungeon_run.guard_thresholds.hp_low_threshold <= 1:
            raise ConfigurationError("hp_low_threshold 必须在 [0, 1] 范围内")
        if not 0 <= self._config.dungeon_run.guard_thresholds.mp_low_threshold <= 1:
            raise ConfigurationError("mp_low_threshold 必须在 [0, 1] 范围内")
        if self._config.dungeon_run.guard_thresholds.hp_critical_threshold > self._config.dungeon_run.guard_thresholds.hp_low_threshold:
            raise ConfigurationError("hp_critical_threshold 不能高于 hp_low_threshold")
        if not self._config.dungeon_run.room_scripts:
            raise ConfigurationError("dungeon_run.room_scripts 不能为空")

        capture_width = self._config.capture.width
        capture_height = self._config.capture.height
        roi_entries = [
            ("dungeon_run.main_view.transition_roi", self._config.dungeon_run.main_view.transition_roi),
            ("dungeon_run.main_view.clear_roi", self._config.dungeon_run.main_view.clear_roi),
            ("dungeon_run.main_view.boss_roi", self._config.dungeon_run.main_view.boss_roi),
            ("dungeon_run.main_view.finish_roi", self._config.dungeon_run.main_view.finish_roi),
            ("dungeon_run.minimap.outer", self._config.dungeon_run.minimap.outer),
            ("dungeon_run.minimap.inner", self._config.dungeon_run.minimap.inner),
            ("dungeon_run.minimap.neighbor_roi", self._config.dungeon_run.minimap.neighbor_roi),
            ("dungeon_run.minimap.special_roi", self._config.dungeon_run.minimap.special_roi),
            ("dungeon_run.ui_rois.hp_bar", self._config.dungeon_run.ui_rois.hp_bar),
            ("dungeon_run.ui_rois.mp_bar", self._config.dungeon_run.ui_rois.mp_bar),
            ("dungeon_run.ui_rois.inventory_flag", self._config.dungeon_run.ui_rois.inventory_flag),
            (
                "dungeon_run.ui_rois.inventory_weight_bar",
                self._config.dungeon_run.ui_rois.inventory_weight_bar,
            ),
            ("dungeon_run.ui_rois.vendor_flag", self._config.dungeon_run.ui_rois.vendor_flag),
            ("dungeon_run.ui_rois.potion_flag", self._config.dungeon_run.ui_rois.potion_flag),
        ]
        for room_script in self._config.dungeon_run.room_scripts:
            roi_entries.append(
                (
                    f"dungeon_run.room_scripts[{room_script.room_idx}].door_confirmation_roi",
                    room_script.door_confirmation_roi,
                )
            )

        for roi_name, roi in roi_entries:
            if min(roi.x, roi.y, roi.w, roi.h) < 0:
                raise ConfigurationError(f"{roi_name} 坐标和尺寸不能为负数")
            if roi.w <= 0 or roi.h <= 0:
                raise ConfigurationError(f"{roi_name} 宽高必须大于 0")
            if roi.x2 > capture_width or roi.y2 > capture_height:
                raise ConfigurationError(
                    f"{roi_name} 超出 capture 分辨率边界: "
                    f"roi=({roi.x},{roi.y},{roi.w},{roi.h}), "
                    f"capture=({capture_width},{capture_height})"
                )

        logger.debug("配置验证通过")

    def _create_default_config(self, config_path: Path) -> None:
        """创建默认配置文件"""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            'detector': {
                'type': 'mock',
                'model_path': 'models/yolov8n_dnf.pt',
                'confidence_threshold': 0.6,
                'nms_threshold': 0.45,
                'input_size': [640, 640],
                'use_gpu': True
            },
            'capture': {
                'window_title': '地下城与勇士',
                'window_class': 'D3D Window',
                'target_fps': 30,
                'width': 960,
                'height': 720,
                'monitor_index': 1,
                'use_mock': False,
                'backend': 'auto',
                'allow_fallback': True,
                'wgc_show_cursor': False,
                'wgc_force_borderless': False,
            },
            'input': {
                'type': 'mock',
                'delay_min': 0.05,
                'delay_max': 0.15,
                'randomization': True
            },
            'combat': {
                'y_tolerance': 15,
                'attack_range': 150,
                'move_speed': 1.0,
                'attack_interval': 0.3
            },
            'system': {
                'debug_mode': False,
                'log_level': 'INFO',
                'enable_overlay': False,
                'kill_switch_key': 'F12'
            },
            'dungeon_run': {
                'enabled': True,
                'dungeon_id': 'jmzjz',
                'route_policy_tag': 'fixed_full_clear',
                'start_room_index': 1,
                'main_view': {
                    'transition_roi': [390, 300, 180, 120],
                    'clear_roi': [360, 95, 240, 90],
                    'boss_roi': [600, 0, 340, 80],
                    'finish_roi': [610, 520, 230, 120],
                    'transition_dark_threshold': 40.0,
                    'clear_blue_ratio_threshold': 0.42,
                    'boss_red_ratio_threshold': 0.42,
                    'finish_green_ratio_threshold': 0.42,
                    'stable_frames': 3,
                },
                'minimap': {
                    'outer': [719, 39, 201, 110],
                    'inner': [742, 60, 132, 35],
                    'neighbor_roi': [740, 58, 155, 48],
                    'special_roi': [880, 58, 26, 26],
                    'resize_scale': 2,
                    'dark_threshold': 55.0,
                    'flash_brightness_threshold': 200.0,
                    'boss_red_ratio_threshold': 0.44,
                    'special_green_ratio_threshold': 0.44,
                    'stable_frames': 8,
                    'pending_timeout_ms': 400,
                },
                'ui_rois': {
                    'hp_bar': [31, 680, 145, 14],
                    'mp_bar': [784, 680, 145, 14],
                    'inventory_flag': [540, 58, 250, 24],
                    'inventory_weight_bar': [523, 546, 160, 20],
                    'vendor_flag': [84, 606, 372, 46],
                    'potion_flag': [130, 632, 48, 42],
                },
                'guard_thresholds': {
                    'hp_critical_threshold': 0.25,
                    'hp_low_threshold': 0.45,
                    'mp_low_threshold': 0.20,
                    'potion_cooldown_ms': 1200,
                },
                'class_profile': {
                    'name': 'map_wide_attack_current_class',
                    'requires_mp': False,
                    'primary_combat_skill': 1,
                    'combat_interval_ms': 450,
                },
                'maintenance': {
                    'sell_dry_run': True,
                    'sell_rarity_threshold': 'uncommon',
                    'max_weight_ratio': 0.85,
                    'min_free_slots': 8,
                    'min_potion_stock': 3,
                },
                'room_scripts': [
                    {
                        'room_idx': 1,
                        'room_type': 'normal',
                        'expected_exit_direction': 'RIGHT',
                        'exit_action_template': 'move_right_hold_1200',
                        'door_confirmation_roi': [640, 220, 180, 180],
                        'transition_timeout_ms': 1800,
                        'is_last_normal_room': False,
                        'route_policy_tag': 'fixed_full_clear',
                        'room_feature_tag': 'normal',
                        'next_step': 'go_next_normal',
                    },
                    {
                        'room_idx': 2,
                        'room_type': 'boss',
                        'expected_exit_direction': 'STOP',
                        'exit_action_template': 'none',
                        'door_confirmation_roi': [640, 220, 180, 180],
                        'transition_timeout_ms': 1800,
                        'is_last_normal_room': False,
                        'route_policy_tag': 'fixed_full_clear',
                        'room_feature_tag': 'boss',
                        'next_step': 'stop_after_finish',
                    },
                ],
            },
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"已创建默认配置文件: {config_path}")

    def reload(self) -> AppConfig:
        """
        重新加载配置文件

        Returns:
            重新加载的配置对象

        Raises:
            ConfigurationError: 如果未加载过配置
        """
        if self._config_path is None:
            raise ConfigurationError("无法重新加载：未加载过配置文件")

        logger.info("重新加载配置...")
        return self.load(str(self._config_path))

    @property
    def config(self) -> AppConfig:
        """
        获取当前配置对象

        Returns:
            应用配置对象
        """
        return self._config

    @property
    def detector(self) -> DetectorConfig:
        """快捷访问：检测器配置"""
        return self._config.detector

    @property
    def capture(self) -> CaptureConfig:
        """快捷访问：截图配置"""
        return self._config.capture

    @property
    def input(self) -> InputConfig:
        """快捷访问：输入配置"""
        return self._config.input

    @property
    def combat(self) -> CombatConfig:
        """快捷访问：战斗配置"""
        return self._config.combat

    @property
    def system(self) -> SystemConfig:
        """快捷访问：系统配置"""
        return self._config.system

    @property
    def dungeon_run(self) -> DungeonRunConfig:
        """快捷访问：固定路线副本配置。"""
        return self._config.dungeon_run


# ==================== 全局单例访问 ====================

# 全局配置加载器实例
_config_loader: Optional[ConfigLoader] = None


def get_config() -> AppConfig:
    """
    获取全局配置对象（快捷方法）

    Examples:
        >>> from core.config import get_config
        >>> config = get_config()
        >>> print(config.detector.model_path)
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = ConfigLoader.instance()
        _config_loader.load()

    return _config_loader.config


def reload_config() -> AppConfig:
    """重新加载配置（快捷方法）"""
    global _config_loader

    if _config_loader is None:
        raise ConfigurationError("配置未初始化")

    return _config_loader.reload()


__all__ = [
    "ConfigLoader",
    "AppConfig",
    "DetectorConfig",
    "CaptureConfig",
    "InputConfig",
    "CombatConfig",
    "SystemConfig",
    "TemplateMatchConfig",
    "MainViewConfig",
    "MinimapConfig",
    "UIRoisConfig",
    "GuardThresholdsConfig",
    "ClassProfileConfig",
    "RoomScriptConfig",
    "MaintenanceConfig",
    "DungeonRunConfig",
    "get_config",
    "reload_config"
]

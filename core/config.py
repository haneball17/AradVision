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
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar
from dataclasses import dataclass, field

from core.exceptions import ConfigurationError
from core.logger import logger

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
    width: int = 1920
    height: int = 1080
    monitor_index: int = 1
    use_mock: bool = False  # 是否使用 Mock 捕获引擎
    backend: str = "auto"  # auto, wgc, mss
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
class AppConfig:
    """应用配置（根配置）"""
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    input: InputConfig = field(default_factory=InputConfig)
    combat: CombatConfig = field(default_factory=CombatConfig)
    system: SystemConfig = field(default_factory=SystemConfig)


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
                width=capture_data.get('width', 1920),
                height=capture_data.get('height', 1080),
                monitor_index=capture_data.get('monitor_index', 1),
                use_mock=capture_data.get('use_mock', False),
                backend=capture_data.get('backend', 'auto'),
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
        if self._config.capture.backend not in {"auto", "wgc", "mss"}:
            raise ConfigurationError("capture.backend 必须是 auto/wgc/mss")

        # 验证战斗配置
        if self._config.combat.y_tolerance < 0:
            raise ConfigurationError("Y 轴容差不能为负数")

        if self._config.combat.attack_range <= 0:
            raise ConfigurationError("攻击距离必须大于 0")

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
                'width': 1920,
                'height': 1080,
                'monitor_index': 1,
                'use_mock': False,
                'backend': 'auto',
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
            }
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
    "get_config",
    "reload_config"
]

"""
UI 配置管理器

管理 UI 相关的配置加载、保存和验证。

Author: haneball17
Date: 2026-02-11
"""

import yaml
from pathlib import Path
from typing import Dict, Any

from core.logger import logger


class UIManager:
    """
    UI 配置管理器

    负责管理 UI 配置的加载、保存和验证。
    """

    def __init__(self, config_dir: str = "configs"):
        """
        初始化管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.ui_config_file = self.config_dir / "ui_config.yaml"

        # 默认配置
        self.default_config = self.get_default_config()

        # 当前配置
        self.current_config = {}

    def get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            默认配置字典
        """
        return {
            "capture": {
                "target_fps": 30,
                "monitor_index": 0,
                "window_title": "地下城与勇士"
            },
            "detector": {
                "mode": "mock",
                "conf_threshold": 0.5,
                "iou_threshold": 0.45
            },
            "combat": {
                "y_tolerance": 15,
                "attack_range": 100,
                "skill_priority": ["a", "s", "d"]
            },
            "world_model": {
                "room_clear_timeout": 2.0
            },
            "ui": {
                "theme": "dark",
                "log_level": "INFO",
                "save_log": True,
                "auto_scroll": True
            }
        }

    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典
        """
        try:
            if self.ui_config_file.exists():
                with open(self.ui_config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info(f"配置文件加载成功: {self.ui_config_file}")
                self.current_config = config
                return config
            else:
                logger.warning("配置文件不存在，使用默认配置")
                self.current_config = self.default_config.copy()
                return self.default_config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            self.current_config = self.default_config.copy()
            return self.default_config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存配置文件

        Args:
            config: 配置字典

        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # 保存到文件
            with open(self.ui_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"配置文件保存成功: {self.ui_config_file}")
            self.current_config = config
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置有效性

        Args:
            config: 配置字典

        Returns:
            是否有效
        """
        try:
            # 验证捕获参数
            if "capture" in config:
                capture = config["capture"]
                if not (10 <= capture.get("target_fps", 30) <= 60):
                    logger.error("target_fps 必须在 10-60 之间")
                    return False

            # 验证战斗参数
            if "combat" in config:
                combat = config["combat"]
                if not (5 <= combat.get("y_tolerance", 15) <= 50):
                    logger.error("y_tolerance 必须在 5-50 之间")
                    return False
                if not (50 <= combat.get("attack_range", 100) <= 200):
                    logger.error("attack_range 必须在 50-200 之间")
                    return False

            # 验证 UI 参数
            if "ui" in config:
                ui = config["ui"]
                if ui.get("theme") not in ["dark", "light"]:
                    logger.error("theme 必须是 'dark' 或 'light'")
                    return False
                if ui.get("log_level") not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                    logger.error("log_level 必须是有效级别")
                    return False

            return True

        except Exception as e:
            logger.error(f"验证配置失败: {e}")
            return False

    def get_param(self, key_path: str, default=None):
        """
        获取参数值

        Args:
            key_path: 参数路径，如 "capture.target_fps"
            default: 默认值

        Returns:
            参数值
        """
        keys = key_path.split(".")
        value = self.current_config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set_param(self, key_path: str, value: Any):
        """
        设置参数值

        Args:
            key_path: 参数路径，如 "capture.target_fps"
            value: 新值
        """
        keys = key_path.split(".")
        config = self.current_config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

"""
参数配置面板组件

提供系统参数的配置和控制功能。

Author: haneball17
Date: 2026-02-11
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QSlider,
    QComboBox, QCheckBox, QSpinBox,
    QDoubleSpinBox, QPushButton, QMessageBox, QFileDialog,
    QScrollArea
)
from PyQt5.QtCore import Qt

from core.logger import logger
from ui.widgets.skill_list import SkillListWidget


class ParameterPanel(QWidget):
    """
    参数配置面板组件

    提供系统参数的配置和控制：
    - 捕获设置
    - 战斗配置
    - 高级设置
    - 日志配置
    - 界面设置
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 参数存储
        self.params = {}
        self.modified = False

        # 当前值显示
        self.value_labels = {}

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 创建容器 widget 和布局
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 捕获设置组
        capture_group = self.create_capture_group()
        main_layout.addWidget(capture_group)

        # 战斗配置组
        combat_group = self.create_combat_group()
        main_layout.addWidget(combat_group)

        # 高级设置组
        advanced_group = self.create_advanced_group()
        main_layout.addWidget(advanced_group)

        # 日志配置组
        log_group = self.create_log_group()
        main_layout.addWidget(log_group)

        # 界面设置组
        ui_group = self.create_ui_group()
        main_layout.addWidget(ui_group)

        # 配置管理按钮
        config_buttons = self.create_config_buttons()
        main_layout.addWidget(config_buttons)

        # 应用按钮
        apply_buttons = QHBoxLayout()
        self.btn_apply = QPushButton("应用所有设置")
        self.btn_apply.clicked.connect(self.apply_settings)
        self.btn_apply.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        self.btn_reset = QPushButton("恢复上次设置")
        self.btn_reset.clicked.connect(self.reset_settings)
        apply_buttons.addWidget(self.btn_apply)
        apply_buttons.addWidget(self.btn_reset)
        main_layout.addLayout(apply_buttons)

        main_layout.addStretch()

        # 设置滚动区域
        scroll_area.setWidget(container)

        # 设置主布局
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)

    def create_capture_group(self) -> QGroupBox:
        """创建捕获设置组"""
        group = QGroupBox("📹 捕获设置")
        layout = QVBoxLayout()

        # 目标 FPS
        fps_layout = QVBoxLayout()
        fps_label_layout = QHBoxLayout()
        fps_label = QLabel("目标 FPS:")
        self.fps_value_label = QLabel("30")
        fps_label_layout.addWidget(fps_label)
        fps_label_layout.addWidget(self.fps_value_label)
        fps_label_layout.addStretch()
        fps_layout.addLayout(fps_label_layout)

        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(10, 60)
        self.fps_slider.setValue(30)
        self.fps_slider.setTickPosition(QSlider.TicksBelow)
        self.fps_slider.setTickInterval(5)
        self.fps_slider.valueChanged.connect(
            lambda v: self.fps_value_label.setText(str(v))
        )
        fps_layout.addWidget(self.fps_slider)
        layout.addLayout(fps_layout)

        # 显示器选择
        monitor_layout = QHBoxLayout()
        monitor_label = QLabel("显示器:")
        self.monitor_combo = QComboBox()
        self.monitor_combo.addItem("主显示器", 0)
        self.monitor_combo.addItem("显示器 2", 1)
        self.monitor_combo.addItem("显示器 3", 2)
        monitor_layout.addWidget(monitor_label)
        monitor_layout.addWidget(self.monitor_combo)
        monitor_layout.addStretch()
        layout.addLayout(monitor_layout)

        # 检测模式
        mode_layout = QHBoxLayout()
        mode_label = QLabel("检测模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Mock (模拟)", "mock")
        self.mode_combo.addItem("YOLO (真实)", "yolo")
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        group.setLayout(layout)
        return group

    def create_combat_group(self) -> QGroupBox:
        """创建战斗配置组"""
        group = QGroupBox("⚔️ 战斗配置")
        layout = QVBoxLayout()

        # Y 轴对齐容差
        y_tolerance_layout = QVBoxLayout()
        y_label_layout = QHBoxLayout()
        y_label = QLabel("Y 轴对齐容差:")
        self.y_tolerance_value_label = QLabel("15")
        y_label_layout.addWidget(y_label)
        y_label_layout.addWidget(self.y_tolerance_value_label)
        y_label_layout.addStretch()
        y_tolerance_layout.addLayout(y_label_layout)

        self.y_tolerance_slider = QSlider(Qt.Horizontal)
        self.y_tolerance_slider.setRange(5, 50)
        self.y_tolerance_slider.setValue(15)
        self.y_tolerance_slider.setTickPosition(QSlider.TicksBelow)
        self.y_tolerance_slider.setTickInterval(5)
        self.y_tolerance_slider.valueChanged.connect(
            lambda v: self.y_tolerance_value_label.setText(str(v))
        )
        y_tolerance_layout.addWidget(self.y_tolerance_slider)
        layout.addLayout(y_tolerance_layout)

        # 攻击范围
        attack_range_layout = QVBoxLayout()
        range_label_layout = QHBoxLayout()
        range_label = QLabel("攻击范围:")
        self.attack_range_value_label = QLabel("100")
        range_label_layout.addWidget(range_label)
        range_label_layout.addWidget(self.attack_range_value_label)
        range_label_layout.addStretch()
        attack_range_layout.addLayout(range_label_layout)

        self.attack_range_slider = QSlider(Qt.Horizontal)
        self.attack_range_slider.setRange(50, 200)
        self.attack_range_slider.setValue(100)
        self.attack_range_slider.setTickPosition(QSlider.TicksBelow)
        self.attack_range_slider.setTickInterval(10)
        self.attack_range_slider.valueChanged.connect(
            lambda v: self.attack_range_value_label.setText(str(v))
        )
        attack_range_layout.addWidget(self.attack_range_slider)
        layout.addLayout(attack_range_layout)

        # 技能优先级
        skill_layout = QVBoxLayout()
        skill_label = QLabel("技能优先级 (拖拽排序):")
        skill_layout.addWidget(skill_label)

        self.skill_list = SkillListWidget()
        skill_layout.addWidget(self.skill_list)

        skill_buttons = QHBoxLayout()
        btn_add_skill = QPushButton("添加技能")
        btn_add_skill.clicked.connect(self.skill_list.add_new_skill)
        btn_remove_skill = QPushButton("删除选中")
        btn_remove_skill.clicked.connect(self.skill_list.remove_selected)
        skill_buttons.addWidget(btn_add_skill)
        skill_buttons.addWidget(btn_remove_skill)
        skill_layout.addLayout(skill_buttons)

        layout.addLayout(skill_layout)

        group.setLayout(layout)
        return group

    def create_advanced_group(self) -> QGroupBox:
        """创建高级设置组"""
        group = QGroupBox("🔧 高级设置")
        layout = QVBoxLayout()

        # 置信度阈值
        conf_layout = QVBoxLayout()
        conf_label_layout = QHBoxLayout()
        conf_label = QLabel("置信度阈值:")
        self.conf_value_label = QLabel("0.5")
        conf_label_layout.addWidget(conf_label)
        conf_label_layout.addWidget(self.conf_value_label)
        conf_label_layout.addStretch()
        conf_layout.addLayout(conf_label_layout)

        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(10, 90)  # 0.1-0.9
        self.conf_slider.setValue(50)
        self.conf_slider.setTickPosition(QSlider.TicksBelow)
        self.conf_slider.setTickInterval(10)
        self.conf_slider.valueChanged.connect(
            lambda v: self.conf_value_label.setText(f"{v/100:.2f}")
        )
        conf_layout.addWidget(self.conf_slider)
        layout.addLayout(conf_layout)

        # 房间清空超时
        timeout_layout = QVBoxLayout()
        timeout_label_layout = QHBoxLayout()
        timeout_label = QLabel("房间清空超时:")
        self.timeout_value_label = QLabel("2.0 秒")
        timeout_label_layout.addWidget(timeout_label)
        timeout_label_layout.addWidget(self.timeout_value_label)
        timeout_label_layout.addStretch()
        timeout_layout.addLayout(timeout_label_layout)

        self.timeout_slider = QSlider(Qt.Horizontal)
        self.timeout_slider.setRange(1, 10)
        self.timeout_slider.setValue(2)
        self.timeout_slider.setTickPosition(QSlider.TicksBelow)
        self.timeout_slider.setTickInterval(1)
        self.timeout_slider.valueChanged.connect(
            lambda v: self.timeout_value_label.setText(f"{v}.0 秒")
        )
        timeout_layout.addWidget(self.timeout_slider)
        layout.addLayout(timeout_layout)

        group.setLayout(layout)
        return group

    def create_log_group(self) -> QGroupBox:
        """创建日志配置组"""
        group = QGroupBox("📋 日志配置")
        layout = QVBoxLayout()

        # 日志级别
        level_layout = QHBoxLayout()
        level_label = QLabel("日志级别:")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("DEBUG", "DEBUG")
        self.log_level_combo.addItem("INFO", "INFO")
        self.log_level_combo.addItem("WARNING", "WARNING")
        self.log_level_combo.addItem("ERROR", "ERROR")
        self.log_level_combo.setCurrentIndex(1)  # 默认 INFO
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.log_level_combo)
        level_layout.addStretch()
        layout.addLayout(level_layout)

        # 日志保存
        self.save_log_checkbox = QCheckBox("保存日志到文件")
        self.save_log_checkbox.setChecked(True)
        layout.addWidget(self.save_log_checkbox)

        group.setLayout(layout)
        return group

    def create_ui_group(self) -> QGroupBox:
        """创建界面设置组"""
        group = QGroupBox("🎨 界面设置")
        layout = QVBoxLayout()

        # 主题选择
        theme_layout = QHBoxLayout()
        theme_label = QLabel("主题:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("暗黑 (默认)", "dark")
        self.theme_combo.addItem("明亮", "light")
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # 开机启动
        self.autostart_checkbox = QCheckBox("开机自动启动")
        self.autostart_checkbox.setChecked(False)
        layout.addWidget(self.autostart_checkbox)

        group.setLayout(layout)
        return group

    def create_config_buttons(self) -> QGroupBox:
        """创建配置管理按钮组"""
        group = QGroupBox("💾 配置管理")
        layout = QVBoxLayout()

        # 按钮行 1
        row1_layout = QHBoxLayout()
        btn_save = QPushButton("保存配置")
        btn_save.clicked.connect(self.save_config)
        btn_load = QPushButton("加载配置")
        btn_load.clicked.connect(self.load_config)
        btn_export = QPushButton("导出配置")
        btn_export.clicked.connect(self.export_config)
        row1_layout.addWidget(btn_save)
        row1_layout.addWidget(btn_load)
        row1_layout.addWidget(btn_export)
        layout.addLayout(row1_layout)

        # 按钮行 2
        row2_layout = QHBoxLayout()
        btn_import = QPushButton("导入配置")
        btn_import.clicked.connect(self.import_config)
        btn_reset = QPushButton("重置默认")
        btn_reset.clicked.connect(self.reset_defaults)
        row2_layout.addWidget(btn_import)
        row2_layout.addWidget(btn_reset)
        row2_layout.addStretch()
        layout.addLayout(row2_layout)

        group.setLayout(layout)
        return group

    def collect_params(self) -> dict:
        """
        收集当前所有参数

        Returns:
            参数字典
        """
        params = {
            "capture": {
                "target_fps": self.fps_slider.value(),
                "monitor_index": self.monitor_combo.currentData(),
                "detection_mode": self.mode_combo.currentData()
            },
            "combat": {
                "y_tolerance": self.y_tolerance_slider.value(),
                "attack_range": self.attack_range_slider.value(),
                "skill_priority": self.skill_list.get_skill_order()
            },
            "advanced": {
                "conf_threshold": self.conf_slider.value() / 100.0,
                "room_clear_timeout": float(self.timeout_slider.value())
            },
            "logging": {
                "log_level": self.log_level_combo.currentData(),
                "save_log": self.save_log_checkbox.isChecked()
            },
            "ui": {
                "theme": self.theme_combo.currentData(),
                "autostart": self.autostart_checkbox.isChecked()
            }
        }

        self.params = params
        return params

    def apply_settings(self):
        """应用所有设置"""
        try:
            # 收集参数
            params = self.collect_params()

            # TODO: 验证参数
            # TODO: 发送到核心引擎
            logger.info(f"应用设置: {params}")

            # 显示成功消息
            QMessageBox.information(
                self,
                "设置已应用",
                "新设置已成功应用到系统。"
            )

            self.modified = False

        except Exception as e:
            logger.error(f"应用设置失败: {e}")
            QMessageBox.critical(
                self,
                "应用失败",
                f"应用设置时发生错误:\n\n{e}"
            )

    def reset_settings(self):
        """恢复上次设置"""
        try:
            # TODO: 从配置文件加载设置
            logger.info("恢复上次设置")
            QMessageBox.information(
                self,
                "设置已恢复",
                "已恢复到上次保存的设置。"
            )

        except Exception as e:
            logger.error(f"恢复设置失败: {e}")

    def save_config(self):
        """保存配置"""
        try:
            # 收集参数
            params = self.collect_params()

            # 文件对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存配置",
                "",
                "YAML Files (*.yaml);;All Files (*)"
            )

            if file_path:
                # TODO: 保存到文件
                logger.info(f"保存配置到: {file_path}")
                QMessageBox.information(
                    self,
                    "配置已保存",
                    f"配置已保存到:\n\n{file_path}"
                )

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(
                self,
                "保存失败",
                f"保存配置时发生错误:\n\n{e}"
            )

    def load_config(self):
        """加载配置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "加载配置",
                "",
                "YAML Files (*.yaml);;All Files (*)"
            )

            if file_path:
                # TODO: 从文件加载配置
                logger.info(f"加载配置: {file_path}")
                QMessageBox.information(
                    self,
                    "配置已加载",
                    f"配置已从以下文件加载:\n\n{file_path}"
                )

        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            QMessageBox.critical(
                self,
                "加载失败",
                f"加载配置时发生错误:\n\n{e}"
            )

    def export_config(self):
        """导出配置"""
        logger.info("导出配置")
        # TODO: 实现配置导出

    def import_config(self):
        """导入配置"""
        logger.info("导入配置")
        # TODO: 实现配置导入

    def reset_defaults(self):
        """重置为默认值"""
        reply = QMessageBox.question(
            self,
            "重置确认",
            "确定要重置所有参数为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 重置所有控件为默认值
            self.fps_slider.setValue(30)
            self.monitor_combo.setCurrentIndex(0)
            self.mode_combo.setCurrentIndex(0)
            self.y_tolerance_slider.setValue(15)
            self.attack_range_slider.setValue(100)
            self.skill_list.set_skill_order(["a", "s", "d"], {"a": "普通攻击", "s": "技能", "d": "大招"})
            self.conf_slider.setValue(50)
            self.timeout_slider.setValue(2)
            self.log_level_combo.setCurrentIndex(1)
            self.save_log_checkbox.setChecked(True)
            self.theme_combo.setCurrentIndex(0)
            self.autostart_checkbox.setChecked(False)

            logger.info("参数已重置为默认值")
            QMessageBox.information(
                self,
                "重置完成",
                "所有参数已重置为默认值。"
            )

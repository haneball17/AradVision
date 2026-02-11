"""
状态面板组件

显示系统运行状态信息。

Author: haneball17
Date: 2026-02-11
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QProgressBar,
    QPushButton
)
from PyQt5.QtCore import Qt

from core.logger import logger


class StatusPanel(QWidget):
    """
    状态面板组件

    显示系统运行状态信息：
    - 性能指标（FPS、延迟、帧数、运行时长）
    - 决策状态（当前状态、持续时长、状态历史）
    - 检测信息（英雄、怪物、物品、门、房间）
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 状态数据
        self.current_state = {
            "fps": 0.0,
            "state": "STOPPED",
            "latency": 0.0,
            "frame_count": 0,
            "run_time": 0.0,
            "monsters": 0,
            "items": 0,
            "doors": 0,
            "room_cleared": False,
            "hero_detected": False
        }

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 性能指标组
        perf_group = self.create_performance_group()
        main_layout.addWidget(perf_group)

        # 决策状态组
        state_group = self.create_state_group()
        main_layout.addWidget(state_group)

        # 检测信息组
        detect_group = self.create_detection_group()
        main_layout.addWidget(detect_group)

        # 快速控制组
        control_group = self.create_control_group()
        main_layout.addWidget(control_group)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def create_performance_group(self) -> QGroupBox:
        """创建性能指标组"""
        group = QGroupBox("📊 性能指标")
        layout = QVBoxLayout()

        # FPS 进度条
        fps_layout = QHBoxLayout()
        fps_label = QLabel("FPS:")
        self.fps_bar = QProgressBar()
        self.fps_bar.setRange(0, 60)
        self.fps_bar.setValue(0)
        self.fps_bar.setFormat("%v")
        fps_label.setFixedWidth(50)
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_bar)
        layout.addLayout(fps_layout)

        # 延迟
        self.latency_label = QLabel("延迟: -- ms")
        layout.addWidget(self.latency_label)

        # 帧数和时长
        info_layout = QHBoxLayout()
        self.frame_count_label = QLabel("帧数: 0")
        self.run_time_label = QLabel("运行时长: 00:00:00")
        info_layout.addWidget(self.frame_count_label)
        info_layout.addWidget(self.run_time_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        group.setLayout(layout)
        return group

    def create_state_group(self) -> QGroupBox:
        """创建决策状态组"""
        group = QGroupBox("🤖 决策状态")
        layout = QVBoxLayout()

        # 当前状态
        self.state_label = QLabel("当前状态: STOPPED")
        self.state_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.state_label)

        # 持续时长
        self.duration_label = QLabel("持续时长: 0.0 秒")
        layout.addWidget(self.duration_label)

        # 状态历史
        self.history_label = QLabel("状态历史: -")
        layout.addWidget(self.history_label)

        group.setLayout(layout)
        return group

    def create_detection_group(self) -> QGroupBox:
        """创建检测信息组"""
        group = QGroupBox("👁️ 检测信息")
        layout = QVBoxLayout()

        # 英雄
        self.hero_label = QLabel("👤 英雄: ✗ 未检测")
        layout.addWidget(self.hero_label)

        # 怪物
        self.monster_label = QLabel("👹 怪物: 0 个")
        layout.addWidget(self.monster_label)

        # 物品
        self.item_label = QLabel("💎 物品: 0 个")
        layout.addWidget(self.item_label)

        # 门
        self.door_label = QLabel("🚪 门: 0 个")
        layout.addWidget(self.door_label)

        # 房间状态
        self.room_label = QLabel("📦 房间: 未清空")
        layout.addWidget(self.room_label)

        group.setLayout(layout)
        return group

    def create_control_group(self) -> QGroupBox:
        """创建快速控制组"""
        group = QGroupBox("🎮 快速控制")
        layout = QHBoxLayout()

        # 启动按钮
        self.btn_start = QPushButton("▶️ 启动")
        self.btn_start.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.btn_start)

        # 暂停按钮
        self.btn_pause = QPushButton("⏸️ 暂停")
        self.btn_pause.clicked.connect(self.on_pause_clicked)
        self.btn_pause.setEnabled(False)
        layout.addWidget(self.btn_pause)

        # 停止按钮
        self.btn_stop = QPushButton("⏹️ 停止")
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        group.setLayout(layout)
        return group

    def update_status(self, status: dict):
        """
        更新状态显示

        Args:
            status: 状态字典
        """
        try:
            # 更新性能指标
            fps = status.get("fps", 0.0)
            self.fps_bar.setValue(int(fps))
            self.latency_label.setText(f"延迟: {status.get('latency', 0.0):.1f} ms")
            self.frame_count_label.setText(f"帧数: {status.get('frame_count', 0)}")

            # 更新运行时长
            run_time = status.get("run_time", 0.0)
            hours = int(run_time // 3600)
            minutes = int((run_time % 3600) // 60)
            seconds = int(run_time % 60)
            self.run_time_label.setText(f"运行时长: {hours:02d}:{minutes:02d}:{seconds:02d}")

            # 更新决策状态
            state = status.get("state", "STOPPED")
            self.state_label.setText(f"当前状态: {state}")
            self.duration_label.setText(f"持续时长: {status.get('duration', 0.0):.1f} 秒")
            self.history_label.setText(f"状态历史: {status.get('history', '-')}")

            # 更新检测信息
            hero_detected = status.get("hero_detected", False)
            self.hero_label.setText(f"👤 英雄: {'✓ 已检测' if hero_detected else '✗ 未检测'}")

            self.monster_label.setText(f"👹 怪物: {status.get('monsters', 0)} 个")
            self.item_label.setText(f"💎 物品: {status.get('items', 0)} 个")
            self.door_label.setText(f"🚪 门: {status.get('doors', 0)} 个")

            room_cleared = status.get("room_cleared", False)
            self.room_label.setText(f"📦 房间: {'已清空' if room_cleared else '未清空'}")

            # 更新按钮状态
            is_running = state != "STOPPED"
            self.btn_start.setEnabled(not is_running)
            self.btn_pause.setEnabled(is_running)
            self.btn_stop.setEnabled(is_running)

        except Exception as e:
            logger.error(f"更新状态显示失败: {e}")

    # ==================== 按钮事件 ====================

    def on_start_clicked(self):
        """启动按钮点击事件"""
        logger.info("快速控制: 启动系统")
        # TODO: 通知主窗口启动系统
        from PyQt5.QtCore import pyqtSignal
        if hasattr(self.parent(), 'start_system'):
            self.parent().start_system()

    def on_pause_clicked(self):
        """暂停按钮点击事件"""
        logger.info("快速控制: 暂停系统")
        # TODO: 通知主窗口暂停系统
        if hasattr(self.parent(), 'toggle_pause'):
            self.parent().toggle_pause()

    def on_stop_clicked(self):
        """停止按钮点击事件"""
        logger.info("快速控制: 停止系统")
        # TODO: 通知主窗口停止系统
        if hasattr(self.parent(), 'stop_system'):
            self.parent().stop_system()

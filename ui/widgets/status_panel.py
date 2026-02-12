"""
状态面板组件

显示系统运行状态信息。

Author: haneball17
Date: 2026-06-02
"""
# 尝试导入 cv2，如果不可用则跳过相关功能
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

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
        layout.addLayout(info_layout)

        group.setLayout(layout)
        return group

    def create_state_group(self) -> QGroupBox:
        """创建决策状态组"""
        group = QGroupBox("📊 决策状态")
        layout = QVBoxLayout()

        # 当前状态
        state_header = QLabel("当前状态: STOPPED")
        layout.addWidget(state_header)

        # 状态历史
        history_label = QLabel("状态历史:")
        layout.addWidget(history_label)

        self.state_history_labels = []
        for i in range(5):
            label = QLabel(f"  {i+1}. STOPPED")
            label.setStyleSheet("color: #888888;")
            layout.addWidget(label)
            self.state_history_labels.append(label)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_detection_group(self) -> QGroupBox:
        """创建检测信息组"""
        group = QGroupBox("🔍 检测信息")
        layout = QVBoxLayout()

        self.monster_label = QLabel("怪物: 0")
        self.item_label = QLabel("物品: 0")
        self.door_label = QLabel("门: 0")
        self.hero_label = QLabel("英雄: --")

        layout.addWidget(self.monster_label)
        layout.addWidget(self.item_label)
        layout.addWidget(self.door_label)
        layout.addWidget(self.hero_label)

        group.setLayout(layout)
        return group

    def create_control_group(self) -> QGroupBox:
        """创建快速控制组"""
        group = QGroupBox("⚡ 快速控制")
        layout = QVBoxLayout()

        # 启动/停止按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ 启动")
        self.stop_btn = QPushButton("⏸ 停止")

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def update_status(self, status: dict):
        """更新状态显示"""
        for key, value in status.items():
            if key in self.current_state:
                self.current_state[key] = value

        # 更新 FPS 和延迟
        if "fps" in status:
            self.fps_bar.setValue(int(min(status["fps"], 60)))
        if "latency" in status:
            self.latency_label.setText(f"延迟: {status['latency']:.0f} ms")
        if "frame_count" in status:
            self.frame_count_label.setText(f"帧数: {status['frame_count']}")
        if "run_time" in status:
            run_seconds = int(status["run_time"])
            minutes = run_seconds // 60
            seconds = run_seconds % 60
            self.run_time_label.setText(f"运行时长: {minutes:02d}:{seconds:02d}")

        # 更新检测信息（支持两种键名：monster_count/monsters）
        monster_count = status.get("monster_count") or status.get("monsters", 0)
        item_count = status.get("item_count") or status.get("items", 0)
        door_count = status.get("door_count") or status.get("doors", 0)

        self.monster_label.setText(f"怪物: {monster_count}")
        self.item_label.setText(f"物品: {item_count}")
        self.door_label.setText(f"门: {door_count}")

        # 更新英雄检测
        hero_detected = status.get("hero_detected", False)
        if hero_detected:
            self.hero_label.setText("英雄: 已检测")
            self.hero_label.setStyleSheet("color: #4CAF50;")
        else:
            self.hero_label.setText("英雄: --")
            self.hero_label.setStyleSheet("color: #888888;")

        # 更新状态历史
        if "state" in status:
            state_str = status["state"]
            # 更新历史记录
            for i, label in enumerate(self.state_history_labels):
                if i < len(self.state_history_labels) - 1:
                    # 移动现有记录
                    label.setText(f"  {i+1}. {state_str}")
                elif i == 0:
                    # 添加新记录
                    label.setText(f"  {i+1}. {state_str}")

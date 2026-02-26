"""
采集控制条组件

提供窗口选择、开始/停止、暂停/继续按钮与状态展示。
"""

from typing import Iterable, List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QSizePolicy,
)


class CaptureControlBar(QWidget):
    """采集控制条。"""

    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    pause_toggled = pyqtSignal(bool)
    refresh_windows_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CaptureControlBar")
        self._compact_mode = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.title_label = QLabel("实时采集控制")
        self.title_label.setObjectName("SectionTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        window_row = QHBoxLayout()
        window_row.setContentsMargins(0, 0, 0, 0)
        window_row.setSpacing(8)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(8)

        self.window_combo = QComboBox()
        self.window_combo.setMinimumWidth(220)
        self.window_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.refresh_button = QPushButton("刷新窗口")
        self.refresh_button.setObjectName("GhostButton")

        self.start_button = QPushButton("开始")
        self.start_button.setObjectName("PrimaryButton")
        self.stop_button = QPushButton("停止")
        self.stop_button.setObjectName("DangerButton")
        self.pause_button = QPushButton("暂停")
        self.pause_button.setCheckable(True)

        self.status_label = QLabel("状态: 空闲")
        self.status_label.setObjectName("StatusPill")
        self.status_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.status_label.setMinimumWidth(0)

        self.refresh_button.clicked.connect(self.refresh_windows_requested.emit)
        self.start_button.clicked.connect(self.start_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.pause_button.toggled.connect(self._on_pause_toggled)

        self.window_label = QLabel("窗口")
        self.action_label = QLabel("动作")

        window_row.addWidget(self.window_label)
        window_row.addWidget(self.window_combo, stretch=1)
        window_row.addWidget(self.refresh_button)

        action_row.addWidget(self.action_label)
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.stop_button)
        action_row.addWidget(self.pause_button)
        action_row.addStretch()
        action_row.addWidget(self.status_label)

        layout.addLayout(header_layout)
        layout.addLayout(window_row)
        layout.addLayout(action_row)

        self.set_window_options([])

    def _on_pause_toggled(self, checked: bool) -> None:
        """切换暂停状态并同步按钮文本。"""
        self.pause_button.setText("继续" if checked else "暂停")
        self.pause_toggled.emit(checked)

    def set_status(self, status_text: str) -> None:
        """更新状态显示。"""
        if self._compact_mode and len(status_text) > 14:
            status_text = status_text[:11] + "..."
        self.status_label.setText(f"状态: {status_text}")

    def set_compact_mode(self, compact: bool) -> None:
        """切换紧凑模式，减小高缩放场景的横向占用。"""
        self._compact_mode = compact
        self.window_combo.setMinimumWidth(160 if compact else 220)

    def selected_window_title(self) -> str:
        """获取当前选中的窗口标题。"""
        return self.window_combo.currentText().strip()

    def set_window_options(self, titles: Iterable[str], selected: str = "") -> None:
        """设置窗口列表并尽量保持选中项。"""
        normalized: List[str] = []
        for title in titles:
            value = str(title).strip()
            if not value:
                continue
            if value not in normalized:
                normalized.append(value)

        if not normalized:
            normalized = ["<未发现可用窗口>"]

        self.window_combo.blockSignals(True)
        self.window_combo.clear()
        self.window_combo.addItems(normalized)

        target = selected.strip()
        if target:
            index = self.window_combo.findText(target)
            if index >= 0:
                self.window_combo.setCurrentIndex(index)
        self.window_combo.blockSignals(False)

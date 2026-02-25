"""
采集控制条组件

提供窗口选择、开始/停止、暂停/继续按钮与状态展示。
"""

from typing import Iterable, List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
)


class CaptureControlBar(QWidget):
    """采集控制条。"""

    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    pause_toggled = pyqtSignal(bool)
    refresh_windows_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.window_combo = QComboBox()
        self.window_combo.setMinimumWidth(320)
        self.refresh_button = QPushButton("刷新窗口")

        self.start_button = QPushButton("开始")
        self.stop_button = QPushButton("停止")
        self.pause_button = QPushButton("暂停")
        self.pause_button.setCheckable(True)

        self.status_label = QLabel("状态: 空闲")

        self.refresh_button.clicked.connect(self.refresh_windows_requested.emit)
        self.start_button.clicked.connect(self.start_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.pause_button.toggled.connect(self._on_pause_toggled)

        layout.addWidget(QLabel("窗口:"))
        layout.addWidget(self.window_combo)
        layout.addWidget(self.refresh_button)
        layout.addSpacing(16)
        layout.addWidget(QLabel("采集:"))
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.pause_button)
        layout.addSpacing(12)
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.set_window_options([])

    def _on_pause_toggled(self, checked: bool) -> None:
        """切换暂停状态并同步按钮文本。"""
        self.pause_button.setText("继续" if checked else "暂停")
        self.pause_toggled.emit(checked)

    def set_status(self, status_text: str) -> None:
        """更新状态显示。"""
        self.status_label.setText(f"状态: {status_text}")

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

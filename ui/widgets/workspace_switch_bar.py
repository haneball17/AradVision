"""
工作区切换条组件

提供“采集工作区 / 预标注工作区”的统一切换入口。
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup


class WorkspaceSwitchBar(QWidget):
    """工作区切换条。"""

    workspace_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.capture_button = QPushButton("采集工作区")
        self.capture_button.setCheckable(True)
        self.capture_button.setChecked(True)
        self.capture_button.clicked.connect(lambda: self.workspace_changed.emit("capture"))

        self.pseudo_button = QPushButton("预标注工作区")
        self.pseudo_button.setCheckable(True)
        self.pseudo_button.clicked.connect(lambda: self.workspace_changed.emit("pseudo"))

        self._button_group.addButton(self.capture_button)
        self._button_group.addButton(self.pseudo_button)

        layout.addWidget(self.capture_button)
        layout.addWidget(self.pseudo_button)
        layout.addStretch()

    def set_workspace(self, workspace: str) -> None:
        """外部同步切换状态。"""
        if workspace == "capture":
            self.capture_button.setChecked(True)
        elif workspace == "pseudo":
            self.pseudo_button.setChecked(True)

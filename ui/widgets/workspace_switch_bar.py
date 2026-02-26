"""
工作区切换条组件

提供“采集工作区 / 筛选工作区 / 预标注工作区”的统一切换入口。
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup, QLabel


class WorkspaceSwitchBar(QWidget):
    """工作区切换条。"""

    workspace_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkspaceSwitchBar")
        self._compact_mode = False

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.title_label = QLabel("工作区")
        self.title_label.setObjectName("SubSectionTitle")

        self.capture_button = QPushButton("采集工作区")
        self.capture_button.setObjectName("SegmentButton")
        self.capture_button.setCheckable(True)
        self.capture_button.setChecked(True)
        self.capture_button.clicked.connect(lambda: self.workspace_changed.emit("capture"))

        self.curation_button = QPushButton("筛选工作区")
        self.curation_button.setObjectName("SegmentButton")
        self.curation_button.setCheckable(True)
        self.curation_button.clicked.connect(lambda: self.workspace_changed.emit("curation"))

        self.pseudo_button = QPushButton("预标注工作区")
        self.pseudo_button.setObjectName("SegmentButton")
        self.pseudo_button.setCheckable(True)
        self.pseudo_button.clicked.connect(lambda: self.workspace_changed.emit("pseudo"))

        self.capture_button.setMinimumHeight(34)
        self.curation_button.setMinimumHeight(34)
        self.pseudo_button.setMinimumHeight(34)

        self._button_group.addButton(self.capture_button)
        self._button_group.addButton(self.curation_button)
        self._button_group.addButton(self.pseudo_button)

        layout.addWidget(self.title_label)
        layout.addWidget(self.capture_button)
        layout.addWidget(self.curation_button)
        layout.addWidget(self.pseudo_button)
        layout.addStretch()

    def set_workspace(self, workspace: str) -> None:
        """外部同步切换状态。"""
        if workspace == "capture":
            self.capture_button.setChecked(True)
        elif workspace == "curation":
            self.curation_button.setChecked(True)
        elif workspace == "pseudo":
            self.pseudo_button.setChecked(True)

    def set_compact_mode(self, compact: bool) -> None:
        """切换紧凑模式，降低高缩放场景的顶部占高。"""
        self._compact_mode = compact
        self.title_label.setVisible(not compact)
        height = 30 if compact else 34
        self.capture_button.setMinimumHeight(height)
        self.curation_button.setMinimumHeight(height)
        self.pseudo_button.setMinimumHeight(height)

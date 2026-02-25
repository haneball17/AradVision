"""
缩略图条组件

当前版本先提供文件列表流式展示，后续可升级为真实缩略图缓存渲染。
"""

from typing import List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel


class FrameStrip(QWidget):
    """缩略图时间流组件。"""

    frame_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("缩略图时间流（文件列表）"))

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def set_frames(self, image_rel_paths: List[str]) -> None:
        """刷新帧列表。"""
        self.list_widget.clear()
        for path in image_rel_paths:
            self.list_widget.addItem(QListWidgetItem(path))

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """向外通知当前选中帧。"""
        self.frame_selected.emit(item.text())

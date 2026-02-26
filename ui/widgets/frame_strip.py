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
        self.setObjectName("FrameStrip")
        self._collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.title_label = QLabel("时间线文件流")
        self.title_label.setObjectName("SubSectionTitle")
        layout.addWidget(self.title_label)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def set_frames(self, image_rel_paths: List[str]) -> None:
        """刷新帧列表。"""
        self.list_widget.clear()
        for path in image_rel_paths:
            self.list_widget.addItem(QListWidgetItem(path))

    def append_frame(self, image_rel_path: str) -> None:
        """增量追加单个帧路径。"""
        self.list_widget.addItem(QListWidgetItem(image_rel_path))
        self.list_widget.scrollToBottom()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """向外通知当前选中帧。"""
        self.frame_selected.emit(item.text())

    def set_collapsed(self, collapsed: bool) -> None:
        """切换折叠状态，用于高缩放场景释放纵向空间。"""
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed
        self.setVisible(not collapsed)

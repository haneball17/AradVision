"""
缩略图条组件

提供可折叠的样本流明细抽屉，支持缩略图预览与单帧选中。
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QSizePolicy,
)

from ui.widgets.thumbnail_cache import ThumbnailCache


class FrameStrip(QWidget):
    """缩略图时间流组件。"""

    frame_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FrameStrip")
        self._user_collapsed = True
        self._force_collapsed = False
        self._path_resolver: Optional[Callable[[str], Optional[str]]] = None
        self._density_mode = "default"
        self._cache = ThumbnailCache(QSize(112, 63), max_items=768)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(42)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.title_label = QLabel("样本流明细")
        self.title_label.setObjectName("SubSectionTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.toggle_button = QPushButton("展开明细")
        self.toggle_button.setObjectName("GhostButton")
        self.toggle_button.clicked.connect(self._on_toggle_clicked)
        header_layout.addWidget(self.toggle_button)
        layout.addLayout(header_layout)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setFlow(QListWidget.LeftToRight)
        self.list_widget.setWrapping(False)
        self.list_widget.setSpacing(8)
        self.list_widget.setWordWrap(True)
        self.list_widget.setIconSize(QSize(112, 63))
        self.list_widget.setGridSize(QSize(132, 100))
        self.list_widget.setMinimumHeight(108)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
        self.set_density_mode("default")
        self._apply_collapsed_state()

    def set_density_mode(self, mode: str) -> None:
        """设置明细条密度模式。"""
        normalized = mode if mode in {"default", "compact", "dense"} else "default"
        if normalized == self._density_mode:
            return
        self._density_mode = normalized

        if normalized == "default":
            icon_size = QSize(112, 63)
            grid_size = QSize(132, 100)
            min_height = 108
        elif normalized == "compact":
            icon_size = QSize(102, 58)
            grid_size = QSize(122, 94)
            min_height = 100
        else:
            icon_size = QSize(92, 52)
            grid_size = QSize(110, 84)
            min_height = 90

        self._cache = ThumbnailCache(icon_size, max_items=768)
        self.list_widget.setIconSize(icon_size)
        self.list_widget.setGridSize(grid_size)
        self.list_widget.setMinimumHeight(min_height)

    def set_image_path_resolver(self, resolver: Optional[Callable[[str], Optional[str]]]) -> None:
        """设置相对路径到绝对路径的解析器。"""
        self._path_resolver = resolver

    def set_frames(self, image_rel_paths: List[str]) -> None:
        """刷新帧列表。"""
        self.list_widget.clear()
        for path in image_rel_paths:
            self.list_widget.addItem(self._build_item(path))

    def append_frame(self, image_rel_path: str) -> None:
        """增量追加单个帧路径。"""
        self.list_widget.addItem(self._build_item(image_rel_path))
        self.list_widget.scrollToBottom()

    def _build_item(self, image_rel_path: str) -> QListWidgetItem:
        """构建带缩略图的帧项。"""
        item = QListWidgetItem(Path(image_rel_path).name or image_rel_path)
        item.setData(Qt.UserRole, image_rel_path)
        resolved_path = ""
        if self._path_resolver is not None:
            try:
                resolved = self._path_resolver(image_rel_path)
                if resolved:
                    resolved_path = str(resolved)
            except Exception:
                resolved_path = ""
        if not resolved_path and Path(image_rel_path).exists():
            resolved_path = image_rel_path
        pixmap = self._cache.get(resolved_path)
        item.setIcon(QIcon(pixmap))
        item.setToolTip(image_rel_path)
        return item

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """向外通知当前选中帧。"""
        rel_path = str(item.data(Qt.UserRole) or item.text())
        self.frame_selected.emit(rel_path)

    def select_frame(self, image_rel_path: str) -> None:
        """按相对路径定位并选中对应帧。"""
        target = str(image_rel_path).strip()
        if not target:
            return
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            if item is None:
                continue
            rel = str(item.data(Qt.UserRole) or "")
            if rel != target:
                continue
            self.list_widget.setCurrentItem(item)
            self.list_widget.scrollToItem(item)
            return

    def _on_toggle_clicked(self) -> None:
        """切换明细抽屉展开状态。"""
        self.set_collapsed(not self._user_collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        """设置用户折叠状态。"""
        self._user_collapsed = collapsed
        self._apply_collapsed_state()

    def set_force_collapsed(self, collapsed: bool) -> None:
        """设置强制折叠状态（高缩放紧凑模式）。"""
        self._force_collapsed = collapsed
        self._apply_collapsed_state()

    def is_content_visible(self) -> bool:
        """当前明细列表是否可见。"""
        return self.list_widget.isVisible()

    def _apply_collapsed_state(self) -> None:
        """根据用户状态与强制状态刷新界面。"""
        effective_collapsed = self._user_collapsed or self._force_collapsed
        self.list_widget.setVisible(not effective_collapsed)
        self.toggle_button.setText("展开明细" if effective_collapsed else "收起明细")
        self.setMinimumHeight(42 if effective_collapsed else 120)

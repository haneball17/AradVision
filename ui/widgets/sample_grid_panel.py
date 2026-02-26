"""
样本网格面板组件

用于作为筛选工作区主视图，提供：
1. 网格浏览
2. 关键词过滤
3. 批量场景修正
"""

from typing import Dict, List

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSizePolicy,
)


class SampleGridPanel(QWidget):
    """样本网格主视图。"""

    sample_activated = pyqtSignal(dict)
    selection_changed = pyqtSignal(object)
    batch_scene_update_requested = pyqtSignal(object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SampleGridPanel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._all_samples: List[Dict[str, object]] = []
        self._filtered_samples: List[Dict[str, object]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("样本网格（主视图）")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索 sample_id / scene / 文件名")
        toolbar.addWidget(self.search_edit, stretch=1)

        self.scene_combo = QComboBox()
        self.scene_combo.addItems(["combat", "navigate", "loot", "boss", "other"])
        toolbar.addWidget(self.scene_combo)

        self.batch_apply_button = QPushButton("批量修正场景")
        self.batch_apply_button.setObjectName("GhostButton")
        toolbar.addWidget(self.batch_apply_button)

        self.selection_label = QLabel("已选 0 / 共 0")
        self.selection_label.setObjectName("HintText")
        toolbar.addWidget(self.selection_label)
        layout.addLayout(toolbar)

        self.grid_list = QListWidget()
        self.grid_list.setViewMode(QListWidget.IconMode)
        self.grid_list.setResizeMode(QListWidget.Adjust)
        self.grid_list.setMovement(QListWidget.Static)
        self.grid_list.setWrapping(True)
        self.grid_list.setSpacing(8)
        self.grid_list.setWordWrap(True)
        self.grid_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.grid_list.setIconSize(QSize(180, 96))
        self.grid_list.setGridSize(QSize(210, 140))
        self.grid_list.setUniformItemSizes(False)
        layout.addWidget(self.grid_list, stretch=1)

        self.search_edit.textChanged.connect(self._apply_filter)
        self.batch_apply_button.clicked.connect(self._on_batch_apply_clicked)
        self.grid_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.grid_list.itemDoubleClicked.connect(self._on_item_double_clicked)

    def set_samples(self, samples: List[Dict[str, object]]) -> None:
        """刷新全量样本。"""
        self._all_samples = list(samples)
        self._apply_filter()

    def append_sample(self, sample: Dict[str, object]) -> None:
        """增量追加样本。"""
        self._all_samples.append(sample)
        self._apply_filter()

    def selected_sample_ids(self) -> List[str]:
        """返回当前选中样本 ID 列表。"""
        result: List[str] = []
        for item in self.grid_list.selectedItems():
            sample = item.data(Qt.UserRole)
            if isinstance(sample, dict):
                result.append(str(sample.get("sample_id", "")))
        return [sid for sid in result if sid]

    def _build_item_text(self, sample: Dict[str, object]) -> str:
        """构建网格卡片文本。"""
        sample_id = str(sample.get("sample_id", "-"))
        scene = str(sample.get("scene", "other"))
        image_path = str(sample.get("image_rel_path", sample.get("image_path", "-")))
        ts = sample.get("timestamp_iso")
        if ts:
            ts_text = str(ts)[:19]
        else:
            ts_text = str(sample.get("timestamp_ms", "-"))

        return f"{sample_id}\nscene: {scene}\n{ts_text}\n{image_path}"

    def _apply_filter(self) -> None:
        """按搜索词过滤并刷新网格。"""
        keyword = self.search_edit.text().strip().lower()
        if not keyword:
            self._filtered_samples = list(self._all_samples)
        else:
            filtered: List[Dict[str, object]] = []
            for sample in self._all_samples:
                text = " ".join(
                    [
                        str(sample.get("sample_id", "")),
                        str(sample.get("scene", "")),
                        str(sample.get("image_rel_path", sample.get("image_path", ""))),
                    ]
                ).lower()
                if keyword in text:
                    filtered.append(sample)
            self._filtered_samples = filtered

        self.grid_list.clear()
        for sample in self._filtered_samples:
            item = QListWidgetItem(self._build_item_text(sample))
            item.setData(Qt.UserRole, sample)
            item.setToolTip(self._build_item_text(sample))
            self.grid_list.addItem(item)

        self._on_selection_changed()

    def _on_selection_changed(self) -> None:
        """更新选中计数并广播选中样本。"""
        selected_ids = self.selected_sample_ids()
        self.selection_label.setText(
            f"已选 {len(selected_ids)} / 共 {len(self._filtered_samples)}"
        )
        self.selection_changed.emit(selected_ids)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """双击卡片后回传样本对象。"""
        sample = item.data(Qt.UserRole)
        if isinstance(sample, dict):
            self.sample_activated.emit(sample)

    def _on_batch_apply_clicked(self) -> None:
        """触发批量场景修正请求。"""
        selected_ids = self.selected_sample_ids()
        if not selected_ids:
            return
        scene = self.scene_combo.currentText().strip()
        if not scene:
            return
        self.batch_scene_update_requested.emit(selected_ids, scene)

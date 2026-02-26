"""
样本网格面板组件

用于作为筛选工作区主视图，提供：
1. 网格浏览
2. 关键词过滤
3. 批量场景修正
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
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

from ui.widgets.thumbnail_cache import ThumbnailCache


class SampleGridPanel(QWidget):
    """样本网格主视图。"""

    sample_activated = pyqtSignal(dict)
    selection_changed = pyqtSignal(object)
    batch_scene_update_requested = pyqtSignal(object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SampleGridPanel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(280)

        self._all_samples: List[Dict[str, object]] = []
        self._filtered_samples: List[Dict[str, object]] = []
        self._image_path_resolver: Optional[Callable[[Dict[str, object]], Optional[str]]] = None
        self._density_mode = "default"
        self._thumbnail_cache = ThumbnailCache(QSize(188, 106), max_items=1024)
        self._thumbnail_cursor = 0
        self._thumbnail_timer = QTimer(self)
        self._thumbnail_timer.setInterval(0)
        self._thumbnail_timer.timeout.connect(self._load_thumbnail_chunk)

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
        self.grid_list.setSpacing(10)
        self.grid_list.setWordWrap(True)
        self.grid_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.grid_list.setIconSize(QSize(188, 106))
        self.grid_list.setGridSize(QSize(220, 168))
        self.grid_list.setUniformItemSizes(False)
        layout.addWidget(self.grid_list, stretch=1)

        self.search_edit.textChanged.connect(self._apply_filter)
        self.batch_apply_button.clicked.connect(self._on_batch_apply_clicked)
        self.grid_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.grid_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.set_density_mode("default")

    def set_density_mode(self, mode: str) -> None:
        """设置网格密度模式，适配不同缩放与窗口尺寸。"""
        normalized = mode if mode in {"default", "compact", "dense"} else "default"
        if normalized == self._density_mode and self.grid_list.count() > 0:
            return
        self._density_mode = normalized

        if normalized == "default":
            icon_size = QSize(188, 106)
            grid_size = QSize(232, 176)
            spacing = 10
            button_text = "批量修正场景"
            show_selection = True
        elif normalized == "compact":
            icon_size = QSize(170, 96)
            grid_size = QSize(206, 158)
            spacing = 8
            button_text = "批量修正"
            show_selection = True
        else:
            icon_size = QSize(150, 84)
            grid_size = QSize(178, 140)
            spacing = 7
            button_text = "修正"
            show_selection = False

        self._thumbnail_cache = ThumbnailCache(icon_size, max_items=1024)
        self.grid_list.setIconSize(icon_size)
        self.grid_list.setGridSize(grid_size)
        self.grid_list.setSpacing(spacing)
        self.batch_apply_button.setText(button_text)
        self.selection_label.setVisible(show_selection)
        self._apply_filter()

    def set_image_path_resolver(
        self, resolver: Optional[Callable[[Dict[str, object]], Optional[str]]]
    ) -> None:
        """设置样本图像路径解析器。"""
        self._image_path_resolver = resolver

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
        sample_id = str(sample.get("sample_id", "-"))[-12:]
        scene = str(sample.get("scene", "other"))
        image_name = Path(
            str(sample.get("image_rel_path", sample.get("image_path", ""))).strip() or "-"
        ).name
        ts_text = self._format_sample_time(sample)

        if self._density_mode == "default":
            return f"{scene}  {ts_text}\n{image_name}"
        if self._density_mode == "compact":
            return f"{scene}  {ts_text}\n{sample_id}"
        return f"{scene} {ts_text}"

    def _build_item_tooltip(self, sample: Dict[str, object]) -> str:
        """构建完整样本提示信息。"""
        sample_id = str(sample.get("sample_id", "-"))
        scene = str(sample.get("scene", "other"))
        image_path = str(sample.get("image_rel_path", sample.get("image_path", "-")))
        ts_text = self._format_sample_time(sample, full=True)
        return (
            f"sample_id: {sample_id}\n"
            f"scene: {scene}\n"
            f"time: {ts_text}\n"
            f"file: {image_path}"
        )

    def _format_sample_time(self, sample: Dict[str, object], full: bool = False) -> str:
        """格式化样本时间文本。"""
        ts_iso = str(sample.get("timestamp_iso", "")).strip()
        if ts_iso:
            text = ts_iso.replace("T", " ").replace("Z", "")
            if full:
                return text
            return text[11:19] if len(text) >= 19 else text

        ts_ms = sample.get("timestamp_ms")
        try:
            ts_value = int(ts_ms)
            dt = datetime.fromtimestamp(ts_value / 1000.0)
            return dt.strftime("%Y-%m-%d %H:%M:%S") if full else dt.strftime("%H:%M:%S")
        except Exception:
            return str(ts_ms if ts_ms is not None else "-")

    def _resolve_image_path(self, sample: Dict[str, object]) -> str:
        """解析样本对应的图片路径。"""
        if self._image_path_resolver is not None:
            try:
                resolved = self._image_path_resolver(sample)
                if resolved:
                    return str(resolved)
            except Exception:
                pass

        candidates = [
            sample.get("image_abs_path"),
            sample.get("image_path"),
            sample.get("image_rel_path"),
        ]
        for candidate in candidates:
            text = str(candidate or "").strip()
            if not text:
                continue
            path = Path(text)
            if path.exists():
                return str(path)
        return ""

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

        self._thumbnail_timer.stop()
        self._thumbnail_cursor = 0
        self.grid_list.clear()
        for sample in self._filtered_samples:
            item = QListWidgetItem(self._build_item_text(sample))
            item.setData(Qt.UserRole, sample)
            item.setToolTip(self._build_item_tooltip(sample))
            item.setTextAlignment(int(Qt.AlignLeft | Qt.AlignTop))
            image_path = self._resolve_image_path(sample)
            item.setData(Qt.UserRole + 1, image_path)
            item.setIcon(QIcon(self._thumbnail_cache.placeholder()))
            self.grid_list.addItem(item)

        self._thumbnail_timer.start()
        self._on_selection_changed()

    def _load_thumbnail_chunk(self) -> None:
        """分块加载缩略图，避免大批样本一次性阻塞 UI。"""
        total = self.grid_list.count()
        if total <= 0:
            self._thumbnail_timer.stop()
            return

        chunk_size = 18
        loaded = 0
        while self._thumbnail_cursor < total and loaded < chunk_size:
            item = self.grid_list.item(self._thumbnail_cursor)
            self._thumbnail_cursor += 1
            if item is None:
                continue
            image_path = str(item.data(Qt.UserRole + 1) or "").strip()
            if not image_path:
                continue
            pixmap = self._thumbnail_cache.get(image_path)
            item.setIcon(QIcon(pixmap))
            loaded += 1

        if self._thumbnail_cursor >= total:
            self._thumbnail_timer.stop()

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

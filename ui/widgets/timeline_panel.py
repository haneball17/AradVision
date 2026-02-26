"""
时间线面板组件

提供轻量时间轨道与 A/B 区间选择。
"""

from __future__ import annotations

from typing import Dict, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QSlider,
    QSizePolicy,
    QPushButton,
    QStyle,
    QStyleOptionSlider,
)


class ClickJumpSlider(QSlider):
    """支持点击轨道即跳转的滑块。"""

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            groove = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderGroove, self
            )
            handle = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
            )

            if self.orientation() == Qt.Horizontal:
                slider_min = groove.x()
                slider_max = groove.right() - handle.width() + 1
                pos = event.pos().x() - handle.width() // 2
            else:
                slider_min = groove.y()
                slider_max = groove.bottom() - handle.height() + 1
                pos = event.pos().y() - handle.height() // 2

            span = max(1, slider_max - slider_min)
            value = QStyle.sliderValueFromPosition(
                self.minimum(),
                self.maximum(),
                pos - slider_min,
                span,
                option.upsideDown,
            )
            self.setValue(value)
            event.accept()
        super().mousePressEvent(event)


class TimelinePanel(QWidget):
    """时间线面板。"""

    range_changed = pyqtSignal(int, int)
    sample_activated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TimelinePanel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(128)

        self._samples: List[Dict[str, object]] = []
        self._cursor_index = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("时间线样本")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        range_layout = QHBoxLayout()
        range_layout.setSpacing(8)
        range_layout.addWidget(QLabel("起点 A:"))
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(0)
        range_layout.addWidget(self.start_spin)

        range_layout.addWidget(QLabel("终点 B:"))
        self.end_spin = QSpinBox()
        self.end_spin.setMinimum(0)
        range_layout.addWidget(self.end_spin)
        self.cursor_to_start_button = QPushButton("游标设为 A")
        self.cursor_to_start_button.setObjectName("GhostButton")
        range_layout.addWidget(self.cursor_to_start_button)
        self.cursor_to_end_button = QPushButton("游标设为 B")
        self.cursor_to_end_button.setObjectName("GhostButton")
        range_layout.addWidget(self.cursor_to_end_button)
        range_layout.addStretch()
        layout.addLayout(range_layout)

        self.track_slider = ClickJumpSlider()
        self.track_slider.setOrientation(Qt.Horizontal)
        self.track_slider.setMinimum(0)
        self.track_slider.setMaximum(0)
        self.track_slider.setSingleStep(1)
        self.track_slider.setPageStep(5)
        layout.addWidget(self.track_slider)

        self.summary_label = QLabel("区间: A=0, B=0 | 游标: 0 | 样本总数: 0")
        self.summary_label.setObjectName("HintText")
        layout.addWidget(self.summary_label)

        self.cursor_hint_label = QLabel("当前样本: -")
        self.cursor_hint_label.setObjectName("HintText")
        layout.addWidget(self.cursor_hint_label)

        self.start_spin.valueChanged.connect(self._emit_range)
        self.end_spin.valueChanged.connect(self._emit_range)
        self.track_slider.valueChanged.connect(self._on_cursor_changed)
        self.cursor_to_start_button.clicked.connect(self._set_start_by_cursor)
        self.cursor_to_end_button.clicked.connect(self._set_end_by_cursor)

    def set_samples(self, samples: List[Dict[str, object]]) -> None:
        """设置并刷新时间轨道。"""
        self._samples = samples
        max_index = max(len(samples) - 1, 0)
        self.start_spin.setMaximum(max_index)
        self.end_spin.setMaximum(max_index)
        self.track_slider.setMaximum(max_index)
        self.track_slider.setPageStep(max(1, max_index // 20))
        self.start_spin.setValue(0)
        self.end_spin.setValue(max_index)
        self.track_slider.setValue(0)
        self._cursor_index = 0
        self._emit_range()

    def append_sample(self, sample: Dict[str, object]) -> None:
        """增量追加单条样本。"""
        self._samples.append(sample)
        max_index = max(len(self._samples) - 1, 0)
        self.start_spin.setMaximum(max_index)
        self.end_spin.setMaximum(max_index)
        self.track_slider.setMaximum(max_index)
        self.track_slider.setPageStep(max(1, max_index // 20))

        # 默认让终点跟随最新样本，便于实时观察。
        self.end_spin.setValue(max_index)
        self.track_slider.setValue(max_index)
        self._cursor_index = max_index
        if self.start_spin.value() > self.end_spin.value():
            self.start_spin.setValue(self.end_spin.value())
        self._update_summary()

    def _emit_range(self) -> None:
        """当 A/B 变化时，保证顺序并广播区间。"""
        start_idx = self.start_spin.value()
        end_idx = self.end_spin.value()

        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx

        self.range_changed.emit(start_idx, end_idx)
        self._update_summary(start_idx, end_idx)

    def _on_cursor_changed(self, value: int) -> None:
        """游标变化时回传样本对象。"""
        self._cursor_index = value
        if value < 0 or value >= len(self._samples):
            self.cursor_hint_label.setText("当前样本: -")
            return
        sample = self._samples[value]
        self.sample_activated.emit(sample)
        self.cursor_hint_label.setText(self._build_cursor_hint(sample))
        self._update_summary()

    def _update_summary(self, start_idx: int = -1, end_idx: int = -1) -> None:
        """刷新区间摘要信息。"""
        if start_idx < 0:
            start_idx = self.start_spin.value()
        if end_idx < 0:
            end_idx = self.end_spin.value()
        total = len(self._samples)
        self.summary_label.setText(
            f"区间: A={start_idx}, B={end_idx} | 游标: {self._cursor_index} | 样本总数: {total}"
        )

    def locate_sample(self, sample: Dict[str, object]) -> None:
        """根据样本对象定位游标位置。"""
        target_id = str(sample.get("sample_id", "")).strip()
        target_rel = str(sample.get("image_rel_path", sample.get("image_path", ""))).strip()
        target_idx = -1

        for idx, item in enumerate(self._samples):
            sample_id = str(item.get("sample_id", "")).strip()
            if target_id and sample_id == target_id:
                target_idx = idx
                break
            rel = str(item.get("image_rel_path", item.get("image_path", ""))).strip()
            if target_rel and rel == target_rel:
                target_idx = idx
                break

        if target_idx >= 0:
            self.locate_index(target_idx)

    def locate_image_path(self, image_rel_path: str) -> None:
        """根据相对路径定位游标。"""
        target = str(image_rel_path).strip()
        if not target:
            return
        for idx, item in enumerate(self._samples):
            rel = str(item.get("image_rel_path", item.get("image_path", ""))).strip()
            if rel == target:
                self.locate_index(idx)
                return

    def locate_index(self, index: int) -> None:
        """定位到指定索引，触发实时预览刷新。"""
        if index < 0 or index >= len(self._samples):
            return
        if index == self.track_slider.value():
            self._cursor_index = index
            sample = self._samples[index]
            self.cursor_hint_label.setText(self._build_cursor_hint(sample))
            self._update_summary()
            return
        self.track_slider.setValue(index)

    def _set_start_by_cursor(self) -> None:
        """将游标位置设置为起点 A。"""
        self.start_spin.setValue(self._cursor_index)

    def _set_end_by_cursor(self) -> None:
        """将游标位置设置为终点 B。"""
        self.end_spin.setValue(self._cursor_index)

    def _build_cursor_hint(self, sample: Dict[str, object]) -> str:
        """构建游标样本摘要。"""
        scene = str(sample.get("scene", "other"))
        rel = str(sample.get("image_rel_path", sample.get("image_path", "-")))
        ts = str(sample.get("timestamp_iso", sample.get("timestamp_ms", "-")))
        ts = ts.replace("T", " ").replace("Z", "")
        if len(ts) > 19:
            ts = ts[:19]
        return f"当前样本: {scene} | {ts} | {rel}"

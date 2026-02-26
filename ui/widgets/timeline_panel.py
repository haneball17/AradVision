"""
时间线面板组件

提供轻量时间轨道与 A/B 区间选择。
"""

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
)


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
        range_layout.addStretch()
        layout.addLayout(range_layout)

        self.track_slider = QSlider()
        self.track_slider.setOrientation(Qt.Horizontal)
        self.track_slider.setMinimum(0)
        self.track_slider.setMaximum(0)
        layout.addWidget(self.track_slider)

        self.summary_label = QLabel("区间: A=0, B=0 | 样本总数: 0")
        self.summary_label.setObjectName("HintText")
        layout.addWidget(self.summary_label)

        self.start_spin.valueChanged.connect(self._emit_range)
        self.end_spin.valueChanged.connect(self._emit_range)
        self.track_slider.valueChanged.connect(self._on_cursor_changed)

    def set_samples(self, samples: List[Dict[str, object]]) -> None:
        """设置并刷新时间轨道。"""
        self._samples = samples
        max_index = max(len(samples) - 1, 0)
        self.start_spin.setMaximum(max_index)
        self.end_spin.setMaximum(max_index)
        self.track_slider.setMaximum(max_index)
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
            return
        self.sample_activated.emit(self._samples[value])
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

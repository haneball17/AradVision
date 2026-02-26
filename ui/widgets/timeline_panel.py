"""
时间线面板组件

提供样本列表展示与 A/B 区间索引选择。
"""

from typing import Dict, List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
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
        self.setMinimumHeight(160)

        self._samples: List[Dict[str, object]] = []

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

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["时间", "场景", "文件"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(72)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.setMinimumHeight(110)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.start_spin.valueChanged.connect(self._emit_range)
        self.end_spin.valueChanged.connect(self._emit_range)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def set_samples(self, samples: List[Dict[str, object]]) -> None:
        """设置并渲染样本列表。"""
        self._samples = samples
        self.table.setRowCount(len(samples))

        for idx, sample in enumerate(samples):
            timestamp = str(sample.get("timestamp_iso", "-"))
            scene = str(sample.get("scene", "-"))
            image_path = str(sample.get("image_rel_path", "-"))

            self.table.setItem(idx, 0, QTableWidgetItem(timestamp))
            self.table.setItem(idx, 1, QTableWidgetItem(scene))
            self.table.setItem(idx, 2, QTableWidgetItem(image_path))

        max_index = max(len(samples) - 1, 0)
        self.start_spin.setMaximum(max_index)
        self.end_spin.setMaximum(max_index)
        self.start_spin.setValue(0)
        self.end_spin.setValue(max_index)
        self._emit_range()

    def append_sample(self, sample: Dict[str, object]) -> None:
        """增量追加单条样本。"""
        self._samples.append(sample)
        row = self.table.rowCount()
        self.table.insertRow(row)

        timestamp = str(sample.get("timestamp_iso", "-"))
        scene = str(sample.get("scene", "-"))
        image_path = str(sample.get("image_rel_path", "-"))

        self.table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.table.setItem(row, 1, QTableWidgetItem(scene))
        self.table.setItem(row, 2, QTableWidgetItem(image_path))

        max_index = max(len(self._samples) - 1, 0)
        self.start_spin.setMaximum(max_index)
        self.end_spin.setMaximum(max_index)

        # 默认让终点跟随最新样本，便于实时观察。
        self.end_spin.setValue(max_index)
        if self.start_spin.value() > self.end_spin.value():
            self.start_spin.setValue(self.end_spin.value())

    def _emit_range(self) -> None:
        """当 A/B 变化时，保证顺序并广播区间。"""
        start_idx = self.start_spin.value()
        end_idx = self.end_spin.value()

        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx

        self.range_changed.emit(start_idx, end_idx)

    def _on_cell_double_clicked(self, row: int, _col: int) -> None:
        """双击样本后回传样本对象。"""
        if row < 0 or row >= len(self._samples):
            return
        self.sample_activated.emit(self._samples[row])

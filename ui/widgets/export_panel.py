"""
导出参数面板组件

负责区间采样参数、输出路径设置与导出触发。
"""

from pathlib import Path
from typing import Dict

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QComboBox,
    QPushButton,
    QLineEdit,
    QFileDialog,
)


class ExportPanel(QWidget):
    """导出参数面板。"""

    export_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ExportPanel")

        self._max_index = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("导出参数")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.start_spin = QSpinBox()
        self.end_spin = QSpinBox()
        self.start_spin.setMinimum(0)
        self.end_spin.setMinimum(0)

        range_layout = QHBoxLayout()
        range_layout.setSpacing(8)
        range_layout.addWidget(QLabel("起点 A"))
        range_layout.addWidget(self.start_spin)
        range_layout.addWidget(QLabel("终点 B"))
        range_layout.addWidget(self.end_spin)
        layout.addLayout(range_layout)

        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1s", "2s", "5s", "自定义"])
        self.interval_custom_spin = QSpinBox()
        self.interval_custom_spin.setRange(1, 60)
        self.interval_custom_spin.setValue(1)
        self.interval_custom_spin.setEnabled(False)

        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(8)
        interval_layout.addWidget(QLabel("采样频率"))
        interval_layout.addWidget(self.interval_combo)
        interval_layout.addWidget(self.interval_custom_spin)
        layout.addLayout(interval_layout)

        self.output_edit = QLineEdit("assets/images/selected")
        self.browse_button = QPushButton("浏览")

        output_layout = QHBoxLayout()
        output_layout.setSpacing(8)
        output_layout.addWidget(QLabel("输出目录"))
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.browse_button)
        layout.addLayout(output_layout)

        self.estimate_label = QLabel("预计导出: 0")
        self.estimate_label.setObjectName("StatusPill")
        layout.addWidget(self.estimate_label)

        self.validation_label = QLabel("导出前校验: 未执行")
        self.validation_label.setObjectName("HintText")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        self.export_button = QPushButton("开始导出")
        self.export_button.setObjectName("PrimaryButton")
        layout.addWidget(self.export_button)
        layout.addStretch()

        self.interval_combo.currentTextChanged.connect(self._on_interval_changed)
        self.start_spin.valueChanged.connect(self._update_estimate)
        self.end_spin.valueChanged.connect(self._update_estimate)
        self.interval_custom_spin.valueChanged.connect(self._update_estimate)
        self.browse_button.clicked.connect(self._choose_output_dir)
        self.export_button.clicked.connect(self._emit_export_requested)

    def set_range(self, max_index: int, start: int, end: int) -> None:
        """同步可导出区间范围。"""
        self._max_index = max(max_index, 0)
        self.start_spin.setMaximum(self._max_index)
        self.end_spin.setMaximum(self._max_index)

        self.start_spin.setValue(max(min(start, self._max_index), 0))
        self.end_spin.setValue(max(min(end, self._max_index), 0))
        self._update_estimate()

    def set_estimated_count(self, count: int) -> None:
        """外部直接更新预计导出数量。"""
        self.estimate_label.setText(f"预计导出: {max(count, 0)}")

    def set_validation_summary(self, summary: str, blocking: bool = False) -> None:
        """更新导出前校验摘要。"""
        prefix = "导出前校验（阻断）: " if blocking else "导出前校验: "
        self.validation_label.setText(prefix + summary)

    def _on_interval_changed(self, value: str) -> None:
        """切换频率模式。"""
        self.interval_custom_spin.setEnabled(value == "自定义")
        self._update_estimate()

    def _choose_output_dir(self) -> None:
        """选择输出目录。"""
        selected = QFileDialog.getExistingDirectory(
            self,
            "选择导出目录",
            str(Path(self.output_edit.text()).resolve()),
        )
        if selected:
            self.output_edit.setText(selected)

    def _resolve_interval_seconds(self) -> int:
        """统一解析采样间隔秒数。"""
        text = self.interval_combo.currentText()
        if text == "自定义":
            return self.interval_custom_spin.value()
        return int(text.replace("s", ""))

    def _update_estimate(self) -> None:
        """根据索引区间与间隔粗略估算导出数量。"""
        start = self.start_spin.value()
        end = self.end_spin.value()
        if start > end:
            start, end = end, start

        interval = max(self._resolve_interval_seconds(), 1)
        raw_count = end - start + 1
        estimated = max(raw_count // interval, 0)
        if raw_count > 0 and estimated == 0:
            estimated = 1

        self.set_estimated_count(estimated)

    def _emit_export_requested(self) -> None:
        """发出导出请求。"""
        start = self.start_spin.value()
        end = self.end_spin.value()
        if start > end:
            start, end = end, start

        payload: Dict[str, object] = {
            "start_index": start,
            "end_index": end,
            "interval_sec": self._resolve_interval_seconds(),
            "output_dir": self.output_edit.text().strip(),
        }
        self.export_requested.emit(payload)

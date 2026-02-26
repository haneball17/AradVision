"""
预标注任务面板组件

用于在 UI 内触发预标注任务，并展示任务状态。
"""

from typing import Dict, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


class PseudoLabelPanel(QWidget):
    """预标注任务面板。"""

    start_task_requested = pyqtSignal(dict)
    stop_task_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PseudoLabelPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("预标注任务")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.dataset_edit = QLineEdit("assets/images/selected")
        self.model_edit = QLineEdit("models/yolov8n_dnf.pt")
        self.version_edit = QLineEdit("v1.0")

        dataset_layout = QHBoxLayout()
        dataset_layout.setSpacing(8)
        dataset_layout.addWidget(QLabel("数据集"))
        dataset_layout.addWidget(self.dataset_edit)
        dataset_btn = QPushButton("浏览")
        dataset_btn.clicked.connect(self._choose_dataset)
        dataset_layout.addWidget(dataset_btn)

        model_layout = QHBoxLayout()
        model_layout.setSpacing(8)
        model_layout.addWidget(QLabel("模型"))
        model_layout.addWidget(self.model_edit)
        model_btn = QPushButton("浏览")
        model_btn.clicked.connect(self._choose_model)
        model_layout.addWidget(model_btn)

        version_layout = QHBoxLayout()
        version_layout.setSpacing(8)
        version_layout.addWidget(QLabel("版本"))
        version_layout.addWidget(self.version_edit)
        version_layout.addStretch()

        layout.addLayout(dataset_layout)
        layout.addLayout(model_layout)
        layout.addLayout(version_layout)

        self.start_button = QPushButton("开始预标注")
        self.start_button.setObjectName("PrimaryButton")
        self.stop_button = QPushButton("停止任务")
        self.stop_button.setObjectName("DangerButton")
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        action_layout.addWidget(self.start_button)
        action_layout.addWidget(self.stop_button)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        self.task_table = QTableWidget(0, 4)
        self.task_table.setHorizontalHeaderLabels(["任务ID", "状态", "进度", "错误摘要"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.task_table.setEditTriggers(self.task_table.NoEditTriggers)
        self.task_table.setSelectionBehavior(self.task_table.SelectRows)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setAlternatingRowColors(True)
        layout.addWidget(self.task_table)

        self.start_button.clicked.connect(self._emit_start)
        self.stop_button.clicked.connect(self._emit_stop)

    def _choose_dataset(self) -> None:
        """选择数据集目录。"""
        selected = QFileDialog.getExistingDirectory(self, "选择数据集目录", self.dataset_edit.text())
        if selected:
            self.dataset_edit.setText(selected)

    def _choose_model(self) -> None:
        """选择模型文件。"""
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "选择模型文件",
            self.model_edit.text(),
            "模型文件 (*.pt *.onnx);;所有文件 (*)",
        )
        if selected:
            self.model_edit.setText(selected)

    def _emit_start(self) -> None:
        """发出开始任务请求。"""
        payload = {
            "dataset_path": self.dataset_edit.text().strip(),
            "model_path": self.model_edit.text().strip(),
            "pseudo_version": self.version_edit.text().strip() or "v1.0",
        }
        self.start_task_requested.emit(payload)

    def _emit_stop(self) -> None:
        """发出停止任务请求。"""
        task_id = self._get_selected_task_id() or ""
        self.stop_task_requested.emit(task_id)

    def _get_selected_task_id(self) -> Optional[str]:
        """读取当前选中任务 ID。"""
        row = self.task_table.currentRow()
        if row < 0:
            return None
        item = self.task_table.item(row, 0)
        return item.text() if item else None

    def upsert_task(self, task: Dict[str, object]) -> None:
        """更新或插入任务行。"""
        task_id = str(task.get("task_id", ""))
        if not task_id:
            return

        target_row = -1
        for row in range(self.task_table.rowCount()):
            existing_item = self.task_table.item(row, 0)
            if existing_item and existing_item.text() == task_id:
                target_row = row
                break

        if target_row < 0:
            target_row = self.task_table.rowCount()
            self.task_table.insertRow(target_row)

        status = str(task.get("status", "unknown"))
        progress = task.get("progress", {})
        processed = int(progress.get("processed", 0)) if isinstance(progress, dict) else 0
        total = int(progress.get("total", 0)) if isinstance(progress, dict) else 0
        progress_text = f"{processed}/{total}" if total > 0 else "-"
        error_summary = str(task.get("error_summary", ""))

        self.task_table.setItem(target_row, 0, QTableWidgetItem(task_id))
        self.task_table.setItem(target_row, 1, QTableWidgetItem(status))
        self.task_table.setItem(target_row, 2, QTableWidgetItem(progress_text))
        self.task_table.setItem(target_row, 3, QTableWidgetItem(error_summary))

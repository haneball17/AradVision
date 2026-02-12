"""
系统日志面板组件

显示和过滤系统日志信息。

Author: haneball17
Date: 2026-02-11
"""

from datetime import datetime
from typing import List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QTextEdit, QComboBox,
    QPushButton, QLineEdit, QLabel, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QFont, QColor

from core.logger import logger


class LogPanel(QWidget):
    """
    系统日志面板组件

    显示和过滤系统日志信息：
    - 日志级别过滤
    - 日志搜索
    - 日志统计
    - 日志导出
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 日志数据
        self.log_messages: List[str] = []
        self.max_lines = 1000  # 最大显示行数
        self.auto_scroll = True  # 自动滚动到底部

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 过滤器组
        filter_group = self.create_filter_group()
        main_layout.addWidget(filter_group)

        # 日志显示区域
        log_group = self.create_log_display_group()
        main_layout.addWidget(log_group)

        # 统计信息组
        stats_group = self.create_stats_group()
        main_layout.addWidget(stats_group)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def create_filter_group(self) -> QGroupBox:
        """创建过滤器组"""
        group = QGroupBox("🔍 日志过滤")
        layout = QVBoxLayout()

        # 第一行：级别过滤和自动滚动
        row1_layout = QHBoxLayout()

        # 日志级别选择
        level_label = QLabel("日志级别:")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("全部", "ALL")
        self.log_level_combo.addItem("DEBUG", "DEBUG")
        self.log_level_combo.addItem("INFO", "INFO")
        self.log_level_combo.addItem("WARNING", "WARNING")
        self.log_level_combo.addItem("ERROR", "ERROR")
        self.log_level_combo.setCurrentIndex(0)  # 默认显示全部
        self.log_level_combo.currentTextChanged.connect(self.apply_filters)
        row1_layout.addWidget(level_label)
        row1_layout.addWidget(self.log_level_combo)

        # 自动滚动复选框
        self.auto_scroll_checkbox = QCheckBox("自动滚动到底部")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.toggled.connect(self.toggle_auto_scroll)
        row1_layout.addWidget(self.auto_scroll_checkbox)

        row1_layout.addStretch()
        layout.addLayout(row1_layout)

        # 第二行：搜索框
        row2_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索日志...")
        self.search_input.textChanged.connect(self.apply_filters)
        row2_layout.addWidget(search_label)
        row2_layout.addWidget(self.search_input)

        # 清除按钮
        btn_clear = QPushButton("清除日志")
        btn_clear.clicked.connect(self.clear_logs)
        row2_layout.addWidget(btn_clear)

        layout.addLayout(row2_layout)

        group.setLayout(layout)
        return group

    def create_log_display_group(self) -> QGroupBox:
        """创建日志显示组"""
        group = QGroupBox("📋 日志内容")
        layout = QVBoxLayout()

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(400)

        # 设置等宽字体
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.log_text.setFont(font)

        # 设置样式
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        layout.addWidget(self.log_text)

        group.setLayout(layout)
        return group

    def create_stats_group(self) -> QGroupBox:
        """创建统计信息组"""
        group = QGroupBox("📊 日志统计")
        layout = QHBoxLayout()

        # 统计标签
        self.total_label = QLabel("总计: 0 条")
        self.debug_label = QLabel("DEBUG: 0")
        self.info_label = QLabel("INFO: 0")
        self.warning_label = QLabel("WARNING: 0")
        self.error_label = QLabel("ERROR: 0")

        # 设置颜色
        self.debug_label.setStyleSheet("color: #808080;")
        self.info_label.setStyleSheet("color: #4FC3F7;")
        self.warning_label.setStyleSheet("color: #FFB74D;")
        self.error_label.setStyleSheet("color: #EF5350;")

        layout.addWidget(self.total_label)
        layout.addWidget(self.debug_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.error_label)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def add_log(self, level: str, message: str):
        """
        添加日志消息

        Args:
            level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
            message: 日志消息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 根据级别设置颜色
        color_map = {
            "DEBUG": "#808080",
            "INFO": "#4FC3F7",
            "WARNING": "#FFB74D",
            "ERROR": "#EF5350"
        }
        color = color_map.get(level, "#D4D4D4")

        # 格式化日志
        log_entry = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span>'

        # 保存原始消息
        self.log_messages.append({
            "level": level,
            "message": message,
            "html": log_entry
        })

        # 限制最大行数
        if len(self.log_messages) > self.max_lines:
            self.log_messages.pop(0)

        # 应用过滤器
        self.apply_filters()
        self.update_stats()

    def apply_filters(self):
        """应用过滤器"""
        level_filter = self.log_level_combo.currentData()
        search_text = self.search_input.text().lower()

        # 清空显示
        self.log_text.clear()

        # 过滤并添加日志
        for log in self.log_messages:
            # 级别过滤
            if level_filter != "ALL" and log["level"] != level_filter:
                continue

            # 搜索过滤
            if search_text and search_text not in log["message"].lower():
                continue

            # 添加日志
            self.log_text.append(log["html"])

        # 自动滚动
        if self.auto_scroll:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)

    def toggle_auto_scroll(self, checked: bool):
        """
        切换自动滚动

        Args:
            checked: 是否启用自动滚动
        """
        self.auto_scroll = checked
        if checked:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)

    def update_stats(self):
        """更新统计信息"""
        total = len(self.log_messages)
        debug = sum(1 for log in self.log_messages if log["level"] == "DEBUG")
        info = sum(1 for log in self.log_messages if log["level"] == "INFO")
        warning = sum(1 for log in self.log_messages if log["level"] == "WARNING")
        error = sum(1 for log in self.log_messages if log["level"] == "ERROR")

        self.total_label.setText(f"总计: {total} 条")
        self.debug_label.setText(f"DEBUG: {debug}")
        self.info_label.setText(f"INFO: {info}")
        self.warning_label.setText(f"WARNING: {warning}")
        self.error_label.setText(f"ERROR: {error}")

    def clear_logs(self):
        """清除所有日志"""
        self.log_messages.clear()
        self.log_text.clear()
        self.update_stats()
        logger.info("日志已清除")

    def append_error(self, error_message: str):
        """
        添加错误消息（用于 error_occurred 信号）

        Args:
            error_message: 错误消息
        """
        self.add_log("ERROR", error_message)

    def export_logs(self):
        """导出日志到文件"""
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            "",
            "Text Files (*.txt);;Log Files (*.log);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for log in self.log_messages:
                        # 移除 HTML 标签
                        from html.parser import HTMLParser

                        class MLStripper(HTMLParser):
                            def __init__(self):
                                super().__init__()
                                self.reset()
                                self.strict = False
                                self.convert_charrefs = True
                                self.text = []

                            def handle_data(self, d):
                                self.text.append(d)

                            def get_data(self):
                                return "".join(self.text)

                        stripper = MLStripper()
                        stripper.feed(log["html"])
                        f.write(stripper.get_data() + "\n")

                logger.info(f"日志已导出到: {file_path}")
            except Exception as e:
                logger.error(f"导出日志失败: {e}")


# 监听 loguru 日志并转发到 LogPanel
class LogHandler:
    """日志处理器，将 loguru 日志转发到 LogPanel"""

    def __init__(self, log_panel: LogPanel):
        self.log_panel = log_panel

    def debug(self, message: str):
        self.log_panel.add_log("DEBUG", message)

    def info(self, message: str):
        self.log_panel.add_log("INFO", message)

    def warning(self, message: str):
        self.log_panel.add_log("WARNING", message)

    def error(self, message: str):
        self.log_panel.add_log("ERROR", message)

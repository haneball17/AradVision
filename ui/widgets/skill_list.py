"""
技能优先级列表组件

支持拖拽排序的技能列表。

Author: haneball17
Date: 2026-02-11
"""

from PyQt5.QtWidgets import (
    QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QDialog, QLineEdit, QLabel
)
from PyQt5.QtCore import Qt

from core.logger import logger


class SkillListWidget(QListWidget):
    """
    技能优先级列表组件

    支持拖拽排序的技能列表，用于配置技能释放顺序。
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 启用拖拽
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)

        # 设置样式
        self.setStyleSheet("""
            SkillListWidget {
                background-color: #2B2B2B;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 12px;
            }
            SkillListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3C3C3C;
            }
            SkillListWidget::item:selected {
                background-color: #0078D7;
                color: #FFFFFF;
            }
            SkillListWidget::item:hover {
                background-color: #3C3C3C;
            }
        """)

        # 添加默认技能
        self.add_skill("a", "普通攻击")
        self.add_skill("s", "技能")
        self.add_skill("d", "大招")

    def add_skill(self, key: str, name: str):
        """
        添加技能项

        Args:
            key: 技能键位
            name: 技能名称
        """
        item = QListWidgetItem(f"{key} - {name}")
        item.setData(Qt.UserRole, key)
        self.addItem(item)

    def get_skill_order(self) -> list:
        """
        获取当前技能顺序

        Returns:
            技能键列表，按优先级排序
        """
        order = []
        for i in range(self.count()):
            item = self.item(i)
            key = item.data(Qt.UserRole)
            if key:
                order.append(key)
        return order

    def set_skill_order(self, keys: list, names: dict = None):
        """
        设置技能顺序

        Args:
            keys: 技能键列表
            names: 技能名称映射（可选）
        """
        self.clear()
        for key in keys:
            name = names.get(key, key) if names else key
            self.add_skill(key, name)

    def remove_selected(self):
        """移除选中的技能"""
        current_item = self.currentItem()
        if current_item:
            row = self.row(current_item)
            self.takeItem(row)
            logger.info(f"移除技能: {current_item.text()}")

    def add_new_skill(self):
        """添加新技能（对话框）"""
        dialog = AddSkillDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            key, name = dialog.get_skill()
            if key:
                self.add_skill(key, name)
                logger.info(f"添加技能: {key} - {name}")


class AddSkillDialog(QDialog):
    """添加技能对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加技能")
        self.setModal(True)
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        # 技能键位
        key_layout = QHBoxLayout()
        key_label = QLabel("技能键位:")
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("例如: a")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        layout.addLayout(key_layout)

        # 技能名称
        name_layout = QHBoxLayout()
        name_label = QLabel("技能名称:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: 普通攻击")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("添加")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_skill(self) -> tuple:
        """
        获取输入的技能信息

        Returns:
            (key, name) 技能键位和名称
        """
        key = self.key_input.text().strip()
        name = self.name_input.text().strip()

        if not key:
            return None, None

        if not name:
            name = key

        return key, name

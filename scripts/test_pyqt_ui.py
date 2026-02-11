"""
PyQt5 控制面板启动脚本

用于测试 UI 界面效果。

使用方法:
    python scripts/test_pyqt_ui.py

Author: haneball17
Date: 2026-02-11
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from core.logger import logger


def main():
    """主函数"""
    # 启用高 DPI 缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("AradVision")
    app.setApplicationVersion("0.1.3")
    app.setOrganizationName("AradVision")

    logger.info("启动 PyQt5 控制面板...")

    # 创建主窗口
    window = MainWindow()

    # 显示窗口
    window.show()

    logger.info("PyQt5 控制面板已启动")

    # 进入事件循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

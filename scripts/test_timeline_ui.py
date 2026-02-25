"""
时间线工作台启动脚本

用于启动“单 UI 双工作区”骨架界面：
- 采集工作区
- 预标注工作区
"""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import logger
from ui.timeline_window import TimelineWorkbenchWindow


def main() -> None:
    """主函数。"""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("AradVision Timeline Workbench")
    app.setApplicationVersion("0.1.4")

    logger.info("启动时间线工作台 UI...")

    window = TimelineWorkbenchWindow()
    window.show()

    logger.info("时间线工作台 UI 已启动")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

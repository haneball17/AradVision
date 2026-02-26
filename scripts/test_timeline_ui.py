"""
时间线工作台启动脚本

用于启动“单 UI 双工作区”骨架界面：
- 采集工作区
- 预标注工作区
"""

import sys
import os
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QApplication

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import logger
from ui.timeline_window import TimelineWorkbenchWindow


def main() -> None:
    """主函数。"""
    # 高 DPI 属性必须在 QApplication 创建前设置。
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Qt5 在分数缩放下常见“舍入放大”问题，这里默认使用 PassThrough。
    # 可通过 ARADVISION_DPI_ROUNDING_POLICY 覆盖：
    # PassThrough / Round / Ceil / Floor / RoundPreferFloor
    rounding_name = os.getenv("ARADVISION_DPI_ROUNDING_POLICY", "PassThrough")
    try:
        policy_enum = getattr(Qt, "HighDpiScaleFactorRoundingPolicy", None)
        if policy_enum and hasattr(QGuiApplication, "setHighDpiScaleFactorRoundingPolicy"):
            policy = getattr(policy_enum, rounding_name, None)
            if policy is not None:
                QGuiApplication.setHighDpiScaleFactorRoundingPolicy(policy)
                logger.info(f"高DPI舍入策略已设置: {rounding_name}")
            else:
                logger.warning(f"未知的高DPI舍入策略: {rounding_name}，将使用Qt默认策略")
    except Exception as exc:
        logger.warning(f"设置高DPI舍入策略失败，将使用Qt默认策略: {exc}")

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

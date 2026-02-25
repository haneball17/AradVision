"""
UI 模块 - PyQt5 控制面板

提供专业的桌面控制界面，支持：
- 实时视频预览
- 参数配置控制
- 系统日志查看
- 主题切换

Author: haneball17
Date: 2026-02-11
Version: 0.1.4
"""

__version__ = "0.1.4"


from ui.widgets import (
    VideoPreviewWidget,
    StatusPanel,
    ParameterPanel,
    SkillListWidget,
    LogPanel,
    LogHandler,
    WorkspaceSwitchBar,
    CaptureControlBar,
    TimelinePanel,
    FrameStrip,
    ExportPanel,
    PseudoLabelPanel,
)

from ui.threads.signals import EngineSignals
from ui.config.manager import UIManager
from ui.timeline_window import TimelineWorkbenchWindow

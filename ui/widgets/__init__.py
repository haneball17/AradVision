"""
自定义组件模块

包含各种自定义 UI 组件：
- VideoPreviewWidget: 视频预览组件
- StatusPanel: 状态面板组件
- ParameterPanel: 参数配置组件
- SkillListWidget: 技能列表组件
- LogPanel: 日志面板组件
- WorkspaceSwitchBar: 工作区切换条
- CaptureControlBar: 采集控制条
- TimelinePanel: 时间线面板
- SampleGridPanel: 样本网格主视图
- FrameStrip: 缩略图时间流
- ExportPanel: 导出参数面板
- PseudoLabelPanel: 预标注任务面板

Author: haneball17
Date: 2026-02-11
"""

from ui.widgets.video_preview import VideoPreviewWidget
from ui.widgets.status_panel import StatusPanel
from ui.widgets.parameter_panel import ParameterPanel
from ui.widgets.skill_list import SkillListWidget
from ui.widgets.log_panel import LogPanel, LogHandler
from ui.widgets.workspace_switch_bar import WorkspaceSwitchBar
from ui.widgets.capture_control_bar import CaptureControlBar
from ui.widgets.timeline_panel import TimelinePanel
from ui.widgets.sample_grid_panel import SampleGridPanel
from ui.widgets.frame_strip import FrameStrip
from ui.widgets.export_panel import ExportPanel
from ui.widgets.pseudo_label_panel import PseudoLabelPanel

__all__ = [
    "VideoPreviewWidget",
    "StatusPanel",
    "ParameterPanel",
    "SkillListWidget",
    "LogPanel",
    "LogHandler",
    "WorkspaceSwitchBar",
    "CaptureControlBar",
    "TimelinePanel",
    "SampleGridPanel",
    "FrameStrip",
    "ExportPanel",
    "PseudoLabelPanel",
]

"""
时间线工作台主窗口

提供单 UI 双工作区：
1. 采集工作区（时间线浏览、区间导出）
2. 预标注工作区（任务入口与状态展示）
"""

from __future__ import annotations

import platform
import uuid
import json
import time
import re
import hashlib
import os
import shutil
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 可选导入 cv2，用于落盘
try:
    import cv2  # type: ignore

    HAS_CV2 = True
except Exception:
    cv2 = None  # type: ignore
    HAS_CV2 = False

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QSplitter,
    QPlainTextEdit,
    QLabel,
    QDockWidget,
)
from PyQt5.QtCore import QSettings

from core.capture import create_capture_engine
from core.config import AppConfig, ConfigLoader
from core.logger import logger
from ui.widgets.capture_control_bar import CaptureControlBar
from ui.widgets.export_panel import ExportPanel
from ui.widgets.frame_strip import FrameStrip
from ui.widgets.pseudo_label_panel import PseudoLabelPanel
from ui.widgets.timeline_panel import TimelinePanel
from ui.widgets.video_preview import VideoPreviewWidget
from ui.widgets.workspace_switch_bar import WorkspaceSwitchBar


class TimelineWorkbenchWindow(QMainWindow):
    """时间线工作台主窗口。"""

    UI_LAYOUT_VERSION = 2

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AradVision 数据采集与预标注工作台")
        self.setMinimumSize(920, 620)
        self._init_window_size()

        self._samples: List[Dict[str, object]] = []
        self._current_task_id: str = ""
        self._task_processed = 0
        self._task_total = 1000
        self._config: AppConfig = AppConfig()

        self._capture_engine: Optional[Any] = None
        self._capture_frame_count = 0
        self._capture_error_streak = 0
        self._capture_timer_interval_ms = 33
        self._capture_save_interval_sec = 0.5
        self._capture_last_save_time = 0.0
        self._capture_saved_count = 0
        self._capture_session_name = ""
        self._capture_session_dir: Optional[Path] = None
        self._capture_images_dir: Optional[Path] = None
        self._capture_meta_file: Optional[Path] = None
        self._capture_session_manifest_file: Optional[Path] = None
        self._capture_prev_saved_frame: Optional[Any] = None
        self._capture_prev_saved_timestamp_ms: Optional[int] = None
        self._capture_expected_interval_ms = int(self._capture_save_interval_sec * 1000)
        self._capture_window_title: str = ""
        self._capture_active_backend: str = "unknown"
        self._capture_started_at: str = ""
        self._capture_stats: Dict[str, int] = {}
        self._using_demo_data = True

        self._task_timer = QTimer(self)
        self._task_timer.timeout.connect(self._tick_pseudo_task)
        self._capture_timer = QTimer(self)
        self._capture_timer.timeout.connect(self._tick_capture_frame)

        self.workspace_switch_bar: WorkspaceSwitchBar
        self.capture_control_bar: CaptureControlBar
        self.workspace_stack: QStackedWidget
        self._page_subtitle: QLabel
        self._root_layout: QVBoxLayout
        self._top_layout: QVBoxLayout
        self._workspace_layout: QVBoxLayout
        self._log_layout: QVBoxLayout
        self._session_layout: QVBoxLayout
        self._center_layout: QVBoxLayout
        self._export_layout: QVBoxLayout
        self._pseudo_layout: QVBoxLayout
        self._capture_content_splitter: QSplitter
        self._center_vertical_splitter: QSplitter
        self._session_dock: QDockWidget
        self._log_dock: QDockWidget
        self._responsive_mode: str = ""
        self._current_screen = None
        self._settings: QSettings = QSettings("AradVision", "TimelineWorkbench")

        self.session_list: QListWidget
        self.timeline_panel: TimelinePanel
        self.frame_strip: FrameStrip
        self.video_preview: VideoPreviewWidget
        self.export_panel: ExportPanel
        self.pseudo_label_panel: PseudoLabelPanel

        self.log_text: QPlainTextEdit

        self._init_ui()
        self._restore_ui_state()
        self._load_runtime_config()
        self._connect_signals()
        self._load_demo_data()
        self._refresh_window_candidates()
        self.apply_theme("light")
        self._apply_responsive_layout(self.width(), force=True)
        self._on_workspace_changed("capture")

        logger.info("时间线工作台窗口初始化完成")

    def _init_window_size(self) -> None:
        """按屏幕可用区域初始化窗口尺寸，避免高缩放下默认过大。"""
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 820)
            return

        available = screen.availableGeometry()
        width = max(1100, int(available.width() * 0.84))
        height = max(760, int(available.height() * 0.88))
        self.resize(width, height)

    def _get_ui_scale_factor(self) -> float:
        """读取当前窗口所在屏幕的 UI 缩放系数（基于逻辑 DPI）。"""
        screen = None
        handle = self.windowHandle()
        if handle is not None:
            screen = handle.screen()
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return 1.0

        scale_candidates: List[float] = []

        logical_dpi = float(screen.logicalDotsPerInch())
        if logical_dpi > 0:
            scale_candidates.append(logical_dpi / 96.0)

        try:
            dpr = float(screen.devicePixelRatio())
            if dpr > 0:
                scale_candidates.append(dpr)
        except Exception:
            pass

        scale = max(scale_candidates) if scale_candidates else 1.0

        # 在部分 Windows 环境中，Qt 可能返回 96 DPI，这里增加 WinAPI 兜底。
        if platform.system().lower() == "windows" and scale < 1.2:
            win_scale = self._get_windows_scale_fallback()
            if win_scale is not None:
                scale = max(scale, win_scale)

        return max(1.0, scale)

    def _get_windows_scale_fallback(self) -> Optional[float]:
        """通过 WinAPI 获取窗口 DPI，作为 Qt DPI 的兜底来源。"""
        try:
            import ctypes  # Windows 专用，按需导入避免跨平台告警。
        except Exception:
            return None

        user32 = getattr(ctypes, "windll", None)
        if user32 is None:
            return None
        user32 = user32.user32
        if user32 is None:
            return None

        hwnd = int(self.winId()) if self.winId() else 0
        dpi = 0

        try:
            if hwnd and hasattr(user32, "GetDpiForWindow"):
                dpi = int(user32.GetDpiForWindow(hwnd))
        except Exception:
            dpi = 0

        if dpi <= 0:
            try:
                if hasattr(user32, "GetDpiForSystem"):
                    dpi = int(user32.GetDpiForSystem())
            except Exception:
                dpi = 0

        if dpi <= 0:
            return None
        return float(dpi) / 96.0

    def _init_ui(self) -> None:
        """初始化主界面结构。"""
        central = QWidget()
        central.setObjectName("TimelineRoot")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        self._root_layout = root_layout
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        top_card = QWidget()
        top_card.setObjectName("TopCard")
        top_layout = QVBoxLayout(top_card)
        self._top_layout = top_layout
        top_layout.setContentsMargins(16, 16, 16, 16)
        top_layout.setSpacing(12)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        title_label = QLabel("数据采集时间线工作台")
        title_label.setObjectName("PageTitle")
        self._page_subtitle = QLabel("采集、筛选、导出与预标注统一入口")
        self._page_subtitle.setObjectName("PageSubtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self._page_subtitle)
        title_layout.addStretch()

        self.workspace_switch_bar = WorkspaceSwitchBar()
        self.capture_control_bar = CaptureControlBar()

        top_layout.addLayout(title_layout)
        top_layout.addWidget(self.workspace_switch_bar)
        top_layout.addWidget(self.capture_control_bar)
        root_layout.addWidget(top_card)

        self.workspace_stack = QStackedWidget()
        workspace_card = QWidget()
        workspace_card.setObjectName("WorkspaceCard")
        workspace_layout = QVBoxLayout(workspace_card)
        self._workspace_layout = workspace_layout
        workspace_layout.setContentsMargins(16, 16, 16, 16)
        workspace_layout.setSpacing(12)
        workspace_layout.addWidget(self.workspace_stack, stretch=1)

        self.workspace_stack.addWidget(self._build_capture_workspace())
        self.workspace_stack.addWidget(self._build_curation_workspace())
        self.workspace_stack.addWidget(self._build_pseudo_workspace())
        root_layout.addWidget(workspace_card, stretch=1)

        self._build_session_dock()
        self._build_log_dock()
        self._init_view_menu()

    def _build_session_dock(self) -> None:
        """构建会话列表停靠面板。"""
        self._session_dock = QDockWidget("会话列表", self)
        self._session_dock.setObjectName("SessionDock")
        self._session_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self._session_dock.setFeatures(
            QDockWidget.DockWidgetClosable
            | QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
        )

        session_panel = QWidget()
        session_panel.setObjectName("SessionPanel")
        session_layout = QVBoxLayout(session_panel)
        self._session_layout = session_layout
        session_layout.setContentsMargins(16, 16, 16, 16)
        session_layout.setSpacing(10)

        session_title = QLabel("会话列表")
        session_title.setObjectName("SectionTitle")
        session_layout.addWidget(session_title)

        session_hint = QLabel("选择会话后可查看样本时间线")
        session_hint.setObjectName("HintText")
        session_layout.addWidget(session_hint)

        self.session_list = QListWidget()
        self.session_list.setMinimumWidth(180)
        session_layout.addWidget(self.session_list, stretch=1)

        self._session_dock.setWidget(session_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._session_dock)

    def _build_log_dock(self) -> None:
        """构建系统日志停靠面板。"""
        self._log_dock = QDockWidget("系统日志", self)
        self._log_dock.setObjectName("LogDock")
        self._log_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self._log_dock.setFeatures(
            QDockWidget.DockWidgetClosable
            | QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
        )

        log_panel = QWidget()
        log_panel.setObjectName("LogCard")
        log_layout = QVBoxLayout(log_panel)
        self._log_layout = log_layout
        log_layout.setContentsMargins(16, 16, 16, 16)
        log_layout.setSpacing(8)

        log_title = QLabel("系统日志")
        log_title.setObjectName("SectionTitle")
        log_layout.addWidget(log_title)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)
        self.log_text.setMinimumHeight(80)
        log_layout.addWidget(self.log_text)

        self._log_dock.setWidget(log_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._log_dock)

    def _init_view_menu(self) -> None:
        """初始化视图菜单，提供会话与日志面板开关。"""
        view_menu = self.menuBar().addMenu("视图")

        session_toggle_action = self._session_dock.toggleViewAction()
        session_toggle_action.setText("会话列表")
        session_toggle_action.setShortcut("Alt+1")
        session_toggle_action.setShortcutContext(Qt.ApplicationShortcut)
        view_menu.addAction(session_toggle_action)

        log_toggle_action = self._log_dock.toggleViewAction()
        log_toggle_action.setText("系统日志")
        log_toggle_action.setShortcut("Alt+2")
        log_toggle_action.setShortcutContext(Qt.ApplicationShortcut)
        view_menu.addAction(log_toggle_action)

    def _load_runtime_config(self) -> None:
        """加载运行时配置。"""
        loader = ConfigLoader.instance()
        try:
            self._config = loader.load("configs/config.yaml")
            self._append_log(
                "配置加载成功: "
                f"backend={self._config.capture.backend}, "
                f"window_title={self._config.capture.window_title}"
            )
        except Exception as exc:
            self._config = AppConfig()
            self._append_log(f"配置加载失败，已回退默认配置: {exc}")

    def _build_capture_workspace(self) -> QWidget:
        """构建采集工作区布局（实时预览优先）。"""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        capture_panel = QWidget()
        capture_panel.setObjectName("CenterPanel")
        capture_layout = QVBoxLayout(capture_panel)
        capture_layout.setContentsMargins(16, 16, 16, 16)
        capture_layout.setSpacing(12)

        preview_title = QLabel("实时采集预览")
        preview_title.setObjectName("SectionTitle")
        preview_hint = QLabel("用于确认窗口绑定、实时画面与采集链路状态")
        preview_hint.setObjectName("HintText")
        self.video_preview = VideoPreviewWidget()

        capture_layout.addWidget(preview_title)
        capture_layout.addWidget(preview_hint)
        capture_layout.addWidget(self.video_preview, stretch=1)
        layout.addWidget(capture_panel, stretch=1)
        return workspace

    def _build_curation_workspace(self) -> QWidget:
        """构建筛选工作区布局（时间线筛选 + 导出）。"""
        workspace = QWidget()
        layout = QHBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._capture_content_splitter = QSplitter(Qt.Horizontal)
        self._capture_content_splitter.setHandleWidth(10)
        self._capture_content_splitter.setChildrenCollapsible(False)
        layout.addWidget(self._capture_content_splitter)

        center_panel = QWidget()
        center_panel.setObjectName("CenterPanel")
        center_layout = QVBoxLayout(center_panel)
        self._center_layout = center_layout
        center_layout.setContentsMargins(16, 16, 16, 16)
        center_layout.setSpacing(12)
        center_title = QLabel("时间线筛选与样本流")
        center_title.setObjectName("SectionTitle")
        center_layout.addWidget(center_title)

        self.timeline_panel = TimelinePanel()
        self.frame_strip = FrameStrip()
        self._center_vertical_splitter = QSplitter(Qt.Vertical)
        self._center_vertical_splitter.setHandleWidth(8)
        self._center_vertical_splitter.setChildrenCollapsible(False)
        self._center_vertical_splitter.addWidget(self.timeline_panel)
        self._center_vertical_splitter.addWidget(self.frame_strip)
        self._center_vertical_splitter.setCollapsible(0, False)
        self._center_vertical_splitter.setCollapsible(1, True)
        self._center_vertical_splitter.setStretchFactor(0, 5)
        self._center_vertical_splitter.setStretchFactor(1, 2)
        self._center_vertical_splitter.setSizes([420, 160])
        center_layout.addWidget(self._center_vertical_splitter, stretch=1)
        self._capture_content_splitter.addWidget(center_panel)

        export_panel_card = QWidget()
        export_panel_card.setObjectName("ExportPanelCard")
        export_layout = QVBoxLayout(export_panel_card)
        self._export_layout = export_layout
        export_layout.setContentsMargins(16, 16, 16, 16)
        export_layout.setSpacing(10)
        export_title = QLabel("导出任务")
        export_title.setObjectName("SectionTitle")
        export_layout.addWidget(export_title)
        self.export_panel = ExportPanel()
        self.export_panel.setMinimumWidth(260)
        export_layout.addWidget(self.export_panel, stretch=1)
        self._capture_content_splitter.addWidget(export_panel_card)
        self._capture_content_splitter.setCollapsible(0, False)
        self._capture_content_splitter.setCollapsible(1, False)
        self._capture_content_splitter.setStretchFactor(0, 4)
        self._capture_content_splitter.setStretchFactor(1, 1)
        self._capture_content_splitter.setSizes([860, 320])
        return workspace

    def _build_pseudo_workspace(self) -> QWidget:
        """构建预标注工作区布局。"""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        pseudo_card = QWidget()
        pseudo_card.setObjectName("PseudoPanelCard")
        pseudo_layout = QVBoxLayout(pseudo_card)
        self._pseudo_layout = pseudo_layout
        pseudo_layout.setContentsMargins(16, 16, 16, 16)
        pseudo_layout.setSpacing(10)

        self.pseudo_label_panel = PseudoLabelPanel()
        pseudo_layout.addWidget(self.pseudo_label_panel)
        layout.addWidget(pseudo_card)
        return workspace

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """窗口尺寸变化时应用响应式布局。"""
        super().resizeEvent(event)
        self._apply_responsive_layout(event.size().width())

    def showEvent(self, event) -> None:  # type: ignore[override]
        """窗口显示后再执行一次响应式判定，确保获取到正确屏幕 DPI。"""
        super().showEvent(event)
        self._attach_screen_signals()
        self._apply_responsive_layout(self.width(), force=True)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """窗口关闭时持久化布局状态。"""
        self._save_ui_state()
        super().closeEvent(event)

    def _attach_screen_signals(self) -> None:
        """监听窗口所在屏幕变化和 DPI 变化。"""
        handle = self.windowHandle()
        if handle is None:
            return

        try:
            handle.screenChanged.disconnect(self._on_window_screen_changed)
        except Exception:
            pass
        handle.screenChanged.connect(self._on_window_screen_changed)

        self._on_window_screen_changed(handle.screen())

    def _on_window_screen_changed(self, screen) -> None:
        """窗口切换到新屏幕后，重连 DPI 信号并重算布局。"""
        if self._current_screen is not None:
            try:
                self._current_screen.logicalDotsPerInchChanged.disconnect(
                    self._on_screen_dpi_changed
                )
            except Exception:
                pass

        self._current_screen = screen
        if self._current_screen is not None:
            try:
                self._current_screen.logicalDotsPerInchChanged.connect(
                    self._on_screen_dpi_changed
                )
            except Exception:
                pass

        self._apply_responsive_layout(self.width(), force=True)

    def _on_screen_dpi_changed(self, _dpi: float) -> None:
        """系统 DPI 变化后刷新响应式布局。"""
        self._apply_responsive_layout(self.width(), force=True)

    def _restore_ui_state(self) -> None:
        """恢复窗口与停靠面板状态。"""
        geometry = self._settings.value("window/geometry")
        state = self._settings.value("window/state")
        has_persisted = bool(self._settings.value("window/persisted", False, type=bool))
        layout_version = int(self._settings.value("window/layout_version", 0, type=int))

        if geometry is not None:
            self.restoreGeometry(geometry)
        if state is not None:
            self.restoreState(state)

        if has_persisted and layout_version >= self.UI_LAYOUT_VERSION:
            session_visible = bool(
                self._settings.value("dock/session_visible", False, type=bool)
            )
            log_visible = bool(self._settings.value("dock/log_visible", False, type=bool))
            self._session_dock.setVisible(session_visible)
            self._log_dock.setVisible(log_visible)
        else:
            # 首次启动默认折叠，需要时再展开。
            self._session_dock.hide()
            self._log_dock.hide()

    def _save_ui_state(self) -> None:
        """保存窗口与停靠面板状态。"""
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("window/state", self.saveState())
        self._settings.setValue("dock/session_visible", self._session_dock.isVisible())
        self._settings.setValue("dock/log_visible", self._log_dock.isVisible())
        self._settings.setValue("window/layout_version", self.UI_LAYOUT_VERSION)
        self._settings.setValue("window/persisted", True)
        self._settings.sync()

    def _rebalance_center_splitter(self, mode: str, scale: float) -> None:
        """按模式和缩放系数重算筛选区纵向布局，避免高缩放下时间线与样本流重叠。"""
        timeline_min = max(120, int(200 / scale))
        strip_min = max(64, int(110 / scale))

        if mode == "default":
            timeline_min = max(timeline_min, 200)
            self.frame_strip.setMaximumHeight(220)
        elif mode == "compact":
            timeline_min = max(timeline_min, 170)
            self.frame_strip.setMaximumHeight(170)
        else:
            timeline_min = max(timeline_min, 150)
            self.frame_strip.setMaximumHeight(0)

        frame_strip_visible = not self.frame_strip.isHidden()
        self.timeline_panel.setMinimumHeight(timeline_min)
        self.frame_strip.setMinimumHeight(strip_min if frame_strip_visible else 0)

        available_height = self._center_vertical_splitter.size().height()
        if available_height <= 0:
            available_height = timeline_min + (strip_min if frame_strip_visible else 0) + 80

        if not frame_strip_visible:
            self._center_vertical_splitter.setSizes([max(available_height, timeline_min), 0])
            return

        timeline_h = max(timeline_min, int(available_height * 0.74))
        strip_h = available_height - timeline_h
        if strip_h < strip_min:
            strip_h = strip_min
            timeline_h = max(timeline_min, available_height - strip_h)

        self._center_vertical_splitter.setSizes([timeline_h, max(strip_h, strip_min)])

    def _apply_responsive_layout(self, width: int, force: bool = False) -> None:
        """根据窗口宽度切换布局密度与分栏策略。"""
        scale = self._get_ui_scale_factor()

        # 优先按缩放系数判断，再用宽度微调，避免 150% 在高分屏下误判为 default。
        if scale >= 1.45:
            mode = "dense"
        elif scale >= 1.25:
            mode = "compact" if width < 1850 else "default"
        elif width < 1360:
            mode = "dense"
        elif width < 1680:
            mode = "compact"
        else:
            mode = "default"

        if not force and mode == self._responsive_mode:
            return

        self._responsive_mode = mode
        logger.info(
            "[TimelineWorkbench] 响应式布局切换: "
            f"mode={mode}, width={width}, scale={scale:.2f}"
        )

        if mode == "default":
            outer_margin = 24
            card_padding = 16
            section_spacing = 12
            root_spacing = 16
            self._capture_content_splitter.setOrientation(Qt.Horizontal)
            self.export_panel.setMinimumWidth(300)
            self._capture_content_splitter.setSizes([780, 340])
            self.video_preview.setMinimumSize(640, 360)
            self.capture_control_bar.set_compact_mode(False)
            self.workspace_switch_bar.set_compact_mode(False)
            self._page_subtitle.setVisible(True)
            self.frame_strip.set_collapsed(False)
        elif mode == "compact":
            outer_margin = 16
            card_padding = 14
            section_spacing = 10
            root_spacing = 12
            self._capture_content_splitter.setOrientation(Qt.Horizontal)
            self.export_panel.setMinimumWidth(260)
            self._capture_content_splitter.setSizes([690, 300])
            self.video_preview.setMinimumSize(520, 300)
            self.capture_control_bar.set_compact_mode(True)
            self.workspace_switch_bar.set_compact_mode(True)
            self._page_subtitle.setVisible(False)
            self.frame_strip.set_collapsed(False)
        else:
            outer_margin = 12
            card_padding = 10
            section_spacing = 6
            root_spacing = 8
            self._capture_content_splitter.setOrientation(Qt.Vertical)
            self.export_panel.setMinimumWidth(0)
            self._capture_content_splitter.setSizes([620, 220])
            self.video_preview.setMinimumSize(420, 240)
            self.capture_control_bar.set_compact_mode(True)
            self.workspace_switch_bar.set_compact_mode(True)
            self._page_subtitle.setVisible(False)
            self.frame_strip.set_collapsed(True)

        self._root_layout.setContentsMargins(
            outer_margin, outer_margin, outer_margin, outer_margin
        )
        self._root_layout.setSpacing(root_spacing)

        for layout in (
            self._top_layout,
            self._workspace_layout,
            self._log_layout,
            self._session_layout,
            self._center_layout,
            self._export_layout,
            self._pseudo_layout,
        ):
            layout.setContentsMargins(card_padding, card_padding, card_padding, card_padding)
            layout.setSpacing(section_spacing)

        self._rebalance_center_splitter(mode, scale)

    def _connect_signals(self) -> None:
        """连接界面交互信号。"""
        self.workspace_switch_bar.workspace_changed.connect(self._on_workspace_changed)

        self.capture_control_bar.start_requested.connect(self._on_capture_start)
        self.capture_control_bar.stop_requested.connect(self._on_capture_stop)
        self.capture_control_bar.pause_toggled.connect(self._on_capture_pause_toggled)
        self.capture_control_bar.refresh_windows_requested.connect(
            self._on_refresh_windows_requested
        )

        self.timeline_panel.range_changed.connect(self._on_range_changed)
        self.timeline_panel.sample_activated.connect(self._on_sample_activated)
        self.frame_strip.frame_selected.connect(self._on_frame_selected)

        self.export_panel.export_requested.connect(self._on_export_requested)

        self.pseudo_label_panel.start_task_requested.connect(self._on_start_pseudo_task)
        self.pseudo_label_panel.stop_task_requested.connect(self._on_stop_pseudo_task)

        self.session_list.itemClicked.connect(self._on_session_selected)

    def _load_demo_data(self) -> None:
        """加载演示数据，确保窗口启动后可直接交互。"""
        self.session_list.addItem(QListWidgetItem("day1_luolan"))
        self.session_list.addItem(QListWidgetItem("day2_forest"))

        base_time = datetime(2026, 2, 25, 14, 0, 0)
        scenes = ["combat", "navigate", "loot", "boss", "other"]

        self._samples = []
        for idx in range(240):
            ts = base_time + timedelta(seconds=idx)
            scene = scenes[idx % len(scenes)]
            ts_ms = int(ts.timestamp() * 1000)
            self._samples.append(
                {
                    "sample_id": f"sample_{idx:06d}",
                    "timestamp_ms": ts_ms,
                    "timestamp_iso": ts.isoformat() + "Z",
                    "scene": scene,
                    "image_rel_path": f"images/{scene}_{idx:06d}.jpg",
                    "state": "raw",
                    "manual_flag": "none",
                    "filtered": False,
                    "filter_reason": "",
                    "source_session": "demo_session",
                }
            )

        self.timeline_panel.set_samples(self._samples)
        self.frame_strip.set_frames([str(item["image_rel_path"]) for item in self._samples])
        self.export_panel.set_range(len(self._samples) - 1, 0, len(self._samples) - 1)
        self._append_log("已加载演示会话与样本数据。")

    def _list_window_titles(self) -> List[str]:
        """枚举可选窗口标题。"""
        candidates: List[str] = []
        default_title = self._config.capture.window_title.strip()
        if default_title:
            candidates.append(default_title)

        if platform.system().lower() != "windows":
            return candidates

        try:
            import win32gui  # type: ignore
        except Exception as exc:  # pragma: no cover - Linux 环境不会安装该依赖
            self._append_log(f"窗口枚举不可用（缺少 win32gui）: {exc}")
            return candidates

        def enum_windows_callback(hwnd: int, _param: object) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return True
            if title not in candidates:
                candidates.append(title)
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as exc:
            self._append_log(f"窗口枚举失败: {exc}")

        return candidates

    def _refresh_window_candidates(self) -> None:
        """刷新窗口下拉列表。"""
        previous = self.capture_control_bar.selected_window_title()
        titles = self._list_window_titles()
        preferred = previous or self._config.capture.window_title
        self.capture_control_bar.set_window_options(titles, preferred)
        self._append_log(f"窗口列表已刷新，可选窗口数量: {len(titles)}")

    def apply_theme(self, theme: str = "light") -> None:
        """应用 QSS 主题。"""
        theme_path = Path(__file__).parent / "themes" / f"{theme}.qss"
        if not theme_path.exists():
            self._append_log(f"主题文件不存在: {theme_path}")
            return

        try:
            self.setStyleSheet(theme_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._append_log(f"主题加载失败: {exc}")

    def _on_workspace_changed(self, workspace: str) -> None:
        """切换工作区。"""
        mapping = {"capture": 0, "curation": 1, "pseudo": 2}
        index = mapping.get(workspace, 0)
        self.workspace_stack.setCurrentIndex(index)
        self.workspace_switch_bar.set_workspace(workspace)
        self.capture_control_bar.setVisible(workspace == "capture")

        if workspace == "capture":
            self._page_subtitle.setText("窗口绑定、启动控制与实时画面检查")
            label = "采集工作区"
        elif workspace == "curation":
            self._page_subtitle.setText("时间线筛选、样本流审阅与导出任务")
            label = "筛选工作区"
        else:
            self._page_subtitle.setText("预标注任务编排、执行与状态追踪")
            label = "预标注工作区"
        self._append_log(f"切换工作区: {label}")

    def _on_refresh_windows_requested(self) -> None:
        """响应“刷新窗口”动作。"""
        self._refresh_window_candidates()

    def _on_capture_start(self) -> None:
        """响应采集开始。"""
        if self._capture_engine is not None:
            self._append_log("采集已在运行，无需重复启动。")
            return

        window_title = self.capture_control_bar.selected_window_title()
        if not window_title or window_title.startswith("<"):
            self.capture_control_bar.set_status("异常")
            self._append_log("采集启动失败：请先选择有效窗口。")
            return

        capture_cfg = replace(self._config.capture)
        capture_cfg.window_title = window_title
        self._capture_window_title = window_title

        if self.capture_control_bar.pause_button.isChecked():
            self.capture_control_bar.pause_button.blockSignals(True)
            self.capture_control_bar.pause_button.setChecked(False)
            self.capture_control_bar.pause_button.setText("暂停")
            self.capture_control_bar.pause_button.blockSignals(False)

        try:
            engine = create_capture_engine(
                config=capture_cfg,
                use_mock=capture_cfg.use_mock,
                backend=capture_cfg.backend,
                allow_fallback=capture_cfg.allow_fallback,
            )
            engine.start()

            self._prepare_capture_session(window_title)

            self._capture_engine = engine
            self._capture_frame_count = 0
            self._capture_error_streak = 0
            fps = max(int(capture_cfg.target_fps), 1)
            self._capture_timer_interval_ms = max(10, int(1000 / fps))
            self._capture_expected_interval_ms = int(self._capture_save_interval_sec * 1000)
            self._capture_timer.start(self._capture_timer_interval_ms)

            active_backend = getattr(engine, "active_backend", "unknown")
            self._capture_active_backend = str(active_backend)
            self.capture_control_bar.set_status(f"采集中({active_backend})")
            self._append_log(
                "采集已启动: "
                f"window='{window_title}', requested={capture_cfg.backend}, active={active_backend}"
            )
            if self._capture_session_dir is not None:
                self._append_log(f"落盘会话目录: {self._capture_session_dir}")
        except Exception as exc:
            self.capture_control_bar.set_status("异常")
            self._capture_engine = None
            self._capture_active_backend = "unknown"
            self._append_log(f"采集启动失败: {exc}")

    def _on_capture_stop(self, error_summary: str = "") -> None:
        """响应采集停止。"""
        self._capture_timer.stop()
        if self._capture_engine is not None:
            try:
                self._capture_engine.stop()
            except Exception as exc:
                self._append_log(f"停止捕获引擎时出现异常: {exc}")
            finally:
                self._capture_engine = None

        if self.capture_control_bar.pause_button.isChecked():
            self.capture_control_bar.pause_button.blockSignals(True)
            self.capture_control_bar.pause_button.setChecked(False)
            self.capture_control_bar.pause_button.setText("暂停")
            self.capture_control_bar.pause_button.blockSignals(False)

        self.capture_control_bar.set_status("空闲")
        self._write_capture_session_manifest(
            status="stopped" if not error_summary else "error",
            error_summary=error_summary,
        )
        self._append_log("采集已停止。")
        self.video_preview.clear_frame()
        self._capture_active_backend = "unknown"

    def _on_capture_pause_toggled(self, paused: bool) -> None:
        """响应采集暂停切换。"""
        if self._capture_engine is None:
            self.capture_control_bar.set_status("空闲")
            self._append_log("当前无运行中的采集任务，忽略暂停/继续。")
            return

        if paused:
            self._capture_timer.stop()
            self.capture_control_bar.set_status("暂停中")
            self._append_log("采集已暂停。")
            return

        self._capture_timer.start(self._capture_timer_interval_ms)
        active_backend = getattr(self._capture_engine, "active_backend", "unknown")
        self.capture_control_bar.set_status(f"采集中({active_backend})")
        self._append_log("采集已继续。")

    def _tick_capture_frame(self) -> None:
        """拉取实时帧，形成真实数据流。"""
        if self._capture_engine is None:
            return

        try:
            frame = self._capture_engine.get_frame()
            if frame is None:
                raise RuntimeError("捕获引擎返回空帧")

            self.video_preview.update_frame(frame)
            self._capture_frame_count += 1
            self._capture_stats["captured"] = self._capture_frame_count

            if self._should_save_frame():
                self._save_capture_frame(frame)

            self._capture_error_streak = 0

            if self._capture_frame_count % 30 == 0:
                stats = self._capture_engine.get_stats()
                shape = getattr(frame, "shape", None)
                self._append_log(
                    "采集中: "
                    f"frames={stats.frame_count}, fps={stats.fps:.1f}, "
                    f"latency={stats.avg_latency:.1f}ms, shape={shape}"
                )
            if self._capture_frame_count % 60 == 0:
                self._write_capture_session_manifest(status="running", error_summary="")
        except Exception as exc:
            self._capture_error_streak += 1
            if self._capture_error_streak == 1 or self._capture_error_streak % 5 == 0:
                self._append_log(
                    f"实时取帧失败({self._capture_error_streak}): {exc}"
                )

            if self._capture_error_streak >= 10:
                self._append_log("连续取帧失败过多，已自动停止采集。")
                self._on_capture_stop(error_summary="连续取帧失败过多，自动停止")

    def _prepare_capture_session(self, window_title: str) -> None:
        """初始化本次采集会话目录与元数据文件。"""
        session_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_window = self._build_ascii_window_tag(window_title)
        self._capture_session_name = f"ui_capture_{session_stamp}_{safe_window}"

        self._capture_session_dir = Path("assets/images/raw") / self._capture_session_name
        self._capture_images_dir = self._capture_session_dir / "images"
        self._capture_meta_file = self._capture_session_dir / "samples.jsonl"
        self._capture_session_manifest_file = self._capture_session_dir / "session_manifest.json"

        self._capture_images_dir.mkdir(parents=True, exist_ok=True)
        self._capture_session_dir.mkdir(parents=True, exist_ok=True)

        self._capture_saved_count = 0
        self._capture_last_save_time = 0.0
        self._capture_prev_saved_frame = None
        self._capture_prev_saved_timestamp_ms = None
        self._capture_active_backend = "unknown"
        self._capture_started_at = self._iso_utc_now()
        self._capture_stats = {
            "captured": 0,
            "saved": 0,
            "filtered_blur": 0,
            "filtered_duplicate": 0,
            "write_failures": 0,
        }

        if self._capture_meta_file.exists():
            self._capture_meta_file.unlink()
        self._write_capture_session_manifest(status="running", error_summary="")

    def _build_ascii_window_tag(self, window_title: str) -> str:
        """构建仅含 ASCII 的窗口标识，避免 Windows 落盘路径兼容问题。"""
        # 仅保留 ASCII 字母数字，其余归一为下划线，避免路径编码问题。
        ascii_only = "".join(
            ch.lower() if ch.isascii() and ch.isalnum() else "_"
            for ch in window_title
        )
        ascii_only = re.sub(r"_+", "_", ascii_only).strip("_")

        # 极端情况下（全中文标题）使用稳定哈希，保证目录可读且可追溯。
        if not ascii_only:
            digest = hashlib.sha1(window_title.encode("utf-8")).hexdigest()[:10]
            return f"window_{digest}"

        return ascii_only[:24]

    def _iso_utc_now(self) -> str:
        """返回 UTC ISO8601 时间戳（毫秒）。"""
        return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

    def _write_capture_session_manifest(self, status: str, error_summary: str) -> None:
        """写入会话级 manifest，记录采集配置和统计信息。"""
        if self._capture_session_manifest_file is None:
            return

        cfg = self._config.capture
        manifest = {
            "schema_version": "v2.2",
            "session_id": self._capture_session_name,
            "created_at": self._capture_started_at or self._iso_utc_now(),
            "updated_at": self._iso_utc_now(),
            "status": status,
            "error_summary": error_summary,
            "backend": {
                "requested": cfg.backend,
                "active": self._capture_active_backend or getattr(
                    self._capture_engine, "active_backend", cfg.backend
                ),
                "allow_fallback": bool(cfg.allow_fallback),
            },
            "window": {
                "title": self._capture_window_title,
                "state": self._detect_window_state(self._capture_window_title),
            },
            "resolution": {"width": int(cfg.width), "height": int(cfg.height)},
            "sampling": {
                "target_fps": int(cfg.target_fps),
                "save_interval_sec": float(self._capture_save_interval_sec),
                "expected_interval_ms": int(self._capture_expected_interval_ms),
            },
            "stats": self._capture_stats,
        }

        try:
            self._capture_session_manifest_file.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            self._append_log(f"写入 session_manifest 失败: {exc}")

    def _detect_window_state(self, window_title: str) -> str:
        """检测目标窗口状态（foreground/background/minimized/unknown）。"""
        if platform.system().lower() != "windows" or not window_title:
            return "unknown"

        try:
            import win32gui  # type: ignore
        except Exception:
            return "unknown"

        target_title = window_title.strip().lower()
        target_hwnd: Optional[int] = None

        def enum_windows_callback(hwnd: int, _param: object) -> bool:
            nonlocal target_hwnd
            if target_hwnd is not None:
                return False
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd).strip().lower()
            if target_title and target_title in title:
                target_hwnd = hwnd
                return False
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
            if target_hwnd is None:
                return "unknown"
            if win32gui.IsIconic(target_hwnd):
                return "minimized"
            foreground = win32gui.GetForegroundWindow()
            return "foreground" if foreground == target_hwnd else "background"
        except Exception:
            return "unknown"

    def _compute_quality_scores(self, frame: Any) -> Tuple[float, float]:
        """计算基础质量分：模糊度与与上一帧的 MSE 差异。"""
        blur_score = -1.0
        dup_mse = -1.0

        if HAS_CV2:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            except Exception:
                blur_score = -1.0

        prev = self._capture_prev_saved_frame
        if prev is not None and hasattr(frame, "shape") and hasattr(prev, "shape"):
            try:
                if frame.shape == prev.shape:
                    diff = frame.astype("float32") - prev.astype("float32")
                    dup_mse = float((diff * diff).mean())
            except Exception:
                dup_mse = -1.0

        return blur_score, dup_mse

    def _should_save_frame(self) -> bool:
        """判断当前帧是否达到落盘时机。"""
        now = time.perf_counter()
        if self._capture_last_save_time == 0.0:
            self._capture_last_save_time = now
            return True

        if now - self._capture_last_save_time >= self._capture_save_interval_sec:
            self._capture_last_save_time = now
            return True
        return False

    def _save_capture_frame(self, frame: Any) -> None:
        """按固定间隔将采集帧落盘并写入样本元数据。"""
        if self._capture_images_dir is None or self._capture_meta_file is None:
            return
        if not HAS_CV2:
            if self._capture_saved_count == 0:
                self._append_log("当前环境缺少 cv2，无法执行图片落盘。")
            return

        timestamp = datetime.utcnow()
        timestamp_iso = timestamp.isoformat(timespec="milliseconds") + "Z"
        timestamp_ms = int(timestamp.timestamp() * 1000)
        actual_interval_ms = -1
        if self._capture_prev_saved_timestamp_ms is not None:
            actual_interval_ms = max(timestamp_ms - self._capture_prev_saved_timestamp_ms, 0)

        filename = f"frame_{self._capture_saved_count:06d}.jpg"
        image_path = self._capture_images_dir / filename
        image_rel_path = f"images/{filename}"

        if not self._write_image_robust(image_path, frame):
            self._capture_stats["write_failures"] = self._capture_stats.get("write_failures", 0) + 1
            raise RuntimeError(f"图片写入失败: {image_path}")

        height = int(frame.shape[0]) if hasattr(frame, "shape") and len(frame.shape) >= 2 else 0
        width = int(frame.shape[1]) if hasattr(frame, "shape") and len(frame.shape) >= 2 else 0
        blur_score, dup_mse = self._compute_quality_scores(frame)

        # 首版使用保守阈值，仅用于标记，不直接丢弃样本。
        blur_threshold = 30.0
        duplicate_threshold = 1.0
        filtered = False
        filter_reason = ""
        if blur_score >= 0 and blur_score < blur_threshold:
            filtered = True
            filter_reason = "blur"
            self._capture_stats["filtered_blur"] = self._capture_stats.get("filtered_blur", 0) + 1
        elif dup_mse >= 0 and dup_mse < duplicate_threshold:
            filtered = True
            filter_reason = "duplicate"
            self._capture_stats["filtered_duplicate"] = (
                self._capture_stats.get("filtered_duplicate", 0) + 1
            )

        sample = {
            "sample_id": f"{self._capture_session_name}_{self._capture_saved_count:06d}",
            "timestamp_ms": timestamp_ms,
            "timestamp_iso": timestamp_iso,
            "image_rel_path": image_rel_path,
            "image_path": image_rel_path,
            "scene": "other",
            "state": "auto_filtered" if filtered else "raw",
            "backend": getattr(self._capture_engine, "active_backend", "unknown"),
            "window_state": self._detect_window_state(self._capture_window_title),
            "width": width,
            "height": height,
            "actual_interval_ms": actual_interval_ms,
            "expected_interval_ms": self._capture_expected_interval_ms,
            "quality": {"blur_score": blur_score, "dup_mse_to_prev": dup_mse},
            "manual_flag": "none",
            "source_session": self._capture_session_name,
            "source_image_path": str(image_path),
            "filtered": filtered,
            "filter_reason": filter_reason,
        }

        with self._capture_meta_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(sample, ensure_ascii=False) + "\n")

        self._capture_saved_count += 1
        self._capture_stats["saved"] = self._capture_saved_count
        self._capture_prev_saved_timestamp_ms = timestamp_ms
        self._capture_prev_saved_frame = frame.copy() if hasattr(frame, "copy") else frame

        if self._using_demo_data:
            self._using_demo_data = False
            self._samples = []
            self.timeline_panel.set_samples([])
            self.frame_strip.set_frames([])
            self.session_list.clear()
            self.session_list.addItem(QListWidgetItem(self._capture_session_name))
            self.session_list.setCurrentRow(0)

        self._samples.append(sample)
        self.timeline_panel.append_sample(sample)
        self.frame_strip.append_frame(image_rel_path)

    def _write_image_robust(self, image_path: Path, frame: Any) -> bool:
        """稳健写图：优先 imwrite，失败后使用 imencode+tofile 回退。"""
        if not HAS_CV2:
            return False

        # 第一优先：常规写入。
        if cv2.imwrite(str(image_path), frame):
            return True

        # 回退方案：兼容 Windows 上部分 OpenCV 构建对 Unicode 路径支持不足的情况。
        try:
            encoded_ok, encoded = cv2.imencode(".jpg", frame)
            if not encoded_ok:
                return False
            encoded.tofile(str(image_path))
            return True
        except Exception:
            return False

    def _on_range_changed(self, start_idx: int, end_idx: int) -> None:
        """同步导出参数区间。"""
        self.export_panel.set_range(len(self._samples) - 1, start_idx, end_idx)

    def _on_sample_activated(self, sample: Dict[str, object]) -> None:
        """双击样本后的日志反馈。"""
        self._append_log(f"定位样本: {sample.get('image_rel_path', '-')}")

    def _on_frame_selected(self, image_path: str) -> None:
        """点击缩略图列表后的日志反馈。"""
        self._append_log(f"选中帧: {image_path}")

    def _on_export_requested(self, payload: Dict[str, object]) -> None:
        """处理导出请求。"""
        if not self._samples:
            self._append_log("导出失败：当前没有可导出的样本。")
            return

        start_idx = max(0, int(payload.get("start_index", 0)))
        end_idx = max(0, int(payload.get("end_index", 0)))
        interval_sec = max(1, int(payload.get("interval_sec", 1)))
        output_dir = str(payload.get("output_dir", "assets/images/selected")).strip()
        if not output_dir:
            output_dir = "assets/images/selected"

        self._append_log(
            f"收到导出请求: 区间={start_idx}-{end_idx}, 频率={interval_sec}s, 输出={output_dir}"
        )

        try:
            selected_samples, selection_manifest = self._build_selection_manifest(
                start_idx=start_idx,
                end_idx=end_idx,
                interval_sec=interval_sec,
            )
            if not selected_samples:
                self._append_log("导出取消：筛选结果为空。")
                return

            export_summary = self._export_selected_samples(
                selected_samples=selected_samples,
                selection_manifest=selection_manifest,
                output_dir=output_dir,
            )
            self._append_log(
                "导出完成: "
                f"export_id={export_summary.get('export_id', '-')}, "
                f"output={export_summary.get('output_dir', '-')}, "
                f"total={export_summary.get('total', 0)}, "
                f"missing={export_summary.get('missing', 0)}"
            )
        except Exception as exc:
            self._append_log(f"导出失败: {exc}")

    def _sample_timestamp_ms(self, sample: Dict[str, object], fallback_ms: int) -> int:
        """提取样本毫秒时间戳，缺失时回落到调用方提供的默认值。"""
        ts = sample.get("timestamp_ms")
        if isinstance(ts, (int, float)):
            return int(ts)

        iso = str(sample.get("timestamp_iso", "")).strip()
        if iso:
            try:
                dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
                return int(dt.timestamp() * 1000)
            except Exception:
                pass
        return fallback_ms

    def _build_selection_manifest(
        self,
        start_idx: int,
        end_idx: int,
        interval_sec: int,
    ) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
        """按闭区间和时间桶规则生成导出选择集与 selection manifest。"""
        if not self._samples:
            return [], {}

        lo = max(0, min(start_idx, end_idx))
        hi = min(max(start_idx, end_idx), len(self._samples) - 1)
        if lo > hi:
            return [], {}

        interval_ms = max(1, interval_sec) * 1000
        candidates: List[Dict[str, object]] = []
        source_sessions = set()

        base_fallback = int(time.time() * 1000)
        for idx in range(lo, hi + 1):
            sample = self._samples[idx]
            manual_flag = str(sample.get("manual_flag", "none")).strip().lower() or "none"
            if manual_flag == "reject":
                continue

            ts_ms = self._sample_timestamp_ms(sample, fallback_ms=base_fallback + idx * 1000)
            enriched = dict(sample)
            enriched["timestamp_ms"] = ts_ms
            enriched["manual_flag"] = manual_flag
            enriched["sample_id"] = str(
                enriched.get("sample_id", f"sample_{idx:06d}")
            )
            source_session = str(
                enriched.get("source_session", self._capture_session_name or "unknown_session")
            )
            enriched["source_session"] = source_session
            candidates.append(enriched)
            source_sessions.add(source_session)

        candidates.sort(key=lambda item: int(item.get("timestamp_ms", 0)))
        if not candidates:
            return [], {}

        start_ms = int(candidates[0]["timestamp_ms"])
        end_ms = int(candidates[-1]["timestamp_ms"])
        bucket_start = start_ms
        pointer = 0
        missed_buckets = 0
        selected: List[Dict[str, object]] = []

        while bucket_start <= end_ms:
            bucket_end = bucket_start + interval_ms
            bucket_items: List[Dict[str, object]] = []

            while pointer < len(candidates):
                ts_ms = int(candidates[pointer]["timestamp_ms"])
                if ts_ms < bucket_start:
                    pointer += 1
                    continue
                if ts_ms >= bucket_end:
                    break
                bucket_items.append(candidates[pointer])
                pointer += 1

            if not bucket_items:
                missed_buckets += 1
                bucket_start += interval_ms
                continue

            bucket_center = bucket_start + interval_ms // 2
            best = min(
                bucket_items,
                key=lambda item: (
                    abs(int(item.get("timestamp_ms", 0)) - bucket_center),
                    int(item.get("timestamp_ms", 0)),
                    str(item.get("sample_id", "")),
                ),
            )
            selected.append(best)
            bucket_start += interval_ms

        selection_id = f"sel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        manual_counter = {"star": 0, "review": 0, "reject": 0, "none": 0}
        for sample in selected:
            flag = str(sample.get("manual_flag", "none")).strip().lower() or "none"
            manual_counter[flag] = manual_counter.get(flag, 0) + 1

        selection_manifest: Dict[str, object] = {
            "schema_version": "v2.2",
            "selection_id": selection_id,
            "created_at": self._iso_utc_now(),
            "source_sessions": sorted(source_sessions),
            "range": {"start_ms": start_ms, "end_ms": end_ms, "inclusive": True},
            "sampling": {
                "mode": "bucket_nearest",
                "frequency_sec": interval_sec,
                "missing_bucket_policy": "skip",
                "tie_breaker": "timestamp_then_sample_id",
                "missed_buckets": missed_buckets,
            },
            "filters": {"manual_flag_not_in": ["reject"]},
            "result": {
                "total": len(selected),
                "star": manual_counter.get("star", 0),
                "review": manual_counter.get("review", 0),
                "reject": manual_counter.get("reject", 0),
                "none": manual_counter.get("none", 0),
            },
        }
        return selected, selection_manifest

    def _resolve_source_image_path(self, sample: Dict[str, object]) -> Optional[Path]:
        """解析样本来源图片绝对路径。"""
        direct = str(sample.get("source_image_path", "")).strip()
        if direct:
            path = Path(direct)
            if path.exists():
                return path

        image_rel = str(sample.get("image_rel_path", sample.get("image_path", ""))).strip()
        if not image_rel:
            return None

        if self._capture_session_dir is not None:
            current_path = self._capture_session_dir / image_rel
            if current_path.exists():
                return current_path

        source_session = str(sample.get("source_session", "")).strip()
        if source_session:
            session_path = Path("assets/images/raw") / source_session / image_rel
            if session_path.exists():
                return session_path

        rel_path = Path(image_rel)
        if rel_path.is_absolute() and rel_path.exists():
            return rel_path

        return None

    def _resolve_unique_export_dir(self, output_root: Path, base_name: str) -> Path:
        """解决导出目录冲突，已存在时自动追加版本后缀。"""
        target = output_root / base_name
        if not target.exists():
            return target
        idx = 2
        while True:
            candidate = output_root / f"{base_name}_v{idx}"
            if not candidate.exists():
                return candidate
            idx += 1

    def _materialize_image(self, source: Path, target: Path) -> str:
        """优先硬链接，失败后回退复制。"""
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(str(source), str(target))
            return "hardlink"
        except Exception:
            shutil.copy2(str(source), str(target))
            return "copy"

    def _assign_split_by_session(
        self,
        samples: List[Dict[str, object]],
    ) -> Tuple[Dict[str, str], Dict[str, int], Dict[str, float]]:
        """按会话分配数据子集，确保同会话不跨集合。"""
        split_ratio = {"train": 0.8, "val": 0.15, "test": 0.05}
        total = len(samples)
        split_targets = {
            "train": int(total * split_ratio["train"]),
            "val": int(total * split_ratio["val"]),
        }
        split_targets["test"] = max(total - split_targets["train"] - split_targets["val"], 0)

        sessions: Dict[str, List[Dict[str, object]]] = {}
        for sample in samples:
            session = str(sample.get("source_session", self._capture_session_name or "unknown_session"))
            sessions.setdefault(session, []).append(sample)

        assignments: Dict[str, str] = {}
        split_counts = {"train": 0, "val": 0, "test": 0}

        if len(sessions) <= 1:
            for sample in samples:
                assignments[str(sample.get("sample_id", ""))] = "train"
            split_counts["train"] = len(samples)
            return assignments, split_counts, split_ratio

        session_items = sorted(sessions.items(), key=lambda item: len(item[1]), reverse=True)
        for _, grouped_samples in session_items:
            preferred = max(
                ("train", "val", "test"),
                key=lambda split: split_targets.get(split, 0) - split_counts.get(split, 0),
            )
            if split_targets.get(preferred, 0) - split_counts.get(preferred, 0) <= 0:
                preferred = "train"

            for sample in grouped_samples:
                assignments[str(sample.get("sample_id", ""))] = preferred
            split_counts[preferred] += len(grouped_samples)

        return assignments, split_counts, split_ratio

    def _build_validation_report(
        self,
        export_dir: Path,
        split_counts: Dict[str, int],
        missing_sources: int,
        failed_items: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """构建导出结果校验报告。"""
        class_count = 3
        total_images = 0
        total_labels = 0
        missing_labels = 0
        malformed_labels = 0
        invalid_class = 0
        invalid_bbox = 0

        for split in ("train", "val", "test"):
            image_dir = export_dir / "images" / split
            label_dir = export_dir / "labels" / split
            image_files = sorted(image_dir.glob("*.*"))
            total_images += len(image_files)
            for image_file in image_files:
                label_file = label_dir / f"{image_file.stem}.txt"
                if not label_file.exists():
                    missing_labels += 1
                    continue
                total_labels += 1
                try:
                    lines = label_file.read_text(encoding="utf-8").splitlines()
                except Exception:
                    malformed_labels += 1
                    continue

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) != 5:
                        malformed_labels += 1
                        continue
                    try:
                        class_id = int(parts[0])
                        xc, yc, w, h = map(float, parts[1:])
                    except Exception:
                        malformed_labels += 1
                        continue

                    if class_id < 0 or class_id >= class_count:
                        invalid_class += 1
                    if (
                        xc < 0
                        or xc > 1
                        or yc < 0
                        or yc > 1
                        or w <= 0
                        or w > 1
                        or h <= 0
                        or h > 1
                    ):
                        invalid_bbox += 1

        blocking_errors: List[str] = []
        if malformed_labels > 0:
            blocking_errors.append("存在标签格式错误")
        if invalid_class > 0:
            blocking_errors.append("存在非法类别ID")
        if invalid_bbox > 0:
            blocking_errors.append("存在非法边界框坐标")

        return {
            "schema_version": "v2.2",
            "created_at": self._iso_utc_now(),
            "status": "pass" if not blocking_errors else "fail",
            "summary": {
                "total_images": total_images,
                "total_labels": total_labels,
                "missing_labels": missing_labels,
                "missing_sources": missing_sources,
                "malformed_labels": malformed_labels,
                "invalid_class_id": invalid_class,
                "invalid_bbox": invalid_bbox,
            },
            "split_counts": split_counts,
            "failed_items": failed_items,
            "blocking_errors": blocking_errors,
        }

    def _export_selected_samples(
        self,
        selected_samples: List[Dict[str, object]],
        selection_manifest: Dict[str, object],
        output_dir: str,
    ) -> Dict[str, object]:
        """将选择集事务化导出为可训练目录结构。"""
        output_root = Path(output_dir)
        output_root.mkdir(parents=True, exist_ok=True)

        export_id = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        final_dir = self._resolve_unique_export_dir(output_root, export_id)
        tmp_dir = output_root / f"tmp_{final_dir.name}"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        for split in ("train", "val", "test"):
            (tmp_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (tmp_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

        assignments, split_counts, split_ratio = self._assign_split_by_session(selected_samples)
        io_stats = {"hardlink": 0, "copy": 0}
        failed_items: List[Dict[str, object]] = []
        copied_images = 0
        copied_labels = 0
        copied_split_counts = {"train": 0, "val": 0, "test": 0}

        checkpoint_path = tmp_dir / "export_checkpoint.json"
        checkpoint = {
            "schema_version": "v2.2",
            "export_id": final_dir.name,
            "status": "running",
            "phase": "copy_images",
            "last_processed_index": -1,
            "copied_images": 0,
            "copied_labels": 0,
            "failed_items": 0,
            "updated_at": self._iso_utc_now(),
        }

        def flush_checkpoint() -> None:
            checkpoint["updated_at"] = self._iso_utc_now()
            checkpoint_path.write_text(
                json.dumps(checkpoint, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        flush_checkpoint()

        try:
            for idx, sample in enumerate(selected_samples):
                sample_id = str(sample.get("sample_id", f"sample_{idx:06d}"))
                split = assignments.get(sample_id, "train")
                source_path = self._resolve_source_image_path(sample)
                checkpoint["last_processed_index"] = idx

                if source_path is None or not source_path.exists():
                    failed_items.append(
                        {
                            "sample_id": sample_id,
                            "reason": "missing_source_image",
                            "image_rel_path": str(sample.get("image_rel_path", "")),
                        }
                    )
                    checkpoint["failed_items"] = int(checkpoint["failed_items"]) + 1
                    if idx % 20 == 0:
                        flush_checkpoint()
                    continue

                suffix = source_path.suffix.lower() or ".jpg"
                target_name = f"{idx:06d}{suffix}"
                target_image = tmp_dir / "images" / split / target_name
                io_mode = self._materialize_image(source_path, target_image)
                io_stats[io_mode] = io_stats.get(io_mode, 0) + 1

                target_label = tmp_dir / "labels" / split / f"{Path(target_name).stem}.txt"
                target_label.write_text("", encoding="utf-8")

                copied_images += 1
                copied_labels += 1
                copied_split_counts[split] = copied_split_counts.get(split, 0) + 1
                checkpoint["copied_images"] = copied_images
                checkpoint["copied_labels"] = copied_labels
                if idx % 20 == 0:
                    flush_checkpoint()

            checkpoint["phase"] = "write_manifest"
            flush_checkpoint()

            data_yaml = (
                "path: .\n"
                "train: images/train\n"
                "val: images/val\n"
                "test: images/test\n"
                "names:\n"
                "  0: monster\n"
                "  1: hero\n"
                "  2: gate\n"
            )
            (tmp_dir / "data.yaml").write_text(data_yaml, encoding="utf-8")

            export_manifest = dict(selection_manifest)
            export_manifest.update(
                {
                    "export_id": final_dir.name,
                    "source_selection_id": selection_manifest.get("selection_id"),
                    "created_at": self._iso_utc_now(),
                    "mode": "by_filter",
                    "split": {
                        "train": split_ratio["train"],
                        "val": split_ratio["val"],
                        "test": split_ratio["test"],
                        "seed": 42,
                    },
                    "io_strategy": {"primary": "hardlink", "fallback": "copy"},
                    "io_stats": io_stats,
                    "result": {
                        "total": copied_images,
                        "train": copied_split_counts.get("train", 0),
                        "val": copied_split_counts.get("val", 0),
                        "test": copied_split_counts.get("test", 0),
                        "missing_sources": len(failed_items),
                        "assigned_before_missing": split_counts,
                    },
                }
            )

            validation_report = self._build_validation_report(
                export_dir=tmp_dir,
                split_counts=copied_split_counts,
                missing_sources=len(failed_items),
                failed_items=failed_items,
            )

            (tmp_dir / "selection_manifest.json").write_text(
                json.dumps(export_manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (tmp_dir / "validation_report.json").write_text(
                json.dumps(validation_report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            checkpoint["status"] = "completed"
            checkpoint["phase"] = "done"
            flush_checkpoint()

            if final_dir.exists():
                shutil.rmtree(final_dir, ignore_errors=True)
            tmp_dir.replace(final_dir)

            return {
                "export_id": final_dir.name,
                "output_dir": str(final_dir),
                "total": copied_images,
                "missing": len(failed_items),
            }
        except Exception:
            checkpoint["status"] = "failed"
            checkpoint["phase"] = "failed"
            flush_checkpoint()
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise

    def _on_start_pseudo_task(self, payload: Dict[str, object]) -> None:
        """启动预标注任务（当前为 UI 演示用模拟流程）。"""
        self._current_task_id = f"task_{uuid.uuid4().hex[:8]}"
        self._task_processed = 0

        task = {
            "task_id": self._current_task_id,
            "status": "running",
            "progress": {"processed": 0, "total": self._task_total, "failed": 0},
            "error_summary": "",
        }
        self.pseudo_label_panel.upsert_task(task)

        self._append_log(
            "预标注任务启动: "
            f"task_id={self._current_task_id}, "
            f"dataset={payload.get('dataset_path', '')}, "
            f"model={payload.get('model_path', '')}, "
            f"version={payload.get('pseudo_version', 'v1.0')}"
        )
        self._task_timer.start(200)

    def _on_stop_pseudo_task(self, task_id: str) -> None:
        """停止预标注任务。"""
        target_id = task_id or self._current_task_id
        if not target_id:
            self._append_log("停止预标注任务失败：未选择任务。")
            return

        self._task_timer.stop()
        self.pseudo_label_panel.upsert_task(
            {
                "task_id": target_id,
                "status": "stopped",
                "progress": {
                    "processed": self._task_processed,
                    "total": self._task_total,
                    "failed": 0,
                },
                "error_summary": "手动停止",
            }
        )
        self._append_log(f"预标注任务已停止: {target_id}")

    def _tick_pseudo_task(self) -> None:
        """模拟预标注任务进度推进。"""
        self._task_processed += 25

        if self._task_processed >= self._task_total:
            self._task_processed = self._task_total
            self._task_timer.stop()
            self.pseudo_label_panel.upsert_task(
                {
                    "task_id": self._current_task_id,
                    "status": "success",
                    "progress": {
                        "processed": self._task_processed,
                        "total": self._task_total,
                        "failed": 0,
                    },
                    "error_summary": "",
                }
            )
            self._append_log(f"预标注任务完成: {self._current_task_id}")
            return

        self.pseudo_label_panel.upsert_task(
            {
                "task_id": self._current_task_id,
                "status": "running",
                "progress": {
                    "processed": self._task_processed,
                    "total": self._task_total,
                    "failed": 0,
                },
                "error_summary": "",
            }
        )

    def _on_session_selected(self, item: QListWidgetItem) -> None:
        """切换会话时记录日志。"""
        self._append_log(f"会话切换: {item.text()}")

    def _append_log(self, message: str) -> None:
        """统一写入界面日志与系统日志。"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.appendPlainText(f"[{timestamp}] {message}")
        logger.info(f"[TimelineWorkbench] {message}")

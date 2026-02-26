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
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

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
)

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

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AradVision 数据采集与预标注工作台")
        self.setMinimumSize(980, 680)
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
        self._main_vertical_splitter: QSplitter
        self._capture_outer_splitter: QSplitter
        self._capture_content_splitter: QSplitter
        self._responsive_mode: str = ""

        self.session_list: QListWidget
        self.timeline_panel: TimelinePanel
        self.frame_strip: FrameStrip
        self.video_preview: VideoPreviewWidget
        self.export_panel: ExportPanel
        self.pseudo_label_panel: PseudoLabelPanel

        self.log_text: QPlainTextEdit

        self._init_ui()
        self._load_runtime_config()
        self._connect_signals()
        self._load_demo_data()
        self._refresh_window_candidates()
        self.apply_theme("light")
        self._apply_responsive_layout(self.width(), force=True)

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
        self.workspace_stack.addWidget(self._build_pseudo_workspace())
        log_card = QWidget()
        log_card.setObjectName("LogCard")
        log_layout = QVBoxLayout(log_card)
        self._log_layout = log_layout
        log_layout.setContentsMargins(16, 16, 16, 16)
        log_layout.setSpacing(8)

        log_title = QLabel("系统日志")
        log_title.setObjectName("SectionTitle")
        log_layout.addWidget(log_title)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)
        self.log_text.setMinimumHeight(120)
        log_layout.addWidget(self.log_text)

        self._main_vertical_splitter = QSplitter(Qt.Vertical)
        self._main_vertical_splitter.setHandleWidth(10)
        self._main_vertical_splitter.addWidget(workspace_card)
        self._main_vertical_splitter.addWidget(log_card)
        self._main_vertical_splitter.setStretchFactor(0, 1)
        self._main_vertical_splitter.setStretchFactor(1, 0)
        root_layout.addWidget(self._main_vertical_splitter, stretch=1)

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
        """构建采集工作区布局。"""
        workspace = QWidget()
        layout = QHBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._capture_outer_splitter = QSplitter(Qt.Horizontal)
        self._capture_outer_splitter.setHandleWidth(10)
        layout.addWidget(self._capture_outer_splitter)

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
        self._capture_outer_splitter.addWidget(session_panel)

        self._capture_content_splitter = QSplitter(Qt.Horizontal)
        self._capture_content_splitter.setHandleWidth(10)
        self._capture_outer_splitter.addWidget(self._capture_content_splitter)

        center_panel = QWidget()
        center_panel.setObjectName("CenterPanel")
        center_layout = QVBoxLayout(center_panel)
        self._center_layout = center_layout
        center_layout.setContentsMargins(16, 16, 16, 16)
        center_layout.setSpacing(12)
        preview_title = QLabel("实时预览与时间线")
        preview_title.setObjectName("SectionTitle")
        center_layout.addWidget(preview_title)
        self.video_preview = VideoPreviewWidget()
        self.timeline_panel = TimelinePanel()
        self.frame_strip = FrameStrip()
        center_layout.addWidget(self.video_preview, stretch=2)
        center_layout.addWidget(self.timeline_panel, stretch=2)
        center_layout.addWidget(self.frame_strip, stretch=1)
        self._capture_content_splitter.addWidget(center_panel)

        export_panel_card = QWidget()
        export_panel_card.setObjectName("ExportPanelCard")
        export_layout = QVBoxLayout(export_panel_card)
        self._export_layout = export_layout
        export_layout.setContentsMargins(16, 16, 16, 16)
        export_layout.setSpacing(10)
        self.export_panel = ExportPanel()
        self.export_panel.setMinimumWidth(260)
        export_layout.addWidget(self.export_panel, stretch=1)
        self._capture_content_splitter.addWidget(export_panel_card)

        self._capture_outer_splitter.setSizes([230, 980])
        self._capture_content_splitter.setSizes([760, 320])
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

    def _apply_responsive_layout(self, width: int, force: bool = False) -> None:
        """根据窗口宽度切换布局密度与分栏策略。"""
        if width < 1280:
            mode = "dense"
        elif width < 1540:
            mode = "compact"
        else:
            mode = "default"

        if not force and mode == self._responsive_mode:
            return

        self._responsive_mode = mode

        if mode == "default":
            outer_margin = 24
            card_padding = 16
            section_spacing = 12
            root_spacing = 16
            self._capture_content_splitter.setOrientation(Qt.Horizontal)
            self.export_panel.setMinimumWidth(300)
            self.session_list.setMinimumWidth(220)
            self.video_preview.setMinimumSize(640, 360)
            self._capture_outer_splitter.setSizes([240, 1020])
            self._capture_content_splitter.setSizes([780, 340])
            self._main_vertical_splitter.setSizes([760, 200])
            self.capture_control_bar.set_compact_mode(False)
            self._page_subtitle.setVisible(True)
        elif mode == "compact":
            outer_margin = 16
            card_padding = 14
            section_spacing = 10
            root_spacing = 12
            self._capture_content_splitter.setOrientation(Qt.Horizontal)
            self.export_panel.setMinimumWidth(260)
            self.session_list.setMinimumWidth(180)
            self.video_preview.setMinimumSize(540, 300)
            self._capture_outer_splitter.setSizes([210, 920])
            self._capture_content_splitter.setSizes([690, 300])
            self._main_vertical_splitter.setSizes([700, 180])
            self.capture_control_bar.set_compact_mode(True)
            self._page_subtitle.setVisible(True)
        else:
            outer_margin = 12
            card_padding = 12
            section_spacing = 8
            root_spacing = 10
            self._capture_content_splitter.setOrientation(Qt.Vertical)
            self.export_panel.setMinimumWidth(0)
            self.session_list.setMinimumWidth(160)
            self.video_preview.setMinimumSize(440, 250)
            self._capture_outer_splitter.setSizes([190, 860])
            self._capture_content_splitter.setSizes([560, 260])
            self._main_vertical_splitter.setSizes([640, 170])
            self.capture_control_bar.set_compact_mode(True)
            self._page_subtitle.setVisible(False)

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
            self._samples.append(
                {
                    "sample_id": f"sample_{idx:06d}",
                    "timestamp_iso": ts.isoformat() + "Z",
                    "scene": scene,
                    "image_rel_path": f"images/{scene}_{idx:06d}.jpg",
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
        index = 0 if workspace == "capture" else 1
        self.workspace_stack.setCurrentIndex(index)
        self._append_log(f"切换工作区: {'采集工作区' if index == 0 else '预标注工作区'}")

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
            self._capture_timer.start(self._capture_timer_interval_ms)

            active_backend = getattr(engine, "active_backend", "unknown")
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
            self._append_log(f"采集启动失败: {exc}")

    def _on_capture_stop(self) -> None:
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
        self._append_log("采集已停止。")
        self.video_preview.clear_frame()

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
        except Exception as exc:
            self._capture_error_streak += 1
            if self._capture_error_streak == 1 or self._capture_error_streak % 5 == 0:
                self._append_log(
                    f"实时取帧失败({self._capture_error_streak}): {exc}"
                )

            if self._capture_error_streak >= 10:
                self._append_log("连续取帧失败过多，已自动停止采集。")
                self._on_capture_stop()

    def _prepare_capture_session(self, window_title: str) -> None:
        """初始化本次采集会话目录与元数据文件。"""
        session_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_window = self._build_ascii_window_tag(window_title)
        self._capture_session_name = f"ui_capture_{session_stamp}_{safe_window}"

        self._capture_session_dir = Path("assets/images/raw") / self._capture_session_name
        self._capture_images_dir = self._capture_session_dir / "images"
        meta_dir = self._capture_session_dir / "meta"
        self._capture_meta_file = meta_dir / "samples.jsonl"

        self._capture_images_dir.mkdir(parents=True, exist_ok=True)
        meta_dir.mkdir(parents=True, exist_ok=True)

        self._capture_saved_count = 0
        self._capture_last_save_time = 0.0

        if self._capture_meta_file.exists():
            self._capture_meta_file.unlink()

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

        filename = f"frame_{self._capture_saved_count:06d}.jpg"
        image_path = self._capture_images_dir / filename
        image_rel_path = f"images/{filename}"

        if not self._write_image_robust(image_path, frame):
            raise RuntimeError(f"图片写入失败: {image_path}")

        height = int(frame.shape[0]) if hasattr(frame, "shape") and len(frame.shape) >= 2 else 0
        width = int(frame.shape[1]) if hasattr(frame, "shape") and len(frame.shape) >= 2 else 0

        sample = {
            "sample_id": f"{self._capture_session_name}_{self._capture_saved_count:06d}",
            "timestamp_ms": timestamp_ms,
            "timestamp_iso": timestamp_iso,
            "image_rel_path": image_rel_path,
            "scene": "other",
            "backend": getattr(self._capture_engine, "active_backend", "unknown"),
            "width": width,
            "height": height,
            "filtered": False,
        }

        with self._capture_meta_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(sample, ensure_ascii=False) + "\n")

        self._capture_saved_count += 1

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
        start_idx = int(payload.get("start_index", 0))
        end_idx = int(payload.get("end_index", 0))
        interval_sec = int(payload.get("interval_sec", 1))
        output_dir = str(payload.get("output_dir", "assets/images/selected"))

        self._append_log(
            f"收到导出请求: 区间={start_idx}-{end_idx}, 频率={interval_sec}s, 输出={output_dir}"
        )

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

"""
主窗口类

AradVision 控制面板的主窗口。

Author: haneball17
Date: 2026-02-11
Version: 0.1.3
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QLabel, QStatusBar, QMenuBar, QToolBar,
    QPushButton, QAction, QStyle
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QKeySequence

from core.logger import logger
from core.config import ConfigLoader


class MainWindow(QMainWindow):
    """
    主窗口类

    AradVision 控制面板的主窗口，包含4个标签页：
    1. 实时监控 - 视频预览和状态显示
    2. 参数配置 - 参数调整和控制
    3. 系统日志 - 日志查看和过滤
    4. 关于 - 项目信息
    """

    def __init__(self):
        super().__init__()

        # 窗口基本设置
        self.setWindowTitle("AradVision 控制面板")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # 核心组件
        self.engine_thread = None
        self.config_loader = ConfigLoader.instance()

        # UI 组件（延迟初始化）
        self.tab_widget = None
        self.video_preview = None
        self.status_panel = None
        self.param_panel = None
        self.log_panel = None

        # 定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_display)

        # 初始化
        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()
        self.load_settings()

        # 应用默认主题
        self.apply_theme("dark")

        logger.info("主窗口初始化完成")

    def init_ui(self):
        """初始化UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 标签页 1: 实时监控
        self.create_monitor_tab()

        # 标签页 2: 参数配置
        self.create_param_tab()

        # 标签页 3: 系统日志
        self.create_log_tab()

        # 标签页 4: 关于
        self.create_about_tab()

    def create_monitor_tab(self):
        """创建实时监控标签页"""
        monitor_widget = QWidget()
        layout = QVBoxLayout(monitor_widget)

        # TODO: 添加视频预览和状态面板
        placeholder = QLabel("实时监控标签页")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

        self.tab_widget.addTab(monitor_widget, "实时监控")

    def create_param_tab(self):
        """创建参数配置标签页"""
        param_widget = QWidget()
        layout = QVBoxLayout(param_widget)

        # TODO: 添加参数配置面板
        placeholder = QLabel("参数配置标签页")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

        self.tab_widget.addTab(param_widget, "参数配置")

    def create_log_tab(self):
        """创建系统日志标签页"""
        log_widget = QWidget()
        layout = QVBoxLayout(log_widget)

        # TODO: 添加日志面板
        placeholder = QLabel("系统日志标签页")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

        self.tab_widget.addTab(log_widget, "系统日志")

    def create_about_tab(self):
        """创建关于标签页"""
        about_widget = QWidget()
        layout = QVBoxLayout(about_widget)
        layout.setAlignment(Qt.AlignCenter)

        # 项目信息
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)

        # 标题
        title_label = QLabel("AradVision")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)

        # 副标题
        subtitle_label = QLabel("DNF 视觉辅助自动化系统")
        subtitle_label.setStyleSheet("font-size: 14px; color: #888888;")
        subtitle_label.setAlignment(Qt.AlignCenter)

        # 版本信息
        version_label = QLabel("版本: v0.1.3")
        version_label.setAlignment(Qt.AlignCenter)

        # 作者信息
        author_label = QLabel("作者: haneball17, yangmq17")
        author_label.setAlignment(Qt.AlignCenter)

        info_layout.addWidget(title_label)
        info_layout.addWidget(subtitle_label)
        info_layout.addSpacing(20)
        info_layout.addWidget(version_label)
        info_layout.addWidget(author_label)
        info_layout.addStretch()

        layout.addLayout(info_layout)
        self.tab_widget.addTab(about_widget, "关于")

    def init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("新建配置", self.new_config)
        file_menu.addAction("打开配置", self.open_config)
        file_menu.addAction("保存配置", self.save_config)
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)

        # 控制菜单
        control_menu = menubar.addMenu("控制")
        control_menu.addAction("启动系统", self.start_system, QKeySequence("F5"))
        control_menu.addAction("停止系统", self.stop_system, QKeySequence("F12"))
        control_menu.addAction("暂停/继续", self.toggle_pause)

        # 视图菜单
        view_menu = menubar.addMenu("视图")
        view_menu.addAction("切换到实时监控", lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction("切换到参数配置", lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction("切换到系统日志", lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction("切换主题", self.toggle_theme)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("文档", self.show_docs)
        help_menu.addAction("关于", self.show_about)

    def init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)

        # 添加工具按钮
        start_action = QAction("启动", self)
        start_action.triggered.connect(self.start_system)
        toolbar.addAction(start_action)

        pause_action = QAction("暂停", self)
        pause_action.triggered.connect(self.toggle_pause)
        toolbar.addAction(pause_action)

        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self.stop_system)
        toolbar.addAction(stop_action)

        toolbar.addSeparator()

        save_action = QAction("保存", self)
        save_action.triggered.connect(self.save_config)
        toolbar.addAction(save_action)

        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh)
        toolbar.addAction(refresh_action)

    def init_statusbar(self):
        """初始化状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)

        # FPS 标签
        self.fps_label = QLabel("FPS: --")
        self.status_bar.addPermanentWidget(self.fps_label)

        # 系统状态标签
        self.system_state_label = QLabel("状态: STOPPED")
        self.status_bar.addPermanentWidget(self.system_state_label)

        # 版本标签
        self.version_label = QLabel("v0.1.3")
        self.status_bar.addPermanentWidget(self.version_label)

    def load_settings(self):
        """加载设置"""
        # TODO: 从配置文件加载设置
        pass

    def apply_theme(self, theme: str):
        """应用主题"""
        # TODO: 实现主题切换
        logger.info(f"应用主题: {theme}")

    # ==================== 菜单操作 ====================

    def new_config(self):
        """新建配置"""
        logger.info("新建配置")

    def open_config(self):
        """打开配置"""
        logger.info("打开配置")

    def save_config(self):
        """保存配置"""
        logger.info("保存配置")

    # ==================== 系统控制 ====================

    def start_system(self):
        """启动系统"""
        logger.info("启动系统")
        self.status_label.setText("系统运行中...")
        self.system_state_label.setText("状态: RUNNING")

    def stop_system(self):
        """停止系统"""
        logger.info("停止系统")
        self.status_label.setText("系统已停止")
        self.system_state_label.setText("状态: STOPPED")

    def toggle_pause(self):
        """切换暂停状态"""
        logger.info("切换暂停状态")

    def toggle_theme(self):
        """切换主题"""
        logger.info("切换主题")

    def refresh(self):
        """刷新"""
        logger.info("刷新")

    # ==================== 帮助 ====================

    def show_docs(self):
        """显示文档"""
        logger.info("显示文档")

    def show_about(self):
        """显示关于"""
        self.tab_widget.setCurrentIndex(3)  # 切换到关于页

    # ==================== 状态更新 ====================

    def update_status_display(self):
        """更新状态显示"""
        # TODO: 从引擎线程获取状态并更新UI
        pass

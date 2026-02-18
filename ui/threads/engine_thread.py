"""
引擎线程模块

将核心引擎包装为 Qt 工作线程，实现后台数据处理。

Author: haneball17
Date: 2026-02-11
"""

import time
from typing import Any, Optional

from PyQt5.QtCore import QThread

from core.logger import logger
from core.config import CaptureConfig, ConfigLoader
from ui.threads.signals import EngineSignals

# 导入核心模块
try:
    from core.capture import create_capture_engine
    from vision.mock_detector import MockYoloDetector
    from logic.world_model import WorldModel
    from logic.bot_fsm import BotFSM
    from input.mock_driver import MockInputDriver
    from input.base_driver import BaseInputDriver
except ImportError as e:
    logger.warning(f"核心模块导入失败: {e}")
    logger.warning("将使用 Mock 模式")

try:
    from input.input_driver import InputDriver
    HAS_REAL_INPUT = True
except Exception:
    HAS_REAL_INPUT = False


class EngineThread(QThread):
    """
    核心引擎工作线程

    在独立线程中运行完整的游戏自动化引擎：
    - 屏幕捕获
    - 目标检测
    - 世界模型更新
    - 状态机决策
    - 输入执行

    通过 Qt 信号与主线程通信，保证 UI 响应流畅。
    """

    def __init__(self, config: dict = None):
        """
        初始化引擎线程

        Args:
            config: 配置字典，如果为 None 则使用默认配置
        """
        super().__init__()

        # 配置
        if config is None:
            config_loader = ConfigLoader.instance()
            config_loader.load("configs/config.yaml")
            self.config = config_loader.config
        else:
            self.config = config

        # 运行状态
        self._running = False
        self._paused = False
        self._should_stop = False

        # 性能统计
        self._frame_count = 0
        self._start_time = None
        self._last_fps_update = time.time()

        # 创建信号对象
        self.signals = EngineSignals()

        logger.info("EngineThread 初始化完成")

    def start(self):
        """启动引擎"""
        if not self._running:
            self._running = True
            self._paused = False
            self._should_stop = False
            self._start_time = time.time()
            logger.info("引擎线程启动")
            super().start()

    def stop(self):
        """停止引擎"""
        logger.info("停止引擎...")
        self._running = False
        self._should_stop = True
        self.wait(3000)  # 等待线程结束，最多 3 秒

    def pause(self):
        """暂停引擎"""
        if self._running and not self._paused:
            logger.info("暂停引擎...")
            self._paused = True

    def resume(self):
        """恢复引擎"""
        if self._running and self._paused:
            logger.info("恢复引擎...")
            self._paused = False

    def is_running(self) -> bool:
        """检查是否运行中"""
        return self._running and not self._paused

    def run(self):
        """
        主循环 - 在独立线程中执行

        完整的数据处理流程：
        1. 屏幕捕获
        2. 目标检测
        3. 世界模型更新
        4. 状态机决策
        5. 输入执行
        """
        logger.info("引擎线程开始运行")

        try:
            # 初始化核心引擎（按配置注入，缺失时回退默认值）
            capture_config = self._build_capture_config()
            config_use_mock = bool(capture_config.use_mock)
            capture_engine = create_capture_engine(
                config=capture_config,
                use_mock=config_use_mock,
                backend=capture_config.backend,
            )
            capture_engine.start()  # 启动捕获引擎
            logger.info(
                "UI 线程捕获引擎启动: "
                f"requested_backend={capture_config.backend}, "
                f"active_backend={getattr(capture_engine, 'active_backend', 'unknown')}"
            )
            detector = self._create_detector()
            world_model = WorldModel(room_clear_timeout=2.0, history_length=30)
            fsm = BotFSM()
            input_driver = self._create_input_driver()

            logger.info("所有核心模块初始化完成")

            # 保存到实例变量以便其他方法访问
            self._fsm = fsm
            self._world_model = world_model

            # 启动信号
            self._running = True
            self._frame_count = 0

            # 获取配置
            target_fps = max(1, int(self._get_config_value("capture", "target_fps", 30)))
            frame_time = 1.0 / target_fps

            # 主循环
            while self._running and not self._should_stop:
                try:
                    loop_start = time.perf_counter()

                    # 暂停检查
                    if self._paused:
                        time.sleep(0.1)
                        continue

                    # ========== 1. 屏幕捕获 ==========
                    frame = capture_engine.get_frame()
                    if frame is None:
                        logger.warning("获取帧失败，等待 100ms")
                        time.sleep(0.1)
                        continue

                    # ========== 2. 目标检测 ==========
                    detections = detector.detect(frame)

                    # ========== 3. 世界模型更新 ==========
                    context = world_model.update(detections)

                    # ========== 4. 状态机决策 ==========
                    command = fsm.update(context)

                    # ========== 5. 输入执行 ==========
                    input_driver.execute(command)

                    # ========== 6. 发送信号 ==========
                    self.signals.frame_ready.emit(frame)

                    # FPS 控制
                    current_time = time.time()
                    if current_time - self._last_fps_update >= 0.2:  # 每 200ms 更新一次 FPS
                        fps = self._frame_count / (current_time - self._start_time + 0.001)
                        status = self._collect_status(context, fps)
                        self.signals.status_update.emit(status)
                        self._last_fps_update = current_time

                    # 帧计数
                    self._frame_count += 1

                    # 帧率控制
                    elapsed = time.perf_counter() - loop_start
                    if elapsed < frame_time:
                        time.sleep(frame_time - elapsed)

                except Exception as e:
                    logger.error(f"主循环异常: {e}")
                    self.signals.error_occurred.emit(str(e))
                    break

        except Exception as e:
            logger.error(f"引擎线程初始化失败: {e}")
            self.signals.error_occurred.emit(f"引擎初始化错误: {e}")

        finally:
            # 清理资源
            if 'capture_engine' in locals():
                capture_engine.stop()
            logger.info(f"引擎线程结束，共处理 {self._frame_count} 帧")
            self._running = False

    def _get_config_value(self, section: str, key: str, default: Any) -> Any:
        """
        读取配置值，兼容 AppConfig 与 dict 两种格式。
        """
        if isinstance(self.config, dict):
            return self.config.get(section, {}).get(key, default)

        section_obj = getattr(self.config, section, None)
        if section_obj is None:
            return default
        return getattr(section_obj, key, default)

    def _build_capture_config(self) -> CaptureConfig:
        """
        构建统一 CaptureConfig，避免 dict/AppConfig 分支在多处散落。
        """
        if isinstance(self.config, dict):
            capture = self.config.get("capture", {})
            return CaptureConfig(
                window_title=capture.get("window_title", "地下城与勇士"),
                window_class=capture.get("window_class", "D3D Window"),
                target_fps=int(capture.get("target_fps", 30)),
                width=int(capture.get("width", 1920)),
                height=int(capture.get("height", 1080)),
                monitor_index=int(capture.get("monitor_index", 1)),
                use_mock=bool(capture.get("use_mock", False)),
                backend=str(capture.get("backend", "auto")),
                wgc_show_cursor=bool(capture.get("wgc_show_cursor", False)),
                wgc_force_borderless=bool(capture.get("wgc_force_borderless", False)),
            )

        return self.config.capture

    def _create_detector(self):
        """
        根据配置创建检测器。
        """
        detector_type = str(self._get_config_value("detector", "type", "mock")).lower()
        if detector_type != "mock":
            logger.warning(
                f"UI 线程暂未接入 '{detector_type}' 检测器实现，回退到 Mock 检测器"
            )
        return MockYoloDetector(mock_mode="random")

    def _create_input_driver(self) -> "BaseInputDriver":
        """
        根据配置创建输入驱动，不可用时回退 Mock。
        """
        input_type = str(self._get_config_value("input", "type", "mock")).lower()
        if input_type != "real":
            return MockInputDriver()

        if not HAS_REAL_INPUT:
            logger.warning("UI 线程真实输入驱动依赖不可用，回退到 Mock 输入驱动")
            return MockInputDriver()

        input_section = self.config.get("input", {}) if isinstance(self.config, dict) else self.config.input
        capture_section = self.config.get("capture", {}) if isinstance(self.config, dict) else self.config.capture

        key_bindings = {}
        if isinstance(self.config, dict):
            key_bindings = input_section.get("key_bindings", {})
            check_focus = input_section.get("window", {}).get("check_focus", True)
            auto_activate = input_section.get("window", {}).get("auto_activate", False)
            randomization = input_section.get("randomization", True)
            delay_min = max(float(input_section.get("delay_min", 0.05)), 0.01)
            delay_max = max(float(input_section.get("delay_max", delay_min)), delay_min)
            window_title = capture_section.get("window_title", "地下城与勇士")
        else:
            key_bindings = dict(getattr(input_section.key_bindings, "__dict__", {}))
            check_focus = input_section.check_focus
            auto_activate = input_section.auto_activate
            randomization = input_section.randomization
            delay_min = max(float(input_section.delay_min), 0.01)
            delay_max = max(float(input_section.delay_max), delay_min)
            window_title = capture_section.window_title

        return InputDriver(
            enable_jitter=randomization,
            jitter_mean=delay_min,
            jitter_std=max((delay_max - delay_min) / 2.0, 0.0),
            key_bindings=key_bindings,
            window_title=window_title,
            check_focus=check_focus,
            auto_activate=auto_activate,
        )

    def _collect_status(self, context, fps: float) -> dict:
        """
        收集当前状态信息

        Args:
            context: 游戏上下文
            fps: 当前帧率

        Returns:
            包含所有状态信息的字典
        """
        hero = context.hero
        monsters = context.monsters
        items = context.items
        doors = context.doors

        return {
            "fps": fps,
            "frame_count": self._frame_count,
            "run_time": time.time() - self._start_time if self._start_time else 0,
            "state": self._fsm.current_state.name if hasattr(self._fsm, "current_state") else "UNKNOWN",
            "hero_detected": hero is not None,
            "monster_count": len(monsters),
            "item_count": len(items),
            "door_count": len(doors),
            "room_cleared": context.room_cleared,
            "paused": self._paused
        }


# 工厂函数
def create_engine_thread(config: dict = None) -> EngineThread:
    """
    创建引擎线程实例

    Args:
        config: 配置字典，如果为 None 则使用默认配置

    Returns:
        EngineThread 实例
    """
    return EngineThread(config)

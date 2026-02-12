"""
引擎线程模块

将核心引擎包装为 Qt 工作线程，实现后台数据处理。

Author: haneball17
Date: 2026-02-11
"""

import time
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt

from core.logger import logger
from core.config import ConfigLoader

# 导入核心模块
try:
    from core.capture import create_capture_engine
    from vision.mock_detector import MockYoloDetector
    from logic.world_model import WorldModel
    from logic.bot_fsm import BotFSM
    from input.mock_driver import MockInputDriver
except ImportError as e:
    logger.warning(f"核心模块导入失败: {e}")
    logger.warning("将使用 Mock 模式")


class EngineSignals(QObject):
    """
    引擎信号定义

    定义引擎与 UI 之间的通信信号。
    """

    # 每秒 30 帧的帧数据信号（用于视频预览）
    frame_ready = pyqtSignal(object)

    # 每秒 5 次的状态更新信号（用于状态面板）
    status_update = pyqtSignal(dict)

    # 日志消息信号（用于日志面板）
    log_message = pyqtSignal(str, str)

    # 错误发生信号
    error_occurred = pyqtSignal(str)


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
            config_loader = ConfigLoader()
            self.config = config_loader.get_config()
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
            # 初始化核心引擎
            capture_engine = create_capture_engine(use_mock=True)
            capture_engine.start()  # 启动捕获引擎
            detector = MockYoloDetector(mock_mode="random")
            world_model = WorldModel(room_clear_timeout=2.0, history_length=30)
            fsm = BotFSM()
            input_driver = MockInputDriver()

            logger.info("所有核心模块初始化完成")

            # 保存到实例变量以便其他方法访问
            self._fsm = fsm
            self._world_model = world_model

            # 启动信号
            self._running = True
            self._frame_count = 0

            # 获取配置
            # 支持 AppConfig 对象或字典
            if hasattr(self.config, 'capture'):
                target_fps = self.config.capture.target_fps
            else:
                target_fps = self.config.get("capture", {}).get("target_fps", 30)
            frame_time = 1.0 / target_fps

            # 主循环
            while self._running and not self._should_stop:
                try:
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
                    elapsed = time.time() - self._loop_start_time(self._frame_count, frame_time)
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

    def _loop_start_time(self, frame_count: int, frame_time: float) -> float:
        """计算循环开始时间（用于 FPS 计算）"""
        return time.time() - (frame_time * (frame_count - 1))

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

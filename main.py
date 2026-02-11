"""
AradVision 主入口

DNF 视觉辅助自动化系统 - 基于计算机视觉的游戏辅助工具。

Author: haneball17, yangmq17
Date: Day 1
Version: 0.1.2
"""

import sys
import time
import signal
import threading
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.logger import logger, setup_logger
from core.config import ConfigLoader, get_config
from core.capture import CaptureEngine, create_capture_engine
from core.exceptions import EmergencyStopException, AradVisionError


class AradVisionApp:
    """
    AradVision 应用主类

    负责系统初始化、主循环、优雅退出等功能。

    Examples:
        >>> app = AradVisionApp()
        >>> app.run()
    """

    def __init__(self, config_path: str = "configs/config.yaml"):
        """
        初始化应用

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.is_running = False
        self._capture_engine: Optional[CaptureEngine] = None
        self._kill_switch_thread: Optional[threading.Thread] = None

        # 初始化日志
        setup_logger(log_level="INFO")
        logger.info("AradVision 初始化中...")

        # 加载配置
        self.config_loader = ConfigLoader.instance()
        try:
            self.config_loader.load(config_path)
            logger.info(f"配置加载成功: {config_path}")
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize(self) -> None:
        """初始化所有模块"""
        logger.info("初始化系统模块...")

        try:
            # 初始化截图引擎
            self._capture_engine = create_capture_engine()
            self._capture_engine.start()
            logger.info("截图引擎启动成功")

            # TODO: 初始化其他模块
            # - 检测器（MockYoloDetector / YoloDetector）
            # - 输入驱动（MockInputDriver / InputDriver）
            # - 状态机（BotFSM）
            # - 路径规划（PathPlanner）

            logger.info("所有模块初始化完成")

        except Exception as e:
            logger.error(f"模块初始化失败: {e}")
            self.shutdown()
            raise

    def run(self) -> None:
        """
        运行主循环

        这是应用的核心循环，负责：
        1. 截取游戏画面
        2. 检测游戏对象
        3. 更新游戏上下文
        4. 执行决策逻辑
        5. 发送输入指令
        """
        if self.is_running:
            logger.warning("应用已在运行中")
            return

        logger.info("启动 AradVision...")

        try:
            # 初始化模块
            self.initialize()

            # 启动紧急停止监控
            self._start_kill_switch_monitor()

            # 进入主循环
            self.is_running = True
            self._main_loop()

        except EmergencyStopException:
            logger.warning("收到紧急停止信号 (F12)")
        except KeyboardInterrupt:
            logger.info("收到键盘中断 (Ctrl+C)")
        except Exception as e:
            logger.error(f"主循环异常: {e}", exc_info=True)
        finally:
            self.shutdown()

    def _main_loop(self) -> None:
        """
        主循环逻辑

        单帧处理流程：
        1. 截取游戏画面
        2. 检测游戏对象
        3. 更新游戏上下文
        4. 执行决策逻辑
        5. 发送输入指令
        """
        frame_count = 0
        loop_start_time = time.perf_counter()

        logger.info("进入主循环...")

        while self.is_running:
            try:
                frame_start = time.perf_counter()

                # 1. 截取游戏画面
                frame = self._capture_engine.get_frame()
                if frame is None:
                    logger.warning("获取帧失败，跳过本帧")
                    continue

                # TODO: 2. 检测游戏对象
                # objects = detector.detect(frame)

                # TODO: 3. 更新游戏上下文
                # context = world_model.update(objects)

                # TODO: 4. 执行决策逻辑
                # command = fsm.update(context)

                # TODO: 5. 发送输入指令
                # input_driver.execute(command)

                # 性能监控
                frame_count += 1
                frame_time = time.perf_counter() - frame_start

                # 每 100 帧输出一次统计信息
                if frame_count % 100 == 0:
                    elapsed = time.perf_counter() - loop_start_time
                    fps = frame_count / elapsed
                    stats = self._capture_engine.get_stats()
                    logger.info(
                        f"FPS: {fps:.1f} | "
                        f"FrameTime: {frame_time*1000:.1f}ms | "
                        f"CaptureLatency: {stats.avg_latency:.1f}ms | "
                        f"Frames: {frame_count}"
                    )

            except EmergencyStopException:
                raise
            except Exception as e:
                logger.error(f"主循环错误: {e}", exc_info=True)
                # 继续运行，不因单帧错误而退出

    def _start_kill_switch_monitor(self) -> None:
        """
        启动紧急停止监控线程（F12）

        这是一个后台线程，持续监控 F12 按键，
        一旦检测到立即触发 EmergencyStopException。
        """
        def monitor():
            """紧急停止监控函数"""
            try:
                import keyboard

                while self.is_running:
                    if keyboard.is_pressed(self.config_loader.config.system.kill_switch_key):
                        logger.warning("检测到紧急停止按键 (F12)")
                        self.is_running = False
                        raise EmergencyStopException("F12 紧急停止")
                    time.sleep(0.05)  # 20Hz 检查频率

            except ImportError:
                logger.warning("keyboard 模块未安装，紧急停止功能不可用")
            except EmergencyStopException:
                raise
            except Exception as e:
                logger.error(f"紧急停止监控异常: {e}")

        self._kill_switch_thread = threading.Thread(
            target=monitor,
            daemon=True,
            name="KillSwitchMonitor"
        )
        self._kill_switch_thread.start()
        logger.info("紧急停止监控已启动")

    def shutdown(self) -> None:
        """优雅关闭应用"""
        if not self.is_running:
            return

        logger.info("正在关闭 AradVision...")
        self.is_running = False

        # 停止截图引擎
        if self._capture_engine:
            self._capture_engine.stop()
            stats = self._capture_engine.get_stats()
            logger.info(
                f"捕获统计: "
                f"frames={stats.frame_count}, "
                f"fps={stats.fps:.1f}, "
                f"avg_latency={stats.avg_latency:.1f}ms, "
                f"drops={stats.drop_count}"
            )

        # TODO: 停止其他模块
        # - 检测器
        # - 输入驱动
        # - 状态机

        logger.info("AradVision 已关闭")

    def _signal_handler(self, signum, frame):
        """系统信号处理器"""
        logger.info(f"收到信号 {signum}，准备退出...")
        self.is_running = False


def main():
    """主函数入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="AradVision - DNF 视觉辅助自动化系统"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="configs/config.yaml",
        help="配置文件路径（默认: configs/config.yaml）"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="AradVision 0.1.2"
    )

    args = parser.parse_args()

    # 创建并运行应用
    try:
        app = AradVisionApp(config_path=args.config)
        app.run()
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

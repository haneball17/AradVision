"""
AradVision 主入口

DNF 视觉辅助自动化系统 - 基于计算机视觉的游戏辅助工具。

Author: haneball17, yangmq17
Date: Day 1
Version: 0.1.3
"""

import sys
import time
import signal
import threading
from pathlib import Path
from typing import Optional, TYPE_CHECKING

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.logger import logger, setup_logger
from core.config import ConfigLoader, get_config
from core.capture import CaptureEngine, create_capture_engine
from core.exceptions import EmergencyStopException, AradVisionError

# 可选导入视觉模块（需要 numpy）
try:
    from vision.mock_detector import MockYoloDetector
    HAS_VISION = True
except ImportError:
    HAS_VISION = False

# 导入 UI 集成模块
try:
    from ui.integration import (
        HAS_PYQT,
        HAS_ENGINE_THREAD,
        HAS_WORLD_MODEL,
        create_ui_engine_thread,
        get_ui_update_handlers,
        connect_ui_signals,
        setup_ui_mode,
        is_ui_mode
    )
    HAS_PYQT = HAS_PYQT
    HAS_ENGINE_THREAD = HAS_ENGINE_THREAD
    HAS_WORLD_MODEL = HAS_WORLD_MODEL
except ImportError:
        logger.warning("UI 集成模块不可用：PyQt5 缺失或导入失败")
        HAS_PYQT = False
        HAS_ENGINE_THREAD = False
        HAS_WORLD_MODEL = False

# 导入决策层模块
from logic.world_model import WorldModel
from logic.bot_fsm import BotFSM, BotState
from logic.combat import CombatLogic
from logic.path_planner import PathPlanner

# 导入输入层模块
from input.mock_driver import MockInputDriver


class AradVisionApp:
    """
    AradVision 应用主类

    负责系统初始化、主循环、优雅退出等功能。

    数据流：
        CaptureEngine → MockYoloDetector → WorldModel → BotFSM → CombatLogic/PathPlanner → MockInputDriver

    Examples:
        >>> app = AradVisionApp()
        >>> app.run()
    """

    def __init__(
        self,
        config_path: str = "configs/config.yaml",
        use_mock: bool = True,
        use_ui: bool = False
    ):
        """
        初始化应用

        Args:
            config_path: 配置文件路径
            use_mock: 是否使用 Mock 模块（用于测试）
            use_ui: 是否启动 UI 控制面板
        """
        self.config_path = config_path
        self.use_mock = use_mock
        self.use_ui = use_ui
        self.is_running = False

        # UI 模式标志
        self._ui_mode = False

        # 模块实例
        self._capture_engine: Optional[CaptureEngine] = None
        self._kill_switch_thread: Optional[threading.Thread] = None
        self._detector: Optional[MockYoloDetector] = None
        self._world_model: Optional[WorldModel] = None
        self._fsm: Optional[BotFSM] = None
        self._combat_logic: Optional[CombatLogic] = None
        self._path_planner: Optional[PathPlanner] = None
        self._input_driver: Optional[MockInputDriver] = None

        # 引擎线程（仅 UI 模式）
        self._engine_thread: Optional["ui.threads.engine_thread.EngineThread"] = None
        self._ui_handlers: dict = {}

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
            # 1. 初始化截图引擎（根据 use_mock 参数选择）
            self._capture_engine = create_capture_engine(use_mock=self.use_mock)
            self._capture_engine.start()
            engine_type = "Mock" if self.use_mock else "真实"
            logger.info(f"✓ {engine_type} 截图引擎启动成功")

            # 2. 初始化检测器（使用 Mock 模块）
            if HAS_VISION:
                self._detector = MockYoloDetector(mock_mode="random")
                logger.info("✓ Mock 检测器初始化成功")
            else:
                raise RuntimeError("vision 模块不可用，无法初始化检测器")

            # 3. 初始化世界模型
            self._world_model = WorldModel(
                room_clear_timeout=2.0,
                history_length=30
            )
            logger.info("✓ 世界模型初始化成功")

            # 4. 初始化状态机
            self._fsm = BotFSM()
            logger.info("✓ 状态机初始化成功")

            # 5. 初始化战斗逻辑
            self._combat_logic = CombatLogic()
            logger.info("✓ 战斗逻辑初始化成功")

            # 6. 初始化路径规划
            self._path_planner = PathPlanner()
            logger.info("✓ 路径规划初始化成功")

            # 7. 初始化输入驱动（使用 Mock 模块）
            self._input_driver = MockInputDriver()
            logger.info("✓ Mock 输入驱动初始化成功")

            logger.info("=" * 60)
            logger.info("所有模块初始化完成")
            logger.info("=" * 60)

            # 初始化 UI 模式（如果启用）
            self._initialize_ui_mode()

        except Exception as e:
            logger.error(f"模块初始化失败: {e}", exc_info=True)
            self.shutdown()
            raise

    def _initialize_ui_mode(self) -> None:
        """初始化 UI 模式"""
        if not self.use_ui:
            return

        if not HAS_PYQT:
            logger.error("UI 模式请求但 PyQt5 不可用，回退到控制台模式")
            return

        logger.info("UI 模式启动，创建引擎线程...")

        try:
            # 导入 UI 集成模块
            from ui.integration import (
                create_ui_engine_thread,
                get_ui_update_handlers,
                connect_ui_signals,
                setup_ui_mode
            )

            # 获取配置字典
            config = self.config_loader.config

            # 获取 UI 更新处理器
            handlers = get_ui_update_handlers(config)
            self._ui_handlers = handlers

            # 创建引擎线程
            self._engine_thread = create_ui_engine_thread(config)
            if not self._engine_thread:
                raise RuntimeError("引擎线程创建失败")

            # 连接信号
            if not connect_ui_signals(self._engine_thread, config):
                raise RuntimeError("信号连接失败")

            # 设置 UI 模式到 WorldModel
            if not setup_ui_mode(self._world_model, config):
                raise RuntimeError("UI 模式设置失败")

            # 标记 UI 模式
            self._ui_mode = True
            logger.info("✓ UI 引擎线程初始化完成")

        except Exception as e:
            logger.error(f"UI 模式初始化失败: {e}", exc_info=True)
            # 继续以控制台模式运行
            self._ui_mode = False

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

            # UI 模式：启动引擎线程并等待
            if self._ui_mode:
                logger.info("UI 模式运行，EngineThread 处理主循环")

                # 启动引擎线程
                if self._engine_thread and not self._engine_thread.isRunning():
                    logger.info("启动引擎线程...")
                    self._engine_thread.start()

                # 等待引擎线程结束或用户停止
                while self.is_running:
                    if self._engine_thread and not self._engine_thread.isRunning():
                        logger.info("引擎线程已停止")
                        break
                    time.sleep(0.1)
            else:
                # 控制台模式：正常运行原有主循环
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

        logger.info("=" * 60)
        logger.info("进入主循环...")
        logger.info("=" * 60)

        while self.is_running:
            try:
                frame_start = time.perf_counter()

                # 1. 截取游戏画面
                frame = self._capture_engine.get_frame()
                if frame is None:
                    logger.warning("获取帧失败，跳过本帧")
                    time.sleep(0.01)
                    continue

                # 2. 检测游戏对象
                detections = self._detector.detect(frame)
                logger.debug(f"检测到 {len(detections)} 个对象")

                # 3. 更新游戏上下文
                context = self._world_model.update(detections, frame)
                logger.debug(
                    f"上下文: frame={context.frame_index}, "
                    f"monsters={len(context.monsters)}, "
                    f"state={self._fsm.current_state.name}"
                )

                # 4. 执行决策逻辑（状态机更新）
                command = self._fsm.update(context)

                # 5. 根据当前状态执行相应的决策逻辑
                if command is not None:
                    if command.action_type.name == "MOVE":
                        # 移动指令：使用路径规划
                        if context.hero and context.monsters:
                            # 规划到最近怪物的路径
                            move_cmd = self._path_planner.plan_to_nearest(
                                context.hero,
                                context.monsters
                            )
                            if move_cmd:
                                self._input_driver.execute(move_cmd)
                                logger.debug(
                                    f"移动: direction={move_cmd.direction}, "
                                    f"duration={move_cmd.duration:.2f}s"
                                )

                    elif command.action_type.name in ["ATTACK", "SKILL"]:
                        # 攻击/技能指令：使用战斗逻辑
                        if context.hero and context.monsters:
                            combat_cmd = self._combat_logic.decide_attack(
                                context.hero,
                                context.monsters
                            )
                            if combat_cmd:
                                self._input_driver.execute(combat_cmd)
                                logger.debug(
                                    f"攻击: action={combat_cmd.action_type.name}, "
                                    f"key={combat_cmd.key_code}"
                                )

                    elif command.action_type.name == "PICKUP":
                        # 拾取指令
                        self._input_driver.execute(command)
                        logger.debug("拾取物品")

                    elif command.action_type.name == "STOP":
                        # 停止指令
                        self._input_driver.execute(command)
                        logger.debug("停止所有输入")

                # 性能监控
                frame_count += 1
                frame_time = time.perf_counter() - frame_start

                # 控制帧率（目标 30 FPS）
                target_frame_time = 1.0 / 30.0
                if frame_time < target_frame_time:
                    time.sleep(target_frame_time - frame_time)

                # 每 100 帧输出一次统计信息
                if frame_count % 100 == 0:
                    elapsed = time.perf_counter() - loop_start_time
                    fps = frame_count / elapsed
                    stats = self._capture_engine.get_stats()
                    logger.info(
                        f"FPS: {fps:.1f} | "
                        f"FrameTime: {frame_time*1000:.1f}ms | "
                        f"CaptureLatency: {stats.avg_latency:.1f}ms | "
                        f"Frames: {frame_count} | "
                        f"State: {self._fsm.current_state.name}"
                    )

            except EmergencyStopException:
                raise
            except Exception as e:
                logger.error(f"主循环错误: {e}", exc_info=True)
                # 继续运行，不因单帧错误而退出
                time.sleep(0.1)

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
        logger.info("紧急停止监控已启动 (F12)")

    def shutdown(self) -> None:
        """优雅关闭应用"""
        if not self.is_running:
            return

        logger.info("正在关闭 AradVision...")
        self.is_running = False

        # 停止引擎线程（UI 模式）
        if self._ui_mode and self._engine_thread:
            if self._engine_thread.isRunning():
                logger.info("停止引擎线程...")
                self._engine_thread.stop()
                # 等待线程结束
                self._engine_thread.wait(timeout=3000)
                logger.info("✓ 引擎线程已停止")

        # 停止输入驱动
        if self._input_driver:
            self._input_driver.stop_all()
            logger.info("✓ 输入驱动已停止")

        # 停止截图引擎
        if self._capture_engine:
            self._capture_engine.stop()
            stats = self._capture_engine.get_stats()
            logger.info(
                f"✓ 截图引擎已停止 | "
                f"frames={stats.frame_count}, "
                f"fps={stats.fps:.1f}, "
                f"avg_latency={stats.avg_latency:.1f}ms, "
                f"drops={stats.drop_count}"
            )

        # 等待紧急停止线程结束
        if self._kill_switch_thread and self._kill_switch_thread.is_alive():
            self._kill_switch_thread.join(timeout=1.0)

        logger.info("=" * 60)
        logger.info("AradVision 已关闭")
        logger.info("=" * 60)

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
        version="AradVision 0.1.3"
    )
    parser.add_argument(
        "--no-mock",
        action="store_true",
        help="不使用 Mock 模块（使用真实模块，需要游戏环境）"
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="启动 UI 控制面板"
    )

    args = parser.parse_args()

    # 创建并运行应用
    try:
        app = AradVisionApp(
            config_path=args.config,
            use_mock=not args.no_mock,
            use_ui=args.ui
        )
        app.run()
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

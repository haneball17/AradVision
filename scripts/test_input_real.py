"""
输入驱动实战测试脚本

用于在真实游戏环境中验证输入驱动是否能够有效控制角色。

功能：
1. 测试方向键移动（上/下/左/右）
2. 测试攻击键
3. 测试技能键
4. 测试 F12 紧急停止

使用方法：
1. 启动游戏并进入修炼场
2. 确保角色可以自由移动
3. 运行此脚本：python scripts/test_input_real.py
4. 按照提示进行测试

Author: haneball17
Date: 2026-02-11
Priority: P0 - 真实环境验证
"""

import sys
import time
import random
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from input.input_driver import InputDriver
from input.kill_switch import KillSwitch
from core.types import Command, CommandType
from core.logger import logger


class InputTester:
    """输入驱动测试器"""

    def __init__(self):
        """初始化测试器"""
        logger.info("初始化输入驱动测试器...")

        # 创建输入驱动
        try:
            self.driver = InputDriver()
            logger.info("✓ 输入驱动创建成功")
        except Exception as e:
            logger.error(f"✗ 输入驱动创建失败: {e}")
            raise

        # 创建紧急停止监听
        try:
            self.kill_switch = KillSwitch(
                on_trigger=self._on_emergency_stop,
                kill_key="F12",
            )
            self.kill_switch.start()
            logger.info("✓ 紧急停止监听已启动（按 F12 停止）")
        except Exception as e:
            logger.warning(f"⚠️ 紧急停止启动失败: {e}")
            self.kill_switch = None

    def _on_emergency_stop(self) -> None:
        """紧急停止回调：释放所有按键并停止输入。"""
        logger.warning("检测到 F12，执行紧急停止")
        self.driver.stop_all()

    def cleanup(self):
        """清理资源"""
        logger.info("清理测试器资源...")
        if self.kill_switch:
            self.kill_switch.stop()
        logger.info("✓ 清理完成")

    def test_move(self, direction: str, duration: float = 0.5):
        """
        测试移动

        Args:
            direction: 方向 (up, down, left, right)
            duration: 持续时间（秒）
        """
        logger.info(f"测试移动: {direction}, 持续 {duration} 秒")

        # 生成方向向量
        direction_map = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }

        if direction not in direction_map:
            logger.error(f"无效方向: {direction}")
            return False

        dx, dy = direction_map[direction]

        # 创建移动指令
        command = Command(
            action_type=CommandType.MOVE,
            direction=(dx, dy),
            duration=duration
        )

        # 执行指令
        try:
            success = self.driver.execute(command)
            if success:
                logger.info(f"✓ 移动执行成功: {direction}")
            else:
                logger.error(f"✗ 移动执行失败: {direction}")
            return success
        except Exception as e:
            logger.error(f"✗ 移动执行异常: {e}")
            return False

    def test_attack(self, key_code: str = "x", count: int = 1):
        """
        测试攻击

        Args:
            key_code: 按键码 (默认 "x")
            count: 攻击次数
        """
        logger.info(f"测试攻击: {key_code}, {count} 次")

        for i in range(count):
            command = Command(
                action_type=CommandType.ATTACK,
                key_code=key_code,
                duration=0.1
            )

            try:
                success = self.driver.execute(command)
                if success:
                    logger.info(f"✓ 攻击 {i+1}/{count} 执行成功")
                else:
                    logger.error(f"✗ 攻击 {i+1}/{count} 执行失败")
                    return False
            except Exception as e:
                logger.error(f"✗ 攻击执行异常: {e}")
                return False

            # 攻击间隔
            if i < count - 1:
                time.sleep(0.3)

        logger.info("✓ 攻击测试完成")
        return True

    def test_skill(self, key_code: str = "a"):
        """
        测试技能

        Args:
            key_code: 技能键 (默认 "a")
        """
        logger.info(f"测试技能: {key_code}")

        command = Command(
            action_type=CommandType.SKILL,
            key_code=key_code,
            duration=0.1
        )

        try:
            success = self.driver.execute(command)
            if success:
                logger.info(f"✓ 技能释放成功: {key_code}")
            else:
                logger.error(f"✗ 技能释放失败: {key_code}")
            return success
        except Exception as e:
            logger.error(f"✗ 技能释放异常: {e}")
            return False

    def test_stop_all(self):
        """测试停止所有输入"""
        logger.info("测试停止所有输入")

        try:
            success = self.driver.stop_all()
            if success:
                logger.info("✓ 停止成功")
            else:
                logger.error("✗ 停止失败")
            return success
        except Exception as e:
            logger.error(f"✗ 停止异常: {e}")
            return False

    def test_random_movement(self, duration: int = 10):
        """
        测试随机移动

        Args:
            duration: 测试持续时间（秒）
        """
        logger.info(f"开始随机移动测试，持续 {duration} 秒")

        directions = ["up", "down", "left", "right"]
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                # 随机选择方向
                direction = random.choice(directions)
                move_duration = random.uniform(0.2, 0.5)

                # 执行移动
                self.test_move(direction, move_duration)

                # 随机间隔
                time.sleep(random.uniform(0.5, 1.0))

            logger.info("✓ 随机移动测试完成")
            return True
        except KeyboardInterrupt:
            logger.warning("用户中断测试")
            return False
        except Exception as e:
            logger.error(f"✗ 随机移动测试异常: {e}")
            return False

    def test_combat_sequence(self):
        """
        测试战斗序列（移动 + 攻击）
        """
        logger.info("开始战斗序列测试")

        try:
            # 测试四个方向移动
            for direction in ["right", "left", "up", "down"]:
                self.test_move(direction, 1.0)
                time.sleep(0.5)

            # 测试攻击
            self.test_attack("x", 5)
            time.sleep(0.5)

            # 测试技能
            self.test_skill("a")
            time.sleep(0.5)

            logger.info("✓ 战斗序列测试完成")
            return True
        except Exception as e:
            logger.error(f"✗ 战斗序列测试异常: {e}")
            return False

    def interactive_mode(self):
        """交互式测试模式"""
        logger.info("=" * 60)
        logger.info(" 输入驱动测试工具 - 交互模式")
        logger.info("=" * 60)
        logger.info("提示：")
        logger.info("  输入 'w' 向上移动 1 秒")
        logger.info("  输入 's' 向下移动 1 秒")
        logger.info("  输入 'a' 向左移动 1 秒")
        logger.info("  输入 'd' 向右移动 1 秒")
        logger.info("  输入 'x' 攻击 5 次")
        logger.info("  输入 'z' 释放技能 a")
        logger.info("  输入 'q' 停止所有输入")
        logger.info("  输入 'r' 随机移动 10 秒")
        logger.info("  输入 'c' 战斗序列测试")
        logger.info("  输入 'f5' 按 F5 键")
        logger.info("  输入 'exit' 退出")
        logger.info("  输入 'F12' 紧急停止")
        logger.info("=" * 60)

        logger.info("\n✓ 测试环境已准备就绪")
        logger.info("请确保游戏窗口处于激活状态\n")

        try:
            while True:
                try:
                    user_input = input("请输入命令 (输入 'help' 查看帮助): ").strip().lower()

                    if not user_input:
                        continue

                    if user_input in ["exit", "quit", "q"]:
                        logger.info("退出交互模式")
                        break

                    elif user_input == "help":
                        self._show_help()

                    elif user_input == "w":
                        self.test_move("up", 1.0)

                    elif user_input == "s":
                        self.test_move("down", 1.0)

                    elif user_input == "a":
                        self.test_move("left", 1.0)

                    elif user_input == "d":
                        self.test_move("right", 1.0)

                    elif user_input == "x":
                        self.test_attack("x", 5)

                    elif user_input == "z":
                        self.test_skill("a")

                    elif user_input == "q":
                        self.test_stop_all()

                    elif user_input == "r":
                        logger.info("开始随机移动测试（10秒），按 Ctrl+C 中断")
                        self.test_random_movement(10)

                    elif user_input == "c":
                        self.test_combat_sequence()

                    elif user_input == "f5":
                        # 测试 F5 键
                        logger.info("测试 F5 键")
                        command = Command(
                            action_type=CommandType.SKILL,
                            key_code="f5",
                            duration=0.1
                        )
                        self.driver.execute(command)

                    elif user_input == "f12":
                        logger.warning("请使用 F12 键进行紧急停止")

                    else:
                        logger.warning(f"未知命令: {user_input}，输入 'help' 查看帮助")

                except KeyboardInterrupt:
                    logger.info("\n检测到键盘中断")
                    break

                except Exception as e:
                    logger.error(f"处理命令时出错: {e}")

        finally:
            logger.info("交互模式结束")

    def _show_help(self):
        """显示帮助信息"""
        logger.info("=" * 60)
        logger.info(" 命令列表")
        logger.info("=" * 60)
        logger.info("移动测试:")
        logger.info("  w - 向上移动 1 秒")
        logger.info("  s - 向下移动 1 秒")
        logger.info("  a - 向左移动 1 秒")
        logger.info("  d - 向右移动 1 秒")
        logger.info("")
        logger.info("攻击测试:")
        logger.info("  x - 攻击 5 次")
        logger.info("  z - 释放技能 a")
        logger.info("  f5 - 按 F5 键")
        logger.info("")
        logger.info("停止控制:")
        logger.info("  q - 停止所有输入")
        logger.info("  F12 - 紧急停止（全局）")
        logger.info("")
        logger.info("自动化测试:")
        logger.info("  r - 随机移动 10 秒")
        logger.info("  c - 战斗序列测试")
        logger.info("")
        logger.info("其他:")
        logger.info("  help - 显示此帮助")
        logger.info("  exit/quit - 退出")
        logger.info("=" * 60)

    def automated_test(self):
        """
        自动化测试模式
        用于在修炼场中进行自动化测试
        """
        logger.info("=" * 60)
        logger.info(" 自动化测试模式")
        logger.info("=" * 60)
        logger.info("说明：")
        logger.info("  1. 确保游戏已进入修炼场")
        logger.info("  2. 确保角色面向正前方")
        logger.info("  3. 测试将在 5 秒后自动开始")
        logger.info("  4. 按 Ctrl+C 或 F12 可以随时停止")
        logger.info("=" * 60)

        # 倒计时
        logger.info("\n测试将在 5 秒后开始...")
        for i in range(5, 0, -1):
            logger.info(f"  {i} 秒...")
            time.sleep(1)

        logger.info("🚀 测试开始！\n")

        try:
            # 测试 1: 向右移动
            logger.info("测试 1/5: 向右移动 2 秒")
            self.test_move("right", 2.0)
            time.sleep(1)

            # 测试 2: 攻击
            logger.info("测试 2/5: 攻击 5 次")
            self.test_attack("x", 5)
            time.sleep(1)

            # 测试 3: 向左移动
            logger.info("测试 3/5: 向左移动 2 秒")
            self.test_move("left", 2.0)
            time.sleep(1)

            # 测试 4: 释放技能
            logger.info("测试 4/5: 释放技能 a")
            self.test_skill("a")
            time.sleep(1)

            # 测试 5: 向上移动
            logger.info("测试 5/5: 向上移动 2 秒")
            self.test_move("up", 2.0)
            time.sleep(1)

            logger.info("\n" + "=" * 60)
            logger.info(" ✅ 自动化测试完成！")
            logger.info("=" * 60)

        except KeyboardInterrupt:
            logger.warning("\n测试被用户中断")
        except Exception as e:
            logger.error(f"\n✗ 测试过程中出错: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="AradVision 输入驱动实战测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-m", "--mode",
        choices=["interactive", "auto", "test"],
        default="interactive",
        help="运行模式: interactive（交互式）, auto（自动化）, test（单项测试）"
    )

    parser.add_argument(
        "--test",
        choices=["move", "attack", "skill", "random", "combat"],
        help="单项测试类型"
    )

    parser.add_argument(
        "--direction",
        choices=["up", "down", "left", "right"],
        help="移动方向"
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=1.0,
        help="持续时间（秒）"
    )

    parser.add_argument(
        "--key",
        type=str,
        default="x",
        help="按键码"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="攻击次数"
    )

    args = parser.parse_args()

    # 创建测试器
    tester = InputTester()

    try:
        if args.mode == "interactive":
            # 交互式模式
            tester.interactive_mode()

        elif args.mode == "auto":
            # 自动化模式
            tester.automated_test()

        elif args.mode == "test":
            # 单项测试模式
            if args.test == "move":
                tester.test_move(args.direction, args.duration)
            elif args.test == "attack":
                tester.test_attack(args.key, args.count)
            elif args.test == "skill":
                tester.test_skill(args.key)
            elif args.test == "random":
                tester.test_random_movement(int(args.duration))
            elif args.test == "combat":
                tester.test_combat_sequence()
            else:
                logger.error(f"未知的测试类型: {args.test}")

    except KeyboardInterrupt:
        logger.info("\n用户中断测试")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # 清理资源
        tester.cleanup()


if __name__ == "__main__":
    main()

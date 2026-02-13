"""
游戏控制测试脚本

用于验证 InputDriver 是否能正确控制游戏。

使用方法：
1. 启动 DNF 并进入训练房
2. 运行此脚本：python scripts/test_input_game.py
3. 按照提示进行测试

Author: haneball17
Date: 2026-02-13
"""

import time
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.logger import logger
from input.input_driver import InputDriver


class GameInputTester:
    """游戏输入测试器"""

    def __init__(self):
        self.driver = InputDriver(enable_jitter=True)
        logger.info("InputDriver 初始化完成")

    def test_basic_keys(self):
        """测试基础按键"""
        print("\n=== 基础按键测试 ===")
        print("将依次测试以下按键，请在游戏中观察：")
        print("  1. 空格键 (普通攻击)")
        print("  2. X 键 (技能)")
        print("  3. 数字键 1-5 (技能栏)")
        print("  4. Esc 键 (取消/逃跑)")

        input("\n按回车开始测试...")

        # 测试空格
        print("\n[测试] 空格键 (普通攻击)")
        for i in range(3):
            self.driver.tap("space")
            time.sleep(0.5)

        time.sleep(1)

        # 测试 X 键
        print("[测试] X 键 (技能)")
        for i in range(3):
            self.driver.tap("x")
            time.sleep(0.5)

        time.sleep(1)

        # 测试数字键
        print("[测试] 数字键 1-5")
        for key in ["1", "2", "3", "4", "5"]:
            self.driver.tap(key)
            print(f"  按下 {key}")
            time.sleep(0.3)

        time.sleep(1)

        # 测试 Esc
        print("[测试] Esc 键")
        self.driver.tap("escape")

        print("\n✓ 基础按键测试完成")

    def test_direction_keys(self):
        """测试方向键"""
        print("\n=== 方向键测试 ===")
        print("将测试角色移动，请确保角色在开阔位置")

        input("\n按回车开始测试...")

        directions = [
            ("up", "向上"),
            ("down", "向下"),
            ("left", "向左"),
            ("right", "向右"),
        ]

        for key, desc in directions:
            print(f"\n[测试] {desc} ({key})")
            # 长按移动
            self.driver.hold(key, 0.5)
            time.sleep(0.2)

        print("\n✓ 方向键测试完成")

    def test_movement_sequence(self):
        """测试移动序列"""
        print("\n=== 移动序列测试 ===")
        print("角色将执行：上 -> 右 -> 下 -> 左 -> 原地旋转")

        input("\n按回车开始测试...")

        # 定义一个移动路径
        sequence = [
            ("up", 0.4, "向上"),
            ("right", 0.4, "向右"),
            ("down", 0.4, "向下"),
            ("left", 0.4, "向左"),
        ]

        for key, duration, desc in sequence:
            print(f"[移动] {desc} ({key})")
            self.driver.hold(key, duration)
            time.sleep(0.1)

        print("\n✓ 移动序列测试完成")

    def test_skill_combo(self):
        """测试技能连招"""
        print("\n=== 技能连招测试 ===")
        print("将测试：X -> 1 -> 2 -> 3 的技能序列")

        input("\n按回车开始测试...")

        skills = ["x", "1", "2", "3"]
        for skill in skills:
            print(f"[技能] 释放 {skill}")
            self.driver.tap(skill)
            time.sleep(0.8)  # 技能间模拟

        print("\n✓ 技能连招测试完成")

    def test_stop_all(self):
        """测试紧急停止"""
        print("\n=== 紧急停止测试 ===")
        print("将持续按住空格键，然后触发 stop_all")

        input("\n按回车开始测试...")

        print("[测试] 持续按住空格...")
        print("[提示] 观察游戏中角色是否持续攻击")
        print("[提示] 3秒后将自动停止")

        # 模拟持续攻击
        for i in range(10):
            self.driver.tap("space")
            time.sleep(0.2)

        # 紧急停止
        print("\n[紧急停止] 触发 stop_all()")
        self.driver.stop_all()

        print("\n✓ 紧急停止测试完成")

    def test_random_input(self):
        """测试随机输入"""
        print("\n=== 随机输入测试 ===")
        print("将随机执行按键和移动，持续 5 秒")

        input("\n按回车开始测试...")

        import random

        keys = ["space", "x", "1", "2", "3", "up", "down", "left", "right"]

        start_time = time.time()
        while time.time() - start_time < 5:
            key = random.choice(keys)
            self.driver.tap(key)
            time.sleep(random.uniform(0.1, 0.3))

        print("\n✓ 随机输入测试完成")

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("AradVision 游戏控制测试")
        print("=" * 50)

        try:
            self.test_basic_keys()

            cont = input("\n是否继续测试方向键? (y/N): ")
            if cont.lower() == 'y':
                self.test_direction_keys()

            cont = input("\n是否继续测试移动序列? (y/N): ")
            if cont.lower() == 'y':
                self.test_movement_sequence()

            cont = input("\n是否继续测试技能连招? (y/N): ")
            if cont.lower() == 'y':
                self.test_skill_combo()

            cont = input("\n是否继续测试紧急停止? (y/N): ")
            if cont.lower() == 'y':
                self.test_stop_all()

            cont = input("\n是否继续测试随机输入? (y/N): ")
            if cont.lower() == 'y':
                self.test_random_input()

            print("\n" + "=" * 50)
            print("所有测试完成!")
            print("=" * 50)

        except KeyboardInterrupt:
            print("\n\n[中断] 用户取消测试")
            self.driver.stop_all()
        except Exception as e:
            print(f"\n\n[错误] 测试失败: {e}")
            self.driver.stop_all()
            raise


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="AradVision 游戏控制测试")
    parser.add_argument(
        "--test",
        choices=["basic", "direction", "move", "skill", "stop", "random", "all"],
        default="all",
        help="指定要执行的测试"
    )
    parser.add_argument(
        "--no-jitter",
        action="store_true",
        help="禁用随机延迟"
    )

    args = parser.parse_args()

    tester = GameInputTester()

    if args.test == "basic":
        tester.test_basic_keys()
    elif args.test == "direction":
        tester.test_direction_keys()
    elif args.test == "move":
        tester.test_movement_sequence()
    elif args.test == "skill":
        tester.test_skill_combo()
    elif args.test == "stop":
        tester.test_stop_all()
    elif args.test == "random":
        tester.test_random_input()
    else:
        tester.run_all_tests()


if __name__ == "__main__":
    main()

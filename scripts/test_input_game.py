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

from core.logger import logger, setup_logger
from core.config import ConfigLoader
from input.input_driver import InputDriver


class GameInputTester:
    """游戏输入测试器"""

    def __init__(self, auto_mode: bool = False):
        """
        初始化测试器

        Args:
            auto_mode: 是否启用自动模式（跳过所有输入确认）
        """
        self.auto_mode = auto_mode

        # 设置日志级别为 DEBUG，以便查看详细的窗口焦点日志
        setup_logger("DEBUG")
        logger.info("=" * 60)
        logger.info("游戏输入测试器初始化")
        logger.info(f"运行模式: {'自动模式' if auto_mode else '交互模式'}")
        logger.info("=" * 60)

        # 加载配置文件
        config_loader = ConfigLoader()
        config = config_loader.load("configs/config.yaml")

        logger.info(f"配置文件加载成功:")
        logger.info(f"  capture.window_title = '{config.capture.window_title}'")
        logger.info(f"  input.check_focus = {config.input.check_focus}")
        logger.info(f"  input.auto_activate = {config.input.auto_activate}")

        # 提取输入配置
        input_config = config.input
        window_title = config.capture.window_title  # 使用 capture 配置中的窗口标题

        # 将 key_bindings 转换为字典格式
        key_bindings_dict = {
            'attack': input_config.key_bindings.attack,
            'skill': input_config.key_bindings.skill,
            'jump': input_config.key_bindings.jump,
            'pick_up': input_config.key_bindings.pick_up,
            'move_up': input_config.key_bindings.move_up,
            'move_down': input_config.key_bindings.move_down,
            'move_left': input_config.key_bindings.move_left,
            'move_right': input_config.key_bindings.move_right,
            'skill_1': input_config.key_bindings.skill_1,
            'skill_2': input_config.key_bindings.skill_2,
            'skill_3': input_config.key_bindings.skill_3,
            'skill_4': input_config.key_bindings.skill_4,
            'skill_5': input_config.key_bindings.skill_5,
            'skill_6': input_config.key_bindings.skill_6,
            'skill_7': input_config.key_bindings.skill_7,
            'skill_8': input_config.key_bindings.skill_8,
        }

        # 创建输入驱动（从配置文件加载）
        self.driver = InputDriver(
            enable_jitter=True,
            key_bindings=key_bindings_dict,
            window_title=window_title,
            check_focus=input_config.check_focus,
            auto_activate=input_config.auto_activate,
        )

        # 保存按键映射引用，供测试方法使用
        self.keys = input_config.key_bindings

        logger.info(f"InputDriver 初始化完成")
        logger.info(f"  窗口标题: {window_title}")
        logger.info(f"  检查焦点: {input_config.check_focus}")
        logger.info(f"  自动激活: {input_config.auto_activate}")
        logger.info(f"  按键映射:")
        logger.info(f"    攻击: {self.keys.attack}")
        logger.info(f"    技能: {self.keys.skill}")
        logger.info(f"    跳跃: {self.keys.jump}")
        logger.info(f"    上: {self.keys.move_up}")
        logger.info(f"    下: {self.keys.move_down}")
        logger.info(f"    左: {self.keys.move_left}")
        logger.info(f"    右: {self.keys.move_right}")

    def _wait_for_confirm(self, prompt: str = "\n按回车开始测试...") -> None:
        """
        等待用户确认（仅在交互模式下）

        Args:
            prompt: 提示信息
        """
        if self.auto_mode:
            logger.debug(f"[自动模式] 跳过确认: {prompt.strip()}")
            # 自动模式下稍微等待，让用户有时间观察
            time.sleep(0.5)
            return
        input(prompt)

    def test_basic_keys(self):
        """测试基础按键（使用配置文件中的按键映射）"""
        print("\n=== 基础按键测试 ===")
        print("将依次测试以下按键，请在游戏中观察：")
        print(f"  1. 攻击键 ({self.keys.attack})")
        print(f"  2. 技能键 ({self.keys.skill})")
        print(f"  3. 跳跃键 ({self.keys.jump})")
        print(f"  4. 技能栏 1-5 ({self.keys.skill_1} - {self.keys.skill_5})")
        print("  5. Esc 键 (取消/逃跑)")

        self._wait_for_confirm("\n按回车开始测试...")

        # 测试攻击键
        print(f"\n[测试] 攻击键 ({self.keys.attack})")
        for i in range(3):
            self.driver.tap(self.keys.attack)
            time.sleep(0.5)

        time.sleep(1)

        # 测试技能键
        print(f"[测试] 技能键 ({self.keys.skill})")
        for i in range(3):
            self.driver.tap(self.keys.skill)
            time.sleep(0.5)

        time.sleep(1)

        # 测试跳跃键
        print(f"[测试] 跳跃键 ({self.keys.jump})")
        self.driver.tap(self.keys.jump)

        time.sleep(1)

        # 测试技能栏数字键
        print(f"[测试] 技能栏数字键")
        for key_num in range(1, 6):
            key = getattr(self.keys, f'skill_{key_num}')
            self.driver.tap(key)
            print(f"  按下技能栏 {key_num} (按键: {key})")
            time.sleep(0.3)

        time.sleep(1)

        # 测试 Esc
        print("[测试] Esc 键")
        self.driver.tap("escape")

        print("\n✓ 基础按键测试完成")

    def test_direction_keys(self):
        """测试方向键（使用配置文件中的按键映射）"""
        print("\n=== 方向键测试 ===")
        print("将测试角色移动，请确保角色在开阔位置")
        print(f"当前方向键配置: 上={self.keys.move_up}, 下={self.keys.move_down}, 左={self.keys.move_left}, 右={self.keys.move_right}")

        self._wait_for_confirm("\n按回车开始测试...")

        directions = [
            (self.keys.move_up, "向上"),
            (self.keys.move_down, "向下"),
            (self.keys.move_left, "向左"),
            (self.keys.move_right, "向右"),
        ]

        for key, desc in directions:
            print(f"\n[测试] {desc} ({key})")
            # 长按移动
            self.driver.hold(key, 0.5)
            time.sleep(0.2)

        print("\n✓ 方向键测试完成")

    def test_movement_sequence(self):
        """测试移动序列（使用配置文件中的按键映射）"""
        print("\n=== 移动序列测试 ===")
        print("角色将执行：上 -> 右 -> 下 -> 左")
        print(f"当前方向键配置: 上={self.keys.move_up}, 右={self.keys.move_right}, 下={self.keys.move_down}, 左={self.keys.move_left}")

        self._wait_for_confirm("\n按回车开始测试...")

        # 定义一个移动路径（使用配置的按键）
        sequence = [
            (self.keys.move_up, 0.4, "向上"),
            (self.keys.move_right, 0.4, "向右"),
            (self.keys.move_down, 0.4, "向下"),
            (self.keys.move_left, 0.4, "向左"),
        ]

        for key, duration, desc in sequence:
            print(f"[移动] {desc} ({key})")
            self.driver.hold(key, duration)
            time.sleep(0.1)

        print("\n✓ 移动序列测试完成")

    def test_skill_combo(self):
        """测试技能连招（使用配置文件中的按键映射）"""
        print("\n=== 技能连招测试 ===")
        print(f"将测试：技能({self.keys.skill}) -> 技能栏1-3 的技能序列")

        self._wait_for_confirm("\n按回车开始测试...")

        skills = [
            (self.keys.skill, "通用技能"),
            (self.keys.skill_1, "技能栏1"),
            (self.keys.skill_2, "技能栏2"),
            (self.keys.skill_3, "技能栏3"),
        ]

        for skill_key, skill_desc in skills:
            print(f"[技能] 释放 {skill_desc} (按键: {skill_key})")
            self.driver.tap(skill_key)
            time.sleep(0.8)  # 技能间模拟

        print("\n✓ 技能连招测试完成")

    def test_stop_all(self):
        """测试紧急停止（使用配置文件中的按键映射）"""
        print("\n=== 紧急停止测试 ===")
        print(f"将持续按住攻击键({self.keys.attack})，然后触发 stop_all")

        self._wait_for_confirm("\n按回车开始测试...")

        print(f"[测试] 持续按住攻击键({self.keys.attack})...")
        print("[提示] 观察游戏中角色是否持续攻击")
        print("[提示] 3秒后将自动停止")

        # 模拟持续攻击
        for i in range(10):
            self.driver.tap(self.keys.attack)
            time.sleep(0.2)

        # 紧急停止
        print("\n[紧急停止] 触发 stop_all()")
        self.driver.stop_all()

        print("\n✓ 紧急停止测试完成")

    def test_random_input(self):
        """测试随机输入（使用配置文件中的按键映射）"""
        print("\n=== 随机输入测试 ===")
        print("将随机执行按键和移动，持续 5 秒")

        self._wait_for_confirm("\n按回车开始测试...")

        import random

        # 使用配置的按键构建随机测试列表
        keys = [
            self.keys.attack,
            self.keys.skill,
            self.keys.jump,
            self.keys.move_up,
            self.keys.move_down,
            self.keys.move_left,
            self.keys.move_right,
            self.keys.skill_1,
            self.keys.skill_2,
            self.keys.skill_3,
        ]

        print(f"[提示] 随机按键池: {keys}")

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
        if self.auto_mode:
            print("[自动模式] 将依次执行所有测试，无需手动确认")
        print("=" * 50)

        try:
            self.test_basic_keys()

            # 自动模式下直接运行所有测试，交互模式下需要确认
            if self.auto_mode:
                self.test_direction_keys()
                self.test_movement_sequence()
                self.test_skill_combo()
                self.test_stop_all()
                self.test_random_input()
            else:
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
    parser.add_argument(
        "--mode",
        choices=["interactive", "auto"],
        default="interactive",
        help="运行模式: interactive（交互式，需要确认）或 auto（自动模式，无需确认）"
    )

    args = parser.parse_args()

    # 根据参数决定是否启用自动模式
    auto_mode = (args.mode == "auto")
    tester = GameInputTester(auto_mode=auto_mode)

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

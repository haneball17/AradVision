"""
Mock输入驱动单元测试

Author: yangmq17
Date: Day 1 下午
"""

import pytest
from input.mock_driver import MockInputDriver
from core.types import Command, CommandType


class TestMockInputDriver:
    """MockInputDriver测试"""

    @pytest.fixture
    def driver(self):
        """Mock输入驱动"""
        return MockInputDriver()

    def test_driver_initialization(self, driver):
        """测试初始化"""
        assert driver.is_running
        assert len(driver.get_history()) == 0

    def test_tap_records_command(self, driver):
        """测试tap记录指令"""
        driver.tap("x")

        history = driver.get_history()
        assert len(history) == 1
        assert history[0].key_code == "x"

    def test_hold_records_command(self, driver):
        """测试hold记录指令"""
        driver.hold("RIGHT", 0.5)

        history = driver.get_history()
        assert len(history) == 1
        assert history[0].key_code == "RIGHT"
        assert history[0].duration > 0  # 有随机抖动

    def test_execute_command(self, driver):
        """测试执行指令"""
        cmd = Command(
            action_type=CommandType.MOVE,
            direction=(1, 0)
        )

        result = driver.execute(cmd)
        assert result is True
        assert len(driver.get_history()) == 1

    def test_clear_history(self, driver):
        """测试清空历史"""
        driver.tap("x")
        driver.tap("a")
        assert len(driver.get_history()) == 2

        driver.clear_history()
        assert len(driver.get_history()) == 0

    def test_get_command_count(self, driver):
        """测试统计指令数量"""
        driver.tap("x")  # ATTACK
        driver.tap("a")  # ATTACK
        # hold -> MOVE

        assert driver.get_command_count() == 3
        assert driver.get_command_count(CommandType.ATTACK) == 2

    def test_stop_all(self, driver):
        """测试停止所有输入"""
        driver.stop_all()
        assert not driver.is_running

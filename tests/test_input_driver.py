"""
InputDriver 单元测试
"""

import pytest

from core.exceptions import InputError
from core.types import Command, CommandType
from input.input_driver import InputDriver, InvalidKeyError


class FakeBackend:
    """测试后端：只记录按键事件，不触发真实系统输入。"""

    def __init__(self):
        self.events = []

    def key_down(self, key: str) -> None:
        self.events.append(("down", key))

    def key_up(self, key: str) -> None:
        self.events.append(("up", key))


@pytest.fixture
def fake_backend():
    return FakeBackend()


@pytest.fixture
def driver(fake_backend):
    # 关闭抖动，避免测试时序不稳定
    return InputDriver(enable_jitter=False, jitter_mean=0.01, backend=fake_backend)


def test_tap_should_press_and_release(driver, fake_backend):
    """tap 应执行一次按下和弹起。"""
    ok = driver.tap("x")
    assert ok is True
    assert fake_backend.events == [("down", "x"), ("up", "x")]


def test_hold_should_press_and_release(driver, fake_backend):
    """hold 应执行一次按下和弹起。"""
    ok = driver.hold("RIGHT", 0.01)
    assert ok is True
    assert fake_backend.events == [("down", "right"), ("up", "right")]


def test_execute_move_by_direction(driver, fake_backend):
    """MOVE 指令可通过 direction 转换为方向键。"""
    cmd = Command(action_type=CommandType.MOVE, direction=(1, 0), duration=0.01)
    ok = driver.execute(cmd)
    assert ok is True
    assert fake_backend.events == [("down", "right"), ("up", "right")]


def test_execute_attack_requires_key_code(driver):
    """攻击类指令缺少 key_code 应报错。"""
    cmd = Command(action_type=CommandType.ATTACK)
    with pytest.raises(InputError):
        driver.execute(cmd)


def test_invalid_key_should_raise(driver):
    """非法按键应抛出 InvalidKeyError。"""
    with pytest.raises(InvalidKeyError):
        driver.tap("INVALID_KEY")


def test_stop_all_should_block_future_execute(driver, fake_backend):
    """stop_all 后 execute 不再发送输入。"""
    assert driver.stop_all() is True
    cmd = Command(action_type=CommandType.ATTACK, key_code="x")
    ok = driver.execute(cmd)
    assert ok is False
    assert fake_backend.events == []


def test_execute_stop_command_should_call_stop_all(driver):
    """STOP 指令应触发 stop_all。"""
    cmd = Command(action_type=CommandType.STOP)
    assert driver.execute(cmd) is True
    assert driver.is_running is False

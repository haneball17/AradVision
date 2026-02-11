"""
KillSwitch 单元测试
"""

import time

from input.kill_switch import KillSwitch


def test_kill_switch_should_trigger_callback_once():
    """检测器返回 True 后应触发一次回调。"""
    calls = []
    state = {"count": 0}

    def checker(_key: str) -> bool:
        state["count"] += 1
        return state["count"] >= 3

    def on_trigger() -> None:
        calls.append("triggered")

    ks = KillSwitch(
        on_trigger=on_trigger,
        kill_key="F12",
        poll_interval=0.001,
        key_checker=checker,
    )
    ks.start()

    deadline = time.time() + 0.2
    while time.time() < deadline and not ks.triggered:
        time.sleep(0.005)

    assert ks.triggered is True
    assert calls == ["triggered"]


def test_kill_switch_stop_should_exit_listener_without_trigger():
    """主动 stop 后不应触发回调。"""
    calls = []

    def checker(_key: str) -> bool:
        return False

    def on_trigger() -> None:
        calls.append("triggered")

    ks = KillSwitch(
        on_trigger=on_trigger,
        poll_interval=0.01,
        key_checker=checker,
    )
    ks.start()
    time.sleep(0.03)
    ks.stop()

    assert ks.is_running is False
    assert ks.triggered is False
    assert calls == []


def test_kill_switch_checker_exception_should_be_recorded_then_continue():
    """按键检测异常应被记录，监听线程继续工作。"""
    calls = []
    state = {"count": 0}

    def checker(_key: str) -> bool:
        state["count"] += 1
        if state["count"] == 1:
            raise RuntimeError("checker failed once")
        return state["count"] >= 2

    def on_trigger() -> None:
        calls.append("triggered")

    ks = KillSwitch(
        on_trigger=on_trigger,
        poll_interval=0.001,
        key_checker=checker,
    )
    ks.start()

    deadline = time.time() + 0.2
    while time.time() < deadline and not ks.triggered:
        time.sleep(0.005)

    assert isinstance(ks.last_error, RuntimeError)
    assert ks.triggered is True
    assert calls == ["triggered"]

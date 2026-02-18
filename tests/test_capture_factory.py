"""CaptureEngine 工厂与降级策略测试。"""

import numpy as np
import pytest

import core.capture as capture_module
from core.capture import BaseCaptureBackend, CaptureEngine, create_capture_engine
from core.config import CaptureConfig
from core.exceptions import CaptureError


class _FailWGCBackend(BaseCaptureBackend):
    """用于测试的失败 WGC 后端。"""

    backend_name = "wgc"

    def start(self) -> None:
        raise CaptureError("mock wgc startup failure")

    def stop(self) -> None:
        self.is_running = False

    def get_frame(self) -> np.ndarray:
        raise CaptureError("no frame")


class _OkMSSBackend(BaseCaptureBackend):
    """用于测试的成功 MSS 后端。"""

    backend_name = "mss"

    def start(self) -> None:
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def get_frame(self) -> np.ndarray:
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        self._update_stats(latency_ms=1.0, frame_size=int(frame.size))
        return frame


def test_create_capture_engine_should_return_mock_when_use_mock_true():
    """显式 use_mock=True 时应返回 MockCaptureEngine。"""
    cfg = CaptureConfig(use_mock=True)
    engine = create_capture_engine(config=cfg, use_mock=True)
    assert engine.__class__.__name__ == "MockCaptureEngine"


def test_capture_engine_auto_should_fallback_to_mss(monkeypatch):
    """Windows + auto 场景下，WGC 失败应降级到 MSS。"""
    cfg = CaptureConfig(backend="auto", use_mock=False)

    monkeypatch.setattr(capture_module, "WGCCaptureBackend", _FailWGCBackend)
    monkeypatch.setattr(capture_module, "MSSCaptureBackend", _OkMSSBackend)
    monkeypatch.setattr(capture_module.platform, "system", lambda: "Windows")

    engine = create_capture_engine(config=cfg, use_mock=False)
    assert isinstance(engine, CaptureEngine)

    engine.start()
    assert engine.active_backend == "mss"

    frame = engine.get_frame()
    assert frame.shape == (10, 10, 3)
    engine.stop()


def test_capture_engine_wgc_without_fallback_should_raise(monkeypatch):
    """强制 wgc 且禁止降级时，失败应直接抛异常。"""
    cfg = CaptureConfig(backend="wgc", use_mock=False)

    monkeypatch.setattr(capture_module, "WGCCaptureBackend", _FailWGCBackend)

    engine = CaptureEngine(config=cfg, backend="wgc", allow_fallback=False)
    with pytest.raises(CaptureError):
        engine.start()

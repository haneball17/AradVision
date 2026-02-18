"""Capture backend 配置解析测试。"""

from pathlib import Path

import pytest
import yaml

from core.config import ConfigLoader
from core.exceptions import ConfigurationError


def _write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def test_capture_backend_should_parse_wgc_options(tmp_path):
    """应正确解析 capture.backend 与 WGC 选项。"""
    config_path = tmp_path / "config.yaml"
    _write_yaml(
        config_path,
        {
            "capture": {
                "backend": "wgc",
                "use_mock": False,
                "wgc_show_cursor": True,
                "wgc_force_borderless": True,
            }
        },
    )

    loader = ConfigLoader.instance()
    cfg = loader.load(str(config_path))

    assert cfg.capture.backend == "wgc"
    assert cfg.capture.use_mock is False
    assert cfg.capture.wgc_show_cursor is True
    assert cfg.capture.wgc_force_borderless is True


def test_capture_backend_should_default_to_auto(tmp_path):
    """未配置 backend 时应回落为 auto。"""
    config_path = tmp_path / "config.yaml"
    _write_yaml(config_path, {"capture": {"use_mock": False}})

    loader = ConfigLoader.instance()
    cfg = loader.load(str(config_path))

    assert cfg.capture.backend == "auto"


def test_capture_backend_should_reject_invalid_value(tmp_path):
    """非法 backend 值应触发配置异常。"""
    config_path = tmp_path / "config.yaml"
    _write_yaml(config_path, {"capture": {"backend": "invalid_backend"}})

    loader = ConfigLoader.instance()
    with pytest.raises(ConfigurationError):
        loader.load(str(config_path))

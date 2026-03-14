"""固定路线副本配置解析测试。"""

from pathlib import Path

import pytest
import yaml

from core.config import ConfigLoader
from core.exceptions import ConfigurationError


def _write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def test_dungeon_run_should_parse_nested_runtime_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    _write_yaml(
        config_path,
        {
            "dungeon_run": {
                "enabled": True,
                "dungeon_id": "jmzjz",
                "start_room_index": 3,
                "main_view": {
                    "transition_roi": [1, 2, 3, 4],
                    "stable_frames": 5,
                },
                "minimap": {
                    "outer": [5, 6, 7, 8],
                    "stable_frames": 9,
                },
                "ui_rois": {
                    "hp_bar": [9, 10, 11, 12],
                },
                "guard_thresholds": {
                    "hp_critical_threshold": 0.2,
                    "potion_cooldown_ms": 900,
                },
                "class_profile": {
                    "requires_mp": True,
                    "primary_combat_skill": 4,
                },
                "maintenance": {
                    "sell_dry_run": True,
                    "max_weight_ratio": 0.7,
                },
                "room_scripts": [
                    {
                        "room_idx": 3,
                        "room_type": "normal",
                        "expected_exit_direction": "RIGHT",
                        "exit_action_template": "move_right_hold_1200",
                        "door_confirmation_roi": [13, 14, 15, 16],
                        "transition_timeout_ms": 1500,
                        "is_last_normal_room": True,
                        "route_policy_tag": "fixed_full_clear",
                        "room_feature_tag": "normal",
                        "next_step": "enter_boss",
                    }
                ],
            }
        },
    )

    loader = ConfigLoader.instance()
    cfg = loader.load(str(config_path))

    assert cfg.dungeon_run.enabled is True
    assert cfg.dungeon_run.start_room_index == 3
    assert cfg.dungeon_run.main_view.transition_roi.to_tuple() == (1, 2, 3, 4)
    assert cfg.dungeon_run.main_view.stable_frames == 5
    assert cfg.dungeon_run.minimap.outer.to_tuple() == (5, 6, 7, 8)
    assert cfg.dungeon_run.minimap.stable_frames == 9
    assert cfg.dungeon_run.ui_rois.hp_bar.to_tuple() == (9, 10, 11, 12)
    assert cfg.dungeon_run.guard_thresholds.hp_critical_threshold == 0.2
    assert cfg.dungeon_run.guard_thresholds.potion_cooldown_ms == 900
    assert cfg.dungeon_run.class_profile.requires_mp is True
    assert cfg.dungeon_run.class_profile.primary_combat_skill == 4
    assert cfg.dungeon_run.maintenance.max_weight_ratio == 0.7
    assert len(cfg.dungeon_run.room_scripts) == 1
    assert cfg.dungeon_run.room_scripts[0].door_confirmation_roi.to_tuple() == (13, 14, 15, 16)


def test_dungeon_run_should_reject_roi_outside_capture_bounds(tmp_path):
    config_path = tmp_path / "config.yaml"
    _write_yaml(
        config_path,
        {
            "capture": {
                "width": 100,
                "height": 100,
            },
            "dungeon_run": {
                "main_view": {
                    "transition_roi": [90, 10, 20, 10],
                    "clear_roi": [10, 10, 10, 10],
                    "boss_roi": [10, 30, 10, 10],
                    "finish_roi": [10, 50, 10, 10],
                },
                "minimap": {
                    "outer": [10, 10, 10, 10],
                    "inner": [20, 20, 10, 10],
                    "neighbor_roi": [30, 30, 10, 10],
                    "special_roi": [40, 40, 10, 10],
                },
                "ui_rois": {
                    "hp_bar": [10, 60, 10, 10],
                    "mp_bar": [30, 60, 10, 10],
                    "inventory_weight_bar": [50, 60, 10, 10],
                    "vendor_flag": [60, 10, 10, 10],
                    "potion_flag": [70, 10, 10, 10],
                },
                "room_scripts": [
                    {
                        "room_idx": 1,
                        "door_confirmation_roi": [10, 10, 10, 10],
                    }
                ],
            },
        },
    )

    loader = ConfigLoader.instance()
    with pytest.raises(ConfigurationError, match="超出 capture 分辨率边界"):
        loader.load(str(config_path))

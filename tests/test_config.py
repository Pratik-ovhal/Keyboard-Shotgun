"""Unit tests for configuration manager."""

import json
from pathlib import Path

import pytest

from core.config_manager import ConfigManager, DEFAULT_CONFIG


def test_default_config_creation(tmp_path: Path):
    """Test that a non-existent config file is automatically populated with defaults."""
    cfg_file = tmp_path / "config.json"
    assert not cfg_file.exists()

    mgr = ConfigManager(cfg_file)
    assert cfg_file.exists()
    assert mgr.get("master_volume") == 0.8
    assert mgr.get("is_muted") is False
    assert mgr.get("pitch_variation_enabled") is True
    assert mgr.get("num_variations") == 10
    assert mgr.get("max_channels") == 8
    assert mgr.get("cooldown_duration") == 0.0


def test_corrupted_config_recovery(tmp_path: Path):
    """Test that an unparseable or corrupted config file safely recovers without crashing."""
    cfg_file = tmp_path / "corrupted_config.json"
    cfg_file.write_text("{ this is completely invalid json !!!", encoding="utf-8")

    mgr = ConfigManager(cfg_file)
    # Manager should fall back to valid defaults and rewrite valid JSON
    assert mgr.get("master_volume") == DEFAULT_CONFIG["master_volume"]
    assert mgr.get("is_muted") == DEFAULT_CONFIG["is_muted"]

    # File should now contain valid JSON
    with open(cfg_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, dict)
        assert data["master_volume"] == 0.8


def test_empty_config_recovery(tmp_path: Path):
    """Test that an empty file recovers safely to default configuration."""
    cfg_file = tmp_path / "empty_config.json"
    cfg_file.write_text("", encoding="utf-8")

    mgr = ConfigManager(cfg_file)
    assert mgr.get("master_volume") == 0.8


def test_value_clamping_and_validation(tmp_path: Path):
    """Test that values are clamped within realistic, safe bounds."""
    cfg_file = tmp_path / "clamp_config.json"
    mgr = ConfigManager(cfg_file)

    # Volume: 0.0 to 1.0
    mgr.set("master_volume", 2.5)
    assert mgr.get("master_volume") == 1.0
    mgr.set("master_volume", -0.5)
    assert mgr.get("master_volume") == 0.0

    # Pitch intensity: 0.0 to 0.5
    mgr.set("pitch_intensity", 0.99)
    assert mgr.get("pitch_intensity") == 0.5

    # Max channels: at least 4
    mgr.set("max_channels", 1)
    assert mgr.get("max_channels") == 4


def test_update_and_persistence(tmp_path: Path):
    """Test updating multiple values and reloading in a new manager instance."""
    cfg_file = tmp_path / "persist_config.json"
    mgr1 = ConfigManager(cfg_file)
    mgr1.update({
        "master_volume": 0.55,
        "is_muted": True,
        "cooldown_duration": 0.15,
    })

    # Reload from disk in a fresh instance
    mgr2 = ConfigManager(cfg_file)
    assert mgr2.get("master_volume") == 0.55
    assert mgr2.get("is_muted") is True
    assert mgr2.get("cooldown_duration") == 0.15


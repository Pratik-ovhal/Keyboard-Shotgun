"""Test suite for the new modern UI/UX redesign components and navigation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from core.config_manager import ConfigManager
from core.event_handler import EventHandler
from core.keyboard_listener import KeyboardListener
from core.sound_engine import SoundEngine
from tests.test_audio_engine import create_fixture_wav
from ui.components.toggle_switch import ToggleSwitch
from ui.components.wave_visualizer import SoundWaveVisualizer
from ui.main_window import MainWindow
from ui.tray_manager import TrayManager


@pytest.fixture(scope="session")
def qapp():
    """Ensure QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_toggle_switch_component(qapp):
    """Test modern ToggleSwitch state, animation properties, and signals."""
    toggle = ToggleSwitch(checked=False)
    assert not toggle.isChecked()
    assert toggle.get_thumb_position() == 0.0

    toggle.setChecked(True)
    assert toggle.isChecked()
    assert toggle.get_thumb_position() == 1.0

    # Test toggled signal
    mock_slot = MagicMock()
    toggle.toggled.connect(mock_slot)
    toggle.setChecked(False)
    mock_slot.assert_called_with(False)


def test_wave_visualizer_component(qapp):
    """Test SoundWaveVisualizer activation and tactile pulse."""
    vis = SoundWaveVisualizer(bar_count=7)
    assert not vis._is_active

    vis.set_active(True)
    assert vis._is_active
    assert vis._timer.isActive()

    vis.pulse()
    assert vis._pulse_intensity == 1.0

    vis.set_active(False)
    assert not vis._is_active
    assert not vis._timer.isActive()


def test_main_window_sidebar_navigation(qapp, tmp_path: Path):
    """Test sidebar navigation button switching across Home, Settings, and About."""
    cfg = ConfigManager(tmp_path / "cfg.json")
    wav_path = create_fixture_wav(tmp_path / "nav.wav")
    engine = SoundEngine(audio_path=wav_path)
    engine.load_audio()
    event_handler = EventHandler(sound_engine=engine, config_manager=cfg)
    keyboard_listener = KeyboardListener(on_key_press_callback=lambda ts: None)
    tray_manager = TrayManager()

    window = MainWindow(
        config_manager=cfg,
        sound_engine=engine,
        event_handler=event_handler,
        keyboard_listener=keyboard_listener,
        tray_manager=tray_manager,
    )

    # Initial page should be Home (index 0)
    assert window.stack.currentIndex() == 0
    assert window.btn_nav_home.isChecked()

    # Switch to Settings (index 1)
    window.btn_nav_settings.click()
    assert window.stack.currentIndex() == 1
    assert window.btn_nav_settings.isChecked()

    # Switch to About (index 2)
    window.btn_nav_about.click()
    assert window.stack.currentIndex() == 2
    assert window.btn_nav_about.isChecked()

    # System diagnostics labels should exist in About page
    assert window.lbl_delay_val is not None
    assert window.lbl_avg_val is not None

    # Switch back to Home (index 0)
    window.btn_nav_home.click()
    assert window.stack.currentIndex() == 0

    window.force_exit()


def test_main_window_hero_toggle_and_volume(qapp, tmp_path: Path):
    """Test Home hero control, volume slider, mute toggle, and status indicators."""
    cfg = ConfigManager(tmp_path / "cfg.json")
    wav_path = create_fixture_wav(tmp_path / "hero.wav")
    engine = SoundEngine(audio_path=wav_path)
    engine.load_audio()
    event_handler = EventHandler(sound_engine=engine, config_manager=cfg)
    keyboard_listener = KeyboardListener(on_key_press_callback=lambda ts: None)
    tray_manager = TrayManager()

    window = MainWindow(
        config_manager=cfg,
        sound_engine=engine,
        event_handler=event_handler,
        keyboard_listener=keyboard_listener,
        tray_manager=tray_manager,
    )

    # Test Hero Button Toggle
    assert not window.keyboard_listener.is_running()
    # Click hero button to start
    window.btn_hero.click()
    assert window.keyboard_listener.is_running()
    assert window.status_badge.text() == "Running"
    assert window.wave_visualizer._is_active

    # Click hero button to stop
    window.btn_hero.click()
    assert not window.keyboard_listener.is_running()
    assert window.status_badge.text() == "Stopped"
    assert not window.wave_visualizer._is_active

    # Test Volume Slider & Label Sync
    window.vol_slider.setValue(45)
    assert window.vol_value_label.text() == "45%"
    assert pytest.approx(window.sound_engine.master_volume, 0.01) == 0.45

    # Test Mute Toggle
    assert not window.sound_engine.is_muted
    window.btn_mute.click()
    assert window.sound_engine.is_muted
    assert window.status_badge.text() == "Muted"

    window.btn_mute.click()
    assert not window.sound_engine.is_muted

    # Test Latency & Pulse update
    window._update_latency_display(1.42)
    assert window.lbl_delay_val.text() == "1.42 ms"

    window.force_exit()


def test_main_window_settings_controls(qapp, tmp_path: Path):
    """Test Settings screen controls and config synchronization."""
    cfg = ConfigManager(tmp_path / "cfg.json")
    wav_path = create_fixture_wav(tmp_path / "settings.wav")
    engine = SoundEngine(audio_path=wav_path)
    engine.load_audio()
    event_handler = EventHandler(sound_engine=engine, config_manager=cfg)
    keyboard_listener = KeyboardListener(on_key_press_callback=lambda ts: None)
    tray_manager = TrayManager()

    window = MainWindow(
        config_manager=cfg,
        sound_engine=engine,
        event_handler=event_handler,
        keyboard_listener=keyboard_listener,
        tray_manager=tray_manager,
    )

    # 1. Pitch variation toggle
    assert window.cb_pitch_variation.isChecked()
    window.cb_pitch_variation.click()
    assert not window.cb_pitch_variation.isChecked()
    assert not cfg.get("pitch_variation_enabled")

    # 2. Pitch intensity slider
    window.slider_pitch_intensity.setValue(15)
    assert window.lbl_intensity_val.text() == "15%"
    assert pytest.approx(cfg.get("pitch_intensity"), 0.01) == 0.15

    # 3. Pre-generated variations
    window.spin_variations.setValue(12)
    assert cfg.get("num_variations") == 12

    # 4. Max channels
    window.spin_channels.setValue(16)
    assert cfg.get("max_channels") == 16

    # 5. Cooldown
    window.spin_cooldown.setValue(0.15)
    assert pytest.approx(cfg.get("cooldown_duration"), 0.01) == 0.15

    # 6. System toggles
    window.cb_start_in_background.click()
    assert cfg.get("start_in_background") is True

    window.cb_minimize_to_tray.click()
    assert cfg.get("minimize_to_tray") is False

    window.cb_show_permissions_notify.click()
    assert cfg.get("show_permission_notifications") is False

    window.force_exit()


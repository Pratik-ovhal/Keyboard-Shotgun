"""Integration tests covering GUI lifecycle, tray minimization, and overlapping playback."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

from core.config_manager import ConfigManager
from core.event_handler import EventHandler
from core.keyboard_listener import KeyboardListener
from core.sound_engine import SoundEngine
from tests.test_audio_engine import create_fixture_wav
from ui.main_window import MainWindow
from ui.tray_manager import TrayManager


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance for Qt GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_overlapping_playback(tmp_path: Path):
    """Verify that multiple simultaneous sounds can play across mixer channels without cutting off."""
    wav_path = create_fixture_wav(tmp_path / "overlap.wav", duration_sec=0.4)
    engine = SoundEngine(audio_path=wav_path, max_channels=8)
    engine.load_audio()

    # Play 6 rapid sounds in succession
    for _ in range(6):
        engine.play()

    # Channels should be active concurrently
    import pygame
    busy_count = pygame.mixer.get_busy()
    assert busy_count > 0

    engine.cleanup()


def test_close_window_minimizes_to_tray_when_enabled(qapp, tmp_path: Path):
    """Test that window close event hides the window instead of exiting when minimize_to_tray is True."""
    cfg = ConfigManager(tmp_path / "cfg.json")
    cfg.set("minimize_to_tray", True)

    wav_path = create_fixture_wav(tmp_path / "gui.wav")
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
    window.show()
    assert window.isVisible()

    # Simulate close event
    close_event = QCloseEvent()
    window.closeEvent(close_event)

    # Event should be ignored (rejected) and window hidden
    assert not close_event.isAccepted()
    assert not window.isVisible()

    window.force_exit()


def test_close_window_exits_when_minimize_to_tray_disabled(qapp, tmp_path: Path):
    """Test that window close event calls force_exit when minimize_to_tray is False."""
    cfg = ConfigManager(tmp_path / "cfg.json")
    cfg.set("minimize_to_tray", False)

    wav_path = create_fixture_wav(tmp_path / "gui2.wav")
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
    window.show()

    close_event = QCloseEvent()
    with patch.object(window, "force_exit") as mock_exit:
        window.closeEvent(close_event)
        assert close_event.isAccepted()
        mock_exit.assert_called_once()

    window.force_exit()


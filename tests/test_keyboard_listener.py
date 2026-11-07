"""Unit tests for keyboard listener, key-repeat filtering, and event queue pipeline."""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pynput.keyboard import Key, KeyCode

from core.config_manager import ConfigManager
from core.event_handler import EventHandler
from core.keyboard_listener import KeyboardListener
from core.sound_engine import SoundEngine
from tests.test_audio_engine import create_fixture_wav


def test_key_repeat_suppression():
    """Verify that holding down a key (repeated on_press) generates only ONE event

    until that key is released.
    """
    events = []

    def on_press(ts):
        events.append(ts)

    listener = KeyboardListener(on_key_press_callback=on_press)

    test_key = KeyCode.from_char("a")

    # Simulate physical press
    listener._on_press(test_key)
    assert len(events) == 1

    # Simulate OS auto-repeat while key is held down
    listener._on_press(test_key)
    listener._on_press(test_key)
    listener._on_press(test_key)
    # Count should still be 1!
    assert len(events) == 1

    # Simulate physical key release
    listener._on_release(test_key)

    # Next press should now be registered
    listener._on_press(test_key)
    assert len(events) == 2


def test_various_key_types_trigger_event():
    """Verify that different key types (letters, numbers, modifiers, function keys)

    all successfully trigger events.
    """
    triggered_keys = []

    def on_press(ts):
        triggered_keys.append(ts)

    listener = KeyboardListener(on_key_press_callback=on_press)

    keys_to_test = [
        KeyCode.from_char("k"),
        KeyCode.from_char("7"),
        Key.space,
        Key.enter,
        Key.backspace,
        Key.shift,
        Key.ctrl_l,
        Key.alt_l,
        Key.f5,
        Key.up,
        Key.down,
    ]

    for key in keys_to_test:
        listener._on_press(key)
        listener._on_release(key)

    assert len(triggered_keys) == len(keys_to_test)


def test_rapid_burst_handling_no_freeze(tmp_path: Path):
    """Verify rapid bursts of key events are queued and processed asynchronously without freezing."""
    wav_path = create_fixture_wav(tmp_path / "burst.wav")
    cfg = ConfigManager(tmp_path / "cfg.json")
    engine = SoundEngine(audio_path=wav_path)
    engine.load_audio()

    played_count = 0

    def on_played(delay):
        nonlocal played_count
        played_count += 1

    handler = EventHandler(
        sound_engine=engine,
        config_manager=cfg,
        on_sound_played=on_played,
    )
    handler.start()

    # Submit 100 rapid events
    start_time = time.perf_counter()
    for _ in range(100):
        handler.submit_event()
    elapsed = time.perf_counter() - start_time

    # Submission should be practically instantaneous (under 50ms total for 100 events)
    assert elapsed < 0.05

    # Allow worker thread to drain queue
    time.sleep(0.3)
    handler.stop()
    engine.cleanup()


def test_cooldown_setting(tmp_path: Path):
    """Verify that setting a cooldown drops events that occur too quickly."""
    wav_path = create_fixture_wav(tmp_path / "cooldown.wav")
    cfg = ConfigManager(tmp_path / "cfg.json")
    cfg.set("cooldown_duration", 0.1)  # 100 ms cooldown

    engine = SoundEngine(audio_path=wav_path)
    engine.load_audio()

    played_count = 0

    def on_played(delay):
        nonlocal played_count
        played_count += 1

    handler = EventHandler(
        sound_engine=engine,
        config_manager=cfg,
        on_sound_played=on_played,
    )
    handler.start()

    # Submit 5 events in immediate succession (0 ms spacing)
    for _ in range(5):
        handler.submit_event()

    time.sleep(0.2)
    handler.stop()
    engine.cleanup()

    # Only 1 sound should have played because subsequent ones were within the 100ms cooldown window
    assert played_count == 1


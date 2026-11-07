"""Unit tests for the sound engine, NumPy pitch shifting, and playback management."""

import struct
import wave
from pathlib import Path

import numpy as np
import pytest

from core.sound_engine import (
    AudioEngineError,
    AudioFileCorruptError,
    AudioFileNotFoundError,
    SoundEngine,
)


def create_fixture_wav(path: Path, duration_sec: float = 0.2, sample_rate: int = 44100) -> Path:
    """Create a minimal clean 16-bit PCM stereo test WAV file in a temporary folder."""
    num_samples = int(duration_sec * sample_rate)
    # Generate a brief decaying transient click/tone
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    decay = np.exp(-t * 20)
    waveform = (np.sin(2 * np.pi * 300 * t) * decay * 16000).astype(np.int16)

    # Stereo interleaving
    stereo_data = np.column_stack((waveform, waveform))

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(stereo_data.tobytes())

    return path


@pytest.fixture
def sample_wav(tmp_path: Path) -> Path:
    """Fixture providing a valid stereo 16-bit WAV file in tmp_path."""
    wav_path = tmp_path / "test_shotgun.wav"
    return create_fixture_wav(wav_path)


def test_missing_audio_file_raises_error(tmp_path: Path):
    """Confirm missing WAV file produces a clear AudioFileNotFoundError."""
    non_existent = tmp_path / "missing_file.wav"
    engine = SoundEngine(audio_path=non_existent)
    with pytest.raises(AudioFileNotFoundError) as exc_info:
        engine.load_audio()
    assert "not found" in str(exc_info.value).lower()


def test_corrupted_audio_file_raises_error(tmp_path: Path):
    """Confirm invalid/corrupted audio data raises AudioFileCorruptError."""
    corrupted_path = tmp_path / "corrupted.wav"
    corrupted_path.write_bytes(b"NOT_A_VALID_RIFF_HEADER_JUST_GARBAGE_BYTES")

    engine = SoundEngine(audio_path=corrupted_path)
    with pytest.raises(AudioFileCorruptError) as exc_info:
        engine.load_audio()
    assert "valid" in str(exc_info.value).lower() or "header" in str(exc_info.value).lower()


def test_audio_loading_and_pitch_variations(sample_wav: Path):
    """Confirm audio loads and creates requested number of variations using NumPy."""
    engine = SoundEngine(
        audio_path=sample_wav,
        pitch_variation_enabled=True,
        pitch_intensity=0.08,
        num_variations=10,
        max_channels=8,
    )
    engine.load_audio()

    assert engine.is_ready()
    # Should have 10 variations preloaded in memory
    assert len(engine._variations) == 10
    assert engine._base_array is not None
    assert engine._base_array.ndim == 2  # stereo

    engine.cleanup()


def test_pitch_variation_disabled(sample_wav: Path):
    """Confirm that when pitch variation is disabled, exactly 1 base variation is kept."""
    engine = SoundEngine(
        audio_path=sample_wav,
        pitch_variation_enabled=False,
        num_variations=10,
    )
    engine.load_audio()

    assert len(engine._variations) == 1
    engine.cleanup()


def test_volume_and_mute(sample_wav: Path):
    """Verify master volume adjustment and immediate mute."""
    engine = SoundEngine(audio_path=sample_wav, master_volume=0.8, is_muted=False)
    engine.load_audio()

    # Adjust volume
    engine.set_volume(0.4)
    assert engine.master_volume == 0.4

    # Test Mute
    engine.set_mute(True)
    assert engine.is_muted is True

    # Play when muted should return immediately without playing
    delay_ms = engine.play()
    assert isinstance(delay_ms, float)

    # Unmute
    engine.set_mute(False)
    assert engine.is_muted is False

    engine.cleanup()


def test_software_latency_metric(sample_wav: Path):
    """Verify software latency calculation from trigger timestamp."""
    import time

    engine = SoundEngine(audio_path=sample_wav)
    engine.load_audio()

    trigger_time = time.perf_counter()
    time.sleep(0.005)  # simulate 5ms processing delay
    delay_ms = engine.play(trigger_timestamp=trigger_time)

    assert delay_ms >= 4.0
    assert engine.last_software_latency_ms == delay_ms
    assert engine.average_software_latency_ms > 0

    engine.cleanup()


"""Audio engine for Keyboard Shotgun.

Responsible for:
- Low-latency audio playback using pygame.mixer.
- Generating realistic pitch variations in-memory using NumPy.
- Multi-channel audio management with overlap preservation.
- Software latency measurement and benchmarking.
"""

import logging
import math
import os
import random
import time
import wave
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pygame

logger = logging.getLogger("KeyboardShotgun.SoundEngine")


class AudioEngineError(Exception):
    """Base exception for audio engine errors."""
    pass


class AudioFileNotFoundError(AudioEngineError):
    """Raised when the specified audio file cannot be found."""
    pass


class AudioFileCorruptError(AudioEngineError):
    """Raised when the audio file is corrupted or unsupported."""
    pass


class AudioDeviceError(AudioEngineError):
    """Raised when no audio playback device is available."""
    pass


class SoundEngine:
    """Core audio engine for loading, pitch-shifting, and playing sound effects."""

    def __init__(
        self,
        audio_path: Optional[str | Path] = None,
        master_volume: float = 0.8,
        is_muted: bool = False,
        pitch_variation_enabled: bool = True,
        pitch_intensity: float = 0.08,
        num_variations: int = 10,
        max_channels: int = 8,
    ) -> None:
        self.audio_path: Optional[Path] = Path(audio_path) if audio_path else None
        self.master_volume: float = max(0.0, min(1.0, float(master_volume)))
        self.is_muted: bool = bool(is_muted)
        self.pitch_variation_enabled: bool = bool(pitch_variation_enabled)
        self.pitch_intensity: float = max(0.0, min(0.5, float(pitch_intensity)))
        self.num_variations: int = max(1, min(32, int(num_variations)))
        self.max_channels: int = max(4, min(64, int(max_channels)))

        self._mixer_initialized: bool = False
        self._base_sound: Optional[pygame.mixer.Sound] = None
        self._base_array: Optional[np.ndarray] = None
        self._variations: List[pygame.mixer.Sound] = []
        self._current_channel_idx: int = 0

        # Latency benchmarking metrics
        self.last_software_latency_ms: float = 0.0
        self.average_software_latency_ms: float = 0.0
        self._latency_sample_count: int = 0
        self._total_latency_ms: float = 0.0

    def initialize_mixer(self, frequency: int = 44100, buffer_size: int = 512) -> None:
        """Initialize pygame mixer with minimal buffer size for low latency."""
        if self._mixer_initialized:
            return

        try:
            # Low buffer size (512 samples) keeps audio buffer latency under ~12ms at 44.1kHz
            pygame.mixer.pre_init(frequency=frequency, size=-16, channels=2, buffer=buffer_size)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(self.max_channels)
            self._mixer_initialized = True
            logger.info(
                f"Audio mixer initialized: freq={frequency}Hz, buffer={buffer_size} samples, "
                f"channels={self.max_channels}"
            )
        except Exception as e:
            self._mixer_initialized = False
            raise AudioDeviceError(f"Failed to initialize audio mixer/output device: {e}") from e

    def validate_audio_file(self, path: Path) -> Tuple[int, int, int]:
        """Validate that the given path points to a readable and valid WAV file.

        Returns:
            Tuple of (channels, sample_width, framerate).
        """
        if not path.exists():
            raise AudioFileNotFoundError(
                f"Audio file '{path.name}' was not found at expected location: {path.resolve()}"
            )

        if not path.is_file():
            raise AudioFileCorruptError(f"Audio path '{path.resolve()}' is not a regular file.")

        try:
            with wave.open(str(path), "rb") as wf:
                nchannels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                nframes = wf.getnframes()

                if nchannels < 1 or nchannels > 2:
                    raise AudioFileCorruptError(
                        f"Unsupported channel count: {nchannels}. Only mono (1) and stereo (2) WAV files are supported."
                    )
                if sampwidth not in (1, 2, 3, 4):
                    raise AudioFileCorruptError(
                        f"Unsupported sample width: {sampwidth * 8}-bit. Supported: 8, 16, 24, or 32-bit."
                    )
                if framerate < 8000 or framerate > 192000:
                    raise AudioFileCorruptError(f"Invalid sample rate: {framerate} Hz.")
                if nframes == 0:
                    raise AudioFileCorruptError("Audio file contains zero audio frames (empty audio).")

                return (nchannels, sampwidth, framerate)
        except wave.Error as e:
            raise AudioFileCorruptError(f"File is not a valid RIFF/WAVE file: {e}") from e
        except Exception as e:
            if isinstance(e, AudioEngineError):
                raise
            raise AudioFileCorruptError(f"Failed to read WAV audio header: {e}") from e

    def load_audio(self, audio_path: Optional[str | Path] = None) -> None:
        """Load the shotgun WAV file into memory and generate pitch variations."""
        if not self._mixer_initialized:
            self.initialize_mixer()

        if audio_path is not None:
            self.audio_path = Path(audio_path)

        if self.audio_path is None:
            raise AudioFileNotFoundError("No audio file path specified.")

        # Validate file integrity first
        self.validate_audio_file(self.audio_path)

        try:
            # Load into Pygame Sound
            self._base_sound = pygame.mixer.Sound(str(self.audio_path))
            self._base_sound.set_volume(self.master_volume)

            # Extract NumPy array from Pygame Sound
            # pygame.sndarray.array produces a copy of the sound's samples matching mixer format
            raw_array = pygame.sndarray.array(self._base_sound)
            self._base_array = raw_array.copy()

            logger.info(
                f"Loaded audio asset '{self.audio_path.name}': shape={self._base_array.shape}, "
                f"dtype={self._base_array.dtype}"
            )

            # Generate pitch variations
            self.generate_variations()

        except Exception as e:
            if isinstance(e, AudioEngineError):
                raise
            raise AudioFileCorruptError(f"Failed to load audio file into sound engine: {e}") from e

    def generate_variations(
        self,
        num_variations: Optional[int] = None,
        intensity: Optional[float] = None,
    ) -> None:
        """Generate pitch-shifted variations using NumPy resampling in memory.

        Resampling stretches or compresses the waveform without altering original files.
        Subtle pitch variation keeps the shotgun attack sharp while adding tactile diversity.
        """
        if self._base_array is None or self._base_sound is None:
            logger.warning("Cannot generate variations: Base audio not loaded.")
            return

        if num_variations is not None:
            self.num_variations = max(1, min(32, int(num_variations)))
        if intensity is not None:
            self.pitch_intensity = max(0.0, min(0.5, float(intensity)))

        orig = self._base_array
        orig_length = orig.shape[0]
        is_stereo = orig.ndim > 1 and orig.shape[1] > 1

        variations: List[pygame.mixer.Sound] = []

        # If variations disabled or count is 1 or intensity is 0, just use the base sound
        if not self.pitch_variation_enabled or self.num_variations <= 1 or self.pitch_intensity <= 0.001:
            self._base_sound.set_volume(self.master_volume)
            self._variations = [self._base_sound]
            logger.info("Pitch variation disabled or zero intensity. Using single base sound.")
            return

        # Generate a spread of pitch factors around 1.0
        # E.g., for intensity 0.08 and 10 variations: evenly spaced from 0.92 to 1.08
        min_factor = max(0.5, 1.0 - self.pitch_intensity)
        max_factor = min(1.5, 1.0 + self.pitch_intensity)
        pitch_factors = np.linspace(min_factor, max_factor, self.num_variations)

        orig_x = np.arange(orig_length)

        for factor in pitch_factors:
            if abs(factor - 1.0) < 0.005:
                # Untouched base sound
                var_sound = self._base_sound
            else:
                # Resample: new length = orig_length / factor
                new_length = int(round(orig_length / factor))
                new_x = np.linspace(0, orig_length - 1, new_length)

                if is_stereo:
                    num_channels = orig.shape[1]
                    resampled = np.empty((new_length, num_channels), dtype=np.float64)
                    for ch in range(num_channels):
                        resampled[:, ch] = np.interp(new_x, orig_x, orig[:, ch].astype(np.float64))
                else:
                    resampled = np.interp(new_x, orig_x, orig.astype(np.float64))

                # Prevent clipping and convert back to int16
                resampled = np.clip(resampled, -32768, 32767).astype(np.int16)
                var_sound = pygame.sndarray.make_sound(resampled)

            var_sound.set_volume(self.master_volume)
            variations.append(var_sound)

        self._variations = variations
        logger.info(
            f"Pre-generated {len(self._variations)} pitch variations in memory "
            f"(intensity={self.pitch_intensity:.3f}, factors range [{min_factor:.3f}, {max_factor:.3f}])."
        )

    def play(self, trigger_timestamp: Optional[float] = None) -> float:
        """Play a random shotgun sound asynchronously.

        Args:
            trigger_timestamp: Timestamp (from time.perf_counter()) of the keyboard event.

        Returns:
            Estimated software processing delay in milliseconds (trigger to playback dispatch).
        """
        play_request_time = time.perf_counter()

        # Compute software processing latency
        if trigger_timestamp is not None and trigger_timestamp > 0:
            software_delay_ms = max(0.0, (play_request_time - trigger_timestamp) * 1000.0)
        else:
            software_delay_ms = 0.0

        self.last_software_latency_ms = software_delay_ms
        self._latency_sample_count += 1
        self._total_latency_ms += software_delay_ms
        self.average_software_latency_ms = self._total_latency_ms / self._latency_sample_count

        if self.is_muted:
            return software_delay_ms

        if not self._mixer_initialized or not self._variations:
            return software_delay_ms

        # Select variation
        if self.pitch_variation_enabled and len(self._variations) > 1:
            sound_to_play = random.choice(self._variations)
        else:
            sound_to_play = self._base_sound or self._variations[0]

        # Overlapping playback channel management:
        # 1. Try to find an idle channel
        # 2. If all channels are busy, use force=True (pygame chooses the longest-running channel)
        try:
            channel = pygame.mixer.find_channel(force=True)
            if channel is not None:
                channel.play(sound_to_play)
            else:
                sound_to_play.play()
        except Exception as e:
            logger.debug(f"Error during audio playback dispatch: {e}")

        return software_delay_ms

    def set_volume(self, volume: float) -> None:
        """Set master volume between 0.0 and 1.0."""
        self.master_volume = max(0.0, min(1.0, float(volume)))
        if self._base_sound is not None:
            self._base_sound.set_volume(self.master_volume)
        for var in self._variations:
            var.set_volume(self.master_volume)

    def set_mute(self, is_muted: bool) -> None:
        """Mute or unmute all sound playback immediately."""
        self.is_muted = bool(is_muted)
        if self.is_muted:
            # Stop any currently active channels immediately
            if self._mixer_initialized:
                try:
                    pygame.mixer.stop()
                except Exception:
                    pass

    def set_pitch_variation_enabled(self, enabled: bool) -> None:
        """Enable or disable pitch variation."""
        self.pitch_variation_enabled = bool(enabled)

    def set_max_channels(self, count: int) -> None:
        """Update maximum simultaneous audio channels."""
        self.max_channels = max(4, min(64, int(count)))
        if self._mixer_initialized:
            try:
                pygame.mixer.set_num_channels(self.max_channels)
            except Exception as e:
                logger.warning(f"Could not update channel count: {e}")

    def is_ready(self) -> bool:
        """Return True if mixer is initialized and audio assets are ready."""
        return self._mixer_initialized and len(self._variations) > 0

    def stop_all(self) -> None:
        """Stop all currently playing audio channels."""
        if self._mixer_initialized:
            try:
                pygame.mixer.stop()
            except Exception:
                pass

    def cleanup(self) -> None:
        """Clean up audio engine resources on application shutdown."""
        self.stop_all()
        self._variations.clear()
        self._base_sound = None
        self._base_array = None
        if self._mixer_initialized:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
            self._mixer_initialized = False
        logger.info("Audio engine cleaned up.")


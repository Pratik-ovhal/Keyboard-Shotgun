"""Event handler and audio worker pipeline for Keyboard Shotgun.

Decouples keyboard event detection from audio playback using a thread-safe queue.
Enforces cooldowns, handles event bursts safely, and benchmarks software latency.
"""

import logging
import queue
import threading
import time
from typing import Callable, Optional

from core.config_manager import ConfigManager
from core.sound_engine import SoundEngine

logger = logging.getLogger("KeyboardShotgun.EventHandler")


class AudioWorker(threading.Thread):
    """Background worker thread that consumes keypress events from a thread-safe queue

    and dispatches audio playback without blocking input.
    """

    def __init__(
        self,
        event_queue: queue.Queue,
        sound_engine: SoundEngine,
        config_manager: ConfigManager,
        on_sound_played: Optional[Callable[[float], None]] = None,
    ) -> None:
        super().__init__(daemon=True, name="AudioWorkerThread")
        self.event_queue = event_queue
        self.sound_engine = sound_engine
        self.config_manager = config_manager
        self.on_sound_played = on_sound_played

        self._running = threading.Event()
        self._running.set()
        self._paused = threading.Event()  # when set, worker ignores or pauses playback

        self._last_played_time: float = 0.0
        self.total_events_processed: int = 0
        self.total_sounds_played: int = 0
        self.dropped_events_count: int = 0

    def pause(self) -> None:
        """Pause audio playback (events are drained/ignored)."""
        self._paused.set()

    def resume(self) -> None:
        """Resume audio playback."""
        self._paused.clear()

    def is_paused(self) -> bool:
        """Return True if playback worker is paused."""
        return self._paused.is_set()

    def stop(self) -> None:
        """Stop worker thread gracefully."""
        self._running.clear()
        # Put sentinel to unblock queue.get()
        try:
            self.event_queue.put_nowait(None)
        except queue.Full:
            pass

    def run(self) -> None:
        """Worker loop processing events from queue."""
        logger.info("Audio worker thread started.")
        while self._running.is_set():
            try:
                # Wait for an event with timeout to periodically check running state
                item = self.event_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if item is None:
                # Sentinel to terminate thread
                break

            self.total_events_processed += 1

            # If paused or muted, discard playback immediately
            if self._paused.is_set() or self.sound_engine.is_muted:
                continue

            trigger_time = item
            now = time.perf_counter()

            # Enforce cooldown if configured
            cooldown = float(self.config_manager.get("cooldown_duration", 0.0))
            if cooldown > 0.0 and (now - self._last_played_time) < cooldown:
                self.dropped_events_count += 1
                continue

            # Play sound through sound engine
            software_delay_ms = self.sound_engine.play(trigger_timestamp=trigger_time)
            self._last_played_time = time.perf_counter()
            self.total_sounds_played += 1

            if self.on_sound_played:
                try:
                    self.on_sound_played(software_delay_ms)
                except Exception as e:
                    logger.debug(f"Error in on_sound_played callback: {e}")

        logger.info("Audio worker thread terminated.")


class EventHandler:
    """Manages the event queue, audio worker thread, and pipeline diagnostics."""

    def __init__(
        self,
        sound_engine: SoundEngine,
        config_manager: ConfigManager,
        max_queue_size: int = 128,
        on_sound_played: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.sound_engine = sound_engine
        self.config_manager = config_manager
        self.event_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.on_sound_played = on_sound_played

        self._worker: Optional[AudioWorker] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the audio worker pipeline."""
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                return
            self._worker = AudioWorker(
                event_queue=self.event_queue,
                sound_engine=self.sound_engine,
                config_manager=self.config_manager,
                on_sound_played=self.on_sound_played,
            )
            self._worker.start()
            logger.info("Event handler pipeline started.")

    def stop(self) -> None:
        """Stop the audio worker pipeline."""
        with self._lock:
            if self._worker is not None:
                self._worker.stop()
                self._worker.join(timeout=1.0)
                self._worker = None
            # Clear remaining queue items
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except queue.Empty:
                    break
            logger.info("Event handler pipeline stopped.")

    def pause(self) -> None:
        """Pause event processing."""
        with self._lock:
            if self._worker:
                self._worker.pause()

    def resume(self) -> None:
        """Resume event processing."""
        with self._lock:
            if self._worker:
                self._worker.resume()

    def is_paused(self) -> bool:
        """Check if pipeline is paused."""
        with self._lock:
            return self._worker.is_paused() if self._worker else True

    def submit_event(self, timestamp: Optional[float] = None) -> bool:
        """Submit a lightweight trigger event to the queue. Non-blocking and thread-safe."""
        ts = timestamp if timestamp is not None else time.perf_counter()
        try:
            self.event_queue.put_nowait(ts)
            return True
        except queue.Full:
            # Drop event during extreme bursts to avoid freezing the app or memory buildup
            logger.debug("Event queue full. Event dropped.")
            return False

    def trigger_test_sound(self) -> float:
        """Directly trigger a test sound and return estimated software processing latency."""
        now = time.perf_counter()
        return self.sound_engine.play(trigger_timestamp=now)


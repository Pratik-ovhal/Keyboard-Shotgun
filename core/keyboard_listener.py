"""Global keyboard listener for Keyboard Shotgun.

Detects global keypresses across Windows and macOS using pynput.
Filters out OS key-repeat events while holding down keys.
Ensures zero logging or storage of typed characters for privacy and security.
"""

import logging
import threading
import time
from typing import Callable, Optional, Set

from pynput import keyboard

logger = logging.getLogger("KeyboardShotgun.KeyboardListener")


class KeyboardListener:
    """Thread-safe global keyboard listener that submits timestamps on key press.

    Filters out key-repeat events to guarantee a single sound per physical keypress.
    """

    def __init__(
        self,
        on_key_press_callback: Callable[[float], None],
        on_error_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.on_key_press_callback = on_key_press_callback
        self.on_error_callback = on_error_callback

        self._listener: Optional[keyboard.Listener] = None
        self._pressed_keys: Set[object] = set()
        self._lock = threading.Lock()
        self._is_running: bool = False
        self._permission_denied: bool = False

    def is_running(self) -> bool:
        """Return True if listener is active."""
        return self._is_running and self._listener is not None and self._listener.is_alive()

    def start(self) -> bool:
        """Start the global keyboard listener in a background thread."""
        with self._lock:
            if self._is_running and self._listener is not None and self._listener.is_alive():
                return True

            self._pressed_keys.clear()
            self._permission_denied = False

            try:
                self._listener = keyboard.Listener(
                    on_press=self._on_press,
                    on_release=self._on_release,
                    suppress=False,  # Do not block system keystrokes
                )
                self._listener.daemon = True
                self._listener.start()
                self._is_running = True
                logger.info("Global keyboard listener started.")
                return True
            except Exception as e:
                self._is_running = False
                self._permission_denied = True
                error_msg = f"Failed to start keyboard listener: {e}"
                logger.error(error_msg)
                if self.on_error_callback:
                    self.on_error_callback(error_msg)
                return False

    def stop(self) -> None:
        """Stop the keyboard listener."""
        with self._lock:
            if self._listener is not None:
                try:
                    self._listener.stop()
                except Exception as e:
                    logger.debug(f"Exception while stopping listener: {e}")
                self._listener = None
            self._pressed_keys.clear()
            self._is_running = False
            logger.info("Global keyboard listener stopped.")

    def reset_state(self) -> None:
        """Clear currently tracked pressed keys."""
        with self._lock:
            self._pressed_keys.clear()

    def _on_press(self, key: object) -> None:
        """Low-latency callback executed upon key down."""
        # Grab high-resolution timestamp immediately as first operation
        trigger_time = time.perf_counter()

        with self._lock:
            # Check if key is already held down (OS auto-repeat filter)
            if key in self._pressed_keys:
                return

            self._pressed_keys.add(key)

        # Dispatch timestamp to event queue (non-blocking)
        try:
            self.on_key_press_callback(trigger_time)
        except Exception as e:
            logger.debug(f"Error executing key press callback: {e}")

    def _on_release(self, key: object) -> None:
        """Callback executed upon key release."""
        with self._lock:
            self._pressed_keys.discard(key)


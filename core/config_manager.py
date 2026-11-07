"""Configuration manager for Keyboard Shotgun.

Handles loading, validating, updating, and saving application configuration
with automatic recovery from corrupted or missing configuration files.
"""

import json
import logging
import os
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("KeyboardShotgun.Config")

DEFAULT_CONFIG: Dict[str, Any] = {
    "master_volume": 0.8,
    "is_muted": False,
    "pitch_variation_enabled": True,
    "pitch_intensity": 0.08,
    "num_variations": 10,
    "max_channels": 8,
    "cooldown_duration": 0.0,
    "start_in_background": False,
    "minimize_to_tray": True,
    "launch_on_startup": False,
    "show_permission_notifications": True,
}


class ConfigManager:
    """Manages application settings stored in a JSON configuration file."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path is None:
            # Default to config.json in project root or current working dir
            self.config_path = Path(__file__).resolve().parent.parent / "config.json"
        else:
            self.config_path = Path(config_path)

        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {}
        self.load()

    def get_defaults(self) -> Dict[str, Any]:
        """Return a copy of the default configuration dictionary."""
        return dict(DEFAULT_CONFIG)

    def load(self) -> Dict[str, Any]:
        """Load configuration from disk. Recreate with defaults if missing or corrupted."""
        with self._lock:
            if not self.config_path.exists():
                logger.info(f"Config file not found at {self.config_path}. Creating with default settings.")
                self._data = dict(DEFAULT_CONFIG)
                self._save_unlocked()
                return dict(self._data)

            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        raise ValueError("Configuration file is empty.")
                    loaded_data = json.loads(content)
                    if not isinstance(loaded_data, dict):
                        raise ValueError("Configuration JSON is not a dictionary.")

                # Validate loaded keys and fill any missing ones with defaults
                merged_data = dict(DEFAULT_CONFIG)
                for key, val in loaded_data.items():
                    if key in DEFAULT_CONFIG:
                        # Type validation & range clamping
                        merged_data[key] = self._validate_field(key, val)

                self._data = merged_data
                return dict(self._data)

            except Exception as e:
                logger.warning(
                    f"Corrupted or invalid config at {self.config_path}: {e}. "
                    "Resetting configuration to default values."
                )
                self._data = dict(DEFAULT_CONFIG)
                self._save_unlocked()
                return dict(self._data)

    def _validate_field(self, key: str, val: Any) -> Any:
        """Validate and clamp configuration values."""
        default = DEFAULT_CONFIG[key]
        if isinstance(default, bool):
            return bool(val)
        if isinstance(default, (int, float)):
            try:
                num = float(val) if isinstance(default, float) else int(val)
                if key == "master_volume":
                    return max(0.0, min(1.0, float(num)))
                if key == "pitch_intensity":
                    return max(0.0, min(0.5, float(num)))
                if key == "num_variations":
                    return max(1, min(32, int(num)))
                if key == "max_channels":
                    return max(4, min(64, int(num)))
                if key == "cooldown_duration":
                    return max(0.0, min(2.0, float(num)))
                return num
            except (ValueError, TypeError):
                return default
        return val

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe retrieval of a configuration value."""
        with self._lock:
            return self._data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any) -> None:
        """Set a single configuration value and persist immediately."""
        with self._lock:
            validated = self._validate_field(key, value) if key in DEFAULT_CONFIG else value
            self._data[key] = validated
            self._save_unlocked()

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration keys and persist atomically."""
        with self._lock:
            for key, val in updates.items():
                if key in DEFAULT_CONFIG:
                    self._data[key] = self._validate_field(key, val)
                else:
                    self._data[key] = val
            self._save_unlocked()

    def get_all(self) -> Dict[str, Any]:
        """Return a copy of all current configuration settings."""
        with self._lock:
            return dict(self._data)

    def reset_to_defaults(self) -> None:
        """Reset all configuration values to defaults and save to disk."""
        with self._lock:
            self._data = dict(DEFAULT_CONFIG)
            self._save_unlocked()

    def _save_unlocked(self) -> None:
        """Atomic write using a temporary file in the same directory."""
        try:
            target_dir = self.config_path.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                dir=target_dir,
                encoding="utf-8",
                delete=False,
                suffix=".tmp"
            )
            try:
                json.dump(self._data, temp_file, indent=2)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_file.close()
                shutil.move(temp_file.name, self.config_path)
            except Exception:
                if os.path.exists(temp_file.name):
                    try:
                        os.remove(temp_file.name)
                    except OSError:
                        pass
                raise
        except Exception as e:
            logger.error(f"Failed to save configuration to {self.config_path}: {e}")

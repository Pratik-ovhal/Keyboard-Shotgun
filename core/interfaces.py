"""Shared interfaces and protocols for Keyboard Shotgun.

Eliminates circular and tight coupling between event pipeline,
audio engine, and configuration management.
"""

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class SoundPlayer(Protocol):
    """Protocol representing an audio player capable of playing keypress sounds."""

    is_muted: bool

    def play(self, trigger_timestamp: Optional[float] = None) -> float:
        """Play sound and return software latency in milliseconds."""
        ...


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for reading configuration keys."""

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve configuration value."""
        ...


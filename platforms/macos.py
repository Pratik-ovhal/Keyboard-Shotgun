"""macOS-specific integration for Keyboard Shotgun.

Handles:
- Accessibility and Input Monitoring permission checks via AXIsProcessTrusted.
- Actionable permission grant instructions.
- Architecture detection (Apple Silicon arm64 vs Intel x86_64).
- Launch on login via LaunchAgents property list (com.keyboardshotgun.plist).
"""

import logging
import os
import sys
from pathlib import Path
from typing import Tuple

logger = logging.getLogger("KeyboardShotgun.Platform.macOS")

LAUNCH_AGENT_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.keyboardshotgun.startup</string>
    <key>ProgramArguments</key>
    <array>
        {PROGRAM_ARGS}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""


def is_macos() -> bool:
    """Return True if running on macOS (Darwin)."""
    return sys.platform == "darwin"


def get_architecture() -> str:
    """Return macOS architecture: 'Apple Silicon (arm64)' or 'Intel (x86_64)'."""
    import platform
    arch = platform.machine().lower()
    if "arm" in arch or "aarch" in arch:
        return "Apple Silicon (arm64)"
    return "Intel (x86_64)"


def check_permissions() -> Tuple[bool, str]:
    """Check macOS Accessibility and Input Monitoring permissions.

    Never silently claims permissions are granted without verifying AXIsProcessTrusted.
    """
    if not is_macos():
        return False, "Not running on macOS."

    try:
        import ctypes
        app_services = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        is_trusted = app_services.AXIsProcessTrusted()

        if is_trusted:
            return True, "macOS Accessibility permissions are granted."

        instructions = (
            "Accessibility / Input Monitoring permission is required to detect global keypresses on macOS.\n\n"
            "Instructions to grant permission:\n"
            "1. Open System Settings > Privacy & Security > Accessibility.\n"
            "2. Turn ON the toggle for Keyboard Shotgun (or Terminal / Python if running from source).\n"
            "3. Also check Privacy & Security > Input Monitoring and enable Keyboard Shotgun.\n"
            "4. Relaunch Keyboard Shotgun."
        )
        return False, instructions
    except Exception as e:
        logger.warning(f"Could not verify macOS Accessibility status via ctypes: {e}")
        return False, f"Unable to verify macOS permissions: {e}"


def get_launch_on_startup() -> bool:
    """Check if LaunchAgent plist exists in ~/Library/LaunchAgents."""
    if not is_macos():
        return False
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.keyboardshotgun.startup.plist"
    return plist_path.exists()


def set_launch_on_startup(enable: bool, executable_path: str | Path | None = None) -> bool:
    """Configure or remove macOS login item via LaunchAgent."""
    if not is_macos():
        return False

    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_path = plist_dir / "com.keyboardshotgun.startup.plist"

    try:
        if enable:
            plist_dir.mkdir(parents=True, exist_ok=True)
            if executable_path is None:
                if getattr(sys, "frozen", False):
                    args = f"<string>{sys.executable}</string>"
                else:
                    main_py = Path(__file__).resolve().parent.parent / "main.py"
                    args = f"<string>{sys.executable}</string>\n        <string>{main_py}</string>"
            else:
                args = f"<string>{Path(executable_path).resolve()}</string>"

            content = LAUNCH_AGENT_PLIST.replace("{PROGRAM_ARGS}", args)
            with open(plist_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Created macOS LaunchAgent at {plist_path}")
            return True
        else:
            if plist_path.exists():
                plist_path.unlink()
                logger.info("Removed macOS LaunchAgent plist.")
            return True
    except Exception as e:
        logger.error(f"Failed to update macOS LaunchAgent: {e}")
        return False


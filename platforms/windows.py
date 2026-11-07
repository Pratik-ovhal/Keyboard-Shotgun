"""Windows-specific integration for Keyboard Shotgun.

Handles:
- Optional launch-on-startup via HKCU Run registry key.
- Windows permission verification (keyboard hook permissions).
- Path resolution for packaged and source executions.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Tuple

logger = logging.getLogger("KeyboardShotgun.Platform.Windows")

RUN_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "KeyboardShotgun"


def is_windows() -> bool:
    """Return True if running on Windows."""
    return sys.platform == "win32"


def check_permissions() -> Tuple[bool, str]:
    """Check if keyboard input detection permissions are sufficient on Windows.

    Windows allows user-level global hooks without special admin rights unless
    running against elevated UAC processes.
    """
    if not is_windows():
        return False, "Not running on Windows."
    # Standard user-level execution is supported
    return True, "Windows keyboard hook permissions available."


def get_launch_on_startup() -> bool:
    """Check if the application is registered in HKCU Run key."""
    if not is_windows():
        return False

    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_KEY, 0, winreg.KEY_READ) as key:
            try:
                val, _ = winreg.QueryValueEx(key, APP_NAME)
                return bool(val)
            except FileNotFoundError:
                return False
    except Exception as e:
        logger.debug(f"Could not read Windows startup registry key: {e}")
        return False


def set_launch_on_startup(enable: bool, executable_path: str | Path | None = None) -> bool:
    """Enable or disable launching Keyboard Shotgun on Windows login."""
    if not is_windows():
        return False

    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_KEY, 0, winreg.KEY_WRITE) as key:
            if enable:
                if executable_path is None:
                    # Determine current executable or python script path
                    if getattr(sys, "frozen", False):
                        cmd = f'"{sys.executable}"'
                    else:
                        main_py = Path(__file__).resolve().parent.parent / "main.py"
                        cmd = f'"{sys.executable}" "{main_py}"'
                else:
                    cmd = f'"{Path(executable_path).resolve()}"'

                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                logger.info(f"Registered Windows startup command: {cmd}")
                return True
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("Removed Windows startup registration.")
                except FileNotFoundError:
                    pass
                return True
    except Exception as e:
        logger.error(f"Failed to update Windows startup registry: {e}")
        return False


"""Asset path resolver for development and frozen PyInstaller environments."""

import sys
from pathlib import Path


def get_asset_path(filename: str) -> Path:
    """Resolve asset path for development and PyInstaller bundled environments.

    Args:
        filename: Name of the asset file (e.g. 'shotgun.wav' or 'config.json').

    Returns:
        Absolute Path pointing to the target asset.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass_path = Path(sys._MEIPASS) / filename
        if meipass_path.exists():
            return meipass_path
        # Fallback for macOS .app bundle directory structure
        if sys.platform == "darwin":
            res_path = Path(sys.executable).parent.parent / "Resources" / filename
            if res_path.exists():
                return res_path
        exe_path = Path(sys.executable).parent / filename
        if exe_path.exists():
            return exe_path
        return meipass_path
    else:
        # Project root directory (parent of core/)
        base_dir = Path(__file__).resolve().parent.parent
        return base_dir / filename


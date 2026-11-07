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
        base_dir = Path(sys._MEIPASS)
    else:
        # Project root directory (parent of core/)
        base_dir = Path(__file__).resolve().parent.parent

    return base_dir / filename


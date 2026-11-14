"""Keyboard Shotgun - Main Entry Point.

Cross-platform desktop application that plays a shotgun sound whenever any key is pressed.
Supports both background mode (system tray) and modern GUI mode (PySide6).
"""

import argparse
import logging
import os
import signal
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from core.assets import get_asset_path
from core.config_manager import ConfigManager
from core.event_handler import EventHandler
from core.keyboard_listener import KeyboardListener
from core.sound_engine import (
    AudioEngineError,
    AudioFileCorruptError,
    AudioFileNotFoundError,
    SoundEngine,
)
from ui.main_window import MainWindow
from ui.tray_manager import TrayManager, create_default_tray_icon

# Setup application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("KeyboardShotgun")


def check_platform_permissions(config_manager: ConfigManager) -> None:
    """Verify platform-specific permissions (e.g. macOS Accessibility)."""
    notify_enabled = config_manager.get("show_permission_notifications", True)

    if sys.platform == "darwin":
        from platforms.macos import check_permissions
        has_perm, msg = check_permissions()
        if not has_perm:
            logger.warning(f"macOS Permission Notice:\n{msg}")
            if notify_enabled and QApplication.instance():
                QMessageBox.warning(
                    None,
                    "macOS Permissions Required",
                    msg
                )
    elif sys.platform == "win32":
        from platforms.windows import check_permissions
        has_perm, msg = check_permissions()
        if not has_perm:
            logger.warning(f"Windows Permission Warning: {msg}")


def main() -> int:
    """Main application routine."""
    parser = argparse.ArgumentParser(description="Keyboard Shotgun - Audio on every keystroke.")
    parser.add_argument(
        "--background", "-b", action="store_true", help="Launch directly into background tray mode."
    )
    parser.add_argument(
        "--gui", "-g", action="store_true", help="Explicitly show the GUI on startup."
    )
    args = parser.parse_args()

    # Set explicit AppUserModelID on Windows so taskbar displays application icon
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("keyboardshotgun.desktop.app")
        except Exception:
            pass

    # Create or reuse PySide6 application
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Keyboard Shotgun")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(create_default_tray_icon())

    # 1. Load configuration
    config_file_path = get_asset_path("config.json")
    config_manager = ConfigManager(config_file_path)

    # 2. Check platform permissions
    check_platform_permissions(config_manager)

    # 3. Locate audio asset
    audio_path = get_asset_path("shotgun.wav")

    # 4. Initialize Sound Engine
    cfg = config_manager.get_all()
    sound_engine = SoundEngine(
        audio_path=audio_path,
        master_volume=cfg.get("master_volume", 0.8),
        is_muted=cfg.get("is_muted", False),
        pitch_variation_enabled=cfg.get("pitch_variation_enabled", True),
        pitch_intensity=cfg.get("pitch_intensity", 0.08),
        num_variations=cfg.get("num_variations", 10),
        max_channels=cfg.get("max_channels", 8),
    )

    audio_load_success = False
    try:
        sound_engine.initialize_mixer()
        sound_engine.load_audio(audio_path)
        audio_load_success = True
    except AudioFileNotFoundError:
        error_msg = (
            f"Audio file 'shotgun.wav' was not found.\n\n"
            f"Expected location: {audio_path.resolve()}\n\n"
            f"Please place your 'shotgun.wav' file in the application directory."
        )
        logger.warning(error_msg)
    except AudioFileCorruptError as e:
        error_msg = f"The audio file 'shotgun.wav' is corrupted or invalid:\n{e}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Failed to initialize audio engine:\n{e}"
        logger.error(error_msg)

    # 5. Initialize Event Handler pipeline
    event_handler = EventHandler(
        sound_engine=sound_engine,
        config_manager=config_manager,
    )
    event_handler.start()

    # 6. Initialize Global Keyboard Listener
    def on_key_pressed(timestamp: float) -> None:
        event_handler.submit_event(timestamp)

    def on_listener_error(err_str: str) -> None:
        logger.error(f"Keyboard listener error: {err_str}")

    keyboard_listener = KeyboardListener(
        on_key_press_callback=on_key_pressed,
        on_error_callback=on_listener_error,
    )

    if audio_load_success:
        keyboard_listener.start()

    # 7. Setup System Tray & Main Window
    tray_manager = TrayManager()
    tray_manager.show()

    main_window = MainWindow(
        config_manager=config_manager,
        sound_engine=sound_engine,
        event_handler=event_handler,
        keyboard_listener=keyboard_listener,
        tray_manager=tray_manager,
    )

    # Determine whether to show GUI on startup
    start_in_bg = args.background or (
        config_manager.get("start_in_background", False) and not args.gui
    )

    if not start_in_bg:
        main_window.show()
    else:
        tray_manager.show_message(
            "Keyboard Shotgun",
            "Keyboard Shotgun is active in the background. Press any key to hear shotgun sounds."
        )

    # Graceful shutdown handler for Ctrl+C / SIGINT
    signal.signal(signal.SIGINT, lambda *args: main_window.force_exit())
    signal.signal(signal.SIGTERM, lambda *args: main_window.force_exit())

    # Periodically allow Python signal handling inside Qt event loop
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    exit_code = app.exec()

    # Clean shutdown of all subsystems
    keyboard_listener.stop()
    event_handler.stop()
    sound_engine.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

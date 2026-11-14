"""Script to render and capture high-resolution screenshots of the 3 redesigned UI pages."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from core.config_manager import ConfigManager
from core.event_handler import EventHandler
from core.keyboard_listener import KeyboardListener
from core.sound_engine import SoundEngine
from ui.main_window import MainWindow
from ui.tray_manager import TrayManager


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    root_dir = Path(".").resolve()
    audio_path = root_dir / "shotgun.wav"
    cfg = ConfigManager(root_dir / "config.json")

    sound_engine = SoundEngine(audio_path=audio_path)
    try:
        sound_engine.initialize_mixer()
        sound_engine.load_audio(audio_path)
    except Exception as e:
        print(f"Audio init note: {e}")

    event_handler = EventHandler(sound_engine=sound_engine, config_manager=cfg)
    keyboard_listener = KeyboardListener(on_key_press_callback=lambda ts: None)
    tray_manager = TrayManager()

    window = MainWindow(
        config_manager=cfg,
        sound_engine=sound_engine,
        event_handler=event_handler,
        keyboard_listener=keyboard_listener,
        tray_manager=tray_manager,
    )
    window.resize(680, 720)
    window.show()

    output_dir = Path("scratch/screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Capture Home screen (Stopped)
    window.stack.setCurrentIndex(0)
    window.btn_nav_home.setChecked(True)
    app.processEvents()

    pix_home_stopped = window.grab()
    home_file_stopped = output_dir / "screenshot_home_stopped.png"
    pix_home_stopped.save(str(home_file_stopped))
    print(f"Captured: {home_file_stopped}")

    # 2. Start engine and capture Home screen (Running)
    window.btn_hero.click()
    # Let visualizer animate a few frames
    for _ in range(5):
        window.wave_visualizer.pulse()
        window.wave_visualizer._animate_step()
        app.processEvents()

    pix_home_running = window.grab()
    home_file_running = output_dir / "screenshot_home_running.png"
    pix_home_running.save(str(home_file_running))
    print(f"Captured: {home_file_running}")

    # 3. Capture Settings screen
    window.stack.setCurrentIndex(1)
    window.btn_nav_settings.setChecked(True)
    window._on_nav_changed(1)
    app.processEvents()

    pix_settings = window.grab()
    settings_file = output_dir / "screenshot_settings.png"
    pix_settings.save(str(settings_file))
    print(f"Captured: {settings_file}")

    # 4. Capture About screen
    window.stack.setCurrentIndex(2)
    window.btn_nav_about.setChecked(True)
    window._on_nav_changed(2)
    app.processEvents()

    pix_about = window.grab()
    about_file = output_dir / "screenshot_about.png"
    pix_about.save(str(about_file))
    print(f"Captured: {about_file}")

    window.force_exit()


if __name__ == "__main__":
    main()

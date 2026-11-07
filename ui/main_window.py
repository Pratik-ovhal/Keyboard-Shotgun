"""Main desktop GUI window for Keyboard Shotgun using PySide6."""

import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import ConfigManager
from core.event_handler import EventHandler
from core.keyboard_listener import KeyboardListener
from core.sound_engine import SoundEngine
from ui.styles import DARK_THEME_QSS
from ui.tray_manager import TrayManager, create_default_tray_icon

logger = logging.getLogger("KeyboardShotgun.MainWindow")


class MainWindow(QMainWindow):
    """Main window for Keyboard Shotgun settings and dashboard."""

    latency_updated = Signal(float)

    def __init__(
        self,
        config_manager: ConfigManager,
        sound_engine: SoundEngine,
        event_handler: EventHandler,
        keyboard_listener: KeyboardListener,
        tray_manager: TrayManager,
    ) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.sound_engine = sound_engine
        self.event_handler = event_handler
        self.keyboard_listener = keyboard_listener
        self.tray_manager = tray_manager

        self.setWindowTitle("Keyboard Shotgun")
        self.resize(520, 680)
        self.setMinimumSize(460, 560)
        self.setWindowIcon(create_default_tray_icon())

        self.setStyleSheet(DARK_THEME_QSS)

        self._force_quit: bool = False
        self._init_ui()
        self._load_config_to_ui()
        self._connect_signals()

        # Connect event handler sound played callback to update latency
        self.event_handler.on_sound_played = self._on_audio_worker_sound_played
        self.latency_updated.connect(self._update_latency_display)

        # Refresh status indicator
        self._update_status_indicator()

    def _init_ui(self) -> None:
        """Construct the UI widgets and layouts."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        # Header Title and Subtitle
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_label = QLabel("Keyboard Shotgun")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #f8fafc;")

        subtitle_label = QLabel("Tactile shotgun audio on every physical keystroke")
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 12px;")

        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Status badge indicator
        self.status_badge = QLabel("Running")
        self.status_badge.setObjectName("statusPillRunning")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.status_badge)

        root_layout.addLayout(header_layout)

        # Dashboard Group
        dashboard_group = QGroupBox("Dashboard")
        dashboard_layout = QVBoxLayout(dashboard_group)
        dashboard_layout.setSpacing(12)

        # Primary controls row (Start, Stop, Mute, Test)
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("primaryBtn")

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("dangerBtn")

        self.btn_mute = QPushButton("Mute")
        self.btn_test = QPushButton("Test Sound")

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(self.btn_mute)
        btn_row.addWidget(self.btn_test)
        dashboard_layout.addLayout(btn_row)

        # Volume slider row
        vol_box = QVBoxLayout()
        vol_label_row = QHBoxLayout()
        vol_title = QLabel("Master Volume")
        vol_title.setStyleSheet("font-weight: 500;")
        self.vol_value_label = QLabel("80%")
        self.vol_value_label.setStyleSheet("color: #60a5fa; font-weight: 600;")
        vol_label_row.addWidget(vol_title)
        vol_label_row.addStretch()
        vol_label_row.addWidget(self.vol_value_label)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)

        vol_box.addLayout(vol_label_row)
        vol_box.addWidget(self.vol_slider)
        dashboard_layout.addLayout(vol_box)

        # Latency & Benchmark Display Row
        latency_frame = QFrame()
        latency_frame.setStyleSheet("background-color: #12141a; border-radius: 6px; padding: 6px;")
        latency_layout = QGridLayout(latency_frame)
        latency_layout.setContentsMargins(8, 6, 8, 6)

        lbl_delay_title = QLabel("Software Processing Delay:")
        lbl_delay_title.setObjectName("metricLabel")
        self.lbl_delay_val = QLabel("< 1.0 ms")
        self.lbl_delay_val.setObjectName("metricValue")

        lbl_avg_title = QLabel("Avg Processing Delay:")
        lbl_avg_title.setObjectName("metricLabel")
        self.lbl_avg_val = QLabel("< 1.0 ms")
        self.lbl_avg_val.setObjectName("metricValue")

        note_label = QLabel("* Measured from key detection to audio dispatch. Excludes physical DAC/speaker hardware delay.")
        note_label.setStyleSheet("color: #64748b; font-size: 10px; font-style: italic;")

        latency_layout.addWidget(lbl_delay_title, 0, 0)
        latency_layout.addWidget(self.lbl_delay_val, 0, 1)
        latency_layout.addWidget(lbl_avg_title, 0, 2)
        latency_layout.addWidget(self.lbl_avg_val, 0, 3)
        latency_layout.addWidget(note_label, 1, 0, 1, 4)

        dashboard_layout.addWidget(latency_frame)
        root_layout.addWidget(dashboard_group)

        # Tabs for Settings (Audio Settings & General Settings)
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #262b36;
                background-color: #181a20;
                border-radius: 8px;
                padding: 10px;
            }
            QTabBar::tab {
                background: #14161c;
                color: #94a3b8;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #181a20;
                color: #60a5fa;
                font-weight: 600;
            }
        """)

        # Tab 1: Audio Settings
        audio_tab = QWidget()
        audio_layout = QVBoxLayout(audio_tab)
        audio_layout.setSpacing(12)

        self.cb_pitch_variation = QCheckBox("Enable Pitch Variation (Natural Nuance)")
        audio_layout.addWidget(self.cb_pitch_variation)

        # Pitch Intensity
        intensity_layout = QHBoxLayout()
        intensity_label = QLabel("Pitch Variation Intensity (±%)")
        self.spin_intensity = QSpinBox()
        self.spin_intensity.setRange(1, 30)
        self.spin_intensity.setValue(8)
        self.spin_intensity.setSuffix(" %")
        intensity_layout.addWidget(intensity_label)
        intensity_layout.addStretch()
        intensity_layout.addWidget(self.spin_intensity)
        audio_layout.addLayout(intensity_layout)

        # Pre-generated variations count
        variations_layout = QHBoxLayout()
        variations_label = QLabel("Pre-generated Variations (in memory)")
        self.spin_variations = QSpinBox()
        self.spin_variations.setRange(8, 16)
        self.spin_variations.setValue(10)
        variations_layout.addWidget(variations_label)
        variations_layout.addStretch()
        variations_layout.addWidget(self.spin_variations)
        audio_layout.addLayout(variations_layout)

        # Max Simultaneous Sounds
        channels_layout = QHBoxLayout()
        channels_label = QLabel("Maximum Simultaneous Sounds (Channels)")
        self.spin_channels = QSpinBox()
        self.spin_channels.setRange(4, 32)
        self.spin_channels.setValue(8)
        channels_layout.addWidget(channels_label)
        channels_layout.addStretch()
        channels_layout.addWidget(self.spin_channels)
        audio_layout.addLayout(channels_layout)

        # Cooldown duration
        cooldown_layout = QHBoxLayout()
        cooldown_label = QLabel("Cooldown Between Sounds (Seconds)")
        self.spin_cooldown = QDoubleSpinBox()
        self.spin_cooldown.setRange(0.0, 1.0)
        self.spin_cooldown.setSingleStep(0.01)
        self.spin_cooldown.setDecimals(2)
        self.spin_cooldown.setValue(0.0)
        self.spin_cooldown.setSuffix(" s")
        cooldown_layout.addWidget(cooldown_label)
        cooldown_layout.addStretch()
        cooldown_layout.addWidget(self.spin_cooldown)
        audio_layout.addLayout(cooldown_layout)

        audio_layout.addStretch()
        tabs.addTab(audio_tab, "Audio Settings")

        # Tab 2: General Settings
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setSpacing(14)

        self.cb_start_in_background = QCheckBox("Start application in background")
        self.cb_minimize_to_tray = QCheckBox("Minimize to system tray instead of exiting")
        self.cb_launch_on_startup = QCheckBox("Launch on system startup (Windows / macOS)")
        self.cb_show_permissions_notify = QCheckBox("Show notifications when permissions are missing")

        general_layout.addWidget(self.cb_start_in_background)
        general_layout.addWidget(self.cb_minimize_to_tray)
        general_layout.addWidget(self.cb_launch_on_startup)
        general_layout.addWidget(self.cb_show_permissions_notify)
        general_layout.addStretch()
        tabs.addTab(general_tab, "General Settings")

        root_layout.addWidget(tabs)

    def _load_config_to_ui(self) -> None:
        """Populate UI controls from ConfigManager."""
        cfg = self.config_manager.get_all()

        vol = int(round(cfg.get("master_volume", 0.8) * 100))
        self.vol_slider.setValue(vol)
        self.vol_value_label.setText(f"{vol}%")

        is_muted = cfg.get("is_muted", False)
        self.btn_mute.setText("Unmute" if is_muted else "Mute")

        self.cb_pitch_variation.setChecked(cfg.get("pitch_variation_enabled", True))
        self.spin_intensity.setValue(int(round(cfg.get("pitch_intensity", 0.08) * 100)))
        self.spin_variations.setValue(cfg.get("num_variations", 10))
        self.spin_channels.setValue(cfg.get("max_channels", 8))
        self.spin_cooldown.setValue(cfg.get("cooldown_duration", 0.0))

        self.cb_start_in_background.setChecked(cfg.get("start_in_background", False))
        self.cb_minimize_to_tray.setChecked(cfg.get("minimize_to_tray", True))
        self.cb_launch_on_startup.setChecked(cfg.get("launch_on_startup", False))
        self.cb_show_permissions_notify.setChecked(cfg.get("show_permission_notifications", True))

    def _connect_signals(self) -> None:
        """Connect UI signals to corresponding handler actions."""
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_mute.clicked.connect(self._on_mute_clicked)
        self.btn_test.clicked.connect(self._on_test_clicked)

        self.vol_slider.valueChanged.connect(self._on_volume_changed)

        self.cb_pitch_variation.toggled.connect(self._on_pitch_variation_toggled)
        self.spin_intensity.valueChanged.connect(self._on_pitch_intensity_changed)
        self.spin_variations.valueChanged.connect(self._on_variations_count_changed)
        self.spin_channels.valueChanged.connect(self._on_max_channels_changed)
        self.spin_cooldown.valueChanged.connect(self._on_cooldown_changed)

        self.cb_start_in_background.toggled.connect(
            lambda val: self.config_manager.set("start_in_background", val)
        )
        self.cb_minimize_to_tray.toggled.connect(
            lambda val: self.config_manager.set("minimize_to_tray", val)
        )
        self.cb_launch_on_startup.toggled.connect(self._on_launch_on_startup_toggled)
        self.cb_show_permissions_notify.toggled.connect(
            lambda val: self.config_manager.set("show_permission_notifications", val)
        )

        # Tray signals
        self.tray_manager.show_window_requested.connect(self.show_and_activate)
        self.tray_manager.toggle_pause_requested.connect(self._on_toggle_pause)
        self.tray_manager.exit_requested.connect(self.force_exit)

    def _on_start_clicked(self) -> None:
        """Start or resume the keyboard listener and event pipeline."""
        if not self.sound_engine.is_ready():
            # Attempt to reload shotgun.wav in case user placed it after startup
            try:
                from main import get_asset_path
                audio_path = get_asset_path("shotgun.wav")
            except Exception:
                audio_path = Path(__file__).resolve().parent.parent / "shotgun.wav"

            try:
                self.sound_engine.load_audio(audio_path)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Missing or Invalid Audio File",
                    f"Cannot start Keyboard Shotgun:\n\n{e}\n\n"
                    f"Please place 'shotgun.wav' in the application directory:\n{audio_path.resolve()}"
                )
                return

        if not self.keyboard_listener.is_running():
            success = self.keyboard_listener.start()
            if not success:
                QMessageBox.warning(
                    self,
                    "Permission / Start Error",
                    "Could not start global keyboard listener. Please check permissions."
                )
        self.event_handler.resume()
        self._update_status_indicator()

    def _on_stop_clicked(self) -> None:
        """Stop keyboard listener."""
        self.keyboard_listener.stop()
        self.event_handler.pause()
        self._update_status_indicator()

    def _on_mute_clicked(self) -> None:
        """Toggle master mute state."""
        new_muted = not self.sound_engine.is_muted
        self.sound_engine.set_mute(new_muted)
        self.config_manager.set("is_muted", new_muted)
        self.btn_mute.setText("Unmute" if new_muted else "Mute")
        self._update_status_indicator()

    def _on_test_clicked(self) -> None:
        """Trigger a test sound and display the software processing latency."""
        if not self.sound_engine.is_ready():
            try:
                from main import get_asset_path
                audio_path = get_asset_path("shotgun.wav")
            except Exception:
                audio_path = Path(__file__).resolve().parent.parent / "shotgun.wav"

            try:
                self.sound_engine.load_audio(audio_path)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Audio Asset Missing",
                    f"Cannot test sound: 'shotgun.wav' was not found or is corrupted.\n\n{e}"
                )
                return

        latency_ms = self.event_handler.trigger_test_sound()
        self._update_latency_display(latency_ms)

    def _on_volume_changed(self, value: int) -> None:
        """Handle master volume slider movement."""
        self.vol_value_label.setText(f"{value}%")
        float_vol = value / 100.0
        self.sound_engine.set_volume(float_vol)
        self.config_manager.set("master_volume", float_vol)

    def _on_pitch_variation_toggled(self, checked: bool) -> None:
        """Handle pitch variation toggle."""
        self.sound_engine.set_pitch_variation_enabled(checked)
        self.config_manager.set("pitch_variation_enabled", checked)
        self.sound_engine.generate_variations()

    def _on_pitch_intensity_changed(self, val: int) -> None:
        """Handle pitch variation intensity change."""
        intensity = val / 100.0
        self.config_manager.set("pitch_intensity", intensity)
        self.sound_engine.generate_variations(intensity=intensity)

    def _on_variations_count_changed(self, val: int) -> None:
        """Handle pre-generated variation count change."""
        self.config_manager.set("num_variations", val)
        self.sound_engine.generate_variations(num_variations=val)

    def _on_max_channels_changed(self, val: int) -> None:
        """Handle channel count adjustment."""
        self.config_manager.set("max_channels", val)
        self.sound_engine.set_max_channels(val)

    def _on_cooldown_changed(self, val: float) -> None:
        """Handle cooldown adjustment."""
        self.config_manager.set("cooldown_duration", val)

    def _on_launch_on_startup_toggled(self, checked: bool) -> None:
        """Configure system startup integration."""
        self.config_manager.set("launch_on_startup", checked)
        if sys.platform == "win32":
            from platform.windows import set_launch_on_startup
            set_launch_on_startup(checked)
        elif sys.platform == "darwin":
            from platform.macos import set_launch_on_startup
            set_launch_on_startup(checked)

    def _on_toggle_pause(self) -> None:
        """Toggle pause state from tray menu."""
        if self.event_handler.is_paused():
            self.event_handler.resume()
        else:
            self.event_handler.pause()
        self._update_status_indicator()

    def _on_audio_worker_sound_played(self, latency_ms: float) -> None:
        """Thread-safe signal emission from worker thread."""
        self.latency_updated.emit(latency_ms)

    def _update_latency_display(self, latency_ms: float) -> None:
        """Update latency text in the UI."""
        self.lbl_delay_val.setText(f"{latency_ms:.2f} ms")
        avg = self.sound_engine.average_software_latency_ms
        self.lbl_avg_val.setText(f"{avg:.2f} ms")

    def _update_status_indicator(self) -> None:
        """Update status pill and button states."""
        is_ready = self.sound_engine.is_ready()
        is_running = self.keyboard_listener.is_running()
        is_paused = self.event_handler.is_paused()
        is_muted = self.sound_engine.is_muted

        if not is_ready:
            self.status_badge.setText("Missing Audio")
            self.status_badge.setObjectName("statusPillStopped")
        elif is_muted:
            self.status_badge.setText("Muted")
            self.status_badge.setObjectName("statusPillPaused")
        elif not is_running:
            self.status_badge.setText("Stopped")
            self.status_badge.setObjectName("statusPillStopped")
        elif is_paused:
            self.status_badge.setText("Paused")
            self.status_badge.setObjectName("statusPillPaused")
        else:
            self.status_badge.setText("Running")
            self.status_badge.setObjectName("statusPillRunning")

        # Force stylesheet re-polish for dynamic objectName change
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

        self.btn_start.setEnabled(not is_running or is_paused or not is_ready)
        self.btn_stop.setEnabled(is_running and not is_paused)

        self.tray_manager.update_status(is_running, is_paused)

    def show_and_activate(self) -> None:
        """Show window and bring to foreground."""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close: minimize to tray if enabled, or quit application."""
        if self._force_quit:
            event.accept()
            return

        minimize_to_tray = self.config_manager.get("minimize_to_tray", True)
        if minimize_to_tray:
            event.ignore()
            self.hide()
            self.tray_manager.show_message(
                "Keyboard Shotgun",
                "Application is still active in the background. Right-click the tray icon to exit."
            )
        else:
            event.accept()
            self.force_exit()

    def force_exit(self) -> None:
        """Perform full cleanup and terminate application."""
        self._force_quit = True
        logger.info("Exiting Keyboard Shotgun...")
        self.keyboard_listener.stop()
        self.event_handler.stop()
        self.sound_engine.cleanup()
        self.tray_manager.hide()
        QApplication.instance().quit()

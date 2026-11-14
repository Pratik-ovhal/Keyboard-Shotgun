"""Main desktop GUI window for Keyboard Shotgun using PySide6.

Features a modern dark interface inspired by high-end audio software,
with sidebar navigation, animated visualizer, and organized control cards.
"""

import logging
import platform as sys_platform
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QCloseEvent, QDesktopServices, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.assets import get_asset_path
from core.config_manager import ConfigManager
from core.event_handler import EventHandler
from core.keyboard_listener import KeyboardListener
from core.sound_engine import SoundEngine
from ui.components.icons import (
    get_about_icon,
    get_github_icon,
    get_home_icon,
    get_power_icon,
    get_settings_icon,
    get_speaker_icon,
)
from ui.components.toggle_switch import ToggleSwitch
from ui.components.wave_visualizer import SoundWaveVisualizer
from ui.styles import DARK_THEME_QSS
from ui.tray_manager import TrayManager, create_default_tray_icon

logger = logging.getLogger("KeyboardShotgun.MainWindow")


class MainWindow(QMainWindow):
    """Modern main window for Keyboard Shotgun desktop application."""

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
        self.resize(680, 720)
        self.setMinimumSize(580, 600)
        self.setWindowIcon(create_default_tray_icon())

        self.setStyleSheet(DARK_THEME_QSS)

        self._force_quit: bool = False
        self._init_ui()
        self._load_config_to_ui()
        self._connect_signals()

        # Connect event handler sound played callback to update latency & wave
        self.event_handler.on_sound_played = self._on_audio_worker_sound_played
        self.latency_updated.connect(self._update_latency_display)

        # Refresh status indicator
        self._update_status_indicator()

    # -------------------------------------------------------------------------
    # UI Construction
    # -------------------------------------------------------------------------

    def _init_ui(self) -> None:
        """Construct the sidebar navigation and stacked content pages."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Navigation Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # 2. Right Stacked Pages
        self.stack = QStackedWidget()
        self.page_home = self._create_home_page()
        self.page_settings = self._create_settings_page()
        self.page_about = self._create_about_page()

        self.stack.addWidget(self.page_home)      # Index 0
        self.stack.addWidget(self.page_settings)  # Index 1
        self.stack.addWidget(self.page_about)     # Index 2

        main_layout.addWidget(self.stack, 1)

    def _create_sidebar(self) -> QWidget:
        """Create the compact, sleek navigation sidebar."""
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebarFrame")
        sidebar_frame.setFixedWidth(175)

        layout = QVBoxLayout(sidebar_frame)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(8)

        # Brand header
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(10)

        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            brand_logo = QLabel()
            brand_pix = QPixmap(str(logo_path.resolve())).scaled(
                22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            brand_logo.setPixmap(brand_pix)
            brand_logo.setStyleSheet("background-color: #FFFFFF; border-radius: 4px; padding: 1px;")
            brand_layout.addWidget(brand_logo)
        else:
            brand_dot = QFrame()
            brand_dot.setFixedSize(10, 10)
            brand_dot.setStyleSheet("background-color: #D4F63D; border-radius: 5px;")
            brand_layout.addWidget(brand_dot)

        brand_label = QLabel("Shotgun")
        brand_font = QFont()
        brand_font.setPointSize(14)
        brand_font.setBold(True)
        brand_label.setFont(brand_font)
        brand_label.setStyleSheet("color: #FFFFFF; letter-spacing: 0.5px;")

        brand_layout.addWidget(brand_label)
        brand_layout.addStretch()

        layout.addLayout(brand_layout)
        layout.addSpacing(22)

        # Navigation buttons
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_nav_home = QPushButton("  Home")
        self.btn_nav_home.setObjectName("navBtn")
        self.btn_nav_home.setIcon(get_home_icon("#8E94A5", 18))
        self.btn_nav_home.setIconSize(QSize(18, 18))
        self.btn_nav_home.setCheckable(True)
        self.btn_nav_home.setChecked(True)
        self.nav_group.addButton(self.btn_nav_home, 0)
        layout.addWidget(self.btn_nav_home)

        self.btn_nav_settings = QPushButton("  Settings")
        self.btn_nav_settings.setObjectName("navBtn")
        self.btn_nav_settings.setIcon(get_settings_icon("#8E94A5", 18))
        self.btn_nav_settings.setIconSize(QSize(18, 18))
        self.btn_nav_settings.setCheckable(True)
        self.nav_group.addButton(self.btn_nav_settings, 1)
        layout.addWidget(self.btn_nav_settings)

        self.btn_nav_about = QPushButton("  About")
        self.btn_nav_about.setObjectName("navBtn")
        self.btn_nav_about.setIcon(get_about_icon("#8E94A5", 18))
        self.btn_nav_about.setIconSize(QSize(18, 18))
        self.btn_nav_about.setCheckable(True)
        self.nav_group.addButton(self.btn_nav_about, 2)
        layout.addWidget(self.btn_nav_about)

        layout.addStretch()

        # Sidebar footer
        footer_label = QLabel("v1.2.0 • Active")
        footer_label.setStyleSheet("color: #4C5264; font-size: 11px;")
        layout.addWidget(footer_label)

        # Connect button group switching
        self.nav_group.idClicked.connect(self._on_nav_changed)

        return sidebar_frame

    def _on_nav_changed(self, idx: int) -> None:
        """Switch stacked page and update active icon highlight."""
        self.stack.setCurrentIndex(idx)

        # Update icons for active/inactive contrast
        self.btn_nav_home.setIcon(
            get_home_icon("#D4F63D" if idx == 0 else "#8E94A5", 18)
        )
        self.btn_nav_settings.setIcon(
            get_settings_icon("#D4F63D" if idx == 1 else "#8E94A5", 18)
        )
        self.btn_nav_about.setIcon(
            get_about_icon("#D4F63D" if idx == 2 else "#8E94A5", 18)
        )

    # -------------------------------------------------------------------------
    # Screen 1: Home / Dashboard
    # -------------------------------------------------------------------------

    def _create_home_page(self) -> QWidget:
        """Create the clean, uncluttered Home / Dashboard screen."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(20)

        # Header: Branding and Status Badge
        header_layout = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(3)

        title = QLabel("Keyboard Shotgun")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #FFFFFF;")

        subtitle = QLabel("Tactile shotgun audio on every physical keystroke")
        subtitle.setStyleSheet("color: #7D8496; font-size: 12px;")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header_layout.addLayout(header_text)
        header_layout.addStretch()

        self.status_badge = QLabel("Running")
        self.status_badge.setObjectName("statusPillRunning")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.status_badge)

        layout.addLayout(header_layout)

        # Hero Card: Focal Point with Visualizer & Hero Action Control
        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 32, 24, 32)
        hero_layout.setSpacing(20)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Audio Wave Visualizer
        self.wave_visualizer = SoundWaveVisualizer(bar_count=9, accent_color="#D4F63D")
        self.wave_visualizer.setFixedHeight(46)
        self.wave_visualizer.setFixedWidth(160)
        hero_layout.addWidget(self.wave_visualizer, 0, Qt.AlignmentFlag.AlignCenter)

        # Hero Action Control (Prominent Start / Stop toggle)
        self.btn_hero = QPushButton("  STOP ENGINE")
        self.btn_hero.setObjectName("heroActionBtnRunning")
        self.btn_hero.setIcon(get_power_icon("#0C0D11", 20))
        self.btn_hero.setIconSize(QSize(20, 20))
        self.btn_hero.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hero.setFixedHeight(50)
        self.btn_hero.setMinimumWidth(240)
        self.btn_hero.clicked.connect(self._on_hero_action_clicked)
        hero_layout.addWidget(self.btn_hero, 0, Qt.AlignmentFlag.AlignCenter)

        # Secondary Start / Stop controls (for backwards compatibility and direct clicks)
        btn_sub_row = QHBoxLayout()
        btn_sub_row.setSpacing(12)
        btn_sub_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_start = QPushButton("Start Listener")
        self.btn_start.setObjectName("secondaryBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_stop = QPushButton("Stop Listener")
        self.btn_stop.setObjectName("secondaryBtn")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_sub_row.addWidget(self.btn_start)
        btn_sub_row.addWidget(self.btn_stop)
        hero_layout.addLayout(btn_sub_row)

        layout.addWidget(hero_card)

        # Master Volume & Audition Card
        vol_card = QFrame()
        vol_card.setObjectName("settingsCard")
        vol_layout = QVBoxLayout(vol_card)
        vol_layout.setContentsMargins(20, 18, 20, 18)
        vol_layout.setSpacing(14)

        # Volume Header
        vol_header = QHBoxLayout()
        vol_speaker_icon = QLabel()
        vol_speaker_icon.setPixmap(get_speaker_icon("#D4F63D", False, 20).pixmap(20, 20))

        vol_title = QLabel("Master Volume")
        vol_title.setObjectName("settingItemTitle")

        self.vol_value_label = QLabel("80%")
        self.vol_value_label.setObjectName("valueBadge")

        vol_header.addWidget(vol_speaker_icon)
        vol_header.addWidget(vol_title)
        vol_header.addStretch()
        vol_header.addWidget(self.vol_value_label)
        vol_layout.addLayout(vol_header)

        # Slider
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        vol_layout.addWidget(self.vol_slider)

        # Quick Actions Row (Mute & Audition Sound)
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        self.btn_mute = QPushButton("Mute Audio")
        self.btn_mute.setObjectName("pillBtn")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setIcon(get_speaker_icon("#A6ABB9", False, 16))
        self.btn_mute.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_test = QPushButton("Audition Sound")
        self.btn_test.setObjectName("pillBtn")
        self.btn_test.setCursor(Qt.CursorShape.PointingHandCursor)

        actions_row.addWidget(self.btn_mute)
        actions_row.addWidget(self.btn_test)
        actions_row.addStretch()
        vol_layout.addLayout(actions_row)

        layout.addWidget(vol_card)
        layout.addStretch()

        return page

    # -------------------------------------------------------------------------
    # Screen 2: Settings
    # -------------------------------------------------------------------------

    def _create_settings_page(self) -> QWidget:
        """Create the organized Settings screen with cards and modern controls."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(20)

        # Page Header
        header_text = QVBoxLayout()
        header_text.setSpacing(3)
        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #FFFFFF;")

        subtitle = QLabel("Fine-tune acoustic variation, playback channels, and system integration")
        subtitle.setStyleSheet("color: #7D8496; font-size: 12px;")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        layout.addLayout(header_text)

        # Card 1: Audio Acoustics
        card_audio = QFrame()
        card_audio.setObjectName("settingsCard")
        audio_layout = QVBoxLayout(card_audio)
        audio_layout.setContentsMargins(20, 18, 20, 18)
        audio_layout.setSpacing(16)

        card_title = QLabel("AUDIO ACOUSTICS")
        card_title.setObjectName("sectionTitle")
        audio_layout.addWidget(card_title)

        # Pitch variation switch
        row_pv = QHBoxLayout()
        text_box_pv = QVBoxLayout()
        lbl_pv_title = QLabel("Natural Pitch Variation")
        lbl_pv_title.setObjectName("settingItemTitle")
        lbl_pv_desc = QLabel("Applies subtle pitch micro-tuning to each keystroke for realism")
        lbl_pv_desc.setObjectName("settingItemDesc")
        text_box_pv.addWidget(lbl_pv_title)
        text_box_pv.addWidget(lbl_pv_desc)

        self.cb_pitch_variation = ToggleSwitch(active_color="#D4F63D")
        row_pv.addLayout(text_box_pv)
        row_pv.addStretch()
        row_pv.addWidget(self.cb_pitch_variation)
        audio_layout.addLayout(row_pv)

        # Pitch Variation Intensity Slider
        row_pi = QVBoxLayout()
        pi_header = QHBoxLayout()
        text_box_pi = QVBoxLayout()
        lbl_pi_title = QLabel("Variation Intensity (±%)")
        lbl_pi_title.setObjectName("settingItemTitle")
        lbl_pi_desc = QLabel("Controls maximum pitch shift deviation")
        lbl_pi_desc.setObjectName("settingItemDesc")
        text_box_pi.addWidget(lbl_pi_title)
        text_box_pi.addWidget(lbl_pi_desc)

        self.lbl_intensity_val = QLabel("8%")
        self.lbl_intensity_val.setObjectName("valueBadge")
        pi_header.addLayout(text_box_pi)
        pi_header.addStretch()
        pi_header.addWidget(self.lbl_intensity_val)

        self.slider_pitch_intensity = QSlider(Qt.Orientation.Horizontal)
        self.slider_pitch_intensity.setRange(1, 30)
        self.slider_pitch_intensity.setValue(8)

        # Backwards-compatible spinbox attribute
        self.spin_intensity = QSpinBox()
        self.spin_intensity.setRange(1, 30)
        self.spin_intensity.setValue(8)
        self.spin_intensity.setVisible(False)

        row_pi.addLayout(pi_header)
        row_pi.addWidget(self.slider_pitch_intensity)
        audio_layout.addLayout(row_pi)

        # Pre-generated variations count
        row_var = QHBoxLayout()
        text_box_var = QVBoxLayout()
        lbl_var_title = QLabel("Pre-generated Variations")
        lbl_var_title.setObjectName("settingItemTitle")
        lbl_var_desc = QLabel("Number of unique pitch variations cached in RAM")
        lbl_var_desc.setObjectName("settingItemDesc")
        text_box_var.addWidget(lbl_var_title)
        text_box_var.addWidget(lbl_var_desc)

        self.spin_variations = QSpinBox()
        self.spin_variations.setRange(8, 16)
        self.spin_variations.setValue(10)
        self.spin_variations.setSuffix(" buffers")

        row_var.addLayout(text_box_var)
        row_var.addStretch()
        row_var.addWidget(self.spin_variations)
        audio_layout.addLayout(row_var)

        layout.addWidget(card_audio)

        # Card 2: Playback & Concurrency
        card_playback = QFrame()
        card_playback.setObjectName("settingsCard")
        play_layout = QVBoxLayout(card_playback)
        play_layout.setContentsMargins(20, 18, 20, 18)
        play_layout.setSpacing(16)

        card_title2 = QLabel("PLAYBACK & CONCURRENCY")
        card_title2.setObjectName("sectionTitle")
        play_layout.addWidget(card_title2)

        # Simultaneous channels
        row_chan = QHBoxLayout()
        text_box_chan = QVBoxLayout()
        lbl_chan_title = QLabel("Simultaneous Audio Channels")
        lbl_chan_title.setObjectName("settingItemTitle")
        lbl_chan_desc = QLabel("Hardware mixer channels for fast typing polyphony")
        lbl_chan_desc.setObjectName("settingItemDesc")
        text_box_chan.addWidget(lbl_chan_title)
        text_box_chan.addWidget(lbl_chan_desc)

        self.spin_channels = QSpinBox()
        self.spin_channels.setRange(4, 32)
        self.spin_channels.setValue(8)
        self.spin_channels.setSuffix(" channels")

        row_chan.addLayout(text_box_chan)
        row_chan.addStretch()
        row_chan.addWidget(self.spin_channels)
        play_layout.addLayout(row_chan)

        # Cooldown duration
        row_cd = QHBoxLayout()
        text_box_cd = QVBoxLayout()
        lbl_cd_title = QLabel("Keypress Sound Cooldown")
        lbl_cd_title.setObjectName("settingItemTitle")
        lbl_cd_desc = QLabel("Minimum interval between consecutive shotgun sounds")
        lbl_cd_desc.setObjectName("settingItemDesc")
        text_box_cd.addWidget(lbl_cd_title)
        text_box_cd.addWidget(lbl_cd_desc)

        self.spin_cooldown = QDoubleSpinBox()
        self.spin_cooldown.setRange(0.0, 1.0)
        self.spin_cooldown.setSingleStep(0.01)
        self.spin_cooldown.setDecimals(2)
        self.spin_cooldown.setValue(0.0)
        self.spin_cooldown.setSuffix(" s")

        row_cd.addLayout(text_box_cd)
        row_cd.addStretch()
        row_cd.addWidget(self.spin_cooldown)
        play_layout.addLayout(row_cd)

        # Quick Test Button in Settings
        row_test_btn = QHBoxLayout()
        self.btn_test_settings = QPushButton("Audition Settings")
        self.btn_test_settings.setObjectName("secondaryBtn")
        self.btn_test_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test_settings.clicked.connect(self._on_test_clicked)
        row_test_btn.addWidget(self.btn_test_settings)
        row_test_btn.addStretch()
        play_layout.addLayout(row_test_btn)

        layout.addWidget(card_playback)

        # Card 3: System Behavior
        card_sys = QFrame()
        card_sys.setObjectName("settingsCard")
        sys_layout = QVBoxLayout(card_sys)
        sys_layout.setContentsMargins(20, 18, 20, 18)
        sys_layout.setSpacing(16)

        card_title3 = QLabel("SYSTEM BEHAVIOR")
        card_title3.setObjectName("sectionTitle")
        sys_layout.addWidget(card_title3)

        # Start in background
        row_bg = QHBoxLayout()
        text_box_bg = QVBoxLayout()
        lbl_bg_title = QLabel("Start in Background")
        lbl_bg_title.setObjectName("settingItemTitle")
        lbl_bg_desc = QLabel("Launch directly into the system tray without showing this window")
        lbl_bg_desc.setObjectName("settingItemDesc")
        text_box_bg.addWidget(lbl_bg_title)
        text_box_bg.addWidget(lbl_bg_desc)
        self.cb_start_in_background = ToggleSwitch(active_color="#D4F63D")
        row_bg.addLayout(text_box_bg)
        row_bg.addStretch()
        row_bg.addWidget(self.cb_start_in_background)
        sys_layout.addLayout(row_bg)

        # Minimize to tray
        row_tray = QHBoxLayout()
        text_box_tray = QVBoxLayout()
        lbl_tray_title = QLabel("Minimize to System Tray")
        lbl_tray_title.setObjectName("settingItemTitle")
        lbl_tray_desc = QLabel("Closing the window keeps the engine active in the taskbar tray")
        lbl_tray_desc.setObjectName("settingItemDesc")
        text_box_tray.addWidget(lbl_tray_title)
        text_box_tray.addWidget(lbl_tray_desc)
        self.cb_minimize_to_tray = ToggleSwitch(active_color="#D4F63D")
        row_tray.addLayout(text_box_tray)
        row_tray.addStretch()
        row_tray.addWidget(self.cb_minimize_to_tray)
        sys_layout.addLayout(row_tray)

        # Launch on startup
        row_startup = QHBoxLayout()
        text_box_startup = QVBoxLayout()
        lbl_start_title = QLabel("Launch on System Startup")
        lbl_start_title.setObjectName("settingItemTitle")
        lbl_start_desc = QLabel("Automatically run Keyboard Shotgun when logging into your user account")
        lbl_start_desc.setObjectName("settingItemDesc")
        text_box_startup.addWidget(lbl_start_title)
        text_box_startup.addWidget(lbl_start_desc)
        self.cb_launch_on_startup = ToggleSwitch(active_color="#D4F63D")
        row_startup.addLayout(text_box_startup)
        row_startup.addStretch()
        row_startup.addWidget(self.cb_launch_on_startup)
        sys_layout.addLayout(row_startup)

        # Permission notifications
        row_notify = QHBoxLayout()
        text_box_notify = QVBoxLayout()
        lbl_notify_title = QLabel("Permission Notifications")
        lbl_notify_title.setObjectName("settingItemTitle")
        lbl_notify_desc = QLabel("Show desktop alerts when system input privileges are missing")
        lbl_notify_desc.setObjectName("settingItemDesc")
        text_box_notify.addWidget(lbl_notify_title)
        text_box_notify.addWidget(lbl_notify_desc)
        self.cb_show_permissions_notify = ToggleSwitch(active_color="#D4F63D")
        row_notify.addLayout(text_box_notify)
        row_notify.addStretch()
        row_notify.addWidget(self.cb_show_permissions_notify)
        sys_layout.addLayout(row_notify)

        layout.addWidget(card_sys)
        layout.addStretch()

        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------------------
    # Screen 3: About
    # -------------------------------------------------------------------------

    def _create_about_page(self) -> QWidget:
        """Create the clean About screen with system diagnostics."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(20)

        # Page Header
        header_text = QVBoxLayout()
        header_text.setSpacing(3)
        title = QLabel("About")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #FFFFFF;")

        subtitle = QLabel("Application identity, live diagnostics, and open-source project info")
        subtitle.setStyleSheet("color: #7D8496; font-size: 12px;")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        layout.addLayout(header_text)

        # Card 1: App Identity
        card_identity = QFrame()
        card_identity.setObjectName("settingsCard")
        id_layout = QVBoxLayout(card_identity)
        id_layout.setContentsMargins(22, 22, 22, 22)
        id_layout.setSpacing(14)

        header_brand_row = QHBoxLayout()
        header_brand_row.setSpacing(16)

        logo_path = get_asset_path("logo.png")
        if logo_path.exists():
            about_logo_lbl = QLabel()
            about_logo_pix = QPixmap(str(logo_path.resolve())).scaled(
                56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            about_logo_lbl.setPixmap(about_logo_pix)
            about_logo_lbl.setFixedSize(56, 56)
            about_logo_lbl.setStyleSheet("background-color: #FFFFFF; border-radius: 10px; padding: 3px;")
            header_brand_row.addWidget(about_logo_lbl)

        id_text_box = QVBoxLayout()
        id_text_box.setSpacing(3)

        app_name_lbl = QLabel("Keyboard Shotgun")
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        app_name_lbl.setFont(name_font)
        app_name_lbl.setStyleSheet("color: #FFFFFF;")

        ver_lbl = QLabel("Version 1.2.0 • Standalone Production Release")
        ver_lbl.setStyleSheet("color: #D4F63D; font-weight: 600; font-size: 12px;")

        id_text_box.addWidget(app_name_lbl)
        id_text_box.addWidget(ver_lbl)
        header_brand_row.addLayout(id_text_box)
        header_brand_row.addStretch()

        id_layout.addLayout(header_brand_row)

        desc_lbl = QLabel(
            "A high-performance tactile desktop audio utility that delivers dynamic, "
            "low-latency shotgun acoustic feedback for every physical keystroke. Built for "
            "mechanical keyboard enthusiasts and desktop customization."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #949BAE; line-height: 1.4; font-size: 13px;")

        btn_github = QPushButton("  GitHub Repository")
        btn_github.setObjectName("secondaryBtn")
        btn_github.setIcon(get_github_icon("#FFFFFF", 18))
        btn_github.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_github.setFixedWidth(180)
        btn_github.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/Pratik-ovhal/Keyboard-Shotgun"))
        )

        id_layout.addWidget(app_name_lbl)
        id_layout.addWidget(ver_lbl)
        id_layout.addWidget(desc_lbl)
        id_layout.addWidget(btn_github)
        layout.addWidget(card_identity)

        # Card 2: System Diagnostics & Metrics
        card_metrics = QFrame()
        card_metrics.setObjectName("metricCard")
        metrics_layout = QVBoxLayout(card_metrics)
        metrics_layout.setContentsMargins(20, 18, 20, 18)
        metrics_layout.setSpacing(14)

        diag_title = QLabel("SYSTEM DIAGNOSTICS & PERFORMANCE")
        diag_title.setObjectName("sectionTitle")
        metrics_layout.addWidget(diag_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)

        # Latency metrics moved from home dashboard to keep main screen clean
        lbl_delay_title = QLabel("Last Key Processing Delay:")
        lbl_delay_title.setStyleSheet("color: #7D8496; font-size: 12px;")
        self.lbl_delay_val = QLabel("< 1.0 ms")
        self.lbl_delay_val.setObjectName("valueBadge")

        lbl_avg_title = QLabel("Average Processing Delay:")
        lbl_avg_title.setStyleSheet("color: #7D8496; font-size: 12px;")
        self.lbl_avg_val = QLabel("< 1.0 ms")
        self.lbl_avg_val.setObjectName("valueBadge")

        lbl_buffer_title = QLabel("Audio Mixer Config:")
        lbl_buffer_title.setStyleSheet("color: #7D8496; font-size: 12px;")
        lbl_buffer_val = QLabel("44.1 kHz • 16-bit Stereo • 512 Buffer")
        lbl_buffer_val.setStyleSheet("color: #FFFFFF; font-weight: 500;")

        lbl_plat_title = QLabel("Platform Subsystem:")
        lbl_plat_title.setStyleSheet("color: #7D8496; font-size: 12px;")
        lbl_plat_val = QLabel(f"{sys_platform.system()} {sys_platform.release()} ({sys_platform.machine()})")
        lbl_plat_val.setStyleSheet("color: #FFFFFF; font-weight: 500;")

        grid.addWidget(lbl_delay_title, 0, 0)
        grid.addWidget(self.lbl_delay_val, 0, 1)
        grid.addWidget(lbl_avg_title, 1, 0)
        grid.addWidget(self.lbl_avg_val, 1, 1)
        grid.addWidget(lbl_buffer_title, 2, 0)
        grid.addWidget(lbl_buffer_val, 2, 1)
        grid.addWidget(lbl_plat_title, 3, 0)
        grid.addWidget(lbl_plat_val, 3, 1)

        metrics_layout.addLayout(grid)

        note_label = QLabel("* Processing delay is measured from key detection hook to audio buffer dispatch.")
        note_label.setStyleSheet("color: #555C6F; font-size: 11px; font-style: italic;")
        metrics_layout.addWidget(note_label)

        layout.addWidget(card_metrics)

        # Card 3: License & Credits
        card_license = QFrame()
        card_license.setObjectName("settingsCard")
        lic_layout = QVBoxLayout(card_license)
        lic_layout.setContentsMargins(20, 18, 20, 18)
        lic_layout.setSpacing(6)

        lic_title = QLabel("LICENSE & ACKNOWLEDGMENTS")
        lic_title.setObjectName("sectionTitle")

        lic_text = QLabel(
            "Released under the MIT License. Built with PySide6 (Qt for Python), "
            "pygame.mixer, NumPy acoustic pitch algorithms, and pynput global hooks."
        )
        lic_text.setWordWrap(True)
        lic_text.setStyleSheet("color: #7D8496; font-size: 12px;")

        lic_layout.addWidget(lic_title)
        lic_layout.addWidget(lic_text)
        layout.addWidget(card_license)

        layout.addStretch()

        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------------------
    # Configuration Sync
    # -------------------------------------------------------------------------

    def _load_config_to_ui(self) -> None:
        """Populate UI controls from ConfigManager."""
        cfg = self.config_manager.get_all()

        vol = int(round(cfg.get("master_volume", 0.8) * 100))
        self.vol_slider.setValue(vol)
        self.vol_value_label.setText(f"{vol}%")

        is_muted = cfg.get("is_muted", False)
        self.btn_mute.setChecked(is_muted)
        self.btn_mute.setText("Unmute" if is_muted else "Mute Audio")
        self.btn_mute.setIcon(get_speaker_icon("#F43F5E" if is_muted else "#A6ABB9", is_muted, 16))

        pv_enabled = cfg.get("pitch_variation_enabled", True)
        self.cb_pitch_variation.setChecked(pv_enabled)

        intensity = int(round(cfg.get("pitch_intensity", 0.08) * 100))
        self.slider_pitch_intensity.setValue(intensity)
        self.spin_intensity.setValue(intensity)
        self.lbl_intensity_val.setText(f"{intensity}%")

        self.spin_variations.setValue(cfg.get("num_variations", 10))
        self.spin_channels.setValue(cfg.get("max_channels", 8))
        self.spin_cooldown.setValue(cfg.get("cooldown_duration", 0.0))

        self.cb_start_in_background.setChecked(cfg.get("start_in_background", False))
        self.cb_minimize_to_tray.setChecked(cfg.get("minimize_to_tray", True))
        self.cb_launch_on_startup.setChecked(cfg.get("launch_on_startup", False))
        self.cb_show_permissions_notify.setChecked(cfg.get("show_permission_notifications", True))

    def _connect_signals(self) -> None:
        """Connect UI signals to corresponding handler actions."""
        # Home controls
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_mute.clicked.connect(self._on_mute_clicked)
        self.btn_test.clicked.connect(self._on_test_clicked)

        self.vol_slider.valueChanged.connect(self._on_volume_changed)

        # Settings controls
        self.cb_pitch_variation.toggled.connect(self._on_pitch_variation_toggled)

        self.slider_pitch_intensity.valueChanged.connect(self._on_intensity_slider_changed)
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

    # -------------------------------------------------------------------------
    # Action Handlers
    # -------------------------------------------------------------------------

    def _on_hero_action_clicked(self) -> None:
        """Toggle engine state from the prominent hero control."""
        is_running = self.keyboard_listener.is_running()
        is_paused = self.event_handler.is_paused()

        if is_running and not is_paused:
            self._on_stop_clicked()
        else:
            self._on_start_clicked()

    def _on_start_clicked(self) -> None:
        """Start or resume the keyboard listener and event pipeline."""
        if not self.sound_engine.is_ready():
            audio_path = get_asset_path("shotgun.wav")
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
        self.event_handler.start()
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

        self.btn_mute.setChecked(new_muted)
        self.btn_mute.setText("Unmute" if new_muted else "Mute Audio")
        self.btn_mute.setIcon(get_speaker_icon("#F43F5E" if new_muted else "#A6ABB9", new_muted, 16))
        self._update_status_indicator()

    def _on_test_clicked(self) -> None:
        """Trigger a test sound and display the software processing latency."""
        if not self.sound_engine.is_ready():
            audio_path = get_asset_path("shotgun.wav")
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

    def _on_intensity_slider_changed(self, val: int) -> None:
        """Handle intensity slider and sync with spinbox and label."""
        self.lbl_intensity_val.setText(f"{val}%")
        if self.spin_intensity.value() != val:
            self.spin_intensity.setValue(val)
        self._on_pitch_intensity_changed(val)

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
            from platforms.windows import set_launch_on_startup
            set_launch_on_startup(checked)
        elif sys.platform == "darwin":
            from platforms.macos import set_launch_on_startup
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
        """Update latency text in the UI and trigger visualizer pulse."""
        self.lbl_delay_val.setText(f"{latency_ms:.2f} ms")
        avg = self.sound_engine.average_software_latency_ms
        self.lbl_avg_val.setText(f"{avg:.2f} ms")

        # Pulse the wave visualizer bars for tactile feedback
        self.wave_visualizer.pulse()

    def _update_status_indicator(self) -> None:
        """Update status pill, wave animation, and button states."""
        is_ready = self.sound_engine.is_ready()
        is_running = self.keyboard_listener.is_running()
        is_paused = self.event_handler.is_paused()
        is_muted = self.sound_engine.is_muted

        active = is_ready and is_running and not is_paused

        # Update animated soundwave visualizer
        self.wave_visualizer.set_active(active)

        if not is_ready:
            self.status_badge.setText("Missing Audio")
            self.status_badge.setObjectName("statusPillStopped")
            self.btn_hero.setText("  AUDIO MISSING")
            self.btn_hero.setObjectName("heroActionBtnStopped")
            self.btn_hero.setIcon(get_power_icon("#FB7185", 20))
        elif is_muted:
            self.status_badge.setText("Muted")
            self.status_badge.setObjectName("statusPillPaused")
            self.btn_hero.setText("  MUTED (ACTIVE)")
            self.btn_hero.setObjectName("heroActionBtnRunning")
            self.btn_hero.setIcon(get_power_icon("#0C0D11", 20))
        elif not is_running:
            self.status_badge.setText("Stopped")
            self.status_badge.setObjectName("statusPillStopped")
            self.btn_hero.setText("  START ENGINE")
            self.btn_hero.setObjectName("heroActionBtnStopped")
            self.btn_hero.setIcon(get_power_icon("#FFFFFF", 20))
        elif is_paused:
            self.status_badge.setText("Paused")
            self.status_badge.setObjectName("statusPillPaused")
            self.btn_hero.setText("  RESUME ENGINE")
            self.btn_hero.setObjectName("heroActionBtnStopped")
            self.btn_hero.setIcon(get_power_icon("#FBBF24", 20))
        else:
            self.status_badge.setText("Running")
            self.status_badge.setObjectName("statusPillRunning")
            self.btn_hero.setText("  STOP ENGINE")
            self.btn_hero.setObjectName("heroActionBtnRunning")
            self.btn_hero.setIcon(get_power_icon("#0C0D11", 20))

        # Re-polish styles dynamically
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

        self.btn_hero.style().unpolish(self.btn_hero)
        self.btn_hero.style().polish(self.btn_hero)

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

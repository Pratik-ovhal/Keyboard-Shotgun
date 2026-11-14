"""System tray integration for Keyboard Shotgun on Windows and macOS."""

import logging
from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

logger = logging.getLogger("KeyboardShotgun.TrayManager")


def create_default_tray_icon() -> QIcon:
    """Load application logo or generate a clean procedural fallback icon."""
    try:
        from core.assets import get_asset_path
        logo_path = get_asset_path("logo.png")
        if logo_path.exists() and logo_path.stat().st_size > 0:
            icon = QIcon(str(logo_path.resolve()))
            if not icon.isNull():
                return icon
    except Exception as e:
        logger.debug(f"Could not load logo.png: {e}")

    # Fallback procedural icon
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))  # transparent background


    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Outer badge circle
    painter.setBrush(QColor("#2563eb"))
    painter.setPen(QColor("#38bdf8"))
    painter.drawEllipse(4, 4, 56, 56)

    # Inner concentric crosshair ring
    painter.setBrush(QColor(0, 0, 0, 0))
    painter.setPen(QColor("#ffffff"))
    painter.drawEllipse(16, 16, 32, 32)

    # Center target dot
    painter.setBrush(QColor("#ef4444"))
    painter.setPen(QColor("#ef4444"))
    painter.drawEllipse(28, 28, 8, 8)

    painter.end()
    return QIcon(pixmap)


class TrayManager(QObject):
    """Manages system tray icon, context menu, and background lifecycle."""

    show_window_requested = Signal()
    toggle_pause_requested = Signal()
    exit_requested = Signal()

    def __init__(
        self,
        parent: Optional[QObject] = None,
        on_show: Optional[Callable[[], None]] = None,
        on_toggle_pause: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.on_show = on_show
        self.on_toggle_pause = on_toggle_pause
        self.on_exit = on_exit

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(create_default_tray_icon())
        self.tray_icon.setToolTip("Keyboard Shotgun - Running in background")

        self._build_menu()
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _build_menu(self) -> None:
        """Create context menu for the system tray icon."""
        self.menu = QMenu()

        self.action_show = QAction("Show Keyboard Shotgun", self)
        self.action_show.triggered.connect(self._trigger_show)
        self.menu.addAction(self.action_show)

        self.action_pause_resume = QAction("Pause Sounds", self)
        self.action_pause_resume.triggered.connect(self._trigger_pause_resume)
        self.menu.addAction(self.action_pause_resume)

        self.menu.addSeparator()

        self.action_exit = QAction("Exit", self)
        self.action_exit.triggered.connect(self._trigger_exit)
        self.menu.addAction(self.action_exit)

        self.tray_icon.setContextMenu(self.menu)

    def show(self) -> None:
        """Display the tray icon."""
        self.tray_icon.show()

    def hide(self) -> None:
        """Hide the tray icon."""
        self.tray_icon.hide()

    def show_message(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        msecs: int = 4000,
    ) -> None:
        """Display a system notification popup via tray."""
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, msecs)

    def update_status(self, is_running: bool, is_paused: bool) -> None:
        """Update context menu text and tooltip based on engine status."""
        if not is_running:
            self.action_pause_resume.setText("Resume Sounds")
            self.action_pause_resume.setEnabled(False)
            self.tray_icon.setToolTip("Keyboard Shotgun - Stopped")
        elif is_paused:
            self.action_pause_resume.setText("Resume Sounds")
            self.action_pause_resume.setEnabled(True)
            self.tray_icon.setToolTip("Keyboard Shotgun - Paused")
        else:
            self.action_pause_resume.setText("Pause Sounds")
            self.action_pause_resume.setEnabled(True)
            self.tray_icon.setToolTip("Keyboard Shotgun - Active")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle user clicks on the tray icon."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._trigger_show()

    def _trigger_show(self) -> None:
        self.show_window_requested.emit()
        if self.on_show:
            self.on_show()

    def _trigger_pause_resume(self) -> None:
        self.toggle_pause_requested.emit()
        if self.on_toggle_pause:
            self.on_toggle_pause()

    def _trigger_exit(self) -> None:
        self.exit_requested.emit()
        if self.on_exit:
            self.on_exit()


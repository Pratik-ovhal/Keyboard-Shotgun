"""Modern premium dark theme styling for Keyboard Shotgun PySide6 GUI.

Inspired by modern high-end audio interfaces: deep charcoal palette,
electric lime accents, rounded cards, and clean typography.
"""

DARK_THEME_QSS = """
/* Global Window & Widget Settings */
QWidget {
    background-color: #0C0D11;
    color: #F1F3F9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #D4F63D;
    selection-color: #0C0D11;
}

QMainWindow {
    background-color: #0C0D11;
}

QLabel {
    background-color: transparent;
}


/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 4px 0 4px 0;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #252834;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #363B4C;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Sidebar Container */
QFrame#sidebarFrame {
    background-color: #111318;
    border-right: 1px solid #1B1E26;
}

/* Sidebar Navigation Buttons */
QPushButton#navBtn {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    color: #8E94A5;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    padding: 10px 14px;
    min-height: 22px;
}

QPushButton#navBtn:hover {
    background-color: #171A21;
    color: #FFFFFF;
}

QPushButton#navBtn:checked {
    background-color: #1A1E27;
    border: 1px solid #262B38;
    color: #D4F63D;
    font-weight: 600;
}

/* Cards & Containers */
QFrame#heroCard {
    background-color: #14161D;
    border: 1px solid #20242F;
    border-radius: 18px;
}

QFrame#settingsCard {
    background-color: #13151C;
    border: 1px solid #1F222C;
    border-radius: 14px;
}

QFrame#metricCard {
    background-color: #181B24;
    border: 1px solid #242936;
    border-radius: 12px;
}

/* Primary Hero Action Button */
QPushButton#heroActionBtnRunning {
    background-color: #D4F63D;
    border: 1px solid #E2FA5F;
    color: #0C0D11;
    border-radius: 14px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QPushButton#heroActionBtnRunning:hover {
    background-color: #E2FA5F;
    border-color: #FFFFFF;
}

QPushButton#heroActionBtnRunning:pressed {
    background-color: #BFDE30;
}

QPushButton#heroActionBtnStopped {
    background-color: #1A1D26;
    border: 1px solid #2D3342;
    color: #FFFFFF;
    border-radius: 14px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QPushButton#heroActionBtnStopped:hover {
    background-color: #232835;
    border-color: #424A60;
}

QPushButton#heroActionBtnStopped:pressed {
    background-color: #151820;
}

/* Secondary Action Buttons */
QPushButton#secondaryBtn {
    background-color: #1A1D26;
    border: 1px solid #272C3A;
    color: #E2E6F0;
    border-radius: 10px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton#secondaryBtn:hover {
    background-color: #232734;
    border-color: #373E52;
    color: #FFFFFF;
}

QPushButton#secondaryBtn:pressed {
    background-color: #14171E;
}

/* Small Pill Buttons (Mute, Test, etc.) */
QPushButton#pillBtn {
    background-color: #1A1D26;
    border: 1px solid #272C3A;
    color: #C8CDDC;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 12px;
}

QPushButton#pillBtn:hover {
    background-color: #222633;
    border-color: #383F53;
    color: #FFFFFF;
}

QPushButton#pillBtn:checked {
    background-color: #2D1B22;
    border: 1px solid #5A2733;
    color: #F43F5E;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #20232E;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #D4F63D;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 3px solid #D4F63D;
    width: 16px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #FFFFFF;
    border-color: #E6FA75;
}

/* Status Badges */
QLabel#statusPillRunning {
    background-color: #142415;
    color: #D4F63D;
    border: 1px solid #2B4527;
    border-radius: 10px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
}

QLabel#statusPillStopped {
    background-color: #241419;
    color: #FB7185;
    border: 1px solid #48212D;
    border-radius: 10px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
}

QLabel#statusPillPaused {
    background-color: #261E10;
    color: #FBBF24;
    border: 1px solid #4D3B1D;
    border-radius: 10px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* Value Badges */
QLabel#valueBadge {
    background-color: #1B1E28;
    color: #D4F63D;
    border: 1px solid #272C3B;
    border-radius: 6px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 12px;
}

/* Section Header Typography */
QLabel#sectionTitle {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 700;
}

QLabel#sectionSubtitle {
    color: #7D8496;
    font-size: 12px;
}

QLabel#settingItemTitle {
    color: #F1F3F9;
    font-size: 13px;
    font-weight: 600;
}

QLabel#settingItemDesc {
    color: #787F91;
    font-size: 12px;
}

/* SpinBoxes */
QSpinBox, QDoubleSpinBox {
    background-color: #1A1D26;
    border: 1px solid #292E3C;
    border-radius: 8px;
    color: #F1F3F9;
    padding: 6px 10px;
    font-weight: 600;
    font-size: 13px;
    min-width: 70px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #D4F63D;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background: transparent;
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid #292E3C;
    border-bottom: 1px solid #292E3C;
    border-top-right-radius: 7px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #272C3B;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: transparent;
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    border-left: 1px solid #292E3C;
    border-bottom-right-radius: 7px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #272C3B;
}

/* Tooltips & Dialogs */
QToolTip {
    background-color: #1A1D26;
    color: #F1F3F9;
    border: 1px solid #2D3344;
    border-radius: 6px;
    padding: 5px 8px;
}

QMessageBox {
    background-color: #12141A;
}

QMessageBox QLabel {
    color: #F1F3F9;
    font-size: 13px;
}

QMessageBox QPushButton {
    background-color: #1E222D;
    border: 1px solid #2F3547;
    border-radius: 8px;
    color: #FFFFFF;
    padding: 6px 18px;
    font-weight: 600;
}

QMessageBox QPushButton:hover {
    background-color: #292E3D;
    border-color: #D4F63D;
}
"""


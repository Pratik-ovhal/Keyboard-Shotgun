"""Modern dark theme styling for Keyboard Shotgun PySide6 GUI."""

DARK_THEME_QSS = """
/* Global Window & Widget Settings */
QWidget {
    background-color: #121316;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #181a20;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Card / Group Containers */
QGroupBox {
    background-color: #181a20;
    border: 1px solid #262b36;
    border-radius: 10px;
    margin-top: 24px;
    padding-top: 18px;
    padding-bottom: 14px;
    padding-left: 14px;
    padding-right: 14px;
    font-weight: 600;
    font-size: 13px;
    color: #94a3b8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #60a5fa;
}

/* Buttons */
QPushButton {
    background-color: #242936;
    border: 1px solid #333d4f;
    color: #f1f5f9;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #2e3647;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #1e2430;
    border-color: #2563eb;
}

QPushButton:disabled {
    background-color: #161a22;
    border-color: #212631;
    color: #475569;
}

/* Primary Action Buttons */
QPushButton#primaryBtn {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#primaryBtn:hover {
    background-color: #1d4ed8;
    border-color: #60a5fa;
}

QPushButton#primaryBtn:pressed {
    background-color: #1e40af;
}

/* Destructive / Stop Action Buttons */
QPushButton#dangerBtn {
    background-color: #dc2626;
    border: 1px solid #ef4444;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#dangerBtn:hover {
    background-color: #b91c1c;
    border-color: #f87171;
}

QPushButton#dangerBtn:pressed {
    background-color: #991b1b;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #242936;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #3b82f6;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #f8fafc;
    border: 2px solid #3b82f6;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #ffffff;
    border-color: #60a5fa;
    box-shadow: 0 0 6px rgba(59, 130, 246, 0.5);
}

/* SpinBox */
QSpinBox, QDoubleSpinBox {
    background-color: #242936;
    border: 1px solid #333d4f;
    border-radius: 6px;
    padding: 4px 8px;
    color: #f1f5f9;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3b82f6;
}

/* Checkboxes */
QCheckBox {
    spacing: 10px;
    color: #e2e8f0;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #333d4f;
    background-color: #242936;
}

QCheckBox::indicator:hover {
    border-color: #3b82f6;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #3b82f6;
    image: none;
}

/* Status Pill */
QLabel#statusPillRunning {
    background-color: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
    border-radius: 12px;
    padding: 3px 12px;
    font-weight: 600;
    font-size: 12px;
}

QLabel#statusPillPaused {
    background-color: #451a03;
    color: #fbbf24;
    border: 1px solid #d97706;
    border-radius: 12px;
    padding: 3px 12px;
    font-weight: 600;
    font-size: 12px;
}

QLabel#statusPillStopped {
    background-color: #450a0a;
    color: #f87171;
    border: 1px solid #dc2626;
    border-radius: 12px;
    padding: 3px 12px;
    font-weight: 600;
    font-size: 12px;
}

/* Latency & Diagnostics Badge */
QLabel#metricLabel {
    color: #94a3b8;
    font-size: 12px;
}

QLabel#metricValue {
    color: #38bdf8;
    font-weight: 600;
    font-size: 12px;
}
"""


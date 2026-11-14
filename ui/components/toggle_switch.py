"""Modern iOS/Fluent-style animated toggle switch for PySide6."""

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    Property,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QAbstractButton


class ToggleSwitch(QAbstractButton):
    """A sleek, animated pill toggle switch matching modern dark interfaces."""

    def __init__(self, parent=None, checked: bool = False, active_color: str = "#D4F63D"):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._active_color = QColor(active_color)
        self._inactive_color = QColor("#22252E")
        self._border_inactive = QColor("#333744")
        self._thumb_inactive = QColor("#A6ABB9")
        self._thumb_active = QColor("#0D0E12")

        # Thumb position ratio from 0.0 (left) to 1.0 (right)
        self._thumb_pos = 1.0 if checked else 0.0

        self._anim = QPropertyAnimation(self, b"thumb_position", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.toggled.connect(self._on_toggled)

    def sizeHint(self) -> QSize:
        return QSize(46, 26)

    def minimumSizeHint(self) -> QSize:
        return QSize(46, 26)

    def get_thumb_position(self) -> float:
        return self._thumb_pos

    def set_thumb_position(self, pos: float):
        self._thumb_pos = pos
        self.update()

    thumb_position = Property(float, get_thumb_position, set_thumb_position)

    def _on_toggled(self, checked: bool):
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._thumb_pos = 1.0 if checked else 0.0
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h / 2.0
        margin = 3.0
        thumb_diameter = h - (margin * 2)

        # Track background
        if self.isChecked():
            # Interpolate or solid active color
            bg_color = self._active_color
            border_color = self._active_color
        else:
            bg_color = self._inactive_color
            border_color = self._border_inactive

        track_rect = QRectF(0.5, 0.5, w - 1.0, h - 1.0)
        painter.setBrush(bg_color)
        painter.setPen(border_color)
        painter.drawRoundedRect(track_rect, radius, radius)

        # Thumb position calculation
        min_x = margin
        max_x = w - margin - thumb_diameter
        current_x = min_x + (max_x - min_x) * self._thumb_pos

        thumb_rect = QRectF(current_x, margin, thumb_diameter, thumb_diameter)
        thumb_color = self._thumb_active if self.isChecked() else self._thumb_inactive

        painter.setBrush(thumb_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(thumb_rect)

        painter.end()

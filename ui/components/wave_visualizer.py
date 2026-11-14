"""Tactile animated audio wave visualizer for Keyboard Shotgun."""

import math
from typing import List
from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget


class SoundWaveVisualizer(QWidget):
    """Subtle, modern audio visualizer bars indicating active listening state."""

    def __init__(self, parent=None, bar_count: int = 7, accent_color: str = "#D4F63D"):
        super().__init__(parent)
        self.bar_count = bar_count
        self.accent_color = QColor(accent_color)
        self.inactive_color = QColor("#2A2E3B")

        self._is_active: bool = False
        self._pulse_intensity: float = 0.0
        self._phase: float = 0.0

        # Heights from 0.0 to 1.0 for each bar
        self._bar_levels: List[float] = [0.25] * bar_count

        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 fps
        self._timer.timeout.connect(self._animate_step)

    def sizeHint(self) -> QSize:
        return QSize(140, 48)

    def minimumSizeHint(self) -> QSize:
        return QSize(80, 32)

    def set_active(self, active: bool):
        """Enable or disable visual animation."""
        if self._is_active == active:
            return
        self._is_active = active
        if active:
            self._timer.start()
        else:
            self._timer.stop()
            self._bar_levels = [0.2] * self.bar_count
            self.update()

    def pulse(self):
        """Trigger an instant tactile spike on keystroke sound dispatch."""
        if self._is_active:
            self._pulse_intensity = 1.0
            self.update()

    def _animate_step(self):
        self._phase += 0.12
        if self._pulse_intensity > 0.02:
            self._pulse_intensity *= 0.85
        else:
            self._pulse_intensity = 0.0

        base_heights = [0.25, 0.55, 0.85, 1.0, 0.85, 0.55, 0.25]
        for i in range(self.bar_count):
            idx_offset = i * 0.9
            sine_wave = (math.sin(self._phase + idx_offset) + 1.0) / 2.0  # 0.0 to 1.0
            target = 0.2 + (base_heights[i % len(base_heights)] * 0.6 * sine_wave)
            if self._pulse_intensity > 0:
                target = min(1.0, target + self._pulse_intensity * 0.45)
            self._bar_levels[i] = target

        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        spacing = 6.0
        total_spacing = spacing * (self.bar_count - 1)
        bar_w = max(4.0, (w - total_spacing) / self.bar_count)
        radius = bar_w / 2.0

        for i in range(self.bar_count):
            level = self._bar_levels[i] if self._is_active else 0.15
            bar_h = max(bar_w, h * level)
            x = i * (bar_w + spacing)
            y = (h - bar_h) / 2.0  # Centered vertically

            rect = QRectF(x, y, bar_w, bar_h)

            if self._is_active:
                # Vertical gradient for active bars
                grad = QLinearGradient(x, y, x, y + bar_h)
                top_col = QColor(self.accent_color)
                # Slightly brighter/glowing at center bars
                if i in (2, 3, 4):
                    top_col.setAlpha(255)
                else:
                    top_col.setAlpha(210)
                bottom_col = QColor(self.accent_color)
                bottom_col.setAlpha(140)

                grad.setColorAt(0.0, top_col)
                grad.setColorAt(1.0, bottom_col)
                painter.setBrush(grad)
                painter.setPen(Qt.PenStyle.NoPen)
            else:
                painter.setBrush(self.inactive_color)
                painter.setPen(Qt.PenStyle.NoPen)

            painter.drawRoundedRect(rect, radius, radius)

        painter.end()

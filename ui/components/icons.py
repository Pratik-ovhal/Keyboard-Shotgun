"""Procedural vector icons rendered via QPainter for crisp DPI scaling."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap


def create_icon_pixmap(draw_fn, size: int = 32) -> QPixmap:
    """Helper to render a procedural drawing function into a crisp transparent QPixmap."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_fn(painter, size)
    painter.end()

    return pixmap


def get_home_icon(color: str = "#FFFFFF", size: int = 24) -> QIcon:
    """Clean geometric Home icon."""
    def draw(p: QPainter, s: int):
        pen = QPen(QColor(color), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        pad = s * 0.18
        w = s - (pad * 2)
        h = s - (pad * 2)
        mid_x = s / 2.0
        roof_y = pad + 1.0

        path = QPainterPath()
        path.moveTo(mid_x, roof_y)
        path.lineTo(pad + 1.0, pad + (h * 0.42))
        path.lineTo(pad + (w * 0.2), pad + (h * 0.42))
        path.lineTo(pad + (w * 0.2), pad + h)
        path.lineTo(pad + (w * 0.8), pad + h)
        path.lineTo(pad + (w * 0.8), pad + (h * 0.42))
        path.lineTo(pad + w - 1.0, pad + (h * 0.42))
        path.closeSubpath()

        p.drawPath(path)

    return QIcon(create_icon_pixmap(draw, size))


def get_settings_icon(color: str = "#FFFFFF", size: int = 24) -> QIcon:
    """Modern Sliders / Controls Settings icon."""
    def draw(p: QPainter, s: int):
        pen = QPen(QColor(color), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        p1_x = s * 0.3
        p2_x = s * 0.7
        top_y = s * 0.2
        bot_y = s * 0.8

        # Vertical rails
        p.drawLine(QPointF(p1_x, top_y), QPointF(p1_x, bot_y))
        p.drawLine(QPointF(p2_x, top_y), QPointF(p2_x, bot_y))

        # Slider knobs
        p.setBrush(QColor(color))
        knob_r = s * 0.1
        p.drawEllipse(QPointF(p1_x, s * 0.42), knob_r, knob_r)
        p.drawEllipse(QPointF(p2_x, s * 0.64), knob_r, knob_r)

    return QIcon(create_icon_pixmap(draw, size))


def get_about_icon(color: str = "#FFFFFF", size: int = 24) -> QIcon:
    """Minimal Info icon."""
    def draw(p: QPainter, s: int):
        pen = QPen(QColor(color), 2.0)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        pad = s * 0.18
        p.drawEllipse(QRectF(pad, pad, s - (pad * 2), s - (pad * 2)))

        p.setBrush(QColor(color))
        p.setPen(Qt.PenStyle.NoPen)
        mid_x = s / 2.0
        # Dot
        p.drawEllipse(QPointF(mid_x, s * 0.36), s * 0.05, s * 0.05)
        # Line
        p.setPen(QPen(QColor(color), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(mid_x, s * 0.48), QPointF(mid_x, s * 0.68))

    return QIcon(create_icon_pixmap(draw, size))


def get_speaker_icon(color: str = "#FFFFFF", muted: bool = False, size: int = 24) -> QIcon:
    """Speaker icon with soundwave arcs or mute cross."""
    def draw(p: QPainter, s: int):
        pen = QPen(QColor(color), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(QColor(color))

        # Speaker horn
        horn = QPainterPath()
        horn.moveTo(s * 0.2, s * 0.38)
        horn.lineTo(s * 0.36, s * 0.38)
        horn.lineTo(s * 0.54, s * 0.24)
        horn.lineTo(s * 0.54, s * 0.76)
        horn.lineTo(s * 0.36, s * 0.62)
        horn.lineTo(s * 0.2, s * 0.62)
        horn.closeSubpath()
        p.drawPath(horn)

        if muted:
            # Draw X slash
            p.setBrush(Qt.BrushStyle.NoBrush)
            x1 = s * 0.66
            x2 = s * 0.84
            y1 = s * 0.40
            y2 = s * 0.60
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            p.drawLine(QPointF(x1, y2), QPointF(x2, y1))
        else:
            # Draw sound wave arc
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(s * 0.46, s * 0.32, s * 0.32, s * 0.36), -60 * 16, 120 * 16)
            p.drawArc(QRectF(s * 0.42, s * 0.22, s * 0.52, s * 0.56), -50 * 16, 100 * 16)

    return QIcon(create_icon_pixmap(draw, size))


def get_power_icon(color: str = "#FFFFFF", size: int = 28) -> QIcon:
    """Tactile power/play symbol for primary hero action."""
    def draw(p: QPainter, s: int):
        pen = QPen(QColor(color), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        pad = s * 0.2
        rect = QRectF(pad, pad, s - (pad * 2), s - (pad * 2))
        # Circle with gap at top
        p.drawArc(rect, 45 * 16, 270 * 16)
        # Vertical line in gap
        mid_x = s / 2.0
        p.drawLine(QPointF(mid_x, s * 0.16), QPointF(mid_x, s * 0.48))

    return QIcon(create_icon_pixmap(draw, size))


def get_github_icon(color: str = "#FFFFFF", size: int = 24) -> QIcon:
    """Minimal GitHub octocat silhouette vector icon."""
    def draw(p: QPainter, s: int):
        pen = QPen(QColor(color), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        pad = s * 0.16
        rect = QRectF(pad, pad, s - (pad * 2), s - (pad * 2))
        p.drawEllipse(rect)

        # Inner cat ear lines
        mid_x = s / 2.0
        p.drawLine(QPointF(mid_x - 3, s * 0.35), QPointF(mid_x - 5, s * 0.28))
        p.drawLine(QPointF(mid_x + 3, s * 0.35), QPointF(mid_x + 5, s * 0.28))

    return QIcon(create_icon_pixmap(draw, size))


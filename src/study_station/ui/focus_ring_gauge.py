"""Custom QPainter Circular Ring Gauge for the Focus Screen.

Provides a tactile, glanceable countdown display inspired by Dieter Rams /
Teenage Engineering appliances and high-end focus hardware:
- Outer Ring: Active session countdown arc (starts full, smoothly recedes clockwise)
- Inner Ring: Subject study cycle goal progress (fills clockwise as minutes accumulate)
- Center Hub: Status badge pill (● FOCUSING / ⏸ PAUSED), giant monospace numerals,
  and cycle progress subtitle.
"""

from __future__ import annotations
import math
from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from study_station.ui.theme import get_modern_font


class FocusRingGaugeWidget(QWidget):
    """Custom antialiased dual-ring gauge for study sessions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(300, 300)

        # State attributes
        self._formatted_time: str = "25:00"
        self._remaining_ratio: float = 1.0  # 1.0 (full) down to 0.0 (finished)
        self._cycle_ratio: float = 0.0       # 0.0 to 1.0+ (cycle progress)
        self._is_paused: bool = False
        self._cycle_text: str = "0 / 60 MIN"
        self._theme_id: str = "noir"

    # -------------------------------------------------------------------------
    # Public API for setting display state
    # -------------------------------------------------------------------------

    def set_timer_state(
        self,
        formatted_time: str,
        remaining_ratio: float,
        is_paused: bool = False,
        cycle_ratio: float = 0.0,
        cycle_text: str = "",
        theme_id: str = "noir",
    ) -> None:
        """Update timer display and trigger repaint."""
        self._formatted_time = formatted_time
        self._remaining_ratio = max(0.0, min(1.0, remaining_ratio))
        self._is_paused = is_paused
        self._cycle_ratio = max(0.0, cycle_ratio)
        self._cycle_text = cycle_text
        self._theme_id = theme_id
        self.update()

    @property
    def formatted_time(self) -> str:
        return self._formatted_time

    @property
    def remaining_ratio(self) -> float:
        return self._remaining_ratio

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def cycle_ratio(self) -> float:
        return self._cycle_ratio

    @property
    def cycle_text(self) -> str:
        return self._cycle_text

    def sizeHint(self) -> QSize:
        return QSize(360, 360)

    # -------------------------------------------------------------------------
    # Painting
    # -------------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        max_r = min(w, h) / 2.0

        # Geometry calculations
        r_outer = max(40.0, max_r - 20.0)
        outer_pen_w = 9.0

        r_inner = max(20.0, r_outer - 18.0)
        inner_pen_w = 4.0

        # Theme color resolution
        is_nerv = (self._theme_id == "nerv")
        if self._is_paused:
            arc_color = QColor("#F59E0B")       # Amber
            pill_bg = QColor("#38240D")
            pill_fg = QColor("#FBBF24")
            state_text = "⏸ PAUSED"
        elif is_nerv:
            arc_color = QColor("#FF7700")       # NERV Orange
            pill_bg = QColor("#3D1600")
            pill_fg = QColor("#FF9933")
            state_text = "● FOCUSING"
        else:
            arc_color = QColor("#10B981")       # Emerald
            pill_bg = QColor("#064E3B")
            pill_fg = QColor("#34D399")
            state_text = "● FOCUSING"

        track_outer_color = QColor("#181820")
        track_inner_color = QColor("#121218")
        cycle_color = QColor("#38BDF8") if self._cycle_ratio < 1.0 else QColor("#10B981")

        # ---------------------------------------------------------------------
        # 1. Outer Track (Background ring)
        # ---------------------------------------------------------------------
        pen_track_outer = QPen(track_outer_color, outer_pen_w)
        pen_track_outer.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect_outer = QRectF(cx - r_outer, cy - r_outer, r_outer * 2, r_outer * 2)
        painter.drawEllipse(rect_outer)

        # ---------------------------------------------------------------------
        # 2. Outer Active Arc (Session countdown)
        # ---------------------------------------------------------------------
        # Angle logic: 12 o'clock = 90 deg. Clockwise sweep is negative.
        if self._remaining_ratio > 0.001:
            pen_arc_outer = QPen(arc_color, outer_pen_w)
            pen_arc_outer.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arc_outer)
            start_angle = int(90 * 16)
            span_angle = int(-360 * 16 * self._remaining_ratio)
            painter.drawArc(rect_outer, start_angle, span_angle)

        # ---------------------------------------------------------------------
        # 3. Inner Track (Background cycle ring)
        # ---------------------------------------------------------------------
        pen_track_inner = QPen(track_inner_color, inner_pen_w)
        pen_track_inner.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track_inner)
        rect_inner = QRectF(cx - r_inner, cy - r_inner, r_inner * 2, r_inner * 2)
        painter.drawEllipse(rect_inner)

        # ---------------------------------------------------------------------
        # 4. Inner Active Arc (Subject cycle progress)
        # ---------------------------------------------------------------------
        if self._cycle_ratio > 0.001:
            pen_arc_inner = QPen(cycle_color, inner_pen_w)
            pen_arc_inner.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arc_inner)
            start_angle_inner = int(90 * 16)
            span_angle_inner = int(-360 * 16 * min(1.0, self._cycle_ratio))
            painter.drawArc(rect_inner, start_angle_inner, span_angle_inner)

        # ---------------------------------------------------------------------
        # 5. Center Hub: State Pill Badge (Top inside ring)
        # ---------------------------------------------------------------------
        pill_w = 114.0
        pill_h = 24.0
        pill_x = cx - (pill_w / 2.0)
        pill_y = cy - (r_inner * 0.44)

        pill_rect = QRectF(pill_x, pill_y, pill_w, pill_h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(pill_bg))
        painter.drawRoundedRect(pill_rect, 12.0, 12.0)

        # Pill text
        painter.setFont(get_modern_font("mono", 10, QFont.Weight.Bold))
        painter.setPen(QPen(pill_fg))
        painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, state_text)

        # ---------------------------------------------------------------------
        # 6. Center Hub: Massive Monospace Countdown Numerals
        # ---------------------------------------------------------------------
        font_size = max(34, int(r_inner * 0.38))
        font_digits = get_modern_font("mono", font_size, QFont.Weight.Bold)
        painter.setFont(font_digits)
        painter.setPen(QPen(QColor("#FFFFFF")))

        digits_rect = QRectF(cx - r_inner, cy - 24, r_inner * 2, font_size * 1.3)
        painter.drawText(digits_rect, Qt.AlignmentFlag.AlignCenter, self._formatted_time)

        # ---------------------------------------------------------------------
        # 7. Center Hub: Cycle Progress Subtitle (Bottom inside ring)
        # ---------------------------------------------------------------------
        if self._cycle_text:
            painter.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
            painter.setPen(QPen(QColor("#71717A")))
            cycle_rect = QRectF(cx - r_inner, cy + (r_inner * 0.38), r_inner * 2, 22.0)
            painter.drawText(cycle_rect, Qt.AlignmentFlag.AlignCenter, self._cycle_text)

        painter.end()

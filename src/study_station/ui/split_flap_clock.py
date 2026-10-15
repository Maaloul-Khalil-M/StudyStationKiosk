"""Compact Split-Flap Flip Clock widget for Study Station."""

from datetime import datetime
import math
from PySide6.QtCore import QPoint, QRect, QSize, QTimer, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from study_station.core.settings import AppSettings
from study_station.ui.theme import THEMES, get_modern_font


class SplitFlapClockWidget(QWidget):
    """Compact, elegant split-flap flip clock widget.
    
    Renders retro-minimal split-flap cards for Hours : Minutes (and optional Seconds)
    with physical crease, notches, and snappy 3D fold animation.
    """

    def __init__(self, settings: AppSettings | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.settings = settings or AppSettings()

        now = datetime.now()
        self._curr_hour = self._get_hour_str(now)
        self._prev_hour = self._curr_hour
        self._curr_minute = f"{now.minute:02d}"
        self._prev_minute = self._curr_minute
        self._curr_second = f"{now.second:02d}"
        self._prev_second = self._curr_second

        self._minute_flip_progress = 1.0
        self._second_flip_progress = 1.0

        # Clock tick timer
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(200 if self.settings.show_seconds else 1000)
        self._clock_timer.timeout.connect(self._on_clock_tick)
        self._clock_timer.start()

        # Animation timer (60 FPS)
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._on_anim_frame)

        self._update_dimensions()

    def _get_layout_metrics(self) -> tuple[int, int, int, int, int]:
        rect = self.rect()
        card_h = min(160, max(60, rect.height() - 8))
        card_w = int(card_h * 0.86)
        gap = 12
        colon_w = 22
        if self.settings.show_seconds:
            total_w = 3 * card_w + 2 * colon_w + 4 * gap
        else:
            total_w = 2 * card_w + colon_w + 2 * gap
        return card_h, card_w, gap, colon_w, total_w

    def sizeHint(self) -> QSize:
        w = 516 if self.settings.show_seconds else 330
        return QSize(w, 168)

    def _update_dimensions(self) -> None:
        w = 516 if self.settings.show_seconds else 330
        self.setFixedSize(w, 168)

    def apply_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        self._clock_timer.setInterval(200 if self.settings.show_seconds else 1000)
        self._update_dimensions()
        self.update()

    def _get_hour_str(self, now: datetime) -> str:
        if self.settings.use_24h:
            return f"{now.hour:02d}"
        h = now.hour % 12
        return f"{12 if h == 0 else h:02d}"

    def _on_clock_tick(self) -> None:
        now = datetime.now()
        new_hour = self._get_hour_str(now)
        new_min = f"{now.minute:02d}"
        new_sec = f"{now.second:02d}"

        hour_changed = new_hour != self._curr_hour
        min_changed = new_min != self._curr_minute
        sec_changed = new_sec != self._curr_second

        if hour_changed or min_changed or sec_changed:
            if min_changed or hour_changed:
                self._prev_hour = self._curr_hour
                self._curr_hour = new_hour
                self._prev_minute = self._curr_minute
                self._curr_minute = new_min
                if self.settings.animate_flip:
                    self._minute_flip_progress = 0.0
                    if not self._anim_timer.isActive():
                        self._anim_timer.start()

            if sec_changed and self.settings.show_seconds:
                self._prev_second = self._curr_second
                self._curr_second = new_sec
                if self.settings.animate_flip:
                    self._second_flip_progress = 0.0
                    if not self._anim_timer.isActive():
                        self._anim_timer.start()

            self.update()

    def _on_anim_frame(self) -> None:
        step = 0.16
        active = False

        if self._minute_flip_progress < 1.0:
            self._minute_flip_progress = min(1.0, self._minute_flip_progress + step)
            active = True

        if self._second_flip_progress < 1.0:
            self._second_flip_progress = min(1.0, self._second_flip_progress + step * 1.4)
            active = True

        if not active:
            self._anim_timer.stop()

        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect()
        theme = THEMES.get(self.settings.theme_id, THEMES["noir"])
        bg_hex = getattr(self.settings, "bg_color", "")
        bg = QColor(bg_hex) if bg_hex else theme.bg_canvas
        painter.fillRect(rect, bg)

        now = datetime.now()
        card_h, card_w, gap, colon_w, total_w = self._get_layout_metrics()

        start_x = (rect.width() - total_w) // 2
        start_y = (rect.height() - card_h) // 2

        x = start_x

        # Card 1: Hours
        hours_rect = QRect(x, start_y, card_w, card_h)
        am_pm = ("AM" if now.hour < 12 else "PM") if not self.settings.use_24h else ""
        self._paint_card(painter, hours_rect, self._curr_hour, self._prev_hour, 1.0, theme, am_pm=am_pm)
        x += card_w + gap

        # Colon 1
        colon1_rect = QRect(x, start_y, colon_w, card_h)
        self._paint_colon(painter, colon1_rect, theme)
        x += colon_w + gap

        # Card 2: Minutes
        min_rect = QRect(x, start_y, card_w, card_h)
        self._paint_card(painter, min_rect, self._curr_minute, self._prev_minute, self._minute_flip_progress, theme)

        # Optional Seconds
        if self.settings.show_seconds:
            x += card_w + gap
            colon2_rect = QRect(x, start_y, colon_w, card_h)
            self._paint_colon(painter, colon2_rect, theme)
            x += colon_w + gap

            sec_rect = QRect(x, start_y, card_w, card_h)
            self._paint_card(painter, sec_rect, self._curr_second, self._prev_second, self._second_flip_progress, theme)

    def _paint_colon(self, painter: QPainter, rect: QRect, theme) -> None:
        """Render stylish physical glowing pill colon markers."""
        painter.save()
        cx = rect.center().x()
        cy = rect.center().y()
        pill_w = 6
        pill_h = 14
        pill_r = 3

        # Top colon pill (centered in top flap zone)
        top_pill = QRect(cx - pill_w // 2, cy - 28 - pill_h // 2, pill_w, pill_h)
        # Bottom colon pill (centered in bottom flap zone)
        bot_pill = QRect(cx - pill_w // 2, cy + 28 - pill_h // 2, pill_w, pill_h)

        accent_hex = getattr(self.settings, "accent_color", "")
        if accent_hex:
            accent = QColor(accent_hex)
        else:
            accent = getattr(theme, "text_accent", getattr(theme, "accent_primary", QColor("#10B981")))
        painter.setBrush(accent)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(top_pill, pill_r, pill_r)
        painter.drawRoundedRect(bot_pill, pill_r, pill_r)
        painter.restore()

    def _paint_card(
        self,
        painter: QPainter,
        rect: QRect,
        curr_digit: str,
        prev_digit: str,
        progress: float,
        theme,
        am_pm: str = "",
    ) -> None:
        corner_r = 8
        notch_r = 4
        y_mid = rect.center().y()

        top_rect = QRect(rect.left(), rect.top(), rect.width(), y_mid - rect.top())
        bottom_rect = QRect(rect.left(), y_mid, rect.width(), rect.bottom() - y_mid + 1)

        # Standard clean sans-serif numeral typography for physical split-flap clarity
        font_size = max(1, int(rect.height() * 0.46))
        digit_font = get_modern_font("sans", size=font_size, weight=QFont.Weight.Bold)
        digit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0)

        # 1. Base card (bottom flap)
        bot_grad = QLinearGradient(bottom_rect.topLeft(), bottom_rect.bottomLeft())
        bot_grad.setColorAt(0.0, theme.card_bottom_grad_start)
        bot_grad.setColorAt(1.0, theme.card_bottom_grad_end)

        bot_path = QPainterPath()
        bot_path.addRoundedRect(rect, corner_r, corner_r)
        painter.fillPath(bot_path, bot_grad)

        # 2. Bottom flap digit
        painter.save()
        painter.setClipRect(bottom_rect)
        painter.setFont(digit_font)
        painter.setPen(theme.text_primary)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, curr_digit)
        painter.restore()

        # 3. Top flap background & digit
        top_grad = QLinearGradient(top_rect.topLeft(), top_rect.bottomLeft())
        top_grad.setColorAt(0.0, theme.card_top_grad_start)
        top_grad.setColorAt(1.0, theme.card_top_grad_end)

        painter.save()
        painter.setClipRect(top_rect)
        top_path = QPainterPath()
        top_path.addRoundedRect(rect, corner_r, corner_r)
        painter.fillPath(top_path, top_grad)
        painter.setFont(digit_font)
        painter.setPen(theme.text_primary)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, curr_digit)
        painter.restore()

        # 4. Animated flip overlay
        if progress < 1.0:
            if progress < 0.5:
                fold_ratio = math.cos(progress * math.pi)
                fold_h = int(top_rect.height() * fold_ratio)
                if fold_h > 0:
                    fold_rect = QRect(top_rect.left(), y_mid - fold_h, top_rect.width(), fold_h)
                    painter.save()
                    painter.setClipRect(fold_rect)
                    painter.fillPath(top_path, top_grad)
                    painter.setFont(digit_font)
                    painter.setPen(theme.text_primary)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, prev_digit)
                    shadow_alpha = int(120 * (progress * 2))
                    painter.fillRect(fold_rect, QColor(0, 0, 0, shadow_alpha))
                    painter.restore()
            else:
                unfold_ratio = math.sin((progress - 0.5) * math.pi)
                unfold_h = int(bottom_rect.height() * unfold_ratio)
                if unfold_h > 0:
                    unfold_rect = QRect(bottom_rect.left(), y_mid, bottom_rect.width(), unfold_h)
                    painter.save()
                    painter.setClipRect(unfold_rect)
                    painter.fillPath(bot_path, bot_grad)
                    painter.setFont(digit_font)
                    painter.setPen(theme.text_primary)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, curr_digit)
                    shadow_alpha = int(120 * (1.0 - (progress - 0.5) * 2))
                    painter.fillRect(unfold_rect, QColor(0, 0, 0, shadow_alpha))
                    painter.restore()

        # 5. Outer card border
        painter.save()
        painter.setPen(QPen(theme.card_border, 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, corner_r, corner_r)
        painter.restore()

        # 6. Physical center hinge groove & crease depth
        groove_rect = QRect(rect.left(), y_mid - 1, rect.width(), 2)
        painter.fillRect(groove_rect, theme.hinge_groove)
        # Crease shadow line above
        painter.fillRect(QRect(rect.left() + 2, y_mid - 2, rect.width() - 4, 1), QColor(0, 0, 0, 80))
        # Crease hairline highlight below
        painter.fillRect(QRect(rect.left() + 2, y_mid + 1, rect.width() - 4, 1), QColor(255, 255, 255, 18))

        # 7. Side hinge notches & center pivot pins
        painter.save()
        painter.setPen(QPen(theme.card_border, 1.0))
        bg_hex = getattr(self.settings, "bg_color", "")
        bg = QColor(bg_hex) if bg_hex else theme.bg_canvas
        painter.setBrush(bg)
        painter.drawEllipse(QPoint(rect.left(), y_mid), notch_r, notch_r)
        painter.drawEllipse(QPoint(rect.right(), y_mid), notch_r, notch_r)
        # Center pivot pins
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(theme.card_border)
        painter.drawEllipse(QPoint(rect.left(), y_mid), 2, 2)
        painter.drawEllipse(QPoint(rect.right(), y_mid), 2, 2)
        painter.restore()

        # 8. AM/PM Indicator
        if am_pm:
            ampm_font = get_modern_font("sans", size=max(9, int(rect.height() * 0.08)), weight=QFont.Weight.Bold)
            painter.setFont(ampm_font)
            painter.setPen(theme.text_muted)
            ampm_rect = QRect(rect.left() + int(rect.width() * 0.08), rect.bottom() - int(rect.height() * 0.18), 36, 18)
            painter.drawText(ampm_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, am_pm)

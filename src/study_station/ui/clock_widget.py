"""Modern split-flap flip clock widget with auto-hiding action bar and calm typography."""

from datetime import datetime
import math
from PySide6.QtCore import (
    QEvent,
    QPoint,
    QPropertyAnimation,
    QRect,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_station.core.settings import AppSettings
from study_station.ui.theme import (
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    THEMES,
    get_modern_font,
)


class AmbientClockWidget(QWidget):
    """Calm, glanceable split-flap ambient clock.
    
    Adheres strictly to the 'clock as centerpiece' principle:
    - Clean split-flap digits with uniform gaps
    - Small, low-contrast date at top
    - Single discreet study progress line
    - Auto-hiding control bar that fades in only on user activity
    """

    start_focus_requested = Signal(int)
    open_customization_requested = Signal()
    switch_subject_requested = Signal()

    def __init__(self, settings: AppSettings | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setMouseTracking(True)

        self.settings = settings or AppSettings()
        self._secondary_text: str = ""
        self._progress_fraction: float = 0.0

        # State tracking for flip animation
        now = datetime.now()
        self._prev_hour = self._get_hour_str(now)
        self._curr_hour = self._prev_hour
        self._prev_minute = f"{now.minute:02d}"
        self._curr_minute = self._prev_minute
        self._prev_second = f"{now.second:02d}"
        self._curr_second = self._prev_second

        # Animation progress: 0.0 to 1.0
        self._minute_flip_progress: float = 1.0
        self._second_flip_progress: float = 1.0

        # Refresh timers
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(200 if self.settings.show_seconds else 1000)
        self._clock_timer.timeout.connect(self._on_clock_tick)
        self._clock_timer.start()

        # Snappy, physical flip animation (~200ms)
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # ~60 FPS
        self._anim_timer.timeout.connect(self._on_anim_frame)

        # Inactivity timer for auto-hiding the action bar (3.5 seconds)
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.setInterval(3500)
        self._inactivity_timer.timeout.connect(self._fade_out_controls)

        self._init_controls()

    def _init_controls(self) -> None:
        """Create auto-hiding action bar with a single primary action."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 32)
        layout.addStretch()

        # Container widget for opacity animation
        self.action_bar_container = QWidget(self)
        self.action_bar_container.setMouseTracking(True)
        action_bar_layout = QHBoxLayout(self.action_bar_container)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
        action_bar_layout.setSpacing(12)
        action_bar_layout.addStretch()

        # Single Primary Focus Button
        self.btn_focus_main = QPushButton("▶ Start Focus")
        self.btn_focus_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_focus_main.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_focus_main.clicked.connect(lambda: self.start_focus_requested.emit(self.settings.default_focus_minutes))
        action_bar_layout.addWidget(self.btn_focus_main)

        # Settings icon button
        self.btn_settings = QPushButton("⚙ Customize")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_settings.clicked.connect(self.open_customization_requested.emit)
        action_bar_layout.addWidget(self.btn_settings)

        action_bar_layout.addStretch()
        layout.addWidget(self.action_bar_container)

        # Opacity effect for smooth fade in/out
        self._opacity_effect = QGraphicsOpacityEffect(self.action_bar_container)
        self._opacity_effect.setOpacity(0.0)
        self.action_bar_container.setGraphicsEffect(self._opacity_effect)

        self._opacity_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._opacity_anim.setDuration(220)

    def reveal_controls(self) -> None:
        """Show action bar smoothly and reset auto-hide inactivity timer."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if self._opacity_effect.opacity() < 0.99 and self._opacity_anim.state() != QPropertyAnimation.State.Running:
            self._opacity_anim.stop()
            self._opacity_anim.setStartValue(self._opacity_effect.opacity())
            self._opacity_anim.setEndValue(1.0)
            self._opacity_anim.start()

        self._inactivity_timer.start()

    def _fade_out_controls(self) -> None:
        """Fade out action bar smoothly after inactivity."""
        if self._opacity_effect.opacity() > 0.01:
            self._opacity_anim.stop()
            self._opacity_anim.setStartValue(self._opacity_effect.opacity())
            self._opacity_anim.setEndValue(0.0)
            self._opacity_anim.start()

        # Auto-hide cursor when in fullscreen and idle
        window = self.window()
        if window and window.isFullScreen():
            self.setCursor(Qt.CursorShape.BlankCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.reveal_controls()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.reveal_controls()
        # Clicking the progress pill opens subject switcher or focus
        rect = self.rect()
        pill_rect = self._get_pill_rect(rect)
        if pill_rect.contains(event.pos()):
            self.switch_subject_requested.emit()
        super().mousePressEvent(event)

    def apply_settings(self, settings: AppSettings) -> None:
        """Apply updated settings and trigger repaint."""
        self.settings = settings
        self._clock_timer.setInterval(200 if self.settings.show_seconds else 1000)
        self.update()

    def toggle_time_format(self) -> None:
        self.settings.use_24h = not self.settings.use_24h
        self.update()

    @property
    def secondary_text(self) -> str:
        return self._secondary_text

    @secondary_text.setter
    def secondary_text(self, text: str) -> None:
        if self._secondary_text != text:
            self._secondary_text = text
            self._calculate_progress_fraction(text)
            self.update()

    def _calculate_progress_fraction(self, text: str) -> None:
        """Extract completed/target fraction for subtle visual indication."""
        try:
            if "/" in text and "MIN" in text:
                parts = text.split("·")[-1].replace("MIN", "").strip().split("/")
                completed = float(parts[0].strip())
                target = float(parts[1].strip())
                self._progress_fraction = min(1.0, max(0.0, completed / target)) if target > 0 else 0.0
            else:
                self._progress_fraction = 0.0
        except Exception:
            self._progress_fraction = 0.0

    def _get_hour_str(self, now: datetime) -> str:
        if self.settings.use_24h:
            return f"{now.hour:02d}"
        h = now.hour % 12
        return f"{12 if h == 0 else h:02d}"

    def _on_clock_tick(self) -> None:
        now = datetime.now()
        new_hour = self._get_hour_str(now)
        new_minute = f"{now.minute:02d}"
        new_second = f"{now.second:02d}"

        minute_changed = new_minute != self._curr_minute
        second_changed = new_second != self._curr_second

        if minute_changed or second_changed:
            if minute_changed:
                self._prev_minute = self._curr_minute
                self._curr_minute = new_minute
                self._prev_hour = self._curr_hour
                self._curr_hour = new_hour
                if self.settings.animate_flip:
                    self._minute_flip_progress = 0.0
                    if not self._anim_timer.isActive():
                        self._anim_timer.start()

            if second_changed and self.settings.show_seconds:
                self._prev_second = self._curr_second
                self._curr_second = new_second
                if self.settings.animate_flip:
                    self._second_flip_progress = 0.0
                    if not self._anim_timer.isActive():
                        self._anim_timer.start()

            self.update()

    def _on_anim_frame(self) -> None:
        """Step flip animation smoothly (~200ms total duration)."""
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

        # Canvas background (pure calm black)
        painter.fillRect(rect, theme.bg_canvas)

        now = datetime.now()

        # 1. Discreet Date Line at top (calm, low contrast)
        if self.settings.show_date:
            self._draw_date_header(painter, rect, now, theme)

        # 2. Split-Flap Clock Cards (uniform spacing, centerpiece)
        self._draw_flip_cards(painter, rect, now, theme)

        # 3. Single Discreet Progress Line (exact concept format: SUBJECT · XX / YY MIN)
        if self._secondary_text:
            self._draw_progress_line(painter, rect, theme)

    def _draw_date_header(self, painter: QPainter, rect: QRect, now: datetime, theme) -> None:
        """Draw small, low-contrast date line at top so it never competes with the clock."""
        day_names = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

        day_name = day_names[now.weekday()]
        month_name = month_names[now.month - 1]

        if self.settings.date_format == "compact":
            date_str = f"{day_name[:3]}, {now.day} {month_name}"
        else:
            date_str = f"{day_name}, {month_name} {now.day}"

        # Small 13px font, low-contrast muted gray (#71717A)
        header_font = get_modern_font("sans", size=13, weight=QFont.Weight.Medium)
        header_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.5)

        header_rect = QRect(0, int(rect.height() * 0.16), rect.width(), 30)

        painter.setFont(header_font)
        painter.setPen(theme.text_muted)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, date_str)

    def _draw_flip_cards(self, painter: QPainter, rect: QRect, now: datetime, theme) -> None:
        """Draw authentic split-flap cards with strictly uniform gaps."""
        # Scale card size for 1366x768
        card_h = int(rect.height() * 0.40)
        card_w = int(card_h * 0.88)
        
        # Strictly uniform gap between ALL panels
        gap = int(card_h * 0.065)

        has_seconds = self.settings.show_seconds
        total_w = card_w * 2 + gap + (gap + card_w if has_seconds else 0)

        start_x = (rect.width() - total_w) // 2
        center_y = int(rect.height() * 0.45)
        start_y = center_y - card_h // 2

        # Card 1: Hours
        hours_rect = QRect(start_x, start_y, card_w, card_h)
        am_pm = ("AM" if now.hour < 12 else "PM") if not self.settings.use_24h else ""
        self._paint_single_flip_card(
            painter, hours_rect, self._curr_hour, self._prev_hour, 1.0, theme, am_pm=am_pm
        )

        # Card 2: Minutes (gap is strictly uniform)
        min_x = start_x + card_w + gap
        min_rect = QRect(min_x, start_y, card_w, card_h)
        self._paint_single_flip_card(
            painter, min_rect, self._curr_minute, self._prev_minute, self._minute_flip_progress, theme
        )

        # Card 3: Seconds (if enabled, gap is strictly uniform)
        if has_seconds:
            sec_x = min_x + card_w + gap
            sec_rect = QRect(sec_x, start_y, card_w, card_h)
            self._paint_single_flip_card(
                painter, sec_rect, self._curr_second, self._prev_second, self._second_flip_progress, theme
            )

    def _paint_single_flip_card(
        self,
        painter: QPainter,
        rect: QRect,
        curr_digit: str,
        prev_digit: str,
        progress: float,
        theme,
        am_pm: str = "",
    ) -> None:
        """Render a single authentic split-flap card with hinge notches and divider."""
        corner_r = max(6, int(rect.height() * 0.055))
        notch_r = max(3, int(rect.height() * 0.032))
        y_mid = rect.center().y()

        top_rect = QRect(rect.left(), rect.top(), rect.width(), y_mid - rect.top())
        bottom_rect = QRect(rect.left(), y_mid, rect.width(), rect.bottom() - y_mid + 1)

        font_size = max(1, int(rect.height() * 0.70))
        digit_font = get_modern_font("mono", size=font_size, weight=QFont.Weight.Bold)

        # 1. Base Card Background (Bottom Flap)
        bot_grad = QLinearGradient(bottom_rect.topLeft(), bottom_rect.bottomLeft())
        bot_grad.setColorAt(0.0, theme.card_bottom_grad_start)
        bot_grad.setColorAt(1.0, theme.card_bottom_grad_end)

        bot_path = QPainterPath()
        bot_path.addRoundedRect(rect, corner_r, corner_r)
        painter.fillPath(bot_path, bot_grad)

        # 2. Draw Bottom Flap Digit (Current Digit)
        painter.save()
        painter.setClipRect(bottom_rect)
        painter.setFont(digit_font)
        painter.setPen(theme.text_primary)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, curr_digit)
        painter.restore()

        # 3. Top Flap Background
        top_grad = QLinearGradient(top_rect.topLeft(), top_rect.bottomLeft())
        top_grad.setColorAt(0.0, theme.card_top_grad_start)
        top_grad.setColorAt(1.0, theme.card_top_grad_end)

        painter.save()
        painter.setClipRect(top_rect)
        top_path = QPainterPath()
        top_path.addRoundedRect(rect, corner_r, corner_r)
        painter.fillPath(top_path, top_grad)

        # Draw Top Flap Digit (Current Digit)
        painter.setFont(digit_font)
        painter.setPen(theme.text_primary)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, curr_digit)
        painter.restore()

        # 4. Animated Flip Overlay if in transition (Physical 3D fold)
        if progress < 1.0:
            if progress < 0.5:
                # Top half folding down (Previous Digit)
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
                    # Gentle deepening shadow
                    shadow_alpha = int(120 * (progress * 2))
                    painter.fillRect(fold_rect, QColor(0, 0, 0, shadow_alpha))
                    painter.restore()
            else:
                # Bottom half unfolding down (Current Digit)
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
                    # Gentle lightening shadow
                    shadow_alpha = int(120 * (1.0 - (progress - 0.5) * 2))
                    painter.fillRect(unfold_rect, QColor(0, 0, 0, shadow_alpha))
                    painter.restore()

        # 5. Outer Card Border
        painter.save()
        border_pen = QPen(theme.card_border, 1.2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, corner_r, corner_r)
        painter.restore()

        # 6. Center Hinge Split Groove
        groove_rect = QRect(rect.left(), y_mid - 1, rect.width(), 2)
        painter.fillRect(groove_rect, theme.hinge_groove)

        # 7. Side Hinge Notches
        notch_pen = QPen(theme.card_border, 1.0)
        painter.setPen(notch_pen)
        painter.setBrush(theme.bg_canvas)
        painter.drawEllipse(QPoint(rect.left(), y_mid), notch_r, notch_r)
        painter.drawEllipse(QPoint(rect.right(), y_mid), notch_r, notch_r)

        # 8. AM/PM Indicator
        if am_pm:
            ampm_font = get_modern_font("sans", size=max(10, int(rect.height() * 0.075)), weight=QFont.Weight.Bold)
            painter.setFont(ampm_font)
            painter.setPen(theme.text_muted)
            ampm_rect = QRect(rect.left() + int(rect.width() * 0.08), rect.bottom() - int(rect.height() * 0.16), 36, 18)
            painter.drawText(ampm_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, am_pm)

    def _get_pill_rect(self, rect: QRect) -> QRect:
        pill_h = 36
        pill_w = min(460, int(rect.width() * 0.65))
        pill_x = (rect.width() - pill_w) // 2
        pill_y = int(rect.height() * 0.70)
        return QRect(pill_x, pill_y, pill_w, pill_h)

    def _draw_progress_line(self, painter: QPainter, rect: QRect, theme) -> None:
        """Draw single discreet progress line: SUBJECT · XX / YY MIN with subtle dropdown affordance."""
        pill_rect = self._get_pill_rect(rect)

        painter.save()
        # Clean, quiet background pill
        pill_path = QPainterPath()
        pill_path.addRoundedRect(pill_rect, 18, 18)
        painter.fillPath(pill_path, QColor("#121215"))
        painter.setPen(QPen(QColor("#242428"), 1.0))
        painter.drawPath(pill_path)

        # Text: calm, readable
        font = get_modern_font("sans", size=13, weight=QFont.Weight.Normal)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(font)
        painter.setPen(QColor("#E4E4E7"))

        # Center text with subtle chevron indicating interactivity
        display_str = f"{self._secondary_text}   ▾"
        painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, display_str)
        painter.restore()

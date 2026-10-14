"""Custom QWidget displaying current local time and ambient study progress."""

from PySide6.QtCore import QTime, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPaintEvent, QPainter
from PySide6.QtWidgets import QWidget


class AmbientClockWidget(QWidget):
    """Minimal ambient flip-style clock widget drawn using QPainter.
    
    Renders current local time in large, clear white digits on a black background,
    with a discreet secondary line underneath for subject progress.
    Optimised for glanceability across the room on a 1366x768 screen.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._use_24h_format = True
        self._secondary_text: str = ""
        self._current_time_str = self._format_time(QTime.currentTime())

        # Setup 1-second update timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start()

    @property
    def secondary_text(self) -> str:
        return self._secondary_text

    @secondary_text.setter
    def secondary_text(self, text: str) -> None:
        if self._secondary_text != text:
            self._secondary_text = text
            self.update()

    @property
    def use_24h_format(self) -> bool:
        return self._use_24h_format

    @use_24h_format.setter
    def use_24h_format(self, value: bool) -> None:
        if self._use_24h_format != value:
            self._use_24h_format = value
            self._current_time_str = self._format_time(QTime.currentTime())
            self.update()

    def toggle_time_format(self) -> None:
        """Toggle between 24-hour and 12-hour display."""
        self.use_24h_format = not self._use_24h_format

    def _format_time(self, qtime: QTime) -> str:
        fmt = "HH:mm" if self._use_24h_format else "h:mm"
        return qtime.toString(fmt)

    def _on_timer_tick(self) -> None:
        """Check current time and trigger repaint only when the displayed minute changes."""
        new_time_str = self._format_time(QTime.currentTime())
        if new_time_str != self._current_time_str:
            self._current_time_str = new_time_str
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint background, large time digits, and discreet secondary line."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect()

        # Pure calm black background
        painter.fillRect(rect, QColor("#000000"))

        # Primary digit font scaling: ~22% of screen height
        time_font_size = max(48, int(rect.height() * 0.22))
        time_font = QFont()
        time_font.setFamilies([
            "DejaVu Sans",
            "Liberation Sans",
            "Segoe UI",
            "Helvetica Neue",
            "Arial",
            "Monospace",
        ])
        time_font.setPixelSize(time_font_size)
        time_font.setWeight(QFont.Weight.Medium)
        time_font.setStyleHint(QFont.StyleHint.SansSerif)

        # Shift clock slightly upwards if secondary line is present for vertical balance
        y_offset = -int(time_font_size * 0.25) if self._secondary_text else 0
        clock_rect = rect.translated(0, y_offset)

        # Draw time digits
        painter.setFont(time_font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(
            clock_rect,
            Qt.AlignmentFlag.AlignCenter,
            self._current_time_str,
        )

        # Subtle flip-clock horizontal crease across the digits
        metrics = painter.fontMetrics()
        text_bounding = metrics.boundingRect(clock_rect, Qt.AlignmentFlag.AlignCenter, self._current_time_str)
        crease_y = text_bounding.center().y()
        crease_height = max(1, int(time_font_size * 0.012))
        crease_margin = int(time_font_size * 0.05)
        crease_rect = text_bounding.adjusted(-crease_margin, 0, crease_margin, 0)
        crease_rect.setTop(crease_y - crease_height // 2)
        crease_rect.setHeight(crease_height)
        painter.fillRect(crease_rect, QColor("#000000"))

        # Discreet secondary line (Screen 1: e.g. "DATA VIS. · 25 / 60 MIN")
        if self._secondary_text:
            sub_font_size = max(14, int(time_font_size * 0.16))
            sub_font = QFont(time_font)
            sub_font.setPixelSize(sub_font_size)
            sub_font.setWeight(QFont.Weight.Normal)
            sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)

            sub_rect = rect.translated(0, y_offset + int(time_font_size * 0.70))
            painter.setFont(sub_font)
            painter.setPen(QColor("#8A8A8E"))  # Muted, low-contrast calm grey
            painter.drawText(
                sub_rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self._secondary_text,
            )

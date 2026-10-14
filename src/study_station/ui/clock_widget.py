"""Custom QWidget displaying current local time."""

from PySide6.QtCore import QTime, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPaintEvent, QPainter
from PySide6.QtWidgets import QWidget


class AmbientClockWidget(QWidget):
    """Minimal ambient clock widget drawn using QPainter.
    
    Renders current local time in large, clear white digits on a black background,
    optimised for glanceability and calm negative space.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._current_time_str = QTime.currentTime().toString("HH:mm")

        # Setup 1-second update timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start()

    def _on_timer_tick(self) -> None:
        """Check current time and trigger repaint only when the displayed minute changes."""
        new_time_str = QTime.currentTime().toString("HH:mm")
        if new_time_str != self._current_time_str:
            self._current_time_str = new_time_str
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint background and large centered time digits."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect()

        # Pure black calm background
        painter.fillRect(rect, QColor("#000000"))

        # Calculate dynamic font size suitable for 1366x768 and other aspect ratios.
        # Target ~22% of window height as digit height for calm, balanced proportions.
        font_pixel_size = max(48, int(rect.height() * 0.22))

        font = QFont()
        # Prefer clean, widely available sans/monospace fonts with tabular figures
        font.setFamilies([
            "DejaVu Sans",
            "Liberation Sans",
            "Segoe UI",
            "Helvetica Neue",
            "Arial",
            "Monospace",
        ])
        font.setPixelSize(font_pixel_size)
        font.setWeight(QFont.Weight.Medium)
        font.setStyleHint(QFont.StyleHint.SansSerif)

        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))

        # Draw centered time string (e.g., "21:08")
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignCenter,
            self._current_time_str,
        )

"""Main application window for Study Station."""

from datetime import datetime
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import QMainWindow

from study_station.core.engine import ScheduleEngine
from study_station.ui.clock_widget import AmbientClockWidget


class MainWindow(QMainWindow):
    """Full-screen ambient clock window for Study Station."""

    def __init__(self, engine: ScheduleEngine | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Study Station")
        self.resize(1366, 768)

        self._engine = engine

        # Black background palette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Central custom clock widget
        self._clock_widget = AmbientClockWidget(self)
        self.setCentralWidget(self._clock_widget)

        # Update secondary line from engine
        if self._engine:
            self._update_progress_line()
            self._status_timer = QTimer(self)
            self._status_timer.setInterval(30_000)  # Refresh every 30 seconds
            self._status_timer.timeout.connect(self._update_progress_line)
            self._status_timer.start()

    def _update_progress_line(self) -> None:
        """Fetch updated ambient status line from ScheduleEngine."""
        if self._engine:
            text = self._engine.get_ambient_status_text(datetime.now())
            self._clock_widget.secondary_text = text

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard shortcuts:
        
        - Esc or Q: Quit
        - F11: Toggle fullscreen
        - T: Toggle 12-hour / 24-hour time format
        """
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.close()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key.Key_T:
            self._clock_widget.toggle_time_format()
        else:
            super().keyPressEvent(event)

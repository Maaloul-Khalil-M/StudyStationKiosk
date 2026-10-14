"""Main application window for Study Station."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import QMainWindow

from study_station.ui.clock_widget import AmbientClockWidget


class MainWindow(QMainWindow):
    """Full-screen ambient clock window for Study Station."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Study Station")
        self.resize(1366, 768)

        # Set black background palette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Central custom clock widget
        self._clock_widget = AmbientClockWidget(self)
        self.setCentralWidget(self._clock_widget)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard shortcuts: Esc or Q to quit, F11 to toggle fullscreen."""
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.close()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)

"""Application entry point for Study Station."""

import sys
from PySide6.QtWidgets import QApplication

from study_station.ui.main_window import MainWindow


def run() -> int:
    """Initialise and run the Study Station application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Study Station")
    app.setOrganizationName("StudyStation")

    window = MainWindow()
    window.showFullScreen()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run())

"""Application entry point for Study Station."""

from pathlib import Path
import sys
from PySide6.QtWidgets import QApplication

from study_station.core.engine import ScheduleEngine
from study_station.ui.main_window import MainWindow


def run() -> int:
    """Initialise and run the Study Station application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Study Station")
    app.setOrganizationName("StudyStation")

    # Load timetable if available
    engine: ScheduleEngine | None = None
    sample_timetable = Path(__file__).resolve().parent.parent.parent / "docs" / "example.json"
    if sample_timetable.exists():
        try:
            engine = ScheduleEngine.from_json_file(sample_timetable)
        except Exception as exc:
            print(f"Warning: Could not load timetable from {sample_timetable}: {exc}")

    window = MainWindow(engine=engine)
    window.showFullScreen()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run())

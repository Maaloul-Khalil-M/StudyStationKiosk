"""Application entry point for Study Station."""

from pathlib import Path
import sys
from PySide6.QtWidgets import QApplication

from study_station.core.engine import ScheduleEngine
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.main_window import MainWindow


def run() -> int:
    """Initialise and run the Study Station application."""
    app = QApplication(sys.argv)
    from study_station.ui.theme import get_modern_font
    app.setFont(get_modern_font("sans", 13))
    app.setApplicationName("Study Station")
    app.setOrganizationName("StudyStation")

    # 1. Initialize SQLite persistence layer
    db = Database()
    repo = StudyStationRepository(db)

    # 2. Seed initial timetable from docs/example.json if database is empty
    sample_timetable = Path(__file__).resolve().parent.parent.parent / "docs" / "example.json"
    if sample_timetable.exists():
        repo.seed_timetable_if_empty(sample_timetable)

    # 3. Initialize ScheduleEngine powered by the persistent repository
    engine = ScheduleEngine.from_repository(repo)

    # 4. Create and show Main Window with recovery check
    window = MainWindow(engine=engine, repository=repo)
    window.showFullScreen()

    exit_code = app.exec()
    db.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(run())

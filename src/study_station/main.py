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
    from study_station.persistence.user_manager import UserManager
    user_manager = UserManager()
    active_user = user_manager.get_active_user()
    db_path = user_manager.get_user_db_path(active_user)
    db = Database(db_path)
    repo = StudyStationRepository(db)

    # 2. Seed initial timetable from docs/example.json ONLY on initial fresh install of Default user
    if user_manager.is_fresh_install and active_user == UserManager.DEFAULT_USER:
        from study_station.core.resources import get_sample_timetable_path
        sample_timetable = get_sample_timetable_path()
        if sample_timetable.exists():
            repo.seed_timetable_if_empty(sample_timetable)

    # 3. Initialize ScheduleEngine powered by the persistent repository
    engine = ScheduleEngine.from_repository(repo)

    # 4. Create and show Main Window with recovery check
    window = MainWindow(engine=engine, repository=repo, user_manager=user_manager)
    window.showFullScreen()

    exit_code = app.exec()
    db.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(run())

"""Unit tests for SQLite persistence and timer recovery."""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from study_station.core.models import AcademicSession, StudyLog, Subject, TimeSlot
from study_station.core.settings import AppSettings
from study_station.core.timer import FocusTimer
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository


class TestPersistence(unittest.TestCase):
    """Test SQLite database operations and timer state recovery."""

    def setUp(self) -> None:
        self.db = Database(":memory:")
        self.repo = StudyStationRepository(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def test_study_logs_crud(self) -> None:
        log1 = StudyLog(
            id="log-1",
            subject_name="Data Vis",
            study_cycle_id="cycle-1",
            started_at=datetime(2026, 10, 14, 10, 0),
            duration_minutes=25,
            source="timer",
        )
        self.repo.add_study_log(log1)

        logs = self.repo.get_all_study_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].id, "log-1")
        self.assertEqual(logs[0].subject_name, "Data Vis")
        self.assertEqual(logs[0].duration_minutes, 25)

    def test_subject_targets(self) -> None:
        self.repo.set_subject_target("Data Vis", 90)
        self.repo.set_subject_target("Math", 45)

        targets = self.repo.get_all_subject_targets()
        self.assertEqual(targets["Data Vis"], 90)
        self.assertEqual(targets["Math"], 45)

    def test_timetable_sessions(self) -> None:
        sessions = [
            AcademicSession(
                day="Lun",
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Data Vis", "TP"),
                location="Lab 20",
            ),
            AcademicSession(
                day="Mar",
                time_slot=TimeSlot("10:00", "11:30"),
                subject=Subject("Math", "Cours"),
                location="SC 1",
            ),
        ]
        self.repo.save_timetable_sessions(sessions)

        loaded = self.repo.get_timetable_sessions()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].subject.name, "Data Vis")
        self.assertEqual(loaded[1].subject.name, "Math")

    def test_app_settings(self) -> None:
        settings = AppSettings(
            use_24h=False,
            show_seconds=True,
            theme_id="slate",
        )
        self.repo.save_settings(settings)

        loaded = self.repo.load_settings()
        self.assertFalse(loaded.use_24h)
        self.assertTrue(loaded.show_seconds)
        self.assertEqual(loaded.theme_id, "slate")

    def test_timer_recovery_completed_while_away(self) -> None:
        timer = FocusTimer()
        timer.start("Data Vis", 15)
        # Simulate timer that completed in the past
        timer.target_end_time = datetime.now() - timedelta(minutes=5)
        self.repo.save_timer_state(timer)

        # Recover
        result = self.repo.recover_timer_state()
        self.assertIsNotNone(result)
        subject, completed_mins, total = result
        self.assertEqual(subject, "Data Vis")
        self.assertEqual(completed_mins, 15)
        self.assertIsNone(total)  # Marks it was fully completed

    def test_timer_recovery_still_running(self) -> None:
        timer = FocusTimer()
        timer.start("Data Vis", 25)
        timer.target_end_time = datetime.now() + timedelta(minutes=10)
        self.repo.save_timer_state(timer)

        result = self.repo.recover_timer_state()
        self.assertIsNotNone(result)
        subject, remaining_seconds, total = result
        self.assertEqual(subject, "Data Vis")
        self.assertGreater(remaining_seconds, 500)
        self.assertEqual(total, 25)


if __name__ == "__main__":
    unittest.main()

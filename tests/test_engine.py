"""Unit tests for ScheduleEngine and domain models."""

import sys
import unittest
from datetime import datetime, date, time
from pathlib import Path

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    StudyLog,
    Subject,
    TimeSlot,
)


class TestScheduleEngine(unittest.TestCase):
    """Test deterministic schedule calculations and study cycles."""

    def setUp(self) -> None:
        # Example schedule with 2 sessions of "Data Vis" on Monday and Friday
        self.session_mon = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Data Vis", "TP"),
            location="Lab 20",
        )
        self.session_fri = AcademicSession(
            day="Ven",
            time_slot=TimeSlot("10:00", "11:30"),
            subject=Subject("Data Vis", "Cours"),
            location="SC 1",
        )
        self.session_tue = AcademicSession(
            day="Mar",
            time_slot=TimeSlot("14:00", "15:30"),
            subject=Subject("Math", "TD"),
            location="SC 2",
        )
        self.engine = ScheduleEngine(
            sessions=[self.session_mon, self.session_tue, self.session_fri],
            default_target_minutes=60,
        )

    def test_current_session_detected(self) -> None:
        # Monday 08:30 -> In Data Vis class
        # 2026-10-19 is a Monday
        dt_in_class = datetime(2026, 10, 19, 8, 30)
        curr = self.engine.get_current_session(dt_in_class)
        self.assertIsNotNone(curr)
        self.assertEqual(curr.subject.name, "Data Vis")

        # Monday 09:45 -> Outside class
        dt_outside = datetime(2026, 10, 19, 9, 45)
        self.assertIsNone(self.engine.get_current_session(dt_outside))

    def test_next_session_detected(self) -> None:
        # Monday 10:00 -> Next class is Tuesday 14:00 Math
        dt = datetime(2026, 10, 19, 10, 0)
        next_sess, next_dt = self.engine.get_next_session(dt)
        self.assertEqual(next_sess.subject.name, "Math")
        self.assertEqual(next_dt, datetime(2026, 10, 20, 14, 0))

    def test_study_cycle_creation_and_progress(self) -> None:
        # Monday 11:00 -> Mon 09:30 class ended, next is Friday 10:00
        dt = datetime(2026, 10, 19, 11, 0)
        cycle = self.engine.get_active_cycle("Data Vis", dt)
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle.start_at, datetime(2026, 10, 19, 9, 30))
        self.assertEqual(cycle.end_at, datetime(2026, 10, 23, 10, 0))
        self.assertEqual(cycle.completed_minutes, 0)
        self.assertEqual(cycle.remaining_minutes, 60)

        # Log 25 minutes of study
        self.engine.add_study_log(
            StudyLog(
                subject_name="Data Vis",
                study_cycle_id=cycle.id,
                started_at=datetime(2026, 10, 20, 16, 0),
                duration_minutes=25,
            )
        )

        cycle_after = self.engine.get_active_cycle("Data Vis", dt)
        self.assertEqual(cycle_after.completed_minutes, 25)
        self.assertEqual(cycle_after.remaining_minutes, 35)

    def test_ambient_status_text(self) -> None:
        dt = datetime(2026, 10, 19, 11, 0)
        # Target 60, completed 0
        text = self.engine.get_ambient_status_text(dt)
        self.assertIn("0 / 60 MIN", text)

    def test_subject_summary(self) -> None:
        dt = datetime(2026, 10, 19, 11, 0)
        summary = self.engine.get_subject_summary("Data Vis", dt)
        self.assertEqual(summary.name, "Data Vis")
        self.assertEqual(summary.target_minutes, 60)
        self.assertEqual(summary.completed_minutes, 0)
        self.assertEqual(summary.remaining_minutes, 60)
        self.assertEqual(summary.progress_percent, 0)
        self.assertFalse(summary.is_target_met)
        self.assertIn("Fri at 10:00", summary.next_session_text)

    def test_all_subjects_summary(self) -> None:
        dt = datetime(2026, 10, 19, 11, 0)
        all_summaries = self.engine.get_all_subjects_summary(dt)
        self.assertEqual(len(all_summaries), 2)
        names = [s.name for s in all_summaries]
        self.assertIn("Data Vis", names)
        self.assertIn("Math", names)


    def test_calendar_week_dates(self) -> None:
        # 2026-10-15 is a Thursday
        d = date(2026, 10, 15)
        mon = ScheduleEngine.get_week_start(d)
        self.assertEqual(mon, date(2026, 10, 12))

        # 6-day academic week (Mon-Sat)
        week_dates = ScheduleEngine.get_week_dates(d, days_count=6)
        self.assertEqual(len(week_dates), 6)
        self.assertEqual(week_dates[0], date(2026, 10, 12))
        self.assertEqual(week_dates[-1], date(2026, 10, 17))

        # Check day date lookup
        self.assertEqual(ScheduleEngine.get_day_date("Jeu", d), date(2026, 10, 15))
        self.assertEqual(ScheduleEngine.get_day_date("Lun", d), date(2026, 10, 12))
        self.assertEqual(ScheduleEngine.get_day_date("Sam", d), date(2026, 10, 17))
        self.assertIsNone(ScheduleEngine.get_day_date("InvalidDay", d))

    def test_format_week_range(self) -> None:
        # Same month
        d1 = date(2026, 10, 15)
        self.assertEqual(ScheduleEngine.format_week_range(d1), "12 – 17 OCT 2026")

        # Cross month (Sep - Oct)
        d2 = date(2026, 10, 1)  # Thursday
        # Mon is Sep 28, Sat is Oct 3
        self.assertEqual(ScheduleEngine.format_week_range(d2), "28 SEP – 03 OCT 2026")

        # Cross year (Dec 2026 - Jan 2027)
        d3 = date(2026, 12, 31)  # Thursday
        # Mon is Dec 28 2026, Sat is Jan 02 2027
        self.assertEqual(ScheduleEngine.format_week_range(d3), "28 DEC 2026 – 02 JAN 2027")


if __name__ == "__main__":
    unittest.main()


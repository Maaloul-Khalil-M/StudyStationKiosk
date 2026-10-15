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

    def test_get_day_sessions(self) -> None:
        # Monday (Lun / 0): should return 1 session (Data Vis at 08:00)
        mon_sessions = self.engine.get_day_sessions(0)
        self.assertEqual(len(mon_sessions), 1)
        self.assertEqual(mon_sessions[0].subject.name, "Data Vis")

        # By day code string ("Lun")
        mon_by_str = self.engine.get_day_sessions("Lun")
        self.assertEqual(len(mon_by_str), 1)
        self.assertEqual(mon_by_str[0].subject.name, "Data Vis")

        # Wednesday (Mer / 2): should return 0 sessions
        mer_sessions = self.engine.get_day_sessions(2)
        self.assertEqual(len(mer_sessions), 0)

    def test_study_statistics_and_log_management(self) -> None:
        log1 = StudyLog(
            id="log-a",
            subject_name="Data Vis",
            started_at=datetime(2026, 10, 14, 10, 0),  # Wednesday of 12-18 Oct week
            duration_minutes=25,
            source="timer",
        )
        log2 = StudyLog(
            id="log-b",
            subject_name="Data Vis",
            started_at=datetime(2026, 10, 15, 14, 0),  # Thursday of same week
            duration_minutes=35,
            source="manual",
        )
        log3 = StudyLog(
            id="log-c",
            subject_name="Math",
            started_at=datetime(2026, 10, 5, 9, 0),  # Previous week
            duration_minutes=40,
            source="timer",
        )
        self.engine.add_study_log(log1)
        self.engine.add_study_log(log2)
        self.engine.add_study_log(log3)

        # Total minutes: 25 + 35 + 40 = 100
        self.assertEqual(self.engine.get_total_study_minutes(), 100)

        # Weekly minutes for Oct 14 week: 25 + 35 = 60
        ref_d = date(2026, 10, 14)
        self.assertEqual(self.engine.get_weekly_study_minutes(ref_d), 60)

        # Weekly breakdown by subject
        breakdown = self.engine.get_weekly_study_by_subject(ref_d)
        self.assertEqual(breakdown.get("Data Vis"), 60)
        self.assertNotIn("Math", breakdown)

        # Filtered logs
        timer_logs = self.engine.get_study_logs(source_filter="timer")
        self.assertEqual(len(timer_logs), 2)
        math_logs = self.engine.get_study_logs(subject_filter="Math")
        self.assertEqual(len(math_logs), 1)

        # Update log
        updated = self.engine.update_study_log("log-a", "Data Vis", 30)
        self.assertTrue(updated)
        self.assertEqual(self.engine.get_total_study_minutes(), 105)

        # Delete log
        deleted = self.engine.delete_study_log("log-c")
        self.assertTrue(deleted)
        self.assertEqual(self.engine.get_total_study_minutes(), 65)
    def test_upcoming_occurrences_with_spelling_variants_and_days(self) -> None:
        sessions = [
            AcademicSession(
                day="ven",  # lowercase french
                time_slot=TimeSlot("13:30", "15:00"),
                subject=Subject("Sécurité et controle d'accées aux Big data", "Cours"),
                location="SC 1",
            ),
            AcademicSession(
                day="Monday",  # full english
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Visualisation des données", "TP"),
                location="Lab 20",
            ),
        ]
        engine = ScheduleEngine(sessions=sessions)

        # Thursday night Oct 15, 2026 20:00
        thursday_night = datetime(2026, 10, 15, 20, 0)

        # 1. Day index resolution
        self.assertEqual(sessions[0].day_index, 4)  # Friday
        self.assertEqual(sessions[1].day_index, 0)  # Monday

        # 2. Upcoming occurrence with normalized accent spelling
        clean_query = "Sécurité et contrôle d'accès aux Big data"
        next_occ = engine.get_next_occurrence_of_subject(clean_query, thursday_night)
        self.assertIsNotNone(next_occ)
        session, next_dt = next_occ
        self.assertEqual(next_dt, datetime(2026, 10, 16, 13, 30))

        # 3. Next class deadline
        deadline = engine.get_next_class_deadline_for_subject(clean_query, thursday_night)
        self.assertEqual(deadline, datetime(2026, 10, 16, 13, 30))

        # 4. Weekend boundary lookahead: from Friday 16:00 to next Monday
        friday_afternoon = datetime(2026, 10, 16, 16, 0)
        next_mon_occ = engine.get_next_occurrence_of_subject("Visualisation des données", friday_afternoon)
        self.assertIsNotNone(next_mon_occ)
        _, next_mon_dt = next_mon_occ
        self.assertEqual(next_mon_dt, datetime(2026, 10, 19, 8, 0))


if __name__ == "__main__":
    unittest.main()


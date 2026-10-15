"""Unit tests for HistoryDialog and EditStudyLogDialog."""

from datetime import date, datetime, timedelta
from pathlib import Path
import sys
import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession, StudyCycle, StudyLog, Subject, TimeSlot
from study_station.ui.history_dialog import (
    EditStudyLogDialog,
    HistoryDialog,
    format_log_timestamp,
    format_minutes_hh_mm,
)


class TestHistoryDialog(unittest.TestCase):
    """Test the study history viewer, statistics calculations, and interactive editing."""

    def setUp(self) -> None:
        self.session_mon = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Data Vis", "TP"),
            location="Lab 20",
        )
        self.session_wed = AcademicSession(
            day="Mer",
            time_slot=TimeSlot("10:00", "11:30"),
            subject=Subject("Math", "Cours"),
            location="SC 1",
        )
        self.engine = ScheduleEngine(
            sessions=[self.session_mon, self.session_wed],
            default_target_minutes=60,
        )

        # Seed study logs
        # This week: Monday Oct 12 to Saturday Oct 17, 2026
        self.log1 = StudyLog(
            id="log-1",
            subject_name="Data Vis",
            started_at=datetime(2026, 10, 14, 9, 30),
            duration_minutes=25,
            source="timer",
        )
        self.log2 = StudyLog(
            id="log-2",
            subject_name="Data Vis",
            started_at=datetime(2026, 10, 15, 14, 0),
            duration_minutes=35,
            source="manual",
        )
        self.log3 = StudyLog(
            id="log-3",
            subject_name="Math",
            started_at=datetime(2026, 10, 5, 11, 0),  # Prior week
            duration_minutes=45,
            source="timer",
        )
        self.engine.add_study_log(self.log1)
        self.engine.add_study_log(self.log2)
        self.engine.add_study_log(self.log3)

    def test_format_helpers(self) -> None:
        self.assertEqual(format_minutes_hh_mm(0), "0m")
        self.assertEqual(format_minutes_hh_mm(45), "45m")
        self.assertEqual(format_minutes_hh_mm(60), "1h")
        self.assertEqual(format_minutes_hh_mm(90), "1h 30m")
        self.assertEqual(format_minutes_hh_mm(125), "2h 05m")

        today = date(2026, 10, 15)
        dt_today = datetime(2026, 10, 15, 14, 30)
        self.assertEqual(format_log_timestamp(dt_today, ref_date=today), "Today, 14:30")

        dt_yesterday = datetime(2026, 10, 14, 9, 15)
        self.assertEqual(format_log_timestamp(dt_yesterday, ref_date=today), "Yesterday, 09:15")

        dt_past = datetime(2026, 9, 28, 8, 0)
        self.assertIn("28 Sep", format_log_timestamp(dt_past, ref_date=today))

    def test_history_dialog_kpis_and_table(self) -> None:
        dialog = HistoryDialog(self.engine)
        self.assertIsNotNone(dialog)

        # Check total time formatted: 25 + 35 + 45 = 105 mins = 1h 45m
        self.assertEqual(dialog.lbl_kpi_total.text(), "1h 45m")

        # Initial table row count: 3 logs
        self.assertEqual(dialog.table.rowCount(), 3)
        self.assertIn("3 sessions recorded", dialog.lbl_session_count.text())

    def test_history_dialog_filtering(self) -> None:
        dialog = HistoryDialog(self.engine)

        # Filter by Math
        idx = dialog.cmb_subject_filter.findData("Math")
        self.assertGreaterEqual(idx, 0)
        dialog.cmb_subject_filter.setCurrentIndex(idx)
        self.assertEqual(dialog.table.rowCount(), 1)
        self.assertIn("1 session recorded", dialog.lbl_session_count.text())

        # Filter by All Subjects, then by Manual Source
        dialog.cmb_subject_filter.setCurrentIndex(0)  # All Subjects
        idx_manual = dialog.cmb_source_filter.findData("manual")
        dialog.cmb_source_filter.setCurrentIndex(idx_manual)
        self.assertEqual(dialog.table.rowCount(), 1)  # Only log2 is manual

        # Filter by Timer
        idx_timer = dialog.cmb_source_filter.findData("timer")
        dialog.cmb_source_filter.setCurrentIndex(idx_timer)
        self.assertEqual(dialog.table.rowCount(), 2)  # log1 and log3 are timer

    def test_edit_study_log_dialog(self) -> None:
        subjects = self.engine.get_distinct_subjects()
        edit_dlg = EditStudyLogDialog(self.log1, available_subjects=subjects)
        self.assertEqual(edit_dlg.spn_duration.value(), 25)

        # Change duration and subject
        edit_dlg.spn_duration.setValue(50)
        new_subj, new_mins = edit_dlg.get_updated_data()
        self.assertEqual(new_mins, 50)
        self.assertEqual(new_subj, "Data Vis")

    def test_history_dialog_update_and_delete(self) -> None:
        dialog = HistoryDialog(self.engine)
        initial_count = dialog.table.rowCount()
        self.assertEqual(initial_count, 3)

        # Update log programmatically and refresh
        self.engine.update_study_log("log-1", "Data Vis", 40)
        dialog.refresh_data()
        self.assertEqual(dialog.lbl_kpi_total.text(), "2h")  # 40 + 35 + 45 = 120 mins = 2h

        # Delete log programmatically and refresh
        self.engine.delete_study_log("log-3")
        dialog.refresh_data()
        self.assertEqual(dialog.table.rowCount(), 2)
        self.assertEqual(dialog.lbl_kpi_total.text(), "1h 15m")  # 40 + 35 = 75 mins


if __name__ == "__main__":
    unittest.main()

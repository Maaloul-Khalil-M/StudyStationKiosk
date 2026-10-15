"""Unit tests for secondary dialogs (Timetable, Targets, ManualLog)."""

from pathlib import Path
import sys
import unittest
from PySide6.QtWidgets import QApplication

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.models import AcademicSession, Subject, TimeSlot
from study_station.ui.manual_log_dialog import ManualLogDialog
from study_station.ui.targets_dialog import TargetsDialog
from study_station.ui.timetable_dialog import TimetableDialog


class TestSecondaryDialogs(unittest.TestCase):
    """Test secondary dialog controllers and signal outputs."""

    def test_manual_log_dialog(self) -> None:
        dialog = ManualLogDialog(subjects=["Data Vis", "Math"], default_subject="Math")
        self.assertEqual(dialog.cmb_subject.count(), 2)
        self.assertEqual(dialog.cmb_subject.currentData(), "Math")

        # Test logging
        logged_result = []
        dialog.time_logged.connect(lambda s, m: logged_result.append((s, m)))
        dialog.spn_minutes.setValue(45)
        dialog._on_save()

        self.assertEqual(len(logged_result), 1)
        self.assertEqual(logged_result[0], ("Math", 45))

    def test_targets_dialog(self) -> None:
        dialog = TargetsDialog(
            subjects=["Data Vis", "Math"],
            current_targets={"Data Vis": 90, "Math": 60},
        )
        self.assertIn("Data Vis", dialog._spinners)
        self.assertEqual(dialog._spinners["Data Vis"].value(), 90)

        # Update target
        dialog._spinners["Math"].setValue(75)

        saved_result = []
        dialog.targets_saved.connect(lambda d: saved_result.append(d))
        dialog._on_save()

        self.assertEqual(len(saved_result), 1)
        self.assertEqual(saved_result[0]["Math"], 75)

    def test_timetable_dialog(self) -> None:
        sessions = [
            AcademicSession(
                day="Lun",
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Data Vis", "TP"),
                location="Lab 20",
            )
        ]
        dialog = TimetableDialog(sessions=sessions)
        self.assertEqual(dialog.table.rowCount(), 1)

        # Test add new session
        dialog.cmb_day.setCurrentText("Mar")
        dialog.txt_start.setText("10:00")
        dialog.txt_end.setText("11:30")
        dialog.txt_subject.setText("Cyber")
        dialog.cmb_core.setCurrentText("Cours")
        dialog.txt_location.setText("SC 1")
        dialog._on_add()

        self.assertEqual(dialog.table.rowCount(), 2)

        # Test delete
        dialog.table.selectRow(0)
        dialog._on_delete()
        self.assertEqual(dialog.table.rowCount(), 1)

    def test_schedule_screen_widget_week_navigation(self) -> None:
        from datetime import date, timedelta
        from study_station.ui.schedule_screen_widget import ScheduleScreenWidget

        sessions = [
            AcademicSession(
                day="Lun",
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Data Vis", "TP"),
                location="Lab 20",
            )
        ]
        widget = ScheduleScreenWidget(sessions=sessions)
        initial_date = widget.current_view_date
        self.assertEqual(initial_date, date.today())
        self.assertFalse(widget.btn_today.isVisible())

        # Next week navigation
        widget.btn_next_week.click()
        self.assertEqual(widget.current_view_date, initial_date + timedelta(days=7))
        self.assertFalse(widget.btn_today.isHidden())

        # Jump back to Today
        widget.btn_today.click()
        self.assertEqual(widget.current_view_date, initial_date)
        self.assertTrue(widget.btn_today.isHidden())

        # Previous week navigation
        widget.btn_prev_week.click()
        self.assertEqual(widget.current_view_date, initial_date - timedelta(days=7))
        self.assertFalse(widget.btn_today.isHidden())


if __name__ == "__main__":
    unittest.main()

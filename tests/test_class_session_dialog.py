"""Unit tests for ClassSessionDialog and direct calendar interactions."""

from pathlib import Path
import sys
import unittest
from PySide6.QtWidgets import QApplication

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.models import AcademicSession, Subject, TimeSlot
from study_station.ui.class_session_dialog import ClassSessionDialog
from study_station.ui.schedule_screen_widget import ScheduleScreenWidget, EmptyGridSlot, ClassGridCard


class TestClassSessionDialog(unittest.TestCase):
    """Test the direct visual calendar editing dialog and interactions."""

    def setUp(self) -> None:
        self.session = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Data Vis", "TP"),
            location="Lab 20",
        )

    def test_add_mode_initialization_and_save(self) -> None:
        dialog = ClassSessionDialog(
            session=None,
            default_day="Jeu",
            default_start="13:30",
            default_end="15:00",
        )
        self.assertEqual(dialog.cmb_day.currentText(), "Jeu")
        self.assertEqual(dialog.txt_start.text(), "13:30")
        self.assertEqual(dialog.txt_end.text(), "15:00")
        self.assertFalse(hasattr(dialog, "btn_delete"))

        # Fill subject and location
        dialog.txt_subject.setText("Network Security")
        dialog.cmb_core.setCurrentText("COURS")
        dialog.txt_location.setText("Room 101")

        saved_emits = []
        dialog.session_saved.connect(lambda old, new: saved_emits.append((old, new)))
        dialog._on_save()

        self.assertEqual(len(saved_emits), 1)
        old_s, new_s = saved_emits[0]
        self.assertIsNone(old_s)
        self.assertEqual(new_s.subject.name, "Network Security")
        self.assertEqual(new_s.subject.core, "COURS")
        self.assertEqual(new_s.location, "Room 101")
        self.assertEqual(new_s.day, "Jeu")
        self.assertEqual(new_s.time_slot.start, "13:30")

    def test_edit_mode_initialization_and_save(self) -> None:
        dialog = ClassSessionDialog(session=self.session)
        self.assertEqual(dialog.txt_subject.text(), "Data Vis")
        self.assertEqual(dialog.txt_location.text(), "Lab 20")
        self.assertTrue(hasattr(dialog, "btn_delete"))
        self.assertTrue(hasattr(dialog, "btn_focus_action"))

        # Edit location
        dialog.txt_location.setText("Lab 21")

        saved_emits = []
        dialog.session_saved.connect(lambda old, new: saved_emits.append((old, new)))
        dialog._on_save()

        self.assertEqual(len(saved_emits), 1)
        old_s, new_s = saved_emits[0]
        self.assertEqual(old_s, self.session)
        self.assertEqual(new_s.location, "Lab 21")

    def test_delete_action(self) -> None:
        dialog = ClassSessionDialog(session=self.session)
        deleted_emits = []
        dialog.session_deleted.connect(lambda s: deleted_emits.append(s))
        dialog._on_delete()

        self.assertEqual(len(deleted_emits), 1)
        self.assertEqual(deleted_emits[0], self.session)

    def test_start_focus_action(self) -> None:
        dialog = ClassSessionDialog(session=self.session)
        focus_emits = []
        dialog.start_focus_requested.connect(lambda s: focus_emits.append(s))
        dialog._on_start_focus()

        self.assertEqual(len(focus_emits), 1)
        self.assertEqual(focus_emits[0], "Data Vis")

    def test_schedule_widget_direct_manipulation(self) -> None:
        widget = ScheduleScreenWidget(sessions=[self.session])
        self.assertEqual(len(widget._sessions), 1)

        # Edit session
        edited = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Data Vis 2", "TP"),
            location="Lab 99",
        )
        widget._on_session_edited(self.session, edited)
        self.assertEqual(len(widget._sessions), 1)
        self.assertEqual(widget._sessions[0].subject.name, "Data Vis 2")

        # Delete session
        widget._on_session_deleted(edited)
        self.assertEqual(len(widget._sessions), 0)

    def test_normalize_time_str_and_timeslot(self) -> None:
        from study_station.core.models import normalize_time_str
        self.assertEqual(normalize_time_str("8:00"), "08:00")
        self.assertEqual(normalize_time_str("08:00"), "08:00")
        self.assertEqual(normalize_time_str("8h30"), "08:30")
        self.assertEqual(normalize_time_str("14h"), "14:00")
        self.assertEqual(normalize_time_str("9"), "09:00")
        self.assertIsNone(normalize_time_str("25:00"))
        self.assertIsNone(normalize_time_str(""))
        self.assertIsNone(normalize_time_str("invalid"))

        # TimeSlot auto-normalization
        ts = TimeSlot(start="8:00", end="9:30")
        self.assertEqual(ts.start, "08:00")
        self.assertEqual(ts.end, "09:30")

    def test_class_session_dialog_validation_and_presets(self) -> None:
        dialog = ClassSessionDialog(session=None)
        # Test preset selection
        dialog._set_preset_time("09:40", "11:10")
        self.assertEqual(dialog.txt_start.text(), "09:40")
        self.assertEqual(dialog.txt_end.text(), "11:10")

        # Test empty subject validation
        dialog.txt_subject.setText("")
        saved = []
        dialog.session_saved.connect(lambda old, new: saved.append(new))
        dialog._on_save()
        self.assertEqual(len(saved), 0)
        self.assertFalse(dialog.lbl_error.isHidden())
        self.assertIn("subject name", dialog.lbl_error.text().lower())

        # Test invalid start/end times
        dialog.txt_subject.setText("Calculus")
        dialog.txt_start.setText("11:00")
        dialog.txt_end.setText("10:00")
        dialog._on_save()
        self.assertEqual(len(saved), 0)
        self.assertIn("before end time", dialog.lbl_error.text().lower())

    def test_schedule_widget_editor_table_and_quick_add(self) -> None:
        widget = ScheduleScreenWidget(sessions=[self.session])
        self.assertEqual(widget.table_sessions.rowCount(), 1)

        # Quick Add: pre-filled defaults exist
        self.assertEqual(widget.txt_start.text(), "08:00")
        self.assertEqual(widget.txt_end.text(), "09:30")

        # Quick Add: missing subject fails with warning
        widget.txt_subject.setText("")
        widget._on_add_session()
        self.assertEqual(len(widget._sessions), 1)
        self.assertIn("enter a subject name", widget.lbl_quick_status.text().lower())

        # Quick Add: fill subject and add successfully
        widget.txt_subject.setText("Operating Systems")
        widget.txt_location.setText("Lab 3")
        widget.cmb_core.setCurrentText("TP")
        widget._on_add_session()
        self.assertEqual(len(widget._sessions), 2)
        self.assertEqual(widget.table_sessions.rowCount(), 2)
        self.assertIn("successfully", widget.lbl_quick_status.text().lower())

        # Test preset slot combo changes times
        widget._on_preset_slot_changed(1)  # 09:40 - 11:10
        self.assertEqual(widget.txt_start.text(), "09:40")
        self.assertEqual(widget.txt_end.text(), "11:10")

        # Filter table
        widget.txt_filter.setText("Operating")
        # Row 0 (Data Vis) should be hidden, Row 1 (Operating Systems) visible
        self.assertTrue(widget.table_sessions.isRowHidden(0))
        self.assertFalse(widget.table_sessions.isRowHidden(1))
        widget.txt_filter.setText("")
        self.assertFalse(widget.table_sessions.isRowHidden(0))
        self.assertFalse(widget.table_sessions.isRowHidden(1))


if __name__ == "__main__":
    unittest.main()

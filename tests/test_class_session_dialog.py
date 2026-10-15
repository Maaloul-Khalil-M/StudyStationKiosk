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


if __name__ == "__main__":
    unittest.main()

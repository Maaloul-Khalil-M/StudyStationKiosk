"""Unit tests for Nightly Desk Debrief & Questionnaire Dialog (Milestone 11)."""

import os
import tempfile
import unittest
from datetime import date, datetime, timedelta

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.debrief_dialog import DebriefDialog

# Ensure QApplication exists for UI testing
app = QApplication.instance() or QApplication([])


class TestDebriefDialog(unittest.TestCase):
    """Test suite covering DebriefDialog workflows, stepping, template injection, and todo creation."""

    def setUp(self) -> None:
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.repo = StudyStationRepository(self.db)

        # Standard test timetable with Thursday (Jeu) classes
        self.sessions = [
            AcademicSession(
                day="Jeu",
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Sécurité Big Data", "TP"),
                location="Lab 5",
            ),
            AcademicSession(
                day="Jeu",
                time_slot=TimeSlot("09:40", "11:10"),
                subject=Subject("Entrepôts de données", "Cours"),
                location="SC 3",
            ),
            AcademicSession(
                day="Ven",
                time_slot=TimeSlot("10:00", "11:30"),
                subject=Subject("Framework Web", "CI"),
                location="SC 2",
            ),
        ]
        self.engine = ScheduleEngine(sessions=self.sessions, repository=self.repo)

    def tearDown(self) -> None:
        self.db.close()
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except OSError:
                pass

    def test_debrief_initialization_with_today_classes(self) -> None:
        # Thursday Oct 15, 2026 at 20:30 (evening desk time)
        ref_dt = datetime(2026, 10, 15, 20, 30)
        dialog = DebriefDialog(self.engine, ref_dt=ref_dt)

        self.assertEqual(len(dialog.distinct_subjects), 2)
        self.assertEqual(dialog.total_steps, 2)
        self.assertEqual(dialog.current_step, 0)
        self.assertEqual(dialog.lbl_step_badge.text(), "STEP 1 OF 2")
        self.assertIn("Sécurité", dialog.lbl_subject_header.text())
        dialog.close()

    def test_apply_template_prefix(self) -> None:
        ref_dt = datetime(2026, 10, 15, 20, 30)
        dialog = DebriefDialog(self.engine, ref_dt=ref_dt)

        dialog._apply_template_prefix("Fix lab exercise: ")
        self.assertEqual(dialog.txt_title.text(), "Fix lab exercise: ")

        # Append custom text
        dialog.txt_title.setText("Fix lab exercise: Docker container setup")
        self.assertEqual(dialog.txt_title.text(), "Fix lab exercise: Docker container setup")
        dialog.close()

    def test_multi_step_save_and_next_workflow(self) -> None:
        ref_dt = datetime(2026, 10, 15, 20, 30)
        dialog = DebriefDialog(self.engine, ref_dt=ref_dt)

        captured_signal = []
        dialog.debrief_completed.connect(lambda todos: captured_signal.extend(todos))

        # Step 1: Sécurité Big Data
        dialog.txt_title.setText("Review access control matrix")
        dialog.txt_notes.setText("Slide 22")
        dialog._on_save_next()

        # Should advance to Step 2
        self.assertEqual(dialog.current_step, 1)
        self.assertEqual(dialog.lbl_step_badge.text(), "STEP 2 OF 2")
        self.assertIn("Entrepôts", dialog.lbl_subject_header.text())

        # Step 2: Add 2 tasks for Entrepôts de données
        dialog.txt_title.setText("Fix ETL join script")
        dialog._on_add_another()  # saves 1st task and clears for 2nd
        self.assertEqual(len(dialog.created_todos), 2)

        dialog.txt_title.setText("Read chapter 3 on Snowflake Schema")
        dialog._on_save_next()  # saves 2nd task and finishes

        # Dialog should be finished
        self.assertEqual(len(dialog.created_todos), 3)
        self.assertEqual(len(captured_signal), 3)

        # Verify engine and repo persisted the tasks
        all_todos = self.engine.get_pending_todos()
        self.assertEqual(len(all_todos), 3)

        entrepots_todos = self.engine.get_pending_todos("Entrepôts de données")
        self.assertEqual(len(entrepots_todos), 2)
        dialog.close()

    def test_skip_subject(self) -> None:
        ref_dt = datetime(2026, 10, 15, 20, 30)
        dialog = DebriefDialog(self.engine, ref_dt=ref_dt)

        # Skip Step 1
        dialog._on_skip()
        self.assertEqual(dialog.current_step, 1)
        self.assertEqual(len(dialog.created_todos), 0)

        # Save Step 2
        dialog.txt_title.setText("Entrepôts lab prep")
        dialog._on_save_next()

        self.assertEqual(len(dialog.created_todos), 1)
        self.assertEqual(dialog.created_todos[0].subject_name, "Entrepôts de données")
        dialog.close()

    def test_custom_deadline_mode(self) -> None:
        ref_dt = datetime(2026, 10, 15, 20, 30)
        dialog = DebriefDialog(self.engine, ref_dt=ref_dt)

        dialog.radio_custom_date.setChecked(True)
        custom_qdate = QDate(2026, 11, 5)
        dialog.date_custom.setDate(custom_qdate)

        dialog.txt_title.setText("Midterm project deliverable")
        dialog._on_save_next()

        todo = dialog.created_todos[0]
        self.assertEqual(todo.due_date.year, 2026)
        self.assertEqual(todo.due_date.month, 11)
        self.assertEqual(todo.due_date.day, 5)
        dialog.close()

    def test_free_study_day_fallback(self) -> None:
        # Sunday Oct 18, 2026 (no scheduled classes)
        sunday_dt = datetime(2026, 10, 18, 19, 0)
        dialog = DebriefDialog(self.engine, ref_dt=sunday_dt)

        self.assertEqual(len(dialog.distinct_subjects), 0)
        self.assertEqual(dialog.lbl_step_badge.text(), "FREE STUDY DAY")
        self.assertFalse(dialog.manual_subject_container.isHidden())
        self.assertGreater(dialog.combo_subjects.count(), 0)

        dialog.combo_subjects.setCurrentText("Framework Web")
        dialog.txt_title.setText("Build REST endpoint")
        dialog._on_save_next()

        self.assertEqual(len(dialog.created_todos), 1)
        self.assertEqual(dialog.created_todos[0].subject_name, "Framework Web")
        dialog.close()


if __name__ == "__main__":
    unittest.main()

"""Unit tests for Todo-Driven Focus Loop & Cognitive Exit Ticket (Milestone 13).

Tests:
1. ExitTicketDialog action selection (complete, extend, put_aside).
2. ExitTicketDialog confidence rating (foggy, progressing, solid).
3. Question and Feynman takeaway capture.
4. FocusWidget task title & due date presentation.
5. MainWindow exit ticket completion, continuation sprint (extend), and question pinning.
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    ExitTicketResult,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.core.timer import FocusTimer
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.exit_ticket_dialog import ExitTicketDialog
from study_station.ui.focus_widget import FocusWidget
from study_station.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])


class TestExitTicket(unittest.TestCase):
    """Test suite for Cognitive Exit Ticket dialog and task-tethered focus loop."""

    def setUp(self) -> None:
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.repo = StudyStationRepository(self.db)

        self.session_db = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Entrepôts de données", "Cours"),
            location="SC 1",
        )
        self.engine = ScheduleEngine(sessions=[self.session_db], repository=self.repo)

    def tearDown(self) -> None:
        self.db.close()
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except OSError:
                pass

    def test_exit_ticket_dialog_defaults_and_selection(self) -> None:
        """Verify default choices, action toggles, and traffic-light confidence selection."""
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Fix Star Schema join exercise",
            due_date=datetime.now() + timedelta(days=7),
            status="pending",
        )

        dialog = ExitTicketDialog(
            subject_name="Entrepôts de données",
            elapsed_minutes=15,
            todo=todo,
        )

        # Default state
        self.assertEqual(dialog.selected_action, "complete")
        self.assertEqual(dialog.selected_confidence, "solid")

        # Toggle action: extend
        dialog.btn_act_extend.click()
        self.assertEqual(dialog.selected_action, "extend")

        # Toggle action: put_aside
        dialog.btn_act_aside.click()
        self.assertEqual(dialog.selected_action, "put_aside")

        # Toggle confidence: foggy
        dialog.btn_conf_foggy.click()
        self.assertEqual(dialog.selected_confidence, "foggy")

        # Toggle confidence: progressing
        dialog.btn_conf_prog.click()
        self.assertEqual(dialog.selected_confidence, "progressing")

        # Enter question and takeaway
        dialog.txt_question.setText("Why does the surrogate key avoid natural key instability?")
        dialog.txt_takeaway.setText("Surrogate keys decouple the warehouse from operational DB changes.")

        # Test result property
        res = dialog.result
        self.assertEqual(res.action, "put_aside")
        self.assertEqual(res.confidence, "progressing")
        self.assertEqual(res.next_class_question, "Why does the surrogate key avoid natural key instability?")
        self.assertEqual(res.takeaway_note, "Surrogate keys decouple the warehouse from operational DB changes.")

    def test_exit_ticket_submission_signal(self) -> None:
        """Verify ticket_submitted signal emission on save."""
        dialog = ExitTicketDialog(
            subject_name="Entrepôts de données",
            elapsed_minutes=15,
        )
        dialog.txt_question.setText("Explain star vs snowflake performance.")

        submitted = []
        dialog.ticket_submitted.connect(lambda r: submitted.append(r))
        dialog._on_save_clicked()

        self.assertEqual(len(submitted), 1)
        self.assertEqual(submitted[0].next_class_question, "Explain star vs snowflake performance.")
        self.assertEqual(submitted[0].action, "complete")

    def test_focus_widget_task_presentation(self) -> None:
        """Verify FocusWidget displays task title and due date when todo is passed."""
        timer = FocusTimer()
        widget = FocusWidget(timer=timer)

        due = datetime(2026, 10, 22, 9, 40)
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Build star schema SQL script",
            due_date=due,
            status="pending",
        )

        # Start session with todo
        widget.start_session("Entrepôts de données", 15, todo=todo)
        self.assertFalse(widget.lbl_task_title.isHidden())
        self.assertIn("Build star schema SQL script", widget.lbl_task_title.text())
        self.assertFalse(widget.lbl_task_due.isHidden())
        self.assertIn("Oct 22", widget.lbl_task_due.text())

        # Start session without todo
        widget.start_session("Entrepôts de données", 15, todo=None)
        self.assertTrue(widget.lbl_task_title.isHidden())
        self.assertTrue(widget.lbl_task_due.isHidden())

    def test_main_window_exit_ticket_complete_workflow(self) -> None:
        """Verify task completion and question persistence via ExitTicketResult."""
        window = MainWindow(engine=self.engine, repository=self.repo)

        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Debug ETL pipeline",
            status="pending",
        )
        self.engine.add_todo(todo)

        # Simulate focus session start with todo
        window._on_start_todo_focus(todo, duration_minutes=15)
        self.assertEqual(window._active_todo.id, todo.id)

        # Mock open_exit_ticket_dialog to return a completed result with question & takeaway
        mock_result = ExitTicketResult(
            action="complete",
            confidence="solid",
            next_class_question="How does columnar indexing optimize aggregation?",
            takeaway_note="ETL completed and loaded fact table successfully.",
        )
        window.open_exit_ticket_dialog = lambda *args, **kwargs: mock_result

        # Finish session via prompt_exit_ticket_and_finish
        window.prompt_exit_ticket_and_finish("Entrepôts de données", 15)

        # Verify todo is now completed in engine
        saved_todo = self.repo.get_todo_by_id(todo.id)
        self.assertIsNotNone(saved_todo)
        self.assertTrue(saved_todo.is_completed)
        self.assertEqual(saved_todo.confidence, "solid")
        self.assertEqual(saved_todo.next_class_question, "How does columnar indexing optimize aggregation?")
        self.assertIn("ETL completed", saved_todo.notes)

        # Verify question is accessible for in-class HUD
        questions = self.engine.get_subject_questions("Entrepôts de données")
        self.assertIn("How does columnar indexing optimize aggregation?", questions)

    def test_main_window_exit_ticket_extend_workflow(self) -> None:
        """Verify action 'extend' launches an immediate continuation sprint."""
        window = MainWindow(engine=self.engine, repository=self.repo)

        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Complex indexing optimization",
            status="pending",
        )
        self.engine.add_todo(todo)
        window._on_start_todo_focus(todo, duration_minutes=15)

        # Student needs 10 more minutes
        mock_result = ExitTicketResult(
            action="extend",
            confidence="progressing",
            extend_minutes=10,
        )
        window.open_exit_ticket_dialog = lambda *args, **kwargs: mock_result

        window.prompt_exit_ticket_and_finish("Entrepôts de données", 15)

        # 15m should be logged
        logs = self.engine.get_study_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].duration_minutes, 15)
        self.assertEqual(logs[0].todo_id, todo.id)

        # Timer should be running again for 10 minutes on the same task
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_FOCUS)
        self.assertEqual(window._timer.total_duration_minutes, 10)
        self.assertEqual(window._active_todo.id, todo.id)

    def test_main_window_exit_ticket_put_aside_workflow(self) -> None:
        """Verify action 'put_aside' leaves task pending with saved confidence and takeaway."""
        window = MainWindow(engine=self.engine, repository=self.repo)

        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Map snowflake dimensions",
            status="pending",
        )
        self.engine.add_todo(todo)
        window._on_start_todo_focus(todo, duration_minutes=15)

        mock_result = ExitTicketResult(
            action="put_aside",
            confidence="foggy",
            next_class_question="Why do snowflake dimensions increase query complexity?",
            takeaway_note="Reached dimension table 3, stopped before fact join.",
        )
        window.open_exit_ticket_dialog = lambda *args, **kwargs: mock_result

        window.prompt_exit_ticket_and_finish("Entrepôts de données", 15)

        # Task remains pending
        saved_todo = self.repo.get_todo_by_id(todo.id)
        self.assertFalse(saved_todo.is_completed)
        self.assertEqual(saved_todo.confidence, "foggy")
        self.assertEqual(saved_todo.next_class_question, "Why do snowflake dimensions increase query complexity?")
        self.assertIn("Reached dimension table 3", saved_todo.notes)


if __name__ == "__main__":
    unittest.main()

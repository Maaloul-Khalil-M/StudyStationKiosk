"""Unit tests for Night Routine Ambient UX & In-Class Payoff (Milestone 14).

Tests:
1. should_prompt_nightly_debrief timing & condition logic (evening, classes attended, un-debriefed).
2. Debrief completion persistence in SQLite repository (mark_day_debriefed, is_day_debriefed).
3. get_priority_study_todo ranking (overdue tasks first, nearest due date next).
4. Question resolution in engine and repository (resolve_subject_question, clear_subject_question).
5. ScheduleScreenWidget debrief banner, dismissal, and Tonight's Priority Task 1-click focus start.
6. ClassGridCard in-class HUD badge ("❓ ASK IN CLASS") and SubjectPreparationSheet payoff resolution.
"""

import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton, QLabel

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.schedule_screen_widget import ClassGridCard, ScheduleScreenWidget
from study_station.ui.subject_preparation_sheet import SubjectPreparationSheet

app = QApplication.instance() or QApplication([])


class TestNightRoutineHud(unittest.TestCase):
    """Test suite for Milestone 14: Evening Desk Routine & In-Class Question Payoff."""

    def setUp(self) -> None:
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.repo = StudyStationRepository(self.db)

        # Monday session: Entrepôts de données (08:00 - 09:30)
        self.session_mon = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Entrepôts de données", "Cours"),
            location="SC 1",
        )
        # Tuesday session: Sécurité logicielle (11:15 - 12:45)
        self.session_tue = AcademicSession(
            day="Mar",
            time_slot=TimeSlot("11:15", "12:45"),
            subject=Subject("Sécurité logicielle", "TP"),
            location="Lab 5",
        )
        self.engine = ScheduleEngine(
            sessions=[self.session_mon, self.session_tue],
            repository=self.repo,
        )

    def tearDown(self) -> None:
        self.db.close()
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except OSError:
                pass

    def test_nightly_debrief_decision_logic(self) -> None:
        """Verify prompt condition: evening hours, classes attended, not debriefed."""
        # 2026-10-12 is a Monday (has session_mon)
        mon_afternoon = datetime(2026, 10, 12, 14, 30)  # Daytime -> False
        mon_evening = datetime(2026, 10, 12, 19, 30)    # Evening with class -> True
        # 2026-10-18 is a Sunday (no classes)
        sun_evening = datetime(2026, 10, 18, 20, 0)     # No class today -> False

        self.assertFalse(self.engine.should_prompt_nightly_debrief(mon_afternoon))
        self.assertTrue(self.engine.should_prompt_nightly_debrief(mon_evening))
        self.assertFalse(self.engine.should_prompt_nightly_debrief(sun_evening))

        # Mark debriefed -> subsequent checks must return False
        self.engine.mark_day_debriefed(mon_evening.date())
        self.assertTrue(self.engine.is_day_debriefed(mon_evening.date()))
        self.assertFalse(self.engine.should_prompt_nightly_debrief(mon_evening))

        # Verify SQLite persistence
        self.assertTrue(self.repo.is_day_debriefed(mon_evening.date()))
        self.assertFalse(self.repo.is_day_debriefed(date(2026, 10, 13)))

    def test_priority_study_todo_ranking(self) -> None:
        """Verify priority task ranking: overdue > earliest due date > completed excluded."""
        now = datetime(2026, 10, 15, 20, 0)

        # Overdue todo
        todo_overdue = StudyTodo(
            subject_name="Entrepôts de données",
            title="Overdue task",
            due_date=now - timedelta(hours=3),
            status="pending",
        )
        # Due tomorrow
        todo_tomorrow = StudyTodo(
            subject_name="Sécurité logicielle",
            title="Tomorrow lab prep",
            due_date=now + timedelta(days=1),
            status="pending",
        )
        # Due next week
        todo_next_week = StudyTodo(
            subject_name="Entrepôts de données",
            title="Long-term project",
            due_date=now + timedelta(days=7),
            status="pending",
        )
        # Completed todo
        todo_done = StudyTodo(
            subject_name="Sécurité logicielle",
            title="Finished exercise",
            due_date=now - timedelta(days=1),
            status="completed",
        )

        self.engine.add_todo(todo_next_week)
        self.engine.add_todo(todo_tomorrow)
        self.engine.add_todo(todo_overdue)
        self.engine.add_todo(todo_done)

        # 1. Overdue task must be picked first
        priority = self.engine.get_priority_study_todo(now)
        self.assertIsNotNone(priority)
        self.assertEqual(priority.id, todo_overdue.id)
        self.assertEqual(priority.title, "Overdue task")

        # 2. Mark overdue completed -> earliest upcoming (tomorrow) is picked next
        self.engine.mark_todo_completed(todo_overdue.id)
        priority_next = self.engine.get_priority_study_todo(now)
        self.assertIsNotNone(priority_next)
        self.assertEqual(priority_next.id, todo_tomorrow.id)

        # 3. Mark all pending completed -> returns None
        self.engine.mark_todo_completed(todo_tomorrow.id)
        self.engine.mark_todo_completed(todo_next_week.id)
        self.assertIsNone(self.engine.get_priority_study_todo(now))

    def test_question_capture_and_resolution(self) -> None:
        """Verify questions formulation, retrieval, and in-class resolution."""
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Review Star Schema",
            due_date=datetime(2026, 10, 22, 9, 40),
            status="completed",
            next_class_question="Why use surrogate keys instead of natural keys in dimension tables?",
        )
        self.engine.add_todo(todo)

        # Check retrieval
        questions = self.engine.get_subject_questions("Entrepôts de données")
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0], "Why use surrogate keys instead of natural keys in dimension tables?")

        # Check repo retrieval
        repo_questions = self.repo.get_questions_by_subject("Entrepôts de données")
        self.assertEqual(len(repo_questions), 1)
        self.assertEqual(repo_questions[0], questions[0])

        # Resolve question
        resolved = self.engine.resolve_subject_question(
            "Entrepôts de données",
            "Why use surrogate keys instead of natural keys in dimension tables?",
        )
        self.assertTrue(resolved)

        # Verify cleared from memory
        self.assertEqual(len(self.engine.get_subject_questions("Entrepôts de données")), 0)

        # Verify cleared from SQLite
        self.assertEqual(len(self.repo.get_questions_by_subject("Entrepôts de données")), 0)

    def test_schedule_screen_widget_banners(self) -> None:
        """Verify debrief banner display, dismissal, and Tonight's Priority Task 1-click focus."""
        # Add a priority task
        now = datetime.now()
        urgent_todo = StudyTodo(
            subject_name="Sécurité logicielle",
            title="Patch buffer overflow in Lab 3",
            due_date=now + timedelta(hours=12),
            status="pending",
        )
        self.engine.add_todo(urgent_todo)

        widget = ScheduleScreenWidget(sessions=self.engine.sessions, engine=self.engine)

        # Verify priority task card is populated and visible
        self.assertFalse(widget.priority_task_card.isHidden())
        self.assertIn("Patch buffer overflow", widget.lbl_priority_title.text())
        self.assertIn("Sécurité logicielle", widget.lbl_priority_title.text())

        # Test 1-click focus start signal
        received_todo = []
        received_duration = []
        widget.start_todo_focus_requested.connect(
            lambda t, d: (received_todo.append(t), received_duration.append(d))
        )
        widget.btn_priority_focus.click()
        self.assertEqual(len(received_todo), 1)
        self.assertEqual(received_todo[0].id, urgent_todo.id)
        self.assertEqual(received_duration[0], 15)

        # Test debrief banner dismissal
        widget._debrief_banner_dismissed = False
        widget.debrief_banner.show()
        self.assertFalse(widget.debrief_banner.isHidden())

        # Find dismiss button in debrief banner
        dismiss_btn = None
        for child in widget.debrief_banner.findChildren(QPushButton):
            if child.text() == "✕":
                dismiss_btn = child
                break
        self.assertIsNotNone(dismiss_btn)
        dismiss_btn.click()
        self.assertTrue(widget.debrief_banner.isHidden())
        self.assertTrue(widget._debrief_banner_dismissed)

    def test_class_grid_card_in_class_hud(self) -> None:
        """Verify in-class HUD badge on class card when session is active and has questions."""
        # Add a question for Entrepôts de données
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Task with question",
            due_date=datetime.now(),
            status="completed",
            next_class_question="How does snowflake schema impact ETL performance?",
        )
        self.engine.add_todo(todo)

        # In-class active card
        card_active = ClassGridCard(
            session=self.session_mon,
            is_current=True,
            engine=self.engine,
        )
        # Search labels for the in-class HUD badge
        badges = [lbl.text() for lbl in card_active.findChildren(QLabel)]
        self.assertTrue(any("ASK IN CLASS" in b for b in badges))

        # Inactive card (same subject, not in class right now)
        card_inactive = ClassGridCard(
            session=self.session_mon,
            is_current=False,
            engine=self.engine,
        )
        inactive_badges = [lbl.text() for lbl in card_inactive.findChildren(QLabel)]
        self.assertTrue(any("❓ 1" in b for b in inactive_badges))
        self.assertFalse(any("ASK IN CLASS" in b for b in inactive_badges))

    def test_subject_preparation_sheet_question_resolution(self) -> None:
        """Verify SubjectPreparationSheet renders questions and resolves them via '✓ Asked' button."""
        q_text = "What is the penalty of normalization in OLAP?"
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Read Chapter 4",
            due_date=datetime.now(),
            status="completed",
            next_class_question=q_text,
        )
        self.engine.add_todo(todo)

        sheet = SubjectPreparationSheet(
            session=self.session_mon,
            engine=self.engine,
        )
        self.assertFalse(sheet.questions_frame.isHidden())

        # Find the "✓ Asked" button
        asked_btn = None
        for btn in sheet.questions_frame.findChildren(QPushButton):
            if "Asked" in btn.text():
                asked_btn = btn
                break
        self.assertIsNotNone(asked_btn)

        # Click Asked button -> triggers resolution
        asked_btn.click()

        # Engine must now have 0 questions for this subject
        self.assertEqual(len(self.engine.get_subject_questions("Entrepôts de données")), 0)
        # And sheet's questions frame should be hidden now that no questions remain
        self.assertTrue(sheet.questions_frame.isHidden())


if __name__ == "__main__":
    unittest.main()

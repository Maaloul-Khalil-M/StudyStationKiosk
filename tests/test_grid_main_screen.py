"""Unit tests for Weekly Schedule Grid as Main Station (Milestone 12).

Tests:
1. ClassGridCard preparation badges (DUE, TODO, READY, ❓ questions).
2. SubjectPreparationSheet task checklist, inline creation, completion, and 1-click focus launcher.
3. ScheduleScreenWidget cockpit interactions (ambient requested, debrief requested, navigation).
4. MainWindow cockpit integration, stack index 0, and todo-tethered focus session logging.
"""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.main_window import MainWindow
from study_station.ui.schedule_screen_widget import ClassGridCard, ScheduleScreenWidget
from study_station.ui.subject_preparation_sheet import SubjectPreparationSheet

# Ensure single shared QApplication instance
app = QApplication.instance() or QApplication([])


class TestGridMainScreen(unittest.TestCase):
    """Test suite for Milestone 12 Academic Cockpit features."""

    def setUp(self) -> None:
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.repo = StudyStationRepository(self.db)

        self.session_sec = AcademicSession(
            day="Jeu",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Sécurité Big Data", "TP"),
            location="Lab 5",
        )
        self.session_data = AcademicSession(
            day="Jeu",
            time_slot=TimeSlot("09:40", "11:10"),
            subject=Subject("Entrepôts de données", "Cours"),
            location="SC 3",
        )
        self.session_web = AcademicSession(
            day="Ven",
            time_slot=TimeSlot("10:00", "11:30"),
            subject=Subject("Framework Web", "CI"),
            location="SC 2",
        )
        self.sessions = [self.session_sec, self.session_data, self.session_web]
        self.engine = ScheduleEngine(sessions=self.sessions, repository=self.repo)

    def tearDown(self) -> None:
        self.db.close()
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except OSError:
                pass

    def test_class_grid_card_badges(self) -> None:
        """Verify ClassGridCard badge rendering across various todo and question states."""
        # Case 1: Fresh subject, no todos, no questions
        card1 = ClassGridCard(self.session_sec, engine=self.engine)
        labels1 = [w.text() for w in card1.findChildren(QLabel)]
        self.assertFalse(any("TODO" in l or "DUE" in l or "READY" in l for l in labels1))

        # Case 2: Subject with regular pending todo (due next week)
        todo1 = StudyTodo(
            subject_name="Sécurité Big Data",
            title="Configure SSL tunnel",
            due_date=datetime.now() + timedelta(days=5),
            status="pending",
        )
        self.engine.add_todo(todo1)

        card2 = ClassGridCard(self.session_sec, engine=self.engine)
        labels2 = [w.text() for w in card2.findChildren(QLabel)]
        self.assertTrue(any("● 1 TODO" in l for l in labels2))

        # Case 3: Subject with urgent todo due within 24 hours
        todo_urgent = StudyTodo(
            subject_name="Sécurité Big Data",
            title="Submit lab report",
            due_date=datetime.now() + timedelta(hours=6),
            status="pending",
        )
        self.engine.add_todo(todo_urgent)

        card3 = ClassGridCard(self.session_sec, engine=self.engine)
        labels3 = [w.text() for w in card3.findChildren(QLabel)]
        self.assertTrue(any("● 2 DUE" in l for l in labels3))

        # Case 4: Complete all todos -> shows ✓ READY
        self.engine.mark_todo_completed(todo1.id)
        self.engine.mark_todo_completed(todo_urgent.id)

        card4 = ClassGridCard(self.session_sec, engine=self.engine)
        labels4 = [w.text() for w in card4.findChildren(QLabel)]
        self.assertTrue(any("✓ READY" in l for l in labels4))

        # Case 5: In-class question badge
        todo_q = StudyTodo(
            subject_name="Sécurité Big Data",
            title="Kerberos analysis",
            next_class_question="Why does kerberos fail on NAT?",
            status="completed",
        )
        self.engine.add_todo(todo_q)
        card5 = ClassGridCard(self.session_sec, engine=self.engine)
        labels5 = [w.text() for w in card5.findChildren(QLabel)]
        self.assertTrue(any("❓ 1" in l for l in labels5))

    def test_subject_preparation_sheet_workflow(self) -> None:
        """Test opening preparation sheet, adding tasks, completing tasks, and emitting focus."""
        todo = StudyTodo(
            subject_name="Sécurité Big Data",
            title="Read iptables lab guide",
            due_date=datetime.now() + timedelta(days=2),
            status="pending",
        )
        self.engine.add_todo(todo)

        sheet = SubjectPreparationSheet(self.session_sec, self.engine)
        self.assertIn("Sécurité Big Data", sheet.lbl_title.text())
        self.assertIn("PREPARATION TASKS (1 pending)", sheet.lbl_tasks_header.text())

        # Test adding an inline task
        sheet.txt_new_task.setText("Review snort packet captures")
        sheet._on_add_task()

        pending = self.engine.get_pending_todos("Sécurité Big Data")
        self.assertEqual(len(pending), 2)
        titles = [t.title for t in pending]
        self.assertIn("Review snort packet captures", titles)

        # Test 1-click focus emission for a task
        focus_emitted = []
        sheet.start_task_focus_requested.connect(lambda t, m: focus_emitted.append((t, m)))
        sheet._on_focus_task(todo)
        self.assertEqual(len(focus_emitted), 1)
        self.assertEqual(focus_emitted[0][0].id, todo.id)
        self.assertEqual(focus_emitted[0][1], 15)

        # Test completing a task
        sheet._on_mark_completed(todo)
        completed = [t for t in self.engine.get_todos("Sécurité Big Data") if t.is_completed]
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].id, todo.id)

    def test_schedule_screen_widget_cockpit_signals(self) -> None:
        """Test ScheduleScreenWidget top header action signals and navigation."""
        widget = ScheduleScreenWidget(sessions=self.sessions, engine=self.engine)

        ambient_emitted = []
        debrief_emitted = []
        widget.ambient_requested.connect(lambda: ambient_emitted.append(True))
        widget.open_debrief_requested.connect(lambda: debrief_emitted.append(True))

        widget.btn_ambient.click()
        self.assertEqual(len(ambient_emitted), 1)

        widget.btn_debrief.click()
        self.assertEqual(len(debrief_emitted), 1)

        # Test week navigation
        initial_date = widget.current_view_date
        widget._on_next_week()
        self.assertEqual(widget.current_view_date, initial_date + timedelta(days=7))
        widget._on_prev_week()
        self.assertEqual(widget.current_view_date, initial_date)

    def test_main_window_cockpit_stack_and_session_logging(self) -> None:
        """Test MainWindow boots to Cockpit Grid and logs todo-tethered focus sessions."""
        window = MainWindow(engine=self.engine, repository=self.repo)

        # 1. Main station is Cockpit Grid (Index 0)
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_GRID)

        # 2. Switch to ambient clock screensaver mode (Index 3)
        window._show_ambient_clock()
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_AMBIENT_CLOCK)

        # 3. Return to cockpit
        window._show_cockpit_screen()
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_GRID)

        # 4. Start 1-click focus session tethered to a todo
        todo = StudyTodo(
            subject_name="Sécurité Big Data",
            title="Complete iptables lab",
            status="pending",
        )
        self.engine.add_todo(todo)

        window._on_start_todo_focus(todo, duration_minutes=15)
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_FOCUS)
        self.assertEqual(window._timer.subject_name, "Sécurité Big Data")
        self.assertEqual(window._active_todo.id, todo.id)

        # 5. Finish session -> study log is recorded with todo_id
        window._on_session_finished("Sécurité Big Data", 15)
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_COMPLETION)

        logs = self.engine.get_study_logs()
        self.assertTrue(len(logs) > 0)
        last_log = logs[-1]
        self.assertEqual(last_log.subject_name, "Sécurité Big Data")
        self.assertEqual(last_log.duration_minutes, 15)
        self.assertEqual(last_log.todo_id, todo.id)

        # 6. Return to cockpit after completion dismissal
        window._show_cockpit_screen()
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_GRID)

    def test_pure_cells_grid_without_left_column(self) -> None:
        """Verify grid layout eliminates left text column and maps 6 days to col 0..5."""
        widget = ScheduleScreenWidget(sessions=self.sessions, engine=self.engine)
        
        # Verify no widget in layout has text "TIME"
        labels = [w.text() for w in widget.grid_container.findChildren(QLabel)]
        self.assertNotIn("TIME", labels)

        # Verify Day Headers occupy columns 0 through 5
        self.assertEqual(widget.grid_layout.columnCount(), 6)
        for col in range(6):
            self.assertEqual(widget.grid_layout.columnStretch(col), 1)

    def test_dynamic_time_slots_and_scrollable_container(self) -> None:
        """Verify dynamic time slot collection and scrollable container height sizing."""
        extra_session = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("17:00", "18:30"),
            subject=Subject("Machine Learning Lab", "TP"),
            location="Lab 10",
        )
        sessions_with_extra = list(self.sessions) + [extra_session]
        widget = ScheduleScreenWidget(sessions=sessions_with_extra, engine=self.engine)

        active_slots = widget._get_active_time_slots()
        # self.sessions contains 1 non-default slot ("10:00 - 11:30") + extra_session ("17:00 - 18:30")
        self.assertEqual(len(active_slots), len(widget.DEFAULT_TIME_SLOTS) + 2)
        self.assertTrue(any(s[0] == "17:00" and s[1] == "18:30" for s in active_slots))

        # Check scroll area configuration
        self.assertEqual(widget.grid_scroll.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.assertEqual(widget.grid_scroll.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Minimum height should comfortably accommodate all slot rows
        expected_min = 40 + len(active_slots) * (86 + 6) + 10
        self.assertEqual(widget.grid_container.minimumHeight(), expected_min)

    def test_compact_banner_proportions(self) -> None:
        """Verify banners are constrained to slim 36px ribbons to preserve screen ratio."""
        widget = ScheduleScreenWidget(sessions=self.sessions, engine=self.engine)
        self.assertEqual(widget.debrief_banner.maximumHeight(), 36)
        self.assertEqual(widget.priority_task_card.maximumHeight(), 36)
        self.assertEqual(widget.special_period_banner.maximumHeight(), 36)


if __name__ == "__main__":
    unittest.main()

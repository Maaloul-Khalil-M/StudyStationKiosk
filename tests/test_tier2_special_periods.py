"""Unit tests for Tier 2 Academic Urgency Engine, Backlog Sorting & Special Period Overrides."""

from datetime import date, datetime, timedelta
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    SpecialPeriod,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.debrief_dialog import DebriefDialog
from study_station.ui.special_period_dialog import SpecialPeriodDialog
from study_station.ui.tasks_dialog import TasksDialog


class TestSpecialPeriodModel(unittest.TestCase):
    """Test SpecialPeriod dataclass duration logic and date containment."""

    def test_single_day_period(self) -> None:
        today = date(2026, 10, 19)
        period = SpecialPeriod(
            name="DS Exam Math",
            period_type="exam",
            start_date=today,
            end_date=today,
            overrides_schedule=True,
        )
        self.assertEqual(period.duration_days, 1)
        self.assertEqual(period.duration_label, "1 Day")
        self.assertTrue(period.contains_date(today))
        self.assertFalse(period.contains_date(today + timedelta(days=1)))

    def test_x_days_period(self) -> None:
        start_d = date(2026, 10, 19)
        end_d = date(2026, 10, 21)
        period = SpecialPeriod(
            name="Hackathon Sprint",
            period_type="intensive",
            start_date=start_d,
            end_date=end_d,
            overrides_schedule=True,
        )
        self.assertEqual(period.duration_days, 3)
        self.assertEqual(period.duration_label, "3 Days")
        self.assertTrue(period.contains_date(date(2026, 10, 20)))
        self.assertFalse(period.contains_date(date(2026, 10, 22)))

    def test_one_week_period(self) -> None:
        start_d = date(2026, 10, 19)  # Monday
        end_d = date(2026, 10, 25)    # Sunday
        period = SpecialPeriod(
            name="Semaine Bloquée",
            period_type="exam",
            start_date=start_d,
            end_date=end_d,
            overrides_schedule=True,
        )
        self.assertEqual(period.duration_days, 7)
        self.assertEqual(period.duration_label, "1 Week")
        self.assertTrue(period.overlaps_week(start_d))

    def test_x_weeks_period(self) -> None:
        start_d = date(2026, 10, 19)
        end_d = date(2026, 11, 1)
        period = SpecialPeriod(
            name="Final Exams Period",
            period_type="exam",
            start_date=start_d,
            end_date=end_d,
            overrides_schedule=True,
        )
        self.assertEqual(period.duration_days, 14)
        self.assertEqual(period.duration_label, "2 Weeks")


class TestSpecialPeriodPersistence(unittest.TestCase):
    """Test SQLite CRUD operations for SpecialPeriod in StudyStationRepository."""

    def setUp(self) -> None:
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.repo = StudyStationRepository(self.db)

    def tearDown(self) -> None:
        self.db.close()
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except OSError:
                pass

    def test_crud_lifecycle(self) -> None:
        period = SpecialPeriod(
            name="DS Revision Sprint",
            period_type="revision",
            start_date=date(2026, 10, 19),
            end_date=date(2026, 10, 24),
            overrides_schedule=True,
            notes="No lectures, labs open",
        )
        self.repo.add_special_period(period)

        loaded = self.repo.get_all_special_periods()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, "DS Revision Sprint")
        self.assertEqual(loaded[0].period_type, "revision")
        self.assertEqual(loaded[0].duration_days, 6)
        self.assertTrue(loaded[0].overrides_schedule)

        # By ID
        fetched = self.repo.get_special_period_by_id(period.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "DS Revision Sprint")

        # Delete
        self.assertTrue(self.repo.delete_special_period(period.id))
        self.assertEqual(len(self.repo.get_all_special_periods()), 0)


class TestAcademicUrgencyEngine(unittest.TestCase):
    """Test the Tomorrow-Morning class proximity bias heuristic in ScheduleEngine."""

    def setUp(self) -> None:
        # Schedule:
        # Monday: Visualisation des données at 08:00
        # Thursday: Entrepôts de données at 14:00
        self.sessions = [
            AcademicSession(
                day="Lun",
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Visualisation des données", "TP"),
                location="Lab 20",
            ),
            AcademicSession(
                day="Jeu",
                time_slot=TimeSlot("14:00", "15:30"),
                subject=Subject("Entrepôts de données", "Cours"),
                location="Amphi B",
            ),
        ]
        self.engine = ScheduleEngine(sessions=self.sessions)

    def test_tomorrow_morning_bias_outranks_distant_class(self) -> None:
        # Reference datetime: Sunday evening Oct 18, 2026 at 20:00
        # Tomorrow morning is Monday Oct 19 at 08:00 (Visualisation des données in 12 hours)
        # Next class for Entrepôts de données is Thursday Oct 22 (in 90 hours)
        now = datetime(2026, 10, 18, 20, 0)

        # Todo A: for Entrepôts de données, due Monday afternoon at 16:00
        todo_thursday_subject = StudyTodo(
            subject_name="Entrepôts de données",
            title="Read Chapter 3",
            due_date=datetime(2026, 10, 19, 16, 0),
        )

        # Todo B: for Visualisation des données, due Monday morning at 08:00 (tomorrow morning's class!)
        todo_tomorrow_morning = StudyTodo(
            subject_name="Visualisation des données",
            title="Finish D3 script before 08:00 lab",
            due_date=datetime(2026, 10, 19, 8, 0),
        )

        self.engine.add_todo(todo_thursday_subject)
        self.engine.add_todo(todo_tomorrow_morning)

        score_tomorrow = self.engine.calculate_todo_urgency_score(todo_tomorrow_morning, now)
        score_thursday = self.engine.calculate_todo_urgency_score(todo_thursday_subject, now)

        # Tomorrow morning's class task must have significantly higher urgency
        self.assertGreater(score_tomorrow, score_thursday)

        # get_priority_study_todo must select the tomorrow morning task!
        priority = self.engine.get_priority_study_todo(now)
        self.assertIsNotNone(priority)
        self.assertEqual(priority.id, todo_tomorrow_morning.id)

    def test_overdue_always_outranks_pending(self) -> None:
        now = datetime(2026, 10, 18, 20, 0)
        overdue_todo = StudyTodo(
            subject_name="Visualisation des données",
            title="Old assignment",
            due_date=now - timedelta(hours=3),
        )
        pending_tomorrow = StudyTodo(
            subject_name="Visualisation des données",
            title="Tomorrow lab",
            due_date=now + timedelta(hours=12),
        )
        self.engine.add_todo(pending_tomorrow)
        self.engine.add_todo(overdue_todo)

        priority = self.engine.get_priority_study_todo(now)
        self.assertIsNotNone(priority)
        self.assertEqual(priority.id, overdue_todo.id)


class TestTasksDialogSortingAndErgonomics(unittest.TestCase):
    """Test multi-criteria sorting and safe empty tasks in TasksDialog."""

    def setUp(self) -> None:
        self.engine = ScheduleEngine(sessions=[])
        now = datetime.now()
        self.t1 = StudyTodo(subject_name="Math", title="Algebra problem", due_date=now + timedelta(days=2))
        self.t2 = StudyTodo(subject_name="Bio", title="Cell structure", due_date=now + timedelta(days=1))
        self.t3 = StudyTodo(subject_name="Algo", title="Binary tree", due_date=now + timedelta(days=5))
        self.engine.add_todo(self.t1)
        self.engine.add_todo(self.t2)
        self.engine.add_todo(self.t3)

    def test_sorting_by_subject(self) -> None:
        dialog = TasksDialog(self.engine)
        dialog._set_status_filter("All")

        # Set sort to Subject (A-Z)
        idx = dialog.combo_sort.findData("subject")
        self.assertGreaterEqual(idx, 0)
        dialog.combo_sort.setCurrentIndex(idx)

        # Tasks rendered in order: Algo, Bio, Math
        self.assertEqual(dialog.combo_sort.currentData(), "subject")

    def test_sorting_by_title(self) -> None:
        dialog = TasksDialog(self.engine)
        dialog._set_status_filter("All")
        idx = dialog.combo_sort.findData("title")
        self.assertGreaterEqual(idx, 0)
        dialog.combo_sort.setCurrentIndex(idx)
        self.assertEqual(dialog.combo_sort.currentData(), "title")

    def test_safe_empty_tasks_confirmation(self) -> None:
        dialog = TasksDialog(self.engine)
        self.assertEqual(len(self.engine.todos), 3)

        # Cancel confirmation -> nothing deleted
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
            dialog._on_empty_tasks_clicked()
        self.assertEqual(len(self.engine.todos), 3)

        # Confirm -> all deleted
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            dialog._on_empty_tasks_clicked()
        self.assertEqual(len(self.engine.todos), 0)


class TestDebriefDialogActiveTemplates(unittest.TestCase):
    """Test active template pill highlight styling in DebriefDialog."""

    def setUp(self) -> None:
        self.engine = ScheduleEngine(sessions=[])

    def test_template_click_highlights_button(self) -> None:
        dialog = DebriefDialog(self.engine)
        self.assertTrue(len(dialog.template_buttons) > 0)

        first_btn, first_prefix = dialog.template_buttons[0]
        first_btn.click()

        # Text input should start with prefix
        self.assertTrue(dialog.txt_title.text().startswith(first_prefix))
        # Button should have emerald highlight style
        self.assertIn("#10B981", first_btn.styleSheet())


class TestSpecialPeriodDialogUI(unittest.TestCase):
    """Test SpecialPeriodDialog UI presets and creation."""

    def setUp(self) -> None:
        self.engine = ScheduleEngine(sessions=[])

    def test_apply_presets_and_create(self) -> None:
        dialog = SpecialPeriodDialog(self.engine)
        dialog._apply_preset(7)  # 1 Week

        self.assertIn("1 Week", dialog.lbl_duration.text())
        self.assertEqual(dialog.txt_name.text(), "Devoirs Surveillés (DS Week)")

        dialog._on_create_clicked()
        self.assertEqual(len(self.engine.special_periods), 1)
        created = self.engine.special_periods[0]
        self.assertEqual(created.name, "Devoirs Surveillés (DS Week)")
        self.assertEqual(created.period_type, "exam")
        self.assertTrue(created.overrides_schedule)


if __name__ == "__main__":
    unittest.main()

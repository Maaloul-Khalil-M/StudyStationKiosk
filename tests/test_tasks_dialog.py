"""Unit tests for TasksDialog and EditTodoDialog (Milestone 15)."""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession, StudyTodo, Subject, TimeSlot
from study_station.ui.edit_todo_dialog import EditTodoDialog
from study_station.ui.subject_preparation_sheet import SubjectPreparationSheet
from study_station.ui.tasks_dialog import TasksDialog


class TestEditTodoDialog(unittest.TestCase):
    """Test the EditTodoDialog in both create and edit modes."""

    def setUp(self) -> None:
        sessions = [
            AcademicSession(
                day="Lun",
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Data Vis", "TP"),
                location="Lab 20",
            ),
            AcademicSession(
                day="Jeu",
                time_slot=TimeSlot("09:40", "11:10"),
                subject=Subject("Entrepôts de données", "Cours"),
                location="SC 3",
            ),
        ]
        self.engine = ScheduleEngine(sessions=sessions)

    def test_create_mode_defaults(self) -> None:
        dialog = EditTodoDialog(
            engine=self.engine,
            todo=None,
            default_subject="Entrepôts de données",
        )
        self.assertTrue(dialog.is_create_mode)
        self.assertEqual(dialog.combo_subject.currentText(), "Entrepôts de données")
        self.assertEqual(dialog.txt_title.text(), "")
        self.assertEqual(dialog.combo_status.currentText(), "Pending")
        self.assertFalse(hasattr(dialog, "btn_delete"))

    def test_create_mode_save(self) -> None:
        dialog = EditTodoDialog(
            engine=self.engine,
            todo=None,
            default_subject="Data Vis",
        )
        dialog.txt_title.setText("Implement D3 scatter plot")
        dialog.txt_notes.setText("Check chapter 4")
        dialog.date_picker.setDate(QDate.currentDate().addDays(2))

        saved_todos: list[StudyTodo] = []
        dialog.todo_saved.connect(saved_todos.append)

        dialog._on_save()

        self.assertEqual(len(saved_todos), 1)
        created = saved_todos[0]
        self.assertEqual(created.title, "Implement D3 scatter plot")
        self.assertEqual(created.subject_name, "Data Vis")
        self.assertEqual(created.notes, "Check chapter 4")
        self.assertFalse(created.is_completed)

        # Check engine has it
        self.assertIn(created, self.engine.todos)

    def test_edit_mode_population_and_update(self) -> None:
        due = datetime.now() + timedelta(days=3)
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Star Schema Lab 2",
            notes="Slide 12",
            due_date=due,
            status="pending",
        )
        self.engine.add_todo(todo)

        dialog = EditTodoDialog(
            engine=self.engine,
            todo=todo,
        )
        self.assertFalse(dialog.is_create_mode)
        self.assertEqual(dialog.txt_title.text(), "Star Schema Lab 2")
        self.assertEqual(dialog.txt_notes.text(), "Slide 12")
        self.assertTrue(hasattr(dialog, "btn_delete"))

        # Modify fields
        dialog.txt_title.setText("Updated: Star Schema Lab 2 and ETL")
        dialog.txt_notes.setText("Slide 12 and 14")
        dialog.combo_status.setCurrentText("Completed")
        dialog.txt_question.setText("Why use surrogate keys?")

        saved_todos: list[StudyTodo] = []
        dialog.todo_saved.connect(saved_todos.append)

        dialog._on_save()

        self.assertEqual(len(saved_todos), 1)
        self.assertEqual(todo.title, "Updated: Star Schema Lab 2 and ETL")
        self.assertEqual(todo.notes, "Slide 12 and 14")
        self.assertTrue(todo.is_completed)
        self.assertEqual(todo.next_class_question, "Why use surrogate keys?")

    def test_delete_action_with_confirmation(self) -> None:
        todo = StudyTodo(
            subject_name="Data Vis",
            title="Temporary task to delete",
            due_date=datetime.now() + timedelta(days=1),
        )
        self.engine.add_todo(todo)

        dialog = EditTodoDialog(
            engine=self.engine,
            todo=todo,
        )

        deleted_ids: list[str] = []
        dialog.todo_deleted.connect(deleted_ids.append)

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            dialog._on_delete()

        self.assertEqual(len(deleted_ids), 1)
        self.assertEqual(deleted_ids[0], todo.id)
        self.assertNotIn(todo, self.engine.todos)


class TestTasksDialog(unittest.TestCase):
    """Test the centralized academic task backlog modal."""

    def setUp(self) -> None:
        sessions = [
            AcademicSession(
                day="Lun",
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Data Vis", "TP"),
                location="Lab 20",
            ),
            AcademicSession(
                day="Jeu",
                time_slot=TimeSlot("09:40", "11:10"),
                subject=Subject("Entrepôts de données", "Cours"),
                location="SC 3",
            ),
        ]
        self.engine = ScheduleEngine(sessions=sessions)

        now = datetime.now()
        # Seed tasks
        # 1. Overdue
        self.t_overdue = StudyTodo(
            subject_name="Data Vis",
            title="Overdue report",
            due_date=now - timedelta(days=2),
            status="pending",
        )
        # 2. Due soon (< 24h)
        self.t_due_soon = StudyTodo(
            subject_name="Data Vis",
            title="Lab prep tomorrow",
            due_date=now + timedelta(hours=12),
            status="pending",
        )
        # 3. Future pending (3 days)
        self.t_future = StudyTodo(
            subject_name="Entrepôts de données",
            title="ETL pipeline design",
            notes="Read documentation",
            due_date=now + timedelta(days=3),
            status="pending",
        )
        # 4. Completed
        self.t_done = StudyTodo(
            subject_name="Entrepôts de données",
            title="Slides review 1",
            due_date=now - timedelta(days=1),
            status="completed",
        )
        self.engine.add_todo(self.t_overdue)
        self.engine.add_todo(self.t_due_soon)
        self.engine.add_todo(self.t_future)
        self.engine.add_todo(self.t_done)

    def test_kpi_cards(self) -> None:
        dialog = TasksDialog(self.engine)
        # Pending: 3 (t_overdue, t_due_soon, t_future)
        self.assertEqual(dialog.kpi_pending.value_label.text(), "3")  # type: ignore
        # Due this week: 2 (t_due_soon, t_future are in next 7 days)
        self.assertEqual(dialog.kpi_due_week.value_label.text(), "2")  # type: ignore
        # Overdue: 1 (t_overdue)
        self.assertEqual(dialog.kpi_overdue.value_label.text(), "1")  # type: ignore
        # Completed: 1 (t_done)
        self.assertEqual(dialog.kpi_completed.value_label.text(), "1")  # type: ignore

    def test_subject_filter(self) -> None:
        dialog = TasksDialog(self.engine)
        # By default Pending filter is active -> 3 tasks
        dialog._set_status_filter("All")

        dialog._on_subject_filter_changed("Data Vis")
        self.assertEqual(dialog._current_subject_filter, "Data Vis")

        # Check rendered rows: 2 for Data Vis (t_overdue, t_due_soon)
        rendered_count = sum(1 for i in range(dialog.tasks_layout.count()) if dialog.tasks_layout.itemAt(i).widget() and not dialog.tasks_layout.itemAt(i).widget().inherits("QLabel"))
        self.assertEqual(rendered_count, 2)

    def test_status_filter(self) -> None:
        dialog = TasksDialog(self.engine)

        dialog._set_status_filter("Completed")
        rendered_count = sum(1 for i in range(dialog.tasks_layout.count()) if dialog.tasks_layout.itemAt(i).widget() and not dialog.tasks_layout.itemAt(i).widget().inherits("QLabel"))
        self.assertEqual(rendered_count, 1)

        dialog._set_status_filter("Overdue")
        rendered_count = sum(1 for i in range(dialog.tasks_layout.count()) if dialog.tasks_layout.itemAt(i).widget() and not dialog.tasks_layout.itemAt(i).widget().inherits("QLabel"))
        self.assertEqual(rendered_count, 1)

    def test_search_filter(self) -> None:
        dialog = TasksDialog(self.engine)
        dialog._set_status_filter("All")

        dialog._on_search_changed("pipeline")
        rendered_count = sum(1 for i in range(dialog.tasks_layout.count()) if dialog.tasks_layout.itemAt(i).widget() and not dialog.tasks_layout.itemAt(i).widget().inherits("QLabel"))
        self.assertEqual(rendered_count, 1)

    def test_toggle_completed_reversible(self) -> None:
        dialog = TasksDialog(self.engine)

        # Mark t_future completed
        dialog._on_toggle_completed(self.t_future, True)
        self.assertTrue(self.t_future.is_completed)
        self.assertEqual(dialog.kpi_pending.value_label.text(), "2")  # type: ignore
        self.assertEqual(dialog.kpi_completed.value_label.text(), "2")  # type: ignore

        # Reopen t_future back to pending
        dialog._on_toggle_completed(self.t_future, False)
        self.assertFalse(self.t_future.is_completed)
        self.assertIsNone(self.t_future.completed_at)
        self.assertEqual(dialog.kpi_pending.value_label.text(), "3")  # type: ignore
        self.assertEqual(dialog.kpi_completed.value_label.text(), "1")  # type: ignore

    def test_focus_task_signal(self) -> None:
        dialog = TasksDialog(self.engine)
        focus_events: list[tuple[StudyTodo, int]] = []
        dialog.start_task_focus_requested.connect(lambda t, m: focus_events.append((t, m)))

        dialog._on_focus_task(self.t_due_soon)
        self.assertEqual(len(focus_events), 1)
        self.assertEqual(focus_events[0][0].id, self.t_due_soon.id)
        self.assertEqual(focus_events[0][1], 15)

    def test_delete_task_with_confirmation(self) -> None:
        dialog = TasksDialog(self.engine)
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            dialog._on_delete_task(self.t_overdue)

        self.assertNotIn(self.t_overdue, self.engine.todos)
        self.assertEqual(dialog.kpi_pending.value_label.text(), "2")  # type: ignore


class TestSubjectPreparationSheetCRUD(unittest.TestCase):
    """Test inline CRUD and reversible toggle in SubjectPreparationSheet."""

    def setUp(self) -> None:
        self.session = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Data Vis", "TP"),
            location="Lab 20",
        )
        self.engine = ScheduleEngine(sessions=[self.session])

        self.todo1 = StudyTodo(
            subject_name="Data Vis",
            title="Lab 1 script",
            due_date=datetime.now() + timedelta(days=2),
            status="pending",
        )
        self.engine.add_todo(self.todo1)

    def test_sheet_toggle_and_edit_delete(self) -> None:
        sheet = SubjectPreparationSheet(self.session, self.engine)

        changed_events: list[bool] = []
        sheet.todo_changed.connect(lambda: changed_events.append(True))

        # Test toggle completed
        sheet._on_toggle_completed(self.todo1, True)
        self.assertTrue(self.todo1.is_completed)
        self.assertEqual(len(changed_events), 1)

        # Test toggle uncompleted
        sheet._on_toggle_completed(self.todo1, False)
        self.assertFalse(self.todo1.is_completed)
        self.assertEqual(len(changed_events), 2)

        # Test delete
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            sheet._on_delete_task(self.todo1)

        self.assertNotIn(self.todo1, self.engine.todos)
        self.assertEqual(len(changed_events), 3)


if __name__ == "__main__":
    unittest.main()

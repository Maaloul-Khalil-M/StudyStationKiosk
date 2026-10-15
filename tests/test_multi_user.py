from datetime import datetime
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QMessageBox

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession, StudyTodo, Subject, TimeSlot
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.persistence.user_manager import UserManager
from study_station.ui.main_window import MainWindow
from study_station.ui.tasks_dialog import TasksDialog
from study_station.ui.user_switch_dialog import UserSwitchDialog


class TestUserManager(unittest.TestCase):
    """Test user profile and database path management."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.manager = UserManager(base_dir=self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_user_initialization(self) -> None:
        users = self.manager.list_users()
        self.assertIn("Default", users)
        self.assertEqual(self.manager.get_active_user(), "Default")

    def test_create_new_user(self) -> None:
        name, db_path = self.manager.create_user("Alice")
        self.assertEqual(name, "Alice")
        self.assertTrue(str(db_path).endswith("Alice.db"))
        self.assertIn("Alice", self.manager.list_users())

    def test_sanitize_username(self) -> None:
        name, _ = self.manager.create_user("Bob / Special:User?")
        self.assertEqual(name, "Bob  SpecialUser")

    def test_set_active_user(self) -> None:
        self.manager.create_user("Charlie")
        self.assertTrue(self.manager.set_active_user("Charlie"))
        self.assertEqual(self.manager.get_active_user(), "Charlie")
        self.assertFalse(self.manager.set_active_user("NonExistent"))

    def test_database_isolation_paths(self) -> None:
        _, db1 = self.manager.create_user("User1")
        _, db2 = self.manager.create_user("User2")
        self.assertNotEqual(db1, db2)
        self.assertTrue(db1.parent.name == "users")

    def test_delete_user(self) -> None:
        self.manager.create_user("TempUser")
        db_path = self.manager.get_user_db_path("TempUser")
        db_path.touch()
        self.assertTrue(db_path.exists())

        self.assertTrue(self.manager.delete_user("TempUser", delete_db_file=True))
        self.assertNotIn("TempUser", self.manager.list_users())
        self.assertFalse(db_path.exists())

    def test_cannot_delete_only_user(self) -> None:
        # Only "Default" exists initially
        self.assertFalse(self.manager.delete_user("Default"))


class TestMultiUserDatabaseIsolation(unittest.TestCase):
    """Test that two users have completely separate databases."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.manager = UserManager(base_dir=self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_separate_todos_and_sessions(self) -> None:
        # Create User 1
        _, db_path_1 = self.manager.create_user("StudentOne")
        db1 = Database(db_path_1)
        repo1 = StudyStationRepository(db1)
        engine1 = ScheduleEngine.from_repository(repo1)

        # Create User 2
        _, db_path_2 = self.manager.create_user("StudentTwo")
        db2 = Database(db_path_2)
        repo2 = StudyStationRepository(db2)
        engine2 = ScheduleEngine.from_repository(repo2)

        # Add a task only to User 1
        todo1 = StudyTodo(
            subject_name="Security",
            title="User 1 Task",
            due_date=datetime(2026, 10, 20, 10, 0),
        )
        engine1.add_todo(todo1)

        # Add a task only to User 2
        todo2 = StudyTodo(
            subject_name="Databases",
            title="User 2 Task",
            due_date=datetime(2026, 10, 21, 10, 0),
        )
        engine2.add_todo(todo2)

        # Verify DB1 has User 1 Task but NOT User 2 Task
        todos_1 = engine1.get_todos()
        titles_1 = [t.title for t in todos_1]
        self.assertIn("User 1 Task", titles_1)
        self.assertNotIn("User 2 Task", titles_1)

        # Verify DB2 has User 2 Task but NOT User 1 Task
        todos_2 = engine2.get_todos()
        titles_2 = [t.title for t in todos_2]
        self.assertIn("User 2 Task", titles_2)
        self.assertNotIn("User 1 Task", titles_2)

        db1.close()
        db2.close()


class TestUserSwitchUI(unittest.TestCase):
    """Test UserSwitchDialog and MainWindow switching integration."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.manager = UserManager(base_dir=self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dialog_user_cards_and_creation(self) -> None:
        self.manager.create_user("Alice")
        dialog = UserSwitchDialog(self.manager)

        # Should have Default and Alice
        self.assertGreaterEqual(dialog.cards_layout.count(), 2)

        # Test creating new user from dialog
        dialog.txt_username.setText("Bob")
        dialog._on_create_user_clicked()
        self.assertEqual(dialog.selected_user, "Bob")
        self.assertEqual(self.manager.get_active_user(), "Bob")
        dialog.close()

    def test_main_window_user_switch(self) -> None:
        _, db1 = self.manager.create_user("UserAlpha")
        _, db2 = self.manager.create_user("UserBeta")
        self.manager.set_active_user("UserAlpha")

        db = Database(db1)
        repo = StudyStationRepository(db)
        engine = ScheduleEngine.from_repository(repo)

        window = MainWindow(engine=engine, repository=repo, user_manager=self.manager)

        # Check button label
        self.assertIn("UserAlpha", window._schedule_widget.btn_user.text())

        # Switch user to UserBeta
        window.switch_user("UserBeta")
        self.assertEqual(window._current_user, "UserBeta")
        self.assertIn("UserBeta", window._schedule_widget.btn_user.text())
        self.assertIn("UserBeta", window._dashboard_widget.btn_user.text())

        window.close()

    def test_dialog_creation_with_empty_and_sample_options(self) -> None:
        dialog = UserSwitchDialog(self.manager)
        self.assertTrue(dialog.rad_empty.isChecked())
        self.assertFalse(dialog.rad_sample.isChecked())

        emitted_signals = []
        dialog.user_switched.connect(lambda name, sample: emitted_signals.append((name, sample)))

        # 1. Create with empty option (default)
        dialog.txt_username.setText("CleanUser")
        dialog._on_create_user_clicked()
        self.assertEqual(len(emitted_signals), 1)
        self.assertEqual(emitted_signals[0], ("CleanUser", False))

        # 2. Create another user with sample template option
        dialog2 = UserSwitchDialog(self.manager)
        dialog2.rad_sample.setChecked(True)
        dialog2.user_switched.connect(lambda name, sample: emitted_signals.append((name, sample)))
        dialog2.txt_username.setText("SampleUser")
        dialog2._on_create_user_clicked()
        self.assertEqual(len(emitted_signals), 2)
        self.assertEqual(emitted_signals[1], ("SampleUser", True))

        dialog.close()
        dialog2.close()

    def test_new_user_starts_with_empty_schedule_and_todos(self) -> None:
        _, db1 = self.manager.create_user("UserAlpha")
        self.manager.set_active_user("UserAlpha")
        db = Database(db1)
        repo = StudyStationRepository(db)
        engine = ScheduleEngine.from_repository(repo)
        window = MainWindow(engine=engine, repository=repo, user_manager=self.manager)

        # Create new user Bob with load_sample=False (the default empty slate)
        _, db_bob = self.manager.create_user("Bob")
        window.switch_user("Bob", load_sample=False)

        # Verify completely empty schedule and empty todos
        self.assertEqual(len(window._engine.sessions), 0)
        self.assertEqual(len(window._engine.todos), 0)
        self.assertIn("Schedule is empty", window._schedule_widget.lbl_sub.text())

        window.close()

    def test_new_user_can_load_sample_template(self) -> None:
        _, db1 = self.manager.create_user("UserAlpha")
        self.manager.set_active_user("UserAlpha")
        db = Database(db1)
        repo = StudyStationRepository(db)
        engine = ScheduleEngine.from_repository(repo)
        window = MainWindow(engine=engine, repository=repo, user_manager=self.manager)

        # Switch to Charlie with load_sample=True
        _, db_charlie = self.manager.create_user("Charlie")
        window.switch_user("Charlie", load_sample=True)

        # Verify sample sessions exist
        self.assertGreater(len(window._engine.sessions), 0)

        window.close()

    def test_empty_schedule_button(self) -> None:
        _, db1 = self.manager.create_user("UserWithClasses")
        self.manager.set_active_user("UserWithClasses")
        db = Database(db1)
        repo = StudyStationRepository(db)
        sample_path = Path(__file__).resolve().parent.parent / "docs" / "example.json"
        if sample_path.exists():
            repo.seed_timetable_if_empty(sample_path)
        engine = ScheduleEngine.from_repository(repo)
        window = MainWindow(engine=engine, repository=repo, user_manager=self.manager)

        self.assertGreater(len(window._schedule_widget._sessions), 0)

        # Simulate clicking "Empty Schedule" with QMessageBox.Yes
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            window._schedule_widget._on_clear_schedule()

        self.assertEqual(len(window._schedule_widget._sessions), 0)
        self.assertEqual(len(window._engine.sessions), 0)
        self.assertIn("Schedule is empty", window._schedule_widget.lbl_sub.text())

        window.close()

    def test_empty_tasks_button(self) -> None:
        _, db1 = self.manager.create_user("UserWithTasks")
        self.manager.set_active_user("UserWithTasks")
        db = Database(db1)
        repo = StudyStationRepository(db)
        engine = ScheduleEngine.from_repository(repo)
        engine.add_todo(StudyTodo(subject_name="Math", title="Homework 1"))
        engine.add_todo(StudyTodo(subject_name="Physics", title="Lab Report"))

        self.assertEqual(len(engine.todos), 2)

        tasks_dlg = TasksDialog(engine)
        self.assertTrue(tasks_dlg.btn_empty_tasks.isEnabled())

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            tasks_dlg._on_empty_tasks_clicked()

        self.assertEqual(len(engine.todos), 0)
        self.assertFalse(tasks_dlg.btn_empty_tasks.isEnabled())
        tasks_dlg.close()

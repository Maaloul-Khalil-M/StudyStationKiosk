"""Unit tests for Academic Todo Engine & Schema (Milestone 10)."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    StudyLog,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository


class TestStudyTodoModel(unittest.TestCase):
    """Test StudyTodo dataclass behaviors and convenience properties."""

    def test_default_initialization(self) -> None:
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Fix ETL connection script",
        )
        self.assertTrue(todo.id)
        self.assertEqual(todo.subject_name, "Entrepôts de données")
        self.assertEqual(todo.title, "Fix ETL connection script")
        self.assertEqual(todo.notes, "")
        self.assertEqual(todo.status, "pending")
        self.assertFalse(todo.is_completed)
        self.assertIsNone(todo.completed_at)
        self.assertIsNone(todo.confidence)
        self.assertIsNone(todo.next_class_question)

    def test_is_overdue(self) -> None:
        now = datetime(2026, 10, 15, 20, 0)
        past_due = now - timedelta(hours=2)
        future_due = now + timedelta(days=2)

        overdue_todo = StudyTodo(
            subject_name="Bases de données NoSQL",
            title="Index review",
            due_date=past_due,
        )
        self.assertTrue(overdue_todo.is_overdue(ref_dt=now))

        future_todo = StudyTodo(
            subject_name="Bases de données NoSQL",
            title="Sharding review",
            due_date=future_due,
        )
        self.assertFalse(future_todo.is_overdue(ref_dt=now))

        # Completed tasks should not be considered overdue even if past due_date
        overdue_todo.status = "completed"
        self.assertFalse(overdue_todo.is_overdue(ref_dt=now))

    def test_is_due_soon(self) -> None:
        now = datetime(2026, 10, 15, 20, 0)
        in_12_hours = now + timedelta(hours=12)
        in_3_days = now + timedelta(days=3)

        soon_todo = StudyTodo(
            subject_name="tests logiciels",
            title="ISTQB equivalence partitioning",
            due_date=in_12_hours,
        )
        self.assertTrue(soon_todo.is_due_soon(hours=24, ref_dt=now))

        distant_todo = StudyTodo(
            subject_name="tests logiciels",
            title="Boundary value analysis",
            due_date=in_3_days,
        )
        self.assertFalse(distant_todo.is_due_soon(hours=24, ref_dt=now))


class TestTodoPersistence(unittest.TestCase):
    """Test SQLite schema migration and StudyStationRepository CRUD operations."""

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

    def test_schema_has_study_todos_and_columns(self) -> None:
        cursor = self.db.connection.execute("PRAGMA table_info(study_todos);")
        col_names = [row["name"] for row in cursor.fetchall()]
        expected = [
            "id", "subject_name", "title", "notes", "created_at", "due_date",
            "status", "completed_at", "confidence", "next_class_question", "session_ref_id"
        ]
        for col in expected:
            self.assertIn(col, col_names)

        # Check study_logs migration for todo_id
        cursor = self.db.connection.execute("PRAGMA table_info(study_logs);")
        log_cols = [row["name"] for row in cursor.fetchall()]
        self.assertIn("todo_id", log_cols)

    def test_crud_todo_workflow(self) -> None:
        due = datetime(2026, 10, 22, 9, 40)
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Fix Star Schema join in Lab 2 script",
            notes="Look at slide 18",
            due_date=due,
        )
        self.repo.add_todo(todo)

        # Retrieve by ID
        fetched = self.repo.get_todo_by_id(todo.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Fix Star Schema join in Lab 2 script")
        self.assertEqual(fetched.subject_name, "Entrepôts de données")
        self.assertEqual(fetched.status, "pending")

        # Update todo
        todo.notes = "Updated notes: check surrogate keys"
        self.assertTrue(self.repo.update_todo(todo))
        updated = self.repo.get_todo_by_id(todo.id)
        self.assertEqual(updated.notes, "Updated notes: check surrogate keys")

        # Mark completed with confidence and next-class question
        completed_at = datetime(2026, 10, 16, 21, 30)
        self.assertTrue(
            self.repo.mark_todo_completed(
                todo_id=todo.id,
                confidence="getting_there",
                next_class_question="Why must dimension tables have synthetic keys?",
                completed_at=completed_at,
            )
        )
        completed_todo = self.repo.get_todo_by_id(todo.id)
        self.assertEqual(completed_todo.status, "completed")
        self.assertEqual(completed_todo.confidence, "getting_there")
        self.assertEqual(
            completed_todo.next_class_question,
            "Why must dimension tables have synthetic keys?",
        )
        self.assertEqual(completed_todo.completed_at, completed_at)

        # Reopen todo
        self.assertTrue(self.repo.mark_todo_pending(todo.id))
        reopened = self.repo.get_todo_by_id(todo.id)
        self.assertEqual(reopened.status, "pending")
        self.assertIsNone(reopened.completed_at)

        # Questions retrieval
        questions = self.repo.get_questions_by_subject("Entrepôts de données")
        self.assertEqual(len(questions), 1)
        self.assertIn("Why must dimension tables have synthetic keys?", questions[0])

        # Delete todo
        self.assertTrue(self.repo.delete_todo(todo.id))
        self.assertIsNone(self.repo.get_todo_by_id(todo.id))

    def test_filtering_todos(self) -> None:
        t1 = StudyTodo(
            subject_name="Math",
            title="Linear algebra exercise 1",
            due_date=datetime(2026, 10, 16, 10, 0),
            status="pending",
        )
        t2 = StudyTodo(
            subject_name="Math",
            title="Linear algebra exercise 2",
            due_date=datetime(2026, 10, 17, 10, 0),
            status="completed",
        )
        t3 = StudyTodo(
            subject_name="Physics",
            title="Optics lab prep",
            due_date=datetime(2026, 10, 18, 10, 0),
            status="pending",
        )
        self.repo.add_todo(t1)
        self.repo.add_todo(t2)
        self.repo.add_todo(t3)

        # All pending
        pending = self.repo.get_pending_todos()
        self.assertEqual(len(pending), 2)

        # Math pending only
        math_pending = self.repo.get_pending_todos("Math")
        self.assertEqual(len(math_pending), 1)
        self.assertEqual(math_pending[0].title, "Linear algebra exercise 1")

        # All math
        all_math = self.repo.get_todos_by_subject("Math")
        self.assertEqual(len(all_math), 2)

    def test_study_log_with_todo_id(self) -> None:
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Lab 2 fix",
            due_date=datetime(2026, 10, 20, 10, 0),
        )
        self.repo.add_todo(todo)

        log = StudyLog(
            subject_name="Entrepôts de données",
            duration_minutes=25,
            source="timer",
            todo_id=todo.id,
        )
        self.repo.add_study_log(log)

        all_logs = self.repo.get_all_study_logs()
        self.assertEqual(len(all_logs), 1)
        self.assertEqual(all_logs[0].todo_id, todo.id)


class TestScheduleEngineTodoIntegration(unittest.TestCase):
    """Test ScheduleEngine's todo methods, queries, and SubjectSummary integration."""

    def setUp(self) -> None:
        sessions = [
            AcademicSession(
                day="Lun",
                time_slot=TimeSlot("08:00", "09:30"),
                subject=Subject("Visualisation des données", "TP"),
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

    def test_engine_todo_lifecycle(self) -> None:
        due = datetime(2026, 10, 22, 9, 40)
        todo = StudyTodo(
            subject_name="Entrepôts de données",
            title="Star Schema diagram",
            due_date=due,
        )
        self.engine.add_todo(todo)

        self.assertEqual(self.engine.get_subject_pending_todos_count("Entrepôts de données"), 1)
        self.assertEqual(self.engine.get_subject_pending_todos_count("Visualisation des données"), 0)

        # Query due before
        due_before = self.engine.get_todos_due_before(datetime(2026, 10, 23, 0, 0))
        self.assertEqual(len(due_before), 1)

        # Mark completed with question
        self.engine.mark_todo_completed(
            todo_id=todo.id,
            confidence="foggy",
            next_class_question="How to partition fact table?",
        )
        self.assertEqual(self.engine.get_subject_pending_todos_count("Entrepôts de données"), 0)

        questions = self.engine.get_subject_questions("Entrepôts de données")
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0], "How to partition fact table?")

        # Reopen todo
        self.assertTrue(self.engine.mark_todo_pending(todo.id))
        self.assertEqual(self.engine.get_subject_pending_todos_count("Entrepôts de données"), 1)

    def test_next_class_deadline_calculation(self) -> None:
        # Thursday Oct 15, 2026 at 12:00 (after 09:40 class)
        ref_dt = datetime(2026, 10, 15, 12, 0)
        deadline = self.engine.get_next_class_deadline_for_subject("Entrepôts de données", ref_dt)
        self.assertIsNotNone(deadline)
        # Next Thursday is Oct 22, 2026 at 09:40
        self.assertEqual(deadline, datetime(2026, 10, 22, 9, 40))

    def test_subject_summary_includes_todos_and_questions(self) -> None:
        todo1 = StudyTodo(
            subject_name="Entrepôts de données",
            title="Lab prep",
            due_date=datetime(2026, 10, 22, 9, 40),
            status="pending",
        )
        todo2 = StudyTodo(
            subject_name="Entrepôts de données",
            title="Lecture check",
            due_date=datetime(2026, 10, 22, 9, 40),
            status="completed",
            next_class_question="Explain grain definition?",
        )
        self.engine.add_todo(todo1)
        self.engine.add_todo(todo2)

        summary = self.engine.get_subject_summary("Entrepôts de données", datetime(2026, 10, 15, 12, 0))
        self.assertEqual(summary.pending_todos_count, 1)
        self.assertEqual(summary.questions_count, 1)


if __name__ == "__main__":
    unittest.main()

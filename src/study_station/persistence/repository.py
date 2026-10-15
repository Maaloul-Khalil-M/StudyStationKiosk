"""Data repository providing domain-level persistence operations."""

from datetime import date, datetime
import json
from pathlib import Path
from typing import Sequence

from study_station.core.models import (
    AcademicSession,
    StudyLog,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.core.settings import AppSettings
from study_station.core.timer import FocusTimer
from study_station.persistence.database import Database


class StudyStationRepository:
    """Repository handling all CRUD and state recovery operations."""

    def __init__(self, database: Database) -> None:
        self.db = database

    # -------------------------------------------------------------------------
    # Study Logs
    # -------------------------------------------------------------------------

    def add_study_log(self, log: StudyLog) -> None:
        """Insert or update a study session record."""
        query = """
            INSERT INTO study_logs (id, subject_name, study_cycle_id, started_at, duration_minutes, source, todo_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                subject_name = excluded.subject_name,
                study_cycle_id = excluded.study_cycle_id,
                started_at = excluded.started_at,
                duration_minutes = excluded.duration_minutes,
                source = excluded.source,
                todo_id = excluded.todo_id;
        """
        with self.db.connection as conn:
            conn.execute(
                query,
                (
                    log.id,
                    log.subject_name,
                    log.study_cycle_id,
                    log.started_at.isoformat(),
                    log.duration_minutes,
                    log.source,
                    log.todo_id,
                ),
            )

    def get_all_study_logs(self) -> list[StudyLog]:
        """Return all study logs ordered chronologically."""
        query = "SELECT id, subject_name, study_cycle_id, started_at, duration_minutes, source, todo_id FROM study_logs ORDER BY started_at ASC"
        cursor = self.db.connection.execute(query)
        logs: list[StudyLog] = []
        for row in cursor.fetchall():
            todo_val = row["todo_id"] if "todo_id" in row.keys() else None
            logs.append(
                StudyLog(
                    id=row["id"],
                    subject_name=row["subject_name"],
                    study_cycle_id=row["study_cycle_id"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    duration_minutes=row["duration_minutes"],
                    source=row["source"],
                    todo_id=todo_val,
                )
            )
        return logs

    def delete_study_log(self, log_id: str) -> bool:
        """Delete a study log by its ID. Returns True if a record was removed."""
        with self.db.connection as conn:
            cursor = conn.execute("DELETE FROM study_logs WHERE id = ?", (log_id,))
            return cursor.rowcount > 0

    def update_study_log(
        self,
        log_id: str,
        subject_name: str,
        duration_minutes: int,
        started_at: datetime | None = None,
        todo_id: str | None = None,
    ) -> bool:
        """Update an existing study log's details. Returns True if updated."""
        query = """
            UPDATE study_logs
            SET subject_name = ?,
                duration_minutes = ?,
                started_at = COALESCE(?, started_at),
                todo_id = COALESCE(?, todo_id)
            WHERE id = ?;
        """
        with self.db.connection as conn:
            cursor = conn.execute(
                query,
                (
                    subject_name,
                    max(1, duration_minutes),
                    started_at.isoformat() if started_at else None,
                    todo_id,
                    log_id,
                ),
            )
            return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # Subject Review Targets
    # -------------------------------------------------------------------------

    def set_subject_target(self, subject_name: str, target_minutes: int) -> None:
        """Persist target review minutes for a subject."""
        query = """
            INSERT INTO subject_targets (subject_name, target_minutes)
            VALUES (?, ?)
            ON CONFLICT(subject_name) DO UPDATE SET
                target_minutes = excluded.target_minutes;
        """
        with self.db.connection as conn:
            conn.execute(query, (subject_name, max(1, target_minutes)))

    def get_all_subject_targets(self) -> dict[str, int]:
        """Return dictionary of subject_name -> target_minutes."""
        cursor = self.db.connection.execute("SELECT subject_name, target_minutes FROM subject_targets")
        return {row["subject_name"]: row["target_minutes"] for row in cursor.fetchall()}

    # -------------------------------------------------------------------------
    # Timetable Sessions
    # -------------------------------------------------------------------------

    def save_timetable_sessions(self, sessions: Sequence[AcademicSession]) -> None:
        """Replace all timetable sessions."""
        with self.db.connection as conn:
            conn.execute("DELETE FROM timetable_sessions")
            conn.executemany(
                """
                INSERT INTO timetable_sessions (day, start_time, end_time, subject_name, core, location)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        s.day,
                        s.time_slot.start,
                        s.time_slot.end,
                        s.subject.name,
                        s.subject.core,
                        s.location,
                    )
                    for s in sessions
                ],
            )

    def get_timetable_sessions(self) -> list[AcademicSession]:
        """Fetch all stored timetable sessions."""
        cursor = self.db.connection.execute(
            "SELECT day, start_time, end_time, subject_name, core, location FROM timetable_sessions ORDER BY id ASC"
        )
        sessions: list[AcademicSession] = []
        for row in cursor.fetchall():
            sessions.append(
                AcademicSession(
                    day=row["day"],
                    time_slot=TimeSlot(start=row["start_time"], end=row["end_time"]),
                    subject=Subject(name=row["subject_name"], core=row["core"]),
                    location=row["location"] or "",
                )
            )
        return sessions

    def seed_timetable_if_empty(self, json_path: str | Path) -> bool:
        """Seed timetable from JSON file if no sessions exist in the database."""
        path = Path(json_path)
        if not path.exists():
            return False

        existing = self.get_timetable_sessions()
        if existing:
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            sessions: list[AcademicSession] = []
            for s in data.get("sessions", []):
                sessions.append(
                    AcademicSession(
                        day=s["day"],
                        time_slot=TimeSlot(start=s["timeSlot"]["start"], end=s["timeSlot"]["end"]),
                        subject=Subject(name=s["subject"]["name"], core=s["subject"].get("core", "COURS")),
                        location=s.get("location", ""),
                    )
                )

            if sessions:
                self.save_timetable_sessions(sessions)
                return True
        except Exception:
            return False

        return False

    # -------------------------------------------------------------------------
    # App Settings
    # -------------------------------------------------------------------------

    def save_settings(self, settings: AppSettings) -> None:
        """Persist application settings dictionary."""
        settings_json = json.dumps(settings.to_dict())
        with self.db.connection as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value)
                VALUES ('ui_settings', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                """,
                (settings_json,),
            )

    def load_settings(self) -> AppSettings:
        """Load persisted settings or return defaults."""
        cursor = self.db.connection.execute(
            "SELECT value FROM app_settings WHERE key = 'ui_settings'"
        )
        row = cursor.fetchone()
        if not row:
            return AppSettings()

        try:
            data = json.loads(row["value"])
            return AppSettings.from_dict(data)
        except Exception:
            return AppSettings()

    # -------------------------------------------------------------------------
    # Active Timer Recovery (Laptop lid-close / crash / restart safety)
    # -------------------------------------------------------------------------

    def save_timer_state(self, timer: FocusTimer) -> None:
        """Store the running or paused timer state."""
        if not timer.is_active:
            self.clear_timer_state()
            return

        with self.db.connection as conn:
            conn.execute(
                """
                INSERT INTO active_timer_state (
                    id, is_active, subject_name, total_duration_minutes,
                    start_time, target_end_time, is_paused, paused_remaining_seconds
                ) VALUES (1, 1, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    is_active = excluded.is_active,
                    subject_name = excluded.subject_name,
                    total_duration_minutes = excluded.total_duration_minutes,
                    start_time = excluded.start_time,
                    target_end_time = excluded.target_end_time,
                    is_paused = excluded.is_paused,
                    paused_remaining_seconds = excluded.paused_remaining_seconds;
                """,
                (
                    timer.subject_name,
                    timer.total_duration_minutes,
                    timer.start_time.isoformat() if timer.start_time else datetime.now().isoformat(),
                    timer.target_end_time.isoformat() if timer.target_end_time else datetime.now().isoformat(),
                    1 if timer.is_paused else 0,
                    timer._paused_remaining_seconds,
                ),
            )

    def clear_timer_state(self) -> None:
        """Clear active timer state on completion or cancellation."""
        with self.db.connection as conn:
            conn.execute("DELETE FROM active_timer_state WHERE id = 1")

    def recover_timer_state(self) -> tuple[str, int, int | None] | None:
        """Recover timer state after app restart or wake from sleep.
        
        Returns:
            None if no timer was running.
            (subject_name, completed_minutes, None) if the session finished while away.
            (subject_name, remaining_seconds, total_duration) if still active to resume.
        """
        cursor = self.db.connection.execute(
            """
            SELECT is_active, subject_name, total_duration_minutes,
                   start_time, target_end_time, is_paused, paused_remaining_seconds
            FROM active_timer_state WHERE id = 1
            """
        )
        row = cursor.fetchone()
        if not row or not row["is_active"]:
            return None

        subject_name = row["subject_name"]
        total_duration = row["total_duration_minutes"]
        target_end = datetime.fromisoformat(row["target_end_time"])
        is_paused = bool(row["is_paused"])
        paused_seconds = row["paused_remaining_seconds"]
        now = datetime.now()

        self.clear_timer_state()

        if is_paused:
            # Paused session survives with paused remaining seconds
            return (subject_name, paused_seconds, total_duration)

        if now >= target_end:
            # Session completed while machine was closed/off!
            # Return full duration as completed minutes so effort is never lost
            return (subject_name, total_duration, None)
        else:
            # Session is still running!
            remaining_seconds = max(1, int((target_end - now).total_seconds()))
            return (subject_name, remaining_seconds, total_duration)

    # -------------------------------------------------------------------------
    # Study Todos & Academic Preparation
    # -------------------------------------------------------------------------

    def _row_to_todo(self, row) -> StudyTodo:
        """Convert a database row into a StudyTodo model."""
        return StudyTodo(
            id=row["id"],
            subject_name=row["subject_name"],
            title=row["title"],
            notes=row["notes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            due_date=datetime.fromisoformat(row["due_date"]),
            status=row["status"],
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            confidence=row["confidence"],
            next_class_question=row["next_class_question"],
            session_ref_id=row["session_ref_id"],
        )

    def add_todo(self, todo: StudyTodo) -> None:
        """Insert or update a preparation task / todo."""
        query = """
            INSERT INTO study_todos (
                id, subject_name, title, notes, created_at, due_date, status,
                completed_at, confidence, next_class_question, session_ref_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                subject_name = excluded.subject_name,
                title = excluded.title,
                notes = excluded.notes,
                created_at = excluded.created_at,
                due_date = excluded.due_date,
                status = excluded.status,
                completed_at = excluded.completed_at,
                confidence = excluded.confidence,
                next_class_question = excluded.next_class_question,
                session_ref_id = excluded.session_ref_id;
        """
        with self.db.connection as conn:
            conn.execute(
                query,
                (
                    todo.id,
                    todo.subject_name,
                    todo.title,
                    todo.notes,
                    todo.created_at.isoformat(),
                    todo.due_date.isoformat(),
                    todo.status,
                    todo.completed_at.isoformat() if todo.completed_at else None,
                    todo.confidence,
                    todo.next_class_question,
                    todo.session_ref_id,
                ),
            )

    def get_todo_by_id(self, todo_id: str) -> StudyTodo | None:
        """Return a single todo by its ID, or None if not found."""
        query = "SELECT * FROM study_todos WHERE id = ?"
        cursor = self.db.connection.execute(query, (todo_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_todo(row)

    def get_all_todos(self, status: str | None = None) -> list[StudyTodo]:
        """Return all study todos, optionally filtered by status, ordered by due_date ASC."""
        if status:
            query = "SELECT * FROM study_todos WHERE status = ? ORDER BY due_date ASC"
            cursor = self.db.connection.execute(query, (status,))
        else:
            query = "SELECT * FROM study_todos ORDER BY due_date ASC"
            cursor = self.db.connection.execute(query)
        return [self._row_to_todo(row) for row in cursor.fetchall()]

    def get_todos_by_subject(self, subject_name: str, status: str | None = None) -> list[StudyTodo]:
        """Return todos for a specific subject, optionally filtered by status, ordered by due_date ASC."""
        if status:
            query = "SELECT * FROM study_todos WHERE subject_name = ? AND status = ? ORDER BY due_date ASC"
            cursor = self.db.connection.execute(query, (subject_name, status))
        else:
            query = "SELECT * FROM study_todos WHERE subject_name = ? ORDER BY due_date ASC"
            cursor = self.db.connection.execute(query, (subject_name,))
        return [self._row_to_todo(row) for row in cursor.fetchall()]

    def get_pending_todos(self, subject_name: str | None = None) -> list[StudyTodo]:
        """Return pending (non-completed) todos, optionally filtered by subject, ordered by due_date ASC."""
        if subject_name:
            return self.get_todos_by_subject(subject_name, status="pending")
        return self.get_all_todos(status="pending")

    def delete_todo(self, todo_id: str) -> bool:
        """Delete a study todo by ID. Returns True if deleted."""
        with self.db.connection as conn:
            cursor = conn.execute("DELETE FROM study_todos WHERE id = ?", (todo_id,))
            return cursor.rowcount > 0

    def update_todo(self, todo: StudyTodo) -> bool:
        """Update an existing study todo's attributes. Returns True if updated."""
        query = """
            UPDATE study_todos
            SET subject_name = ?,
                title = ?,
                notes = ?,
                due_date = ?,
                status = ?,
                completed_at = ?,
                confidence = ?,
                next_class_question = ?,
                session_ref_id = ?
            WHERE id = ?;
        """
        with self.db.connection as conn:
            cursor = conn.execute(
                query,
                (
                    todo.subject_name,
                    todo.title,
                    todo.notes,
                    todo.due_date.isoformat(),
                    todo.status,
                    todo.completed_at.isoformat() if todo.completed_at else None,
                    todo.confidence,
                    todo.next_class_question,
                    todo.session_ref_id,
                    todo.id,
                ),
            )
            return cursor.rowcount > 0

    def mark_todo_completed(
        self,
        todo_id: str,
        confidence: str | None = None,
        next_class_question: str | None = None,
        completed_at: datetime | None = None,
    ) -> bool:
        """Mark a todo as completed with optional confidence rating and next-class question."""
        now = completed_at or datetime.now()
        query = """
            UPDATE study_todos
            SET status = 'completed',
                completed_at = ?,
                confidence = COALESCE(?, confidence),
                next_class_question = COALESCE(?, next_class_question)
            WHERE id = ?;
        """
        with self.db.connection as conn:
            cursor = conn.execute(
                query,
                (
                    now.isoformat(),
                    confidence,
                    next_class_question,
                    todo_id,
                ),
            )
            return cursor.rowcount > 0

    def mark_todo_pending(self, todo_id: str) -> bool:
        """Mark a completed todo back as pending."""
        query = """
            UPDATE study_todos
            SET status = 'pending',
                completed_at = NULL
            WHERE id = ?;
        """
        with self.db.connection as conn:
            cursor = conn.execute(query, (todo_id,))
            return cursor.rowcount > 0

    def get_questions_by_subject(self, subject_name: str) -> list[str]:
        """Return non-empty next_class_question entries for a subject."""
        query = """
            SELECT next_class_question
            FROM study_todos
            WHERE subject_name = ?
              AND next_class_question IS NOT NULL
              AND trim(next_class_question) != ''
            ORDER BY due_date ASC
        """
        cursor = self.db.connection.execute(query, (subject_name,))
        return [row["next_class_question"] for row in cursor.fetchall()]

    def mark_day_debriefed(self, ref_date: date) -> None:
        """Mark a calendar date as having completed the nightly desk debrief."""
        with self.db.connection as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value) VALUES ('last_debrief_date', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                """,
                (ref_date.isoformat(),),
            )

    def is_day_debriefed(self, ref_date: date) -> bool:
        """Check if ref_date was marked as debriefed."""
        cursor = self.db.connection.execute(
            "SELECT value FROM app_settings WHERE key = 'last_debrief_date'"
        )
        row = cursor.fetchone()
        if row and row["value"]:
            return row["value"] == ref_date.isoformat()
        return False

    def clear_subject_question(self, subject_name: str, question_text: str) -> bool:
        """Clear a specific next_class_question when asked/resolved in class."""
        query = """
            UPDATE study_todos
            SET next_class_question = ''
            WHERE subject_name = ? AND next_class_question = ?;
        """
        with self.db.connection as conn:
            cursor = conn.execute(query, (subject_name, question_text))
            return cursor.rowcount > 0



"""Data repository providing domain-level persistence operations."""

from datetime import datetime
import json
from pathlib import Path
from typing import Sequence

from study_station.core.models import (
    AcademicSession,
    StudyLog,
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
            INSERT INTO study_logs (id, subject_name, study_cycle_id, started_at, duration_minutes, source)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                subject_name = excluded.subject_name,
                study_cycle_id = excluded.study_cycle_id,
                started_at = excluded.started_at,
                duration_minutes = excluded.duration_minutes,
                source = excluded.source;
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
                ),
            )

    def get_all_study_logs(self) -> list[StudyLog]:
        """Return all study logs ordered chronologically."""
        query = "SELECT id, subject_name, study_cycle_id, started_at, duration_minutes, source FROM study_logs ORDER BY started_at ASC"
        cursor = self.db.connection.execute(query)
        logs: list[StudyLog] = []
        for row in cursor.fetchall():
            logs.append(
                StudyLog(
                    id=row["id"],
                    subject_name=row["subject_name"],
                    study_cycle_id=row["study_cycle_id"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    duration_minutes=row["duration_minutes"],
                    source=row["source"],
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
    ) -> bool:
        """Update an existing study log's details. Returns True if updated."""
        query = """
            UPDATE study_logs
            SET subject_name = ?,
                duration_minutes = ?,
                started_at = COALESCE(?, started_at)
            WHERE id = ?;
        """
        with self.db.connection as conn:
            cursor = conn.execute(
                query,
                (
                    subject_name,
                    max(1, duration_minutes),
                    started_at.isoformat() if started_at else None,
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

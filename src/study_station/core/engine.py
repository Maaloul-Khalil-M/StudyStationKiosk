"""Schedule Engine for Study Station.

Deterministic core logic answering schedule and study-cycle questions based on
the weekly timetable and current local time.
"""

from __future__ import annotations
from datetime import datetime, date, time, timedelta
import json
from pathlib import Path
from typing import Sequence

from study_station.core.models import (
    AcademicSession,
    DAY_INDEX_MAP,
    StudyCycle,
    StudyLog,
    StudyTodo,
    Subject,
    SubjectSummary,
    TimeSlot,
)


class ScheduleEngine:
    """Pure, deterministic engine managing timetable sessions and study cycles."""

    def __init__(
        self,
        sessions: Sequence[AcademicSession] | None = None,
        default_target_minutes: int = 60,
        repository: "StudyStationRepository | None" = None,
    ) -> None:
        self.repository = repository
        self.default_target_minutes = default_target_minutes

        if self.repository is not None:
            loaded_sessions = self.repository.get_timetable_sessions()
            self.sessions: list[AcademicSession] = list(loaded_sessions if loaded_sessions else (sessions or []))
            self._target_overrides: dict[str, int] = self.repository.get_all_subject_targets()
            self.study_logs: list[StudyLog] = self.repository.get_all_study_logs()
            self.todos: list[StudyTodo] = self.repository.get_all_todos()
        else:
            self.sessions = list(sessions or [])
            self.study_logs = []
            self.todos = []
            self._target_overrides = {}

    @classmethod
    def from_repository(cls, repository: "StudyStationRepository", default_target_minutes: int = 60) -> ScheduleEngine:
        """Create ScheduleEngine powered by persistence repository."""
        return cls(repository=repository, default_target_minutes=default_target_minutes)

    @classmethod
    def from_json_file(cls, json_path: str | Path, default_target_minutes: int = 60) -> ScheduleEngine:
        """Load schedule from a JSON file matching the timetable schema."""
        path = Path(json_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_sessions = data.get("sessions", [])
        sessions: list[AcademicSession] = []
        for s in raw_sessions:
            time_slot = TimeSlot(
                start=s["timeSlot"]["start"],
                end=s["timeSlot"]["end"],
            )
            subject = Subject(
                name=s["subject"]["name"],
                core=s["subject"].get("core", "COURS"),
            )
            session = AcademicSession(
                day=s["day"],
                time_slot=time_slot,
                subject=subject,
                location=s.get("location", ""),
            )
            sessions.append(session)

        return cls(sessions=sessions, default_target_minutes=default_target_minutes)

    def set_subject_target(self, subject_name: str, target_minutes: int) -> None:
        """Set or update target review minutes for a specific subject."""
        val = max(1, target_minutes)
        self._target_overrides[subject_name] = val
        if self.repository is not None:
            self.repository.set_subject_target(subject_name, val)

    def get_subject_target(self, subject_name: str) -> int:
        """Return the target review minutes for a subject."""
        return self._target_overrides.get(subject_name, self.default_target_minutes)

    def add_study_log(self, log: StudyLog) -> None:
        """Record a completed study session or manual time entry."""
        self.study_logs.append(log)
        if self.repository is not None:
            self.repository.add_study_log(log)

    def delete_study_log(self, log_id: str) -> bool:
        """Delete a study log by its ID from memory and database."""
        idx = next((i for i, l in enumerate(self.study_logs) if l.id == log_id), None)
        if idx is not None:
            self.study_logs.pop(idx)
            if self.repository is not None:
                self.repository.delete_study_log(log_id)
            return True
        return False

    def update_study_log(
        self,
        log_id: str,
        subject_name: str,
        duration_minutes: int,
        started_at: datetime | None = None,
    ) -> bool:
        """Update an existing study log's details in memory and database."""
        for log in self.study_logs:
            if log.id == log_id:
                log.subject_name = subject_name
                log.duration_minutes = max(1, duration_minutes)
                if started_at is not None:
                    log.started_at = started_at
                if self.repository is not None:
                    self.repository.update_study_log(log_id, subject_name, duration_minutes, started_at)
                return True
        return False

    def get_study_logs(
        self,
        reverse: bool = True,
        subject_filter: str | None = None,
        source_filter: str | None = None,
    ) -> list[StudyLog]:
        """Return study logs with optional filtering and sorting."""
        logs = list(self.study_logs)
        if subject_filter:
            logs = [l for l in logs if l.subject_name == subject_filter]
        if source_filter:
            logs = [l for l in logs if l.source.lower() == source_filter.lower()]
        logs.sort(key=lambda l: l.started_at, reverse=reverse)
        return logs

    def get_total_study_minutes(self) -> int:
        """Calculate total study minutes recorded across all sessions."""
        return sum(log.duration_minutes for log in self.study_logs)

    def get_weekly_study_minutes(self, ref_date: date | None = None) -> int:
        """Calculate total study minutes recorded in the academic week of ref_date."""
        monday = self.get_week_start(ref_date)
        week_start_dt = datetime.combine(monday, time.min)
        week_end_dt = datetime.combine(monday + timedelta(days=7), time.min)
        return sum(
            log.duration_minutes
            for log in self.study_logs
            if week_start_dt <= log.started_at < week_end_dt
        )

    def get_weekly_study_by_subject(self, ref_date: date | None = None) -> dict[str, int]:
        """Return a mapping of subject_name -> minutes studied in ref_date's week."""
        monday = self.get_week_start(ref_date)
        week_start_dt = datetime.combine(monday, time.min)
        week_end_dt = datetime.combine(monday + timedelta(days=7), time.min)
        breakdown: dict[str, int] = {}
        for log in self.study_logs:
            if week_start_dt <= log.started_at < week_end_dt:
                breakdown[log.subject_name] = breakdown.get(log.subject_name, 0) + log.duration_minutes
        return breakdown

    def get_cycle_completion_stats(self, ref_dt: datetime | None = None) -> tuple[int, int, int]:
        """Return (completed_cycles, total_cycles, completion_percent) across active cycles."""
        current_dt = ref_dt or datetime.now()
        active_cycles = self.get_all_active_cycles(current_dt)
        if not active_cycles:
            return 0, 0, 0
        completed = sum(1 for c in active_cycles if c.is_target_met)
        total = len(active_cycles)
        pct = int((completed / total) * 100) if total > 0 else 0
        return completed, total, pct

    # -------------------------------------------------------------------------
    # Study Todos & Academic Preparation
    # -------------------------------------------------------------------------

    def add_todo(self, todo: StudyTodo) -> None:
        """Add or update a study todo."""
        existing_idx = next((i for i, t in enumerate(self.todos) if t.id == todo.id), None)
        if existing_idx is not None:
            self.todos[existing_idx] = todo
        else:
            self.todos.append(todo)
        if self.repository is not None:
            self.repository.add_todo(todo)

    def delete_todo(self, todo_id: str) -> bool:
        """Delete a study todo by ID."""
        idx = next((i for i, t in enumerate(self.todos) if t.id == todo_id), None)
        if idx is not None:
            self.todos.pop(idx)
            if self.repository is not None:
                self.repository.delete_todo(todo_id)
            return True
        return False

    def update_todo(self, todo: StudyTodo) -> bool:
        """Update a study todo."""
        idx = next((i for i, t in enumerate(self.todos) if t.id == todo.id), None)
        if idx is not None:
            self.todos[idx] = todo
            if self.repository is not None:
                self.repository.update_todo(todo)
            return True
        return False

    def mark_todo_completed(
        self,
        todo_id: str,
        confidence: str | None = None,
        next_class_question: str | None = None,
        completed_at: datetime | None = None,
    ) -> bool:
        """Mark a todo as completed in memory and persistence."""
        now = completed_at or datetime.now()
        for t in self.todos:
            if t.id == todo_id:
                t.status = "completed"
                t.completed_at = now
                if confidence is not None:
                    t.confidence = confidence
                if next_class_question is not None:
                    t.next_class_question = next_class_question
                if self.repository is not None:
                    self.repository.mark_todo_completed(todo_id, confidence, next_class_question, now)
                return True
        return False

    def get_todos(
        self,
        subject_filter: str | None = None,
        status_filter: str | None = None,
    ) -> list[StudyTodo]:
        """Return study todos with optional filtering, sorted by due_date ASC."""
        res = list(self.todos)
        if subject_filter:
            res = [t for t in res if t.subject_name.lower() == subject_filter.lower()]
        if status_filter:
            res = [t for t in res if t.status.lower() == status_filter.lower()]
        res.sort(key=lambda t: t.due_date)
        return res

    def get_pending_todos(self, subject_name: str | None = None) -> list[StudyTodo]:
        """Return all pending study todos, optionally filtered by subject."""
        return self.get_todos(subject_filter=subject_name, status_filter="pending")

    def get_todos_due_before(self, dt: datetime, subject_name: str | None = None) -> list[StudyTodo]:
        """Return pending todos due on or before dt."""
        pending = self.get_pending_todos(subject_name)
        return [t for t in pending if t.due_date <= dt]

    def get_subject_pending_todos_count(self, subject_name: str) -> int:
        """Count pending todos for a subject."""
        return len(self.get_pending_todos(subject_name))

    def get_subject_questions(self, subject_name: str) -> list[str]:
        """Return list of non-empty next_class_questions for a subject."""
        questions = []
        clean = self.clean_subject_name(subject_name)
        for t in self.todos:
            if self.clean_subject_name(t.subject_name).lower() == clean.lower():
                if t.next_class_question and t.next_class_question.strip():
                    questions.append(t.next_class_question.strip())
        return questions

    def resolve_subject_question(self, subject_name: str, question_text: str) -> bool:
        """Mark an in-class question as asked/resolved."""
        clean = self.clean_subject_name(subject_name)
        matched = False
        for t in self.todos:
            if self.clean_subject_name(t.subject_name).lower() == clean.lower():
                if t.next_class_question and t.next_class_question.strip() == question_text.strip():
                    t.next_class_question = ""
                    matched = True
        if self.repository is not None:
            self.repository.clear_subject_question(subject_name, question_text)
        return matched

    def mark_day_debriefed(self, ref_date: date | None = None) -> None:
        """Record that the nightly debrief for ref_date has been completed."""
        d = ref_date or date.today()
        if not hasattr(self, "_debriefed_dates"):
            self._debriefed_dates = set()
        self._debriefed_dates.add(d.isoformat())
        if self.repository is not None:
            self.repository.mark_day_debriefed(d)

    def is_day_debriefed(self, ref_date: date | None = None) -> bool:
        """Check if ref_date was marked as debriefed."""
        d = ref_date or date.today()
        if not hasattr(self, "_debriefed_dates"):
            self._debriefed_dates = set()
        if d.isoformat() in self._debriefed_dates:
            return True
        if self.repository is not None:
            debriefed = self.repository.is_day_debriefed(d)
            if debriefed:
                self._debriefed_dates.add(d.isoformat())
            return debriefed
        return False

    def should_prompt_nightly_debrief(self, current_dt: datetime | None = None) -> bool:
        """Determine whether the nightly debrief banner should be displayed."""
        now = current_dt or datetime.now()
        is_evening = (now.hour >= 18 or now.hour < 4)
        if not is_evening:
            return False
        day_sessions = self.get_day_sessions(now.weekday())
        if not day_sessions:
            return False
        return not self.is_day_debriefed(now.date())

    def get_priority_study_todo(self, current_dt: datetime | None = None) -> StudyTodo | None:
        """Find the single most urgent pending task for tonight's study session."""
        now = current_dt or datetime.now()
        pending = self.get_pending_todos()
        if not pending:
            return None

        def sort_key(todo: StudyTodo):
            is_overdue = todo.is_overdue(now)
            return (0 if is_overdue else 1, todo.due_date)

        pending.sort(key=sort_key)
        return pending[0]

    def get_next_class_deadline_for_subject(
        self, subject_name: str, current_dt: datetime
    ) -> datetime | None:
        """Calculate the start datetime of the next occurrence of a subject, ideal as default task deadline."""
        next_info = self.get_next_occurrence_of_subject(subject_name, current_dt)
        if next_info:
            _, next_start = next_info
            return next_start
        return None

    def get_distinct_subjects(self) -> list[str]:
        """Return sorted list of distinct subject names in timetable."""
        return sorted({s.subject.name for s in self.sessions})

    @classmethod
    def get_week_start(cls, ref_date: date | None = None) -> date:
        """Return the Monday date of the week containing ref_date (defaults to today)."""
        d = ref_date or date.today()
        return d - timedelta(days=d.weekday())

    @classmethod
    def get_week_dates(cls, ref_date: date | None = None, days_count: int = 6) -> list[date]:
        """Return list of dates for the academic week starting on Monday.

        Args:
            ref_date: Any date within the target week.
            days_count: Number of days in academic week (default 6: Monday to Saturday).
        """
        monday = cls.get_week_start(ref_date)
        return [monday + timedelta(days=i) for i in range(days_count)]

    @classmethod
    def format_week_range(cls, ref_date: date | None = None, days_count: int = 6) -> str:
        """Return a formatted string representing the week range.

        Examples:
            "12 – 17 OCT 2026"
            "28 SEP – 03 OCT 2026"
            "28 DEC 2026 – 02 JAN 2027"
        """
        dates = cls.get_week_dates(ref_date, days_count=days_count)
        start_d = dates[0]
        end_d = dates[-1]

        month_start = start_d.strftime("%b").upper()
        month_end = end_d.strftime("%b").upper()

        if start_d.year != end_d.year:
            return f"{start_d.day:02d} {month_start} {start_d.year} – {end_d.day:02d} {month_end} {end_d.year}"
        elif start_d.month != end_d.month:
            return f"{start_d.day:02d} {month_start} – {end_d.day:02d} {month_end} {start_d.year}"
        else:
            return f"{start_d.day:02d} – {end_d.day:02d} {month_start} {start_d.year}"

    @classmethod
    def get_day_date(cls, day_code: str, ref_date: date | None = None) -> date | None:
        """Return the specific date for a given day code ('Lun', 'Mar', etc.) in ref_date's week."""
        idx = DAY_INDEX_MAP.get(day_code.capitalize())
        if idx is None:
            return None
        monday = cls.get_week_start(ref_date)
        return monday + timedelta(days=idx)

    def get_session_datetime(self, session: AcademicSession, ref_date: date) -> tuple[datetime, datetime]:
        """Convert a session to actual start and end datetimes for the week of ref_date."""
        monday = ref_date - timedelta(days=ref_date.weekday())
        session_date = monday + timedelta(days=session.day_index)
        start_dt = datetime.combine(session_date, session.time_slot.start_time)
        end_dt = datetime.combine(session_date, session.time_slot.end_time)
        return start_dt, end_dt

    def get_day_sessions(self, day: int | str) -> list[AcademicSession]:
        """Return all sessions scheduled for a given day (0-indexed int or 'Lun'/'Mar' etc.), sorted by start time."""
        if isinstance(day, str):
            day_idx = DAY_INDEX_MAP.get(day.capitalize(), 0)
        else:
            day_idx = day
        matching = [s for s in self.sessions if s.day_index == day_idx]
        matching.sort(key=lambda s: s.time_slot.start_time)
        return matching

    def get_current_session(self, current_dt: datetime) -> AcademicSession | None:
        """Return the AcademicSession in progress at current_dt, if any."""
        current_day_idx = current_dt.weekday()
        current_time = current_dt.time()

        for session in self.sessions:
            if session.day_index == current_day_idx:
                if session.time_slot.start_time <= current_time < session.time_slot.end_time:
                    return session
        return None

    def get_next_session(self, current_dt: datetime) -> tuple[AcademicSession, datetime] | None:
        """Return the chronologically next upcoming session and its start datetime."""
        if not self.sessions:
            return None

        candidates: list[tuple[datetime, AcademicSession]] = []
        for week_offset in (0, 1):
            ref_date = current_dt.date() + timedelta(weeks=week_offset)
            for session in self.sessions:
                start_dt, _ = self.get_session_datetime(session, ref_date)
                if start_dt > current_dt:
                    candidates.append((start_dt, session))

        if not candidates:
            return None

        candidates.sort(key=lambda c: c[0])
        next_dt, next_session = candidates[0]
        return next_session, next_dt

    def get_upcoming_sessions(self, current_dt: datetime, limit: int = 4) -> list[tuple[AcademicSession, datetime]]:
        """Return the next `limit` upcoming academic sessions sorted chronologically."""
        if not self.sessions:
            return []

        candidates: list[tuple[datetime, AcademicSession]] = []
        for week_offset in (0, 1):
            ref_date = current_dt.date() + timedelta(weeks=week_offset)
            for session in self.sessions:
                start_dt, _ = self.get_session_datetime(session, ref_date)
                if start_dt > current_dt:
                    candidates.append((start_dt, session))

        if not candidates:
            return []

        candidates.sort(key=lambda c: c[0])
        return [(session, dt) for dt, session in candidates[:limit]]

    def get_next_occurrence_of_subject(
        self, subject_name: str, current_dt: datetime
    ) -> tuple[AcademicSession, datetime] | None:
        """Find the next scheduled session for a specific subject after current_dt."""
        matching = [s for s in self.sessions if s.subject.name == subject_name]
        if not matching:
            return None

        candidates: list[tuple[datetime, AcademicSession]] = []
        for week_offset in (0, 1):
            ref_date = current_dt.date() + timedelta(weeks=week_offset)
            for s in matching:
                start_dt, _ = self.get_session_datetime(s, ref_date)
                if start_dt > current_dt:
                    candidates.append((start_dt, s))

        if not candidates:
            return None

        candidates.sort(key=lambda c: c[0])
        next_dt, session = candidates[0]
        return session, next_dt

    def get_active_cycle(self, subject_name: str, current_dt: datetime) -> StudyCycle | None:
        """Construct the active StudyCycle for a subject at current_dt."""
        matching = [s for s in self.sessions if s.subject.name == subject_name]
        if not matching:
            return None

        all_occurrences: list[tuple[datetime, datetime]] = []
        for week_offset in (-1, 0, 1):
            ref_date = current_dt.date() + timedelta(weeks=week_offset)
            for s in matching:
                start_dt, end_dt = self.get_session_datetime(s, ref_date)
                all_occurrences.append((start_dt, end_dt))

        all_occurrences.sort(key=lambda occ: occ[0])

        last_ended: datetime | None = None
        next_start: datetime | None = None

        for start_dt, end_dt in all_occurrences:
            if end_dt <= current_dt:
                last_ended = end_dt
            elif start_dt > current_dt and next_start is None:
                next_start = start_dt
                break

        if last_ended is None or next_start is None:
            return None

        # Calculate completed minutes within this cycle window
        completed_minutes = sum(
            log.duration_minutes
            for log in self.study_logs
            if log.subject_name == subject_name and last_ended <= log.started_at < next_start
        )

        target = self.get_subject_target(subject_name)
        cycle_id = f"{subject_name}-{last_ended.isoformat()}"

        return StudyCycle(
            id=cycle_id,
            subject_name=subject_name,
            start_at=last_ended,
            end_at=next_start,
            target_minutes=target,
            status="active",
            completed_minutes=completed_minutes,
        )

    def get_all_active_cycles(self, current_dt: datetime) -> list[StudyCycle]:
        """Return active cycles for all subjects at current_dt."""
        cycles: list[StudyCycle] = []
        for name in self.get_distinct_subjects():
            cycle = self.get_active_cycle(name, current_dt)
            if cycle is not None:
                cycles.append(cycle)
        return cycles

    def get_suggested_cycle(self, current_dt: datetime) -> StudyCycle | None:
        """Recommend the next unfinished cycle whose upcoming class is closest."""
        active_cycles = self.get_all_active_cycles(current_dt)
        unfinished = [c for c in active_cycles if not c.is_target_met]

        if not unfinished:
            return active_cycles[0] if active_cycles else None

        # Sort by urgency: class occurrence arriving soonest
        unfinished.sort(key=lambda c: c.end_at)
        return unfinished[0]

    def get_ambient_status_text(self, current_dt: datetime) -> str:
        """Format the single discreet secondary line for the ambient screen.
        
        Example: "DATA VIS. · 25 / 60 MIN"
        """
        # If currently in class:
        current_session = self.get_current_session(current_dt)
        if current_session:
            short_name = self._abbreviate_subject(current_session.subject.name)
            loc = f" ({current_session.location})" if current_session.location else ""
            return f"IN CLASS · {short_name}{loc}"

        # Otherwise show suggested active cycle progress
        suggested = self.get_suggested_cycle(current_dt)
        if suggested:
            short_name = self._abbreviate_subject(suggested.subject_name)
            return f"{short_name} · {suggested.completed_minutes} / {suggested.target_minutes} MIN"

        # Fallback to next upcoming class if no cycles
        next_info = self.get_next_session(current_dt)
        if next_info:
            next_session, next_time = next_info
            short_name = self._abbreviate_subject(next_session.subject.name)
            delta = next_time - current_dt
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            mins = remainder // 60
            if hours > 0:
                time_str = f"IN {hours}H {mins:02d}M"
            else:
                time_str = f"IN {mins}M"
            return f"NEXT · {short_name} {time_str}"

        return ""

    @classmethod
    def clean_subject_name(cls, name: str) -> str:
        """Fix common spelling errors in imported subject titles."""
        return (
            name.strip()
            .replace("ACCÉES", "ACCÈS")
            .replace("accées", "accès")
            .replace("CONTROLE", "CONTRÔLE")
            .replace("controle", "contrôle")
        )

    @classmethod
    def _abbreviate_subject(cls, name: str) -> str:
        """Keep subject names readable and compact for the ambient secondary line."""
        clean = cls.clean_subject_name(name)
        upper = clean.upper()

        # Direct friendly abbreviations
        mapping = {
            "VISUALISATION DES DONNÉES": "DATA VIS.",
            "TECHNIQUES DE PRÉVISION": "PRÉVISION",
            "TECHNIQUE DE VEILLE": "VEILLE",
            "LA CYBER-CRIMINALITÉ": "CYBER-CRIME",
            "BASES DE DONNÉES NOSQL": "NOSQL",
            "ENTREPÔTS DE DONNÉES": "DATA WAREHOUSE",
            "SÉCURITÉ ET CONTRÔLE D'ACCÈS AUX BIG DATA": "SÉCURITÉ BIG DATA",
            "SÉCURITÉ ET CONTROLE D'ACCÉES AUX BIG DATA": "SÉCURITÉ BIG DATA",
            "FRAMEWORK DE DÉVELOPPEMENT WEB": "WEB DEV",
            "TESTS LOGICIELS (CERTIFICATION ISTQB)": "TESTS LOGICIELS",
            "ENTREPRENARIAT": "ENTREPRENARIAT",
            "ANGLAIS 4": "ANGLAIS 4",
        }
        if upper in mapping:
            return mapping[upper]

        # General cleanup fallback
        for k, v in mapping.items():
            if k in upper or upper in k:
                return v

        return upper if len(upper) <= 22 else upper[:20].rstrip() + "…"

    def get_subject_summary(self, subject_name: str, current_dt: datetime) -> SubjectSummary:
        """Return rich summary for subject display, progress, and upcoming schedule context."""
        clean_name = self.clean_subject_name(subject_name)
        short_name = self._abbreviate_subject(clean_name)

        # Check if currently in class for this subject
        curr_session = self.get_current_session(current_dt)
        is_current_class = bool(curr_session and curr_session.subject.name == subject_name)

        # Find next occurrence
        next_info = self.get_next_occurrence_of_subject(subject_name, current_dt)
        next_dt: datetime | None = None
        next_text = "No upcoming class"
        core_type = "COURS"
        loc = ""

        if next_info:
            session, next_dt = next_info
            core_type = session.subject.core
            loc = session.location
            next_text = self._format_relative_session_time(next_dt, current_dt)
        else:
            matches = [s for s in self.sessions if s.subject.name == subject_name]
            if matches:
                core_type = matches[0].subject.core
                loc = matches[0].location

        # Cycle progress
        cycle = self.get_active_cycle(subject_name, current_dt)
        if cycle:
            target = cycle.target_minutes
            completed = cycle.completed_minutes
            remaining = cycle.remaining_minutes
            met = cycle.is_target_met
        else:
            target = self.get_subject_target(subject_name)
            completed = 0
            remaining = target
            met = False

        pct = min(100, int((completed / target) * 100)) if target > 0 else 0
        pending_count = self.get_subject_pending_todos_count(subject_name)
        questions_count = len(self.get_subject_questions(subject_name))

        return SubjectSummary(
            name=clean_name,
            short_name=short_name,
            core=core_type,
            location=loc,
            target_minutes=target,
            completed_minutes=completed,
            remaining_minutes=remaining,
            progress_percent=pct,
            next_session_dt=next_dt,
            next_session_text=next_text,
            is_target_met=met,
            is_current_class=is_current_class,
            pending_todos_count=pending_count,
            questions_count=questions_count,
        )

    def get_all_subjects_summary(self, current_dt: datetime) -> list[SubjectSummary]:
        """Return summaries for all distinct subjects, prioritizing those needing attention."""
        summaries = [self.get_subject_summary(name, current_dt) for name in self.get_distinct_subjects()]

        def sort_key(s: SubjectSummary) -> tuple[int, datetime]:
            prio = 0 if s.is_current_class else (1 if not s.is_target_met else 2)
            far_future = datetime.max
            return (prio, s.next_session_dt or far_future)

        summaries.sort(key=sort_key)
        return summaries

    @classmethod
    def _format_relative_session_time(cls, session_dt: datetime, current_dt: datetime) -> str:
        """Format friendly relative time string for next class."""
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_str = day_names[session_dt.weekday()]
        time_str = session_dt.strftime("%H:%M")

        delta = session_dt - current_dt
        days_ahead = (session_dt.date() - current_dt.date()).days

        if days_ahead == 0:
            hours = int(delta.total_seconds() // 3600)
            mins = int((delta.total_seconds() % 3600) // 60)
            rel = f"in {hours}h {mins:02d}m" if hours > 0 else f"in {mins}m"
            return f"Today at {time_str} ({rel})"
        elif days_ahead == 1:
            return f"Tomorrow at {time_str}"
        elif days_ahead > 1:
            return f"{day_str} at {time_str} (in {days_ahead} days)"
        else:
            return f"{day_str} at {time_str}"

    def export_timetable(self, target_path: Path | str, file_format: str = "json") -> None:
        """Export current timetable sessions to JSON or CSV."""
        from study_station.core.timetable_portability import (
            export_sessions_to_json,
            export_sessions_to_csv,
        )
        if file_format.lower() == "csv":
            export_sessions_to_csv(self.sessions, target_path)
        else:
            export_sessions_to_json(self.sessions, target_path)

    def import_timetable_file(
        self,
        file_path: Path | str,
        replace: bool = False,
    ) -> tuple[int, list[str], list[tuple[AcademicSession, AcademicSession]]]:
        """Import timetable sessions from JSON, CSV, or PDF file.
        
        Returns (added_count, warnings, collisions).
        """
        from study_station.core.timetable_portability import (
            import_sessions_from_json,
            import_sessions_from_csv,
            import_sessions_from_pdf,
            detect_collisions,
            merge_sessions,
        )
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".json":
            incoming, warnings = import_sessions_from_json(path)
        elif ext in (".csv", ".tsv", ".txt"):
            incoming, warnings = import_sessions_from_csv(path)
        elif ext == ".pdf":
            incoming, warnings = import_sessions_from_pdf(path)
        else:
            return 0, [f"Unsupported file format '{ext}'. Supported: .json, .csv, .pdf"], []

        if not incoming:
            return 0, warnings, []

        merged_sessions, added, duplicates = merge_sessions(self.sessions, incoming, replace=replace)
        collisions = detect_collisions(merged_sessions)

        self.sessions = merged_sessions
        if self.repository is not None:
            self.repository.save_timetable_sessions(self.sessions)

        return added, warnings, collisions


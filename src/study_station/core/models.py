"""Domain models for Study Station.

Preserves separation between timetable facts and study-tracking behaviour.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time
import uuid


DAY_NAMES = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
DAY_INDEX_MAP = {day: idx for idx, day in enumerate(DAY_NAMES)}


def normalize_time_str(val: str) -> str | None:
    """Normalize '8:00', '08:00', '8h00', '8h' into standard '08:00'."""
    if not val:
        return None
    val = val.strip().replace("h", ":").replace("H", ":")
    if ":" in val:
        parts = val.split(":")
        try:
            h = int(parts[0])
            m = int(parts[1]) if parts[1] else 0
            if 0 <= h < 24 and 0 <= m < 60:
                return f"{h:02d}:{m:02d}"
        except (ValueError, IndexError):
            return None
    else:
        try:
            h = int(val)
            if 0 <= h < 24:
                return f"{h:02d}:00"
        except ValueError:
            return None
    return None


@dataclass(frozen=True)
class TimeSlot:
    """Represents a start and end time within a day."""

    start: str  # "HH:MM"
    end: str    # "HH:MM"

    def __post_init__(self) -> None:
        norm_start = normalize_time_str(self.start) or self.start
        norm_end = normalize_time_str(self.end) or self.end
        object.__setattr__(self, "start", norm_start)
        object.__setattr__(self, "end", norm_end)

    @property
    def start_time(self) -> time:
        hour, minute = map(int, self.start.split(":"))
        return time(hour, minute)

    @property
    def end_time(self) -> time:
        hour, minute = map(int, self.end.split(":"))
        return time(hour, minute)


@dataclass(frozen=True)
class Subject:
    """Represents an academic subject/module and session core type."""

    name: str
    core: str  # COURS, TD, TP, CI


@dataclass(frozen=True)
class AcademicSession:
    """Represents a scheduled class session on the timetable."""

    day: str  # "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"
    time_slot: TimeSlot
    subject: Subject
    location: str

    @property
    def day_index(self) -> int:
        """Return 0-indexed day of week (Monday=0 ... Sunday=6)."""
        return DAY_INDEX_MAP.get(self.day, 0)


@dataclass
class StudyCycle:
    """Represents the review period between consecutive occurrences of a subject."""

    id: str
    subject_name: str
    start_at: datetime
    end_at: datetime
    target_minutes: int = 60
    status: str = "active"  # "active" or "closed"
    completed_minutes: int = 0

    @property
    def remaining_minutes(self) -> int:
        return max(0, self.target_minutes - self.completed_minutes)

    @property
    def is_target_met(self) -> bool:
        return self.completed_minutes >= self.target_minutes


@dataclass
class StudyLog:
    """Records a single study session or manual time entry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject_name: str = ""
    study_cycle_id: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    duration_minutes: int = 0
    source: str = "timer"  # "timer" or "manual"
    todo_id: str | None = None


@dataclass
class StudyTodo:
    """Represents an actionable preparation task or project milestone for a subject."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject_name: str = ""
    title: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    due_date: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # "pending", "in_progress", "completed"
    completed_at: datetime | None = None
    confidence: str | None = None  # "foggy", "getting_there", "solid"
    next_class_question: str | None = None  # Formulated question for next class
    session_ref_id: str | None = None  # Reference to the session/class that generated this todo

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    def is_overdue(self, ref_dt: datetime | None = None) -> bool:
        now = ref_dt or datetime.now()
        return not self.is_completed and self.due_date < now

    def is_due_soon(self, hours: int = 24, ref_dt: datetime | None = None) -> bool:
        now = ref_dt or datetime.now()
        if self.is_completed or self.due_date < now:
            return False
        from datetime import timedelta
        return (self.due_date - now) <= timedelta(hours=hours)


@dataclass
class SubjectSummary:
    """Consolidated summary for a subject, its active cycle, next class, and review progress."""

    name: str
    short_name: str
    core: str
    location: str
    target_minutes: int
    completed_minutes: int
    remaining_minutes: int
    progress_percent: int  # 0 to 100
    next_session_dt: datetime | None
    next_session_text: str
    is_target_met: bool
    is_current_class: bool = False
    pending_todos_count: int = 0
    questions_count: int = 0


@dataclass
class ExitTicketResult:
    """Outcome of a Cognitive Exit Ticket debrief after a focus sprint."""

    action: str = "complete"  # "complete", "extend", "put_aside"
    confidence: str = "solid"  # "foggy", "progressing", "solid"
    next_class_question: str = ""
    takeaway_note: str = ""
    extend_minutes: int = 10




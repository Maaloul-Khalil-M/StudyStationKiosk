"""Domain models for Study Station.

Preserves separation between timetable facts and study-tracking behaviour.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time
import uuid


DAY_NAMES = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
DAY_INDEX_MAP = {day: idx for idx, day in enumerate(DAY_NAMES)}


@dataclass(frozen=True)
class TimeSlot:
    """Represents a start and end time within a day."""

    start: str  # "HH:MM"
    end: str    # "HH:MM"

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

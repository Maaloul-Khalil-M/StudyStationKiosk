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
    Subject,
    TimeSlot,
)


class ScheduleEngine:
    """Pure, deterministic engine managing timetable sessions and study cycles."""

    def __init__(
        self,
        sessions: Sequence[AcademicSession] | None = None,
        default_target_minutes: int = 60,
    ) -> None:
        self.sessions: list[AcademicSession] = list(sessions or [])
        self.default_target_minutes = default_target_minutes
        self.study_logs: list[StudyLog] = []
        self._target_overrides: dict[str, int] = {}  # subject_name -> target_minutes

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
        self._target_overrides[subject_name] = max(1, target_minutes)

    def get_subject_target(self, subject_name: str) -> int:
        """Return the target review minutes for a subject."""
        return self._target_overrides.get(subject_name, self.default_target_minutes)

    def add_study_log(self, log: StudyLog) -> None:
        """Record a completed study session or manual time entry."""
        self.study_logs.append(log)

    def get_distinct_subjects(self) -> list[str]:
        """Return sorted list of distinct subject names in timetable."""
        return sorted({s.subject.name for s in self.sessions})

    def get_session_datetime(self, session: AcademicSession, ref_date: date) -> tuple[datetime, datetime]:
        """Convert a session to actual start and end datetimes for the week of ref_date."""
        monday = ref_date - timedelta(days=ref_date.weekday())
        session_date = monday + timedelta(days=session.day_index)
        start_dt = datetime.combine(session_date, session.time_slot.start_time)
        end_dt = datetime.combine(session_date, session.time_slot.end_time)
        return start_dt, end_dt

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

"""Reliable focus countdown timer.

Uses real timestamps (target_end_time) to ensure resilience against
system clock suspension, sleep, or backgrounding.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable


@dataclass
class TimerSnapshot:
    """Read-only snapshot of current timer state."""

    subject_name: str
    remaining_seconds: int
    total_duration_minutes: int
    is_paused: bool
    is_finished: bool

    @property
    def formatted_remaining(self) -> str:
        mins, secs = divmod(self.remaining_seconds, 60)
        return f"{mins:02d}:{secs:02d}"


class FocusTimer:
    """Timestamp-based focus countdown timer."""

    def __init__(self) -> None:
        self.subject_name: str = ""
        self.total_duration_minutes: int = 0
        self.start_time: datetime | None = None
        self.target_end_time: datetime | None = None
        self._is_paused: bool = False
        self._paused_remaining_seconds: int = 0
        self._is_active: bool = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def start(self, subject_name: str, duration_minutes: int) -> None:
        """Start a new focus session."""
        now = datetime.now()
        self.subject_name = subject_name
        self.total_duration_minutes = duration_minutes
        self.start_time = now
        self.target_end_time = now + timedelta(minutes=duration_minutes)
        self._is_paused = False
        self._paused_remaining_seconds = duration_minutes * 60
        self._is_active = True

    def pause(self) -> None:
        """Pause the running countdown."""
        if not self._is_active or self._is_paused:
            return
        self._paused_remaining_seconds = self.get_remaining_seconds()
        self._is_paused = True

    def resume(self) -> None:
        """Resume counting down."""
        if not self._is_active or not self._is_paused:
            return
        self.target_end_time = datetime.now() + timedelta(seconds=self._paused_remaining_seconds)
        self._is_paused = False

    def toggle_pause(self) -> bool:
        """Toggle between paused and running state. Returns new is_paused state."""
        if self._is_paused:
            self.resume()
        else:
            self.pause()
        return self._is_paused

    def add_minutes(self, minutes: int = 5) -> None:
        """Extend the current session by additional minutes."""
        if not self._is_active:
            return
        self.total_duration_minutes += minutes
        if self._is_paused:
            self._paused_remaining_seconds += minutes * 60
        else:
            if self.target_end_time is not None:
                self.target_end_time += timedelta(minutes=minutes)

    def get_remaining_seconds(self) -> int:
        """Calculate remaining seconds based on real timestamp."""
        if not self._is_active:
            return 0
        if self._is_paused:
            return max(0, self._paused_remaining_seconds)
        if self.target_end_time is None:
            return 0

        diff = (self.target_end_time - datetime.now()).total_seconds()
        return max(0, int(round(diff)))

    def get_elapsed_minutes(self) -> int:
        """Calculate whole minutes spent focusing so far."""
        if not self._is_active or self.start_time is None:
            return 0
        rem = self.get_remaining_seconds()
        total_seconds = self.total_duration_minutes * 60
        elapsed_seconds = max(0, total_seconds - rem)
        return max(1, elapsed_seconds // 60) if elapsed_seconds >= 60 else 0

    def snapshot(self) -> TimerSnapshot:
        """Return an immutable snapshot of current state."""
        rem = self.get_remaining_seconds()
        return TimerSnapshot(
            subject_name=self.subject_name,
            remaining_seconds=rem,
            total_duration_minutes=self.total_duration_minutes,
            is_paused=self._is_paused,
            is_finished=self._is_active and rem == 0,
        )

    def stop(self) -> int:
        """Stop the timer and return the number of completed minutes."""
        elapsed = self.get_elapsed_minutes()
        self._is_active = False
        self._is_paused = False
        return elapsed

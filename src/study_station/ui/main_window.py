"""Main application window for Study Station.

Manages the transitions between the three primary screen states:
1. Ambient Clock (custom QPainter flip clock)
2. Focus Screen (countdown timer with Qt Designer controls)
3. Completion Screen (progress confirmation)
"""

from datetime import datetime
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from study_station.core.engine import ScheduleEngine
from study_station.core.models import StudyLog
from study_station.core.timer import FocusTimer
from study_station.ui.clock_widget import AmbientClockWidget
from study_station.ui.completion_widget import CompletionWidget
from study_station.ui.focus_widget import FocusWidget


class MainWindow(QMainWindow):
    """Full-screen application window hosting ambient, focus, and completion screens."""

    INDEX_CLOCK = 0
    INDEX_FOCUS = 1
    INDEX_COMPLETION = 2

    def __init__(self, engine: ScheduleEngine | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Study Station")
        self.resize(1366, 768)

        self._engine = engine
        self._timer = FocusTimer()

        # Pure black palette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Screen Stack
        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)

        # 1. Ambient Clock Screen
        self._clock_widget = AmbientClockWidget(self)
        self._stack.addWidget(self._clock_widget)

        # 2. Focus Screen
        self._focus_widget = FocusWidget(self._timer, self)
        self._focus_widget.session_finished.connect(self._on_session_finished)
        self._stack.addWidget(self._focus_widget)

        # 3. Completion Screen
        self._completion_widget = CompletionWidget(self)
        self._completion_widget.dismissed.connect(self._show_clock_screen)
        self._stack.addWidget(self._completion_widget)

        # Default to ambient screen
        self._stack.setCurrentIndex(self.INDEX_CLOCK)

        # Background status update timer
        if self._engine:
            self._update_progress_line()
            self._status_timer = QTimer(self)
            self._status_timer.setInterval(30_000)
            self._status_timer.timeout.connect(self._update_progress_line)
            self._status_timer.start()

    def _update_progress_line(self) -> None:
        """Fetch updated ambient status line from ScheduleEngine."""
        if self._engine:
            text = self._engine.get_ambient_status_text(datetime.now())
            self._clock_widget.secondary_text = text

    def start_focus_session(self, duration_minutes: int = 15) -> None:
        """Low-friction start of a focus session for the suggested subject."""
        subject_name = "STUDY"
        if self._engine:
            suggested = self._engine.get_suggested_cycle(datetime.now())
            if suggested:
                subject_name = suggested.subject_name
            elif self._engine.sessions:
                subject_name = self._engine.sessions[0].subject.name

        self._focus_widget.start_session(subject_name, duration_minutes)
        self._stack.setCurrentIndex(self.INDEX_FOCUS)

    def _on_session_finished(self, subject_name: str, elapsed_minutes: int) -> None:
        """Handle focus session completion or manual finish."""
        if elapsed_minutes <= 0:
            # Cancelled before completing a minute
            self._show_clock_screen()
            return

        # Record study log in engine
        target = 60
        completed = elapsed_minutes
        if self._engine:
            self._engine.add_study_log(
                StudyLog(
                    subject_name=subject_name,
                    started_at=datetime.now(),
                    duration_minutes=elapsed_minutes,
                    source="timer",
                )
            )
            cycle = self._engine.get_active_cycle(subject_name, datetime.now())
            if cycle:
                completed = cycle.completed_minutes
                target = cycle.target_minutes

            self._update_progress_line()

        # Show completion screen
        self._completion_widget.show_completion(
            subject_name=subject_name,
            added_minutes=elapsed_minutes,
            completed_minutes=completed,
            target_minutes=target,
        )
        self._stack.setCurrentIndex(self.INDEX_COMPLETION)

    def _show_clock_screen(self) -> None:
        """Return to ambient clock."""
        self._update_progress_line()
        self._stack.setCurrentIndex(self.INDEX_CLOCK)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Central keyboard shortcut dispatch."""
        key = event.key()
        current_idx = self._stack.currentIndex()

        # Global shortcuts
        if key == Qt.Key.Key_Q and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.close()
            return
        if key == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            return

        # Screen-specific shortcuts
        if current_idx == self.INDEX_CLOCK:
            if key == Qt.Key.Key_Escape:
                self.close()
            elif key == Qt.Key.Key_T:
                self._clock_widget.toggle_time_format()
            elif key in (Qt.Key.Key_Space, Qt.Key.Key_Return):
                # Low-friction session start (default 15m)
                self.start_focus_session(15)
            elif key == Qt.Key.Key_1:
                self.start_focus_session(5)
            elif key == Qt.Key.Key_2:
                self.start_focus_session(10)
            elif key == Qt.Key.Key_3:
                self.start_focus_session(15)
            elif key == Qt.Key.Key_4:
                self.start_focus_session(25)
            else:
                super().keyPressEvent(event)

        elif current_idx == self.INDEX_FOCUS:
            if key == Qt.Key.Key_Space:
                self._timer.toggle_pause()
                self._focus_widget._update_display()
            elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self._timer.add_minutes(5)
                self._focus_widget._update_display()
            elif key in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
                self._focus_widget._on_end_clicked()
            else:
                super().keyPressEvent(event)

        elif current_idx == self.INDEX_COMPLETION:
            # Any key dismisses completion screen
            self._show_clock_screen()
        else:
            super().keyPressEvent(event)

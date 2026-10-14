"""Main application window for Study Station.

Manages transitions between:
1. Modern Ambient Flip Clock with Date & Auto-hiding Action Bar
2. Focus Screen (countdown timer with visual progress and cycle tracking)
3. Completion Screen (progress confirmation)
"""

from datetime import datetime
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import QMainWindow, QMenu, QStackedWidget

from study_station.core.engine import ScheduleEngine
from study_station.core.models import StudyLog
from study_station.core.settings import AppSettings
from study_station.core.timer import FocusTimer
from study_station.ui.clock_widget import AmbientClockWidget
from study_station.ui.completion_widget import CompletionWidget
from study_station.ui.customization_dialog import CustomizationDialog
from study_station.ui.focus_widget import FocusWidget
from study_station.ui.theme import THEMES


class MainWindow(QMainWindow):
    """Full-screen application window hosting modern ambient, focus, and completion screens."""

    INDEX_CLOCK = 0
    INDEX_FOCUS = 1
    INDEX_COMPLETION = 2

    def __init__(self, engine: ScheduleEngine | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Study Station")
        self.resize(1366, 768)

        self._engine = engine
        self._settings = AppSettings()
        self._timer = FocusTimer()
        self._selected_subject: str | None = None

        self._apply_window_palette()

        # Screen Stack
        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)

        # 1. Modern Ambient Clock Screen
        self._clock_widget = AmbientClockWidget(self._settings, self)
        self._clock_widget.start_focus_requested.connect(self.start_focus_session)
        self._clock_widget.open_customization_requested.connect(self.open_customization_dialog)
        self._clock_widget.switch_subject_requested.connect(self.show_subject_selector)
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

    def _apply_window_palette(self) -> None:
        theme = THEMES.get(self._settings.theme_id, THEMES["noir"])
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, theme.bg_canvas)
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def toggle_fullscreen(self) -> None:
        """Toggle between Fullscreen and Normal window mode."""
        if self.isFullScreen():
            self.showNormal()
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.showFullScreen()

    def open_customization_dialog(self) -> None:
        """Open modern customization modal."""
        dialog = CustomizationDialog(self._settings, self)
        dialog.settings_changed.connect(self._on_settings_updated)
        dialog.exec()

    def _on_settings_updated(self, settings: AppSettings) -> None:
        self._settings = settings
        self._apply_window_palette()
        self._clock_widget.apply_settings(settings)

    def _update_progress_line(self) -> None:
        """Fetch updated ambient status line from ScheduleEngine."""
        if self._engine:
            if self._selected_subject:
                cycle = self._engine.get_active_cycle(self._selected_subject, datetime.now())
                short = self._engine._abbreviate_subject(self._selected_subject)
                if cycle:
                    text = f"{short} · {cycle.completed_minutes} / {cycle.target_minutes} MIN"
                else:
                    text = f"{short} · 0 / 60 MIN"
            else:
                text = self._engine.get_ambient_status_text(datetime.now())
            self._clock_widget.secondary_text = text

    def show_subject_selector(self) -> None:
        """Show clean popup menu to switch active study subject."""
        if not self._engine:
            return

        subjects = self._engine.get_distinct_subjects()
        if not subjects:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #161619;
                color: #F4F4F5;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 18px;
                border-radius: 4px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #27272A;
            }
        """)

        # Add auto recommendation option
        auto_action = menu.addAction("● Recommended (Auto)")
        auto_action.triggered.connect(lambda: self._set_selected_subject(None))
        menu.addSeparator()

        for s in subjects:
            clean = ScheduleEngine.clean_subject_name(s)
            action = menu.addAction(clean)
            action.triggered.connect(lambda checked=False, subj=s: self._set_selected_subject(subj))

        # Position menu above the progress pill
        rect = self.rect()
        pill_rect = self._clock_widget._get_pill_rect(rect)
        global_pos = self.mapToGlobal(pill_rect.topLeft())
        menu.exec(global_pos)

    def _set_selected_subject(self, subject_name: str | None) -> None:
        self._selected_subject = subject_name
        self._update_progress_line()

    def start_focus_session(self, duration_minutes: int = 15) -> None:
        """Low-friction start of a focus session for the chosen or suggested subject."""
        subject_name = "STUDY"
        cycle_info = ""

        if self._engine:
            if self._selected_subject:
                subject_name = self._selected_subject
            else:
                suggested = self._engine.get_suggested_cycle(datetime.now())
                if suggested:
                    subject_name = suggested.subject_name
                elif self._engine.sessions:
                    subject_name = self._engine.sessions[0].subject.name

            cycle = self._engine.get_active_cycle(subject_name, datetime.now())
            if cycle:
                cycle_info = f"{cycle.completed_minutes} / {cycle.target_minutes} MIN"

        self._focus_widget.start_session(subject_name, duration_minutes, cycle_info=cycle_info)
        self._stack.setCurrentIndex(self.INDEX_FOCUS)

    def _on_session_finished(self, subject_name: str, elapsed_minutes: int) -> None:
        """Handle focus session completion or manual finish."""
        if elapsed_minutes <= 0:
            self._show_clock_screen()
            return

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
            self.toggle_fullscreen()
            return

        # Screen-specific shortcuts
        if current_idx == self.INDEX_CLOCK:
            self._clock_widget.reveal_controls()

            if key == Qt.Key.Key_Escape:
                self.close()
            elif key == Qt.Key.Key_T:
                self._clock_widget.toggle_time_format()
            elif key == Qt.Key.Key_C:
                self.open_customization_dialog()
            elif key in (Qt.Key.Key_Space, Qt.Key.Key_Return):
                self.start_focus_session(self._settings.default_focus_minutes)
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
            elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal, Qt.Key.Key_5):
                self._timer.add_minutes(5)
                self._focus_widget._update_display()
            elif key in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
                self._focus_widget._on_end_clicked()
            else:
                super().keyPressEvent(event)

        elif current_idx == self.INDEX_COMPLETION:
            self._show_clock_screen()
        else:
            super().keyPressEvent(event)

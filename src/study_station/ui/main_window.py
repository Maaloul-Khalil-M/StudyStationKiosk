"""Main application window for Study Station.

Manages transitions between:
1. Subject-Centric Ambient Dashboard with Flip Clock & Quick Switcher
2. Focus Screen (countdown timer with visual progress and cycle tracking)
3. Completion Screen (progress confirmation)
4. Secondary dialogs: Timetable Editor, Review Targets, Manual Study Logger
"""

from datetime import datetime, timedelta
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession, StudyLog
from study_station.core.settings import AppSettings
from study_station.core.timer import FocusTimer
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.completion_widget import CompletionWidget
from study_station.ui.customization_dialog import CustomizationDialog
from study_station.ui.dashboard_widget import SubjectDashboardWidget
from study_station.ui.focus_widget import FocusWidget
from study_station.ui.manual_log_dialog import ManualLogDialog
from study_station.ui.targets_dialog import TargetsDialog
from study_station.ui.theme import GLOBAL_QSS, THEMES
from study_station.ui.timetable_dialog import TimetableDialog
from study_station.ui.weekly_schedule_dialog import WeeklyScheduleGridDialog


class MainWindow(QMainWindow):
    """Full-screen application window hosting ambient, focus, completion, and management screens."""

    INDEX_DASHBOARD = 0
    INDEX_FOCUS = 1
    INDEX_COMPLETION = 2

    def __init__(
        self,
        engine: ScheduleEngine | None = None,
        repository: StudyStationRepository | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Study Station")
        self.resize(1366, 768)

        self._repo = repository
        self._engine = engine
        self._settings = self._repo.load_settings() if self._repo else AppSettings()
        self._timer = FocusTimer()

        self._apply_window_palette()

        # Screen Stack
        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)

        # 1. Subject-Centric Dashboard Screen (Subject is Centerpiece)
        self._dashboard_widget = SubjectDashboardWidget(self._engine, self._settings, self)
        self._dashboard_widget.start_focus_requested.connect(self._on_start_focus_requested)
        self._dashboard_widget.open_settings_requested.connect(self.open_customization_dialog)
        self._dashboard_widget.open_timetable_requested.connect(self.open_timetable_editor)
        self._dashboard_widget.open_targets_requested.connect(self.open_targets_dialog)
        self._dashboard_widget.open_manual_log_requested.connect(self.open_manual_log_dialog)
        self._dashboard_widget.toggle_fullscreen_requested.connect(self.toggle_fullscreen)
        self._stack.addWidget(self._dashboard_widget)

        # 2. Focus Screen
        self._focus_widget = FocusWidget(self._timer, self)
        self._focus_widget.session_finished.connect(self._on_session_finished)
        self._stack.addWidget(self._focus_widget)

        # 3. Completion Screen
        self._completion_widget = CompletionWidget(self)
        self._completion_widget.dismissed.connect(self._show_dashboard_screen)
        self._stack.addWidget(self._completion_widget)

        # Default to Subject Dashboard screen
        self._stack.setCurrentIndex(self.INDEX_DASHBOARD)

        # Background status update timer (every 30 seconds)
        if self._engine:
            self._status_timer = QTimer(self)
            self._status_timer.setInterval(30_000)
            self._status_timer.timeout.connect(self._dashboard_widget.refresh_dashboard)
            self._status_timer.start()

        # Timer state synchronization (survives crashes / sleep)
        if self._repo:
            self._timer_sync_timer = QTimer(self)
            self._timer_sync_timer.setInterval(5000)
            self._timer_sync_timer.timeout.connect(self._sync_timer_state)
            self._timer_sync_timer.start()

            # Check for crash/sleep recovery on startup
            self._check_timer_recovery()

    def _sync_timer_state(self) -> None:
        """Persist active timer progress to SQLite for recovery safety."""
        if self._repo and self._timer.is_active:
            self._repo.save_timer_state(self._timer)

    def _check_timer_recovery(self) -> None:
        """Recover timer state if application restarted or PC woke from sleep."""
        if not self._repo:
            return

        recovered = self._repo.recover_timer_state()
        if not recovered:
            return

        subject_name, sec_or_min, total_duration = recovered
        if total_duration is None:
            # Session completed while machine was suspended or app was closed!
            self._on_session_finished(subject_name, sec_or_min)
        else:
            # Resume active focus session
            self._timer.start(subject_name, total_duration)
            self._timer.target_end_time = datetime.now() + timedelta(seconds=sec_or_min)
            cycle_info = ""
            if self._engine:
                cycle = self._engine.get_active_cycle(subject_name, datetime.now())
                if cycle:
                    cycle_info = f"{cycle.completed_minutes} / {cycle.target_minutes} MIN"
            self._focus_widget.start_session(subject_name, total_duration, cycle_info=cycle_info)
            self._stack.setCurrentIndex(self.INDEX_FOCUS)

    def _apply_window_palette(self) -> None:
        theme = THEMES.get(self._settings.theme_id, THEMES["noir"])
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, theme.bg_canvas)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setStyleSheet(GLOBAL_QSS)

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
        dialog.open_timetable_requested.connect(self.open_timetable_editor)
        dialog.open_targets_requested.connect(self.open_targets_dialog)
        dialog.open_manual_log_requested.connect(self.open_manual_log_dialog)
        dialog.exec()

    def _on_settings_updated(self, settings: AppSettings) -> None:
        self._settings = settings
        if self._repo:
            self._repo.save_settings(settings)
        self._apply_window_palette()
        self._dashboard_widget.apply_settings(settings)

    # -------------------------------------------------------------------------
    # Secondary Management Dialogs
    # -------------------------------------------------------------------------

    def open_timetable_editor(self) -> None:
        """Open weekly timetable (defaults to visual Weekly Schedule Grid)."""
        sessions = self._engine.sessions if self._engine else []
        dialog = WeeklyScheduleGridDialog(
            sessions=sessions,
            current_subject=self._dashboard_widget.selected_subject,
            parent=self,
        )
        dialog.subject_selected.connect(self._dashboard_widget.set_selected_subject)
        dialog.edit_timetable_requested.connect(self.open_timetable_form_editor)
        dialog.exec()

    def open_timetable_form_editor(self) -> None:
        """Open raw tabular timetable editor dialog."""
        sessions = self._engine.sessions if self._engine else []
        dialog = TimetableDialog(sessions, self)
        dialog.timetable_changed.connect(self._on_timetable_updated)
        dialog.exec()

    def _on_timetable_updated(self, sessions: list[AcademicSession]) -> None:
        if self._engine:
            self._engine.sessions = list(sessions)
        if self._repo:
            self._repo.save_timetable_sessions(sessions)
        self._dashboard_widget.refresh_dashboard()

    def open_targets_dialog(self, default_subject: str | None = None) -> None:
        """Open subject review targets configuration dialog."""
        subjects = self._engine.get_distinct_subjects() if self._engine else []
        current_targets = self._repo.get_all_subject_targets() if self._repo else {}
        target_subject = default_subject or self._dashboard_widget.selected_subject
        dialog = TargetsDialog(
            subjects,
            current_targets,
            default_subject=target_subject,
            parent=self,
        )
        dialog.targets_saved.connect(self._on_targets_updated)
        dialog.exec()

    def _on_targets_updated(self, targets: dict[str, int]) -> None:
        if self._engine:
            for subj, target in targets.items():
                self._engine.set_subject_target(subj, target)
        self._dashboard_widget.refresh_dashboard()

    def open_manual_log_dialog(self, default_subject: str | None = None) -> None:
        """Open manual study time entry dialog for offline study."""
        subjects = self._engine.get_distinct_subjects() if self._engine else []
        target_subject = default_subject or self._dashboard_widget.selected_subject
        dialog = ManualLogDialog(subjects, default_subject=target_subject, parent=self)
        dialog.time_logged.connect(self._on_manual_time_logged)
        dialog.exec()

    def _on_manual_time_logged(self, subject_name: str, minutes: int) -> None:
        """Handle manual time entry logged away from the computer."""
        self._on_session_finished(subject_name, minutes)

    # -------------------------------------------------------------------------
    # Progress & Flow
    # -------------------------------------------------------------------------

    def _on_start_focus_requested(self, subject_name: str, duration_minutes: int) -> None:
        self.start_focus_session(duration_minutes=duration_minutes, subject_name=subject_name)

    def start_focus_session(
        self,
        duration_minutes: int = 15,
        subject_name: str | None = None,
    ) -> None:
        """Low-friction start of a focus session for the chosen or suggested subject."""
        target_name = subject_name or self._dashboard_widget.selected_subject or "STUDY"
        cycle_info = ""

        if self._engine:
            if not subject_name and not self._dashboard_widget.selected_subject:
                suggested = self._engine.get_suggested_cycle(datetime.now())
                if suggested:
                    target_name = suggested.subject_name
                elif self._engine.sessions:
                    target_name = self._engine.sessions[0].subject.name

            cycle = self._engine.get_active_cycle(target_name, datetime.now())
            if cycle:
                cycle_info = f"{cycle.completed_minutes} / {cycle.target_minutes} MIN"

        self._focus_widget.start_session(target_name, duration_minutes, cycle_info=cycle_info)
        if self._repo:
            self._repo.save_timer_state(self._timer)

        self._stack.setCurrentIndex(self.INDEX_FOCUS)

    def _on_session_finished(self, subject_name: str, elapsed_minutes: int) -> None:
        """Handle focus session completion or manual finish."""
        if self._repo:
            self._repo.clear_timer_state()

        if elapsed_minutes <= 0:
            self._show_dashboard_screen()
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

            self._dashboard_widget.refresh_dashboard()

        self._completion_widget.show_completion(
            subject_name=subject_name,
            added_minutes=elapsed_minutes,
            completed_minutes=completed,
            target_minutes=target,
        )
        self._stack.setCurrentIndex(self.INDEX_COMPLETION)

    def _show_dashboard_screen(self) -> None:
        """Return to Subject Dashboard."""
        self._dashboard_widget.refresh_dashboard()
        self._stack.setCurrentIndex(self.INDEX_DASHBOARD)

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
        if current_idx == self.INDEX_DASHBOARD:
            if key == Qt.Key.Key_Escape:
                self.close()
            elif key == Qt.Key.Key_C:
                self.open_customization_dialog()
            elif key == Qt.Key.Key_E:
                self.open_timetable_editor()
            elif key == Qt.Key.Key_S:
                self.open_targets_dialog()
            elif key == Qt.Key.Key_M:
                self.open_manual_log_dialog()
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
                if self._repo:
                    self._repo.save_timer_state(self._timer)
            elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal, Qt.Key.Key_5):
                self._timer.add_minutes(5)
                self._focus_widget._update_display()
                if self._repo:
                    self._repo.save_timer_state(self._timer)
            elif key in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
                self._focus_widget._on_end_clicked()
            else:
                super().keyPressEvent(event)

        elif current_idx == self.INDEX_COMPLETION:
            self._show_dashboard_screen()
        else:
            super().keyPressEvent(event)

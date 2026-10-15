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
from PySide6.QtWidgets import QDialog, QMainWindow, QStackedWidget

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    ExitTicketResult,
    StudyLog,
    StudyTodo,
)
from study_station.core.settings import AppSettings
from study_station.core.timer import FocusTimer
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.completion_widget import CompletionWidget
from study_station.ui.customization_dialog import CustomizationDialog
from study_station.ui.dashboard_widget import SubjectDashboardWidget
from study_station.ui.debrief_dialog import DebriefDialog
from study_station.ui.exit_ticket_dialog import ExitTicketDialog
from study_station.ui.focus_widget import FocusWidget
from study_station.ui.history_dialog import HistoryDialog
from study_station.ui.import_export_dialog import ImportExportDialog
from study_station.ui.manual_log_dialog import ManualLogDialog
from study_station.ui.schedule_screen_widget import ScheduleScreenWidget
from study_station.ui.targets_dialog import TargetsDialog
from study_station.ui.tasks_dialog import TasksDialog
from study_station.ui.theme import GLOBAL_QSS, THEMES
from study_station.ui.timetable_dialog import TimetableDialog
from study_station.ui.weekly_schedule_dialog import WeeklyScheduleGridDialog


class MainWindow(QMainWindow):
    """Full-screen application window hosting ambient, focus, completion, and management screens."""

    INDEX_GRID = 0
    INDEX_DASHBOARD = 0  # Primary Cockpit Grid
    INDEX_FOCUS = 1
    INDEX_COMPLETION = 2
    INDEX_AMBIENT_CLOCK = 3
    INDEX_SCHEDULE = 0   # Alias for backward compatibility

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
        self._prompt_exit_ticket = True

        self._apply_window_palette()

        # Screen Stack
        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)

        # 1. Primary Cockpit Screen: Full-Screen Weekly Schedule & Task Badges
        sessions = self._engine.sessions if self._engine else []
        self._schedule_widget = ScheduleScreenWidget(sessions=sessions, parent=self, engine=self._engine)
        self._schedule_widget.ambient_requested.connect(self._show_ambient_clock)
        self._schedule_widget.open_debrief_requested.connect(self.open_debrief_dialog)
        self._schedule_widget.start_focus_requested.connect(self._on_start_focus_requested)
        self._schedule_widget.start_todo_focus_requested.connect(self._on_start_todo_focus)
        self._schedule_widget.timetable_changed.connect(self._on_timetable_updated)
        self._schedule_widget.open_import_export_requested.connect(self.open_import_export_dialog)
        self._schedule_widget.open_tasks_requested.connect(self.open_tasks_dialog)
        self._stack.addWidget(self._schedule_widget)

        # 2. Focus Screen
        self._focus_widget = FocusWidget(self._timer, self)
        self._focus_widget.apply_settings(self._settings)
        self._focus_widget.session_finished.connect(self.prompt_exit_ticket_and_finish)
        self._stack.addWidget(self._focus_widget)

        # 3. Completion Screen
        self._completion_widget = CompletionWidget(self)
        self._completion_widget.dismissed.connect(self._show_cockpit_screen)
        self._stack.addWidget(self._completion_widget)

        # 4. Secondary Screen: Ambient Split-Flap Clock & Quick Switcher
        self._dashboard_widget = SubjectDashboardWidget(self._engine, self._settings, self)
        self._dashboard_widget.start_focus_requested.connect(self._on_start_focus_requested)
        self._dashboard_widget.open_settings_requested.connect(self.open_customization_dialog)
        self._dashboard_widget.open_timetable_requested.connect(self.open_timetable_editor)
        self._dashboard_widget.open_targets_requested.connect(self.open_targets_dialog)
        self._dashboard_widget.open_manual_log_requested.connect(self.open_manual_log_dialog)
        self._dashboard_widget.open_history_requested.connect(self.open_history_dialog)
        self._dashboard_widget.open_debrief_requested.connect(self.open_debrief_dialog)
        self._dashboard_widget.open_tasks_requested.connect(self.open_tasks_dialog)
        self._dashboard_widget.toggle_fullscreen_requested.connect(self.toggle_fullscreen)
        self._stack.addWidget(self._dashboard_widget)

        # Scrim Overlay for dialogs (prevents main screen background text leakage)
        from PySide6.QtWidgets import QFrame
        self._scrim_overlay = QFrame(self)
        self._scrim_overlay.setObjectName("scrimOverlay")
        self._scrim_overlay.setStyleSheet("QFrame#scrimOverlay { background-color: rgba(9, 9, 11, 0.96); border: none; }")
        self._scrim_overlay.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._scrim_overlay.hide()

        # Default to Weekly Schedule Cockpit screen
        self._stack.setCurrentIndex(self.INDEX_GRID)

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
        bg_hex = getattr(self._settings, "bg_color", "") or "#09090B"
        bg_color = QColor(bg_hex)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, bg_color)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setStyleSheet(f"QMainWindow {{ background-color: {bg_hex}; }} {GLOBAL_QSS}")
        if hasattr(self, "_scrim_overlay"):
            self._scrim_overlay.setStyleSheet(f"QFrame#scrimOverlay {{ background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 0.96); border: none; }}")

    def toggle_fullscreen(self) -> None:
        """Toggle between Fullscreen and Normal window mode."""
        if self.isFullScreen():
            self.showNormal()
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.showFullScreen()

    def _show_scrim(self) -> None:
        self._scrim_overlay.setGeometry(self.rect())
        self._scrim_overlay.raise_()
        self._scrim_overlay.show()

    def _hide_scrim(self) -> None:
        self._scrim_overlay.hide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_scrim_overlay"):
            self._scrim_overlay.setGeometry(self.rect())

    def open_customization_dialog(self) -> None:
        """Open modern customization modal with dark backdrop scrim."""
        self._show_scrim()
        try:
            dialog = CustomizationDialog(self._settings, self)
            dialog.settings_changed.connect(self._on_settings_updated)
            dialog.open_timetable_requested.connect(self.open_timetable_editor)
            dialog.open_targets_requested.connect(self.open_targets_dialog)
            dialog.open_manual_log_requested.connect(self.open_manual_log_dialog)
            dialog.open_import_export_requested.connect(self.open_import_export_dialog)
            dialog.exec()
        finally:
            self._hide_scrim()

    def _on_settings_updated(self, settings: AppSettings) -> None:
        self._settings = settings
        if self._repo:
            self._repo.save_settings(settings)
        self._apply_window_palette()
        self._dashboard_widget.apply_settings(settings)
        self._focus_widget.apply_settings(settings)
        if hasattr(self, "_schedule_widget"):
            self._schedule_widget.apply_settings(settings)

    # -------------------------------------------------------------------------
    # Secondary Management Dialogs & Full-Screen Views
    # -------------------------------------------------------------------------

    def _show_ambient_clock(self) -> None:
        """Switch to ambient split-flap clock screensaver mode."""
        self._dashboard_widget.refresh_dashboard()
        self._stack.setCurrentIndex(self.INDEX_AMBIENT_CLOCK)

    def _show_cockpit_screen(self) -> None:
        """Return to primary Weekly Schedule Cockpit screen."""
        if self._engine:
            self._schedule_widget.update_sessions(self._engine.sessions)
        self._stack.setCurrentIndex(self.INDEX_GRID)

    def _show_dashboard_screen(self) -> None:
        """Alias for returning to main station screen."""
        self._show_cockpit_screen()

    def open_timetable_editor(self) -> None:
        """Switch to full-screen Weekly Schedule and Class Cockpit view."""
        self._show_cockpit_screen()

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
        self._schedule_widget.update_sessions(sessions)

    def open_targets_dialog(self, default_subject: str | None = None) -> None:
        """Open subject review targets configuration dialog with dark scrim."""
        self._show_scrim()
        try:
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
        finally:
            self._hide_scrim()

    def _on_targets_updated(self, targets: dict[str, int]) -> None:
        if self._engine:
            for subj, target in targets.items():
                self._engine.set_subject_target(subj, target)
        self._dashboard_widget.refresh_dashboard()

    def open_manual_log_dialog(self, default_subject: str | None = None) -> None:
        """Open manual study time entry dialog with dark scrim."""
        self._show_scrim()
        try:
            subjects = self._engine.get_distinct_subjects() if self._engine else []
            target_subject = default_subject or self._dashboard_widget.selected_subject
            dialog = ManualLogDialog(subjects, default_subject=target_subject, parent=self)
            dialog.time_logged.connect(self._on_manual_time_logged)
            dialog.exec()
        finally:
            self._hide_scrim()

    def open_history_dialog(self) -> None:
        """Open Study History & Cycle Statistics dialog with dark scrim."""
        if not self._engine:
            return
        self._show_scrim()
        try:
            dialog = HistoryDialog(self._engine, parent=self)
            dialog.history_changed.connect(self._dashboard_widget.refresh_dashboard)
            dialog.exec()
        finally:
            self._hide_scrim()

    def open_import_export_dialog(self) -> None:
        """Open Timetable Import / Export modal dialog with dark scrim."""
        if not self._engine:
            return
        self._show_scrim()
        try:
            dialog = ImportExportDialog(self.engine if hasattr(self, "engine") else self._engine, parent=self)
            dialog.timetable_imported.connect(self._on_timetable_updated)
            dialog.exec()
        finally:
            self._hide_scrim()

    def open_debrief_dialog(self, ref_dt: datetime | None = None) -> None:
        """Open Nightly Desk Debrief questionnaire dialog with dark scrim."""
        if not self._engine:
            return
        self._show_scrim()
        try:
            dialog = DebriefDialog(self._engine, ref_dt=ref_dt, parent=self)
            def _on_debrief_done(todos):
                self._dashboard_widget.refresh_dashboard()
                self._schedule_widget.update_sessions(self._engine.sessions)
            dialog.debrief_completed.connect(_on_debrief_done)
            dialog.exec()
        finally:
            self._hide_scrim()

    def open_tasks_dialog(self) -> None:
        """Open Academic Task Backlog dialog with dark scrim."""
        if not self._engine:
            return
        self._show_scrim()
        try:
            dialog = TasksDialog(self._engine, parent=self)
            dialog.start_task_focus_requested.connect(self._on_start_todo_focus)
            def _on_tasks_changed():
                self._dashboard_widget.refresh_dashboard()
                self._schedule_widget.update_sessions(self._engine.sessions)
            dialog.tasks_changed.connect(_on_tasks_changed)
            dialog.exec()
            self._dashboard_widget.refresh_dashboard()
            self._schedule_widget.update_sessions(self._engine.sessions)
        finally:
            self._hide_scrim()

    def _on_manual_time_logged(self, subject_name: str, minutes: int) -> None:
        """Handle manual time entry logged away from the computer."""
        self._on_session_finished(subject_name, minutes, source="manual")

    # -------------------------------------------------------------------------
    # Progress & Flow
    # -------------------------------------------------------------------------

    def _on_start_focus_requested(self, subject_name: str, duration_minutes: int) -> None:
        self.start_focus_session(duration_minutes=duration_minutes, subject_name=subject_name)

    def _on_start_todo_focus(self, todo: StudyTodo, duration_minutes: int = 15) -> None:
        """Handle 1-click focus session initiated for a specific StudyTodo task."""
        self.start_focus_session(duration_minutes=duration_minutes, subject_name=todo.subject_name, todo=todo)

    def start_focus_session(
        self,
        duration_minutes: int = 15,
        subject_name: str | None = None,
        todo: StudyTodo | None = None,
    ) -> None:
        """Low-friction start of a focus session for the chosen or suggested subject."""
        self._active_todo = todo
        target_name = subject_name or (todo.subject_name if todo else None) or self._dashboard_widget.selected_subject or "STUDY"
        cycle_info = ""

        if self._engine:
            if not subject_name and not todo and not self._dashboard_widget.selected_subject:
                suggested = self._engine.get_suggested_cycle(datetime.now())
                if suggested:
                    target_name = suggested.subject_name
                elif self._engine.sessions:
                    target_name = self._engine.sessions[0].subject.name

            cycle = self._engine.get_active_cycle(target_name, datetime.now())
            if cycle:
                cycle_info = f"{cycle.completed_minutes} / {cycle.target_minutes} MIN"

        self._focus_widget.start_session(target_name, duration_minutes, cycle_info=cycle_info, todo=todo)
        if self._repo:
            self._repo.save_timer_state(self._timer)

        self._stack.setCurrentIndex(self.INDEX_FOCUS)

    def prompt_exit_ticket_and_finish(self, subject_name: str, elapsed_minutes: int) -> None:
        """Prompt student with the Cognitive Exit Ticket and process completion."""
        exit_result: ExitTicketResult | None = None
        if self._prompt_exit_ticket and elapsed_minutes > 0:
            exit_result = self.open_exit_ticket_dialog(
                subject_name=subject_name,
                elapsed_minutes=elapsed_minutes,
                todo=getattr(self, "_active_todo", None),
            )
        self._on_session_finished(
            subject_name=subject_name,
            elapsed_minutes=elapsed_minutes,
            source="timer",
            exit_result=exit_result,
        )

    def open_exit_ticket_dialog(
        self,
        subject_name: str,
        elapsed_minutes: int,
        todo: StudyTodo | None = None,
    ) -> ExitTicketResult | None:
        """Open Cognitive Exit Ticket modal with dark scrim overlay."""
        self._show_scrim()
        try:
            ticket_dialog = ExitTicketDialog(
                subject_name=subject_name,
                elapsed_minutes=elapsed_minutes,
                todo=todo,
                parent=self,
            )
            res = ticket_dialog.exec()
            if res == QDialog.DialogCode.Accepted:
                return ticket_dialog.result
            return ticket_dialog.result or ExitTicketResult()
        finally:
            self._hide_scrim()

    def _on_session_finished(
        self,
        subject_name: str,
        elapsed_minutes: int,
        source: str = "timer",
        exit_result: ExitTicketResult | None = None,
    ) -> None:
        """Handle focus session completion or manual finish."""
        if self._repo:
            self._repo.clear_timer_state()

        if elapsed_minutes <= 0:
            self._show_cockpit_screen()
            return

        # Handle "extend" action -> log current minutes, then immediately launch continuation sprint
        if exit_result and exit_result.action == "extend":
            todo_id = self._active_todo.id if getattr(self, "_active_todo", None) else None
            if self._engine:
                self._engine.add_study_log(
                    StudyLog(
                        subject_name=subject_name,
                        started_at=datetime.now(),
                        duration_minutes=elapsed_minutes,
                        source=source,
                        todo_id=todo_id,
                    )
                )
            self.start_focus_session(
                duration_minutes=exit_result.extend_minutes,
                subject_name=subject_name,
                todo=self._active_todo,
            )
            return

        # Handle "complete" vs "put_aside" action -> update engine and persistence
        task_confidence = "solid"
        if exit_result:
            task_confidence = exit_result.confidence
            if self._engine:
                active_todo = getattr(self, "_active_todo", None)
                if active_todo is not None:
                    note = exit_result.takeaway_note.strip()
                    if note:
                        if active_todo.notes:
                            active_todo.notes = f"{active_todo.notes} · {note}"
                        else:
                            active_todo.notes = note
                        self._engine.update_todo(active_todo)

                    if exit_result.action == "complete":
                        self._engine.mark_todo_completed(
                            active_todo.id,
                            confidence=exit_result.confidence,
                            next_class_question=exit_result.next_class_question.strip(),
                        )
                    else:  # put_aside
                        active_todo.confidence = exit_result.confidence
                        if exit_result.next_class_question.strip():
                            active_todo.next_class_question = exit_result.next_class_question.strip()
                        self._engine.update_todo(active_todo)
                elif exit_result.next_class_question.strip() or exit_result.takeaway_note.strip():
                    auto_todo = StudyTodo(
                        subject_name=subject_name,
                        title=f"Review: {subject_name}",
                        notes=exit_result.takeaway_note.strip(),
                        confidence=exit_result.confidence,
                        next_class_question=exit_result.next_class_question.strip(),
                        status="completed",
                    )
                    self._engine.add_todo(auto_todo)

        target = 60
        completed = elapsed_minutes
        if self._engine:
            todo_id = self._active_todo.id if getattr(self, "_active_todo", None) else None
            self._engine.add_study_log(
                StudyLog(
                    subject_name=subject_name,
                    started_at=datetime.now(),
                    duration_minutes=elapsed_minutes,
                    source=source,
                    todo_id=todo_id,
                )
            )
            cycle = self._engine.get_active_cycle(subject_name, datetime.now())
            if cycle:
                completed = cycle.completed_minutes
                target = cycle.target_minutes

            self._dashboard_widget.refresh_dashboard()
            self._schedule_widget.update_sessions(self._engine.sessions)

        task_title = self._active_todo.title if getattr(self, "_active_todo", None) else None
        self._completion_widget.show_completion(
            subject_name=subject_name,
            added_minutes=elapsed_minutes,
            completed_minutes=completed,
            target_minutes=target,
            task_title=task_title,
            confidence=task_confidence,
        )

        # Milestone 8: Play calm acoustic completion chime
        if source == "timer" and getattr(self._settings, "sound_enabled", True):
            from study_station.core.sound_manager import SoundManager
            SoundManager.get_instance().play_completion_chime(enabled=True)

        self._stack.setCurrentIndex(self.INDEX_COMPLETION)

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
        if current_idx == self.INDEX_GRID:
            if key == Qt.Key.Key_Escape:
                self.close()
            elif key in (Qt.Key.Key_C, Qt.Key.Key_A):
                self._show_ambient_clock()
            elif key == Qt.Key.Key_D:
                self.open_debrief_dialog()
            elif key == Qt.Key.Key_E:
                self.open_timetable_editor()
            elif key == Qt.Key.Key_I:
                self.open_import_export_dialog()
            elif key == Qt.Key.Key_S:
                self.open_targets_dialog()
            elif key == Qt.Key.Key_M:
                self.open_manual_log_dialog()
            elif key == Qt.Key.Key_H:
                self.open_history_dialog()
            elif key == Qt.Key.Key_T:
                self.open_tasks_dialog()
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
            self._show_cockpit_screen()

        elif current_idx == self.INDEX_AMBIENT_CLOCK:
            if key in (Qt.Key.Key_Escape, Qt.Key.Key_G):
                self._show_cockpit_screen()
            elif key == Qt.Key.Key_C:
                self.open_customization_dialog()
            elif key == Qt.Key.Key_E:
                self.open_timetable_editor()
            elif key == Qt.Key.Key_S:
                self.open_targets_dialog()
            elif key == Qt.Key.Key_M:
                self.open_manual_log_dialog()
            elif key == Qt.Key.Key_H:
                self.open_history_dialog()
            elif key == Qt.Key.Key_D:
                self.open_debrief_dialog()
            elif key == Qt.Key.Key_I:
                self.open_import_export_dialog()
            elif key == Qt.Key.Key_T:
                self.open_tasks_dialog()
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
        else:
            super().keyPressEvent(event)

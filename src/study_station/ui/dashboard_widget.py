"""Subject-Centric Ambient Kiosk Dashboard Widget for Study Station.

Implements the Dieter Rams / Teenage Engineering minimalist appliance philosophy:
- Medium split-flap mechanical flip clock
- Giant bold Swiss typography subject name
- Single-line rotating info carousel with hairline progress bar
- Zero clutter in idle mode (all buttons and navigation hide after inactivity and reveal on hover)
- Subject switching via interactive Weekly Schedule Grid (Google Calendar / grid.pdf model)
"""

from __future__ import annotations
from datetime import datetime, timedelta
from PySide6.QtCore import QEvent, QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import SubjectSummary
from study_station.core.settings import AppSettings
from study_station.ui.split_flap_clock import SplitFlapClockWidget
from study_station.ui.theme import (
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class SubjectDashboardWidget(QWidget):
    """Primary Ambient Kiosk Screen & Study Sprint Launchpad of Study Station."""

    start_focus_requested = Signal(str, int)  # (subject_name, duration_minutes)
    start_todo_focus_requested = Signal(object, int)  # (todo, duration_minutes)
    open_settings_requested = Signal()
    open_timetable_requested = Signal()
    open_targets_requested = Signal(str)  # subject_name
    open_manual_log_requested = Signal(str)  # subject_name
    open_history_requested = Signal()
    open_debrief_requested = Signal()
    open_tasks_requested = Signal()
    toggle_fullscreen_requested = Signal()
    open_switch_user_requested = Signal()

    def __init__(
        self,
        engine: ScheduleEngine | None = None,
        settings: AppSettings | None = None,
        parent: QWidget | None = None,
        current_user: str = "Default",
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.settings = settings or AppSettings()
        self.current_user = current_user
        self.selected_subject: str | None = None
        self.active_todo = None

        self._chip_buttons: dict[str | None, QPushButton] = {}
        self._carousel_index = 0
        self._carousel_slides: list[str] = []
        self._is_interactive = False

        self._init_ui()

        # Inactivity timer for auto-hiding interactive controls (3.5s)
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setInterval(3500)
        self._inactivity_timer.timeout.connect(self._on_inactivity_timeout)

        # Carousel rotation timer (7s per slide)
        self._carousel_timer = QTimer(self)
        self._carousel_timer.setInterval(7000)
        self._carousel_timer.timeout.connect(self._rotate_carousel)
        self._carousel_timer.start()

        # Periodic refresh timer (30s) to keep live date and class statuses updated
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(30000)
        self._refresh_timer.timeout.connect(lambda: self.refresh_dashboard())
        self._refresh_timer.start()

        # Install application event filter to detect mouse interaction
        QApplication.instance().installEventFilter(self)

        # Start in idle glance mode
        self._set_interactive_mode(False)

    def _init_ui(self) -> None:
        self.setMouseTracking(True)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 20, 32, 24)
        main_layout.setSpacing(0)

        # ---------------------------------------------------------------------
        # 1. Top Bar (Auto-hides in idle mode)
        # ---------------------------------------------------------------------
        self.top_bar = self._create_top_bar()
        main_layout.addWidget(self.top_bar)

        main_layout.addStretch(1)

        # ---------------------------------------------------------------------
        # 2. Stylish Date Badge (Directly above flip clock)
        # ---------------------------------------------------------------------
        self.lbl_date = QLabel(self)
        self.lbl_date.setObjectName("lblDashboardDate")
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_date.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_date.setToolTip("Click to open schedule")
        self.lbl_date.mousePressEvent = lambda e: self.open_timetable_requested.emit()
        main_layout.addWidget(self.lbl_date, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(14)

        # ---------------------------------------------------------------------
        # 3. Medium Mechanical Flip Clock
        # ---------------------------------------------------------------------
        self.clock_widget = SplitFlapClockWidget(self.settings, self)
        main_layout.addWidget(self.clock_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(20)

        # ---------------------------------------------------------------------
        # 3. Mission Hub: Task Kicker, Task Headline, Subject Name
        # ---------------------------------------------------------------------
        mission_container = QWidget(self)
        mission_container.setFixedWidth(740)
        mission_layout = QVBoxLayout(mission_container)
        mission_layout.setContentsMargins(0, 0, 0, 0)
        mission_layout.setSpacing(6)
        mission_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Task urgency kicker pill badge
        self.lbl_task_kicker = QLabel("🎯 ACTIVE STUDY SPRINT")
        self.lbl_task_kicker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_task_kicker.setStyleSheet("""
            QLabel {
                background-color: #18181B;
                color: #71717A;
                border: 1px solid #27272A;
                border-radius: 11px;
                padding: 3px 12px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }
        """)
        mission_layout.addWidget(self.lbl_task_kicker, alignment=Qt.AlignmentFlag.AlignCenter)

        # Actionable task verb headline
        self.lbl_task_title = QLabel("Preparation & Practice Sprint")
        self.lbl_task_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_task_title.setWordWrap(True)
        self.lbl_task_title.setFixedWidth(740)
        self.lbl_task_title.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_task_title.mousePressEvent = lambda e: self.open_tasks_requested.emit()
        mission_layout.addWidget(self.lbl_task_title)

        # Subject / Module context & hint
        self.lbl_subject_name = QLabel("LOADING...")
        self.lbl_subject_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subject_name.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_subject_name.mousePressEvent = lambda e: self.open_timetable_requested.emit()
        mission_layout.addWidget(self.lbl_subject_name)

        self.lbl_subject_hint = QLabel("▾ Click to open schedule")
        self.lbl_subject_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mission_layout.addWidget(self.lbl_subject_hint)

        main_layout.addWidget(mission_container, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(14)

        # ---------------------------------------------------------------------
        # 4. Single-Line Info Carousel
        # ---------------------------------------------------------------------
        carousel_container = QWidget(self)
        carousel_container.setMaximumWidth(680)
        carousel_layout = QVBoxLayout(carousel_container)
        carousel_layout.setContentsMargins(0, 0, 0, 0)
        carousel_layout.setSpacing(8)

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        self.btn_prev_carousel = QPushButton("‹")
        self.btn_prev_carousel.setFixedSize(28, 28)
        self.btn_prev_carousel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev_carousel.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #71717A;
                border: 1px solid #27272A;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #27272A;
                color: #FFFFFF;
            }
        """)
        self.btn_prev_carousel.clicked.connect(self._prev_carousel)
        row_layout.addWidget(self.btn_prev_carousel)

        self.lbl_carousel_text = QLabel("")
        self.lbl_carousel_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_carousel_text.setStyleSheet("""
            color: #A1A1AA;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        row_layout.addWidget(self.lbl_carousel_text, stretch=1)

        self.btn_next_carousel = QPushButton("›")
        self.btn_next_carousel.setFixedSize(28, 28)
        self.btn_next_carousel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next_carousel.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #71717A;
                border: 1px solid #27272A;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #27272A;
                color: #FFFFFF;
            }
        """)
        self.btn_next_carousel.clicked.connect(self._next_carousel)
        row_layout.addWidget(self.btn_next_carousel)

        carousel_layout.addLayout(row_layout)

        # Hairline progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1C1C22;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 2px;
            }
        """)
        carousel_layout.addWidget(self.progress_bar)

        main_layout.addWidget(carousel_container, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(24)

        # ---------------------------------------------------------------------
        # 5. Tactile Focus Action Buttons (Auto-hides in idle mode)
        # ---------------------------------------------------------------------
        self.action_container = QWidget(self)
        action_layout = QHBoxLayout(self.action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(12)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Primary Start Focus Button
        self.btn_focus_15 = QPushButton("▶ START 15m SPRINT")
        self.btn_focus_15.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_focus_15.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_focus_15.setToolTip("Launch a 15-minute high-focus sprint on this mission")
        self.btn_focus_15.clicked.connect(lambda: self._on_start_focus(15))
        action_layout.addWidget(self.btn_focus_15)

        # 25m Focus Button
        self.btn_focus_25 = QPushButton("25m POMODORO")
        self.btn_focus_25.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_focus_25.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_focus_25.setToolTip("Launch a 25-minute Pomodoro study block")
        self.btn_focus_25.clicked.connect(lambda: self._on_start_focus(25))
        action_layout.addWidget(self.btn_focus_25)

        # Quick Backlog Button
        self.btn_quick_tasks = QPushButton("TASKS")
        self.btn_quick_tasks.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_quick_tasks.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quick_tasks.setToolTip("Open Academic Task Backlog to select or manage tasks")
        self.btn_quick_tasks.clicked.connect(self.open_tasks_requested.emit)
        action_layout.addWidget(self.btn_quick_tasks)

        # Backwards compatibility triggers (accessible via top bar)
        self.btn_hero_log = QPushButton(self)
        self.btn_hero_log.hide()
        self.btn_hero_log.clicked.connect(lambda: self.open_manual_log_requested.emit(self.selected_subject or ""))

        self.btn_hero_target = QPushButton(self)
        self.btn_hero_target.hide()
        self.btn_hero_target.clicked.connect(lambda: self.open_targets_requested.emit(self.selected_subject or ""))

        main_layout.addWidget(self.action_container)

        main_layout.addStretch(1)

        # ---------------------------------------------------------------------
        # 6. Ambient Today's Timeline Strip (Removed from display per user request)
        # ---------------------------------------------------------------------
        self.timeline_strip = self._create_timeline_strip()
        self.timeline_strip.hide()

        # Hidden backwards-compatibility widgets for unit tests
        self.lbl_status_badge = QLabel(self)
        self.lbl_status_badge.hide()
        self.lbl_cycle_progress = QLabel(self)
        self.lbl_cycle_progress.hide()

        self._update_typography()
        self.refresh_dashboard()

    def _update_typography(self) -> None:
        """Apply either Evangelion Matisse display serif or Swiss Modern Minimal."""
        is_eva = getattr(self.settings, "typography_style", "eva") == "eva"
        accent = getattr(self.settings, "accent_color", "") or ("#FF7700" if is_eva else "#10B981")
        if is_eva:
            # Matisse EB inspired editorial display serif with tight tracking
            self.lbl_task_title.setFont(get_modern_font("sans", 22, QFont.Weight.Bold))
            self.lbl_task_title.setStyleSheet(f"""
                QLabel {{
                    color: #FFFFFF;
                    font-size: 22px;
                    font-weight: 700;
                    letter-spacing: -0.2px;
                }}
                QLabel:hover {{
                    color: {accent};
                }}
            """)
            self.lbl_subject_name.setFont(get_modern_font("eva_body", 13, QFont.Weight.Bold))
            self.lbl_subject_name.setStyleSheet(f"""
                QLabel {{
                    color: #A1A1AA;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 1.2px;
                }}
                QLabel:hover {{
                    color: #FFFFFF;
                }}
            """)
            self.lbl_subject_hint.setText("Click to open schedule")
            self.lbl_subject_hint.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 500; letter-spacing: 0.3px;")
            self.btn_focus_15.setText("▶ START 15m SPRINT")
            self.btn_focus_25.setText("25m POMODORO")
        else:
            self.lbl_task_title.setFont(get_modern_font("sans", 22, QFont.Weight.Bold))
            self.lbl_task_title.setStyleSheet(f"""
                QLabel {{
                    color: #FFFFFF;
                    font-size: 22px;
                    font-weight: 700;
                    letter-spacing: -0.2px;
                }}
                QLabel:hover {{
                    color: {accent};
                }}
            """)
            self.lbl_subject_name.setFont(get_modern_font("sans", 13, QFont.Weight.Bold))
            self.lbl_subject_name.setStyleSheet(f"""
                QLabel {{
                    color: #A1A1AA;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 1.2px;
                }}
                QLabel:hover {{
                    color: #FFFFFF;
                }}
            """)
            self.lbl_subject_hint.setText("Click to open schedule")
            self.lbl_subject_hint.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 500; letter-spacing: 0.3px;")
            self.btn_focus_15.setText("▶ START 15m SPRINT")
            self.btn_focus_25.setText("25m POMODORO")

    def _update_date_display(self, now: datetime) -> None:
        """Format the stylish date badge directly above the split-flap clock."""
        accent_color = getattr(self.settings, "accent_color", "") or "#10B981"
        fmt = getattr(self.settings, "date_format", "full")

        if fmt == "compact":
            day_str = now.strftime("%a").upper()
            date_str = now.strftime("%d %b").upper()
        elif fmt == "clean":
            day_str = ""
            date_str = now.strftime("%d %B").upper()
        else:  # full
            day_str = now.strftime("%A").upper()
            date_str = now.strftime("%B %d").upper()

        if day_str:
            html = (
                f"<span style='color: {accent_color}; font-weight: 800; letter-spacing: 2.2px;'>{day_str}</span>"
                f"&nbsp;&nbsp;<span style='color: #52525B;'>•</span>&nbsp;&nbsp;"
                f"<span style='color: #E4E4E7; font-weight: 600; letter-spacing: 1.8px;'>{date_str}</span>"
            )
        else:
            html = f"<span style='color: #E4E4E7; font-weight: 600; letter-spacing: 1.8px;'>{date_str}</span>"

        self.lbl_date.setText(html)
        self.lbl_date.setStyleSheet(f"""
            QLabel#lblDashboardDate {{
                background-color: #121215;
                color: #E4E4E7;
                border: 1px solid #27272A;
                border-radius: 13px;
                padding: 5px 18px;
                font-size: 11px;
            }}
            QLabel#lblDashboardDate:hover {{
                border: 1px solid {accent_color};
                background-color: #18181B;
            }}
        """)

    def set_current_user(self, username: str) -> None:
        """Update user button label."""
        self.current_user = username
        if hasattr(self, "btn_user"):
            self.btn_user.setText(f"👤 {username}")

    def _create_top_bar(self) -> QWidget:
        bar = QWidget(self)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addStretch()

        # Navigation Buttons Container (Auto-reveals on hover/interaction)
        self.nav_container = QWidget(bar)
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)

        self.btn_user = QPushButton(f"👤 {self.current_user}")
        self.btn_user.setStyleSheet("""
            QPushButton {
                background-color: #14221D;
                color: #38BDF8;
                border: 1px solid #0369A1;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #0369A1;
                color: #FFFFFF;
            }
        """)
        self.btn_user.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_user.setToolTip("Switch user profile (no password)")
        self.btn_user.clicked.connect(self.open_switch_user_requested.emit)
        nav_layout.addWidget(self.btn_user)

        self.btn_timetable = QPushButton("Schedule")
        self.btn_timetable.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_timetable.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_timetable.clicked.connect(self.open_timetable_requested.emit)
        nav_layout.addWidget(self.btn_timetable)

        self.btn_debrief = QPushButton("Debrief")
        self.btn_debrief.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_debrief.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_debrief.clicked.connect(self.open_debrief_requested.emit)
        nav_layout.addWidget(self.btn_debrief)

        self.btn_tasks = QPushButton("Tasks")
        self.btn_tasks.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_tasks.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tasks.clicked.connect(self.open_tasks_requested.emit)
        nav_layout.addWidget(self.btn_tasks)

        self.btn_targets = QPushButton("Targets")
        self.btn_targets.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_targets.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_targets.clicked.connect(lambda: self.open_targets_requested.emit(self.selected_subject or ""))
        nav_layout.addWidget(self.btn_targets)

        self.btn_log = QPushButton("Log")
        self.btn_log.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_log.clicked.connect(lambda: self.open_manual_log_requested.emit(self.selected_subject or ""))
        nav_layout.addWidget(self.btn_log)

        self.btn_history = QPushButton("History")
        self.btn_history.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_history.clicked.connect(self.open_history_requested.emit)
        nav_layout.addWidget(self.btn_history)

        self.btn_settings = QPushButton("Settings")
        self.btn_settings.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_settings_requested.emit)
        nav_layout.addWidget(self.btn_settings)

        self.btn_fullscreen = QPushButton("⛶")
        self.btn_fullscreen.setFixedSize(36, 32)
        self.btn_fullscreen.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_fullscreen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen_requested.emit)
        nav_layout.addWidget(self.btn_fullscreen)

        layout.addWidget(self.nav_container)

        return bar

    def _create_timeline_strip(self) -> QWidget:
        strip = QWidget(self)
        layout = QVBoxLayout(strip)
        layout.setContentsMargins(0, 0, 0, 2)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_timeline_title = QLabel("TODAY'S SCHEDULE")
        self.lbl_timeline_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_timeline_title.setStyleSheet("""
            color: #52525B;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        layout.addWidget(self.lbl_timeline_title)

        self.timeline_cards_container = QWidget(strip)
        self.timeline_cards_layout = QHBoxLayout(self.timeline_cards_container)
        self.timeline_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_cards_layout.setSpacing(8)
        self.timeline_cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timeline_cards_container)

        return strip

    # -------------------------------------------------------------------------
    # Inactivity & Hover Visibility Logic
    # -------------------------------------------------------------------------

    def eventFilter(self, watched, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress):
            self._on_user_interaction()
        return super().eventFilter(watched, event)

    def _on_user_interaction(self) -> None:
        if not self._is_interactive:
            self._set_interactive_mode(True)
        self._inactivity_timer.start()

    def _on_inactivity_timeout(self) -> None:
        self._set_interactive_mode(False)

    def _set_interactive_mode(self, interactive: bool) -> None:
        self._is_interactive = interactive
        self.nav_container.setVisible(interactive)
        self.action_container.setVisible(interactive)
        self.btn_prev_carousel.setVisible(interactive)
        self.btn_next_carousel.setVisible(interactive)
        self.lbl_subject_hint.setVisible(interactive)

    # -------------------------------------------------------------------------
    # Carousel Logic
    # -------------------------------------------------------------------------

    def _rotate_carousel(self) -> None:
        if not self._carousel_slides:
            return
        self._carousel_index = (self._carousel_index + 1) % len(self._carousel_slides)
        self.lbl_carousel_text.setText(self._carousel_slides[self._carousel_index])

    def _prev_carousel(self) -> None:
        if not self._carousel_slides:
            return
        self._carousel_index = (self._carousel_index - 1) % len(self._carousel_slides)
        self.lbl_carousel_text.setText(self._carousel_slides[self._carousel_index])

    def _next_carousel(self) -> None:
        if not self._carousel_slides:
            return
        self._carousel_index = (self._carousel_index + 1) % len(self._carousel_slides)
        self.lbl_carousel_text.setText(self._carousel_slides[self._carousel_index])

    # -------------------------------------------------------------------------
    # Data Refresh & State
    # -------------------------------------------------------------------------

    def refresh_dashboard(self, ref_dt: datetime | None = None) -> None:
        now = ref_dt or datetime.now()
        self._update_date_display(now)

        # Update ambient bottom timeline strip
        self._update_timeline_strip(now)

        if not self.engine:
            self.lbl_subject_name.setText("STUDY STATION")
            self.lbl_task_title.setText("Ready to Focus")
            self.lbl_task_kicker.setText("⚡ AMBIENT LAUNCHPAD")
            self._carousel_slides = ["● READY TO FOCUS"]
            self.lbl_carousel_text.setText(self._carousel_slides[0])
            self.active_todo = None
            return

        # Build virtual chip buttons dict for unit test backwards compatibility
        all_summaries = self.engine.get_all_subjects_summary(now)
        self._chip_buttons = {None: QPushButton("Auto")}
        for s in all_summaries:
            self._chip_buttons[s.name] = QPushButton(s.name)

        # Determine active subject
        summary = None
        if self.selected_subject:
            summary = self.engine.get_subject_summary(self.selected_subject, now)

        if not summary:
            # Auto-suggest: check for priority study todo across subjects
            priority_todo = self.engine.get_priority_study_todo(now)
            if priority_todo:
                summary = self.engine.get_subject_summary(priority_todo.subject_name, now)
                self.active_todo = priority_todo

            if not summary:
                suggested = self.engine.get_suggested_cycle(now)
                if suggested:
                    summary = self.engine.get_subject_summary(suggested.subject_name, now)
                elif all_summaries:
                    summary = all_summaries[0]

        if not summary:
            self.lbl_subject_name.setText("NO ACTIVE CLASSES")
            self.lbl_task_title.setText("Add sessions in Schedule Cockpit")
            self.lbl_task_kicker.setText("NO ACTIVE SESSIONS")
            self._carousel_slides = ["● ADD SESSIONS IN SCHEDULE GRID"]
            self.lbl_carousel_text.setText(self._carousel_slides[0])
            self.active_todo = None
            return

        clean_name = ScheduleEngine.clean_subject_name(summary.name)
        self.lbl_subject_name.setText(clean_name)

        # Resolve active pending task for this subject
        subject_todos = self.engine.get_pending_todos(summary.name)
        if subject_todos:
            def todo_urgency(t):
                return (0 if t.is_overdue(now) else 1, t.due_date)
            subject_todos.sort(key=todo_urgency)
            self.active_todo = subject_todos[0]
        elif not self.selected_subject and not getattr(self, "active_todo", None):
            self.active_todo = self.engine.get_priority_study_todo(now)
        elif self.selected_subject and (not self.active_todo or self.engine.clean_subject_name(self.active_todo.subject_name).lower() != clean_name.lower()):
            self.active_todo = None

        clean_next = summary.next_session_text.replace("📅 ", "").replace("📅", "") if summary.next_session_text else "No upcoming session"
        accent_color = getattr(self.settings, "accent_color", "") or "#10B981"

        if self.active_todo:
            self.lbl_task_title.setText(self.active_todo.title)
            due_fmt = self.active_todo.due_date.strftime('%a %d %b %H:%M')
            self.lbl_task_title.setToolTip(f"Active Mission: {self.active_todo.title}\nDue: {due_fmt}\nClick to view Task Backlog")

            if self.active_todo.is_overdue(now):
                delta = now - self.active_todo.due_date
                total_hours = int(delta.total_seconds() // 3600)
                if total_hours >= 24:
                    time_str = f"{total_hours // 24}d {total_hours % 24}h AGO"
                elif total_hours > 0:
                    time_str = f"{total_hours}h AGO"
                else:
                    time_str = "JUST NOW"
                self.lbl_task_kicker.setText(f"⚠ OVERDUE · WAS DUE {time_str}")
                self.lbl_task_kicker.setStyleSheet("""
                    QLabel {
                        background-color: rgba(239, 68, 68, 0.15);
                        color: #F87171;
                        border: 1px solid rgba(239, 68, 68, 0.35);
                        border-radius: 11px;
                        padding: 3px 12px;
                        font-size: 10px;
                        font-weight: 700;
                        letter-spacing: 1px;
                    }
                """)
            else:
                delta = self.active_todo.due_date - now
                total_hours = int(delta.total_seconds() // 3600)
                if total_hours < 24:
                    mins = int((delta.total_seconds() % 3600) // 60)
                    time_str = f"IN {total_hours}h {mins}m" if total_hours > 0 else f"IN {mins}m"
                elif total_hours < 48:
                    time_str = "TOMORROW"
                else:
                    days = total_hours // 24
                    time_str = f"IN {days} DAYS"
                self.lbl_task_kicker.setText(f"🎯 PRIORITY TASK · DUE {time_str}")
                self.lbl_task_kicker.setStyleSheet(f"""
                    QLabel {{
                        background-color: rgba(16, 185, 129, 0.12);
                        color: {accent_color};
                        border: 1px solid rgba(16, 185, 129, 0.28);
                        border-radius: 11px;
                        padding: 3px 12px;
                        font-size: 10px;
                        font-weight: 700;
                        letter-spacing: 1px;
                    }}
                """)
        else:
            self.lbl_task_title.setText("Preparation & Practice Sprint")
            self.lbl_task_title.setToolTip("No pending tasks recorded for this module. Click to add or manage tasks.")
            self.lbl_task_kicker.setText(f"ACTIVE MODULE · NEXT CLASS: {clean_next.upper()}")
            self.lbl_task_kicker.setStyleSheet("""
                QLabel {
                    background-color: #18181B;
                    color: #71717A;
                    border: 1px solid #27272A;
                    border-radius: 11px;
                    padding: 3px 12px;
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 1px;
                }
            """)

        # Build info carousel slides
        comp = summary.completed_minutes
        tgt = summary.target_minutes
        pct = summary.progress_percent
        self.progress_bar.setValue(pct)

        # Backwards compatibility labels
        self.lbl_status_badge.setText(f"{tgt} MIN")
        self.lbl_cycle_progress.setText(f"{comp} / {tgt} MIN")

        slide_progress = f"● {comp} / {tgt} MIN COMPLETED · {pct}%"
        slide_next = f"NEXT CLASS · {clean_next}"
        slide_format = f"{summary.core} · {summary.location or 'Class'}"
        if summary.is_current_class:
            slide_progress = f"● IN CLASS NOW · {summary.core}"

        # If there are unresolved questions for this subject, highlight as carousel slide!
        questions = self.engine.get_subject_questions(summary.name)
        slide_question = f"❓ QUESTION: {questions[0]}" if questions else f"{len(subject_todos)} PENDING TASKS FOR {clean_name.upper()}"

        self._carousel_slides = [slide_progress, slide_next, slide_question]
        self._carousel_index = 0
        self.lbl_carousel_text.setText(self._carousel_slides[0])

    def _update_timeline_strip(self, now: datetime) -> None:
        """Populate the ambient bottom strip with today's scheduled classes or upcoming classes."""
        if not hasattr(self, "timeline_cards_layout"):
            return

        while self.timeline_cards_layout.count():
            item = self.timeline_cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.engine or not self.engine.sessions:
            if hasattr(self, "lbl_timeline_title"):
                self.lbl_timeline_title.setText("SCHEDULE")
            empty_lbl = QLabel("READY TO FOCUS")
            empty_lbl.setStyleSheet("color: #3F3F46; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
            self.timeline_cards_layout.addWidget(empty_lbl)
            return

        today_idx = now.weekday()
        today_sessions = self.engine.get_day_sessions(today_idx)

        if not today_sessions:
            empty_lbl = QLabel("NO CLASSES SCHEDULED TODAY · FREE STUDY & REVIEW")
            empty_lbl.setStyleSheet("color: #3F3F46; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
            self.timeline_cards_layout.addWidget(empty_lbl)
            return

        current_time = now.time()

        for session in today_sessions:
            start_t = session.time_slot.start_time
            end_t = session.time_slot.end_time
            clean_name = ScheduleEngine.clean_subject_name(session.subject.name)

            is_current = (start_t <= current_time < end_t)
            is_past = (current_time >= end_t)

            btn = QPushButton()
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            if is_current:
                loc_txt = f" ({session.location})" if session.location else ""
                btn.setText(f"● NOW  {session.time_slot.start} – {session.time_slot.end}  {clean_name}{loc_txt}")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #064E3B;
                        color: #A7F3D0;
                        border: 1px solid #10B981;
                        border-radius: 13px;
                        padding: 5px 14px;
                        font-size: 11px;
                        font-weight: 700;
                        letter-spacing: 0.4px;
                    }
                    QPushButton:hover {
                        background-color: #047857;
                        color: #FFFFFF;
                    }
                """)
            elif is_past:
                btn.setText(f"✓ {session.time_slot.start}  {clean_name}")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #111114;
                        color: #52525B;
                        border: 1px solid #1C1C22;
                        border-radius: 13px;
                        padding: 5px 12px;
                        font-size: 11px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #1C1C22;
                        color: #A1A1AA;
                    }
                """)
            else:
                loc_str = f" · {session.location}" if session.location else ""
                btn.setText(f"{session.time_slot.start}  {clean_name}{loc_str}")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #18181B;
                        color: #D4D4D8;
                        border: 1px solid #27272A;
                        border-radius: 13px;
                        padding: 5px 12px;
                        font-size: 11px;
                        font-weight: 600;
                        letter-spacing: 0.3px;
                    }
                    QPushButton:hover {
                        background-color: #27272A;
                        color: #FFFFFF;
                        border: 1px solid #3F3F46;
                    }
                """)

            btn.clicked.connect(lambda _, s=clean_name: self.set_selected_subject(s))
            self.timeline_cards_layout.addWidget(btn)

    def set_selected_subject(self, subject_name: str | None) -> None:
        self.selected_subject = subject_name
        self.refresh_dashboard()

    def _on_start_focus(self, minutes: int) -> None:
        subject = self.selected_subject
        if not subject and self.engine:
            if self.active_todo:
                subject = self.active_todo.subject_name
            else:
                suggested = self.engine.get_suggested_cycle(datetime.now())
                if suggested:
                    subject = suggested.subject_name
                elif self.engine.sessions:
                    subject = self.engine.sessions[0].subject.name

        if self.active_todo is not None:
            self.start_todo_focus_requested.emit(self.active_todo, minutes)
        else:
            self.start_focus_requested.emit(subject or "STUDY", minutes)

    def apply_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        bg_hex = getattr(settings, "bg_color", "") or "#09090B"
        accent_hex = getattr(settings, "accent_color", "") or "#10B981"
        self.setStyleSheet(f"background-color: {bg_hex};")
        if hasattr(self, "progress_bar"):
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #1C1C22;
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {accent_hex};
                    border-radius: 2px;
                }}
            """)
        self.clock_widget.apply_settings(settings)
        self._update_typography()
        self.refresh_dashboard()

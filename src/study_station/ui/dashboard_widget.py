"""Subject-Centric Dashboard Widget for Study Station.

Centers the application around the Subject, its study cycle review progress,
and upcoming class schedule, accompanied by an elegant split-flap flip clock
and quick subject switching.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
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
    CHIP_BUTTON_ACTIVE_STYLE,
    CHIP_BUTTON_STYLE,
    get_modern_font,
)


class SubjectDashboardWidget(QWidget):
    """Primary Subject-Centric Screen of Study Station."""

    start_focus_requested = Signal(str, int)  # (subject_name, duration_minutes)
    open_settings_requested = Signal()
    open_timetable_requested = Signal()
    open_targets_requested = Signal(str)  # subject_name
    open_manual_log_requested = Signal(str)  # subject_name
    toggle_fullscreen_requested = Signal()

    def __init__(
        self,
        engine: ScheduleEngine | None = None,
        settings: AppSettings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.settings = settings or AppSettings()
        self.selected_subject: str | None = None

        self._chip_buttons: dict[str | None, QPushButton] = {}

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 16, 28, 16)
        main_layout.setSpacing(12)

        # 1. Top Bar
        self.top_bar = self._create_top_bar()
        main_layout.addWidget(self.top_bar)

        # 2. Split-Flap Clock Widget
        self.clock_widget = SplitFlapClockWidget(self.settings, self)
        main_layout.addWidget(self.clock_widget)

        # 3. Dual-Card Cockpit Container
        self.cards_container = QWidget(self)
        self.cards_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cards_layout = QHBoxLayout(self.cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(16)

        self.hero_card = self._create_hero_card()
        self.hero_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cards_layout.addWidget(self.hero_card, stretch=6)

        self.upcoming_card = self._create_upcoming_card()
        self.upcoming_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cards_layout.addWidget(self.upcoming_card, stretch=4)

        main_layout.addWidget(self.cards_container, stretch=1)

        # 4. Subject Switcher Shelf
        self.switcher_widget = self._create_subject_switcher()
        main_layout.addWidget(self.switcher_widget)

        self.refresh_dashboard()

    # -------------------------------------------------------------------------
    # Top Bar
    # -------------------------------------------------------------------------

    def _create_top_bar(self) -> QWidget:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Brand / Mode Badge
        self.lbl_brand = QLabel("● STUDY STATION", container)
        self.lbl_brand.setFont(get_modern_font("sans", 12, QFont.Weight.Bold))
        self.lbl_brand.setStyleSheet("""
            QLabel {
                color: #A1A1AA;
                background-color: #141418;
                border: 1px solid #27272A;
                border-radius: 14px;
                padding: 5px 14px;
                letter-spacing: 1.5px;
            }
        """)
        layout.addWidget(self.lbl_brand)

        # Date Label
        self.lbl_date = QLabel("", container)
        self.lbl_date.setFont(get_modern_font("sans", 13, QFont.Weight.Medium))
        self.lbl_date.setStyleSheet("color: #71717A; letter-spacing: 1.5px;")
        layout.addWidget(self.lbl_date)

        layout.addStretch()

        # Direct Editing & Utility Buttons (Clean typography without multi-color emojis)
        self.btn_timetable = QPushButton("Timetable", container)
        self.btn_timetable.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_timetable.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_timetable.clicked.connect(lambda checked=False: self.open_timetable_requested.emit())
        layout.addWidget(self.btn_timetable)

        self.btn_targets = QPushButton("Targets", container)
        self.btn_targets.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_targets.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_targets.clicked.connect(lambda checked=False: self.open_targets_requested.emit(self.selected_subject or ""))
        layout.addWidget(self.btn_targets)

        self.btn_log = QPushButton("Log Time", container)
        self.btn_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_log.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_log.clicked.connect(lambda checked=False: self.open_manual_log_requested.emit(self.selected_subject or ""))
        layout.addWidget(self.btn_log)

        self.btn_settings = QPushButton("Settings", container)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_settings.clicked.connect(lambda checked=False: self.open_settings_requested.emit())
        layout.addWidget(self.btn_settings)

        self.btn_fullscreen = QPushButton("⛶", container)
        self.btn_fullscreen.setToolTip("Toggle Fullscreen (F11)")
        self.btn_fullscreen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fullscreen.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_fullscreen.clicked.connect(lambda checked=False: self.toggle_fullscreen_requested.emit())
        layout.addWidget(self.btn_fullscreen)

        return container

    # -------------------------------------------------------------------------
    # Hero Subject Card
    # -------------------------------------------------------------------------

    def _create_hero_card(self) -> QFrame:
        card = QFrame(self)
        card.setObjectName("heroCard")
        card.setStyleSheet("""
            QFrame#heroCard {
                background-color: #121216;
                border: 1px solid #24242C;
                border-radius: 18px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 20, 26, 20)
        layout.setSpacing(12)

        # Row 1: Header tags (Session type / Location & Target status)
        row1 = QHBoxLayout()
        self.lbl_type_loc = QLabel("SESSION TYPE · LOCATION", card)
        self.lbl_type_loc.setFont(get_modern_font("sans", 11, QFont.Weight.DemiBold))
        self.lbl_type_loc.setStyleSheet("""
            color: #38BDF8;
            background-color: #0C2136;
            border: 1px solid #0369A1;
            border-radius: 8px;
            padding: 3px 10px;
            letter-spacing: 0.5px;
        """)
        row1.addWidget(self.lbl_type_loc, alignment=Qt.AlignmentFlag.AlignVCenter)

        row1.addStretch()

        self.lbl_status_badge = QLabel("TARGET: 60 MIN", card)
        self.lbl_status_badge.setFont(get_modern_font("sans", 11, QFont.Weight.DemiBold))
        self.lbl_status_badge.setStyleSheet("""
            color: #A1A1AA;
            background-color: #18181D;
            border: 1px solid #27272A;
            border-radius: 8px;
            padding: 3px 10px;
            letter-spacing: 0.5px;
        """)
        row1.addWidget(self.lbl_status_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(row1)

        # Row 2: Subject Title
        self.lbl_subject_name = QLabel("SUBJECT NAME", card)
        self.lbl_subject_name.setFont(get_modern_font("sans", 22, QFont.Weight.Bold))
        self.lbl_subject_name.setWordWrap(True)
        self.lbl_subject_name.setStyleSheet("color: #FFFFFF; line-height: 1.25;")
        layout.addWidget(self.lbl_subject_name)

        # Row 3: Progress Bar
        self.progress_bar = QProgressBar(card)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E1E26;
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Row 4: Progress Stats
        row_stats = QHBoxLayout()
        self.lbl_completed_text = QLabel("0 / 60 MIN COMPLETED", card)
        self.lbl_completed_text.setFont(get_modern_font("sans", 12, QFont.Weight.DemiBold))
        self.lbl_completed_text.setStyleSheet("color: #F4F4F5; letter-spacing: 0.5px;")
        row_stats.addWidget(self.lbl_completed_text, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.lbl_remaining_text = QLabel("60 MIN REMAINING", card)
        self.lbl_remaining_text.setFont(get_modern_font("sans", 12, QFont.Weight.Medium))
        self.lbl_remaining_text.setStyleSheet("color: #71717A; letter-spacing: 0.5px;")
        row_stats.addWidget(self.lbl_remaining_text, alignment=Qt.AlignmentFlag.AlignVCenter)

        row_stats.addStretch()

        self.lbl_pct_badge = QLabel("0%", card)
        self.lbl_pct_badge.setFont(get_modern_font("mono", 11, QFont.Weight.Bold))
        self.lbl_pct_badge.setStyleSheet("""
            color: #E4E4E7;
            background-color: #1A1A22;
            border: 1px solid #2E2E38;
            border-radius: 6px;
            padding: 2px 8px;
        """)
        row_stats.addWidget(self.lbl_pct_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(row_stats)

        # Row 5: Schedule context (Next class)
        self.lbl_next_class = QLabel("Next class: Friday at 08:00 (in 2 days)", card)
        self.lbl_next_class.setFont(get_modern_font("sans", 12, QFont.Weight.Normal))
        self.lbl_next_class.setStyleSheet("color: #9CA3AF;")
        layout.addWidget(self.lbl_next_class)

        layout.addStretch(1)

        # Row 6: Action Buttons
        layout.addSpacing(4)
        row_actions = QHBoxLayout()
        row_actions.setSpacing(10)

        self.btn_focus_15 = QPushButton("▶ Start Focus (15m)", card)
        self.btn_focus_15.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_focus_15.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_focus_15.clicked.connect(lambda checked=False: self._on_start_focus(15))
        row_actions.addWidget(self.btn_focus_15)

        self.btn_focus_25 = QPushButton("▶ 25m", card)
        self.btn_focus_25.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_focus_25.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_focus_25.clicked.connect(lambda checked=False: self._on_start_focus(25))
        row_actions.addWidget(self.btn_focus_25)

        self.btn_hero_log = QPushButton("Log Time", card)
        self.btn_hero_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hero_log.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_hero_log.clicked.connect(lambda checked=False: self.open_manual_log_requested.emit(self.selected_subject or ""))
        row_actions.addWidget(self.btn_hero_log)

        self.btn_hero_target = QPushButton("Edit Target", card)
        self.btn_hero_target.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hero_target.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_hero_target.clicked.connect(lambda checked=False: self.open_targets_requested.emit(self.selected_subject or ""))
        row_actions.addWidget(self.btn_hero_target)

        row_actions.addStretch()
        layout.addLayout(row_actions)

        return card

    # -------------------------------------------------------------------------
    # Upcoming Classes Card (Part of Dual-Card Cockpit)
    # -------------------------------------------------------------------------

    def _create_upcoming_card(self) -> QFrame:
        card = QFrame(self)
        card.setObjectName("upcomingCard")
        card.setStyleSheet("""
            QFrame#upcomingCard {
                background-color: #121216;
                border: 1px solid #24242C;
                border-radius: 18px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        # Header Row
        header_row = QHBoxLayout()
        lbl_title = QLabel("UPCOMING CLASSES", card)
        lbl_title.setFont(get_modern_font("sans", 11, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #A1A1AA; letter-spacing: 1.5px;")
        header_row.addWidget(lbl_title)
        header_row.addStretch()

        lbl_badge = QLabel("TIMETABLE", card)
        lbl_badge.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        lbl_badge.setStyleSheet("""
            color: #71717A;
            background-color: #18181D;
            border: 1px solid #27272A;
            border-radius: 6px;
            padding: 2px 7px;
            letter-spacing: 1px;
        """)
        header_row.addWidget(lbl_badge)
        layout.addLayout(header_row)

        # Upcoming list layout
        self.upcoming_list_layout = QVBoxLayout()
        self.upcoming_list_layout.setSpacing(6)
        layout.addLayout(self.upcoming_list_layout)

        layout.addStretch()

        # Footer shortcut hint
        lbl_hint = QLabel("Press 'E' for full timetable · 'M' to log time", card)
        lbl_hint.setFont(get_modern_font("sans", 11, QFont.Weight.Normal))
        lbl_hint.setStyleSheet("color: #52525B;")
        layout.addWidget(lbl_hint)

        return card

    # -------------------------------------------------------------------------
    # Subject Switcher Shelf
    # -------------------------------------------------------------------------

    def _create_subject_switcher(self) -> QWidget:
        container = QWidget(self)
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(6)

        lbl_section = QLabel("ENROLLED SUBJECTS · CLICK TO FOCUS", container)
        lbl_section.setFont(get_modern_font("sans", 11, QFont.Weight.DemiBold))
        lbl_section.setStyleSheet("color: #71717A; letter-spacing: 1.5px;")
        vbox.addWidget(lbl_section)

        # Horizontal Scroll Area for subject chips
        self.chips_scroll = QScrollArea(container)
        self.chips_scroll.setWidgetResizable(True)
        self.chips_scroll.setFixedHeight(48)
        self.chips_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chips_scroll.setStyleSheet("background: transparent; border: none;")
        self.chips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chips_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chips_container = QWidget()
        self.chips_container.setStyleSheet("background: transparent;")
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(8)

        self.chips_scroll.setWidget(self.chips_container)
        vbox.addWidget(self.chips_scroll)

        return container

    # -------------------------------------------------------------------------
    # State & Updates
    # -------------------------------------------------------------------------

    def apply_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        self.clock_widget.apply_settings(settings)
        self.refresh_dashboard()

    def set_selected_subject(self, subject_name: str | None) -> None:
        self.selected_subject = subject_name
        self.refresh_dashboard()

    def _on_start_focus(self, minutes: int) -> None:
        name = self.selected_subject
        if not name and self.engine:
            suggested = self.engine.get_suggested_cycle(datetime.now())
            if suggested:
                name = suggested.subject_name
            elif self.engine.sessions:
                name = self.engine.sessions[0].subject.name
        self.start_focus_requested.emit(name or "STUDY", minutes)

    def refresh_dashboard(self) -> None:
        """Refresh Date, Hero Subject card, and Subject Switcher chips."""
        now = datetime.now()

        # 1. Update Date
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        day_str = day_names[now.weekday()]
        month_str = month_names[now.month - 1]
        self.lbl_date.setText(f"{day_str.upper()}, {month_str.upper()} {now.day}, {now.year}")

        if not self.engine or not self.engine.sessions:
            # Fallback when timetable is empty
            self._render_empty_state()
            return

        # 2. Determine hero subject
        hero_subject_name = self.selected_subject
        is_auto = False
        if not hero_subject_name:
            is_auto = True
            suggested = self.engine.get_suggested_cycle(now)
            if suggested:
                hero_subject_name = suggested.subject_name
            elif self.engine.sessions:
                hero_subject_name = self.engine.sessions[0].subject.name

        if hero_subject_name:
            summary = self.engine.get_subject_summary(hero_subject_name, now)
            self._render_hero_summary(summary, is_auto)

        # 3. Update Subject Switcher Chips
        self._rebuild_subject_chips(now)

        # 4. Update Upcoming Classes Timeline
        self._render_upcoming_classes(now)

    def _render_empty_state(self) -> None:
        self.lbl_type_loc.setText("TIMETABLE EMPTY")
        self.lbl_type_loc.setStyleSheet("""
            color: #A1A1AA;
            background-color: #18181D;
            border: 1px solid #27272A;
            border-radius: 8px;
            padding: 3px 10px;
        """)
        self.lbl_status_badge.setText("GET STARTED")
        self.lbl_subject_name.setText("WELCOME TO STUDY STATION")
        self.lbl_next_class.setText("Add your weekly timetable to track review cycles between classes.")
        self.progress_bar.setValue(0)
        self.lbl_completed_text.setText("0 / 0 MIN")
        self.lbl_remaining_text.setText("No active cycle")
        self.lbl_pct_badge.setText("0%")
        self.btn_focus_15.setText("▶ Start Focus (15m)")
        self._render_upcoming_classes(datetime.now())

    def _render_hero_summary(self, summary: SubjectSummary, is_auto: bool) -> None:
        # Type & Location
        loc_str = f" · {summary.location}" if summary.location else ""
        if summary.is_current_class:
            self.lbl_type_loc.setText(f"● IN CLASS NOW · {summary.core}{loc_str}")
            self.lbl_type_loc.setStyleSheet("""
                color: #34D399;
                background-color: #064E3B;
                border: 1px solid #059669;
                border-radius: 8px;
                padding: 3px 10px;
                letter-spacing: 0.5px;
            """)
        else:
            self.lbl_type_loc.setText(f"{summary.core}{loc_str}")
            self.lbl_type_loc.setStyleSheet("""
                color: #38BDF8;
                background-color: #0C2136;
                border: 1px solid #0369A1;
                border-radius: 8px;
                padding: 3px 10px;
                letter-spacing: 0.5px;
            """)

        # Status badge
        if summary.is_target_met:
            self.lbl_status_badge.setText("✓ TARGET COMPLETED")
            self.lbl_status_badge.setStyleSheet("""
                color: #34D399;
                background-color: #064E3B;
                border: 1px solid #059669;
                border-radius: 8px;
                padding: 3px 10px;
                letter-spacing: 0.5px;
            """)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background-color: #1E1E26;
                    border-radius: 4px;
                    border: none;
                }
                QProgressBar::chunk {
                    background-color: #10B981;
                    border-radius: 4px;
                }
            """)
        else:
            auto_label = " (RECOMMENDED)" if is_auto else ""
            self.lbl_status_badge.setText(f"TARGET: {summary.target_minutes} MIN{auto_label}")
            self.lbl_status_badge.setStyleSheet("""
                color: #A1A1AA;
                background-color: #18181D;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 3px 10px;
                letter-spacing: 0.5px;
            """)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background-color: #1E1E26;
                    border-radius: 4px;
                    border: none;
                }
                QProgressBar::chunk {
                    background-color: #3B82F6;
                    border-radius: 4px;
                }
            """)

        # Subject name
        self.lbl_subject_name.setText(summary.name)

        # Progress bar & stats
        self.progress_bar.setValue(summary.progress_percent)
        self.lbl_completed_text.setText(f"{summary.completed_minutes} / {summary.target_minutes} MIN COMPLETED")
        self.lbl_remaining_text.setText(f"{summary.remaining_minutes} MIN REMAINING")
        self.lbl_pct_badge.setText(f"{summary.progress_percent}%")

        # Next class
        self.lbl_next_class.setText(f"Next class: {summary.next_session_text}")

        # Primary button text
        self.btn_focus_15.setText(f"▶ Start Focus ({self.settings.default_focus_minutes}m)")

    def _render_upcoming_classes(self, current_dt: datetime) -> None:
        """Populate the upcoming classes mini-timeline card."""
        while self.upcoming_list_layout.count():
            item = self.upcoming_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        if not self.engine or not self.engine.sessions:
            lbl = QLabel("No timetable sessions loaded.\nClick 'Timetable' above to add your weekly classes.")
            lbl.setFont(get_modern_font("sans", 12, QFont.Weight.Normal))
            lbl.setStyleSheet("color: #71717A; line-height: 1.4;")
            lbl.setWordWrap(True)
            self.upcoming_list_layout.addWidget(lbl)
            return

        upcoming = self.engine.get_upcoming_sessions(current_dt, limit=3)
        if not upcoming:
            lbl = QLabel("No upcoming classes scheduled this week.")
            lbl.setFont(get_modern_font("sans", 12, QFont.Weight.Normal))
            lbl.setStyleSheet("color: #71717A;")
            self.upcoming_list_layout.addWidget(lbl)
            return

        for session, start_dt in upcoming:
            item_frame = QFrame()
            item_frame.setStyleSheet("""
                QFrame {
                    background-color: #16161D;
                    border: 1px solid #22222A;
                    border-radius: 10px;
                }
            """)
            item_layout = QVBoxLayout(item_frame)
            item_layout.setContentsMargins(12, 8, 12, 8)
            item_layout.setSpacing(4)

            # Header row: When + Type Badge
            top_row = QHBoxLayout()
            if start_dt.date() == current_dt.date():
                time_prefix = "Today"
            elif start_dt.date() == (current_dt + timedelta(days=1)).date():
                time_prefix = "Tomorrow"
            else:
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                time_prefix = day_names[start_dt.weekday()]

            time_str = f"{time_prefix} at {session.time_slot.start}"
            lbl_time = QLabel(time_str)
            lbl_time.setFont(get_modern_font("sans", 11, QFont.Weight.DemiBold))
            lbl_time.setStyleSheet("color: #93C5FD; letter-spacing: 0.5px;")
            top_row.addWidget(lbl_time)
            top_row.addStretch()

            type_text = f"{session.subject.core} · {session.location}" if session.location else session.subject.core
            lbl_type = QLabel(type_text)
            lbl_type.setFont(get_modern_font("sans", 10, QFont.Weight.Medium))
            lbl_type.setStyleSheet("""
                color: #71717A;
                background-color: #1F1F28;
                border-radius: 4px;
                padding: 1px 6px;
            """)
            top_row.addWidget(lbl_type)
            item_layout.addLayout(top_row)

            # Subject title
            clean_name = ScheduleEngine.clean_subject_name(session.subject.name)
            lbl_sub = QLabel(clean_name)
            lbl_sub.setFont(get_modern_font("sans", 12, QFont.Weight.DemiBold))
            lbl_sub.setStyleSheet("color: #F4F4F5;")
            lbl_sub.setWordWrap(True)
            item_layout.addWidget(lbl_sub)

            self.upcoming_list_layout.addWidget(item_frame)

    def _rebuild_subject_chips(self, current_dt: datetime) -> None:
        """Populate the horizontal subject selector shelf."""
        # Clear existing chips
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._chip_buttons.clear()

        # 1. "Auto (Recommended)" Chip
        auto_btn = QPushButton("★ Auto (Next Class)", self.chips_container)
        auto_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        auto_btn.setStyleSheet(CHIP_BUTTON_ACTIVE_STYLE if self.selected_subject is None else CHIP_BUTTON_STYLE)
        auto_btn.clicked.connect(lambda: self.set_selected_subject(None))
        self.chips_layout.addWidget(auto_btn)
        self._chip_buttons[None] = auto_btn

        if not self.engine:
            self.chips_layout.addStretch()
            return

        # 2. Individual Subject Chips
        all_summaries = self.engine.get_all_subjects_summary(current_dt)
        for s in all_summaries:
            status_icon = "✓ " if s.is_target_met else ""
            label_text = f"{status_icon}{s.short_name} · {s.completed_minutes}/{s.target_minutes}m"
            btn = QPushButton(label_text, self.chips_container)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            is_active = (self.selected_subject == s.name)
            btn.setStyleSheet(CHIP_BUTTON_ACTIVE_STYLE if is_active else CHIP_BUTTON_STYLE)
            btn.clicked.connect(lambda checked=False, name=s.name: self.set_selected_subject(name))
            self.chips_layout.addWidget(btn)
            self._chip_buttons[s.name] = btn

        self.chips_layout.addStretch()

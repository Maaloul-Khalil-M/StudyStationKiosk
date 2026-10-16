"""Full-Screen Weekly Schedule & Class Editor view for Study Station.

Provides an immersive, edge-to-edge weekly calendar grid modeled directly after
university schedule (docs/grid.pdf / Google Calendar) with an inline session editor.
Eliminates floating dialog rims, text-peeking, and modal-on-modal stacking.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from PySide6.QtCore import QPoint, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    DAY_INDEX_MAP,
    StudyTodo,
    Subject,
    TimeSlot,
    normalize_time_str,
)
from study_station.ui.class_session_dialog import ClassSessionDialog
from study_station.ui.subject_preparation_sheet import SubjectPreparationSheet
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class EmptyGridSlot(QPushButton):
    """An interactive empty slot in the schedule grid allowing click-to-add."""

    clicked_slot = Signal(str, str, str)  # (day_code, start_time, end_time)

    def __init__(
        self,
        day_code: str,
        start_time: str,
        end_time: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.day_code = day_code
        self.start_time = start_time
        self.end_time = end_time
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"{day_code} {start_time} – {end_time} · Click to add class")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(2)

        self.lbl_plus = QLabel("+")
        self.lbl_plus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_plus.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_plus.setStyleSheet("color: #27272E; font-size: 16px; font-weight: 400;")
        layout.addWidget(self.lbl_plus)

        self.lbl_time = QLabel(f"{start_time} – {end_time}")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_time.setStyleSheet("color: #3F3F4E; font-size: 10px; font-family: monospace;")
        layout.addWidget(self.lbl_time)

        self.setStyleSheet("""
            EmptyGridSlot {
                background-color: #0E0E12;
                border: 1px solid #18181F;
                border-radius: 8px;
            }
            EmptyGridSlot:hover {
                background-color: #14141C;
                border: 1px dashed #3F3F4E;
            }
            EmptyGridSlot:hover QLabel {
                color: #10B981;
            }
            EmptyGridSlot:pressed {
                background-color: #1C1C26;
            }
        """)
        self.clicked.connect(lambda: self.clicked_slot.emit(self.day_code, self.start_time, self.end_time))


class ClassGridCard(QPushButton):
    """An interactive class card in the weekly schedule grid."""

    clicked_session = Signal(str)  # subject name (legacy)
    clicked_session_card = Signal(object)  # AcademicSession

    def __init__(
        self,
        session: AcademicSession,
        is_current: bool = False,
        engine: ScheduleEngine | None = None,
        is_overridden: bool = False,
        override_label: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.is_current = is_current
        self.is_overridden = is_overridden
        self.override_label = override_label
        self.engine = engine
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(86)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        clean_name = ScheduleEngine.clean_subject_name(session.subject.name)
        core_type = session.subject.core.upper()
        room = session.location or "Class"

        # Preparation Metrics
        pending_todos_count = 0
        questions_count = 0
        has_due_soon = False
        completed_todos_count = 0

        if self.engine:
            pending = self.engine.get_pending_todos(clean_name)
            pending_todos_count = len(pending)
            has_due_soon = any(t.is_due_soon(24) or t.is_overdue() for t in pending)
            questions = self.engine.get_subject_questions(clean_name)
            questions_count = len(questions)
            completed_todos_count = sum(1 for t in self.engine.get_todos(subject_filter=clean_name) if t.is_completed)

        # Refined calm badge colors
        core_colors = {
            "TP": ("#064E3B", "#6EE7B7"),      # Emerald
            "COURS": ("#1E293B", "#93C5FD"),   # Slate Blue
            "TD": ("#2E1065", "#C4B5FD"),      # Muted Indigo
            "CI": ("#451A03", "#FCD34D"),      # Warm Amber
        }
        bg_badge, fg_badge = core_colors.get(core_type, ("#1E1E24", "#A1A1AA"))

        if is_overridden:
            current_border = "border: 1px dashed #D97706;"
            current_bg = "background-color: #17130D;"
        elif is_current:
            current_border = "border: 2px solid #10B981;"
            current_bg = "background-color: #14221D;"
        else:
            current_border = "border: 1px solid #222228;"
            current_bg = "background-color: #121216;"

        self.setStyleSheet(f"""
            ClassGridCard {{
                {current_bg}
                {current_border}
                border-radius: 8px;
                padding: 6px 8px;
                text-align: left;
            }}
            ClassGridCard:hover {{
                background-color: #1A1A22;
                border: 1px solid #3F3F4A;
            }}
            ClassGridCard:pressed {{
                background-color: #24242E;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # Header row: Core badge + Room
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        lbl_core = QLabel(core_type)
        lbl_core.setStyleSheet(f"""
            background-color: {bg_badge};
            color: {fg_badge};
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        header_row.addWidget(lbl_core)

        if is_overridden:
            lbl_ovr = QLabel("⚡ OVERRIDDEN")
            lbl_ovr.setStyleSheet("""
                background-color: #78350F;
                color: #FDE68A;
                font-size: 8px;
                font-weight: 800;
                padding: 1px 4px;
                border-radius: 3px;
            """)
            header_row.addWidget(lbl_ovr)
        elif is_current:
            lbl_now = QLabel("● NOW")
            lbl_now.setStyleSheet("color: #10B981; font-size: 10px; font-weight: 700;")
            header_row.addWidget(lbl_now)

        header_row.addStretch()

        lbl_room = QLabel(room)
        lbl_room.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 600;")
        header_row.addWidget(lbl_room)
        layout.addLayout(header_row)

        # Subject title
        lbl_name = QLabel(clean_name)
        lbl_name.setFont(get_modern_font("eva_display", 11, QFont.Weight.Bold))
        lbl_name.setWordWrap(True)
        lbl_name.setStyleSheet("color: #F4F4F6; font-size: 11px; font-weight: 700;")
        layout.addWidget(lbl_name)

        # Preparation Badges Row
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 2, 0, 0)
        badge_row.setSpacing(4)

        if pending_todos_count > 0:
            badge_text = f"● {pending_todos_count} DUE" if has_due_soon else f"● {pending_todos_count} TODO"
            lbl_todo = QLabel(badge_text)
            if has_due_soon:
                lbl_todo.setStyleSheet("""
                    background-color: #451A03;
                    color: #FCD34D;
                    border: 1px solid #78350F;
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: 700;
                    padding: 1px 4px;
                """)
            else:
                lbl_todo.setStyleSheet("""
                    background-color: #1E293B;
                    color: #93C5FD;
                    border: 1px solid #334155;
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: 700;
                    padding: 1px 4px;
                """)
            badge_row.addWidget(lbl_todo)
        elif completed_todos_count > 0:
            lbl_ready = QLabel("✓ READY")
            lbl_ready.setStyleSheet("""
                background-color: #064E3B;
                color: #6EE7B7;
                border: 1px solid #047857;
                border-radius: 3px;
                font-size: 9px;
                font-weight: 700;
                padding: 1px 4px;
            """)
            badge_row.addWidget(lbl_ready)

        if questions_count > 0:
            if is_current:
                lbl_q = QLabel(f"❓ ASK IN CLASS ({questions_count})")
                lbl_q.setStyleSheet("""
                    background-color: #0369A1;
                    color: #F0F9FF;
                    border: 1px solid #38BDF8;
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: 800;
                    padding: 1px 5px;
                """)
            else:
                lbl_q = QLabel(f"❓ {questions_count}")
                lbl_q.setStyleSheet("""
                    background-color: #082F49;
                    color: #38BDF8;
                    border: 1px solid #0369A1;
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: 700;
                    padding: 1px 4px;
                """)
            badge_row.addWidget(lbl_q)

        badge_row.addStretch()
        layout.addLayout(badge_row)

        layout.addStretch()

        # Time footer
        lbl_time = QLabel(f"{session.time_slot.start} - {session.time_slot.end}")
        lbl_time.setFont(get_modern_font("mono", 10, QFont.Weight.Medium))
        lbl_time.setStyleSheet("color: #52525B; font-size: 10px;")
        layout.addWidget(lbl_time)
        self.clicked.connect(self._on_card_clicked)

    def _on_card_clicked(self) -> None:
        self.clicked_session_card.emit(self.session)


class ScheduleScreenWidget(QWidget):
    """Full-Screen edge-to-edge weekly timetable and schedule management screen."""

    back_requested = Signal()
    ambient_requested = Signal()
    open_debrief_requested = Signal()
    open_switch_user_requested = Signal()
    subject_selected = Signal(str)
    start_focus_requested = Signal(str, int)
    start_todo_focus_requested = Signal(object, int)
    timetable_changed = Signal(list)  # list[AcademicSession]
    open_import_export_requested = Signal()
    open_tasks_requested = Signal()
    open_settings_requested = Signal()
    lock_requested = Signal()

    DEFAULT_TIME_SLOTS = [
        ("08:00", "09:30", "08:00 - 09:30"),
        ("09:40", "11:10", "09:40 - 11:10"),
        ("11:15", "12:45", "11:15 - 12:45"),
        ("13:30", "15:00", "13:30 - 15:00"),
        ("15:10", "16:40", "15:10 - 16:40"),
    ]
    TIME_SLOTS = DEFAULT_TIME_SLOTS  # Backward compatibility alias

    DAYS = [
        ("Lun", "MONDAY"),
        ("Mar", "TUESDAY"),
        ("Mer", "WEDNESDAY"),
        ("Jeu", "THURSDAY"),
        ("Ven", "FRIDAY"),
        ("Sam", "SATURDAY"),
    ]

    def _get_active_time_slots(self) -> list[tuple[str, str, str]]:
        """Collect all active time slots merging defaults and any extra session times."""
        slots_dict: dict[str, tuple[str, str, str]] = {
            s[0]: s for s in self.DEFAULT_TIME_SLOTS
        }
        for s in self._sessions:
            start_t = s.time_slot.start
            end_t = s.time_slot.end
            if start_t not in slots_dict:
                label_t = f"{start_t} - {end_t}"
                slots_dict[start_t] = (start_t, end_t, label_t)
        return sorted(slots_dict.values(), key=lambda x: x[0])

    def __init__(
        self,
        sessions: list[AcademicSession],
        current_subject: str | None = None,
        parent: QWidget | None = None,
        engine: ScheduleEngine | None = None,
        current_user: str = "Default",
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self._current_user = current_user
        self._sessions = list(sessions)
        self._current_subject = current_subject
        self._now = datetime.now()
        self._current_view_date: date = self._now.date()
        self._debrief_banner_dismissed = False
        self._priority_card_dismissed = False
        self._current_priority_todo: StudyTodo | None = None

        self._build_ui()
        self._refresh_cockpit_banners()

    def set_current_user(self, username: str) -> None:
        """Update user button display label."""
        self._current_user = username
        if hasattr(self, "btn_user"):
            self.btn_user.setText(f"👤 {username}")

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        main_layout.setSpacing(6)

        # ---------------------------------------------------------------------
        # Top Navigation & Header Bar (3 Balanced Clusters)
        # ---------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        # 1. Left Cluster: Student Identity & Evening Rituals
        left_cluster = QHBoxLayout()
        left_cluster.setContentsMargins(0, 0, 0, 0)
        left_cluster.setSpacing(6)

        self.btn_user = QPushButton(f"👤 {self._current_user}")
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
        left_cluster.addWidget(self.btn_user)

        self.btn_debrief = QPushButton("⚡ Debrief")
        self.btn_debrief.setStyleSheet("""
            QPushButton {
                background-color: #14221D;
                color: #34D399;
                border: 1px solid #059669;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #064E3B;
                color: #FFFFFF;
            }
        """)
        self.btn_debrief.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_debrief.clicked.connect(self.open_debrief_requested.emit)
        left_cluster.addWidget(self.btn_debrief)

        self.btn_tasks = QPushButton("✓ Tasks")
        self.btn_tasks.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_tasks.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tasks.clicked.connect(self.open_tasks_requested.emit)
        left_cluster.addWidget(self.btn_tasks)

        header.addLayout(left_cluster)
        header.addStretch(1)

        # 2. Center Cluster: Title & Academic Week Navigator
        center_cluster = QHBoxLayout()
        center_cluster.setContentsMargins(0, 0, 0, 0)
        center_cluster.setSpacing(8)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        lbl_title = QLabel("WEEKLY SCHEDULE")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1.5px;")
        title_col.addWidget(lbl_title)

        self.lbl_sub = QLabel("Click class to inspect · Esc to return")
        self.lbl_sub.setStyleSheet("color: #71717A; font-size: 11px;")
        title_col.addWidget(self.lbl_sub)
        center_cluster.addLayout(title_col)

        # Tactile Week Navigator: [ ‹ ] [ 12 – 17 OCT 2026 ] [ › ] [ Today ]
        self.week_nav_container = QWidget()
        week_layout = QHBoxLayout(self.week_nav_container)
        week_layout.setContentsMargins(0, 0, 0, 0)
        week_layout.setSpacing(4)

        self.btn_prev_week = QPushButton("‹")
        self.btn_prev_week.setFixedSize(26, 26)
        self.btn_prev_week.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev_week.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 13px;
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #27272A;
                color: #FFFFFF;
                border-color: #3F3F46;
            }
        """)
        self.btn_prev_week.clicked.connect(self._on_prev_week)
        week_layout.addWidget(self.btn_prev_week)

        self.lbl_week_range = QLabel(ScheduleEngine.format_week_range(self._current_view_date))
        self.lbl_week_range.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; padding: 0 4px;")
        week_layout.addWidget(self.lbl_week_range)

        self.btn_next_week = QPushButton("›")
        self.btn_next_week.setFixedSize(26, 26)
        self.btn_next_week.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next_week.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 13px;
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #27272A;
                color: #FFFFFF;
                border-color: #3F3F46;
            }
        """)
        self.btn_next_week.clicked.connect(self._on_next_week)
        week_layout.addWidget(self.btn_next_week)

        self.btn_today = QPushButton("Today")
        self.btn_today.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_today.setStyleSheet("""
            QPushButton {
                background-color: #14221D;
                color: #34D399;
                border: 1px solid #059669;
                border-radius: 11px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #064E3B;
                color: #FFFFFF;
            }
        """)
        self.btn_today.clicked.connect(self._on_today_clicked)
        self.btn_today.hide()
        week_layout.addWidget(self.btn_today)

        center_cluster.addWidget(self.week_nav_container)
        header.addLayout(center_cluster)

        header.addStretch(1)

        # 3. Right Cluster: Station Views, View Switcher & Portability Tools
        right_cluster = QHBoxLayout()
        right_cluster.setContentsMargins(0, 0, 0, 0)
        right_cluster.setSpacing(6)

        # Special Period Override Trigger
        self.btn_special_period = QPushButton("⚡ Period Mode")
        self.btn_special_period.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_special_period.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_special_period.setToolTip("Designate special academic periods (day, x days, weeks) that override timetable")
        self.btn_special_period.clicked.connect(self._open_special_period_dialog)
        right_cluster.addWidget(self.btn_special_period)

        self.btn_ambient = QPushButton("⏱ Clock")
        self.btn_ambient.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_ambient.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ambient.clicked.connect(self.ambient_requested.emit)
        right_cluster.addWidget(self.btn_ambient)

        # View Mode Toggle: [ Grid View | Edit Classes ]
        self.btn_mode_grid = QPushButton("Grid View")
        self.btn_mode_grid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_grid.setStyleSheet("""
            QPushButton {
                background-color: #272730;
                color: #FFFFFF;
                border: 1px solid #3F3F4E;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        self.btn_mode_grid.clicked.connect(lambda: self._set_view_mode(0))
        right_cluster.addWidget(self.btn_mode_grid)

        self.btn_mode_edit = QPushButton("Edit Classes")
        self.btn_mode_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_edit.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_mode_edit.clicked.connect(lambda: self._set_view_mode(1))
        right_cluster.addWidget(self.btn_mode_edit)

        # Import / Export Portability Button
        self.btn_portability = QPushButton("⇄ Import / Export")
        self.btn_portability.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_portability.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_portability.clicked.connect(self.open_import_export_requested.emit)
        right_cluster.addWidget(self.btn_portability)

        # Settings & Customization Button
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Settings & Customization")
        self.btn_settings.clicked.connect(self.open_settings_requested.emit)
        right_cluster.addWidget(self.btn_settings)

        # Kiosk Lock Button
        self.btn_lock = QPushButton("🔒")
        self.btn_lock.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_lock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lock.setToolTip("Lock Station (<kbd>L</kbd>)")
        self.btn_lock.clicked.connect(self.lock_requested.emit)
        right_cluster.addWidget(self.btn_lock)

        header.addLayout(right_cluster)
        main_layout.addLayout(header)

        # ---------------------------------------------------------------------
        # Cockpit Ambient Banners (Nightly Debrief, Priority Task, Special Period)
        # ---------------------------------------------------------------------
        self.debrief_banner = self._create_debrief_banner()
        main_layout.addWidget(self.debrief_banner)

        self.priority_task_card = self._create_priority_task_card()
        main_layout.addWidget(self.priority_task_card)

        self.special_period_banner = self._create_special_period_banner()
        main_layout.addWidget(self.special_period_banner)

        # ---------------------------------------------------------------------
        # View Switcher: Stack (0: Visual Grid, 1: Edit Classes)
        # ---------------------------------------------------------------------
        self.view_stack = QStackedWidget(self)

        # Page 0: Visual Calendar Grid
        self.grid_scroll = self._create_grid_view()
        self.view_stack.addWidget(self.grid_scroll)

        # Page 1: Inline Class Editor
        self.editor_widget = self._create_editor_view()
        self.view_stack.addWidget(self.editor_widget)

        main_layout.addWidget(self.view_stack, stretch=1)

    def _create_debrief_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("debriefBanner")
        banner.setMaximumHeight(36)
        banner.setStyleSheet("""
            QFrame#debriefBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0B291E, stop:0.5 #0F2E23, stop:1 #12121A);
                border: 1px solid #059669;
                border-radius: 7px;
            }
        """)
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(12, 3, 10, 3)
        layout.setSpacing(8)

        self.lbl_debrief_title = QLabel("🌙 NIGHTLY DESK DEBRIEF")
        self.lbl_debrief_title.setStyleSheet("color: #34D399; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(self.lbl_debrief_title)

        self.lbl_debrief_sub = QLabel("· Classes attended today! Capture actionable preparation tasks before next week.")
        self.lbl_debrief_sub.setStyleSheet("color: #A7F3D0; font-size: 11px;")
        layout.addWidget(self.lbl_debrief_sub)

        layout.addStretch(1)

        btn_start_debrief = QPushButton("⚡ Start Debrief")
        btn_start_debrief.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_start_debrief.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        btn_start_debrief.clicked.connect(self.open_debrief_requested.emit)
        layout.addWidget(btn_start_debrief)

        btn_dismiss = QPushButton("✕")
        btn_dismiss.setToolTip("Dismiss for now")
        btn_dismiss.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dismiss.setFixedSize(22, 22)
        btn_dismiss.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6EE7B7;
                border: 1px solid transparent;
                border-radius: 11px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
        """)
        btn_dismiss.clicked.connect(self._dismiss_debrief_banner)
        layout.addWidget(btn_dismiss)

        banner.hide()
        return banner

    def _create_priority_task_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("priorityTaskCard")
        card.setMaximumHeight(36)
        card.setStyleSheet("""
            QFrame#priorityTaskCard {
                background-color: #121218;
                border: 1px solid #272736;
                border-left: 3px solid #6366F1;
                border-radius: 7px;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 3, 10, 3)
        layout.setSpacing(8)

        lbl_badge = QLabel("TONIGHT'S PRIORITY")
        lbl_badge.setStyleSheet("""
            background-color: #1E1B4B;
            color: #C7D2FE;
            border: 1px solid #3730A3;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(lbl_badge)

        self.lbl_priority_title = QLabel("")
        self.lbl_priority_title.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 700;")
        layout.addWidget(self.lbl_priority_title)

        self.lbl_priority_due = QLabel("")
        self.lbl_priority_due.setStyleSheet("color: #94A3B8; font-size: 11px;")
        layout.addWidget(self.lbl_priority_due)

        layout.addStretch(1)

        self.btn_priority_focus = QPushButton("▶ 15m Focus")
        self.btn_priority_focus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_priority_focus.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_priority_focus.clicked.connect(self._on_start_priority_focus)
        layout.addWidget(self.btn_priority_focus)

        btn_dismiss_prio = QPushButton("✕")
        btn_dismiss_prio.setToolTip("Dismiss priority task capsule")
        btn_dismiss_prio.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dismiss_prio.setFixedSize(22, 22)
        btn_dismiss_prio.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #818CF8;
                border: 1px solid transparent;
                border-radius: 11px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
        """)
        btn_dismiss_prio.clicked.connect(self._dismiss_priority_card)
        layout.addWidget(btn_dismiss_prio)

        card.hide()
        return card

    def _dismiss_debrief_banner(self) -> None:
        self._debrief_banner_dismissed = True
        if hasattr(self, "debrief_banner"):
            self.debrief_banner.hide()

    def _dismiss_priority_card(self) -> None:
        self._priority_card_dismissed = True
        if hasattr(self, "priority_task_card"):
            self.priority_task_card.hide()

    def _on_start_priority_focus(self) -> None:
        if self._current_priority_todo is not None:
            self.start_todo_focus_requested.emit(self._current_priority_todo, 15)

    def _refresh_cockpit_banners(self) -> None:
        if self.engine is None:
            if hasattr(self, "debrief_banner"):
                self.debrief_banner.hide()
            if hasattr(self, "priority_task_card"):
                self.priority_task_card.hide()
            return

        now = datetime.now()

        # 1. Debrief banner
        if hasattr(self, "debrief_banner"):
            should_prompt = self.engine.should_prompt_nightly_debrief(now)
            if should_prompt and not self._debrief_banner_dismissed:
                self.debrief_banner.show()
            else:
                self.debrief_banner.hide()

        # 2. Priority task card
        if hasattr(self, "priority_task_card"):
            priority_todo = self.engine.get_priority_study_todo(now)
            self._current_priority_todo = priority_todo
            if priority_todo is not None and not self._priority_card_dismissed:
                due_str = priority_todo.due_date.strftime("%a, %b %d at %H:%M")
                if priority_todo.is_overdue(now):
                    due_text = f"· <span style='color: #EF4444; font-weight: 700;'>⚠️ OVERDUE</span> (was due: {due_str})"
                else:
                    due_text = f"· Due: {due_str}"

                self.lbl_priority_title.setText(f"{priority_todo.subject_name} · {priority_todo.title}")
                self.lbl_priority_due.setText(due_text)
                self.priority_task_card.show()
            else:
                self.priority_task_card.hide()

        # 3. Special Period Banner (Overwrites/Overrides: day / x days / weeks / x weeks)
        if hasattr(self, "special_period_banner") and not getattr(self, "_special_period_banner_dismissed", False):
            week_periods = self.engine.get_special_periods_for_week(self._current_view_date)
            if week_periods:
                p = week_periods[0]
                self.lbl_sp_title.setText(f"{p.name.upper()} ({p.duration_label.upper()})")
                if p.overrides_schedule:
                    self.lbl_sp_sub.setText(f"· Active {p.start_date.strftime('%d %b')} – {p.end_date.strftime('%d %b %Y')} · Timetable overridden")
                else:
                    self.lbl_sp_sub.setText(f"· Active {p.start_date.strftime('%d %b')} – {p.end_date.strftime('%d %b %Y')} · Standard timetable in effect")
                self.special_period_banner.show()
            else:
                self.special_period_banner.hide()
        elif hasattr(self, "special_period_banner"):
            self.special_period_banner.hide()

    def _create_special_period_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("specialPeriodBanner")
        banner.setMaximumHeight(36)
        banner.setStyleSheet("""
            QFrame#specialPeriodBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #271406, stop:0.5 #381E09, stop:1 #12121A);
                border: 1px solid #D97706;
                border-radius: 7px;
            }
        """)
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(12, 3, 10, 3)
        layout.setSpacing(8)

        badge = QLabel("⚡ SPECIAL PERIOD")
        badge.setStyleSheet("""
            background-color: #78350F;
            color: #FDE68A;
            border: 1px solid #D97706;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(badge)

        self.lbl_sp_title = QLabel("SPECIAL ACADEMIC PERIOD ACTIVE")
        self.lbl_sp_title.setStyleSheet("color: #FDE68A; font-size: 11px; font-weight: 800;")
        layout.addWidget(self.lbl_sp_title)

        self.lbl_sp_sub = QLabel("· Standard timetable is overridden during this period.")
        self.lbl_sp_sub.setStyleSheet("color: #FCD34D; font-size: 11px;")
        layout.addWidget(self.lbl_sp_sub)

        layout.addStretch(1)

        btn_manage = QPushButton("Manage Periods")
        btn_manage.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_manage.setStyleSheet("""
            QPushButton {
                background-color: #D97706;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #B45309;
            }
        """)
        btn_manage.clicked.connect(self._open_special_period_dialog)
        layout.addWidget(btn_manage)

        btn_dismiss = QPushButton("✕")
        btn_dismiss.setToolTip("Dismiss special period banner")
        btn_dismiss.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dismiss.setFixedSize(22, 22)
        btn_dismiss.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #FCD34D;
                border: 1px solid transparent;
                border-radius: 11px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
        """)
        btn_dismiss.clicked.connect(self._dismiss_special_period_banner)
        layout.addWidget(btn_dismiss)

        banner.hide()
        return banner

    def _dismiss_special_period_banner(self) -> None:
        self._special_period_banner_dismissed = True
        if hasattr(self, "special_period_banner"):
            self.special_period_banner.hide()

    def _open_special_period_dialog(self) -> None:
        from study_station.ui.special_period_dialog import SpecialPeriodDialog
        dialog = SpecialPeriodDialog(engine=self.engine, initial_date=self._current_view_date, parent=self)
        dialog.periods_changed.connect(self._on_periods_changed)
        dialog.exec()

    def _on_periods_changed(self) -> None:
        self._special_period_banner_dismissed = False
        self._refresh_calendar_grid()
        self._refresh_cockpit_banners()

    def refresh_cockpit_banners(self) -> None:
        """Public trigger to re-evaluate debrief and priority banners."""
        self._refresh_cockpit_banners()

    def _set_view_mode(self, mode_idx: int) -> None:
        self.view_stack.setCurrentIndex(mode_idx)
        active_style = """
            QPushButton {
                background-color: #272730;
                color: #FFFFFF;
                border: 1px solid #3F3F4E;
                border-radius: 14px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
        """
        inactive_style = BUTTON_NAV_STYLE

        if mode_idx == 0:
            self.btn_mode_grid.setStyleSheet(active_style)
            self.btn_mode_edit.setStyleSheet(inactive_style)
            self._refresh_cockpit_banners()
        else:
            self.btn_mode_grid.setStyleSheet(inactive_style)
            self.btn_mode_edit.setStyleSheet(active_style)
            if hasattr(self, "debrief_banner"):
                self.debrief_banner.hide()
            if hasattr(self, "priority_task_card"):
                self.priority_task_card.hide()

    # -------------------------------------------------------------------------
    # Visual Calendar Grid View
    # -------------------------------------------------------------------------

    def _create_grid_view(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(6)

        self._refresh_calendar_grid()
        scroll.setWidget(self.grid_container)
        return scroll

    def _on_prev_week(self) -> None:
        self._current_view_date -= timedelta(days=7)
        self._refresh_calendar_grid()

    def _on_next_week(self) -> None:
        self._current_view_date += timedelta(days=7)
        self._refresh_calendar_grid()

    def _on_today_clicked(self) -> None:
        self._current_view_date = datetime.now().date()
        self._refresh_calendar_grid()

    @property
    def current_view_date(self) -> date:
        return self._current_view_date

    def set_view_date(self, target_date: date) -> None:
        self._current_view_date = target_date
        self._refresh_calendar_grid()

    def _refresh_calendar_grid(self) -> None:
        # Update week range label and today button
        week_str = ScheduleEngine.format_week_range(self._current_view_date)
        if hasattr(self, "lbl_week_range"):
            self.lbl_week_range.setText(week_str)

        if hasattr(self, "lbl_sub"):
            if not self._sessions:
                self.lbl_sub.setText("Schedule is empty · Click any '+' slot to add a class, or use Import / Export")
            else:
                self.lbl_sub.setText("Click class to inspect · Esc to return")

        is_current_week = (
            ScheduleEngine.get_week_start(self._current_view_date)
            == ScheduleEngine.get_week_start(datetime.now().date())
        )
        if hasattr(self, "btn_today"):
            self.btn_today.setVisible(not is_current_week)

        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        # Day Headers (Col 0..5) with Real Dates - Left text column removed
        week_dates = ScheduleEngine.get_week_dates(self._current_view_date, days_count=6)
        today_date = datetime.now().date()

        for col_idx, (day_code, _) in enumerate(self.DAYS):
            col_date = week_dates[col_idx]
            is_today = (col_date == today_date)
            sp = self.engine.get_special_period_for_date(col_date) if self.engine else None

            if sp and sp.overrides_schedule:
                today_bg = "background-color: #271406; border: 1px solid #D97706;"
                today_color = "color: #FDE68A;"
                date_num_color = "color: #FCD34D;"
            elif is_today:
                today_color = "color: #34D399;"
                date_num_color = "color: #10B981;"
                today_bg = "background-color: #14221D; border: 1px solid #059669;"
            else:
                today_color = "color: #D4D4D8;"
                date_num_color = "color: #71717A;"
                today_bg = "background-color: #121216; border: 1px solid #222228;"

            day_box = QFrame()
            day_box.setStyleSheet(f"{today_bg}; border-radius: 6px; padding: 4px 8px;")
            day_box_layout = QVBoxLayout(day_box)
            day_box_layout.setContentsMargins(4, 3, 4, 3)
            day_box_layout.setSpacing(2)

            top_row = QHBoxLayout()
            top_row.setContentsMargins(0, 0, 0, 0)

            lbl_day = QLabel(day_code.upper())
            lbl_day.setStyleSheet(f"{today_color}; font-size: 12px; font-weight: 800; letter-spacing: 0.5px;")
            top_row.addWidget(lbl_day)

            if sp:
                sp_badge = QLabel(f"⚡ {sp.period_type.upper()}")
                sp_badge.setStyleSheet("""
                    background-color: #78350F;
                    color: #FDE68A;
                    font-size: 8px;
                    font-weight: 800;
                    padding: 1px 4px;
                    border-radius: 3px;
                """)
                top_row.addWidget(sp_badge)
            elif is_today:
                lbl_badge = QLabel("TODAY")
                lbl_badge.setStyleSheet("""
                    background-color: #064E3B;
                    color: #34D399;
                    font-size: 9px;
                    font-weight: 800;
                    padding: 1px 4px;
                    border-radius: 3px;
                """)
                top_row.addWidget(lbl_badge)

            top_row.addStretch()

            lbl_num = QLabel(f"{col_date.day:02d} {col_date.strftime('%b').upper()}")
            lbl_num.setStyleSheet(f"{date_num_color}; font-size: 11px; font-weight: 700;")
            top_row.addWidget(lbl_num)

            day_box_layout.addLayout(top_row)
            self.grid_layout.addWidget(day_box, 0, col_idx)

        # Dynamic Slot Rows (Row 1..N) - Pure Cells without left text column
        active_slots = self._get_active_time_slots()
        for row_idx, (start_t, end_t, label_t) in enumerate(active_slots, start=1):
            for col_idx, (day_code, _) in enumerate(self.DAYS):
                col_date = week_dates[col_idx]
                is_today = (col_date == today_date)
                sp = self.engine.get_special_period_for_date(col_date) if self.engine else None
                is_overridden = bool(sp and sp.overrides_schedule)
                override_lbl = sp.name if sp else ""

                matching = [
                    s for s in self._sessions
                    if s.day.lower() == day_code.lower()
                    and s.time_slot.start == start_t
                ]

                if matching:
                    session = matching[0]
                    now_str = datetime.now().strftime("%H:%M")
                    is_current_session = (
                        is_today
                        and session.time_slot.start <= now_str <= session.time_slot.end
                    )
                    card = ClassGridCard(
                        session,
                        is_current=is_current_session,
                        engine=self.engine,
                        is_overridden=is_overridden,
                        override_label=override_lbl,
                    )
                    card.clicked_session_card.connect(
                        lambda s=session: QTimer.singleShot(0, lambda: self._open_session_manager(s))
                    )
                    self.grid_layout.addWidget(card, row_idx, col_idx)
                else:
                    empty = EmptyGridSlot(day_code=day_code, start_time=start_t, end_time=end_t)
                    empty.clicked_slot.connect(self._open_add_slot_dialog)
                    self.grid_layout.addWidget(empty, row_idx, col_idx)

        # Equal column distribution across the 6 days
        for i in range(len(self.DAYS)):
            self.grid_layout.setColumnStretch(i, 1)

        # Equal row stretch for all slot rows
        self.grid_layout.setRowStretch(0, 0)
        for r in range(1, len(active_slots) + 1):
            self.grid_layout.setRowStretch(r, 1)

        # Maintain minimum comfortable height to enable smooth scrolling when window is constrained
        min_slot_height = 86
        min_total_height = 40 + len(active_slots) * (min_slot_height + 6) + 10
        self.grid_container.setMinimumHeight(min_total_height)

        if hasattr(self, "btn_special_period") and self.engine is not None:
            active_periods = self.engine.get_special_periods_for_week(self._current_view_date)
            if active_periods:
                p = active_periods[0]
                self.btn_special_period.setText(f"⚡ {p.duration_label.upper()}: {p.name}")
                self.btn_special_period.setStyleSheet("""
                    QPushButton {
                        background-color: #2D1B06;
                        color: #FCD34D;
                        border: 1px solid #D97706;
                        border-radius: 14px;
                        padding: 6px 12px;
                        font-size: 11px;
                        font-weight: 800;
                    }
                    QPushButton:hover {
                        background-color: #78350F;
                        color: #FFFFFF;
                    }
                """)
            else:
                self.btn_special_period.setText("⚡ Period Mode")
                self.btn_special_period.setStyleSheet(BUTTON_NAV_STYLE)

        self._refresh_cockpit_banners()

    # -------------------------------------------------------------------------
    # Inline Class Editor View
    # -------------------------------------------------------------------------

    def _create_editor_view(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(12)

        # 1. Header Toolbar
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(1)
        self.lbl_editor_title = QLabel("SCHEDULED SESSIONS")
        self.lbl_editor_title.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800; letter-spacing: 1.2px;")
        title_layout.addWidget(self.lbl_editor_title)

        lbl_editor_hint = QLabel("Select class to inspect, edit, or delete · Use + Add Class to schedule a session")
        lbl_editor_hint.setStyleSheet("color: #71717A; font-size: 11px;")
        title_layout.addWidget(lbl_editor_hint)
        top_row.addLayout(title_layout)

        top_row.addSpacing(10)

        # Search / filter box
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍 Filter classes...")
        self.txt_filter.setStyleSheet("""
            QLineEdit {
                background-color: #18181E;
                color: #FFFFFF;
                border: 1px solid #27272E;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        self.txt_filter.textChanged.connect(self._filter_table_rows)
        top_row.addWidget(self.txt_filter, stretch=1)

        # Primary Modal "+ Add Class" button
        self.btn_top_add = QPushButton("+ Add Class")
        self.btn_top_add.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_top_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_top_add.clicked.connect(self._open_new_class_dialog)
        top_row.addWidget(self.btn_top_add)

        # "Edit Selected" button
        self.btn_edit_selected = QPushButton("Edit Selected")
        self.btn_edit_selected.setStyleSheet(BUTTON_NAV_STYLE + """
            QPushButton:disabled { color: #3F3F46; border-color: #1E1E26; background-color: #0E0E12; }
        """)
        self.btn_edit_selected.setEnabled(False)
        self.btn_edit_selected.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit_selected.clicked.connect(self._on_edit_selected_session)
        top_row.addWidget(self.btn_edit_selected)

        # "Delete Selected" button
        self.btn_delete_session = QPushButton("Delete Selected")
        self.btn_delete_session.setStyleSheet(BUTTON_DANGER_STYLE + """
            QPushButton:disabled { color: #3F3F46; border-color: #1E1E26; background-color: #0E0E12; }
        """)
        self.btn_delete_session.setEnabled(False)
        self.btn_delete_session.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete_session.clicked.connect(self._on_delete_session)
        top_row.addWidget(self.btn_delete_session)

        # "Empty Schedule" button
        self.btn_clear_schedule = QPushButton("🗑 Empty Schedule")
        self.btn_clear_schedule.setStyleSheet(BUTTON_DANGER_STYLE + """
            QPushButton:disabled { color: #3F3F46; border-color: #1E1E26; background-color: #0E0E12; }
        """)
        self.btn_clear_schedule.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_schedule.setToolTip("Clear all scheduled classes for this user")
        self.btn_clear_schedule.clicked.connect(self._on_clear_schedule)
        top_row.addWidget(self.btn_clear_schedule)

        layout.addLayout(top_row)

        # 2. Modern Table of sessions
        self.table_sessions = QTableWidget()
        self.table_sessions.setColumnCount(6)
        header_labels = ["DAY", "TIME", "SUBJECT", "TYPE", "LOCATION", "ACTIONS"]
        self.table_sessions.setHorizontalHeaderLabels(header_labels)
        for c in range(len(header_labels)):
            item = self.table_sessions.horizontalHeaderItem(c)
            if item:
                if c == 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table_sessions.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_sessions.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_sessions.setShowGrid(False)
        self.table_sessions.verticalHeader().setVisible(False)
        self.table_sessions.setStyleSheet("""
            QTableWidget {
                background-color: #121216;
                color: #F4F4F6;
                border: 1px solid #222228;
                border-radius: 10px;
                selection-background-color: #222230;
                outline: none;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #1C1C24;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #16161C;
                color: #71717A;
                font-size: 11px;
                font-weight: 700;
                padding: 10px 8px;
                border: none;
                border-bottom: 1px solid #27272A;
                letter-spacing: 0.8px;
            }
        """)

        header = self.table_sessions.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_sessions.setColumnWidth(0, 70)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_sessions.setColumnWidth(1, 140)

        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table_sessions.setColumnWidth(3, 90)

        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table_sessions.setColumnWidth(4, 110)

        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table_sessions.setColumnWidth(5, 130)

        self.table_sessions.cellDoubleClicked.connect(self._on_table_cell_double_clicked)
        layout.addWidget(self.table_sessions, stretch=1)

        # 3. Quick Add Bar retained headlessly for backwards compatibility & test suite
        self.quick_add_bar = QFrame(container)
        self.quick_add_bar.setObjectName("quickAddBar")
        bar_layout = QVBoxLayout(self.quick_add_bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(6)

        bar_header = QHBoxLayout()
        lbl_quick_title = QLabel("QUICK INLINE ADD")
        bar_header.addWidget(lbl_quick_title)

        self.lbl_quick_status = QLabel("")
        bar_header.addWidget(self.lbl_quick_status)
        bar_layout.addLayout(bar_header)

        form_row = QHBoxLayout()
        self.cmb_day = QComboBox()
        for d in ("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"):
            self.cmb_day.addItem(d)
        form_row.addWidget(self.cmb_day)

        self.cmb_preset = QComboBox()
        self.cmb_preset.addItem("08:00 – 09:30")
        self.cmb_preset.addItem("09:40 – 11:10")
        self.cmb_preset.addItem("11:15 – 12:45")
        self.cmb_preset.addItem("13:30 – 15:00")
        self.cmb_preset.addItem("15:10 – 16:40")
        self.cmb_preset.addItem("Custom...")
        self.cmb_preset.currentIndexChanged.connect(self._on_preset_slot_changed)
        form_row.addWidget(self.cmb_preset)

        self.txt_start = QLineEdit("08:00")
        form_row.addWidget(self.txt_start)

        self.txt_end = QLineEdit("09:30")
        form_row.addWidget(self.txt_end)

        self.txt_subject = QLineEdit()
        form_row.addWidget(self.txt_subject)

        self.cmb_core = QComboBox()
        for c in ("COURS", "TD", "TP", "CI"):
            self.cmb_core.addItem(c)
        form_row.addWidget(self.cmb_core)

        self.txt_location = QLineEdit()
        form_row.addWidget(self.txt_location)

        self.btn_add_session = QPushButton("+ Add Class")
        self.btn_add_session.clicked.connect(self._on_add_session)
        form_row.addWidget(self.btn_add_session)

        bar_layout.addLayout(form_row)
        self.quick_add_bar.hide()

        self._refresh_table()
        self.table_sessions.selectionModel().selectionChanged.connect(self._update_selection_buttons)
        self._update_selection_buttons()
        return container

    def _update_selection_buttons(self) -> None:
        """Enable/disable row-action buttons based on table row selection."""
        has_sel = bool(self.table_sessions.selectionModel().selectedRows())
        self.btn_edit_selected.setEnabled(has_sel)
        self.btn_delete_session.setEnabled(has_sel)
        if hasattr(self, "btn_clear_schedule"):
            self.btn_clear_schedule.setEnabled(len(self._sessions) > 0)

    def _on_preset_slot_changed(self, idx: int) -> None:
        preset_map = {
            0: ("08:00", "09:30"),
            1: ("09:40", "11:10"),
            2: ("11:15", "12:45"),
            3: ("13:30", "15:00"),
            4: ("15:10", "16:40"),
        }
        if idx in preset_map:
            s, e = preset_map[idx]
            self.txt_start.setText(s)
            self.txt_end.setText(e)

    def _open_new_class_dialog(self) -> None:
        existing_names = sorted({s.subject.name for s in self._sessions})
        dialog = ClassSessionDialog(
            session=None,
            default_day="Lun",
            default_start="08:00",
            default_end="09:30",
            existing_subjects=existing_names,
            parent=self,
        )
        dialog.session_saved.connect(self._on_session_edited)
        dialog.exec()

    def _on_edit_selected_session(self) -> None:
        selected_rows = self.table_sessions.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        if 0 <= row_idx < len(self._sessions):
            self._open_session_manager(self._sessions[row_idx])

    def _on_table_cell_double_clicked(self, row: int, col: int) -> None:
        if 0 <= row < len(self._sessions):
            self._open_session_manager(self._sessions[row])

    def _filter_table_rows(self, query: str) -> None:
        q = query.strip().lower()
        for row in range(self.table_sessions.rowCount()):
            day_text = self.table_sessions.item(row, 0).text().lower() if self.table_sessions.item(row, 0) else ""
            time_text = self.table_sessions.item(row, 1).text().lower() if self.table_sessions.item(row, 1) else ""
            subj_text = self.table_sessions.item(row, 2).text().lower() if self.table_sessions.item(row, 2) else ""
            loc_text = self.table_sessions.item(row, 4).text().lower() if self.table_sessions.item(row, 4) else ""

            match = (not q) or (q in day_text) or (q in time_text) or (q in subj_text) or (q in loc_text)
            self.table_sessions.setRowHidden(row, not match)

    def _refresh_table(self) -> None:
        # Cleanly remove and destroy existing cell widgets to prevent orphaned viewport overlays
        for r in range(self.table_sessions.rowCount()):
            for c in range(self.table_sessions.columnCount()):
                w = self.table_sessions.cellWidget(r, c)
                if w is not None:
                    self.table_sessions.removeCellWidget(r, c)
                    w.setParent(None)
                    w.deleteLater()
        self.table_sessions.clearContents()

        self._sessions.sort(key=lambda s: (s.day_index, s.time_slot.start))
        self.table_sessions.setRowCount(len(self._sessions))

        for row, s in enumerate(self._sessions):
            self.table_sessions.setRowHeight(row, 44)

            # Day
            day_item = QTableWidgetItem(s.day.upper())
            day_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sessions.setItem(row, 0, day_item)

            # Time
            time_str = f"{s.time_slot.start} – {s.time_slot.end}"
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sessions.setItem(row, 1, time_item)

            # Subject
            clean_name = ScheduleEngine.clean_subject_name(s.subject.name)
            subj_item = QTableWidgetItem(clean_name)
            self.table_sessions.setItem(row, 2, subj_item)

            # Type
            core_upper = s.subject.core.upper()
            core_item = QTableWidgetItem(core_upper)
            core_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sessions.setItem(row, 3, core_item)

            # Location
            loc_item = QTableWidgetItem(s.location or "—")
            loc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sessions.setItem(row, 4, loc_item)

            # Actions Column
            action_cell = QWidget()
            cell_layout = QHBoxLayout(action_cell)
            cell_layout.setContentsMargins(4, 4, 4, 4)
            cell_layout.setSpacing(6)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("✏ Edit")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setFixedHeight(26)
            btn_edit.setMinimumWidth(64)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #272732;
                    color: #FFFFFF;
                    border: 1px solid #3F3F4A;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #38BDF8;
                    color: #000000;
                    border-color: #38BDF8;
                }
            """)
            btn_edit.clicked.connect(lambda _, sess=s: self._open_session_manager(sess))
            cell_layout.addWidget(btn_edit)

            btn_del = QPushButton("🗑")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setFixedSize(28, 26)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #1A1A22;
                    color: #F87171;
                    border: 1px solid #2E2E38;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #EF4444;
                    color: #FFFFFF;
                    border-color: #EF4444;
                }
            """)
            btn_del.clicked.connect(lambda _, sess=s: self._on_session_deleted(sess))
            cell_layout.addWidget(btn_del)

            self.table_sessions.setCellWidget(row, 5, action_cell)

        # Re-apply filter if text was typed
        if hasattr(self, "txt_filter") and self.txt_filter.text():
            self._filter_table_rows(self.txt_filter.text())

    def _on_add_session(self) -> None:
        day = self.cmb_day.currentText()
        raw_start = self.txt_start.text().strip()
        raw_end = self.txt_end.text().strip()
        subject = self.txt_subject.text().strip()
        core = self.cmb_core.currentText()
        location = self.txt_location.text().strip()

        if not subject:
            self.lbl_quick_status.setText("⚠️ Please enter a subject name")
            self.lbl_quick_status.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 600;")
            self.txt_subject.setFocus()
            return

        start = normalize_time_str(raw_start)
        end = normalize_time_str(raw_end)

        if not start or not end:
            self.lbl_quick_status.setText("⚠️ Invalid time format (use HH:MM)")
            self.lbl_quick_status.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 600;")
            return

        if start >= end:
            self.lbl_quick_status.setText("⚠️ Start time must be before end time")
            self.lbl_quick_status.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 600;")
            return

        session = AcademicSession(
            day=day,
            time_slot=TimeSlot(start=start, end=end),
            subject=Subject(name=subject, core=core),
            location=location,
        )
        self._sessions.append(session)
        self._refresh_table()
        self._refresh_calendar_grid()
        self.timetable_changed.emit(self._sessions)

        self.lbl_quick_status.setText("✓ Class added successfully!")
        self.lbl_quick_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600;")

        self.txt_subject.clear()
        self.txt_location.clear()

    def _on_delete_session(self) -> None:
        selected_rows = self.table_sessions.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        if 0 <= row_idx < len(self._sessions):
            del self._sessions[row_idx]
            self._refresh_table()
            self._refresh_calendar_grid()
            self.timetable_changed.emit(self._sessions)

    def _on_clear_schedule(self) -> None:
        """Clear all classes from the schedule with student confirmation."""
        if not self._sessions:
            QMessageBox.information(
                self,
                "Schedule Empty",
                "Your schedule is already empty. There are no classes to clear.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Empty Schedule",
            "Are you sure you want to clear all classes from your schedule?\n\nThis will remove all scheduled sessions for the current profile. This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._sessions.clear()
            self._refresh_table()
            self._refresh_calendar_grid()
            self._update_selection_buttons()
            self.timetable_changed.emit([])

    def _open_session_manager(self, session: AcademicSession) -> None:
        if self.engine is not None:
            sheet = SubjectPreparationSheet(session, self.engine, parent=self)
            sheet.start_task_focus_requested.connect(self.start_todo_focus_requested.emit)
            sheet.start_subject_focus_requested.connect(self.start_focus_requested.emit)
            sheet.session_modified.connect(self._on_session_edited)
            sheet.session_deleted.connect(self._on_session_deleted)
            sheet.todo_changed.connect(lambda: (self._refresh_calendar_grid(), self._refresh_cockpit_banners()))
            sheet.exec()
            self._refresh_calendar_grid()
            self._refresh_cockpit_banners()
            return

        existing_names = sorted({s.subject.name for s in self._sessions})
        dialog = ClassSessionDialog(session=session, existing_subjects=existing_names, parent=self)
        dialog.start_focus_requested.connect(self._on_session_card_clicked)
        dialog.session_saved.connect(self._on_session_edited)
        dialog.session_deleted.connect(self._on_session_deleted)
        dialog.exec()

    def _open_add_slot_dialog(self, day_code: str, start_t: str, end_t: str) -> None:
        existing_names = sorted({s.subject.name for s in self._sessions})
        dialog = ClassSessionDialog(
            session=None,
            default_day=day_code,
            default_start=start_t,
            default_end=end_t,
            existing_subjects=existing_names,
            parent=self,
        )
        dialog.session_saved.connect(self._on_session_edited)
        dialog.exec()

    def _on_session_edited(self, old_session: AcademicSession | None, new_session: AcademicSession) -> None:
        if old_session is not None:
            if old_session in self._sessions:
                idx = self._sessions.index(old_session)
                self._sessions[idx] = new_session
            else:
                matched = False
                for i, s in enumerate(self._sessions):
                    if s.day.lower() == old_session.day.lower() and s.time_slot.start == old_session.time_slot.start:
                        self._sessions[i] = new_session
                        matched = True
                        break
                if not matched:
                    self._sessions.append(new_session)
        else:
            self._sessions.append(new_session)

        self._refresh_table()
        self._refresh_calendar_grid()
        self.timetable_changed.emit(self._sessions)

    def _on_session_deleted(self, session: AcademicSession) -> None:
        if session in self._sessions:
            self._sessions.remove(session)
            self._refresh_table()
            self._refresh_calendar_grid()
            self.timetable_changed.emit(self._sessions)

    def _on_session_card_clicked(self, subject_name: str) -> None:
        self.subject_selected.emit(subject_name)
        self.back_requested.emit()

    def _open_original_doc(self) -> None:
        from study_station.core.resources import get_doc_path
        doc_path = get_doc_path("grid.pdf")
        if doc_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(doc_path)))

    def update_sessions(self, sessions: list[AcademicSession]) -> None:
        self._sessions = list(sessions)
        self._refresh_table()
        self._refresh_calendar_grid()
        self._refresh_cockpit_banners()

    def apply_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        bg_hex = getattr(settings, "bg_color", "") or "#09090B"
        self.setStyleSheet(f"background-color: {bg_hex};")
        self._refresh_calendar_grid()
        self._refresh_cockpit_banners()

"""Full-Screen Weekly Schedule & Class Editor view for Study Station.

Provides an immersive, edge-to-edge weekly calendar grid modeled directly after
university schedule (docs/grid.pdf / Google Calendar) with an inline session editor.
Eliminates floating dialog rims, text-peeking, and modal-on-modal stacking.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from PySide6.QtCore import QPoint, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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
    Subject,
    TimeSlot,
)
from study_station.ui.class_session_dialog import ClassSessionDialog
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
        self.setMinimumHeight(74)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText("+")
        self.setStyleSheet("""
            EmptyGridSlot {
                background-color: #0E0E12;
                border: 1px solid #18181F;
                border-radius: 8px;
                color: #27272E;
                font-size: 18px;
                font-weight: 400;
            }
            EmptyGridSlot:hover {
                background-color: #14141C;
                border: 1px dashed #3F3F4E;
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
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.is_current = is_current
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        clean_name = ScheduleEngine.clean_subject_name(session.subject.name)
        core_type = session.subject.core.upper()
        room = session.location or "Class"

        # Refined calm badge colors
        core_colors = {
            "TP": ("#064E3B", "#6EE7B7"),      # Emerald
            "COURS": ("#1E293B", "#93C5FD"),   # Slate Blue
            "TD": ("#2E1065", "#C4B5FD"),      # Muted Indigo
            "CI": ("#451A03", "#FCD34D"),      # Warm Amber
        }
        bg_badge, fg_badge = core_colors.get(core_type, ("#1E1E24", "#A1A1AA"))

        current_border = "border: 2px solid #10B981;" if is_current else "border: 1px solid #222228;"
        current_bg = "background-color: #14221D;" if is_current else "background-color: #121216;"

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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

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

        if is_current:
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
        lbl_name.setFont(get_modern_font("eva_display", 12, QFont.Weight.Bold))
        lbl_name.setWordWrap(True)
        lbl_name.setStyleSheet("color: #F4F4F6; font-size: 12px; font-weight: 700;")
        layout.addWidget(lbl_name)

        layout.addStretch()

        # Time footer
        lbl_time = QLabel(f"{session.time_slot.start} - {session.time_slot.end}")
        lbl_time.setFont(get_modern_font("mono", 10, QFont.Weight.Medium))
        lbl_time.setStyleSheet("color: #52525B; font-size: 10px;")
        self.clicked.connect(self._on_card_clicked)

    def _on_card_clicked(self) -> None:
        self.clicked_session_card.emit(self.session)
        self.clicked_session.emit(self.session.subject.name)


class ScheduleScreenWidget(QWidget):
    """Full-Screen edge-to-edge weekly timetable and schedule management screen."""

    back_requested = Signal()
    subject_selected = Signal(str)
    timetable_changed = Signal(list)  # list[AcademicSession]

    TIME_SLOTS = [
        ("08:00", "09:30", "08h - 09h30"),
        ("09:40", "11:10", "09h40 - 11h10"),
        ("11:15", "12:45", "11h15 - 12h45"),
        ("13:30", "15:00", "13h30 - 15h00"),
        ("15:10", "16:40", "15h10 - 16h40"),
    ]

    DAYS = [
        ("Lun", "MONDAY"),
        ("Mar", "TUESDAY"),
        ("Mer", "WEDNESDAY"),
        ("Jeu", "THURSDAY"),
        ("Ven", "FRIDAY"),
        ("Sam", "SATURDAY"),
    ]

    def __init__(
        self,
        sessions: list[AcademicSession],
        current_subject: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._sessions = list(sessions)
        self._current_subject = current_subject
        self._now = datetime.now()
        self._current_view_date: date = self._now.date()

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(14)

        # ---------------------------------------------------------------------
        # Top Navigation & Header Bar
        # ---------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(14)

        btn_back = QPushButton("← Station")
        btn_back.setStyleSheet(BUTTON_NAV_STYLE)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self.back_requested.emit)
        header.addWidget(btn_back)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("WEEKLY SCHEDULE")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 1.5px;")
        title_col.addWidget(lbl_title)

        lbl_sub = QLabel("Click any class block to set active subject · Press Esc to return")
        lbl_sub.setStyleSheet("color: #71717A; font-size: 12px;")
        title_col.addWidget(lbl_sub)
        header.addLayout(title_col)

        header.addSpacing(16)

        # Tactile Week Navigator: [ ‹ ] [ 12 – 17 OCT 2026 ] [ › ] [ Today ]
        self.week_nav_container = QWidget()
        week_layout = QHBoxLayout(self.week_nav_container)
        week_layout.setContentsMargins(0, 0, 0, 0)
        week_layout.setSpacing(6)

        self.btn_prev_week = QPushButton("‹")
        self.btn_prev_week.setFixedSize(28, 28)
        self.btn_prev_week.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev_week.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 14px;
                font-size: 16px;
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
        self.lbl_week_range.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; padding: 0 4px;")
        week_layout.addWidget(self.lbl_week_range)

        self.btn_next_week = QPushButton("›")
        self.btn_next_week.setFixedSize(28, 28)
        self.btn_next_week.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next_week.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 14px;
                font-size: 16px;
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
                border-radius: 12px;
                padding: 4px 10px;
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

        header.addWidget(self.week_nav_container)

        header.addStretch()

        # View Mode Toggle: [ Grid View | Edit Classes ]
        self.btn_mode_grid = QPushButton("Grid View")
        self.btn_mode_grid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_grid.setStyleSheet("""
            QPushButton {
                background-color: #272730;
                color: #FFFFFF;
                border: 1px solid #3F3F4E;
                border-radius: 14px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        self.btn_mode_grid.clicked.connect(lambda: self._set_view_mode(0))
        header.addWidget(self.btn_mode_grid)

        self.btn_mode_edit = QPushButton("Edit Classes")
        self.btn_mode_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_edit.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_mode_edit.clicked.connect(lambda: self._set_view_mode(1))
        header.addWidget(self.btn_mode_edit)

        # Original PDF Button
        btn_pdf = QPushButton("Original PDF")
        btn_pdf.setStyleSheet(BUTTON_NAV_STYLE)
        btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pdf.clicked.connect(self._open_original_doc)
        header.addWidget(btn_pdf)

        main_layout.addLayout(header)

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
        else:
            self.btn_mode_grid.setStyleSheet(inactive_style)
            self.btn_mode_edit.setStyleSheet(active_style)

    # -------------------------------------------------------------------------
    # Visual Calendar Grid View
    # -------------------------------------------------------------------------

    def _create_grid_view(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(8)

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

        # Corner: TIME
        lbl_corner = QLabel("TIME")
        lbl_corner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_corner.setStyleSheet("color: #52525B; font-size: 11px; font-weight: 800; letter-spacing: 1px;")
        self.grid_layout.addWidget(lbl_corner, 0, 0)

        # Day Headers (Col 1..6) with Real Dates
        week_dates = ScheduleEngine.get_week_dates(self._current_view_date, days_count=6)
        today_date = datetime.now().date()

        for col_idx, (day_code, _) in enumerate(self.DAYS, start=1):
            col_date = week_dates[col_idx - 1]
            is_today = (col_date == today_date)

            today_color = "color: #34D399;" if is_today else "color: #D4D4D8;"
            date_num_color = "color: #10B981;" if is_today else "color: #71717A;"
            today_bg = (
                "background-color: #14221D; border: 1px solid #059669;"
                if is_today
                else "background-color: #121216; border: 1px solid #222228;"
            )

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

            if is_today:
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

        # Slot Rows (Row 1..5)
        for row_idx, (start_t, end_t, label_t) in enumerate(self.TIME_SLOTS, start=1):
            time_lbl = QLabel(label_t)
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            time_lbl.setStyleSheet("color: #71717A; font-size: 11px; font-family: monospace; font-weight: 600;")
            time_lbl.setFixedWidth(100)
            self.grid_layout.addWidget(time_lbl, row_idx, 0)

            for col_idx, (day_code, _) in enumerate(self.DAYS, start=1):
                col_date = week_dates[col_idx - 1]
                is_today = (col_date == today_date)

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
                    card = ClassGridCard(session, is_current=is_current_session)
                    card.clicked_session_card.connect(self._open_session_manager)
                    self.grid_layout.addWidget(card, row_idx, col_idx)
                else:
                    empty = EmptyGridSlot(day_code=day_code, start_time=start_t, end_time=end_t)
                    empty.clicked_slot.connect(self._open_add_slot_dialog)
                    self.grid_layout.addWidget(empty, row_idx, col_idx)

        self.grid_layout.setColumnStretch(0, 1)
        for i in range(1, 7):
            self.grid_layout.setColumnStretch(i, 3)

    # -------------------------------------------------------------------------
    # Inline Class Editor View
    # -------------------------------------------------------------------------

    def _create_editor_view(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Top row: Info & Delete button
        top_row = QHBoxLayout()
        lbl_info = QLabel("Manage your weekly schedule sessions:")
        lbl_info.setStyleSheet("color: #A1A1AA; font-size: 13px; font-weight: 500;")
        top_row.addWidget(lbl_info)

        top_row.addStretch()

        self.btn_delete_session = QPushButton("Delete Selected")
        self.btn_delete_session.setStyleSheet(BUTTON_DANGER_STYLE)
        self.btn_delete_session.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete_session.clicked.connect(self._on_delete_session)
        top_row.addWidget(self.btn_delete_session)
        layout.addLayout(top_row)

        # Table of sessions
        self.table_sessions = QTableWidget()
        self.table_sessions.setColumnCount(5)
        self.table_sessions.setHorizontalHeaderLabels(["Day", "Time", "Subject", "Type", "Location"])
        header = self.table_sessions.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table_sessions, stretch=1)

        # Add Session Bar
        add_bar = QFrame()
        add_bar.setStyleSheet("""
            QFrame {
                background-color: #121216;
                border: 1px solid #222228;
                border-radius: 10px;
                padding: 6px;
            }
        """)
        bar_layout = QHBoxLayout(add_bar)
        bar_layout.setContentsMargins(8, 6, 8, 6)
        bar_layout.setSpacing(8)

        self.cmb_day = QComboBox()
        for d in ("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"):
            self.cmb_day.addItem(d)
        self.cmb_day.setFixedWidth(70)
        bar_layout.addWidget(self.cmb_day)

        self.txt_start = QLineEdit()
        self.txt_start.setPlaceholderText("08:00")
        self.txt_start.setFixedWidth(90)
        bar_layout.addWidget(self.txt_start)

        self.txt_end = QLineEdit()
        self.txt_end.setPlaceholderText("09:30")
        self.txt_end.setFixedWidth(90)
        bar_layout.addWidget(self.txt_end)

        self.txt_subject = QLineEdit()
        self.txt_subject.setPlaceholderText("Subject Name")
        bar_layout.addWidget(self.txt_subject, stretch=1)

        self.cmb_core = QComboBox()
        for c in ("TP", "COURS", "TD", "CI"):
            self.cmb_core.addItem(c)
        self.cmb_core.setFixedWidth(85)
        bar_layout.addWidget(self.cmb_core)

        self.txt_location = QLineEdit()
        self.txt_location.setPlaceholderText("Room/Lab")
        self.txt_location.setFixedWidth(90)
        bar_layout.addWidget(self.txt_location)

        self.btn_add_session = QPushButton("+ Add Class")
        self.btn_add_session.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_add_session.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_session.clicked.connect(self._on_add_session)
        bar_layout.addWidget(self.btn_add_session)

        layout.addWidget(add_bar)
        self._refresh_table()
        return container

    def _refresh_table(self) -> None:
        self._sessions.sort(key=lambda s: (s.day_index, s.time_slot.start))
        self.table_sessions.setRowCount(len(self._sessions))

        for row, s in enumerate(self._sessions):
            day_item = QTableWidgetItem(s.day)
            day_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sessions.setItem(row, 0, day_item)

            time_str = f"{s.time_slot.start} - {s.time_slot.end}"
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sessions.setItem(row, 1, time_item)

            clean_name = ScheduleEngine.clean_subject_name(s.subject.name)
            self.table_sessions.setItem(row, 2, QTableWidgetItem(clean_name))

            core_item = QTableWidgetItem(s.subject.core)
            core_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sessions.setItem(row, 3, core_item)

            self.table_sessions.setItem(row, 4, QTableWidgetItem(s.location))

    def _on_add_session(self) -> None:
        day = self.cmb_day.currentText()
        start = self.txt_start.text().strip()
        end = self.txt_end.text().strip()
        subject = self.txt_subject.text().strip()
        core = self.cmb_core.currentText()
        location = self.txt_location.text().strip()

        if not start or not end or not subject:
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

    def _open_session_manager(self, session: AcademicSession) -> None:
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
        if old_session is not None and old_session in self._sessions:
            idx = self._sessions.index(old_session)
            self._sessions[idx] = new_session
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
        doc_path = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "grid.pdf"
        if doc_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(doc_path)))

    def update_sessions(self, sessions: list[AcademicSession]) -> None:
        self._sessions = list(sessions)
        self._refresh_table()
        self._refresh_calendar_grid()

"""Special Academic Override Period Dialog for Study Station.

Enables students and faculty to designate special academic periods (day, x days, 1 week, x weeks)
such as Exams / DS weeks, Revision / Dead weeks, Intensive Project Sprints, or Breaks that
overwrite or modify the standard recurring weekly schedule.
"""

from __future__ import annotations
from datetime import date, datetime, timedelta
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import SpecialPeriod
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
)


class SpecialPeriodDialog(QDialog):
    """Modal dialog allowing configuration of Special Academic Periods that overwrite the timetable."""

    periods_changed = Signal()

    TYPE_OPTIONS = [
        ("exam", "📝 Exam / DS Period"),
        ("revision", "📖 Revision / Dead Week"),
        ("intensive", "💻 Intensive Project Sprint"),
        ("holiday", "🏖️ Break / Vacation"),
        ("custom", "⚙️ Custom Override"),
    ]

    def __init__(
        self,
        engine: ScheduleEngine,
        parent: QWidget | None = None,
        initial_date: date | None = None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self._initial_date = initial_date or date.today()

        self.setFixedSize(680, 680)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._refresh_periods_list()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().rect()
            self.move(parent_rect.center() - self.rect().center())

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.container = QFrame(self)
        self.container.setObjectName("dialogContainer")
        self.container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #121216;
                border: 1px solid #27272A;
                border-radius: 14px;
            }
        """)
        main_layout.addWidget(self.container)

        content = QVBoxLayout(self.container)
        content.setContentsMargins(24, 20, 24, 20)
        content.setSpacing(14)

        # ---------------------------------------------------------------------
        # 1. Header: Title, Subtitle, Close
        # ---------------------------------------------------------------------
        header = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        lbl_title = QLabel("ACADEMIC PERIOD OVERRIDES")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1px;")
        title_row.addWidget(lbl_title)

        lbl_badge = QLabel("⚡ OVERWRITE ENGINE")
        lbl_badge.setStyleSheet("""
            background-color: #2E1065;
            color: #C084FC;
            border: 1px solid #7E22CE;
            border-radius: 4px;
            font-size: 9px;
            font-weight: 800;
            padding: 2px 6px;
            letter-spacing: 0.5px;
        """)
        title_row.addWidget(lbl_badge)
        title_row.addStretch()
        header_text.addLayout(title_row)

        lbl_sub = QLabel("Designate special days or weeks (Exams, Revision, Sprints) that override normal classes")
        lbl_sub.setStyleSheet("color: #71717A; font-size: 11px;")
        header_text.addWidget(lbl_sub)
        header.addLayout(header_text)

        header.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #71717A;
                border: 1px solid #27272A;
                border-radius: 14px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #27272A;
                color: #FFFFFF;
            }
        """)
        btn_close.clicked.connect(self.accept)
        header.addWidget(btn_close)

        content.addLayout(header)

        # Hairline separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #27272A; border: none;")
        content.addWidget(sep)

        # ---------------------------------------------------------------------
        # 2. Creator Card: Presets + Form
        # ---------------------------------------------------------------------
        creator_frame = QFrame()
        creator_frame.setStyleSheet("""
            QFrame {
                background-color: #18181F;
                border: 1px solid #272732;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        creator_layout = QVBoxLayout(creator_frame)
        creator_layout.setContentsMargins(12, 12, 12, 12)
        creator_layout.setSpacing(10)

        # Presets Row
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(6)
        lbl_presets = QLabel("QUICK PRESETS:")
        lbl_presets.setStyleSheet("color: #A1A1AA; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
        presets_layout.addWidget(lbl_presets)

        presets = [
            ("1 Day (Today)", 1),
            ("3 Days (Sprint)", 3),
            ("1 Week (This Week)", 7),
            ("2 Weeks (Exams)", 14),
        ]
        for label, days in presets:
            btn_preset = QPushButton(label)
            btn_preset.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_preset.setStyleSheet("""
                QPushButton {
                    background: #202028;
                    color: #E4E4E7;
                    border: 1px solid #323240;
                    border-radius: 11px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #2A2A38;
                    border-color: #10B981;
                    color: #FFFFFF;
                }
            """)
            btn_preset.clicked.connect(lambda _, d=days: self._apply_preset(d))
            presets_layout.addWidget(btn_preset)

        presets_layout.addStretch()
        creator_layout.addLayout(presets_layout)

        # Inputs Grid
        form_row_1 = QHBoxLayout()
        form_row_1.setSpacing(10)

        # Title
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Period name (e.g. Devoirs Surveillés DS 1, Revision Week)")
        self.txt_name.setStyleSheet("""
            QLineEdit {
                background-color: #121216;
                color: #FFFFFF;
                border: 1px solid #2E2E38;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        form_row_1.addWidget(self.txt_name, stretch=3)

        # Type Combo
        self.combo_type = QComboBox()
        self.combo_type.setStyleSheet("""
            QComboBox {
                background-color: #121216;
                color: #FFFFFF;
                border: 1px solid #2E2E38;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #18181F;
                color: #FFFFFF;
                selection-background-color: #272734;
            }
        """)
        for code, label in self.TYPE_OPTIONS:
            self.combo_type.addItem(label, code)
        form_row_1.addWidget(self.combo_type, stretch=2)
        creator_layout.addLayout(form_row_1)

        # Dates & Duration Row
        form_row_2 = QHBoxLayout()
        form_row_2.setSpacing(8)

        lbl_from = QLabel("From:")
        lbl_from.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 600;")
        form_row_2.addWidget(lbl_from)

        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat("dd MMM yyyy")
        self.date_start.setDate(QDate(self._initial_date.year, self._initial_date.month, self._initial_date.day))
        self.date_start.setStyleSheet("""
            QDateEdit {
                background-color: #121216;
                color: #FFFFFF;
                border: 1px solid #2E2E38;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.date_start.dateChanged.connect(self._update_duration_label)
        form_row_2.addWidget(self.date_start)

        lbl_to = QLabel("To:")
        lbl_to.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 600;")
        form_row_2.addWidget(lbl_to)

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat("dd MMM yyyy")
        # Default to Saturday of this week
        mon = self._initial_date - timedelta(days=self._initial_date.weekday())
        sat = mon + timedelta(days=5)
        self.date_end.setDate(QDate(sat.year, sat.month, sat.day))
        self.date_end.setStyleSheet("""
            QDateEdit {
                background-color: #121216;
                color: #FFFFFF;
                border: 1px solid #2E2E38;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        self.date_end.dateChanged.connect(self._update_duration_label)
        form_row_2.addWidget(self.date_end)

        self.lbl_duration = QLabel("Duration: 1 Week")
        self.lbl_duration.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700; padding-left: 6px;")
        form_row_2.addWidget(self.lbl_duration)
        form_row_2.addStretch()

        creator_layout.addLayout(form_row_2)

        # Checkbox & Create Button
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.chk_overwrite = QCheckBox("Overwrite / suspend standard weekly classes during this period")
        self.chk_overwrite.setChecked(True)
        self.chk_overwrite.setStyleSheet("""
            QCheckBox {
                color: #E4E4E7;
                font-size: 11px;
                font-weight: 600;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid #3F3F4E;
                background-color: #121216;
            }
            QCheckBox::indicator:checked {
                background-color: #10B981;
                border-color: #10B981;
            }
        """)
        action_row.addWidget(self.chk_overwrite, stretch=1)

        self.btn_create = QPushButton("+ Create Special Period")
        self.btn_create.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_create.clicked.connect(self._on_create_clicked)
        action_row.addWidget(self.btn_create)

        creator_layout.addLayout(action_row)
        content.addWidget(creator_frame)

        # ---------------------------------------------------------------------
        # 3. Active / Scheduled Overrides List
        # ---------------------------------------------------------------------
        list_header = QHBoxLayout()
        lbl_list = QLabel("SCHEDULED SPECIAL PERIODS")
        lbl_list.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        list_header.addWidget(lbl_list)

        self.lbl_count_badge = QLabel("0 PERIODS")
        self.lbl_count_badge.setStyleSheet("""
            background: #18181B;
            color: #71717A;
            border: 1px solid #27272A;
            border-radius: 3px;
            font-size: 9px;
            font-weight: 700;
            padding: 1px 5px;
        """)
        list_header.addWidget(self.lbl_count_badge)
        list_header.addStretch()
        content.addLayout(list_header)

        # Scroll container for periods
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: 1px solid #27272A;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #27272A;
                border-radius: 3px;
            }
        """)
        self.periods_container = QWidget()
        self.periods_layout = QVBoxLayout(self.periods_container)
        self.periods_layout.setContentsMargins(8, 8, 8, 8)
        self.periods_layout.setSpacing(6)
        self.scroll_area.setWidget(self.periods_container)
        content.addWidget(self.scroll_area, stretch=1)

        # Bottom Close Row
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        btn_done = QPushButton("Done")
        btn_done.setFixedSize(110, 32)
        btn_done.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_done.clicked.connect(self.accept)
        bottom_row.addWidget(btn_done)
        content.addLayout(bottom_row)

        self._update_duration_label()

    def _apply_preset(self, days: int) -> None:
        today = self._initial_date
        if days == 1:
            start_d = today
            end_d = today
            self.txt_name.setText("Special Exam / Focus Day")
        elif days == 3:
            start_d = today
            end_d = today + timedelta(days=2)
            self.txt_name.setText("Intensive Sprint (3 Days)")
            self.combo_type.setCurrentIndex(2)  # Intensive
        elif days == 7:
            start_d = today - timedelta(days=today.weekday())
            end_d = start_d + timedelta(days=6)
            self.txt_name.setText("Devoirs Surveillés (DS Week)")
            self.combo_type.setCurrentIndex(0)  # Exam
        elif days == 14:
            start_d = today - timedelta(days=today.weekday())
            end_d = start_d + timedelta(days=13)
            self.txt_name.setText("Semester Final Exams (2 Weeks)")
            self.combo_type.setCurrentIndex(0)  # Exam
        else:
            start_d = today
            end_d = today + timedelta(days=days - 1)

        self.date_start.setDate(QDate(start_d.year, start_d.month, start_d.day))
        self.date_end.setDate(QDate(end_d.year, end_d.month, end_d.day))
        self._update_duration_label()

    def _update_duration_label(self) -> None:
        q_start = self.date_start.date()
        q_end = self.date_end.date()
        start_d = date(q_start.year(), q_start.month(), q_start.day())
        end_d = date(q_end.year(), q_end.month(), q_end.day())

        if end_d < start_d:
            self.lbl_duration.setText("⚠️ Invalid date range (End is before Start)")
            self.lbl_duration.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 700;")
            self.btn_create.setEnabled(False)
            return

        self.btn_create.setEnabled(True)
        days = (end_d - start_d).days + 1
        if days == 1:
            dur_str = "1 Day (Single Day Override)"
        elif days in (6, 7):
            dur_str = "1 Week"
        elif days in (13, 14):
            dur_str = "2 Weeks"
        elif days % 7 == 0:
            dur_str = f"{days // 7} Weeks ({days} Days)"
        elif days % 6 == 0:
            dur_str = f"{days // 6} Weeks ({days} Days)"
        elif days < 7:
            dur_str = f"{days} Days"
        else:
            dur_str = f"{days} Days ({days // 7}w {days % 7}d)"

        self.lbl_duration.setText(f"Duration: {dur_str}")
        self.lbl_duration.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700;")

    def _on_create_clicked(self) -> None:
        name = self.txt_name.text().strip()
        if not name:
            name = self.combo_type.currentText()

        q_start = self.date_start.date()
        q_end = self.date_end.date()
        start_d = date(q_start.year(), q_start.month(), q_start.day())
        end_d = date(q_end.year(), q_end.month(), q_end.day())

        period_code = self.combo_type.currentData() or "exam"
        overrides = self.chk_overwrite.isChecked()

        period = SpecialPeriod(
            name=name,
            period_type=period_code,
            start_date=start_d,
            end_date=end_d,
            overrides_schedule=overrides,
        )

        self.engine.add_special_period(period)
        self.txt_name.clear()
        self._refresh_periods_list()
        self.periods_changed.emit()

    def _refresh_periods_list(self) -> None:
        while self.periods_layout.count():
            item = self.periods_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        periods = list(self.engine.special_periods)
        self.lbl_count_badge.setText(f"{len(periods)} PERIODS")

        if not periods:
            empty_lbl = QLabel("No special periods scheduled. Regular weekly timetable is in effect.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #71717A; font-size: 12px; padding: 20px;")
            self.periods_layout.addWidget(empty_lbl)
            return

        for p in periods:
            card = self._create_period_card(p)
            self.periods_layout.addWidget(card)
        self.periods_layout.addStretch()

    def _create_period_card(self, period: SpecialPeriod) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #16161D;
                border: 1px solid #272732;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QFrame:hover {
                background-color: #1A1A24;
                border-color: #383846;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        type_color_map = {
            "exam": ("#78350F", "#FDE68A"),       # Amber
            "revision": ("#581C87", "#E9D5FF"),   # Purple
            "intensive": ("#1E3A8A", "#BFDBFE"),  # Blue
            "holiday": ("#064E3B", "#A7F3D0"),    # Emerald
            "custom": ("#27272A", "#D4D4D8"),     # Neutral
        }
        bg_col, fg_col = type_color_map.get(period.period_type, ("#27272A", "#D4D4D8"))

        badge = QLabel(period.period_type.upper())
        badge.setStyleSheet(f"""
            background-color: {bg_col};
            color: {fg_col};
            border-radius: 4px;
            font-size: 9px;
            font-weight: 800;
            padding: 2px 6px;
        """)
        layout.addWidget(badge)

        col = QVBoxLayout()
        col.setSpacing(2)

        lbl_name = QLabel(period.name)
        lbl_name.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 700;")
        col.addWidget(lbl_name)

        date_range_str = f"{period.start_date.strftime('%d %b %Y')} → {period.end_date.strftime('%d %b %Y')}"
        lbl_meta = QLabel(f"{date_range_str} · {period.duration_label}")
        lbl_meta.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        col.addWidget(lbl_meta)
        layout.addLayout(col, stretch=1)

        if period.overrides_schedule:
            lbl_ovr = QLabel("⚡ OVERWRITES")
            lbl_ovr.setStyleSheet("""
                color: #F59E0B;
                background-color: #2D1B06;
                border: 1px solid #78350F;
                border-radius: 4px;
                font-size: 9px;
                font-weight: 800;
                padding: 2px 6px;
            """)
            layout.addWidget(lbl_ovr)

        btn_del = QPushButton("✕")
        btn_del.setToolTip("Delete special period")
        btn_del.setFixedSize(24, 24)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background: #201315;
                color: #F87171;
                border: 1px solid #5C1D24;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #7F1D1D;
                color: #FFFFFF;
            }
        """)
        btn_del.clicked.connect(lambda _, p_id=period.id: self._on_delete_period(p_id))
        layout.addWidget(btn_del)

        return card

    def _on_delete_period(self, period_id: str) -> None:
        self.engine.delete_special_period(period_id)
        self._refresh_periods_list()
        self.periods_changed.emit()

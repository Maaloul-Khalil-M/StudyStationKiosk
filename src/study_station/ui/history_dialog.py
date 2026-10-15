"""Study History and Cycle Statistics Dialog for Study Station.

Provides a comprehensive, retro-minimal modal viewer for:
1. Overview KPI cards: This Week's review time, Total Study Time, and Cycle Target Completion Rate.
2. Chronological session history with multi-criteria filtering (Subject, Source).
3. In-place session correction (editing duration or subject).
4. Deletion of accidental/mistaken sessions with instant cycle recalculation.
"""

from __future__ import annotations
from datetime import date, datetime, timedelta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import StudyLog
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


def format_minutes_hh_mm(total_minutes: int) -> str:
    """Format minutes into human-readable hours and minutes (e.g. 150 -> '2h 30m')."""
    if total_minutes <= 0:
        return "0m"
    hours = total_minutes // 60
    mins = total_minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours}h {mins:02d}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"


def format_log_timestamp(dt: datetime, ref_date: date | None = None) -> str:
    """Format session timestamp cleanly (Today, Yesterday, or DD Mon YYYY)."""
    today = ref_date or date.today()
    log_date = dt.date()
    time_str = dt.strftime("%H:%M")
    
    if log_date == today:
        return f"Today, {time_str}"
    elif log_date == today - timedelta(days=1):
        return f"Yesterday, {time_str}"
    elif log_date.year == today.year:
        return f"{dt.strftime('%d %b')}, {time_str}"
    else:
        return f"{dt.strftime('%d %b %Y')}, {time_str}"


class DeleteConfirmDialog(QDialog):
    """Custom dark confirmation modal for deleting a study session."""

    def __init__(self, log: StudyLog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Delete Session")
        self.setFixedSize(420, 270)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #141418;
                border: 1px solid #3B1C1C;
                border-radius: 14px;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        lbl_title = QLabel("DELETE STUDY SESSION")
        lbl_title.setStyleSheet("color: #EF4444; font-size: 13px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(lbl_title)

        lbl_msg = QLabel("Remove this session from your records? Logged minutes will be subtracted from the subject's active review cycle.")
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #A1A1AA; font-size: 12px; line-height: 1.4;")
        layout.addWidget(lbl_msg)

        # Summary box
        summary_box = QFrame()
        summary_box.setStyleSheet("""
            QFrame {
                background-color: #1A1A20;
                border: 1px solid #27272E;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        sum_layout = QHBoxLayout(summary_box)
        sum_layout.setContentsMargins(12, 8, 12, 8)
        
        clean_name = ScheduleEngine.clean_subject_name(log.subject_name)
        lbl_subj_info = QLabel(clean_name)
        lbl_subj_info.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600;")
        sum_layout.addWidget(lbl_subj_info, stretch=1)

        lbl_dur_badge = QLabel(f"+{log.duration_minutes}m")
        lbl_dur_badge.setStyleSheet("color: #10B981; font-size: 13px; font-weight: 700;")
        sum_layout.addWidget(lbl_dur_badge)

        layout.addWidget(summary_box)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_confirm = QPushButton("Delete Session")
        btn_confirm.setStyleSheet(BUTTON_DANGER_STYLE)
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm.clicked.connect(self.accept)
        btn_row.addWidget(btn_confirm)

        layout.addLayout(btn_row)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class EditStudyLogDialog(QDialog):
    """Clean modal dialog allowing correction of a logged study session."""

    def __init__(
        self,
        log: StudyLog,
        available_subjects: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Study Session")
        self.setFixedSize(440, 380)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.log = log
        self.available_subjects = available_subjects

        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #121215;
                border: 1px solid #27272A;
                border-radius: 14px;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        lbl_title = QLabel("EDIT STUDY SESSION")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(lbl_title)

        time_info = format_log_timestamp(log.started_at)
        lbl_sub = QLabel(f"Recorded: {time_info} ({log.source.upper()})")
        lbl_sub.setStyleSheet("color: #71717A; font-size: 12px;")
        layout.addWidget(lbl_sub)

        # Subject Selector
        lbl_subj = QLabel("SUBJECT")
        lbl_subj.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 600; letter-spacing: 0.5px;")
        layout.addWidget(lbl_subj)

        self.cmb_subject = QComboBox()
        self.cmb_subject.setStyleSheet("""
            QComboBox {
                background-color: #18181D;
                color: #FFFFFF;
                border: 1px solid #27272E;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox QAbstractItemView {
                background-color: #141418;
                color: #FFFFFF;
                selection-background-color: #27272E;
                selection-color: #FFFFFF;
                border: 1px solid #27272A;
                padding: 4px;
            }
        """)
        for s in self.available_subjects:
            clean = ScheduleEngine.clean_subject_name(s)
            self.cmb_subject.addItem(clean, userData=s)
        
        idx = self.cmb_subject.findData(log.subject_name)
        if idx >= 0:
            self.cmb_subject.setCurrentIndex(idx)
        else:
            self.cmb_subject.addItem(log.subject_name, userData=log.subject_name)
            self.cmb_subject.setCurrentIndex(self.cmb_subject.count() - 1)
        layout.addWidget(self.cmb_subject)

        # Duration SpinBox & Presets
        lbl_dur = QLabel("DURATION (MINUTES)")
        lbl_dur.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 600; letter-spacing: 0.5px;")
        layout.addWidget(lbl_dur)

        self.spn_duration = QSpinBox()
        self.spn_duration.setRange(1, 480)
        self.spn_duration.setValue(log.duration_minutes)
        self.spn_duration.setSuffix(" min")
        self.spn_duration.setStyleSheet("""
            QSpinBox {
                background-color: #18181D;
                color: #10B981;
                border: 1px solid #27272E;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        layout.addWidget(self.spn_duration)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        for m in (15, 25, 30, 45, 60):
            btn = QPushButton(f"{m}m")
            btn.setFixedHeight(26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(BUTTON_NAV_STYLE)
            btn.clicked.connect(lambda checked=False, val=m: self.spn_duration.setValue(val))
            preset_row.addWidget(btn)
        layout.addLayout(preset_row)

        layout.addStretch()

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_save.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_save)

        layout.addLayout(btn_row)

    def get_updated_data(self) -> tuple[str, int]:
        """Return (subject_name, duration_minutes)."""
        subj = self.cmb_subject.currentData() or self.cmb_subject.currentText()
        mins = self.spn_duration.value()
        return subj, mins

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class HistoryDialog(QDialog):
    """Full-featured modal for viewing, filtering, and managing study logs and statistics."""

    log_deleted = Signal(str)  # log_id
    log_updated = Signal(str, str, int)  # (log_id, subject_name, duration_minutes)
    history_changed = Signal()

    def __init__(
        self,
        engine: ScheduleEngine,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Study History & Cycle Statistics")
        self.setFixedSize(840, 620)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._init_ui()
        self.refresh_data()

    def _init_ui(self) -> None:
        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #121215;
                border: 1px solid #27272A;
                border-radius: 14px;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        # ---------------------------------------------------------------------
        # 1. Header Bar
        # ---------------------------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)

        self.lbl_title = QLabel("STUDY HISTORY & STATISTICS")
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700; letter-spacing: 1.5px;")
        header_text_layout.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel("Review session history, weekly volume, and cycle completion.")
        self.lbl_subtitle.setStyleSheet("color: #71717A; font-size: 12px;")
        header_text_layout.addWidget(self.lbl_subtitle)

        header_row.addLayout(header_text_layout, stretch=1)

        self.btn_close_top = QPushButton("✕")
        self.btn_close_top.setFixedSize(32, 32)
        self.btn_close_top.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_top.setStyleSheet("""
            QPushButton {
                background: #18181D;
                color: #71717A;
                border: 1px solid #27272E;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #27272E;
                color: #FFFFFF;
            }
        """)
        self.btn_close_top.clicked.connect(self.reject)
        header_row.addWidget(self.btn_close_top)

        main_layout.addLayout(header_row)

        # ---------------------------------------------------------------------
        # 2. KPI Telemetry Summary Cards
        # ---------------------------------------------------------------------
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        # Card 1: This Week
        card_week, self.lbl_kpi_week, self.lbl_kpi_week_sub = self._create_kpi_card(
            title="THIS WEEK",
            accent_color="#10B981",
        )
        kpi_row.addWidget(card_week)

        # Card 2: All-Time Total
        card_total, self.lbl_kpi_total, self.lbl_kpi_total_sub = self._create_kpi_card(
            title="ALL-TIME TOTAL",
            accent_color="#F4F4F6",
            title_color="#A1A1AA",
        )
        kpi_row.addWidget(card_total)

        # Card 3: Cycle Completion
        card_cycles, self.lbl_kpi_cycles, self.lbl_kpi_cycles_sub = self._create_kpi_card(
            title="CYCLE COMPLETION",
            accent_color="#38BDF8",
        )
        kpi_row.addWidget(card_cycles)

        main_layout.addLayout(kpi_row)

        # ---------------------------------------------------------------------
        # 3. Filter Bar
        # ---------------------------------------------------------------------
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        lbl_filter_subj = QLabel("Subject:")
        lbl_filter_subj.setStyleSheet("color: #71717A; font-size: 12px; font-weight: 500;")
        filter_row.addWidget(lbl_filter_subj)

        self.cmb_subject_filter = QComboBox()
        self.cmb_subject_filter.setStyleSheet("""
            QComboBox {
                background-color: #18181D;
                color: #E4E4E7;
                border: 1px solid #27272E;
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 500;
                min-width: 170px;
            }
            QComboBox:hover {
                border-color: #3F3F4A;
            }
            QComboBox QAbstractItemView {
                background-color: #141418;
                color: #FFFFFF;
                selection-background-color: #27272E;
                selection-color: #FFFFFF;
                border: 1px solid #27272A;
                padding: 4px;
            }
        """)
        self.cmb_subject_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.cmb_subject_filter)

        lbl_filter_src = QLabel("Source:")
        lbl_filter_src.setStyleSheet("color: #71717A; font-size: 12px; font-weight: 500;")
        filter_row.addWidget(lbl_filter_src)

        self.cmb_source_filter = QComboBox()
        self.cmb_source_filter.setStyleSheet("""
            QComboBox {
                background-color: #18181D;
                color: #E4E4E7;
                border: 1px solid #27272E;
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 500;
                min-width: 110px;
            }
            QComboBox:hover {
                border-color: #3F3F4A;
            }
            QComboBox QAbstractItemView {
                background-color: #141418;
                color: #FFFFFF;
                selection-background-color: #27272E;
                selection-color: #FFFFFF;
                border: 1px solid #27272A;
                padding: 4px;
            }
        """)
        self.cmb_source_filter.addItem("All Sources", userData=None)
        self.cmb_source_filter.addItem("Timer Only", userData="timer")
        self.cmb_source_filter.addItem("Manual Only", userData="manual")
        self.cmb_source_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.cmb_source_filter)

        filter_row.addStretch()

        self.lbl_session_count = QLabel("0 sessions recorded")
        self.lbl_session_count.setStyleSheet("color: #71717A; font-size: 12px; font-weight: 500;")
        filter_row.addWidget(self.lbl_session_count)

        main_layout.addLayout(filter_row)

        # ---------------------------------------------------------------------
        # 4. History Sessions Table
        # ---------------------------------------------------------------------
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["DATE & TIME", "SUBJECT", "DURATION", "SOURCE", "ACTIONS"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0E0E11;
                border: 1px solid #202026;
                border-radius: 10px;
                font-size: 13px;
                color: #F4F4F6;
            }
            QTableWidget::item {
                border-bottom: 1px solid #18181F;
                padding: 4px 8px;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #141418;
                color: #71717A;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                border: none;
                border-bottom: 1px solid #202026;
                padding: 10px 12px;
            }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(2, 95)
        self.table.setColumnWidth(3, 95)
        self.table.setColumnWidth(4, 150)

        main_layout.addWidget(self.table, stretch=1)

        # ---------------------------------------------------------------------
        # 5. Bottom Navigation & Shortcut Bar
        # ---------------------------------------------------------------------
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        lbl_hint = QLabel("Esc to close · Changes update active cycles immediately")
        lbl_hint.setStyleSheet("color: #52525B; font-size: 11px;")
        bottom_row.addWidget(lbl_hint, stretch=1)

        self.btn_done = QPushButton("Close")
        self.btn_done.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_done.clicked.connect(self.accept)
        bottom_row.addWidget(self.btn_done)

        main_layout.addLayout(bottom_row)

    def _create_kpi_card(
        self,
        title: str,
        accent_color: str,
        title_color: str | None = None,
    ) -> tuple[QFrame, QLabel, QLabel]:
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setStyleSheet("""
            QFrame#kpiCard {
                background-color: #16161B;
                border: 1px solid #222228;
                border-radius: 10px;
            }
            QFrame#kpiCard QLabel {
                border: none;
                background: transparent;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        tc = title_color or accent_color
        lbl_header = QLabel(title)
        lbl_header.setWordWrap(False)
        lbl_header.setStyleSheet(f"color: {tc}; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;")
        layout.addWidget(lbl_header)

        lbl_val = QLabel("0m")
        lbl_val.setStyleSheet(f"color: {accent_color}; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;")
        layout.addWidget(lbl_val)

        lbl_sub = QLabel("...")
        lbl_sub.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 500;")
        layout.addWidget(lbl_sub)

        return card, lbl_val, lbl_sub

    def refresh_data(self) -> None:
        """Reload all statistics and session logs from the schedule engine."""
        # 1. Update Subjects in Filter (preserving current selection)
        current_filter = self.cmb_subject_filter.currentData()
        self.cmb_subject_filter.blockSignals(True)
        self.cmb_subject_filter.clear()
        self.cmb_subject_filter.addItem("All Subjects", userData=None)

        subjects = self.engine.get_distinct_subjects()
        for s in subjects:
            clean = ScheduleEngine.clean_subject_name(s)
            self.cmb_subject_filter.addItem(clean, userData=s)

        if current_filter:
            idx = self.cmb_subject_filter.findData(current_filter)
            if idx >= 0:
                self.cmb_subject_filter.setCurrentIndex(idx)
        self.cmb_subject_filter.blockSignals(False)

        # 2. Recalculate KPIs
        week_mins = self.engine.get_weekly_study_minutes()
        total_mins = self.engine.get_total_study_minutes()
        completed_cycles, total_cycles, pct = self.engine.get_cycle_completion_stats()

        self.lbl_kpi_week.setText(format_minutes_hh_mm(week_mins))
        self.lbl_kpi_week_sub.setText("Monday – Sunday volume")

        self.lbl_kpi_total.setText(format_minutes_hh_mm(total_mins))
        self.lbl_kpi_total_sub.setText("Total across all subjects")

        self.lbl_kpi_cycles.setText(f"{pct}%")
        self.lbl_kpi_cycles_sub.setText(f"{completed_cycles} of {total_cycles} cycles on target")

        # 3. Populate Table Rows
        self._populate_table()

    def _on_filter_changed(self) -> None:
        self._populate_table()

    def _populate_table(self) -> None:
        subj_filter = self.cmb_subject_filter.currentData()
        src_filter = self.cmb_source_filter.currentData()

        logs = self.engine.get_study_logs(
            reverse=True,
            subject_filter=subj_filter,
            source_filter=src_filter,
        )

        self.lbl_session_count.setText(f"{len(logs)} session{'s' if len(logs) != 1 else ''} recorded")

        self.table.setRowCount(len(logs))
        self.table.verticalHeader().setDefaultSectionSize(44)

        for row, log in enumerate(logs):
            # Col 0: Timestamp
            time_text = format_log_timestamp(log.started_at)
            item_time = QTableWidgetItem(time_text)
            item_time.setForeground(QColor("#A1A1AA"))
            item_time.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 0, item_time)

            # Col 1: Subject
            clean_name = ScheduleEngine.clean_subject_name(log.subject_name)
            item_subj = QTableWidgetItem(clean_name)
            item_subj.setForeground(QColor("#F4F4F6"))
            item_subj.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 1, item_subj)

            # Col 2: Duration badge
            dur_widget = self._create_badge(
                f"+{log.duration_minutes}m",
                bg="#0F291E",
                fg="#10B981",
                border="#1B4D36",
            )
            self.table.setCellWidget(row, 2, dur_widget)

            # Col 3: Source badge
            if log.source.lower() == "manual":
                src_widget = self._create_badge(
                    "MANUAL",
                    bg="#201830",
                    fg="#C084FC",
                    border="#3B2A59",
                )
            else:
                src_widget = self._create_badge(
                    "TIMER",
                    bg="#122438",
                    fg="#38BDF8",
                    border="#1E3E60",
                )
            self.table.setCellWidget(row, 3, src_widget)

            # Col 4: Actions (Edit / Delete)
            actions_widget = self._create_actions_widget(log)
            self.table.setCellWidget(row, 4, actions_widget)

    def _create_badge(self, text: str, bg: str, fg: str, border: str = "transparent") -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
                border: 1px solid {border};
                border-radius: 6px;
                padding: 3px 10px;
            }}
        """)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        return container

    def _create_actions_widget(self, log: StudyLog) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_edit = QPushButton("Edit")
        btn_edit.setFixedSize(56, 26)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #18181D;
                color: #D4D4D8;
                border: 1px solid #2B2B34;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #272730;
                border-color: #3F3F4E;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #121215;
            }
        """)
        btn_edit.clicked.connect(lambda checked=False, l=log: self._on_edit_log(l))
        layout.addWidget(btn_edit)

        btn_del = QPushButton("Delete")
        btn_del.setFixedSize(60, 26)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: #221316;
                color: #F87171;
                border: 1px solid #451B22;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #351A20;
                border-color: #68202C;
                color: #EF4444;
            }
            QPushButton:pressed {
                background-color: #170C0E;
            }
        """)
        btn_del.clicked.connect(lambda checked=False, l=log: self._on_delete_log(l))
        layout.addWidget(btn_del)

        return widget

    def _on_edit_log(self, log: StudyLog) -> None:
        """Open edit dialog and save modified session details."""
        subjects = self.engine.get_distinct_subjects()
        dlg = EditStudyLogDialog(log, available_subjects=subjects, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_subj, new_mins = dlg.get_updated_data()
            self.engine.update_study_log(
                log_id=log.id,
                subject_name=new_subj,
                duration_minutes=new_mins,
            )
            self.log_updated.emit(log.id, new_subj, new_mins)
            self.history_changed.emit()
            self.refresh_data()

    def _on_delete_log(self, log: StudyLog) -> None:
        """Confirm and delete a study log session using custom dark modal."""
        confirm_dlg = DeleteConfirmDialog(log, parent=self)
        if confirm_dlg.exec() == QDialog.DialogCode.Accepted:
            self.engine.delete_study_log(log.id)
            self.log_deleted.emit(log.id)
            self.history_changed.emit()
            self.refresh_data()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

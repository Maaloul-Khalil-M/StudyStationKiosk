"""Nightly Desk Debrief & Questionnaire Dialog for Study Station.

Implements the evening desk ritual:
1. Detects today's attended academic sessions.
2. Steps through each subject to capture concrete preparation tasks before next week's session.
3. Automatically sets the deadline to the exact start of the next class occurrence.
4. Allows custom deadlines for long-term deliverables/projects.
5. Persists generated StudyTodo items into SQLite and updates the schedule engine.
"""

from __future__ import annotations
from datetime import date, datetime, timedelta
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession, StudyTodo
from study_station.ui.theme import (
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class DebriefDateSelector(QComboBox):
    """Custom styled dark dropdown for selecting custom debrief deadlines."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        _today = date.today()
        for _label, _delta in [("Tomorrow", 1), ("+3 Days", 3), ("+1 Week", 7), ("+2 Weeks", 14), ("+1 Month", 30)]:
            self.addItem(_label, _today + timedelta(days=_delta))
        self.setStyleSheet("""
            QComboBox {
                background-color: #18181B;
                color: #52525B;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 110px;
            }
            QComboBox:enabled {
                color: #FFFFFF;
                border-color: #3F3F46;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                selection-background-color: #272730;
            }
        """)

    def setDate(self, qdate_or_date) -> None:
        if hasattr(qdate_or_date, "year") and callable(qdate_or_date.year):
            py_date = date(qdate_or_date.year(), qdate_or_date.month(), qdate_or_date.day())
        elif hasattr(qdate_or_date, "toPython"):
            py_date = qdate_or_date.toPython()
        else:
            py_date = qdate_or_date

        label = py_date.strftime("%d %b %Y")
        for i in range(self.count()):
            if self.itemData(i) == py_date:
                self.setCurrentIndex(i)
                return
        self.addItem(label, py_date)
        self.setCurrentIndex(self.count() - 1)

    def date(self) -> QDate:
        d = self.currentData()
        if d:
            return QDate(d.year, d.month, d.day)
        return QDate.currentDate()


class DebriefDialog(QDialog):
    """Interactive modal stepping through today's classes to generate preparation todos."""

    debrief_completed = Signal(list)  # list of StudyTodo created

    QUICK_TEMPLATES = [
        ("Lab Fix", "Fix lab exercise: "),
        ("Slides", "Review lecture slides: "),
        ("TD Problem", "Solve TD exercises: "),
        ("Exam Prep", "Exam prep: "),
        ("Project", "Project milestone: "),
    ]

    def __init__(
        self,
        engine: ScheduleEngine,
        ref_dt: datetime | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.ref_dt = ref_dt or datetime.now()
        self.created_todos: list[StudyTodo] = []

        # Determine target subjects for today
        self.today_sessions: list[AcademicSession] = self._resolve_today_sessions()
        self.distinct_subjects: list[str] = []
        for s in self.today_sessions:
            clean = ScheduleEngine.clean_subject_name(s.subject.name)
            if clean not in self.distinct_subjects:
                self.distinct_subjects.append(clean)

        self.current_step = 0
        self.total_steps = len(self.distinct_subjects)

        self.setFixedSize(620, 520)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._load_current_step()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().rect()
            self.move(parent_rect.center() - self.rect().center())

    def _resolve_today_sessions(self) -> list[AcademicSession]:
        """Fetch today's scheduled classes from engine."""
        if not self.engine:
            return []
        today_idx = self.ref_dt.weekday()
        return self.engine.get_day_sessions(today_idx)

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

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(28, 24, 28, 24)
        container_layout.setSpacing(16)

        # ---------------------------------------------------------------------
        # Header: Title, Date, and Close
        # ---------------------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)

        self.lbl_title = QLabel("NIGHTLY DESK DEBRIEF")
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 1px;")
        header_text_layout.addWidget(self.lbl_title)

        date_str = self.ref_dt.strftime("%A, %b %d").upper()
        self.lbl_subtitle = QLabel(f"{date_str} · Prepare today's subjects before next week")
        self.lbl_subtitle.setStyleSheet("color: #71717A; font-size: 12px; font-weight: 500;")
        header_text_layout.addWidget(self.lbl_subtitle)

        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #71717A;
                border: 1px solid #27272A;
                border-radius: 15px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #27272A;
                color: #FFFFFF;
            }
        """)
        self.btn_close.clicked.connect(self.reject)
        header_layout.addWidget(self.btn_close)

        container_layout.addLayout(header_layout)

        # Hairline separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #27272A; border: none;")
        container_layout.addWidget(sep)

        # ---------------------------------------------------------------------
        # Dynamic Step Body
        # ---------------------------------------------------------------------
        self.step_widget = QWidget(self.container)
        self.step_layout = QVBoxLayout(self.step_widget)
        self.step_layout.setContentsMargins(0, 0, 0, 0)
        self.step_layout.setSpacing(14)

        # Step badge & Subject Header
        subject_row = QHBoxLayout()
        self.lbl_step_badge = QLabel("STEP 1 OF 3")
        self.lbl_step_badge.setStyleSheet("""
            color: #10B981;
            background: #14221D;
            border: 1px solid #059669;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        subject_row.addWidget(self.lbl_step_badge)

        self.lbl_subject_header = QLabel("SUBJECT NAME")
        self.lbl_subject_header.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")
        subject_row.addWidget(self.lbl_subject_header)
        subject_row.addStretch()
        self.step_layout.addLayout(subject_row)

        # Next class relative deadline text
        self.lbl_next_class_info = QLabel("Next class: Thursday, Oct 22 at 09:40 (in 7 days)")
        self.lbl_next_class_info.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: 600;")
        self.step_layout.addWidget(self.lbl_next_class_info)

        # Fallback manual subject dropdown (shown when no scheduled sessions today)
        self.manual_subject_container = QWidget(self.step_widget)
        manual_layout = QVBoxLayout(self.manual_subject_container)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(4)
        lbl_pick = QLabel("Choose subject to prepare:")
        lbl_pick.setStyleSheet("color: #A1A1AA; font-size: 12px; font-weight: 600;")
        manual_layout.addWidget(lbl_pick)

        self.combo_subjects = QComboBox()
        self.combo_subjects.setStyleSheet("""
            QComboBox {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #18181B;
                color: #FFFFFF;
                selection-background-color: #27272A;
                border: 1px solid #27272A;
            }
        """)
        self.combo_subjects.currentTextChanged.connect(self._on_manual_subject_changed)
        manual_layout.addWidget(self.combo_subjects)
        self.step_layout.addWidget(self.manual_subject_container)

        # Task Input
        task_label = QLabel("What needs to be done / reviewed before next class?")
        task_label.setStyleSheet("color: #E4E4E7; font-size: 12px; font-weight: 600;")
        self.step_layout.addWidget(task_label)

        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("e.g. Fix Star Schema join in Lab 2 script")
        self.txt_title.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #10B981;
            }
        """)
        self.step_layout.addWidget(self.txt_title)

        # Quick Template Pills
        template_layout = QHBoxLayout()
        template_layout.setContentsMargins(0, 0, 0, 0)
        template_layout.setSpacing(6)
        for label, prefix in self.QUICK_TEMPLATES:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background: #18181B;
                    color: #A1A1AA;
                    border: 1px solid #27272A;
                    border-radius: 12px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #27272A;
                    color: #FFFFFF;
                    border-color: #3F3F46;
                }
            """)
            btn.clicked.connect(lambda _, p=prefix: self._apply_template_prefix(p))
            template_layout.addWidget(btn)
        template_layout.addStretch()
        self.step_layout.addLayout(template_layout)

        # Notes / Slide References
        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Optional notes, slide numbers, or error details...")
        self.txt_notes.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
                color: #FFFFFF;
            }
        """)
        self.step_layout.addWidget(self.txt_notes)

        # Deadline Mode Selector
        deadline_layout = QHBoxLayout()
        deadline_layout.setSpacing(12)

        self.radio_next_class = QRadioButton("Next class occurrence")
        self.radio_next_class.setChecked(True)
        self.radio_next_class.setStyleSheet("""
            QRadioButton {
                color: #E4E4E7;
                font-size: 12px;
                font-weight: 500;
            }
            QRadioButton::indicator:checked {
                background-color: #10B981;
                border: 2px solid #10B981;
                border-radius: 6px;
            }
        """)
        self.radio_next_class.toggled.connect(self._on_deadline_mode_changed)
        deadline_layout.addWidget(self.radio_next_class)

        self.radio_custom_date = QRadioButton("Custom date:")
        self.radio_custom_date.setStyleSheet("""
            QRadioButton {
                color: #A1A1AA;
                font-size: 12px;
                font-weight: 500;
            }
            QRadioButton::indicator:checked {
                background-color: #10B981;
                border: 2px solid #10B981;
                border-radius: 6px;
            }
        """)
        deadline_layout.addWidget(self.radio_custom_date)

        self.date_custom = DebriefDateSelector()
        self.date_custom.setEnabled(False)
        deadline_layout.addWidget(self.date_custom)
        deadline_layout.addStretch()
        self.step_layout.addLayout(deadline_layout)

        container_layout.addWidget(self.step_widget)
        container_layout.addStretch()

        # ---------------------------------------------------------------------
        # Bottom Controls: Skip, Add Another, Save & Next
        # ---------------------------------------------------------------------
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        self.btn_skip = QPushButton("Skip Subject")
        self.btn_skip.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.clicked.connect(self._on_skip)
        btn_layout.addWidget(self.btn_skip)

        self.btn_add_another = QPushButton("+ Add Another Task")
        self.btn_add_another.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_add_another.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_another.clicked.connect(self._on_add_another)
        btn_layout.addWidget(self.btn_add_another)

        btn_layout.addStretch()

        self.btn_save_next = QPushButton("Save & Next →")
        self.btn_save_next.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_save_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_next.clicked.connect(self._on_save_next)
        btn_layout.addWidget(self.btn_save_next)

        container_layout.addLayout(btn_layout)

    def _apply_template_prefix(self, prefix: str) -> None:
        """Insert or set template prefix into title input."""
        current = self.txt_title.text().strip()
        if not current:
            self.txt_title.setText(prefix)
        elif not current.startswith(prefix):
            self.txt_title.setText(f"{prefix}{current}")
        self.txt_title.setFocus()
        self.txt_title.setCursorPosition(len(self.txt_title.text()))

    def _on_deadline_mode_changed(self) -> None:
        """Toggle custom date edit state."""
        self.date_custom.setEnabled(self.radio_custom_date.isChecked())

    def _on_manual_subject_changed(self, subject_name: str) -> None:
        """Update deadline display when picking a manual subject."""
        if not subject_name:
            return
        self.lbl_subject_header.setText(subject_name)
        deadline = self.engine.get_next_class_deadline_for_subject(subject_name, self.ref_dt)
        if deadline:
            rel = self._format_relative_deadline(deadline)
            self.lbl_next_class_info.setText(f"Next class: {deadline.strftime('%A, %b %d at %H:%M')} ({rel})")
        else:
            self.lbl_next_class_info.setText("No upcoming scheduled class found for this subject.")

    def _load_current_step(self) -> None:
        """Render UI for the current step in the debrief."""
        self.txt_title.clear()
        self.txt_notes.clear()
        self.radio_next_class.setChecked(True)
        self.date_custom.setEnabled(False)

        if not self.distinct_subjects:
            # Free study day / no scheduled classes today
            self.lbl_step_badge.setText("FREE STUDY DAY")
            self.lbl_subject_header.setText("Ad-hoc Preparation")
            self.manual_subject_container.show()
            all_subjects = self.engine.get_distinct_subjects() if self.engine else []
            self.combo_subjects.clear()
            self.combo_subjects.addItems(all_subjects)
            self.btn_skip.setText("Skip / Close")
            self.btn_save_next.setText("Save Task")
            if all_subjects:
                self._on_manual_subject_changed(all_subjects[0])
            return

        self.manual_subject_container.hide()
        current_subject = self.distinct_subjects[self.current_step]
        self.lbl_step_badge.setText(f"STEP {self.current_step + 1} OF {self.total_steps}")
        self.lbl_subject_header.setText(current_subject)

        deadline = self.engine.get_next_class_deadline_for_subject(current_subject, self.ref_dt)
        if deadline:
            rel = self._format_relative_deadline(deadline)
            self.lbl_next_class_info.setText(f"Next class: {deadline.strftime('%A, %b %d at %H:%M')} ({rel})")
        else:
            self.lbl_next_class_info.setText("No upcoming scheduled class found (custom date recommended).")

        # Set button labels
        is_last = (self.current_step == self.total_steps - 1)
        self.btn_save_next.setText("Finish Debrief ✓" if is_last else "Save & Next →")
        self.btn_skip.setText("Skip Subject" if not is_last else "Skip & Finish")

    def _format_relative_deadline(self, deadline: datetime) -> str:
        delta = deadline - self.ref_dt
        days = delta.days
        hours = int(delta.total_seconds() // 3600)
        if days > 1:
            return f"in {days} days"
        elif days == 1:
            return "tomorrow"
        elif hours > 0:
            return f"in {hours} hours"
        else:
            return "today"

    def _resolve_active_subject_name(self) -> str:
        if self.distinct_subjects:
            return self.distinct_subjects[self.current_step]
        return self.combo_subjects.currentText().strip()

    def _resolve_active_due_date(self, subject_name: str) -> datetime:
        if self.radio_custom_date.isChecked():
            selected = self.date_custom.currentData()
            if selected:
                return datetime(selected.year, selected.month, selected.day, 23, 59)

        # Default: next class start datetime
        deadline = self.engine.get_next_class_deadline_for_subject(subject_name, self.ref_dt)
        if deadline:
            return deadline
        # Fallback to 7 days ahead
        return self.ref_dt + timedelta(days=7)

    def _save_task_for_current_step(self) -> bool:
        """Create StudyTodo and save to engine. Returns True if task was created."""
        title = self.txt_title.text().strip()
        if not title:
            return False

        subject_name = self._resolve_active_subject_name()
        if not subject_name:
            return False

        due_date = self._resolve_active_due_date(subject_name)
        notes = self.txt_notes.text().strip()

        todo = StudyTodo(
            subject_name=subject_name,
            title=title,
            notes=notes,
            due_date=due_date,
            status="pending",
        )
        self.engine.add_todo(todo)
        self.created_todos.append(todo)
        return True

    def _on_add_another(self) -> None:
        """Save current task and clear inputs to let user add a 2nd task for same subject."""
        saved = self._save_task_for_current_step()
        if saved:
            self.txt_title.clear()
            self.txt_notes.clear()
            self.txt_title.setPlaceholderText("Add another task for this subject...")
            self.txt_title.setFocus()

    def _on_save_next(self) -> None:
        """Save current task and advance or finish."""
        self._save_task_for_current_step()
        self._advance_step()

    def _on_skip(self) -> None:
        """Skip current subject without saving."""
        self._advance_step()

    def _advance_step(self) -> None:
        """Move to next step or complete dialog."""
        if not self.distinct_subjects or self.current_step >= self.total_steps - 1:
            if self.engine is not None:
                self.engine.mark_day_debriefed(self.ref_dt.date())
            self.debrief_completed.emit(self.created_todos)
            self.accept()
            return

        self.current_step += 1
        self._load_current_step()

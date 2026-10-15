"""Edit / Create Academic Todo Modal Dialog for Study Station.

Provides full CRUD interface for individual StudyTodo items:
- Title and Notes editing
- Subject module assignment
- Due date selection with quick presets (Next Class, Tomorrow, +3 Days, +1 Week)
- Status toggling (Pending vs. Completed)
- Confidence rating and in-class question viewing/editing
- Safe task deletion with confirmation
"""

from __future__ import annotations
from datetime import date, datetime, timedelta
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import StudyTodo
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class EditTodoDialog(QDialog):
    """Modal dialog allowing creating a new task or editing an existing StudyTodo."""

    todo_saved = Signal(object)  # (StudyTodo)
    todo_deleted = Signal(str)  # (todo_id)

    def __init__(
        self,
        engine: ScheduleEngine,
        todo: StudyTodo | None = None,
        default_subject: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.todo = todo
        self.is_create_mode = todo is None

        # Determine subject
        self.subjects = self.engine.get_distinct_subjects() if self.engine else []
        if self.todo and self.todo.subject_name and self.todo.subject_name not in self.subjects:
            self.subjects.append(self.todo.subject_name)
        elif default_subject and default_subject not in self.subjects:
            self.subjects.append(default_subject)

        self.initial_subject = (
            (self.todo.subject_name if self.todo else None)
            or default_subject
            or (self.subjects[0] if self.subjects else "General Study")
        )

        self.setFixedSize(580, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._populate_fields()

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

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # ---------------------------------------------------------------------
        # Header: Title, Mode, Close
        # ---------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        header_text = QVBoxLayout()
        header_text.setSpacing(3)

        title_text = "CREATE PREPARATION TASK" if self.is_create_mode else "EDIT PREPARATION TASK"
        self.lbl_title = QLabel(title_text)
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 1px;")
        header_text.addWidget(self.lbl_title)

        sub_text = "Add a concrete task before next class" if self.is_create_mode else "Update task details, notes, or deadline"
        lbl_sub = QLabel(sub_text)
        lbl_sub.setStyleSheet("color: #71717A; font-size: 12px;")
        header_text.addWidget(lbl_sub)
        header.addLayout(header_text)

        header.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("""
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
        btn_close.clicked.connect(self.reject)
        header.addWidget(btn_close)

        layout.addLayout(header)

        # Hairline separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #27272A; border: none;")
        layout.addWidget(sep)

        # ---------------------------------------------------------------------
        # Form Fields
        # ---------------------------------------------------------------------
        # 1. Subject Selector
        row_subj = QVBoxLayout()
        row_subj.setSpacing(4)
        lbl_subj = QLabel("ACADEMIC SUBJECT / MODULE")
        lbl_subj.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        row_subj.addWidget(lbl_subj)

        self.combo_subject = QComboBox()
        self.combo_subject.setEditable(True)
        for s in self.subjects:
            self.combo_subject.addItem(s)
        self.combo_subject.setStyleSheet("""
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
        self.combo_subject.currentTextChanged.connect(self._on_subject_changed)
        row_subj.addWidget(self.combo_subject)
        layout.addLayout(row_subj)

        # 2. Task Title
        row_title = QVBoxLayout()
        row_title.setSpacing(4)
        lbl_title_field = QLabel("ACTIONABLE TASK TITLE")
        lbl_title_field.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        row_title.addWidget(lbl_title_field)

        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("e.g. Fix Star Schema join in Lab 2 script")
        self.txt_title.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        row_title.addWidget(self.txt_title)
        layout.addLayout(row_title)

        # 3. Notes / References
        row_notes = QVBoxLayout()
        row_notes.setSpacing(4)
        lbl_notes = QLabel("CONTEXT / NOTES (OPTIONAL)")
        lbl_notes.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        row_notes.addWidget(lbl_notes)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Slide references, exercise numbers, or error details...")
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
                border-color: #38BDF8;
                color: #FFFFFF;
            }
        """)
        row_notes.addWidget(self.txt_notes)
        layout.addLayout(row_notes)

        # 4. Due Date with Quick Presets
        row_due = QVBoxLayout()
        row_due.setSpacing(4)
        lbl_due = QLabel("DUE DATE / DEADLINE")
        lbl_due.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        row_due.addWidget(lbl_due)

        due_input_row = QHBoxLayout()
        due_input_row.setSpacing(8)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate().addDays(7))
        self.date_picker.setStyleSheet("""
            QDateEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
        """)
        due_input_row.addWidget(self.date_picker, stretch=1)

        # Presets: Next Class, Tomorrow, +3 Days, +1 Week
        btn_next_class = QPushButton("Next Class")
        btn_next_class.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_next_class.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_next_class.clicked.connect(self._set_deadline_next_class)
        due_input_row.addWidget(btn_next_class)

        btn_tomorrow = QPushButton("Tomorrow")
        btn_tomorrow.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_tomorrow.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_tomorrow.clicked.connect(lambda: self.date_picker.setDate(QDate.currentDate().addDays(1)))
        due_input_row.addWidget(btn_tomorrow)

        btn_3days = QPushButton("+3 Days")
        btn_3days.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_3days.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_3days.clicked.connect(lambda: self.date_picker.setDate(QDate.currentDate().addDays(3)))
        due_input_row.addWidget(btn_3days)

        btn_1week = QPushButton("+1 Wk")
        btn_1week.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_1week.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_1week.clicked.connect(lambda: self.date_picker.setDate(QDate.currentDate().addDays(7)))
        due_input_row.addWidget(btn_1week)

        row_due.addLayout(due_input_row)
        layout.addLayout(row_due)

        # 5. Status & In-Class Question Row
        status_row = QHBoxLayout()
        status_row.setSpacing(12)

        # Status Dropdown
        col_status = QVBoxLayout()
        col_status.setSpacing(4)
        lbl_status = QLabel("STATUS")
        lbl_status.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 700;")
        col_status.addWidget(lbl_status)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Pending", "Completed"])
        self.combo_status.setStyleSheet("""
            QComboBox {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
        """)
        col_status.addWidget(self.combo_status)
        status_row.addLayout(col_status, stretch=1)

        # In-Class Question Field
        col_q = QVBoxLayout()
        col_q.setSpacing(4)
        lbl_q = QLabel("QUESTION FOR PROFESSOR (OPTIONAL)")
        lbl_q.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700;")
        col_q.addWidget(lbl_q)

        self.txt_question = QLineEdit()
        self.txt_question.setPlaceholderText("Question formulated for next class...")
        self.txt_question.setStyleSheet("""
            QLineEdit {
                background-color: #082F49;
                color: #F0F9FF;
                border: 1px solid #0284C7;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
        """)
        col_q.addWidget(self.txt_question)
        status_row.addLayout(col_q, stretch=2)

        layout.addLayout(status_row)

        layout.addStretch()

        # ---------------------------------------------------------------------
        # Footer Action Buttons
        # ---------------------------------------------------------------------
        footer = QHBoxLayout()
        footer.setSpacing(10)

        if not self.is_create_mode:
            self.btn_delete = QPushButton("🗑 Delete Task")
            self.btn_delete.setStyleSheet(BUTTON_DANGER_STYLE)
            self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_delete.clicked.connect(self._on_delete)
            footer.addWidget(self.btn_delete)

        footer.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(BUTTON_NAV_STYLE)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        footer.addWidget(btn_cancel)

        save_label = "+ Create Task" if self.is_create_mode else "Save Changes"
        self.btn_save = QPushButton(save_label)
        self.btn_save.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._on_save)
        footer.addWidget(self.btn_save)

        layout.addLayout(footer)

    def _populate_fields(self) -> None:
        """Initialize fields from existing todo or defaults."""
        # Select initial subject
        idx = self.combo_subject.findText(self.initial_subject)
        if idx >= 0:
            self.combo_subject.setCurrentIndex(idx)
        else:
            self.combo_subject.setEditText(self.initial_subject)

        if self.todo:
            self.txt_title.setText(self.todo.title)
            self.txt_notes.setText(self.todo.notes)
            qd = QDate(self.todo.due_date.year, self.todo.due_date.month, self.todo.due_date.day)
            self.date_picker.setDate(qd)
            self.combo_status.setCurrentText("Completed" if self.todo.is_completed else "Pending")
            self.txt_question.setText(self.todo.next_class_question or "")
        else:
            self._set_deadline_next_class()

    def _on_subject_changed(self, subject_name: str) -> None:
        """Auto-adjust deadline to next class if in create mode."""
        if self.is_create_mode and subject_name.strip():
            self._set_deadline_next_class()

    def _set_deadline_next_class(self) -> None:
        """Calculate next occurrence start datetime for current subject."""
        subject = self.combo_subject.currentText().strip()
        if not subject or not self.engine:
            return
        now = datetime.now()
        deadline = self.engine.get_next_class_deadline_for_subject(subject, now)
        if deadline:
            self.date_picker.setDate(QDate(deadline.year, deadline.month, deadline.day))
        else:
            self.date_picker.setDate(QDate.currentDate().addDays(7))

    def _on_save(self) -> None:
        """Validate and save task."""
        title = self.txt_title.text().strip()
        if not title:
            self.txt_title.setFocus()
            return

        subject = self.combo_subject.currentText().strip()
        if not subject:
            subject = "General Study"

        qd = self.date_picker.date()
        due_date = datetime(qd.year(), qd.month(), qd.day(), 23, 59)
        notes = self.txt_notes.text().strip()
        status = "completed" if self.combo_status.currentText() == "Completed" else "pending"
        question = self.txt_question.text().strip() or None

        if self.is_create_mode:
            new_todo = StudyTodo(
                subject_name=subject,
                title=title,
                notes=notes,
                due_date=due_date,
                status=status,
                completed_at=datetime.now() if status == "completed" else None,
                next_class_question=question,
            )
            if self.engine:
                self.engine.add_todo(new_todo)
            self.todo_saved.emit(new_todo)
        else:
            assert self.todo is not None
            self.todo.subject_name = subject
            self.todo.title = title
            self.todo.notes = notes
            self.todo.due_date = due_date
            self.todo.status = status
            if status == "completed" and not self.todo.completed_at:
                self.todo.completed_at = datetime.now()
            elif status == "pending":
                self.todo.completed_at = None
            self.todo.next_class_question = question

            if self.engine:
                self.engine.update_todo(self.todo)
            self.todo_saved.emit(self.todo)

        self.accept()

    def _on_delete(self) -> None:
        """Confirm and delete task."""
        if not self.todo:
            return

        confirm = QMessageBox.question(
            self,
            "Delete Task",
            f"Are you sure you want to delete this task?\n\n\"{self.todo.title}\"",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            todo_id = self.todo.id
            if self.engine:
                self.engine.delete_todo(todo_id)
            self.todo_deleted.emit(todo_id)
            self.accept()

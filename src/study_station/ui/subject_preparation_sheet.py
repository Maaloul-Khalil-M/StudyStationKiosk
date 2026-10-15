"""Subject Preparation Sheet & Task Checklist Dialog for Study Station.

Provides the interactive preparation drawer/modal when clicking any class card on the Weekly Grid:
1. Inspects all pending preparation tasks for the clicked subject.
2. Direct inline task check-off (marking completed in engine and persistence).
3. 1-click focus start directly tethered to a specific task.
4. Quick inline task addition with automatic next-class deadline calculation.
5. In-class question viewer and editor.
6. Access to class time/room timetable editing via ClassSessionDialog.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession, StudyTodo
from study_station.ui.class_session_dialog import ClassSessionDialog
from study_station.ui.edit_todo_dialog import EditTodoDialog
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class SubjectPreparationSheet(QDialog):
    """Cockpit preparation sheet for an academic subject and its class session."""

    start_task_focus_requested = Signal(object, int)  # (StudyTodo, minutes)
    start_subject_focus_requested = Signal(str, int)  # (subject_name, minutes)
    session_modified = Signal(object, object)  # (old_session, new_session)
    session_deleted = Signal(object)  # (session)
    todo_changed = Signal()  # emitted when tasks are added, edited, deleted, or toggled

    def __init__(
        self,
        session: AcademicSession,
        engine: ScheduleEngine,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.engine = engine
        self.subject_name = ScheduleEngine.clean_subject_name(session.subject.name)

        self.setFixedSize(680, 620)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._refresh_content()

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

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(24, 20, 24, 20)
        self.content_layout.setSpacing(14)

        # ---------------------------------------------------------------------
        # Header: Subject Name, Core Badge, Room, Close Button
        # ---------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        header_text = QVBoxLayout()
        header_text.setSpacing(3)

        title_row = QHBoxLayout()
        self.lbl_title = QLabel(self.subject_name)
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 800; letter-spacing: 0.5px;")
        title_row.addWidget(self.lbl_title)

        core_type = self.session.subject.core.upper()
        self.lbl_core = QLabel(core_type)
        self.lbl_core.setStyleSheet("""
            background-color: #1E293B;
            color: #93C5FD;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        """)
        title_row.addWidget(self.lbl_core)
        title_row.addStretch()
        header_text.addLayout(title_row)

        loc = self.session.location or "Classroom"
        day_str = self.session.day
        time_str = f"{self.session.time_slot.start} – {self.session.time_slot.end}"
        self.lbl_schedule_info = QLabel(f"Scheduled: {day_str} {time_str} · {loc}")
        self.lbl_schedule_info.setStyleSheet("color: #71717A; font-size: 12px; font-weight: 500;")
        header_text.addWidget(self.lbl_schedule_info)

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
        btn_close.clicked.connect(self.accept)
        header.addWidget(btn_close)

        self.content_layout.addLayout(header)

        # Hairline separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #27272A; border: none;")
        self.content_layout.addWidget(sep)

        # ---------------------------------------------------------------------
        # Next Class Deadline Callout
        # ---------------------------------------------------------------------
        deadline_box = QFrame()
        deadline_box.setStyleSheet("background-color: #18181F; border-radius: 8px; padding: 8px 12px;")
        d_layout = QHBoxLayout(deadline_box)
        d_layout.setContentsMargins(4, 4, 4, 4)

        self.lbl_deadline = QLabel("NEXT CLASS: Computing...")
        self.lbl_deadline.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: 600;")
        d_layout.addWidget(self.lbl_deadline)
        d_layout.addStretch()

        self.content_layout.addWidget(deadline_box)

        # ---------------------------------------------------------------------
        # Scrollable Tasks Section
        # ---------------------------------------------------------------------
        tasks_header_row = QHBoxLayout()
        self.lbl_tasks_header = QLabel("PREPARATION TASKS")
        self.lbl_tasks_header.setStyleSheet("color: #E4E4E7; font-size: 12px; font-weight: 800; letter-spacing: 1px;")
        tasks_header_row.addWidget(self.lbl_tasks_header)
        tasks_header_row.addStretch()
        self.content_layout.addLayout(tasks_header_row)

        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
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
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(8, 8, 8, 8)
        self.tasks_layout.setSpacing(8)
        self.tasks_scroll.setWidget(self.tasks_container)
        self.content_layout.addWidget(self.tasks_scroll, stretch=1)

        # Quick Add Task Input Bar
        add_task_row = QHBoxLayout()
        add_task_row.setSpacing(8)

        self.txt_new_task = QLineEdit()
        self.txt_new_task.setPlaceholderText("+ Add preparation task for this class...")
        self.txt_new_task.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #10B981;
            }
        """)
        self.txt_new_task.returnPressed.connect(self._on_add_task)
        add_task_row.addWidget(self.txt_new_task, stretch=1)

        btn_add = QPushButton("Add Task")
        btn_add.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._on_add_task)
        add_task_row.addWidget(btn_add)

        self.content_layout.addLayout(add_task_row)

        # ---------------------------------------------------------------------
        # In-Class Payoff: Questions to Ask Professor
        # ---------------------------------------------------------------------
        self.questions_frame = QFrame()
        self.questions_frame.setStyleSheet("""
            QFrame {
                background-color: #082F49;
                border: 1px solid #0284C7;
                border-radius: 8px;
            }
        """)
        self.questions_layout = QVBoxLayout(self.questions_frame)
        self.questions_layout.setContentsMargins(10, 8, 10, 8)
        self.questions_layout.setSpacing(6)
        self.content_layout.addWidget(self.questions_frame)

        # ---------------------------------------------------------------------
        # Bottom Actions: Timetable Edit, Focus on Subject, Done
        # ---------------------------------------------------------------------
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 4, 0, 0)
        footer_layout.setSpacing(10)

        self.btn_edit_timetable = QPushButton("✏ Edit Class Time/Room")
        self.btn_edit_timetable.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_edit_timetable.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit_timetable.clicked.connect(self._open_timetable_editor)
        footer_layout.addWidget(self.btn_edit_timetable)

        footer_layout.addStretch()

        self.btn_general_focus = QPushButton("▶ Start Focus (15m)")
        self.btn_general_focus.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_general_focus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_general_focus.clicked.connect(self._on_start_general_focus)
        footer_layout.addWidget(self.btn_general_focus)

        self.content_layout.addLayout(footer_layout)

    def _refresh_content(self) -> None:
        """Repopulate tasks and deadline information."""
        now = datetime.now()
        next_deadline = self.engine.get_next_class_deadline_for_subject(self.subject_name, now)
        if next_deadline:
            days = (next_deadline.date() - now.date()).days
            delta = next_deadline - now
            hours = int(delta.total_seconds() // 3600)
            mins = int((delta.total_seconds() % 3600) // 60)
            if days == 0:
                rel_str = f"today in {hours}h {mins:02d}m" if hours > 0 else f"today in {mins}m"
            elif days == 1:
                rel_str = "tomorrow"
            else:
                rel_str = f"in {days} days"
            self.lbl_deadline.setText(
                f"NEXT CLASS: {next_deadline.strftime('%A, %b %d at %H:%M')} ({rel_str})"
            )
        else:
            self.lbl_deadline.setText("NEXT CLASS: No upcoming session scheduled")

        # Clear existing task widgets
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        pending_todos = self.engine.get_pending_todos(self.subject_name)
        completed_todos = [t for t in self.engine.get_todos(subject_filter=self.subject_name) if t.is_completed]
        self.lbl_tasks_header.setText(f"PREPARATION TASKS ({len(pending_todos)} pending)")

        if not pending_todos and not completed_todos:
            empty_lbl = QLabel("No preparation tasks recorded yet.\nAdd what needs to be done before next week above!")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #71717A; font-size: 12px; padding: 24px;")
            self.tasks_layout.addWidget(empty_lbl)
        else:
            # Render pending tasks
            for todo in pending_todos:
                row_widget = self._create_todo_row(todo)
                self.tasks_layout.addWidget(row_widget)

            # Render completed tasks (dimmed)
            if completed_todos:
                comp_lbl = QLabel(f"✓ COMPLETED ({len(completed_todos)})")
                comp_lbl.setStyleSheet("color: #059669; font-size: 10px; font-weight: 700; padding-top: 8px;")
                self.tasks_layout.addWidget(comp_lbl)
                for todo in completed_todos:
                    row_widget = self._create_todo_row(todo, is_done=True)
                    self.tasks_layout.addWidget(row_widget)

        self.tasks_layout.addStretch()

        # ---------------------------------------------------------------------
        # Populate In-Class Questions (In-Class Payoff)
        # ---------------------------------------------------------------------
        while self.questions_layout.count():
            item = self.questions_layout.takeAt(0)
            w = item.widget()
            l = item.layout()
            if w:
                w.deleteLater()
            elif l:
                while l.count():
                    sub = l.takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        questions = self.engine.get_subject_questions(self.subject_name)
        if questions:
            self.questions_frame.show()
            lbl_q_head = QLabel(f"❓ IN-CLASS PAYOFF · QUESTIONS FOR PROFESSOR ({len(questions)})")
            lbl_q_head.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 800; letter-spacing: 0.8px;")
            self.questions_layout.addWidget(lbl_q_head)

            for q_text in questions:
                q_row = QHBoxLayout()
                q_row.setContentsMargins(0, 2, 0, 2)
                lbl_q = QLabel(f"• {q_text}")
                lbl_q.setWordWrap(True)
                lbl_q.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 600;")
                q_row.addWidget(lbl_q, stretch=1)

                btn_copy = QPushButton("📋 Copy")
                btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_copy.setFixedHeight(24)
                btn_copy.setStyleSheet("""
                    QPushButton {
                        background-color: #0C4A6E;
                        color: #E0F2FE;
                        border: 1px solid #0284C7;
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: 600;
                        padding: 2px 6px;
                    }
                    QPushButton:hover {
                        background-color: #0284C7;
                        color: #FFFFFF;
                    }
                """)
                def do_copy(_checked=False, text=q_text):
                    from PySide6.QtWidgets import QApplication
                    QApplication.clipboard().setText(text)
                btn_copy.clicked.connect(do_copy)
                q_row.addWidget(btn_copy)

                btn_resolved = QPushButton("✓ Asked")
                btn_resolved.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_resolved.setFixedHeight(24)
                btn_resolved.setStyleSheet("""
                    QPushButton {
                        background-color: #064E3B;
                        color: #34D399;
                        border: 1px solid #059669;
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: 700;
                        padding: 2px 6px;
                    }
                    QPushButton:hover {
                        background-color: #059669;
                        color: #FFFFFF;
                    }
                """)
                def do_resolve(_checked=False, text=q_text):
                    self.engine.resolve_subject_question(self.subject_name, text)
                    self._refresh_content()
                btn_resolved.clicked.connect(do_resolve)
                q_row.addWidget(btn_resolved)

                self.questions_layout.addLayout(q_row)
        else:
            self.questions_frame.hide()

    def _create_todo_row(self, todo: StudyTodo, is_done: bool = False) -> QWidget:
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: #18181B;
                border: 1px solid #27272A;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #3F3F46;
            }
        """)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Checkbox: reversible toggle
        chk = QCheckBox()
        chk.setChecked(is_done)
        chk.toggled.connect(lambda checked, t=todo: self._on_toggle_completed(t, checked))
        layout.addWidget(chk)

        # Text column
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_style = "color: #71717A; text-decoration: line-through;" if is_done else "color: #FFFFFF; font-weight: 600;"
        lbl_task_title = QLabel(todo.title)
        lbl_task_title.setStyleSheet(f"font-size: 13px; {title_style}")
        lbl_task_title.setWordWrap(True)
        text_layout.addWidget(lbl_task_title)

        meta_parts = []
        if todo.due_date and not is_done:
            due_str = todo.due_date.strftime("%a, %b %d")
            is_overdue = todo.is_overdue()
            color = "#EF4444" if is_overdue else "#71717A"
            meta_parts.append(f"<span style='color: {color};'>Due: {due_str}</span>")
        elif is_done:
            meta_parts.append("<span style='color: #10B981; font-weight: 600;'>✓ Completed</span>")

        if todo.notes:
            meta_parts.append(f"<span style='color: #52525B;'>{todo.notes}</span>")

        if meta_parts:
            lbl_meta = QLabel(" · ".join(meta_parts))
            lbl_meta.setStyleSheet("font-size: 11px;")
            text_layout.addWidget(lbl_meta)

        layout.addLayout(text_layout, stretch=1)

        # 1. Focus button (only for pending tasks)
        if not is_done:
            btn_focus_task = QPushButton("▶ 15m")
            btn_focus_task.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_focus_task.setFixedSize(54, 28)
            btn_focus_task.setStyleSheet("""
                QPushButton {
                    background-color: #14221D;
                    color: #10B981;
                    border: 1px solid #059669;
                    border-radius: 14px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #10B981;
                    color: #000000;
                }
            """)
            btn_focus_task.clicked.connect(lambda _, t=todo: self._on_focus_task(t))
            layout.addWidget(btn_focus_task)

        # 2. Edit button
        btn_edit = QPushButton("✏")
        btn_edit.setToolTip("Edit Task")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setFixedSize(28, 28)
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
                border-color: #3F3F46;
            }
        """)
        btn_edit.clicked.connect(lambda _, t=todo: self._on_edit_task(t))
        layout.addWidget(btn_edit)

        # 3. Delete button
        btn_delete = QPushButton("✕")
        btn_delete.setToolTip("Delete Task")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setFixedSize(28, 28)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #71717A;
                border: 1px solid #27272A;
                border-radius: 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #451A1A;
                color: #EF4444;
                border-color: #991B1B;
            }
        """)
        btn_delete.clicked.connect(lambda _, t=todo: self._on_delete_task(t))
        layout.addWidget(btn_delete)

        return row

    def _on_add_task(self) -> None:
        title = self.txt_new_task.text().strip()
        if not title:
            return

        now = datetime.now()
        default_deadline = self.engine.get_next_class_deadline_for_subject(self.subject_name, now)
        due_date = default_deadline or (now + timedelta(days=7))

        todo = StudyTodo(
            subject_name=self.subject_name,
            title=title,
            due_date=due_date,
            status="pending",
        )
        self.engine.add_todo(todo)
        self.txt_new_task.clear()
        self.todo_changed.emit()
        self._refresh_content()

    def _on_toggle_completed(self, todo: StudyTodo, checked: bool) -> None:
        if checked:
            self.engine.mark_todo_completed(todo.id, confidence="solid")
        else:
            self.engine.mark_todo_pending(todo.id)
        self.todo_changed.emit()
        self._refresh_content()

    def _on_mark_completed(self, todo: StudyTodo) -> None:
        self._on_toggle_completed(todo, True)

    def _on_edit_task(self, todo: StudyTodo) -> None:
        dialog = EditTodoDialog(
            engine=self.engine,
            todo=todo,
            parent=self,
        )
        def on_changed(_):
            self.todo_changed.emit()
            self._refresh_content()
        dialog.todo_saved.connect(on_changed)
        dialog.todo_deleted.connect(on_changed)
        dialog.exec()

    def _on_delete_task(self, todo: StudyTodo) -> None:
        confirm = QMessageBox.question(
            self,
            "Delete Task",
            f"Are you sure you want to delete this task?\n\n\"{todo.title}\"",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.engine.delete_todo(todo.id)
            self.todo_changed.emit()
            self._refresh_content()

    def _on_focus_task(self, todo: StudyTodo) -> None:
        self.start_task_focus_requested.emit(todo, 15)
        self.accept()

    def _on_start_general_focus(self) -> None:
        self.start_subject_focus_requested.emit(self.subject_name, 15)
        self.accept()

    def _open_timetable_editor(self) -> None:
        """Open ClassSessionDialog to edit session timetable attributes."""
        existing_names = sorted({s.subject.name for s in self.engine.sessions})
        dialog = ClassSessionDialog(
            session=self.session,
            existing_subjects=existing_names,
            parent=self,
        )

        def on_saved(old_s, new_s):
            self.session = new_s
            self.subject_name = ScheduleEngine.clean_subject_name(new_s.subject.name)
            self.session_modified.emit(old_s, new_s)
            self._refresh_content()

        def on_deleted(sess):
            self.session_deleted.emit(sess)
            self.reject()

        dialog.session_saved.connect(on_saved)
        dialog.session_deleted.connect(on_deleted)
        dialog.exec()

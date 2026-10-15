"""Academic Task Backlog & Focus Management Modal for Study Station.

Provides the comprehensive task hub:
1. Macro KPI overview across all enrolled subjects (Pending, Due This Week, Overdue, Completed).
2. Multi-criteria filtering by Subject, Status (All, Pending, Due Soon, Overdue, Completed), and Search query.
3. 1-click focus sprint launcher tethered to any task.
4. Interactive check-offs with reversible toggle (pending <-> completed).
5. In-place Edit and Delete buttons for each task row.
6. Central "+ New Task" creator.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from study_station.core.models import StudyTodo
from study_station.ui.edit_todo_dialog import EditTodoDialog
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class TasksDialog(QDialog):
    """Central Academic Task Backlog modal dialog."""

    start_task_focus_requested = Signal(object, int)  # (StudyTodo, minutes)
    tasks_changed = Signal()

    def __init__(
        self,
        engine: ScheduleEngine,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self._current_status_filter = "Pending"  # "All", "Pending", "Due Soon", "Overdue", "Completed"
        self._current_subject_filter = "All Subjects"
        self._search_query = ""

        self.setFixedSize(880, 660)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._refresh_all()

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
        # 1. Header: Title, "+ New Task", and Close Button
        # ---------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        lbl_title = QLabel("ACADEMIC TASK BACKLOG")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 1px;")
        header_text.addWidget(lbl_title)

        lbl_sub = QLabel("Manage deliverables, deadlines, and launch focus sprints across all modules")
        lbl_sub.setStyleSheet("color: #71717A; font-size: 12px;")
        header_text.addWidget(lbl_sub)
        header.addLayout(header_text)

        header.addStretch()

        self.btn_new_task = QPushButton("+ New Task")
        self.btn_new_task.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_new_task.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_task.clicked.connect(self._open_create_dialog)
        header.addWidget(self.btn_new_task)

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
        # 2. KPI Telemetry Summary Cards
        # ---------------------------------------------------------------------
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_pending = self._create_kpi_card("TOTAL PENDING", "0", "#38BDF8")
        self.kpi_due_week = self._create_kpi_card("DUE THIS WEEK", "0", "#F59E0B")
        self.kpi_overdue = self._create_kpi_card("OVERDUE", "0", "#EF4444")
        self.kpi_completed = self._create_kpi_card("COMPLETED", "0", "#10B981")

        kpi_row.addWidget(self.kpi_pending)
        kpi_row.addWidget(self.kpi_due_week)
        kpi_row.addWidget(self.kpi_overdue)
        kpi_row.addWidget(self.kpi_completed)

        self.content_layout.addLayout(kpi_row)

        # ---------------------------------------------------------------------
        # 3. Filter & Search Controls
        # ---------------------------------------------------------------------
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        # Search box
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Filter by title, notes, or course...")
        self.txt_search.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        self.txt_search.textChanged.connect(self._on_search_changed)
        filter_bar.addWidget(self.txt_search, stretch=3)

        # Subject filter dropdown
        self.combo_subject_filter = QComboBox()
        self.combo_subject_filter.setStyleSheet("""
            QComboBox {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #18181B;
                color: #FFFFFF;
                selection-background-color: #27272A;
                border: 1px solid #27272A;
            }
        """)
        self._populate_subject_filter()
        self.combo_subject_filter.currentTextChanged.connect(self._on_subject_filter_changed)
        filter_bar.addWidget(self.combo_subject_filter, stretch=2)

        self.content_layout.addLayout(filter_bar)

        # Status Segmented Filter Pills
        status_pills_row = QHBoxLayout()
        status_pills_row.setSpacing(6)

        self.status_buttons: dict[str, QPushButton] = {}
        for status_label in ["All", "Pending", "Due Soon (<24h)", "Overdue", "Completed"]:
            btn = QPushButton(status_label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, s=status_label: self._set_status_filter(s))
            self.status_buttons[status_label] = btn
            status_pills_row.addWidget(btn)

        status_pills_row.addStretch()
        self.content_layout.addLayout(status_pills_row)
        self._update_status_pill_styles()

        # ---------------------------------------------------------------------
        # 4. Scrollable Tasks List
        # ---------------------------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
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
        self.scroll_area.setWidget(self.tasks_container)
        self.content_layout.addWidget(self.scroll_area, stretch=1)

    def _create_kpi_card(self, title: str, initial_val: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #18181E;
                border: 1px solid #27272A;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;")
        layout.addWidget(lbl_t)

        lbl_v = QLabel(initial_val)
        lbl_v.setStyleSheet(f"color: {accent_color}; font-size: 20px; font-weight: 800;")
        layout.addWidget(lbl_v)

        card.value_label = lbl_v  # type: ignore
        return card

    def _populate_subject_filter(self) -> None:
        self.combo_subject_filter.clear()
        self.combo_subject_filter.addItem("All Subjects")
        if self.engine:
            for s in self.engine.get_distinct_subjects():
                self.combo_subject_filter.addItem(s)

    def _set_status_filter(self, status: str) -> None:
        self._current_status_filter = status
        self._update_status_pill_styles()
        self._refresh_tasks_list()

    def _update_status_pill_styles(self) -> None:
        for label, btn in self.status_buttons.items():
            if label == self._current_status_filter:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #272730;
                        color: #FFFFFF;
                        border: 1px solid #10B981;
                        border-radius: 12px;
                        padding: 4px 12px;
                        font-size: 11px;
                        font-weight: 700;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #18181B;
                        color: #71717A;
                        border: 1px solid #27272A;
                        border-radius: 12px;
                        padding: 4px 12px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #27272A;
                        color: #FFFFFF;
                    }
                """)

    def _on_search_changed(self, text: str) -> None:
        self._search_query = text.strip().lower()
        self._refresh_tasks_list()

    def _on_subject_filter_changed(self, subject: str) -> None:
        self._current_subject_filter = subject
        self._refresh_tasks_list()

    def _refresh_all(self) -> None:
        """Update KPIs and re-render task list."""
        self._refresh_kpis()
        self._refresh_tasks_list()

    def _refresh_kpis(self) -> None:
        if not self.engine:
            return
        now = datetime.now()
        all_todos = self.engine.todos
        pending = [t for t in all_todos if not t.is_completed]
        completed = [t for t in all_todos if t.is_completed]
        overdue = [t for t in pending if t.is_overdue(now)]

        week_end = now + timedelta(days=7)
        due_this_week = [t for t in pending if now <= t.due_date <= week_end]

        self.kpi_pending.value_label.setText(str(len(pending)))  # type: ignore
        self.kpi_due_week.value_label.setText(str(len(due_this_week)))  # type: ignore
        self.kpi_overdue.value_label.setText(str(len(overdue)))  # type: ignore
        self.kpi_completed.value_label.setText(str(len(completed)))  # type: ignore

    def _refresh_tasks_list(self) -> None:
        """Clear and rebuild task items based on current filters."""
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.engine:
            return

        now = datetime.now()
        todos = list(self.engine.todos)

        # 1. Subject filter
        if self._current_subject_filter and self._current_subject_filter != "All Subjects":
            todos = [t for t in todos if t.subject_name.lower() == self._current_subject_filter.lower()]

        # 2. Status filter
        if self._current_status_filter == "Pending":
            todos = [t for t in todos if not t.is_completed]
        elif self._current_status_filter == "Completed":
            todos = [t for t in todos if t.is_completed]
        elif self._current_status_filter == "Overdue":
            todos = [t for t in todos if t.is_overdue(now)]
        elif self._current_status_filter == "Due Soon (<24h)":
            todos = [t for t in todos if t.is_due_soon(24, now)]

        # 3. Search query filter
        if self._search_query:
            q = self._search_query
            todos = [
                t for t in todos
                if q in t.title.lower() or q in t.notes.lower() or q in t.subject_name.lower()
            ]

        # Sort: pending first by due date, then completed
        todos.sort(key=lambda t: (1 if t.is_completed else 0, t.due_date))

        if not todos:
            empty_lbl = QLabel(
                "No tasks found matching current filters.\nClick '+ New Task' above to add one!"
            )
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #71717A; font-size: 13px; padding: 40px;")
            self.tasks_layout.addWidget(empty_lbl)
        else:
            for todo in todos:
                row_widget = self._create_todo_row(todo)
                self.tasks_layout.addWidget(row_widget)

        self.tasks_layout.addStretch()

    def _create_todo_row(self, todo: StudyTodo) -> QWidget:
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
        chk.setChecked(todo.is_completed)
        chk.toggled.connect(lambda checked, t=todo: self._on_toggle_completed(t, checked))
        layout.addWidget(chk)

        # Content column
        content = QVBoxLayout()
        content.setSpacing(3)

        # Title & Subject Badge Row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        # Subject badge
        lbl_subj = QLabel(todo.subject_name.upper())
        lbl_subj.setStyleSheet("""
            background-color: #1E293B;
            color: #93C5FD;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        title_row.addWidget(lbl_subj)

        title_style = "color: #71717A; text-decoration: line-through;" if todo.is_completed else "color: #FFFFFF; font-weight: 600;"
        lbl_title = QLabel(todo.title)
        lbl_title.setStyleSheet(f"font-size: 13px; {title_style}")
        lbl_title.setWordWrap(True)
        title_row.addWidget(lbl_title, stretch=1)
        content.addLayout(title_row)

        # Meta row: Due date, notes, questions
        meta_parts = []
        if todo.is_completed:
            meta_parts.append("<span style='color: #10B981; font-weight: 600;'>✓ Completed</span>")
        else:
            now = datetime.now()
            due_str = todo.due_date.strftime("%a, %b %d at %H:%M")
            if todo.is_overdue(now):
                meta_parts.append(f"<span style='color: #EF4444; font-weight: 700;'>⚠️ OVERDUE ({due_str})</span>")
            elif todo.is_due_soon(24, now):
                meta_parts.append(f"<span style='color: #F59E0B; font-weight: 700;'>● Due Soon ({due_str})</span>")
            else:
                meta_parts.append(f"<span style='color: #71717A;'>Due: {due_str}</span>")

        if todo.notes:
            meta_parts.append(f"<span style='color: #52525B;'>{todo.notes}</span>")

        if todo.next_class_question:
            meta_parts.append(f"<span style='color: #38BDF8;'>❓ {todo.next_class_question}</span>")

        if meta_parts:
            lbl_meta = QLabel(" · ".join(meta_parts))
            lbl_meta.setStyleSheet("font-size: 11px;")
            content.addWidget(lbl_meta)

        layout.addLayout(content, stretch=1)

        # Action Buttons
        # 1. Focus button (only for pending tasks)
        if not todo.is_completed:
            btn_focus = QPushButton("▶ 15m")
            btn_focus.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_focus.setFixedSize(54, 28)
            btn_focus.setStyleSheet("""
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
            btn_focus.clicked.connect(lambda _, t=todo: self._on_focus_task(t))
            layout.addWidget(btn_focus)

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
        btn_edit.clicked.connect(lambda _, t=todo: self._open_edit_dialog(t))
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

    def _on_toggle_completed(self, todo: StudyTodo, checked: bool) -> None:
        if checked:
            self.engine.mark_todo_completed(todo.id, confidence="solid")
        else:
            self.engine.mark_todo_pending(todo.id)
        self.tasks_changed.emit()
        self._refresh_all()

    def _on_focus_task(self, todo: StudyTodo) -> None:
        self.start_task_focus_requested.emit(todo, 15)
        self.accept()

    def _open_create_dialog(self) -> None:
        default_sub = (
            self._current_subject_filter
            if self._current_subject_filter != "All Subjects"
            else None
        )
        dialog = EditTodoDialog(
            engine=self.engine,
            todo=None,
            default_subject=default_sub,
            parent=self,
        )
        dialog.todo_saved.connect(self._on_todo_saved)
        dialog.exec()

    def _open_edit_dialog(self, todo: StudyTodo) -> None:
        dialog = EditTodoDialog(
            engine=self.engine,
            todo=todo,
            parent=self,
        )
        dialog.todo_saved.connect(self._on_todo_saved)
        dialog.todo_deleted.connect(self._on_todo_deleted)
        dialog.exec()

    def _on_todo_saved(self, _todo: StudyTodo) -> None:
        self.tasks_changed.emit()
        self._refresh_all()

    def _on_todo_deleted(self, _todo_id: str) -> None:
        self.tasks_changed.emit()
        self._refresh_all()

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
            self.tasks_changed.emit()
            self._refresh_all()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)

"""Academic Task Backlog & Focus Management Modal for Study Station.

Provides the comprehensive task hub:
1. Macro KPI overview across all enrolled subjects (Pending, Due This Week, Overdue, Completed).
2. Tonight's Priority Focus hero banner with 1-click sprint initiation.
3. Multi-criteria filtering by Subject, Status (with live counters), and Search query with instant clear.
4. Quick-action empty state presets (+ Prepare Notes, + Lab Exercise, + Review Slides, + Revision).
5. 1-click focus sprint launcher tethered to any task.
6. Interactive check-offs with reversible toggle (pending <-> completed).
7. In-place Edit and Delete buttons for each task row.
8. Central "+ New Task" creator with keyboard ergonomics (<kbd>N</kbd>, <kbd>/</kbd>, <kbd>Esc</kbd>).
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
        self._current_priority_todo: StudyTodo | None = None

        self.setFixedSize(890, 680)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._refresh_all()

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

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(24, 20, 24, 20)
        self.content_layout.setSpacing(12)

        # ---------------------------------------------------------------------
        # 1. Header: Title + Active Badge, "+ New Task", and Close Button
        # ---------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        lbl_title = QLabel("ACADEMIC TASK BACKLOG")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 1px;")
        title_row.addWidget(lbl_title)

        self.lbl_header_badge = QLabel("● 0 ACTIVE")
        self.lbl_header_badge.setStyleSheet("""
            background-color: #1E293B;
            color: #38BDF8;
            border: 1px solid #334155;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            letter-spacing: 0.5px;
        """)
        title_row.addWidget(self.lbl_header_badge)
        title_row.addStretch()

        header_text.addLayout(title_row)

        lbl_sub = QLabel("Manage deliverables, deadlines, and launch focus sprints across all modules · Press / to search")
        lbl_sub.setStyleSheet("color: #71717A; font-size: 11px;")
        header_text.addWidget(lbl_sub)
        header.addLayout(header_text)

        header.addStretch()

        self.btn_new_task = QPushButton("+ New Task")
        self.btn_new_task.setToolTip("Create deliverable (N)")
        self.btn_new_task.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_new_task.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_task.clicked.connect(lambda: self._open_create_dialog())
        header.addWidget(self.btn_new_task)

        btn_close = QPushButton("✕")
        btn_close.setToolTip("Close (Esc)")
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
        # 3. Tonight's Priority Focus Hero Banner
        # ---------------------------------------------------------------------
        self.priority_banner = self._create_priority_banner()
        self.content_layout.addWidget(self.priority_banner)

        # ---------------------------------------------------------------------
        # 4. Filter & Search Controls
        # ---------------------------------------------------------------------
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        # Search box with clear button
        search_wrap = QHBoxLayout()
        search_wrap.setSpacing(4)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Filter by title, notes, or course... (Press / to focus)")
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
        search_wrap.addWidget(self.txt_search, stretch=1)

        self.btn_clear_search = QPushButton("✕")
        self.btn_clear_search.setToolTip("Clear filter")
        self.btn_clear_search.setFixedSize(26, 26)
        self.btn_clear_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_search.setStyleSheet("""
            QPushButton {
                background: #27272A;
                color: #A1A1AA;
                border: none;
                border-radius: 13px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #3F3F46;
                color: #FFFFFF;
            }
        """)
        self.btn_clear_search.hide()
        self.btn_clear_search.clicked.connect(self.txt_search.clear)
        search_wrap.addWidget(self.btn_clear_search)

        filter_bar.addLayout(search_wrap, stretch=3)

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

        # Sort Mode Selector
        self.combo_sort = QComboBox()
        self.combo_sort.setStyleSheet("""
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
        self.combo_sort.addItem("Sort: Deadline (Earliest)", "due_earliest")
        self.combo_sort.addItem("Sort: Academic Urgency", "urgency")
        self.combo_sort.addItem("Sort: Subject (A–Z)", "subject")
        self.combo_sort.addItem("Sort: Title (A–Z)", "title")
        self.combo_sort.currentIndexChanged.connect(lambda: self._refresh_tasks_list())
        filter_bar.addWidget(self.combo_sort, stretch=2)

        self.content_layout.addLayout(filter_bar)

        # Status Segmented Filter Pills with dynamic counters
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
        # 5. Scrollable Tasks List
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

        # ---------------------------------------------------------------------
        # 6. Footer Utility & Safety Bar
        # ---------------------------------------------------------------------
        footer_bar = QHBoxLayout()
        footer_bar.setContentsMargins(4, 2, 4, 0)
        footer_bar.setSpacing(8)

        lbl_shortcuts = QLabel("⌨ Shortcuts: [N] New Task  ·  [/] Search  ·  [Esc] Close")
        lbl_shortcuts.setStyleSheet("color: #52525B; font-size: 11px;")
        footer_bar.addWidget(lbl_shortcuts)

        footer_bar.addStretch()

        self.btn_empty_tasks = QPushButton("🗑 Clear All Tasks...")
        self.btn_empty_tasks.setToolTip("Clear all tasks from the backlog (safe 2-step confirmation)")
        self.btn_empty_tasks.setStyleSheet("""
            QPushButton {
                background: #18181B;
                color: #71717A;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #201315;
                color: #FCA5A5;
                border-color: #5C1D24;
            }
            QPushButton:disabled { color: #3F3F46; border-color: #1E1E26; background-color: #0E0E12; }
        """)
        self.btn_empty_tasks.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_empty_tasks.clicked.connect(self._on_empty_tasks_clicked)
        footer_bar.addWidget(self.btn_empty_tasks)

        self.content_layout.addLayout(footer_bar)

    def _create_kpi_card(self, title: str, initial_val: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setStyleSheet("""
            QFrame#kpiCard {
                background-color: #16161C;
                border: 1px solid #272732;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #8E8EA0; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;")
        layout.addWidget(lbl_t)

        lbl_v = QLabel(initial_val)
        lbl_v.setStyleSheet(f"color: {accent_color}; font-size: 22px; font-weight: 800;")
        layout.addWidget(lbl_v)

        card.value_label = lbl_v  # type: ignore
        return card

    def _create_priority_banner(self) -> QFrame:
        """Create highlighted banner for Tonight's most urgent priority task."""
        card = QFrame()
        card.setObjectName("priorityFocusBanner")
        card.setStyleSheet("""
            QFrame#priorityFocusBanner {
                background-color: #151522;
                border: 1px solid #4F46E5;
                border-radius: 8px;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        lbl_badge = QLabel("⚡ TONIGHT'S PRIORITY FOCUS")
        lbl_badge.setStyleSheet("""
            background-color: #312E81;
            color: #C7D2FE;
            border: 1px solid #4338CA;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 800;
            padding: 3px 6px;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(lbl_badge)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.lbl_prio_title = QLabel("")
        self.lbl_prio_title.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 700;")
        text_col.addWidget(self.lbl_prio_title)

        self.lbl_prio_due = QLabel("")
        self.lbl_prio_due.setStyleSheet("color: #A5B4FC; font-size: 11px;")
        text_col.addWidget(self.lbl_prio_due)
        layout.addLayout(text_col, stretch=1)

        self.btn_prio_focus_15 = QPushButton("▶ 15m Focus")
        self.btn_prio_focus_15.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prio_focus_15.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
        """)
        self.btn_prio_focus_15.clicked.connect(lambda: self._on_focus_priority_task(15))
        layout.addWidget(self.btn_prio_focus_15)

        self.btn_prio_focus_25 = QPushButton("25m")
        self.btn_prio_focus_25.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prio_focus_25.setStyleSheet("""
            QPushButton {
                background-color: #1E1B4B;
                color: #C7D2FE;
                border: 1px solid #4338CA;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #312E81;
                color: #FFFFFF;
            }
        """)
        self.btn_prio_focus_25.clicked.connect(lambda: self._on_focus_priority_task(25))
        layout.addWidget(self.btn_prio_focus_25)

        card.hide()
        return card

    def _on_focus_priority_task(self, minutes: int = 15) -> None:
        if self._current_priority_todo:
            self._on_focus_task(self._current_priority_todo, minutes)

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
        self.btn_clear_search.setVisible(bool(self._search_query))
        self._refresh_tasks_list()

    def _on_subject_filter_changed(self, subject: str) -> None:
        self._current_subject_filter = subject
        self._refresh_tasks_list()

    def _refresh_all(self) -> None:
        """Update KPIs, priority banner, and re-render task list."""
        self._refresh_kpis()
        self._refresh_priority_banner()
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
        due_soon_count = len([t for t in pending if t.is_due_soon(24, now)])

        self.kpi_pending.value_label.setText(str(len(pending)))  # type: ignore
        self.kpi_due_week.value_label.setText(str(len(due_this_week)))  # type: ignore
        self.kpi_overdue.value_label.setText(str(len(overdue)))  # type: ignore
        self.kpi_completed.value_label.setText(str(len(completed)))  # type: ignore

        # Header live badge
        if hasattr(self, "btn_empty_tasks"):
            self.btn_empty_tasks.setEnabled(bool(all_todos))

        if pending:
            self.lbl_header_badge.setText(f"● {len(pending)} PENDING")
            self.lbl_header_badge.setStyleSheet("""
                background-color: #1E293B;
                color: #38BDF8;
                border: 1px solid #334155;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 6px;
                letter-spacing: 0.5px;
            """)
        else:
            self.lbl_header_badge.setText("✓ ALL CAUGHT UP")
            self.lbl_header_badge.setStyleSheet("""
                background-color: #064E3B;
                color: #6EE7B7;
                border: 1px solid #047857;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 6px;
                letter-spacing: 0.5px;
            """)

        # Update button labels with live counts
        counts = {
            "All": len(all_todos),
            "Pending": len(pending),
            "Due Soon (<24h)": due_soon_count,
            "Overdue": len(overdue),
            "Completed": len(completed),
        }
        for label, count in counts.items():
            if label in self.status_buttons:
                btn = self.status_buttons[label]
                btn.setText(f"{label} ({count})")

    def _refresh_priority_banner(self) -> None:
        if not self.engine:
            self.priority_banner.hide()
            return

        now = datetime.now()
        priority_todo = self.engine.get_priority_study_todo(now)
        if not priority_todo or priority_todo.is_completed:
            self.priority_banner.hide()
            return

        self._current_priority_todo = priority_todo
        clean_sub = ScheduleEngine.clean_subject_name(priority_todo.subject_name)
        self.lbl_prio_title.setText(f"{clean_sub} · {priority_todo.title}")

        if priority_todo.is_overdue(now):
            due_txt = f"⚠️ OVERDUE (was due {priority_todo.due_date.strftime('%a, %b %d at %H:%M')})"
            self.lbl_prio_due.setText(due_txt)
            self.lbl_prio_due.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 700;")
        else:
            rel = self._format_relative_due(priority_todo.due_date, now)
            self.lbl_prio_due.setText(f"Due {rel} ({priority_todo.due_date.strftime('%a, %b %d at %H:%M')})")
            self.lbl_prio_due.setStyleSheet("color: #A5B4FC; font-size: 11px;")

        self.priority_banner.show()

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
            clean_filt = ScheduleEngine.clean_subject_name(self._current_subject_filter).lower()
            todos = [
                t for t in todos
                if ScheduleEngine.clean_subject_name(t.subject_name).lower() == clean_filt
            ]

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

        # Multi-criteria Backlog Sorting (Tier 2)
        sort_mode = self.combo_sort.currentData() if hasattr(self, "combo_sort") and self.combo_sort.currentData() else "due_earliest"
        if sort_mode == "urgency":
            todos.sort(key=lambda t: (1 if t.is_completed else 0, -self.engine.calculate_todo_urgency_score(t, now)))
        elif sort_mode == "subject":
            todos.sort(key=lambda t: (1 if t.is_completed else 0, ScheduleEngine.clean_subject_name(t.subject_name).lower(), t.due_date))
        elif sort_mode == "title":
            todos.sort(key=lambda t: (1 if t.is_completed else 0, t.title.lower()))
        else:
            todos.sort(key=lambda t: (1 if t.is_completed else 0, t.due_date))

        if not todos:
            empty_frame = QFrame()
            empty_frame.setStyleSheet("background: transparent; border: none; padding: 24px;")
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setSpacing(12)

            lbl_hint = QLabel("No tasks found matching current filters.")
            lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_hint.setStyleSheet("color: #71717A; font-size: 13px; font-weight: 500;")
            empty_layout.addWidget(lbl_hint)

            lbl_presets_hint = QLabel("Quick-seed a deliverable with 1-click:")
            lbl_presets_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_presets_hint.setStyleSheet("color: #52525B; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
            empty_layout.addWidget(lbl_presets_hint)

            presets_row = QHBoxLayout()
            presets_row.setSpacing(8)
            presets_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

            presets = [
                "+ Prepare Next Class Notes",
                "+ Complete Lab Exercise",
                "+ Review Lecture Slides",
                "+ Exam Revision Sprint",
            ]
            for p_text in presets:
                btn_p = QPushButton(p_text)
                btn_p.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_p.setStyleSheet("""
                    QPushButton {
                        background-color: #18181F;
                        color: #93C5FD;
                        border: 1px solid #283548;
                        border-radius: 12px;
                        padding: 5px 12px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #243048;
                        color: #FFFFFF;
                        border-color: #38BDF8;
                    }
                """)
                clean_p = p_text.replace("+ ", "")
                btn_p.clicked.connect(lambda _, t=clean_p: self._open_create_dialog(preset_title=t))
                presets_row.addWidget(btn_p)

            empty_layout.addLayout(presets_row)
            self.tasks_layout.addWidget(empty_frame)
        else:
            for todo in todos:
                row_widget = self._create_todo_row(todo)
                self.tasks_layout.addWidget(row_widget)

        self.tasks_layout.addStretch()

    def _get_subject_core_colors(self, subject_name: str) -> tuple[str, str]:
        """Return (bg_color, fg_color) for subject badge based on core type."""
        clean = ScheduleEngine.clean_subject_name(subject_name).lower()
        core = "COURS"
        if self.engine:
            for s in self.engine.sessions:
                if self.engine.clean_subject_name(s.subject.name).lower() == clean:
                    core = s.subject.core.upper()
                    break

        core_map = {
            "TP": ("#064E3B", "#6EE7B7"),      # Emerald
            "COURS": ("#1E293B", "#93C5FD"),   # Slate Blue
            "TD": ("#2E1065", "#C4B5FD"),      # Indigo
            "CI": ("#451A03", "#FCD34D"),      # Amber
        }
        return core_map.get(core, ("#1E293B", "#93C5FD"))

    @classmethod
    def _format_relative_due(cls, due_date: datetime, now: datetime) -> str:
        days_diff = (due_date.date() - now.date()).days
        delta = due_date - now
        total_seconds = delta.total_seconds()
        hours = int(total_seconds // 3600)
        mins = int((total_seconds % 3600) // 60)

        if total_seconds < 0:
            past_hours = abs(int(total_seconds // 3600))
            if past_hours < 24:
                return f"⚠️ OVERDUE by {past_hours}h"
            past_days = abs(days_diff)
            return f"⚠️ OVERDUE by {past_days} day{'s' if past_days > 1 else ''}"

        if days_diff == 0:
            time_str = due_date.strftime("%H:%M")
            rel = f"in {hours}h {mins:02d}m" if hours > 0 else f"in {mins}m"
            return f"Today at {time_str} ({rel})"
        elif days_diff == 1:
            return f"Tomorrow at {due_date.strftime('%H:%M')}"
        elif days_diff < 7:
            day_name = due_date.strftime("%A")
            return f"{day_name} (in {days_diff} days)"
        else:
            return f"in {days_diff} days ({due_date.strftime('%b %d')})"

    def _create_todo_row(self, todo: StudyTodo) -> QWidget:
        row = QFrame()
        row.setObjectName("todoRow")
        row.setStyleSheet("""
            QFrame#todoRow {
                background-color: #16161C;
                border: 1px solid #272732;
                border-radius: 8px;
            }
            QFrame#todoRow:hover {
                background-color: #1A1A24;
                border-color: #383848;
            }
            QLabel {
                background: transparent;
                border: none;
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

        # Subject badge with core colors
        bg_color, fg_color = self._get_subject_core_colors(todo.subject_name)
        clean_sub = ScheduleEngine.clean_subject_name(todo.subject_name)
        lbl_subj = QLabel(clean_sub.upper())
        lbl_subj.setStyleSheet(f"""
            background-color: {bg_color};
            color: {fg_color};
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        title_row.addWidget(lbl_subj)

        title_style = (
            "color: #71717A; text-decoration: line-through;"
            if todo.is_completed
            else "color: #FFFFFF; font-weight: 600;"
        )
        lbl_title = QLabel(todo.title)
        lbl_title.setStyleSheet(f"font-size: 13px; {title_style}")
        lbl_title.setWordWrap(True)
        title_row.addWidget(lbl_title, stretch=1)
        content.addLayout(title_row)

        # Meta row: Due date, notes, questions
        meta_parts = []
        if todo.is_completed:
            done_date_str = f" on {todo.completed_at.strftime('%b %d')}" if todo.completed_at else ""
            meta_parts.append(f"<span style='color: #10B981; font-weight: 600;'>✓ Completed{done_date_str}</span>")
        else:
            now = datetime.now()
            due_str = todo.due_date.strftime("%a, %b %d at %H:%M")
            if todo.is_overdue(now):
                rel = self._format_relative_due(todo.due_date, now)
                meta_parts.append(f"<span style='color: #EF4444; font-weight: 700;'>{rel} ({due_str})</span>")
            elif todo.is_due_soon(24, now):
                rel = self._format_relative_due(todo.due_date, now)
                meta_parts.append(f"<span style='color: #F59E0B; font-weight: 700;'>● {rel}</span>")
            else:
                rel = self._format_relative_due(todo.due_date, now)
                meta_parts.append(f"<span style='color: #71717A;'>Due: {rel}</span>")

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
            btn_focus.setToolTip("Start 15-minute Focus Sprint")
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
            btn_focus.clicked.connect(lambda _, t=todo: self._on_focus_task(t, 15))
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

    def _on_focus_task(self, todo: StudyTodo, minutes: int = 15) -> None:
        self.start_task_focus_requested.emit(todo, minutes)
        self.accept()

    def _open_create_dialog(self, preset_title: str | None = None) -> None:
        default_sub = (
            self._current_subject_filter
            if self._current_subject_filter != "All Subjects"
            else None
        )
        dialog = EditTodoDialog(
            engine=self.engine,
            todo=None,
            default_subject=default_sub,
            preset_title=preset_title,
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

    def _on_empty_tasks_clicked(self) -> None:
        if not self.engine or not self.engine.todos:
            QMessageBox.information(
                self,
                "Tasks Empty",
                "Your task backlog is already empty. There are no tasks to clear.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Empty Task Backlog",
            "Are you sure you want to clear all tasks from your backlog?\n\nThis will remove all pending and completed deliverables for the current profile. This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for todo in list(self.engine.todos):
                self.engine.delete_todo(todo.id)
            self.tasks_changed.emit()
            self._refresh_all()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        elif event.key() == Qt.Key.Key_Slash and not self.txt_search.hasFocus():
            self.txt_search.setFocus()
            self.txt_search.selectAll()
            event.accept()
        elif event.key() == Qt.Key.Key_N and (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier or not self.txt_search.hasFocus()
        ):
            self._open_create_dialog()
            event.accept()
        else:
            super().keyPressEvent(event)

"""Weekly Schedule Grid dialog modeled after university schedule (docs/grid.pdf / Google Calendar)."""

from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QPoint, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
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


class ClassGridCard(QPushButton):
    """An interactive class card in the weekly schedule grid."""

    clicked_session = Signal(str)  # subject name

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

        # Badge colors
        core_colors = {
            "TP": ("#064E3B", "#34D399"),      # Emerald
            "COURS": ("#1E3A5F", "#60A5FA"),   # Blue
            "TD": ("#4C1D95", "#A78BFA"),      # Purple
            "CI": ("#78350F", "#FBBF24"),      # Amber
        }
        bg_badge, fg_badge = core_colors.get(core_type, ("#27272A", "#A1A1AA"))

        current_border = "border: 2px solid #10B981;" if is_current else "border: 1px solid #27272A;"
        current_bg = "background-color: #18221E;" if is_current else "background-color: #141418;"

        self.setStyleSheet(f"""
            ClassGridCard {{
                {current_bg}
                {current_border}
                border-radius: 8px;
                padding: 6px 8px;
                text-align: left;
            }}
            ClassGridCard:hover {{
                background-color: #1C1C24;
                border: 1px solid #3F3F46;
            }}
            ClassGridCard:pressed {{
                background-color: #27272A;
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
            padding: 2px 5px;
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
        lbl_name.setWordWrap(True)
        lbl_name.setStyleSheet("color: #F4F4F5; font-size: 12px; font-weight: 700;")
        layout.addWidget(lbl_name)

        layout.addStretch()

        # Time footer
        lbl_time = QLabel(f"{session.time_slot.start} - {session.time_slot.end}")
        lbl_time.setStyleSheet("color: #52525B; font-size: 10px; font-family: monospace;")
        layout.addWidget(lbl_time)

        self.clicked.connect(lambda: self.clicked_session.emit(self.session.subject.name))


class WeeklyScheduleGridDialog(QDialog):
    """Google Calendar / grid.pdf style visual weekly timetable and subject picker."""

    subject_selected = Signal(str)
    edit_timetable_requested = Signal()

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
        self.setWindowTitle("Weekly Schedule")
        self.setFixedSize(1120, 660)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._sessions = sessions
        self._current_subject = current_subject
        self._now = datetime.now()

        self._build_ui()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)

        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #0F0F12;
                border: 1px solid #27272A;
                border-radius: 14px;
            }
        """)
        outer_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ---------------------------------------------------------------------
        # Top Header Bar
        # ---------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        lbl_title = QLabel("WEEKLY SCHEDULE")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 1.5px;")
        title_col.addWidget(lbl_title)

        lbl_subtitle = QLabel("Click any class block to set as active subject · Press Esc to close")
        lbl_subtitle.setStyleSheet("color: #71717A; font-size: 12px;")
        title_col.addWidget(lbl_subtitle)
        header.addLayout(title_col)

        header.addStretch()

        # Action Buttons
        btn_open_doc = QPushButton("📄 Original PDF")
        btn_open_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_doc.setStyleSheet("""
            QPushButton {
                background-color: #1A1A20;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 16px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
                border-color: #3F3F46;
            }
        """)
        btn_open_doc.clicked.connect(self._open_original_doc)
        header.addWidget(btn_open_doc)

        btn_edit = QPushButton("✏ Edit Classes")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #1A1A20;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 16px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
                border-color: #3F3F46;
            }
        """)
        btn_edit.clicked.connect(self._on_edit_timetable)
        header.addWidget(btn_edit)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1A1A20;
                color: #71717A;
                border: 1px solid #27272A;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
                border-color: #3F3F46;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header.addWidget(btn_close)

        layout.addLayout(header)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1F1F23; background-color: #1F1F23; max-height: 1px;")
        layout.addWidget(sep)

        # ---------------------------------------------------------------------
        # Calendar Grid
        # ---------------------------------------------------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(8)

        # Corner cell: TIME label
        lbl_corner = QLabel("TIME")
        lbl_corner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_corner.setStyleSheet("color: #52525B; font-size: 11px; font-weight: 800; letter-spacing: 1px;")
        grid.addWidget(lbl_corner, 0, 0)

        # Day Headers (Row 0, Col 1..6)
        day_keys = [d[0] for d in self.DAYS]
        current_day_idx = self._now.weekday()  # Mon=0, Sat=5
        for col_idx, (day_code, day_full) in enumerate(self.DAYS, start=1):
            is_today = (col_idx - 1) == current_day_idx
            today_color = "color: #10B981;" if is_today else "color: #D4D4D8;"
            today_bg = "background-color: #14221D; border: 1px solid #059669;" if is_today else "background-color: #141418; border: 1px solid #27272A;"
            
            day_box = QFrame()
            day_box.setStyleSheet(f"{today_bg}; border-radius: 6px; padding: 4px 6px;")
            day_box_layout = QVBoxLayout(day_box)
            day_box_layout.setContentsMargins(2, 2, 2, 2)
            day_box_layout.setSpacing(0)

            lbl_day = QLabel(day_code.upper())
            lbl_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_day.setStyleSheet(f"{today_color}; font-size: 13px; font-weight: 800;")
            day_box_layout.addWidget(lbl_day)

            grid.addWidget(day_box, 0, col_idx)

        # Time slot rows (Rows 1..5)
        for row_idx, (start_t, end_t, label_t) in enumerate(self.TIME_SLOTS, start=1):
            time_lbl = QLabel(label_t)
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            time_lbl.setStyleSheet("color: #71717A; font-size: 11px; font-family: monospace; font-weight: 600;")
            time_lbl.setFixedWidth(100)
            grid.addWidget(time_lbl, row_idx, 0)

            # Match sessions for this slot
            for col_idx, (day_code, _) in enumerate(self.DAYS, start=1):
                matching = [
                    s for s in self._sessions
                    if s.day.lower() == day_code.lower()
                    and s.time_slot.start == start_t
                ]

                if matching:
                    session = matching[0]
                    is_current_session = (
                        (col_idx - 1) == current_day_idx
                        and session.time_slot.contains(self._now.strftime("%H:%M"))
                    )
                    card = ClassGridCard(session, is_current=is_current_session)
                    card.clicked_session.connect(self._on_session_clicked)
                    grid.addWidget(card, row_idx, col_idx)
                else:
                    # Empty quiet slot
                    empty = QFrame()
                    empty.setStyleSheet("""
                        background-color: #111114;
                        border: 1px dashed #1E1E24;
                        border-radius: 8px;
                    """)
                    empty.setMinimumHeight(74)
                    grid.addWidget(empty, row_idx, col_idx)

        # Set column stretch
        grid.setColumnStretch(0, 1)
        for i in range(1, 7):
            grid.setColumnStretch(i, 3)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

    def _open_original_doc(self) -> None:
        """Open docs/grid.pdf in system PDF viewer."""
        doc_path = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "grid.pdf"
        if doc_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(doc_path)))

    def _on_session_clicked(self, subject_name: str) -> None:
        """Select subject and close dialog."""
        self.subject_selected.emit(subject_name)
        self.accept()

    def _on_edit_timetable(self) -> None:
        self.edit_timetable_requested.emit()
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

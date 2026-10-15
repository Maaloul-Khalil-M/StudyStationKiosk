"""Dialog for adding, editing, or starting focus on a scheduled class session."""

from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class ClassSessionDialog(QDialog):
    """Direct visual calendar dialog to edit, delete, or add a class session."""

    start_focus_requested = Signal(str)  # subject_name
    session_saved = Signal(object, object)  # (old_session | None, new_session)
    session_deleted = Signal(object)  # (session)

    DAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"]
    CORES = ["TP", "COURS", "TD", "CI"]

    def __init__(
        self,
        session: AcademicSession | None = None,
        default_day: str = "Lun",
        default_start: str = "08:00",
        default_end: str = "09:30",
        existing_subjects: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.default_day = default_day
        self.default_start = default_start
        self.default_end = default_end
        self.existing_subjects = existing_subjects or []

        self.setFixedSize(500, 480 if session else 410)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #121216;
                border: 1px solid #27272A;
                border-radius: 14px;
            }
        """)
        main_layout.addWidget(container)

        card_layout = QVBoxLayout(container)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(16)

        # Header Title
        title_text = "MANAGE CLASS" if self.session else "ADD CLASS"
        self.lbl_title = QLabel(title_text)
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1.5px;")
        card_layout.addWidget(self.lbl_title)

        # Optional Start Focus Action (if editing existing session)
        if self.session:
            clean_sub = ScheduleEngine.clean_subject_name(self.session.subject.name)
            self.btn_focus_action = QPushButton(f"▶  Start Focus on {clean_sub}")
            self.btn_focus_action.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: 700;
                    border-radius: 18px;
                    padding: 9px 18px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            self.btn_focus_action.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_focus_action.clicked.connect(self._on_start_focus)
            card_layout.addWidget(self.btn_focus_action)

            divider = QFrame()
            divider.setFixedHeight(1)
            divider.setStyleSheet("background-color: #222228;")
            card_layout.addWidget(divider)

        # Form: Day & Time row
        row_time = QHBoxLayout()
        row_time.setSpacing(10)

        col_day = QVBoxLayout()
        lbl_day = QLabel("DAY")
        lbl_day.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        self.cmb_day = QComboBox()
        for d in self.DAYS:
            self.cmb_day.addItem(d)
        if self.session:
            self.cmb_day.setCurrentText(self.session.day)
        else:
            self.cmb_day.setCurrentText(self.default_day)
        col_day.addWidget(lbl_day)
        col_day.addWidget(self.cmb_day)
        row_time.addLayout(col_day, stretch=2)

        col_start = QVBoxLayout()
        lbl_start = QLabel("START")
        lbl_start.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        self.txt_start = QLineEdit()
        self.txt_start.setText(self.session.time_slot.start if self.session else self.default_start)
        col_start.addWidget(lbl_start)
        col_start.addWidget(self.txt_start)
        row_time.addLayout(col_start, stretch=3)

        col_end = QVBoxLayout()
        lbl_end = QLabel("END")
        lbl_end.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        self.txt_end = QLineEdit()
        self.txt_end.setText(self.session.time_slot.end if self.session else self.default_end)
        col_end.addWidget(lbl_end)
        col_end.addWidget(self.txt_end)
        row_time.addLayout(col_end, stretch=3)

        card_layout.addLayout(row_time)

        # Form: Subject Name
        col_subject = QVBoxLayout()
        lbl_subject = QLabel("SUBJECT NAME")
        lbl_subject.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        self.txt_subject = QLineEdit()
        self.txt_subject.setPlaceholderText("e.g. Visualisation des données")
        if self.session:
            self.txt_subject.setText(self.session.subject.name)
        col_subject.addWidget(lbl_subject)
        col_subject.addWidget(self.txt_subject)
        card_layout.addLayout(col_subject)

        # Form: Pedagogical Core & Room row
        row_core = QHBoxLayout()
        row_core.setSpacing(10)

        col_core = QVBoxLayout()
        lbl_core = QLabel("TYPE")
        lbl_core.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        self.cmb_core = QComboBox()
        for c in self.CORES:
            self.cmb_core.addItem(c)
        if self.session:
            self.cmb_core.setCurrentText(self.session.subject.core.upper())
        col_core.addWidget(lbl_core)
        col_core.addWidget(self.cmb_core)
        row_core.addLayout(col_core, stretch=2)

        col_loc = QVBoxLayout()
        lbl_loc = QLabel("ROOM / LAB")
        lbl_loc.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        self.txt_location = QLineEdit()
        self.txt_location.setPlaceholderText("e.g. Lab 20, SC 3")
        if self.session:
            self.txt_location.setText(self.session.location)
        col_loc.addWidget(lbl_loc)
        col_loc.addWidget(self.txt_location)
        row_core.addLayout(col_loc, stretch=3)

        card_layout.addLayout(row_core)

        card_layout.addStretch()

        # Bottom Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        if self.session:
            self.btn_delete = QPushButton("Delete Class")
            self.btn_delete.setStyleSheet(BUTTON_DANGER_STYLE)
            self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_delete.clicked.connect(self._on_delete)
            actions_layout.addWidget(self.btn_delete)

        actions_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(BUTTON_NAV_STYLE)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        actions_layout.addWidget(self.btn_cancel)

        save_label = "Save Changes" if self.session else "+ Add Class"
        self.btn_save = QPushButton(save_label)
        self.btn_save.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._on_save)
        actions_layout.addWidget(self.btn_save)

        card_layout.addLayout(actions_layout)

    def _on_start_focus(self) -> None:
        if self.session:
            self.start_focus_requested.emit(self.session.subject.name)
            self.accept()

    def _on_delete(self) -> None:
        if self.session:
            self.session_deleted.emit(self.session)
            self.accept()

    def _on_save(self) -> None:
        subject_name = self.txt_subject.text().strip()
        start = self.txt_start.text().strip()
        end = self.txt_end.text().strip()
        day = self.cmb_day.currentText()
        core = self.cmb_core.currentText()
        location = self.txt_location.text().strip()

        if not subject_name or not start or not end:
            return

        new_session = AcademicSession(
            day=day,
            time_slot=TimeSlot(start=start, end=end),
            subject=Subject(name=subject_name, core=core),
            location=location,
        )

        self.session_saved.emit(self.session, new_session)
        self.accept()

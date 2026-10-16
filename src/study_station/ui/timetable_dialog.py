"""Controller for managing and editing the weekly timetable."""

from pathlib import Path
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHeaderView,
    QLineEdit,
    QPushButton,
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
    normalize_time_str,
)
from study_station.ui.class_session_dialog import ClassSessionDialog


class TimetableDialog(QDialog):
    """Dialog allowing students to view, add, and delete weekly timetable sessions."""

    timetable_changed = Signal(list)  # list[AcademicSession]

    def __init__(self, sessions: list[AcademicSession], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Weekly Timetable")
        self.setFixedSize(760, 580)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._sessions = list(sessions)

        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #121215;
                border: 1px solid #27272A;
                border-radius: 14px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Load UI
        from study_station.core.resources import get_ui_path
        ui_path = get_ui_path("timetable_dialog.ui")
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, container)
        ui_file.close()
        self.ui.setWindowFlags(Qt.WindowType.Widget)

        container_layout.addWidget(self.ui)

        # UI References
        self.table: QTableWidget = self.ui.findChild(QTableWidget, "tableSessions")
        self.btn_delete: QPushButton = self.ui.findChild(QPushButton, "btnDelete")
        self.btn_add: QPushButton = self.ui.findChild(QPushButton, "btnAdd")
        self.btn_close: QPushButton = self.ui.findChild(QPushButton, "btnClose")

        self.cmb_day: QComboBox = self.ui.findChild(QComboBox, "cmbDay")
        self.txt_start: QLineEdit = self.ui.findChild(QLineEdit, "txtStart")
        self.txt_end: QLineEdit = self.ui.findChild(QLineEdit, "txtEnd")
        self.txt_subject: QLineEdit = self.ui.findChild(QLineEdit, "txtSubject")
        self.cmb_core: QComboBox = self.ui.findChild(QComboBox, "cmbCore")
        self.txt_location: QLineEdit = self.ui.findChild(QLineEdit, "txtLocation")

        # Setup Form Options
        for day in ("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"):
            self.cmb_day.addItem(day)

        for core in ("COURS", "TD", "TP", "CI"):
            self.cmb_core.addItem(core)

        # Pre-fill sensible default times
        if not self.txt_start.text():
            self.txt_start.setText("08:00")
        if not self.txt_end.text():
            self.txt_end.setText("09:30")

        # Setup Table
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Day", "Time", "Subject", "Type", "Location"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self._refresh_table()

        # Connections
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_add.clicked.connect(self._on_add)
        self.btn_close.clicked.connect(self._on_save_and_close)
        self.table.cellDoubleClicked.connect(self._on_table_cell_double_clicked)

    def _refresh_table(self) -> None:
        """Populate table sorted chronologically by day and start time."""
        self._sessions.sort(key=lambda s: (s.day_index, s.time_slot.start))
        self.table.setRowCount(len(self._sessions))

        for row, s in enumerate(self._sessions):
            day_item = QTableWidgetItem(s.day)
            day_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, day_item)

            time_str = f"{s.time_slot.start} - {s.time_slot.end}"
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, time_item)

            clean_name = ScheduleEngine.clean_subject_name(s.subject.name)
            self.table.setItem(row, 2, QTableWidgetItem(clean_name))

            core_item = QTableWidgetItem(s.subject.core)
            core_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, core_item)

            self.table.setItem(row, 4, QTableWidgetItem(s.location))

    def _on_table_cell_double_clicked(self, row: int, col: int) -> None:
        if 0 <= row < len(self._sessions):
            session = self._sessions[row]
            existing_names = sorted({s.subject.name for s in self._sessions})
            dialog = ClassSessionDialog(session=session, existing_subjects=existing_names, parent=self)
            dialog.session_saved.connect(self._on_session_saved)
            dialog.session_deleted.connect(self._on_session_deleted)
            dialog.exec()

    def _on_session_saved(self, old_s: AcademicSession | None, new_s: AcademicSession) -> None:
        if old_s and old_s in self._sessions:
            idx = self._sessions.index(old_s)
            self._sessions[idx] = new_s
        else:
            self._sessions.append(new_s)
        self._refresh_table()

    def _on_session_deleted(self, s: AcademicSession) -> None:
        if s in self._sessions:
            self._sessions.remove(s)
            self._refresh_table()

    def _on_delete(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row_idx = selected_rows[0].row()
        if 0 <= row_idx < len(self._sessions):
            del self._sessions[row_idx]
            self._refresh_table()

    def _on_add(self) -> None:
        day = self.cmb_day.currentText()
        raw_start = self.txt_start.text().strip()
        raw_end = self.txt_end.text().strip()
        subject = self.txt_subject.text().strip()
        core = self.cmb_core.currentText()
        location = self.txt_location.text().strip()

        start = normalize_time_str(raw_start) or "08:00"
        end = normalize_time_str(raw_end) or "09:30"

        if not subject:
            self.txt_subject.setFocus()
            return

        session = AcademicSession(
            day=day,
            time_slot=TimeSlot(start=start, end=end),
            subject=Subject(name=subject, core=core),
            location=location,
        )
        self._sessions.append(session)
        self._refresh_table()

        # Clear inputs
        self.txt_subject.clear()
        self.txt_location.clear()

    def _on_save_and_close(self) -> None:
        self.timetable_changed.emit(self._sessions)
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


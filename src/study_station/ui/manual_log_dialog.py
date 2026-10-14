"""Controller for logging offline study time."""

from pathlib import Path
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine


class ManualLogDialog(QDialog):
    """Dialog allowing students to manually record review completed away from the computer."""

    time_logged = Signal(str, int)  # (subject_name, duration_minutes)

    def __init__(
        self,
        subjects: list[str],
        default_subject: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Log Offline Study Time")
        self.setFixedSize(460, 360)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

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
        ui_path = Path(__file__).resolve().parent / "designer" / "manual_log_dialog.ui"
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, container)
        ui_file.close()
        self.ui.setWindowFlags(Qt.WindowType.Widget)

        container_layout.addWidget(self.ui)

        # Widget references
        self.cmb_subject: QComboBox = self.ui.findChild(QComboBox, "cmbSubject")
        self.spn_minutes: QSpinBox = self.ui.findChild(QSpinBox, "spnMinutes")
        self.btn_cancel: QPushButton = self.ui.findChild(QPushButton, "btnCancel")
        self.btn_save: QPushButton = self.ui.findChild(QPushButton, "btnSave")

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)

        # Populate subjects
        self._subjects = subjects
        for s in subjects:
            clean = ScheduleEngine.clean_subject_name(s)
            self.cmb_subject.addItem(clean, userData=s)

        if default_subject:
            idx = self.cmb_subject.findData(default_subject)
            if idx >= 0:
                self.cmb_subject.setCurrentIndex(idx)

    def _on_save(self) -> None:
        raw_subject = self.cmb_subject.currentData() or self.cmb_subject.currentText()
        minutes = self.spn_minutes.value()
        self.time_logged.emit(raw_subject, minutes)
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


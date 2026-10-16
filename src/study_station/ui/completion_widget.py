"""Completion screen controller wrapping completion_screen.ui."""

from pathlib import Path
from PySide6.QtCore import QFile, QTimer, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class CompletionWidget(QWidget):
    """Completion confirmation screen showing logged progress."""

    dismissed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Load Qt Designer UI
        from study_station.core.resources import get_ui_path
        ui_path = get_ui_path("completion_screen.ui")
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        # UI References
        self.lbl_subject: QLabel = self.ui.findChild(QLabel, "lblSubject")
        self.lbl_confirmation: QLabel = self.ui.findChild(QLabel, "lblConfirmation")
        self.lbl_progress: QLabel = self.ui.findChild(QLabel, "lblProgress")
        self.btn_return: QPushButton = self.ui.findChild(QPushButton, "btnReturn")

        self.btn_return.clicked.connect(self._on_dismiss)

        # Auto-dismiss timer (returns to ambient clock after 5 seconds)
        self._auto_dismiss_timer = QTimer(self)
        self._auto_dismiss_timer.setSingleShot(True)
        self._auto_dismiss_timer.setInterval(5000)
        self._auto_dismiss_timer.timeout.connect(self._on_dismiss)

    def show_completion(
        self,
        subject_name: str,
        added_minutes: int,
        completed_minutes: int,
        target_minutes: int,
        task_title: str | None = None,
        confidence: str | None = None,
    ) -> None:
        """Display the completion feedback and start auto-dismiss countdown."""
        from study_station.core.engine import ScheduleEngine
        clean_name = ScheduleEngine.clean_subject_name(subject_name)
        title_text = f"{clean_name.upper()}"
        if task_title:
            title_text += f"\n{task_title}"
        self.lbl_subject.setText(title_text)

        conf_badge = ""
        if confidence == "solid":
            conf_badge = " · 🟢 Solid"
        elif confidence == "progressing":
            conf_badge = " · 🟡 Getting There"
        elif confidence == "foggy":
            conf_badge = " · 🔴 Foggy"

        self.lbl_confirmation.setText(f"+{added_minutes} MIN{conf_badge}")
        self.lbl_progress.setText(f"{completed_minutes} / {target_minutes} MIN COMPLETED")

        self._auto_dismiss_timer.start()

    def _on_dismiss(self) -> None:
        self._auto_dismiss_timer.stop()
        self.dismissed.emit()

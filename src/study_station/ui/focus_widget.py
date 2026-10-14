"""Focus screen controller wrapping focus_screen.ui."""

from pathlib import Path
from PySide6.QtCore import QFile, QTimer, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from study_station.core.engine import ScheduleEngine
from study_station.core.timer import FocusTimer


class FocusWidget(QWidget):
    """Focus screen managing the countdown timer, visual progress bar, and session controls."""

    session_finished = Signal(str, int)  # (subject_name, elapsed_minutes)
    session_cancelled = Signal()

    def __init__(self, timer: FocusTimer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.timer = timer

        # Load Qt Designer UI
        ui_path = Path(__file__).resolve().parent / "designer" / "focus_screen.ui"
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        # Layout container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        # UI References
        self.lbl_subject: QLabel = self.ui.findChild(QLabel, "lblSubject")
        self.lbl_state: QLabel = self.ui.findChild(QLabel, "lblState")
        self.lbl_remaining: QLabel = self.ui.findChild(QLabel, "lblRemaining")
        self.lbl_cycle: QLabel = self.ui.findChild(QLabel, "lblCycleProgress")
        self.progress_bar: QProgressBar = self.ui.findChild(QProgressBar, "progressBar")
        self.btn_pause: QPushButton = self.ui.findChild(QPushButton, "btnPause")
        self.btn_add_five: QPushButton = self.ui.findChild(QPushButton, "btnAddFive")
        self.btn_end: QPushButton = self.ui.findChild(QPushButton, "btnEnd")

        # Connect controls
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        self.btn_add_five.clicked.connect(self._on_add_five_clicked)
        self.btn_end.clicked.connect(self._on_end_clicked)

        # 1-second refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(500)
        self._refresh_timer.timeout.connect(self._on_tick)

    def start_session(self, subject_name: str, duration_minutes: int, cycle_info: str = "") -> None:
        """Start a new focus session and display."""
        self.timer.start(subject_name, duration_minutes)

        clean_name = ScheduleEngine.clean_subject_name(subject_name)
        # Shorten gracefully with ellipsis if excessively long
        if len(clean_name) > 36:
            clean_name = clean_name[:34].rstrip() + "…"
        self.lbl_subject.setText(clean_name.upper())

        self.lbl_state.setText("FOCUSING")
        self.btn_pause.setText("Pause")

        if cycle_info:
            self.lbl_cycle.setText(f"{cycle_info} (CYCLE)")
        else:
            self.lbl_cycle.setText("")

        self.progress_bar.setValue(0)
        self._update_display()
        self._refresh_timer.start()

    def _on_tick(self) -> None:
        """Called every tick to refresh remaining time and visual session progress bar."""
        snap = self.timer.snapshot()
        self._update_display()

        if snap.is_finished:
            self._complete_session()

    def _update_display(self) -> None:
        snap = self.timer.snapshot()
        self.lbl_remaining.setText(snap.formatted_remaining)

        # Update session progress bar (0 to 100%)
        total_sec = snap.total_duration_minutes * 60
        if total_sec > 0:
            elapsed_sec = max(0, total_sec - snap.remaining_seconds)
            progress_pct = int((elapsed_sec / total_sec) * 100)
            self.progress_bar.setValue(min(100, max(0, progress_pct)))

        if snap.is_paused:
            self.lbl_state.setText("PAUSED")
            self.btn_pause.setText("Resume")
        else:
            self.lbl_state.setText("FOCUSING")
            self.btn_pause.setText("Pause")

    def _on_pause_clicked(self) -> None:
        self.timer.toggle_pause()
        self._update_display()

    def _on_add_five_clicked(self) -> None:
        self.timer.add_minutes(5)
        self._update_display()

    def _on_end_clicked(self) -> None:
        self._complete_session()

    def _complete_session(self) -> None:
        self._refresh_timer.stop()
        subject = self.timer.subject_name
        elapsed = self.timer.stop()
        self.session_finished.emit(subject, elapsed)

"""Focus screen controller wrapping focus_screen.ui."""

from pathlib import Path
from PySide6.QtCore import QFile, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.timer import FocusTimer
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


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
        self.focus_card: QFrame = self.ui.findChild(QFrame, "focusCard")
        self.lbl_subject: QLabel = self.ui.findChild(QLabel, "lblSubject")
        self.lbl_state: QLabel = self.ui.findChild(QLabel, "lblState")
        self.lbl_remaining: QLabel = self.ui.findChild(QLabel, "lblRemaining")
        self.lbl_cycle: QLabel = self.ui.findChild(QLabel, "lblCycleProgress")
        self.progress_bar: QProgressBar = self.ui.findChild(QProgressBar, "progressBar")
        self.btn_pause: QPushButton = self.ui.findChild(QPushButton, "btnPause")
        self.btn_add_five: QPushButton = self.ui.findChild(QPushButton, "btnAddFive")
        self.btn_end: QPushButton = self.ui.findChild(QPushButton, "btnEnd")
        self.lbl_shortcuts_hint: QLabel = self.ui.findChild(QLabel, "lblShortcutsHint")

        # Make card seamless with background
        if self.focus_card:
            self.focus_card.setStyleSheet("""
                QFrame#focusCard {
                    background-color: transparent;
                    border: none;
                }
            """)

        # Apply harmonized theme styles
        self.btn_pause.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_add_five.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_add_five.setText("+5 MIN")
        self.btn_end.setStyleSheet(BUTTON_DANGER_STYLE)
        self.btn_end.setText("END SESSION")
        if self.lbl_shortcuts_hint:
            self.lbl_shortcuts_hint.setText("SPACE // PAUSE · [+] // +5M · ESC // ABORT")
            self.lbl_shortcuts_hint.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 600; letter-spacing: 1px;")

        # Connect controls
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        self.btn_add_five.clicked.connect(self._on_add_five_clicked)
        self.btn_end.clicked.connect(self._on_end_clicked)

        # Inactivity timer for auto-hiding controls (3s)
        self._controls_visible = True
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setInterval(3000)
        self._inactivity_timer.timeout.connect(self._hide_controls)

        # 1-second refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(500)
        self._refresh_timer.timeout.connect(self._on_tick)

        self.setMouseTracking(True)
        self.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        from PySide6.QtCore import QEvent
        if event.type() in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress):
            self._show_controls()
            self._inactivity_timer.start()
        return super().eventFilter(watched, event)

    def _show_controls(self) -> None:
        self.btn_pause.setVisible(True)
        self.btn_add_five.setVisible(True)
        self.btn_end.setVisible(True)
        if self.lbl_shortcuts_hint:
            self.lbl_shortcuts_hint.setVisible(True)
        self._controls_visible = True

    def _hide_controls(self) -> None:
        self.btn_pause.setVisible(False)
        self.btn_add_five.setVisible(False)
        self.btn_end.setVisible(False)
        if self.lbl_shortcuts_hint:
            self.lbl_shortcuts_hint.setVisible(False)
        self._controls_visible = False

    def start_session(self, subject_name: str, duration_minutes: int, cycle_info: str = "") -> None:
        """Start a new focus session and display."""
        self.timer.start(subject_name, duration_minutes)

        clean_name = ScheduleEngine.clean_subject_name(subject_name)
        self.lbl_subject.setText(clean_name.upper())
        self.lbl_subject.setFont(get_modern_font("eva_display", 26, QFont.Weight.Bold))
        self.lbl_subject.setStyleSheet("color: #FFFFFF; letter-spacing: 1px;")

        self.lbl_state.setText("● ACTIVE // FOCUSING")
        self.lbl_state.setStyleSheet("""
            background-color: #064E3B;
            color: #34D399;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            padding: 4px 14px;
            border-radius: 10px;
        """)
        self.btn_pause.setText("Pause")

        if cycle_info:
            self.lbl_cycle.setText(f"{cycle_info} // CYCLE TARGET")
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
            self.lbl_state.setText("⏸ SUSPENDED // PAUSED")
            self.lbl_state.setStyleSheet("""
                background-color: #38240D;
                color: #FBBF24;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
                padding: 4px 14px;
                border-radius: 10px;
            """)
            self.btn_pause.setText("Resume")
        else:
            self.lbl_state.setText("● ACTIVE // FOCUSING")
            self.lbl_state.setStyleSheet("""
                background-color: #064E3B;
                color: #34D399;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
                padding: 4px 14px;
                border-radius: 10px;
            """)
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

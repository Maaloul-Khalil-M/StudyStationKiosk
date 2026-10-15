"""Focus screen controller wrapping focus_screen.ui."""

from pathlib import Path
from PySide6.QtCore import QFile, QTimer, Qt, Signal
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
from study_station.ui.focus_ring_gauge import FocusRingGaugeWidget
from study_station.ui.theme import (
    BUTTON_DANGER_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class FocusWidget(QWidget):
    """Focus screen managing the countdown timer, visual ring gauge, and session controls."""

    session_finished = Signal(str, int)  # (subject_name, elapsed_minutes)
    session_cancelled = Signal()

    def __init__(self, timer: FocusTimer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.timer = timer
        self._cycle_info = ""
        self._cycle_ratio = 0.0
        self._theme_id = "noir"

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
            self.focus_card.setMinimumHeight(520)

            # Hide old flat elements and insert custom Ring Gauge in center
            self.lbl_state.hide()
            self.lbl_remaining.hide()
            self.lbl_cycle.hide()
            self.progress_bar.hide()

            card_spacer = self.focus_card.findChild(QWidget, "cardMiddleSpacer")
            if card_spacer:
                card_spacer.hide()

            # Insert Ring Gauge into card layout after lblSubject
            card_layout = self.focus_card.layout()
            self.ring_gauge = FocusRingGaugeWidget(self)
            # Insert at position 1 (right after lblSubject)
            card_layout.insertWidget(1, self.ring_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            self.ring_gauge = FocusRingGaugeWidget(self)

        # Apply harmonized theme styles
        self.btn_pause.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_add_five.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.btn_add_five.setText("+5 MIN")
        self.btn_end.setStyleSheet(BUTTON_DANGER_STYLE)
        self.btn_end.setText("END SESSION")
        if self.lbl_shortcuts_hint:
            self.lbl_shortcuts_hint.setText("Space to pause · +5m · Esc to end")
            self.lbl_shortcuts_hint.setStyleSheet("color: #71717A; font-size: 11px; font-weight: 500;")

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

    def apply_settings(self, settings) -> None:
        """Apply theme settings to Focus screen."""
        self._theme_id = getattr(settings, "theme_id", "noir")
        is_eva = getattr(settings, "typography_style", "eva") == "eva"
        if is_eva:
            self.lbl_subject.setFont(get_modern_font("eva_display", 26, QFont.Weight.Bold))
        else:
            self.lbl_subject.setFont(get_modern_font("sans", 24, QFont.Weight.Bold))
        self._update_display()

    def start_session(self, subject_name: str, duration_minutes: int, cycle_info: str = "") -> None:
        """Start a new focus session and display."""
        self.timer.start(subject_name, duration_minutes)

        clean_name = ScheduleEngine.clean_subject_name(subject_name)
        self.lbl_subject.setText(clean_name.upper())
        self.lbl_subject.setFont(get_modern_font("eva_display", 26, QFont.Weight.Bold))
        self.lbl_subject.setStyleSheet("color: #FFFFFF; letter-spacing: 0.5px;")

        self.lbl_state.setText("● FOCUSING")
        self.btn_pause.setText("Pause")

        self._cycle_info = cycle_info
        self._cycle_ratio = 0.0
        if cycle_info:
            self.lbl_cycle.setText(cycle_info)
            if "/" in cycle_info:
                try:
                    parts = cycle_info.split("/")
                    comp = int(parts[0].strip().split()[0])
                    tgt = int(parts[1].strip().split()[0])
                    self._cycle_ratio = comp / max(1, tgt) if tgt > 0 else 0.0
                except Exception:
                    self._cycle_ratio = 0.0
        else:
            self.lbl_cycle.setText("")

        self.progress_bar.setValue(0)
        self._update_display()
        self._refresh_timer.start()

    def _on_tick(self) -> None:
        """Called every tick to refresh remaining time and visual ring gauge."""
        snap = self.timer.snapshot()
        self._update_display()

        if snap.is_finished:
            self._complete_session()

    def _update_display(self) -> None:
        snap = self.timer.snapshot()
        self.lbl_remaining.setText(snap.formatted_remaining)

        # Update session progress bar (0 to 100%)
        total_sec = snap.total_duration_minutes * 60
        remaining_ratio = 1.0
        if total_sec > 0:
            elapsed_sec = max(0, total_sec - snap.remaining_seconds)
            progress_pct = int((elapsed_sec / total_sec) * 100)
            self.progress_bar.setValue(min(100, max(0, progress_pct)))
            remaining_ratio = snap.remaining_seconds / total_sec

        # Update custom Ring Gauge
        if hasattr(self, "ring_gauge"):
            self.ring_gauge.set_timer_state(
                formatted_time=snap.formatted_remaining,
                remaining_ratio=remaining_ratio,
                is_paused=snap.is_paused,
                cycle_ratio=self._cycle_ratio,
                cycle_text=self._cycle_info,
                theme_id=self._theme_id,
            )

        if snap.is_paused:
            self.lbl_state.setText("⏸ PAUSED")
            self.lbl_state.setStyleSheet("""
                background-color: #38240D;
                color: #FBBF24;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.5px;
                padding: 4px 14px;
                border-radius: 10px;
            """)
            self.btn_pause.setText("Resume")
        else:
            self.lbl_state.setText("● FOCUSING")
            self.lbl_state.setStyleSheet("""
                background-color: #064E3B;
                color: #34D399;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.5px;
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

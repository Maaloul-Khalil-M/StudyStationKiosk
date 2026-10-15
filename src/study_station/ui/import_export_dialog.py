"""Timetable Portability Dialog for Study Station.

Provides an elegant, retro-minimal dialog for:
1. Exporting timetable schedules to JSON (full structured format) or CSV (spreadsheets).
2. Importing timetable schedules from JSON, CSV, or university PDF files.
3. Pre-import validation, session count preview, collision detection warning, and merge/replace options.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession
from study_station.core.timetable_portability import (
    detect_collisions,
    export_sessions_to_csv,
    export_sessions_to_json,
    import_sessions_from_csv,
    import_sessions_from_json,
    import_sessions_from_pdf,
    merge_sessions,
)
from study_station.ui.theme import (
    BUTTON_NAV_STYLE,
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    get_modern_font,
)


class ImportExportDialog(QDialog):
    """Modern modal dialog for timetable import and export operations."""

    timetable_imported = Signal(list)  # list[AcademicSession]

    def __init__(
        self,
        engine: ScheduleEngine,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Timetable Portability")
        self.setFixedSize(680, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._pending_sessions: list[AcademicSession] = []
        self._pending_file: Path | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #121215;
                border: 1px solid #27272A;
                border-radius: 14px;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        # ---------------------------------------------------------------------
        # 1. Header Bar
        # ---------------------------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        lbl_title = QLabel("TIMETABLE PORTABILITY")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700; letter-spacing: 1.5px;")
        header_text.addWidget(lbl_title)

        lbl_subtitle = QLabel("Backup or import weekly class schedules via JSON, CSV, or university PDF.")
        lbl_subtitle.setStyleSheet("color: #71717A; font-size: 12px;")
        header_text.addWidget(lbl_subtitle)

        header_row.addLayout(header_text, stretch=1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #18181D;
                color: #71717A;
                border: 1px solid #27272E;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #27272E;
                color: #FFFFFF;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header_row.addWidget(btn_close)

        main_layout.addLayout(header_row)

        # ---------------------------------------------------------------------
        # 2. Export Card
        # ---------------------------------------------------------------------
        card_export = QFrame()
        card_export.setObjectName("exportCard")
        card_export.setStyleSheet("""
            QFrame#exportCard {
                background-color: #16161B;
                border: 1px solid #222228;
                border-radius: 10px;
            }
            QFrame#exportCard QLabel {
                border: none;
                background: transparent;
            }
        """)
        export_layout = QVBoxLayout(card_export)
        export_layout.setContentsMargins(18, 14, 18, 14)
        export_layout.setSpacing(10)

        lbl_exp_header = QLabel("EXPORT SCHEDULE (BACKUP)")
        lbl_exp_header.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        export_layout.addWidget(lbl_exp_header)

        session_count = len(self.engine.sessions)
        self.lbl_export_info = QLabel(f"{session_count} classes currently configured in your weekly timetable.")
        self.lbl_export_info.setStyleSheet("color: #F4F4F6; font-size: 13px; font-weight: 500;")
        export_layout.addWidget(self.lbl_export_info)

        export_btn_row = QHBoxLayout()
        export_btn_row.setSpacing(10)

        btn_exp_json = QPushButton("Export JSON")
        btn_exp_json.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exp_json.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_exp_json.clicked.connect(self._on_export_json)
        export_btn_row.addWidget(btn_exp_json)

        btn_exp_csv = QPushButton("Export CSV")
        btn_exp_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exp_csv.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_exp_csv.clicked.connect(self._on_export_csv)
        export_btn_row.addWidget(btn_exp_csv)

        export_btn_row.addStretch()

        self.lbl_export_status = QLabel("")
        self.lbl_export_status.setStyleSheet("color: #10B981; font-size: 12px; font-weight: 600;")
        export_btn_row.addWidget(self.lbl_export_status)

        export_layout.addLayout(export_btn_row)
        main_layout.addWidget(card_export)

        # ---------------------------------------------------------------------
        # 3. Import Card
        # ---------------------------------------------------------------------
        card_import = QFrame()
        card_import.setObjectName("importCard")
        card_import.setStyleSheet("""
            QFrame#importCard {
                background-color: #16161B;
                border: 1px solid #222228;
                border-radius: 10px;
            }
            QFrame#importCard QLabel {
                border: none;
                background: transparent;
            }
        """)
        import_layout = QVBoxLayout(card_import)
        import_layout.setContentsMargins(18, 14, 18, 14)
        import_layout.setSpacing(10)

        lbl_imp_header = QLabel("IMPORT SCHEDULE")
        lbl_imp_header.setStyleSheet("color: #71717A; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        import_layout.addWidget(lbl_imp_header)

        # Select file row
        file_row = QHBoxLayout()
        file_row.setSpacing(10)

        btn_browse = QPushButton("Select File...")
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_browse.clicked.connect(self._on_browse_file)
        file_row.addWidget(btn_browse)

        self.lbl_file_path = QLabel("Supported: .json, .csv, .pdf")
        self.lbl_file_path.setStyleSheet("color: #71717A; font-size: 12px;")
        file_row.addWidget(self.lbl_file_path, stretch=1)

        import_layout.addLayout(file_row)

        # Preview & Diagnostics Area
        self.preview_container = QWidget()
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(0, 4, 0, 0)
        preview_layout.setSpacing(8)

        self.lbl_preview_summary = QLabel("")
        self.lbl_preview_summary.setStyleSheet("font-size: 12px; font-weight: 600;")
        preview_layout.addWidget(self.lbl_preview_summary)

        self.lbl_collision_warning = QLabel("")
        self.lbl_collision_warning.setStyleSheet("""
            color: #FBBF24;
            background-color: #2D200E;
            border: 1px solid #78350F;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 11px;
            font-weight: 500;
        """)
        self.lbl_collision_warning.hide()
        preview_layout.addWidget(self.lbl_collision_warning)

        # Mode Selection: Replace vs Merge
        mode_row = QHBoxLayout()
        mode_row.setSpacing(16)

        self.rb_replace = QRadioButton("Replace current schedule")
        self.rb_replace.setChecked(True)
        self.rb_replace.setStyleSheet("""
            QRadioButton {
                color: #D4D4D8;
                font-size: 12px;
                font-weight: 500;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid #383842;
                background-color: #18181E;
            }
            QRadioButton::indicator:checked {
                background-color: #10B981;
                border-color: #059669;
            }
        """)

        self.rb_merge = QRadioButton("Merge and add new classes")
        self.rb_merge.setStyleSheet(self.rb_replace.styleSheet())

        mode_group = QButtonGroup(self)
        mode_group.addButton(self.rb_replace)
        mode_group.addButton(self.rb_merge)

        mode_row.addWidget(self.rb_replace)
        mode_row.addWidget(self.rb_merge)
        mode_row.addStretch()

        preview_layout.addLayout(mode_row)

        # Confirm Import Button
        self.btn_confirm_import = QPushButton("Import Schedule")
        self.btn_confirm_import.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_confirm_import.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm_import.setFixedHeight(34)
        self.btn_confirm_import.setEnabled(False)
        self.btn_confirm_import.clicked.connect(self._on_confirm_import)
        preview_layout.addWidget(self.btn_confirm_import)

        import_layout.addWidget(self.preview_container)
        main_layout.addWidget(card_import, stretch=1)

        # ---------------------------------------------------------------------
        # 4. Footer Bar
        # ---------------------------------------------------------------------
        footer_row = QHBoxLayout()
        lbl_hint = QLabel("Esc to close · Changes update active cycles immediately")
        lbl_hint.setStyleSheet("color: #52525B; font-size: 11px;")
        footer_row.addWidget(lbl_hint, stretch=1)

        btn_done = QPushButton("Close")
        btn_done.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_done.clicked.connect(self.accept)
        footer_row.addWidget(btn_done)

        main_layout.addLayout(footer_row)

    # -------------------------------------------------------------------------
    # Export Actions
    # -------------------------------------------------------------------------

    def _on_export_json(self) -> None:
        today_str = datetime.now().strftime("%Y-%m-%d")
        default_name = f"timetable_backup_{today_str}.json"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Timetable as JSON",
            default_name,
            "JSON Files (*.json);;All Files (*.*)",
        )
        if not path:
            return

        try:
            self.engine.export_timetable(path, file_format="json")
            count = len(self.engine.sessions)
            self.lbl_export_status.setText(f"✓ Saved {count} classes to JSON")
        except Exception as e:
            self.lbl_export_status.setStyleSheet("color: #EF4444; font-size: 12px;")
            self.lbl_export_status.setText(f"Export error: {e}")

    def _on_export_csv(self) -> None:
        today_str = datetime.now().strftime("%Y-%m-%d")
        default_name = f"timetable_{today_str}.csv"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Timetable as CSV",
            default_name,
            "CSV Files (*.csv);;All Files (*.*)",
        )
        if not path:
            return

        try:
            self.engine.export_timetable(path, file_format="csv")
            count = len(self.engine.sessions)
            self.lbl_export_status.setText(f"✓ Saved {count} classes to CSV")
        except Exception as e:
            self.lbl_export_status.setStyleSheet("color: #EF4444; font-size: 12px;")
            self.lbl_export_status.setText(f"Export error: {e}")

    # -------------------------------------------------------------------------
    # Import Actions & Validation
    # -------------------------------------------------------------------------

    def _on_browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Schedule File to Import",
            "",
            "Timetable Files (*.json *.csv *.pdf);;JSON Files (*.json);;CSV Files (*.csv);;PDF Files (*.pdf);;All Files (*.*)",
        )
        if not path:
            return

        self._load_and_preview_file(Path(path))

    def _load_and_preview_file(self, file_path: Path) -> None:
        self._pending_file = file_path
        self.lbl_file_path.setText(file_path.name)
        ext = file_path.suffix.lower()

        if ext == ".json":
            sessions, warnings = import_sessions_from_json(file_path)
        elif ext in (".csv", ".tsv", ".txt"):
            sessions, warnings = import_sessions_from_csv(file_path)
        elif ext == ".pdf":
            sessions, warnings = import_sessions_from_pdf(file_path)
        else:
            sessions, warnings = [], [f"Unsupported file format '{ext}'."]

        self._pending_sessions = sessions

        if not sessions:
            self.lbl_preview_summary.setStyleSheet("color: #EF4444; font-size: 12px;")
            err_msg = warnings[0] if warnings else "No valid class sessions found in file."
            self.lbl_preview_summary.setText(f"✕ {err_msg}")
            self.lbl_collision_warning.hide()
            self.btn_confirm_import.setEnabled(False)
            return

        # Valid sessions found
        self.btn_confirm_import.setEnabled(True)
        warn_txt = f" ({len(warnings)} warnings)" if warnings else ""
        self.lbl_preview_summary.setStyleSheet("color: #10B981; font-size: 12px;")
        self.lbl_preview_summary.setText(f"✓ Found {len(sessions)} valid class sessions{warn_txt}")

        # Check collisions
        collisions = detect_collisions(sessions)
        if collisions:
            c1, c2 = collisions[0]
            desc = f"{c1.day} {c1.time_slot.start} ({c1.subject.name}) and {c2.time_slot.start} ({c2.subject.name})"
            self.lbl_collision_warning.setText(f"⚠️ {len(collisions)} time overlap(s) detected: {desc}")
            self.lbl_collision_warning.show()
        else:
            self.lbl_collision_warning.hide()

    def _on_confirm_import(self) -> None:
        if not self._pending_sessions or not self._pending_file:
            return

        replace_mode = self.rb_replace.isChecked()
        added, warnings, collisions = self.engine.import_timetable_file(
            self._pending_file,
            replace=replace_mode,
        )

        self.timetable_imported.emit(self.engine.sessions)
        self.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

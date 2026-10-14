"""Controller for configuring subject review targets."""

from pathlib import Path
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from study_station.core.engine import ScheduleEngine
from study_station.ui.theme import get_modern_font


class TargetsDialog(QDialog):
    """Dialog allowing students to edit target review minutes per subject."""

    targets_saved = Signal(dict)  # dict[str, int] -> subject_name to target_minutes

    def __init__(
        self,
        subjects: list[str],
        current_targets: dict[str, int],
        default_target: int = 60,
        default_subject: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Subject Review Targets")
        self.setFixedSize(660, 540)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #111115;
                border: 1px solid #24242C;
                border-radius: 14px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Load UI
        ui_path = Path(__file__).resolve().parent / "designer" / "targets_dialog.ui"
        loader = QUiLoader()
        ui_file = QFile(str(ui_path))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, container)
        ui_file.close()
        self.ui.setWindowFlags(Qt.WindowType.Widget)

        container_layout.addWidget(self.ui)

        # UI References
        self.scroll_layout: QVBoxLayout = self.ui.findChild(QVBoxLayout, "subjectsListLayout")
        self.btn_cancel: QPushButton = self.ui.findChild(QPushButton, "btnCancel")
        self.btn_save: QPushButton = self.ui.findChild(QPushButton, "btnSave")

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)

        self._spinners: dict[str, QSpinBox] = {}
        self._preset_buttons: dict[str, dict[int, QPushButton]] = {}

        # Populate rows
        for s in subjects:
            is_highlighted = bool(default_subject and s == default_subject)
            self._add_subject_row(s, current_targets.get(s, default_target), is_highlighted=is_highlighted)

        self.scroll_layout.setContentsMargins(0, 0, 8, 0)
        self.scroll_layout.addStretch()

    def _add_subject_row(self, subject_name: str, target_val: int, is_highlighted: bool = False) -> None:
        row_frame = QFrame()
        border_css = "1.5px solid #10B981" if is_highlighted else "1px solid #222228"
        bg_css = "#14201A" if is_highlighted else "#141418"
        row_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_css};
                border: {border_css};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(14, 8, 14, 8)
        row_layout.setSpacing(10)

        # Clean subject name
        clean_name = ScheduleEngine.clean_subject_name(subject_name)
        lbl = QLabel(clean_name)
        lbl.setFont(get_modern_font("sans", 13, QFont.Weight.Medium))
        lbl.setStyleSheet("color: #F4F4F5; border: none; background: transparent;")
        row_layout.addWidget(lbl, 1)

        self._preset_buttons[subject_name] = {}

        # Preset pills
        for preset in (30, 60, 90):
            btn = QPushButton(f"{preset}m")
            btn.setFixedSize(48, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, val=preset, s=subject_name: self._set_spin_value(s, val))
            self._preset_buttons[subject_name][preset] = btn
            row_layout.addWidget(btn)

        # Target SpinBox
        spn = QSpinBox()
        spn.setRange(10, 600)
        spn.setSingleStep(5)
        spn.setValue(target_val)
        spn.setSuffix(" m")
        spn.setFixedWidth(92)
        spn.valueChanged.connect(lambda val, s=subject_name: self._update_row_presets(s, val))
        self._spinners[subject_name] = spn
        row_layout.addWidget(spn)

        self._update_row_presets(subject_name, target_val)
        self.scroll_layout.addWidget(row_frame)

    def _update_row_presets(self, subject_name: str, current_val: int) -> None:
        if subject_name not in self._preset_buttons:
            return
        for preset, btn in self._preset_buttons[subject_name].items():
            if preset == current_val:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #10B981;
                        color: #09090B;
                        font-size: 11px;
                        font-weight: 700;
                        border-radius: 6px;
                        border: none;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #222228;
                        color: #A1A1AA;
                        font-size: 11px;
                        font-weight: 500;
                        border-radius: 6px;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #2E2E38;
                        color: #FFFFFF;
                    }
                """)

    def _set_spin_value(self, subject_name: str, val: int) -> None:
        if subject_name in self._spinners:
            self._spinners[subject_name].setValue(val)
        if subject_name in self._spinners:
            self._spinners[subject_name].setValue(val)

    def _on_save(self) -> None:
        result = {subj: spn.value() for subj, spn in self._spinners.items()}
        self.targets_saved.emit(result)
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


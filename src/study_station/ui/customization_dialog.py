"""Customization dialog for Study Station."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from study_station.core.settings import AppSettings
from study_station.core.sound_manager import SoundManager
from study_station.ui.theme import BUTTON_PRIMARY_STYLE, BUTTON_SECONDARY_STYLE, THEMES, get_modern_font


class CustomizationDialog(QDialog):
    """Modern modal dialog allowing live visual customization and navigation to secondary tools."""

    settings_changed = Signal(AppSettings)
    open_timetable_requested = Signal()
    open_targets_requested = Signal()
    open_manual_log_requested = Signal()
    open_import_export_requested = Signal()

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Clock & Display Customization")
        self.setFixedSize(500, 700)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._settings = settings

        self._init_ui()

    def _init_ui(self) -> None:
        # Outer container with modern dark card styling
        container = QFrame(self)
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #111115;
                border: 1px solid #24242C;
                border-radius: 14px;
            }
            QLabel {
                color: #F4F4F5;
            }
            QRadioButton, QCheckBox {
                color: #D4D4D8;
                font-size: 13px;
                font-weight: 500;
                spacing: 10px;
            }
            QRadioButton:hover, QCheckBox:hover {
                color: #FFFFFF;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 1px solid #383842;
                background-color: #18181E;
            }
            QCheckBox::indicator:checked {
                background-color: #10B981;
                border-color: #059669;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #383842;
                background-color: #18181E;
            }
            QRadioButton::indicator:checked {
                background-color: #10B981;
                border-color: #059669;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(container)

        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(24, 18, 24, 18)
        content_layout.setSpacing(11)

        # Header with title and close button
        header_layout = QHBoxLayout()
        title = QLabel("Settings & Customization")
        title.setFont(get_modern_font("sans", 18, QFont.Weight.Bold))
        title.setMinimumHeight(32)
        title.setStyleSheet("padding: 2px 0 4px 0;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #A1A1AA;
                font-size: 15px;
                border-radius: 15px;
                border: 1px solid #27272A;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
            }
        """)
        btn_close.clicked.connect(self.accept)
        header_layout.addWidget(btn_close)
        content_layout.addLayout(header_layout)

        # Section 1: Time Format
        sec1_lbl = QLabel("TIME FORMAT")
        sec1_lbl.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        sec1_lbl.setStyleSheet("color: #71717A; letter-spacing: 1px;")
        content_layout.addWidget(sec1_lbl)

        time_layout = QHBoxLayout()
        self.rb_24h = QRadioButton("24-Hour")
        self.rb_12h = QRadioButton("12-Hour")
        if self._settings.use_24h:
            self.rb_24h.setChecked(True)
        else:
            self.rb_12h.setChecked(True)

        time_group = QButtonGroup(self)
        time_group.addButton(self.rb_24h)
        time_group.addButton(self.rb_12h)
        self.rb_24h.toggled.connect(self._on_format_changed)

        time_layout.addWidget(self.rb_24h)
        time_layout.addWidget(self.rb_12h)
        time_layout.addStretch()
        content_layout.addLayout(time_layout)

        content_layout.addWidget(self._create_divider())

        # Section 2: Display Cards & Elements
        sec2_lbl = QLabel("DISPLAY ELEMENTS")
        sec2_lbl.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        sec2_lbl.setStyleSheet("color: #71717A; letter-spacing: 1px;")
        content_layout.addWidget(sec2_lbl)

        self.cb_seconds = QCheckBox("Show Seconds Card")
        self.cb_seconds.setChecked(self._settings.show_seconds)
        self.cb_seconds.toggled.connect(self._on_seconds_toggled)
        content_layout.addWidget(self.cb_seconds)

        self.cb_date = QCheckBox("Show Date Header")
        self.cb_date.setChecked(self._settings.show_date)
        self.cb_date.toggled.connect(self._on_date_toggled)
        content_layout.addWidget(self.cb_date)

        self.cb_anim = QCheckBox("Smooth 3D Flip Animation")
        self.cb_anim.setChecked(self._settings.animate_flip)
        self.cb_anim.toggled.connect(self._on_anim_toggled)
        content_layout.addWidget(self.cb_anim)

        content_layout.addWidget(self._create_divider())

        # Section 2.5: Typography System
        sec_typo_lbl = QLabel("TYPOGRAPHY SYSTEM")
        sec_typo_lbl.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        sec_typo_lbl.setStyleSheet("color: #71717A; letter-spacing: 1px;")
        content_layout.addWidget(sec_typo_lbl)

        typo_layout = QHBoxLayout()
        typo_layout.setSpacing(16)
        typo_group = QButtonGroup(self)

        current_typo = getattr(self._settings, "typography_style", "eva")

        self.rb_typo_eva = QRadioButton("Evangelion Serif")
        self.rb_typo_eva.setChecked(current_typo == "eva")
        self.rb_typo_eva.toggled.connect(lambda c: self._on_typo_toggled(c, "eva"))
        typo_group.addButton(self.rb_typo_eva)
        typo_layout.addWidget(self.rb_typo_eva)

        self.rb_typo_modern = QRadioButton("Modern Sans")
        self.rb_typo_modern.setChecked(current_typo == "modern")
        self.rb_typo_modern.toggled.connect(lambda c: self._on_typo_toggled(c, "modern"))
        typo_group.addButton(self.rb_typo_modern)
        typo_layout.addWidget(self.rb_typo_modern)

        typo_layout.addStretch()
        content_layout.addLayout(typo_layout)

        content_layout.addWidget(self._create_divider())

        # Section 3: Theme Palette
        sec3_lbl = QLabel("CARD THEME")
        sec3_lbl.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        sec3_lbl.setStyleSheet("color: #71717A; letter-spacing: 1px;")
        content_layout.addWidget(sec3_lbl)

        theme_grid = QGridLayout()
        theme_grid.setContentsMargins(0, 0, 0, 0)
        theme_grid.setHorizontalSpacing(24)
        theme_grid.setVerticalSpacing(10)
        theme_grid.setRowMinimumHeight(0, 26)
        theme_grid.setRowMinimumHeight(1, 26)
        theme_group = QButtonGroup(self)

        # 2x2 theme layout
        items = list(THEMES.items())
        for idx, (theme_key, theme_data) in enumerate(items):
            rb = QRadioButton(theme_data.name)
            rb.setProperty("theme_key", theme_key)
            rb.setFixedHeight(24)
            if self._settings.theme_id == theme_key:
                rb.setChecked(True)
            rb.toggled.connect(lambda checked, k=theme_key: self._on_theme_toggled(checked, k))
            theme_group.addButton(rb)
            row = idx // 2
            col = idx % 2
            theme_grid.addWidget(rb, row, col)

        content_layout.addLayout(theme_grid)

        content_layout.addWidget(self._create_divider())

        # Section 4: Audio Cues & Calm Feedback
        sec_audio_lbl = QLabel("AUDIO & CALM CUES")
        sec_audio_lbl.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        sec_audio_lbl.setStyleSheet("color: #71717A; letter-spacing: 1px;")
        content_layout.addWidget(sec_audio_lbl)

        audio_row = QHBoxLayout()
        audio_row.setSpacing(12)

        self.cb_sound = QCheckBox("Focus completion chime")
        self.cb_sound.setChecked(getattr(self._settings, "sound_enabled", True))
        self.cb_sound.toggled.connect(self._on_sound_toggled)
        audio_row.addWidget(self.cb_sound)

        audio_row.addStretch()

        self.btn_preview_sound = QPushButton("▶ Test Chime")
        self.btn_preview_sound.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preview_sound.setFixedHeight(28)
        self.btn_preview_sound.setStyleSheet("""
            QPushButton {
                background: #18181D;
                color: #A1A1AA;
                border: 1px solid #27272E;
                border-radius: 14px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #27272E;
                color: #FFFFFF;
                border-color: #3F3F4A;
            }
        """)
        self.btn_preview_sound.clicked.connect(self._on_preview_sound)
        audio_row.addWidget(self.btn_preview_sound)

        content_layout.addLayout(audio_row)

        content_layout.addWidget(self._create_divider())

        # Section 5: Secondary Tools
        sec5_lbl = QLabel("STUDY MANAGEMENT")
        sec5_lbl.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        sec5_lbl.setStyleSheet("color: #71717A; letter-spacing: 1px;")
        content_layout.addWidget(sec5_lbl)

        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(8)

        btn_timetable = QPushButton("Timetable")
        btn_timetable.setFixedHeight(30)
        btn_timetable.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_timetable.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_timetable.clicked.connect(self._on_timetable_clicked)
        tools_layout.addWidget(btn_timetable)

        btn_targets = QPushButton("Targets")
        btn_targets.setFixedHeight(30)
        btn_targets.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_targets.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_targets.clicked.connect(self._on_targets_clicked)
        tools_layout.addWidget(btn_targets)

        btn_manual = QPushButton("Log Time")
        btn_manual.setFixedHeight(30)
        btn_manual.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_manual.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_manual.clicked.connect(self._on_manual_clicked)
        tools_layout.addWidget(btn_manual)

        btn_import_export = QPushButton("Import/Export")
        btn_import_export.setFixedHeight(30)
        btn_import_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import_export.setStyleSheet(BUTTON_SECONDARY_STYLE)
        btn_import_export.clicked.connect(self._on_import_export_clicked)
        tools_layout.addWidget(btn_import_export)

        content_layout.addLayout(tools_layout)

        content_layout.addStretch()

        # Done button
        done_layout = QHBoxLayout()
        done_layout.addStretch()
        btn_done = QPushButton("Done")
        btn_done.setFixedSize(160, 36)
        btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_done.setStyleSheet(BUTTON_PRIMARY_STYLE)
        btn_done.clicked.connect(self.accept)
        done_layout.addWidget(btn_done)
        done_layout.addStretch()
        content_layout.addLayout(done_layout)

    @staticmethod
    def _create_divider() -> QFrame:
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #1E1E26; border: none;")
        return div

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().rect()
            self.move(parent_rect.center() - self.rect().center())

    def _on_timetable_clicked(self) -> None:
        self.accept()
        self.open_timetable_requested.emit()

    def _on_targets_clicked(self) -> None:
        self.accept()
        self.open_targets_requested.emit()

    def _on_manual_clicked(self) -> None:
        self.accept()
        self.open_manual_log_requested.emit()

    def _on_import_export_clicked(self) -> None:
        self.accept()
        self.open_import_export_requested.emit()

    def _on_format_changed(self) -> None:
        self._settings.use_24h = self.rb_24h.isChecked()
        self.settings_changed.emit(self._settings)

    def _on_seconds_toggled(self, checked: bool) -> None:
        self._settings.show_seconds = checked
        self.settings_changed.emit(self._settings)

    def _on_date_toggled(self, checked: bool) -> None:
        self._settings.show_date = checked
        self.settings_changed.emit(self._settings)

    def _on_anim_toggled(self, checked: bool) -> None:
        self._settings.animate_flip = checked
        self.settings_changed.emit(self._settings)

    def _on_typo_toggled(self, checked: bool, style: str) -> None:
        if checked:
            self._settings.typography_style = style
            self.settings_changed.emit(self._settings)

    def _on_theme_toggled(self, checked: bool, theme_key: str) -> None:
        if checked:
            self._settings.theme_id = theme_key
            self.settings_changed.emit(self._settings)

    def _on_sound_toggled(self, checked: bool) -> None:
        self._settings.sound_enabled = checked
        self.settings_changed.emit(self._settings)

    def _on_preview_sound(self) -> None:
        SoundManager.get_instance().play_completion_chime(enabled=True)

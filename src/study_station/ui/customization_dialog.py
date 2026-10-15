"""Customization dialog for Study Station."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_station.core.settings import AppSettings
from study_station.core.sound_manager import SoundManager
from study_station.ui.theme import (
    BUTTON_PRIMARY_STYLE,
    BUTTON_SECONDARY_STYLE,
    PRESET_ACCENTS,
    PRESET_BACKGROUNDS,
    THEMES,
    get_modern_font,
)


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
        self.setFixedSize(510, 740)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._settings = settings
        self._accent_buttons: dict[str, QPushButton] = {}
        self._bg_buttons: dict[str, QPushButton] = {}

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
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 10, 20, 10)
        container_layout.setSpacing(4)

        # Header with title and close button
        header_layout = QHBoxLayout()
        title = QLabel("Settings & Customization")
        title.setFont(get_modern_font("sans", 16, QFont.Weight.Bold))
        title.setMinimumHeight(26)
        title.setStyleSheet("padding: 0px 0 2px 0;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1F;
                color: #A1A1AA;
                font-size: 13px;
                border-radius: 13px;
                border: 1px solid #27272A;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
            }
        """)
        btn_close.clicked.connect(self.accept)
        header_layout.addWidget(btn_close)
        container_layout.addLayout(header_layout)

        # Scroll area for clean content viewing
        scroll = QScrollArea(container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 6px;
                background: rgba(0, 0, 0, 0.15);
                border-radius: 3px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #2E2E3A;
                min-height: 24px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4A4A5E;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px;
                background: transparent;
            }
        """)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 6, 0)
        content_layout.setSpacing(6)

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

        # Section 3: Theme Palette Presets
        sec3_lbl = QLabel("CARD THEME PRESETS")
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

        # Section 3.5: Accent Colors Swatches
        sec_accent_lbl = QLabel("ACCENT COLOR")
        sec_accent_lbl.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        sec_accent_lbl.setStyleSheet("color: #71717A; letter-spacing: 1px;")
        content_layout.addWidget(sec_accent_lbl)

        content_layout.addWidget(self._create_accent_swatches())

        content_layout.addWidget(self._create_divider())

        # Section 3.6: Background Tone Swatches
        sec_bg_lbl = QLabel("BACKGROUND TONE")
        sec_bg_lbl.setFont(get_modern_font("sans", 10, QFont.Weight.DemiBold))
        sec_bg_lbl.setStyleSheet("color: #71717A; letter-spacing: 1px;")
        content_layout.addWidget(sec_bg_lbl)

        content_layout.addWidget(self._create_bg_swatches())

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

        scroll.setWidget(scroll_content)
        container_layout.addWidget(scroll, stretch=1)

        # Done button pinned at bottom
        done_layout = QHBoxLayout()
        done_layout.setContentsMargins(0, 4, 0, 0)
        done_layout.addStretch()
        btn_done = QPushButton("Done")
        btn_done.setFixedSize(140, 32)
        btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_done.setStyleSheet(BUTTON_PRIMARY_STYLE)
        btn_done.clicked.connect(self.accept)
        done_layout.addWidget(btn_done)
        done_layout.addStretch()
        container_layout.addLayout(done_layout)

    def _create_accent_swatches(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._accent_buttons = {}
        for hex_code, name in PRESET_ACCENTS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"{name} ({hex_code})")
            btn.clicked.connect(lambda _, h=hex_code: self._on_accent_selected(h))
            self._accent_buttons[hex_code.lower()] = btn
            layout.addWidget(btn)

        self.btn_custom_accent = QPushButton("🎨")
        self.btn_custom_accent.setFixedSize(28, 28)
        self.btn_custom_accent.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_custom_accent.setToolTip("Pick Custom Accent Color...")
        self.btn_custom_accent.clicked.connect(self._on_custom_accent_clicked)
        layout.addWidget(self.btn_custom_accent)
        layout.addStretch()

        self._update_accent_swatch_styles()
        return widget

    def _create_bg_swatches(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._bg_buttons = {}
        for hex_code, name in PRESET_BACKGROUNDS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"{name} ({hex_code})")
            btn.clicked.connect(lambda _, h=hex_code: self._on_bg_selected(h))
            self._bg_buttons[hex_code.lower()] = btn
            layout.addWidget(btn)

        self.btn_custom_bg = QPushButton("🎨")
        self.btn_custom_bg.setFixedSize(28, 28)
        self.btn_custom_bg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_custom_bg.setToolTip("Pick Custom Background Tone...")
        self.btn_custom_bg.clicked.connect(self._on_custom_bg_clicked)
        layout.addWidget(self.btn_custom_bg)
        layout.addStretch()

        self._update_bg_swatch_styles()
        return widget

    def _update_accent_swatch_styles(self) -> None:
        curr = (getattr(self._settings, "accent_color", "") or "#10B981").lower()
        for hex_code, btn in self._accent_buttons.items():
            is_active = (hex_code == curr)
            border_style = "2.5px solid #FFFFFF" if is_active else "1px solid rgba(255, 255, 255, 0.15)"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border: {border_style};
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border: 2px solid #E4E4E7;
                }}
            """)
        if curr not in self._accent_buttons:
            self.btn_custom_accent.setStyleSheet(f"""
                QPushButton {{
                    background-color: {curr};
                    border: 2.5px solid #FFFFFF;
                    border-radius: 14px;
                    font-size: 13px;
                }}
            """)
        else:
            self.btn_custom_accent.setStyleSheet("""
                QPushButton {
                    background: #18181D;
                    border: 1px dashed #3F3F4E;
                    border-radius: 14px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #272730;
                    border-color: #71717A;
                }
            """)

    def _update_bg_swatch_styles(self) -> None:
        curr = (getattr(self._settings, "bg_color", "") or "#09090B").lower()
        for hex_code, btn in self._bg_buttons.items():
            is_active = (hex_code == curr)
            border_style = "2.5px solid #FFFFFF" if is_active else "1px solid #383842"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border: {border_style};
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border: 2px solid #E4E4E7;
                }}
            """)
        if curr not in self._bg_buttons:
            self.btn_custom_bg.setStyleSheet(f"""
                QPushButton {{
                    background-color: {curr};
                    border: 2.5px solid #FFFFFF;
                    border-radius: 14px;
                    font-size: 13px;
                }}
            """)
        else:
            self.btn_custom_bg.setStyleSheet("""
                QPushButton {
                    background: #18181D;
                    border: 1px dashed #3F3F4E;
                    border-radius: 14px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #272730;
                    border-color: #71717A;
                }
            """)

    def _on_accent_selected(self, hex_code: str) -> None:
        self._settings.accent_color = hex_code
        self._update_accent_swatch_styles()
        self.settings_changed.emit(self._settings)

    def _on_bg_selected(self, hex_code: str) -> None:
        self._settings.bg_color = hex_code
        self._update_bg_swatch_styles()
        self.settings_changed.emit(self._settings)

    def _on_custom_accent_clicked(self) -> None:
        initial = QColor(getattr(self._settings, "accent_color", "#10B981"))
        color = QColorDialog.getColor(initial=initial, parent=self, title="Choose Custom Accent Color")
        if color.isValid():
            self._on_accent_selected(color.name())

    def _on_custom_bg_clicked(self) -> None:
        initial = QColor(getattr(self._settings, "bg_color", "#09090B"))
        color = QColorDialog.getColor(initial=initial, parent=self, title="Choose Custom Background Color")
        if color.isValid():
            self._on_bg_selected(color.name())

    @staticmethod
    def _create_divider() -> QFrame:
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #1A1A22; margin: 1px 0; border: none;")
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
            theme = THEMES.get(theme_key)
            if theme:
                self._settings.bg_color = theme.bg_canvas.name()
                self._settings.accent_color = theme.text_accent.name()
                self._update_accent_swatch_styles()
                self._update_bg_swatch_styles()
            self.settings_changed.emit(self._settings)

    def _on_sound_toggled(self, checked: bool) -> None:
        self._settings.sound_enabled = checked
        self.settings_changed.emit(self._settings)

    def _on_preview_sound(self) -> None:
        SoundManager.get_instance().play_completion_chime(enabled=True)

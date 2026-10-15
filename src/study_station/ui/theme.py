"""Theme definitions, color discipline, and unified button styles for Study Station."""

from dataclasses import dataclass
from PySide6.QtGui import QColor, QFont


@dataclass
class ColorTheme:
    """Color configuration for clock cards and backgrounds."""

    name: str
    bg_canvas: QColor
    card_top_grad_start: QColor
    card_top_grad_end: QColor
    card_bottom_grad_start: QColor
    card_bottom_grad_end: QColor
    card_border: QColor
    hinge_groove: QColor
    text_primary: QColor
    text_muted: QColor
    text_accent: QColor
    progress_bar_bg: QColor
    progress_bar_fill: QColor


THEMES = {
    "noir": ColorTheme(
        name="Classic Noir",
        bg_canvas=QColor("#09090B"),
        card_top_grad_start=QColor("#202026"),
        card_top_grad_end=QColor("#18181E"),
        card_bottom_grad_start=QColor("#14141A"),
        card_bottom_grad_end=QColor("#0E0E12"),
        card_border=QColor("#2A2A34"),
        hinge_groove=QColor("#070709"),
        text_primary=QColor("#F4F4F6"),
        text_muted=QColor("#71717A"),
        text_accent=QColor("#10B981"),
        progress_bar_bg=QColor("#1A1A22"),
        progress_bar_fill=QColor("#10B981"),
    ),
    "slate": ColorTheme(
        name="Midnight Slate",
        bg_canvas=QColor("#0B0F19"),
        card_top_grad_start=QColor("#1E2638"),
        card_top_grad_end=QColor("#171F2E"),
        card_bottom_grad_start=QColor("#121824"),
        card_bottom_grad_end=QColor("#0D121C"),
        card_border=QColor("#283548"),
        hinge_groove=QColor("#070A10"),
        text_primary=QColor("#F8FAFC"),
        text_muted=QColor("#64748B"),
        text_accent=QColor("#38BDF8"),
        progress_bar_bg=QColor("#172033"),
        progress_bar_fill=QColor("#38BDF8"),
    ),
    "espresso": ColorTheme(
        name="Warm Espresso",
        bg_canvas=QColor("#120E0C"),
        card_top_grad_start=QColor("#261F1B"),
        card_top_grad_end=QColor("#1E1815"),
        card_bottom_grad_start=QColor("#171310"),
        card_bottom_grad_end=QColor("#100D0B"),
        card_border=QColor("#362820"),
        hinge_groove=QColor("#0A0807"),
        text_primary=QColor("#FAFAF9"),
        text_muted=QColor("#8C827A"),
        text_accent=QColor("#F59E0B"),
        progress_bar_bg=QColor("#241B16"),
        progress_bar_fill=QColor("#F59E0B"),
    ),
    "nerv": ColorTheme(
        name="NERV Terminal",
        bg_canvas=QColor("#050507"),
        card_top_grad_start=QColor("#1C1814"),
        card_top_grad_end=QColor("#16120E"),
        card_bottom_grad_start=QColor("#120E0A"),
        card_bottom_grad_end=QColor("#0A0806"),
        card_border=QColor("#3E2A1A"),
        hinge_groove=QColor("#040303"),
        text_primary=QColor("#F5F5F7"),
        text_muted=QColor("#9E8A7A"),
        text_accent=QColor("#FF7700"),
        progress_bar_bg=QColor("#261A10"),
        progress_bar_fill=QColor("#FF7700"),
    ),
}


def get_modern_font(family_preference: str = "sans", size: int = 14, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Return a modern font configured with cross-platform fallbacks and tabular figures."""
    font = QFont()
    safe_size = max(1, int(size))
    font.setPixelSize(safe_size)
    font.setWeight(weight)
    
    if family_preference in ("serif", "eva", "eva_display"):
        # Evangelion Matisse-inspired high-contrast display serif
        font.setFamilies([
            "Century Schoolbook",
            "Bodoni MT",
            "Georgia",
            "Times New Roman",
            "Palatino Linotype",
            "DejaVu Serif",
            "serif",
        ])
        # Mechanical compression / tight tracking characteristic of Matisse EB
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 96)
    elif family_preference in ("hud", "hud_telemetry", "condensed"):
        # Evangelion NERV HUD telemetry style
        font.setFamilies([
            "Impact",
            "DIN Alternate",
            "Franklin Gothic Medium",
            "Arial Narrow",
            "JetBrains Mono",
            "Inter",
            "Segoe UI",
            "sans-serif",
        ])
        font.setCapitalization(QFont.Capitalization.AllUppercase)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 110)
    elif family_preference == "mono":
        font.setFamilies([
            "JetBrains Mono",
            "SF Mono",
            "Cascadia Code",
            "Segoe UI",
            "DejaVu Sans Mono",
            "Monospace",
        ])
    else:  # "sans"
        font.setFamilies([
            "Inter",
            "SF Pro Display",
            "Segoe UI Variable Display",
            "Segoe UI",
            "Roboto",
            "Helvetica Neue",
            "DejaVu Sans",
            "Arial",
        ])
    return font


# Harmonized pill button styling for the entire application
BUTTON_PRIMARY_STYLE = """
QPushButton {
    background-color: #F4F4F5;
    color: #09090B;
    font-size: 13px;
    font-weight: 600;
    height: 36px;
    border: 1px solid #F4F4F5;
    border-radius: 18px;
    padding: 0px 22px;
}
QPushButton:hover {
    background-color: #FFFFFF;
    border-color: #FFFFFF;
}
QPushButton:pressed {
    background-color: #D4D4D8;
    border-color: #D4D4D8;
}
"""

BUTTON_SECONDARY_STYLE = """
QPushButton {
    background-color: #141418;
    color: #D4D4D8;
    font-size: 13px;
    font-weight: 500;
    height: 36px;
    border: 1px solid #27272E;
    border-radius: 18px;
    padding: 0px 18px;
}
QPushButton:hover {
    background-color: #222228;
    color: #FFFFFF;
    border-color: #3F3F4A;
}
QPushButton:pressed {
    background-color: #101014;
}
"""

BUTTON_DANGER_STYLE = """
QPushButton {
    background-color: #161214;
    color: #F87171;
    font-size: 13px;
    font-weight: 500;
    height: 36px;
    border: 1px solid #3B1C1C;
    border-radius: 18px;
    padding: 0px 18px;
}
QPushButton:hover {
    background-color: #261618;
    color: #EF4444;
    border-color: #7F1D1D;
}
QPushButton:pressed {
    background-color: #120E10;
}
"""

BUTTON_NAV_STYLE = """
QPushButton {
    background-color: #141418;
    color: #D4D4D8;
    font-size: 12px;
    font-weight: 500;
    border-radius: 14px;
    padding: 6px 14px;
    border: 1px solid #27272E;
}
QPushButton:hover {
    background-color: #202026;
    color: #FFFFFF;
    border-color: #3F3F4A;
}
QPushButton:pressed {
    background-color: #101014;
}
"""

CHIP_BUTTON_STYLE = """
QPushButton {
    background-color: #121216;
    color: #A1A1AA;
    font-size: 12px;
    font-weight: 500;
    border-radius: 14px;
    padding: 7px 16px;
    border: 1px solid #24242A;
    text-align: center;
}
QPushButton:hover {
    background-color: #1A1A22;
    color: #F4F4F5;
    border-color: #383842;
}
"""

CHIP_BUTTON_ACTIVE_STYLE = """
QPushButton {
    background-color: #172554;
    color: #93C5FD;
    font-size: 12px;
    font-weight: 600;
    border-radius: 14px;
    padding: 7px 16px;
    border: 1.5px solid #3B82F6;
    text-align: center;
}
QPushButton:hover {
    background-color: #1E3A8A;
    color: #BFDBFE;
}
"""

GLOBAL_QSS = """
/* =========================================================================
   Global Reset & Modern PyQt Design System
   ========================================================================= */

/* Universal Tooltips */
QToolTip {
    background-color: #18181D;
    color: #F4F4F5;
    border: 1px solid #27272E;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
}

/* Universal Minimalist ScrollBars (Eradicates Windows 95 / Classic OS Look) */
QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 5px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #2E2E38;
    min-width: 24px;
    border-radius: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: #4B4B58;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    width: 0px;
    height: 0px;
    background: transparent;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 5px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #2E2E38;
    min-height: 24px;
    border-radius: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #4B4B58;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    width: 0px;
    height: 0px;
    background: transparent;
}

/* Universal Form Controls */
QLineEdit, QSpinBox, QComboBox {
    background-color: #141418;
    color: #F4F4F5;
    border: 1px solid #27272E;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #3B82F6;
    background-color: #18181F;
}

/* Dropdown Popup View */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: none;
}
QComboBox QAbstractItemView {
    background-color: #16161A;
    color: #F4F4F5;
    border: 1px solid #27272E;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #1E293B;
    selection-color: #93C5FD;
    outline: none;
}

/* Universal Tables */
QTableWidget, QTableView {
    background-color: #101014;
    color: #F4F4F5;
    border: 1px solid #24242A;
    border-radius: 10px;
    gridline-color: #1A1A22;
    selection-background-color: #172554;
    selection-color: #FFFFFF;
    outline: none;
}
QHeaderView::section {
    background-color: #141418;
    color: #71717A;
    font-weight: 600;
    font-size: 11px;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #24242A;
    letter-spacing: 0.5px;
}
QTableCornerButton::section {
    background-color: #141418;
    border: none;
    border-bottom: 1px solid #24242A;
}

/* Universal Progress Bar */
QProgressBar {
    background-color: #1A1A22;
    border-radius: 5px;
    border: none;
}
QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 5px;
}
"""


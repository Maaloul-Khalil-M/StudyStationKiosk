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
        bg_canvas=QColor("#000000"),
        card_top_grad_start=QColor("#222226"),
        card_top_grad_end=QColor("#1A1A1E"),
        card_bottom_grad_start=QColor("#161619"),
        card_bottom_grad_end=QColor("#101012"),
        card_border=QColor("#2C2C32"),
        hinge_groove=QColor("#000000"),
        text_primary=QColor("#FFFFFF"),
        text_muted=QColor("#71717A"),
        text_accent=QColor("#E4E4E7"),
        progress_bar_bg=QColor("#27272A"),
        progress_bar_fill=QColor("#E4E4E7"),
    ),
    "slate": ColorTheme(
        name="Midnight Slate",
        bg_canvas=QColor("#080A10"),
        card_top_grad_start=QColor("#1E2430"),
        card_top_grad_end=QColor("#171D27"),
        card_bottom_grad_start=QColor("#121720"),
        card_bottom_grad_end=QColor("#0D1118"),
        card_border=QColor("#2E3848"),
        hinge_groove=QColor("#05070B"),
        text_primary=QColor("#F8FAFC"),
        text_muted=QColor("#64748B"),
        text_accent=QColor("#CBD5E1"),
        progress_bar_bg=QColor("#1E293B"),
        progress_bar_fill=QColor("#94A3B8"),
    ),
    "espresso": ColorTheme(
        name="Warm Espresso",
        bg_canvas=QColor("#0C0A09"),
        card_top_grad_start=QColor("#241F1C"),
        card_top_grad_end=QColor("#1D1916"),
        card_bottom_grad_start=QColor("#171411"),
        card_bottom_grad_end=QColor("#100E0C"),
        card_border=QColor("#342C26"),
        hinge_groove=QColor("#060504"),
        text_primary=QColor("#FAFAF9"),
        text_muted=QColor("#78716C"),
        text_accent=QColor("#D6D3D1"),
        progress_bar_bg=QColor("#292524"),
        progress_bar_fill=QColor("#A8A29E"),
    ),
}


def get_modern_font(family_preference: str = "sans", size: int = 14, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Return a modern font configured with cross-platform fallbacks and tabular figures."""
    font = QFont()
    font.setPixelSize(size)
    font.setWeight(weight)
    
    if family_preference == "sans":
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
    elif family_preference == "mono":
        font.setFamilies([
            "JetBrains Mono",
            "SF Mono",
            "Cascadia Code",
            "Segoe UI",
            "DejaVu Sans Mono",
            "Monospace",
        ])
    return font


# Harmonized pill button styling for the entire application
BUTTON_PRIMARY_STYLE = """
QPushButton {
    background-color: #F4F4F5;
    color: #09090B;
    font-size: 14px;
    font-weight: 600;
    border-radius: 20px;
    padding: 10px 24px;
    border: none;
}
QPushButton:hover {
    background-color: #FFFFFF;
}
QPushButton:pressed {
    background-color: #D4D4D8;
}
"""

BUTTON_SECONDARY_STYLE = """
QPushButton {
    background-color: #161619;
    color: #D4D4D8;
    font-size: 13px;
    font-weight: 500;
    border-radius: 20px;
    padding: 9px 20px;
    border: 1px solid #27272A;
}
QPushButton:hover {
    background-color: #27272A;
    color: #FFFFFF;
    border-color: #3F3F46;
}
QPushButton:pressed {
    background-color: #1A1A1E;
}
"""

BUTTON_DANGER_STYLE = """
QPushButton {
    background-color: #161619;
    color: #F87171;
    font-size: 13px;
    font-weight: 500;
    border-radius: 20px;
    padding: 9px 20px;
    border: 1px solid #27272A;
}
QPushButton:hover {
    background-color: #27272A;
    color: #EF4444;
    border-color: #7F1D1D;
}
QPushButton:pressed {
    background-color: #1A1A1E;
}
"""

BUTTON_NAV_STYLE = """
QPushButton {
    background-color: #161619;
    color: #D4D4D8;
    font-size: 12px;
    font-weight: 500;
    border-radius: 16px;
    padding: 6px 14px;
    border: 1px solid #27272A;
}
QPushButton:hover {
    background-color: #27272A;
    color: #FFFFFF;
    border-color: #3F3F46;
}
QPushButton:pressed {
    background-color: #1A1A1E;
}
"""

CHIP_BUTTON_STYLE = """
QPushButton {
    background-color: #141418;
    color: #A1A1AA;
    font-size: 12px;
    font-weight: 500;
    border-radius: 16px;
    padding: 8px 16px;
    border: 1px solid #27272A;
    text-align: center;
}
QPushButton:hover {
    background-color: #202026;
    color: #F4F4F5;
    border-color: #3F3F46;
}
"""

CHIP_BUTTON_ACTIVE_STYLE = """
QPushButton {
    background-color: #1E293B;
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 600;
    border-radius: 16px;
    padding: 8px 16px;
    border: 1.5px solid #3B82F6;
    text-align: center;
}
QPushButton:hover {
    background-color: #2563EB;
    color: #FFFFFF;
}
"""


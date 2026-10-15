"""User interface customization settings."""

from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class AppSettings:
    """Settings controlling appearance and display options."""

    use_24h: bool = True
    show_seconds: bool = False
    show_date: bool = True
    date_format: str = "full"  # "full", "compact", "clean"
    theme_id: str = "noir"     # "noir", "slate", "espresso"
    accent_color: str = "#10B981"  # hex color for focus accents, glowing pills, highlights
    bg_color: str = "#09090B"      # hex color for global canvas and card backgrounds
    animate_flip: bool = True
    default_focus_minutes: int = 15
    typography_style: str = "eva"  # "eva" (Matisse Serif + HUD) or "modern" (Swiss Sans)
    sound_enabled: bool = True     # Milestone 8: Audio completion chime toggle

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

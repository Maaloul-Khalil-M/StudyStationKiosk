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
    animate_flip: bool = True
    default_focus_minutes: int = 15

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

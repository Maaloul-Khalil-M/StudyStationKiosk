"""User and profile management for multi-user kiosk workstation."""

from __future__ import annotations
import json
import os
from pathlib import Path
import re
import sys


def get_base_data_dir() -> Path:
    """Return the platform-standard base directory for Study Station."""
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA")
        base_dir = Path(app_data) if app_data else Path.home() / "AppData" / "Roaming"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        base_dir = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"

    db_dir = base_dir / "study_station"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


class UserManager:
    """Manages user profiles and their corresponding SQLite databases."""

    DEFAULT_USER = "Default"

    def __init__(self, base_dir: Path | str | None = None) -> None:
        self.base_dir = Path(base_dir).resolve() if base_dir else get_base_data_dir()
        self.users_dir = self.base_dir / "users"
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.base_dir / "profiles.json"
        self.is_fresh_install = not self.config_path.exists()
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        """Ensure profiles.json exists with at least the default user."""
        if not self.config_path.exists():
            data = {
                "active_user": self.DEFAULT_USER,
                "users": [self.DEFAULT_USER],
            }
            self._save_config(data)

    def _load_config(self) -> dict:
        """Load profiles configuration."""
        if not self.config_path.exists():
            return {
                "active_user": self.DEFAULT_USER,
                "users": [self.DEFAULT_USER],
            }
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Invalid profiles format")
                if "users" not in data or not data["users"]:
                    data["users"] = [self.DEFAULT_USER]
                if "active_user" not in data or data["active_user"] not in data["users"]:
                    data["active_user"] = data["users"][0]
                return data
        except Exception:
            return {
                "active_user": self.DEFAULT_USER,
                "users": [self.DEFAULT_USER],
            }

    def _save_config(self, data: dict) -> None:
        """Save profiles configuration."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def sanitize_username(username: str) -> str:
        """Sanitize a username for safe filesystem usage."""
        cleaned = re.sub(r'[\\/*?:"<>|]', "", username.strip())
        return cleaned or "User"

    def list_users(self) -> list[str]:
        """Return list of all registered user names."""
        config = self._load_config()
        return list(config.get("users", [self.DEFAULT_USER]))

    def get_active_user(self) -> str:
        """Return the current active user name."""
        config = self._load_config()
        return config.get("active_user", self.DEFAULT_USER)

    def set_active_user(self, username: str) -> bool:
        """Set active user. If user doesn't exist, returns False."""
        config = self._load_config()
        users = config.get("users", [])
        if username not in users:
            return False
        config["active_user"] = username
        self._save_config(config)
        return True

    def get_user_db_path(self, username: str | None = None) -> Path:
        """Get the database file path for a given user (or active user)."""
        target = username or self.get_active_user()
        safe_name = self.sanitize_username(target)

        # Backwards compatibility: if "Default" and legacy studystation.db exists
        legacy_path = self.base_dir / "studystation.db"
        if safe_name == self.DEFAULT_USER and legacy_path.exists():
            return legacy_path

        return self.users_dir / f"{safe_name}.db"

    def create_user(self, username: str) -> tuple[str, Path]:
        """Create a new user profile and return (safe_username, db_path)."""
        safe_name = self.sanitize_username(username)
        config = self._load_config()
        users = config.get("users", [])

        if safe_name not in users:
            users.append(safe_name)
            config["users"] = users
            self._save_config(config)

        db_path = self.get_user_db_path(safe_name)
        return safe_name, db_path

    def delete_user(self, username: str, delete_db_file: bool = True) -> bool:
        """Delete a user profile. Cannot delete if it is the only user."""
        config = self._load_config()
        users = config.get("users", [])
        if username not in users or len(users) <= 1:
            return False

        users.remove(username)
        config["users"] = users

        # If active user was deleted, switch active to the first remaining user
        if config.get("active_user") == username:
            config["active_user"] = users[0]

        self._save_config(config)

        if delete_db_file:
            db_path = self.get_user_db_path(username)
            if db_path.exists() and db_path != self.base_dir / "studystation.db":
                try:
                    db_path.unlink()
                except Exception:
                    pass

        return True

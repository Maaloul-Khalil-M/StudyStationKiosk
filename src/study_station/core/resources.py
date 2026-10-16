"""Centralized cross-platform resource resolution for Study Station.

Handles resolving assets, Qt Designer .ui templates, and docs across:
1. Development environment (source tree)
2. Installed wheel / site-packages package layout
3. PyInstaller frozen single-binary / onedir executable bundles (sys._MEIPASS)
"""

from __future__ import annotations
import sys
from pathlib import Path


def get_bundle_dir() -> Path:
    """Return the base bundle directory (sys._MEIPASS when frozen, or package directory)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # In development: return src/study_station directory
    return Path(__file__).resolve().parent.parent


def get_ui_path(filename: str) -> Path:
    """Resolve the absolute path to a Qt Designer .ui file."""
    # 1. Package directory layout (standard dev & wheel)
    pkg_ui = Path(__file__).resolve().parent.parent / "ui" / "designer" / filename
    if pkg_ui.exists():
        return pkg_ui

    # 2. PyInstaller bundle layout
    bundle_ui = get_bundle_dir() / "study_station" / "ui" / "designer" / filename
    if bundle_ui.exists():
        return bundle_ui

    alt_bundle_ui = get_bundle_dir() / "ui" / "designer" / filename
    if alt_bundle_ui.exists():
        return alt_bundle_ui

    return pkg_ui


def get_sample_timetable_path() -> Path:
    """Resolve the path to example.json timetable template."""
    # 1. Check packaged assets directory (pip wheel / installed package)
    pkg_path = Path(__file__).resolve().parent.parent / "assets" / "example.json"
    if pkg_path.exists():
        return pkg_path

    # 2. Relative to repo root in development
    dev_path = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "example.json"
    if dev_path.exists():
        return dev_path

    # 3. PyInstaller bundle docs directory
    bundle_path = get_bundle_dir() / "docs" / "example.json"
    if bundle_path.exists():
        return bundle_path

    alt_path = get_bundle_dir() / "study_station" / "docs" / "example.json"
    if alt_path.exists():
        return alt_path

    return pkg_path


def get_doc_path(filename: str) -> Path:
    """Resolve path to documentation or asset file (e.g. grid.pdf)."""
    # 1. Check packaged assets directory (pip wheel / installed package)
    pkg_path = Path(__file__).resolve().parent.parent / "assets" / filename
    if pkg_path.exists():
        return pkg_path

    # 2. Development source root
    dev_path = Path(__file__).resolve().parent.parent.parent.parent / "docs" / filename
    if dev_path.exists():
        return dev_path

    # 3. PyInstaller bundle
    bundle_path = get_bundle_dir() / "docs" / filename
    if bundle_path.exists():
        return bundle_path

    return pkg_path


def get_writable_sound_dir() -> Path:
    """Return a guaranteed writable directory for generated audio assets.

    Never attempts to write into a read-only frozen bundle or site-packages.
    """
    from study_station.persistence.user_manager import get_base_data_dir
    sound_dir = get_base_data_dir() / "sounds"
    sound_dir.mkdir(parents=True, exist_ok=True)
    return sound_dir

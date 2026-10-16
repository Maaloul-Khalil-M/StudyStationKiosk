# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for Study Station (Windows & Linux Fedora)."""

import os
import sys
from pathlib import Path

block_cipher = None

# Base repository paths
ROOT_DIR = Path(SPECPATH).resolve()
SRC_DIR = ROOT_DIR / "src"
DOCS_DIR = ROOT_DIR / "docs"
DESIGNER_DIR = SRC_DIR / "study_station" / "ui" / "designer"

# Collect assets and data files
datas = [
    (str(DESIGNER_DIR / "*.ui"), "study_station/ui/designer"),
    (str(DOCS_DIR / "example.json"), "docs"),
    (str(DOCS_DIR / "grid.pdf"), "docs"),
]

# Hidden imports needed for PySide6 dynamic loader
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtUiTools",
    "pypdf",
    "sqlite3",
    "hashlib",
    "secrets",
]

a = Analysis(
    [str(SRC_DIR / "study_station" / "main.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "numpy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="study-station",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

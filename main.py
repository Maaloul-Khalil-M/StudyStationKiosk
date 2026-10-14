"""Convenience launcher for Study Station."""

import sys
from pathlib import Path

# Ensure src/ is on sys.path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from study_station.main import run

if __name__ == "__main__":
    sys.exit(run())

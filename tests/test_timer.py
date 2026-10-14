"""Unit tests for FocusTimer."""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from study_station.core.timer import FocusTimer


class TestFocusTimer(unittest.TestCase):
    """Test timer calculations, pausing, resumption, and additions."""

    def test_start_and_snapshot(self) -> None:
        timer = FocusTimer()
        timer.start("Data Vis", 15)
        self.assertTrue(timer.is_active)
        self.assertFalse(timer.is_paused)

        snap = timer.snapshot()
        self.assertEqual(snap.subject_name, "Data Vis")
        self.assertGreaterEqual(snap.remaining_seconds, 14 * 60)
        self.assertEqual(snap.total_duration_minutes, 15)
        self.assertFalse(snap.is_finished)

    def test_pause_and_resume(self) -> None:
        timer = FocusTimer()
        timer.start("Data Vis", 10)
        timer.pause()
        self.assertTrue(timer.is_paused)

        rem_paused = timer.get_remaining_seconds()
        self.assertEqual(rem_paused, 600)

        timer.resume()
        self.assertFalse(timer.is_paused)
        self.assertGreaterEqual(timer.get_remaining_seconds(), 598)

    def test_add_minutes(self) -> None:
        timer = FocusTimer()
        timer.start("Data Vis", 10)
        timer.add_minutes(5)
        self.assertEqual(timer.total_duration_minutes, 15)
        self.assertGreater(timer.get_remaining_seconds(), 14 * 60)

    def test_stop_returns_elapsed(self) -> None:
        timer = FocusTimer()
        timer.start("Data Vis", 25)
        # Simulate elapsed time
        timer.start_time = datetime.now() - timedelta(minutes=10)
        timer.target_end_time = datetime.now() + timedelta(minutes=15)
        elapsed = timer.stop()
        self.assertEqual(elapsed, 10)
        self.assertFalse(timer.is_active)


if __name__ == "__main__":
    unittest.main()

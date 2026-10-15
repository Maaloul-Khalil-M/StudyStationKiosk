"""Unit tests for FocusRingGaugeWidget."""

from pathlib import Path
import sys
import unittest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.ui.focus_ring_gauge import FocusRingGaugeWidget


class TestFocusRingGaugeWidget(unittest.TestCase):
    """Test the visual ring gauge properties, state transitions, and geometry."""

    def test_initial_state(self) -> None:
        gauge = FocusRingGaugeWidget()
        self.assertEqual(gauge.formatted_time, "25:00")
        self.assertEqual(gauge.remaining_ratio, 1.0)
        self.assertEqual(gauge.cycle_ratio, 0.0)
        self.assertFalse(gauge.is_paused)
        self.assertEqual(gauge.sizeHint(), QSize(360, 360))

    def test_set_timer_state_active(self) -> None:
        gauge = FocusRingGaugeWidget()
        gauge.set_timer_state(
            formatted_time="14:59",
            remaining_ratio=0.6,
            is_paused=False,
            cycle_ratio=0.45,
            cycle_text="25 / 60 MIN (CYCLE)",
            theme_id="noir",
        )
        self.assertEqual(gauge.formatted_time, "14:59")
        self.assertAlmostEqual(gauge.remaining_ratio, 0.6)
        self.assertAlmostEqual(gauge.cycle_ratio, 0.45)
        self.assertFalse(gauge.is_paused)
        self.assertEqual(gauge.cycle_text, "25 / 60 MIN (CYCLE)")

    def test_set_timer_state_paused(self) -> None:
        gauge = FocusRingGaugeWidget()
        gauge.set_timer_state(
            formatted_time="08:20",
            remaining_ratio=0.33,
            is_paused=True,
            cycle_ratio=0.8,
            cycle_text="50 / 60 MIN",
            theme_id="nerv",
        )
        self.assertTrue(gauge.is_paused)
        self.assertEqual(gauge._theme_id, "nerv")
        self.assertEqual(gauge.formatted_time, "08:20")

    def test_bounds_clamping(self) -> None:
        gauge = FocusRingGaugeWidget()
        # Test negative clamping
        gauge.set_timer_state(
            formatted_time="00:00",
            remaining_ratio=-0.5,
            cycle_ratio=-0.2,
        )
        self.assertEqual(gauge.remaining_ratio, 0.0)
        self.assertEqual(gauge.cycle_ratio, 0.0)

        # Test upper clamping for remaining ratio
        gauge.set_timer_state(
            formatted_time="25:00",
            remaining_ratio=1.5,
            cycle_ratio=1.2,
        )
        self.assertEqual(gauge.remaining_ratio, 1.0)
        self.assertEqual(gauge.cycle_ratio, 1.2)


if __name__ == "__main__":
    unittest.main()

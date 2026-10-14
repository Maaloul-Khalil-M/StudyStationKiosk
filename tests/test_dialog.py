"""Unit test for CustomizationDialog and AppSettings."""

from pathlib import Path
import sys
import unittest
from PySide6.QtWidgets import QApplication

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ensure QApplication exists for widget testing
app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.settings import AppSettings
from study_station.ui.customization_dialog import CustomizationDialog


class TestCustomizationDialog(unittest.TestCase):
    """Test CustomizationDialog instantiation and signals."""

    def test_dialog_creation_and_toggles(self) -> None:
        settings = AppSettings()
        dialog = CustomizationDialog(settings)
        self.assertIsNotNone(dialog)

        # Toggle seconds
        dialog.cb_seconds.setChecked(True)
        self.assertTrue(settings.show_seconds)

        # Toggle 12h
        dialog.rb_12h.setChecked(True)
        self.assertFalse(settings.use_24h)


if __name__ == "__main__":
    unittest.main()

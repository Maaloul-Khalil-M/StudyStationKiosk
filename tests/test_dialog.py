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

    def test_color_and_background_customization(self) -> None:
        settings = AppSettings()
        dialog = CustomizationDialog(settings)
        emitted = []
        dialog.settings_changed.connect(lambda s: emitted.append(s))

        # Select custom accent color
        dialog._on_accent_selected("#38BDF8")
        self.assertEqual(settings.accent_color, "#38BDF8")
        self.assertEqual(len(emitted), 1)

        # Select custom background color
        dialog._on_bg_selected("#0B0F19")
        self.assertEqual(settings.bg_color, "#0B0F19")
        self.assertEqual(len(emitted), 2)

        # Theme toggle updates both colors
        dialog._on_theme_toggled(True, "espresso")
        self.assertEqual(settings.theme_id, "espresso")
        self.assertEqual(len(emitted), 3)


if __name__ == "__main__":
    unittest.main()

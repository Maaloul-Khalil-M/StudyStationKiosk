"""Unit tests for Milestone 8: SoundManager and Audio Cues."""

from pathlib import Path
import sys
import tempfile
import unittest
import wave
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.settings import AppSettings
from study_station.core.sound_manager import SoundManager
from study_station.ui.customization_dialog import CustomizationDialog


class TestSoundManager(unittest.TestCase):
    """Test audio synthesis, playback manager, and settings integration."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sound_dir = Path(self.temp_dir.name)
        self.manager = SoundManager(sound_dir=self.sound_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_chime_synthesis(self) -> None:
        """Verify the synthesized chime is a valid 44.1kHz 16-bit PCM WAV."""
        self.assertTrue(self.manager.chime_path.exists())
        self.assertGreater(self.manager.chime_path.stat().st_size, 10000)

        with wave.open(str(self.manager.chime_path), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 1)
            self.assertEqual(wav.getsampwidth(), 2)  # 16-bit
            self.assertEqual(wav.getframerate(), 44100)
            self.assertGreater(wav.getnframes(), 40000)

    def test_play_chime_disabled(self) -> None:
        """Disabled chime should return False and not initiate playback."""
        result = self.manager.play_completion_chime(enabled=False)
        self.assertFalse(result)

    def test_play_chime_enabled(self) -> None:
        """Enabled chime should return True and record last_played_file."""
        with patch.object(self.manager, "_play_file") as mock_play:
            result = self.manager.play_completion_chime(enabled=True)
            self.assertTrue(result)
            self.assertEqual(self.manager.last_played_file, str(self.manager.chime_path))

    def test_app_settings_sound_serialization(self) -> None:
        """Verify sound_enabled round-trips through AppSettings dict."""
        settings = AppSettings(sound_enabled=True)
        d = settings.to_dict()
        self.assertIn("sound_enabled", d)
        self.assertTrue(d["sound_enabled"])

        loaded = AppSettings.from_dict({"sound_enabled": False, "theme_id": "noir"})
        self.assertFalse(loaded.sound_enabled)

    def test_customization_dialog_sound_toggle(self) -> None:
        """Verify CustomizationDialog displays and toggles sound_enabled."""
        settings = AppSettings(sound_enabled=True)
        dialog = CustomizationDialog(settings)

        self.assertTrue(hasattr(dialog, "cb_sound"))
        self.assertTrue(dialog.cb_sound.isChecked())

        received_settings = []
        dialog.settings_changed.connect(lambda s: received_settings.append(s.sound_enabled))

        # Toggle to off
        dialog.cb_sound.setChecked(False)
        self.assertFalse(settings.sound_enabled)
        self.assertIn(False, received_settings)

        # Toggle to on
        dialog.cb_sound.setChecked(True)
        self.assertTrue(settings.sound_enabled)
        self.assertIn(True, received_settings)

    def test_customization_dialog_test_chime_button(self) -> None:
        """Verify Preview button calls SoundManager.play_completion_chime."""
        settings = AppSettings(sound_enabled=True)
        dialog = CustomizationDialog(settings)

        with patch.object(SoundManager.get_instance(), "play_completion_chime") as mock_play:
            dialog.btn_preview_sound.click()
            mock_play.assert_called_once_with(enabled=True)


if __name__ == "__main__":
    unittest.main()

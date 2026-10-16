"""Unit tests for cross-platform resource resolution."""

from pathlib import Path
import unittest

from study_station.core.resources import (
    get_bundle_dir,
    get_doc_path,
    get_sample_timetable_path,
    get_ui_path,
    get_writable_sound_dir,
)


class TestResources(unittest.TestCase):
    """Test cross-platform resource resolution in dev and packaged contexts."""

    def test_get_bundle_dir(self) -> None:
        bundle_dir = get_bundle_dir()
        self.assertTrue(bundle_dir.exists())

    def test_get_ui_path_existing(self) -> None:
        ui_files = [
            "completion_screen.ui",
            "focus_screen.ui",
            "manual_log_dialog.ui",
            "targets_dialog.ui",
            "timetable_dialog.ui",
        ]
        for name in ui_files:
            path = get_ui_path(name)
            self.assertTrue(path.exists(), f"Failed to locate {name} at {path}")
            self.assertTrue(path.is_file())

    def test_get_sample_timetable_path(self) -> None:
        path = get_sample_timetable_path()
        self.assertTrue(path.exists(), f"Failed to locate sample timetable at {path}")
        self.assertEqual(path.name, "example.json")

    def test_get_doc_path(self) -> None:
        path = get_doc_path("grid.pdf")
        self.assertTrue(path.exists(), f"Failed to locate grid.pdf at {path}")
        self.assertEqual(path.name, "grid.pdf")

    def test_get_writable_sound_dir(self) -> None:
        sound_dir = get_writable_sound_dir()
        self.assertTrue(sound_dir.exists())
        self.assertTrue(sound_dir.is_dir())


if __name__ == "__main__":
    unittest.main()

"""Unit tests for Milestone 9: Timetable Portability (Import & Export)."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession, Subject, TimeSlot
from study_station.core.timetable_portability import (
    clean_time,
    detect_collisions,
    export_sessions_to_csv,
    export_sessions_to_json,
    import_sessions_from_csv,
    import_sessions_from_json,
    import_sessions_from_pdf,
    merge_sessions,
    normalize_day,
)
from study_station.ui.import_export_dialog import ImportExportDialog


class TestTimetablePortability(unittest.TestCase):
    """Test core portability logic and Import/Export dialog."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        self.s1 = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Visualisation des données", "TP"),
            location="Lab 20",
        )
        self.s2 = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("09:40", "11:10"),
            subject=Subject("Techniques de prévision", "Cours"),
            location="SC 3",
        )
        self.s3 = AcademicSession(
            day="Mar",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("La cyber-criminalité", "Cours"),
            location="SC 1",
        )
        self.sessions = [self.s1, self.s2, self.s3]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_day_and_time_normalization(self) -> None:
        """Verify day and time parsing robustness."""
        self.assertEqual(normalize_day("LUN"), "Lun")
        self.assertEqual(normalize_day("lundi"), "Lun")
        self.assertEqual(normalize_day("Monday"), "Lun")
        self.assertEqual(normalize_day("vendredi"), "Ven")

        self.assertEqual(clean_time("8:00"), "08:00")
        self.assertEqual(clean_time("8h30"), "08:30")
        self.assertEqual(clean_time("15h"), "15:00")
        self.assertEqual(clean_time("16:40"), "16:40")

    def test_json_export_and_import(self) -> None:
        """Verify round-trip JSON serialization and schema validity."""
        json_file = self.dir_path / "schedule.json"
        export_sessions_to_json(self.sessions, json_file)
        self.assertTrue(json_file.exists())

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("sessions", data)
        self.assertEqual(len(data["sessions"]), 3)

        loaded, warnings = import_sessions_from_json(json_file)
        self.assertEqual(len(warnings), 0)
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded[0].subject.name, "Visualisation des données")
        self.assertEqual(loaded[0].time_slot.start, "08:00")

    def test_csv_export_and_import(self) -> None:
        """Verify round-trip CSV serialization and delimiter detection."""
        csv_file = self.dir_path / "schedule.csv"
        export_sessions_to_csv(self.sessions, csv_file)
        self.assertTrue(csv_file.exists())

        loaded, warnings = import_sessions_from_csv(csv_file)
        self.assertEqual(len(warnings), 0)
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded[1].subject.name, "Techniques de prévision")
        self.assertEqual(loaded[1].location, "SC 3")

    def test_csv_semicolon_delimited_french_format(self) -> None:
        """Verify French Excel semicolon CSV parsing."""
        raw_csv = (
            "Jour;Début;Fin;Matière;Format;Salle\n"
            "Lun;08:00;09:30;Visualisation des données;TP;Lab 20\n"
            "Mar;13:30;15:00;Technique de veille;TP;Lab 11\n"
        )
        csv_file = self.dir_path / "french.csv"
        with open(csv_file, "w", encoding="utf-8") as f:
            f.write(raw_csv)

        loaded, warnings = import_sessions_from_csv(csv_file)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].day, "Lun")
        self.assertEqual(loaded[1].subject.name, "Technique de veille")

    def test_collision_detection(self) -> None:
        """Verify overlapping time slot detection on identical weekdays."""
        # s1: Lun 08:00 - 09:30
        overlapping = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("09:00", "10:30"),  # overlaps with s1 and s2
            subject=Subject("Overlap Class", "TD"),
            location="Lab 1",
        )
        non_overlapping = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("11:30", "13:00"),
            subject=Subject("Separate Class", "CI"),
            location="SC 2",
        )

        collisions = detect_collisions([self.s1, self.s2, overlapping, non_overlapping])
        self.assertGreater(len(collisions), 0)
        # s1 and overlapping overlap
        pairs = {(c[0].subject.name, c[1].subject.name) for c in collisions}
        self.assertTrue(
            ("Visualisation des données", "Overlap Class") in pairs
            or ("Overlap Class", "Visualisation des données") in pairs
        )

    def test_merge_sessions(self) -> None:
        """Verify replace and merge duplicate-skipping logic."""
        incoming_new = AcademicSession(
            day="Mer",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("New Subject", "Cours"),
            location="Room A",
        )
        # Duplicate of s1
        incoming_dup = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Visualisation des données", "TP"),
            location="Lab 20",
        )

        # Merge mode
        merged, added, dups = merge_sessions(self.sessions, [incoming_new, incoming_dup], replace=False)
        self.assertEqual(len(merged), 4)  # 3 original + 1 new
        self.assertEqual(added, 1)
        self.assertEqual(dups, 1)

        # Replace mode
        replaced, added_r, _ = merge_sessions(self.sessions, [incoming_new], replace=True)
        self.assertEqual(len(replaced), 1)
        self.assertEqual(replaced[0].subject.name, "New Subject")

    def test_pdf_parsing_grid(self) -> None:
        """Verify extraction from official university grid.pdf."""
        grid_pdf = Path(__file__).resolve().parent.parent / "docs" / "grid.pdf"
        if not grid_pdf.exists():
            self.skipTest("docs/grid.pdf not found")

        sessions, warnings = import_sessions_from_pdf(grid_pdf)
        self.assertGreater(len(sessions), 10)
        subjects = {s.subject.name for s in sessions}
        # Check known university subjects
        self.assertTrue(any("Visualisation" in s for s in subjects))

    def test_engine_import_export_methods(self) -> None:
        """Verify ScheduleEngine integration methods."""
        engine = ScheduleEngine(sessions=self.sessions)
        export_file = self.dir_path / "engine_export.json"
        engine.export_timetable(export_file, file_format="json")
        self.assertTrue(export_file.exists())

        # Test importing with replace=True
        engine_empty = ScheduleEngine(sessions=[])
        added, warnings, collisions = engine_empty.import_timetable_file(export_file, replace=True)
        self.assertEqual(added, 3)
        self.assertEqual(len(engine_empty.sessions), 3)

    def test_import_export_dialog_flow(self) -> None:
        """Verify ImportExportDialog UI interactions."""
        engine = ScheduleEngine(sessions=self.sessions)
        dialog = ImportExportDialog(engine)

        self.assertIn("3 classes", dialog.lbl_export_info.text())
        self.assertFalse(dialog.btn_confirm_import.isEnabled())

        # Simulate loading file in preview
        json_file = self.dir_path / "preview.json"
        export_sessions_to_json(self.sessions, json_file)
        dialog._load_and_preview_file(json_file)

        self.assertTrue(dialog.btn_confirm_import.isEnabled())
        self.assertIn("Found 3", dialog.lbl_preview_summary.text())

        # Test import confirmation
        emitted_sessions = []
        dialog.timetable_imported.connect(lambda s: emitted_sessions.append(s))
        dialog._on_confirm_import()
        self.assertEqual(len(emitted_sessions), 1)


if __name__ == "__main__":
    unittest.main()

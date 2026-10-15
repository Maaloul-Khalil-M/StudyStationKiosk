"""Unit tests for SubjectDashboardWidget, SplitFlapClockWidget, and MainWindow."""

from datetime import datetime
from pathlib import Path
import sys
import unittest
from PySide6.QtWidgets import QApplication

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

app = QApplication.instance() or QApplication(sys.argv)

from study_station.core.engine import ScheduleEngine
from study_station.core.models import AcademicSession, Subject, TimeSlot
from study_station.core.settings import AppSettings
from study_station.ui.dashboard_widget import SubjectDashboardWidget
from study_station.ui.main_window import MainWindow
from study_station.ui.split_flap_clock import SplitFlapClockWidget


class TestDashboardUI(unittest.TestCase):
    """Test the Subject-Centric UI components."""

    def setUp(self) -> None:
        self.session_mon = AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Data Vis", "TP"),
            location="Lab 20",
        )
        self.session_fri = AcademicSession(
            day="Ven",
            time_slot=TimeSlot("10:00", "11:30"),
            subject=Subject("Data Vis", "Cours"),
            location="SC 1",
        )
        self.session_tue = AcademicSession(
            day="Mar",
            time_slot=TimeSlot("14:00", "15:30"),
            subject=Subject("Math", "TD"),
            location="SC 2",
        )
        self.engine = ScheduleEngine(
            sessions=[self.session_mon, self.session_tue, self.session_fri],
            default_target_minutes=60,
        )
        self.settings = AppSettings()

    def test_split_flap_clock_widget(self) -> None:
        clock = SplitFlapClockWidget(self.settings)
        self.assertIsNotNone(clock)
        self.assertEqual(clock.height(), 168)

        # Apply updated settings
        new_settings = AppSettings(use_24h=False, show_seconds=True)
        clock.apply_settings(new_settings)
        self.assertTrue(clock.settings.show_seconds)
        self.assertFalse(clock.settings.use_24h)

    def test_subject_dashboard_widget(self) -> None:
        dashboard = SubjectDashboardWidget(self.engine, self.settings)
        self.assertIsNotNone(dashboard)

        # Check Hero card populated
        self.assertIn("DATA VIS", dashboard.lbl_subject_name.text().upper())
        self.assertIn("60 MIN", dashboard.lbl_status_badge.text())

        # Check chip buttons populated
        self.assertIn(None, dashboard._chip_buttons)  # Auto chip
        self.assertIn("Data Vis", dashboard._chip_buttons)
        self.assertIn("Math", dashboard._chip_buttons)

        # Switch subject to Math
        dashboard.set_selected_subject("Math")
        self.assertEqual(dashboard.selected_subject, "Math")
        self.assertEqual(dashboard.lbl_subject_name.text(), "Math")

        # Test start focus signal
        emitted = []
        dashboard.start_focus_requested.connect(lambda s, m: emitted.append((s, m)))
        dashboard._on_start_focus(15)
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0], ("Math", 15))

        # Test history button signal
        history_emitted = []
        dashboard.open_history_requested.connect(lambda: history_emitted.append(True))
        dashboard.btn_history.click()
        self.assertEqual(len(history_emitted), 1)

    def test_ambient_date_and_nav_toggle(self) -> None:
        dashboard = SubjectDashboardWidget(self.engine, self.settings)
        # In idle mode: top_bar and lbl_date remain visible; nav_container is hidden
        dashboard._set_interactive_mode(False)
        self.assertFalse(dashboard.top_bar.isHidden())
        self.assertFalse(dashboard.lbl_date.isHidden())
        self.assertTrue(dashboard.nav_container.isHidden())
        self.assertTrue(dashboard.action_container.isHidden())

        # In interactive mode: nav_container and action_container become visible
        dashboard._set_interactive_mode(True)
        self.assertFalse(dashboard.nav_container.isHidden())
        self.assertFalse(dashboard.action_container.isHidden())

    def test_ambient_bottom_timeline_strip(self) -> None:
        dashboard = SubjectDashboardWidget(self.engine, self.settings)
        # Monday: has 1 class (Data Vis at 08:00)
        monday_dt = datetime(2026, 10, 19, 7, 30)
        dashboard.refresh_dashboard(monday_dt)
        self.assertEqual(dashboard.timeline_cards_layout.count(), 1)
        btn = dashboard.timeline_cards_layout.itemAt(0).widget()
        self.assertIn("08:00", btn.text())
        self.assertIn("Data Vis", btn.text())

        # Clicking the timeline card selects the subject
        btn.click()
        self.assertEqual(dashboard.selected_subject, "Data Vis")

        # Wednesday: no classes scheduled
        wednesday_dt = datetime(2026, 10, 21, 12, 0)
        dashboard.refresh_dashboard(wednesday_dt)
        self.assertEqual(dashboard.timeline_cards_layout.count(), 1)
        lbl = dashboard.timeline_cards_layout.itemAt(0).widget()
        self.assertIn("NO CLASSES SCHEDULED TODAY", lbl.text())

    def test_main_window_integration(self) -> None:
        window = MainWindow(engine=self.engine)
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_DASHBOARD)

        # Start a focus session
        window.start_focus_session(duration_minutes=15, subject_name="Math")
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_FOCUS)
        self.assertEqual(window._timer.subject_name, "Math")

        # Finish session
        window._on_session_finished("Math", 15)
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_COMPLETION)

        # Return to dashboard
        window._show_dashboard_screen()
        self.assertEqual(window._stack.currentIndex(), MainWindow.INDEX_DASHBOARD)

    def test_dialog_triggers_from_dashboard(self) -> None:
        window = MainWindow(engine=self.engine)
        invoked = []
        window.open_timetable_editor = lambda: invoked.append("timetable")
        window.open_targets_dialog = lambda s="": invoked.append(f"targets:{s}")
        window.open_manual_log_dialog = lambda s="": invoked.append(f"log:{s}")

        window._dashboard_widget.set_selected_subject("Math")

        # Top bar buttons
        window._dashboard_widget.btn_timetable.click()
        window._dashboard_widget.btn_targets.click()
        window._dashboard_widget.btn_log.click()

        # Hero card buttons
        window._dashboard_widget.btn_hero_target.click()
        window._dashboard_widget.btn_hero_log.click()

        self.assertEqual(
            invoked,
            ["timetable", "targets:Math", "log:Math", "targets:Math", "log:Math"],
        )


if __name__ == "__main__":
    unittest.main()


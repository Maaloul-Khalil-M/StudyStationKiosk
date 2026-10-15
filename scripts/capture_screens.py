"""Automated screen capture script for Study Station documentation.

Generates high-resolution screenshots in docs/screens/:
- grid_schedual.png: Academic Cockpit Grid with Tonight's Priority Task & Debrief Banner.
- debrief_modal.png: Nightly Desk Debrief questionnaire dialog.
- exit_ticket.png: Cognitive Exit Ticket dialog with traffic-light confidence.
- preparation_sheet.png: Subject Preparation Sheet with In-Class HUD Payoff questions.
- focus.png: Focus Screen with task-tethered focus gauge.
"""

import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.core.settings import AppSettings
from study_station.core.timer import FocusTimer
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.persistence.user_manager import UserManager
from study_station.ui.class_session_dialog import ClassSessionDialog
from study_station.ui.customization_dialog import CustomizationDialog
from study_station.ui.debrief_dialog import DebriefDialog
from study_station.ui.exit_ticket_dialog import ExitTicketDialog
from study_station.ui.focus_widget import FocusWidget
from study_station.ui.import_export_dialog import ImportExportDialog
from study_station.ui.main_window import MainWindow
from study_station.ui.subject_preparation_sheet import SubjectPreparationSheet
from study_station.ui.tasks_dialog import TasksDialog
from study_station.ui.user_switch_dialog import UserSwitchDialog


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    out_dir = Path(__file__).resolve().parent.parent / "docs" / "screens"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_screenss = Path(__file__).resolve().parent.parent / "docs" / "SCREENSS"
    out_screenss.mkdir(parents=True, exist_ok=True)

    def save_both(pixmap, name_screens: str, name_screenss: str | None = None):
        pixmap.save(str(out_dir / name_screens))
        print(f"Captured: {out_dir / name_screens}")
        if name_screenss:
            pixmap.save(str(out_screenss / name_screenss))
            print(f"Captured (SCREENSS): {out_screenss / name_screenss}")

    # Temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    db = Database(temp_db.name)
    repo = StudyStationRepository(db)

    # Populate realistic academic sessions
    sessions = [
        AcademicSession(
            day="Lun",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Entrepôts de données", "Cours"),
            location="SC 1",
        ),
        AcademicSession(
            day="Lun",
            time_slot=TimeSlot("09:40", "11:10"),
            subject=Subject("Entrepôts de données", "TD"),
            location="SC 1",
        ),
        AcademicSession(
            day="Mar",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Sécurité logicielle", "Cours"),
            location="Lab 5",
        ),
        AcademicSession(
            day="Mar",
            time_slot=TimeSlot("09:40", "11:10"),
            subject=Subject("Sécurité logicielle", "TP"),
            location="Lab 5",
        ),
        AcademicSession(
            day="Mer",
            time_slot=TimeSlot("11:15", "12:45"),
            subject=Subject("Visualisation de données", "Cours"),
            location="Lab 20",
        ),
        AcademicSession(
            day="Jeu",
            time_slot=TimeSlot("08:00", "09:30"),
            subject=Subject("Cybercriminalité", "Cours"),
            location="SC 3",
        ),
        AcademicSession(
            day="Ven",
            time_slot=TimeSlot("10:00", "11:30"),
            subject=Subject("Framework Web", "CI"),
            location="SC 2",
        ),
    ]
    repo.save_timetable_sessions(sessions)
    engine = ScheduleEngine(sessions=sessions, repository=repo)

    now = datetime.now()

    # Priority Todo
    todo_prio = StudyTodo(
        subject_name="Entrepôts de données",
        title="Fix Star Schema join and foreign key mapping in Lab 2 script",
        notes="Review surrogate keys and composite join performance",
        due_date=now + timedelta(days=2),
        status="pending",
    )
    repo.add_todo(todo_prio)
    engine.add_todo(todo_prio)

    # Todo with Question
    todo_q = StudyTodo(
        subject_name="Entrepôts de données",
        title="Lecture 3 dimensional modeling slides",
        notes="Understood snowflake vs star schema trade-offs",
        due_date=now - timedelta(days=1),
        status="completed",
        confidence="progressing",
        next_class_question="Why use surrogate keys instead of natural keys in slowly changing dimensions?",
    )
    repo.add_todo(todo_q)
    engine.add_todo(todo_q)

    # Another task for Sécurité logicielle
    todo_sec = StudyTodo(
        subject_name="Sécurité logicielle",
        title="Complete buffer overflow exploitation exercise",
        notes="Lab 3 write-up due before next session",
        due_date=now + timedelta(hours=14),
        status="pending",
    )
    repo.add_todo(todo_sec)
    engine.add_todo(todo_sec)

    # 1. Capture MainWindow / Grid Cockpit View (grid_schedual.png / s1 main-grid.png)
    window = MainWindow(repository=repo, engine=engine)
    window.resize(1366, 768)
    window.show()
    # Ensure banners are visible
    window._schedule_widget.debrief_banner.show()
    window._schedule_widget.priority_task_card.show()
    app.processEvents()
    pix_grid = window.grab()
    save_both(pix_grid, "grid_schedule.png", "s1 main-grid.png")
    pix_grid.save(str(out_dir / "grid_schedual.png"))

    # 2. Capture Edit Classes view (edit_schedule.png / editSchedual.png / s4 edit classes.png)
    window._schedule_widget._set_view_mode(1)
    app.processEvents()
    pix_edit = window.grab()
    save_both(pix_edit, "edit_schedule.png", "s4 edit classes.png")
    pix_edit.save(str(out_dir / "editSchedual.png"))
    window._schedule_widget._set_view_mode(0)
    app.processEvents()

    # 3. Capture Ambient Clock Screensaver (clock_no_hover.png & clock_with_hover.png)
    window._show_ambient_clock()
    window._dashboard_widget._set_interactive_mode(False)
    app.processEvents()
    save_both(window.grab(), "clock_no_hover.png", "s7 clock_no_hover.png")

    window._dashboard_widget._set_interactive_mode(True)
    app.processEvents()
    save_both(window.grab(), "clock_with_hover.png", "s7 clock_with_hover.png")

    # 4. Capture Focus Screen (focus.png)
    window.start_focus_session(duration_minutes=15, todo=todo_prio)
    app.processEvents()
    save_both(window.grab(), "focus.png")
    window.close()

    # 5. Capture Add/Edit Class Session Modal (add_class.png / s2 add class.png)
    add_dlg = ClassSessionDialog(
        session=sessions[0],
        existing_subjects=["Entrepôts de données", "Sécurité logicielle", "Visualisation de données"],
    )
    add_dlg.resize(480, 520)
    add_dlg.show()
    app.processEvents()
    save_both(add_dlg.grab(), "add_class.png", "s2 add class.png")
    add_dlg.close()

    # 6. Capture Subject Preparation Sheet (preparation_sheet.png / s2 preparation_sheet.png)
    prep_sheet = SubjectPreparationSheet(session=sessions[0], engine=engine)
    prep_sheet.resize(680, 620)
    prep_sheet.show()
    app.processEvents()
    save_both(prep_sheet.grab(), "preparation_sheet.png", "s2 preparation_sheet.png")
    prep_sheet.close()

    # 7. Capture Debrief Dialog (debrief_modal.png / s3 start debrief.png)
    debrief_dlg = DebriefDialog(engine=engine, ref_dt=now)
    debrief_dlg.resize(640, 560)
    debrief_dlg.show()
    app.processEvents()
    save_both(debrief_dlg.grab(), "debrief_modal.png", "s3 start debrief.png")
    debrief_dlg.close()

    # 8. Capture Import / Export Dialog (import_export.png / s5 importExport.png)
    ie_dlg = ImportExportDialog(engine=engine)
    ie_dlg.resize(680, 560)
    ie_dlg.show()
    app.processEvents()
    save_both(ie_dlg.grab(), "import_export.png", "s5 importExport.png")
    ie_dlg.close()

    # 9. Capture Academic Task Backlog Dialog (tasks_modal.png / s6 tasks.png)
    tasks_dlg = TasksDialog(engine=engine)
    tasks_dlg.resize(890, 680)
    tasks_dlg.show()
    app.processEvents()
    save_both(tasks_dlg.grab(), "tasks_modal.png", "s6 tasks.png")
    tasks_dlg.close()

    # 10. Capture Settings / Customization Dialog (settings.png / s8 settings.png)
    settings_dlg = CustomizationDialog(settings=AppSettings())
    settings_dlg.resize(510, 740)
    settings_dlg.show()
    app.processEvents()
    save_both(settings_dlg.grab(), "settings.png", "s8 settings.png")
    settings_dlg.close()

    # 11. Capture Exit Ticket Dialog (exit_ticket.png / s9 exit_ticket.png)
    exit_dlg = ExitTicketDialog(
        subject_name="Entrepôts de données",
        elapsed_minutes=15,
        todo=todo_prio,
    )
    exit_dlg.resize(680, 560)
    exit_dlg.show()
    app.processEvents()
    save_both(exit_dlg.grab(), "exit_ticket.png", "s9 exit_ticket.png")
    exit_dlg.close()

    # 12. Capture User Switch Dialog (switch_user_modal.png / s10 switch_user.png)
    temp_user_dir = tempfile.mkdtemp()
    user_mgr = UserManager(base_dir=temp_user_dir)
    user_mgr.create_user("Alice")
    user_mgr.create_user("Bob")
    user_dlg = UserSwitchDialog(user_manager=user_mgr)
    user_dlg.resize(560, 525)
    user_dlg.show()
    app.processEvents()
    save_both(user_dlg.grab(), "switch_user_modal.png", "s10 switch_user.png")
    user_dlg.close()
    shutil.rmtree(temp_user_dir, ignore_errors=True)

    # Clean up
    db.close()
    if os.path.exists(temp_db.name):
        try:
            os.remove(temp_db.name)
        except OSError:
            pass

    print("All screenshots successfully captured!")


if __name__ == "__main__":
    main()

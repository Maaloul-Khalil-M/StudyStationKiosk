"""Automated screen capture script for Study Station documentation.

Generates high-resolution screenshots in docs/screens/:
- grid_schedual.png: Academic Cockpit Grid with Tonight's Priority Task & Debrief Banner.
- debrief_modal.png: Nightly Desk Debrief questionnaire dialog.
- exit_ticket.png: Cognitive Exit Ticket dialog with traffic-light confidence.
- preparation_sheet.png: Subject Preparation Sheet with In-Class HUD Payoff questions.
- focus.png: Focus Screen with task-tethered focus gauge.
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication

from study_station.core.engine import ScheduleEngine
from study_station.core.models import (
    AcademicSession,
    StudyTodo,
    Subject,
    TimeSlot,
)
from study_station.core.timer import FocusTimer
from study_station.persistence.database import Database
from study_station.persistence.repository import StudyStationRepository
from study_station.ui.debrief_dialog import DebriefDialog
from study_station.ui.exit_ticket_dialog import ExitTicketDialog
from study_station.ui.focus_widget import FocusWidget
from study_station.ui.main_window import MainWindow
from study_station.ui.subject_preparation_sheet import SubjectPreparationSheet


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    out_dir = Path(__file__).resolve().parent.parent / "docs" / "screens"
    out_dir.mkdir(parents=True, exist_ok=True)

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

    # 1. Capture MainWindow / Grid Cockpit View (grid_schedual.png)
    window = MainWindow(repository=repo, engine=engine)
    window.resize(1366, 768)
    window.show()
    # Ensure banners are visible
    window._schedule_widget.debrief_banner.show()
    window._schedule_widget.priority_task_card.show()
    app.processEvents()

    pix_grid = window.grab()
    grid_path = out_dir / "grid_schedual.png"
    pix_grid.save(str(grid_path))
    print(f"Captured: {grid_path}")

    # 2. Capture Focus Screen (focus.png)
    window.start_focus_session(duration_minutes=15, todo=todo_prio)
    app.processEvents()
    pix_focus = window.grab()
    focus_path = out_dir / "focus.png"
    pix_focus.save(str(focus_path))
    print(f"Captured: {focus_path}")
    window.close()

    # 3. Capture Debrief Dialog (debrief_modal.png)
    debrief_dlg = DebriefDialog(engine=engine, ref_dt=now)
    debrief_dlg.resize(640, 560)
    debrief_dlg.show()
    app.processEvents()
    pix_debrief = debrief_dlg.grab()
    debrief_path = out_dir / "debrief_modal.png"
    pix_debrief.save(str(debrief_path))
    print(f"Captured: {debrief_path}")
    debrief_dlg.close()

    # 4. Capture Exit Ticket Dialog (exit_ticket.png)
    exit_dlg = ExitTicketDialog(
        subject_name="Entrepôts de données",
        elapsed_minutes=15,
        todo=todo_prio,
    )
    exit_dlg.resize(540, 520)
    exit_dlg.show()
    app.processEvents()
    pix_exit = exit_dlg.grab()
    exit_path = out_dir / "exit_ticket.png"
    pix_exit.save(str(exit_path))
    print(f"Captured: {exit_path}")
    exit_dlg.close()

    # 5. Capture Subject Preparation Sheet (preparation_sheet.png)
    prep_sheet = SubjectPreparationSheet(session=sessions[0], engine=engine)
    prep_sheet.resize(680, 620)
    prep_sheet.show()
    app.processEvents()
    pix_prep = prep_sheet.grab()
    prep_path = out_dir / "preparation_sheet.png"
    pix_prep.save(str(prep_path))
    print(f"Captured: {prep_path}")
    prep_sheet.close()

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

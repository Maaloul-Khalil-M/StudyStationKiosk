# Study Station — Implementation Progress

This document tracks completed features, current work in progress, and planned roadmap items based on the project documents in `docs/`.

---

## Architecture Overview

Study Station is a minimalist, schedule-aware study companion for Linux (Fedora / Xfce / X11) and cross-platform desktop use:
- **Framework:** PySide6 (Qt Widgets)
- **UI Architecture:** Custom `QPainter` for the ambient flip clock + Qt Designer (`.ui` files) for interaction screens
- **Design Philosophy:** Retro Minimal, glanceable ambient display, one question per screen, zero accumulating debt

---

## Implementation Roadmap & Status

### Milestone 1: Project Foundation & Screen Framework `[COMPLETED]`
- [x] Python project structure (`src/study_station/`, `requirements.txt`, `.gitignore`).
- [x] Virtual environment setup with `PySide6-Essentials`.
- [x] Full-screen black window (`MainWindow`) with 1366×768 target support.
- [x] Clean exit shortcut (<kbd>Esc</kbd> / <kbd>Q</kbd>) and fullscreen toggle (<kbd>F11</kbd>).
- [x] Linux/Fedora X11 documentation (e.g. `xcb-util-cursor`, `libxkbcommon-x11`).

### Milestone 2: Ambient Flip Clock & Schedule Engine `[COMPLETED]`
- [x] Custom `QPainter` clock widget (`AmbientClockWidget`).
- [x] Retro minimal typography with dynamic screen-height font scaling (~22%).
- [x] Subtle flip-clock horizontal crease across digits.
- [x] 12-hour / 24-hour time format toggle (<kbd>T</kbd>).
- [x] Core domain model (`AcademicSession`, `TimeSlot`, `Subject`, `StudyCycle`, `StudyLog`).
- [x] Deterministic `ScheduleEngine` with timetable parsing, session detection, cycle creation, and priority suggestion.
- [x] Discreet secondary progress line (`SUBJECT · X / Y MIN`) rendered underneath clock in calm muted grey (`#8A8A8E`).
- [x] Unit test suite (`tests/test_engine.py`) covering all schedule engine operations.

### Milestone 2.5: Modern UI Redesign & Calm Discipline `[COMPLETED]`
- [x] Authentic Fliqlo-inspired split-flap flip cards with uniform panel gaps and mechanical side notch cutouts.
- [x] Snappy 3D-folding flip animation (~200ms) on minute/second transitions.
- [x] Calm, low-contrast Date line at top (`WEDNESDAY, OCT 14`, font size 13px, `#71717A`) that never competes with the clock.
- [x] Auto-hiding Action Bar: hidden by default for maximum calm; fades in smoothly on mouse movement/key press, fades out after 3.5s of inactivity.
- [x] Single primary focus action: `[ ▶ Start Focus ]` plus a quiet `[ ⚙ Customize ]` button.
- [x] Cursor auto-hide when idle in fullscreen.
- [x] Single discreet progress line: `SUBJECT · XX / YY MIN ▾` with dropdown subject selector on click.
- [x] Normalized French spelling typography (e.g. `ACCÈS`, `CONTRÔLE`).
- [x] Modernized Focus screen:
  - Subject in white (`#F4F4F5`), gracefully truncated.
  - State label in readable medium gray (`#9CA3AF`).
  - Large tabular countdown timer.
  - Cycle progress indicator (`XX / YY MIN (CYCLE)`).
  - Visual session progress bar along the bottom of the card.
  - Harmonized pill buttons: primary filled `Pause`, outline `+5 Min`, outline red `End Session` with hover/pressed states.
  - Quiet shortcuts hint line (`Space to pause · + for 5m · Esc to end`).
- [x] Modern Customization Modal (`CustomizationDialog`):
  - 12h vs 24h toggle
  - Optional seconds flip card
  - Emphasize date toggle & format
  - Color palettes (Classic Noir, Midnight Slate, Warm Espresso)
  - Animation toggle (Smooth flip vs Instant)

### Milestone 3: Focus Timer & Completion Screens `[COMPLETED]`
- [x] Screen management with `QStackedWidget` (Ambient Clock ↔ Focus ↔ Completion).
- [x] Focus Timer engine (`FocusTimer`) using timestamp-based target ends (`target_end_time`) for suspend/resume resilience.
- [x] Flexible micro-session durations (5, 10, 15, 25 minutes).
- [x] Low-friction session start from ambient screen (<kbd>Space</kbd> / <kbd>Enter</kbd> or number keys `1`-`4`, or clicking action bar buttons).
- [x] Focus screen (`focus_screen.ui` + `FocusWidget`):
  - Subject label
  - Large countdown display
  - Simple state label (Focusing, Paused)
  - Controls: Pause / Resume, +5 min, End session
- [x] Completion screen (`completion_screen.ui` + `CompletionWidget`):
  - Session summary confirmation (e.g. `+15 MIN`)
  - Updated study cycle progress (`X / Y MIN COMPLETED`)
  - Auto-return to Ambient Clock after a brief interval (5s) or any keypress.
- [x] Unit test suite (`tests/test_timer.py`) verifying timer calculations and pause/resume logic.

### Milestone 4: Local Persistence & State Recovery `[COMPLETED]`
- [x] SQLite database architecture with WAL mode (`Database` in `database.py`).
- [x] Standard cross-platform storage locations (`~/.local/share/study_station/studystation.db` on Linux, `%APPDATA%/StudyStation/` on Windows).
- [x] Persistent study logs repository (`StudyStationRepository.add_study_log`, `get_all_study_logs`).
- [x] Timetable sessions repository with auto-seeding from `docs/example.json` if empty.
- [x] Subject review target overrides repository.
- [x] UI settings persistence (`AppSettings` stored in SQLite, reloaded on startup).
- [x] Hardware resilience: active timer state tracking & recovery:
  - If app restarts or wakes from sleep with session in progress: seamlessly resumes remaining countdown.
  - If machine was suspended/off past target end: automatically logs the completed session so student effort is never lost.
- [x] Unit test suite (`tests/test_persistence.py`) verifying all CRUD operations and timer recovery scenarios.

### Milestone 5: Secondary Screens (Qt Designer) `[COMPLETED]`
- [x] Weekly Timetable Editor dialog ([`timetable_dialog.ui`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/designer/timetable_dialog.ui) + `TimetableDialog`):
  - Chronological schedule table (Day, Time, Subject, Type, Location).
  - Add session form with instant validation.
  - Delete selected session.
  - Persists directly to SQLite and updates active cycles in real time.
- [x] Subject Review Target Configuration dialog ([`targets_dialog.ui`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/designer/targets_dialog.ui) + `TargetsDialog`):
  - Configure target review minutes per subject (e.g. 45m, 60m, 90m).
  - Quick preset buttons (`30m`, `60m`, `90m`).
  - Persists to SQLite and recalculates cycle completion percentage immediately.
- [x] Offline Study Time Logger dialog ([`manual_log_dialog.ui`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/designer/manual_log_dialog.ui) + `ManualLogDialog`):
  - Record offline review completed away from the computer (books, paper, library).
  - Subject selector and minutes spinbox.
  - Automatically logs `StudyLog(source="manual")` and displays completion feedback (`+X MIN`).
- [x] Central access via Customization Dialog and dedicated keyboard shortcuts (<kbd>E</kbd> for Timetable, <kbd>S</kbd> for Targets, <kbd>M</kbd> for Manual Log).
- [x] Unit test suite (`tests/test_secondary_dialogs.py`) verifying all three dialogs and their signal pipelines.

### Milestone 6: Subject-Centric UI & Streamlined Interaction Rework `[COMPLETED]`
- [x] **Subject-First Philosophy:** Refocused Study Station so the **Subject** and its review cycle are the true hero and centerpiece rather than just a clock screensaver.
- [x] **Hero Subject Card:**
  - Clear, prominent subject title with normalized French typography (`ACCÈS`, `CONTRÔLE`).
  - Core format & location badge (`TP · Lab 20`, or emerald `● IN CLASS NOW` when active).
  - High-visibility progress bar with status percentage and remaining minutes counter.
  - Next scheduled class context: `📅 Next class: Friday at 08:00 (in 2 days)`.
  - Prominent, easy-to-hit action buttons:
    - `[ ▶ Start Focus (15m) ]` (Primary pill, bold filled)
    - `[ ▶ 25m ]` (Secondary pill)
    - `[ ✍ Log Time ]` (Secondary pill, pre-selects current subject)
    - `[ ✏ Edit Target ]` (Secondary pill, opens target configurator with current subject highlighted)
- [x] **Subject Switcher Carousel / Shelf:**
  - Horizontal shelf displaying all enrolled subjects with mini progress indicators (`Data Vis · 25/60m`, `✓ Veille · 60/60m`).
  - `★ Auto (Next Class)` mode to dynamically follow the next arriving class deadline.
  - 1-click subject switching updating the Hero Card in real time.
- [x] **Compact Split-Flap Flip Clock:**
  - Isolated into `SplitFlapClockWidget`: authentic retro-minimal Fliqlo-inspired cards, 3D flip folding animations, center groove, and side notches.
  - Repositioned as an elegant upper companion to the subject hero rather than monopolizing the screen.
- [x] **Streamlined Top Bar Navigation:**
  - One-click access to `[ 📅 Timetable ]`, `[ 🎯 Targets ]`, `[ ✍ Log Time ]`, `[ ⚙ Settings ]`, and `[ ⛶ Fullscreen ]`.
- [x] **Domain Model Expansion:**
  - `SubjectSummary` model with `ScheduleEngine.get_subject_summary` and `get_all_subjects_summary`.
- [x] **Dialog Sizing & Translucent Background Fix:**
  - Resolved issue where frameless translucent dialogs (`TimetableDialog`, `TargetsDialog`, `ManualLogDialog`) loaded via `QUiLoader` defaulted to (0, 0) size and 0 alpha (invisible).
  - Encapsulated within solid `QFrame#dialogContainer` with fixed dimensions (`760x580`, `560x540`, `460x360`) and <kbd>Esc</kbd> dismissal.
  - Hardened signal/slot bindings using `lambda checked=False: ...` to safely handle Qt's boolean click parameter.
- [x] **Unit Test Suite:**
  - 24/24 passing unit tests across `test_dashboard_ui.py`, `test_engine.py`, `test_timer.py`, `test_persistence.py`, `test_dialog.py`, and `test_secondary_dialogs.py`.


---

## Key Decisions & Guiding Rules
1. **Subject first (not Time first):** Study Station is a dedicated study machine; the Subject, its study cycle review progress, and the class schedule are the visual and functional centerpiece. The split-flap clock is a calm, glanceable companion.
2. **One question per screen:**
   - *Dashboard:* What subject am I reviewing, what is my cycle progress, and when is my next class?
   - *Focus:* What am I working on right now?
   - *Completion:* Did my effort count toward my subject goal?
3. **No guilt debt:** Unfinished review minutes do not accumulate as overdue debt across class cycles.
4. **Deterministic core:** Engine, models, and timer logic remain pure and unit-testable independently of Qt UI.


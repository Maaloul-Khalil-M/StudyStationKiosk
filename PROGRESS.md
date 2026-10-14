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

### Milestone 6.5: Professional UI Polish & Integrated Split-Station Overhaul `[COMPLETED]`
- [x] **Integrated Split-Station Cockpit (Option A):**
  - Eliminated the 200px empty black void on 1366×768 displays by arranging the Hero Focus Card (stretch=6) and Upcoming Classes Card (stretch=4) in a balanced horizontal cockpit layout.
  - Retained the scaled ambient split-flap flip clock at the top as an authentic mechanical companion.
- [x] **Upcoming Classes Timeline:**
  - Added `ScheduleEngine.get_upcoming_sessions()` returning chronological upcoming class sessions from SQLite.
  - Dynamic upcoming card rendering with class times, course titles, room/type badges, and friendly relative countdowns (e.g. `Tomorrow at 08:00`).
- [x] **Global Modern QSS Reset & OS Artifact Elimination:**
  - Eliminated 1990s Windows 95 17px bevel scrollbars across all scroll areas, tables, and dialogs.
  - Implemented 5px sleek semi-transparent thumb with 0-height arrows, smooth rounded corners, and transparent gutter.
  - Uniform dark theme resets for `QLineEdit`, `QSpinBox`, `QComboBox`, `QTableWidget`, `QHeaderView`, and `QProgressBar`.
- [x] **Iconography & Visual Tone Cleanup:**
  - Replaced multi-colored emojis in the top navigation bar (`📅`, `🎯`, `✍`, `⚙`, `⛶`) with clean, typographic labels and subtle unicode glyphs.
  - Replaced emojis in subject chips, hero buttons, and dialogs with professional micro-typography.
- [x] **Qt Button Radius Quirks Solved:**
  - Solved Qt's Windows rendering engine bug where `border-radius` calculation collapses to 90-degree rectangle corners if `border: none;` or `border-radius > (height / 2)`.
  - Enforced explicit button geometry (`height: 36px; border-radius: 18px; border: 1px solid <color>;`) guaranteeing razor-smooth pill buttons.
- [x] **Full-Width Focus Screen Overhaul:**
  - Widened focus card to 780×420 to utilize the 1366×768 canvas proportionally.
  - Upgraded timer typography to 76pt tabular monospace numerals.
  - Enabled multi-line word wrapping on long French subject titles (`wordWrap=True`).
  - Added dynamic state badge coloring: `#10B981` emerald pill for active focus, `#F59E0B` amber pill for paused.
- [x] **Secondary Dialog Polish:**
  - Fixed Windows shortcut parser issue in `timetable_dialog.ui` where `&` resulted in `Save Close` by properly escaping to `Save && Close`.
  - Harmonized spinboxes in `targets_dialog.ui` to 92px width with clear `" m"` suffix and modern zero-arrow scrollbars.
  - Harmonized action buttons across all secondary dialogs (`ManualLogDialog`, `TimetableDialog`, `TargetsDialog`, `CustomizationDialog`).
- [x] **Verification & Test Suite:**
  - Created automated screenshot tool `capture_screens.py` refreshing all screen states in `docs/currentScreens/`.
  - 100% test pass rate maintained: 24/24 unit tests passing.


---

## Key Decisions & Guiding Rules
1. **Subject first (not Time first):** Study Station is a dedicated study machine; the Subject, its study cycle review progress, and the class schedule are the visual and functional centerpiece. The split-flap clock is a calm, glanceable companion.
2. **One question per screen:**
   - *Dashboard:* What subject am I reviewing, what is my cycle progress, and when is my next class?
   - *Focus:* What am I working on right now?
   - *Completion:* Did my effort count toward my subject goal?
3. **No guilt debt:** Unfinished review minutes do not accumulate as overdue debt across class cycles.
4. **Deterministic core:** Engine, models, and timer logic remain pure and unit-testable independently of Qt UI.

---

## Next Steps Roadmap & Recommended Work

### Milestone 7: Study History & Cycle Statistics `[RECOMMENDED NEXT]`
- [ ] **Study History Dialog (`HistoryDialog`):**
  - Chronological log viewer of all completed focus sessions and manual entries (Date, Time, Subject, Duration, Source).
  - Ability to delete or correct mistaken time logs.
  - Weekly study summary: total hours completed across subjects.
  - Cycle target completion rate (percentage of study cycles completed on target).
- [ ] **Top Bar Integration:** Add a `[ 📊 History ]` button in the top navigation bar.

### Milestone 8: Audio Cues & Calm Feedback
- [ ] **Discreet Completion Chime:**
  - Subtle, calm audible tone when a focus countdown finishes (useful when looking away from the screen reading notes or books).
  - Configurable sound toggle in Settings (`CustomizationDialog`): Enabled / Disabled.
  - Cross-platform audio via `QSoundEffect` or synthesized chime.

### Milestone 9: Timetable Portability (Import & Export)
- [ ] **Timetable JSON / CSV Export & Import:**
  - Export timetable sessions to standard JSON/CSV for backup or sharing.
  - Import schedule files directly through `TimetableDialog` with collision validation.
- [ ] **Optional PDF Timetable Parser:**
  - CLI/dialog helper to extract timetable sessions from university PDF schedules with a human verification step before saving.

### Milestone 10: Dedicated Kiosk Mode & Packaging
- [ ] **Custom Duration Presets:**
  - Configure preferred primary focus duration (e.g., 20m, 30m) directly in Settings.
- [ ] **Linux / Fedora Dedicated Machine Deployment:**
  - Autostart `.desktop` entry for Xfce / X11 kiosk setup.
  - Standalone binary build script with PyInstaller for one-click deployment.



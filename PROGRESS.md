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

### Milestone 6.6: Kiosk & Ambient Study Appliance Overhaul `[COMPLETED]`
- [x] **Philosophy Pivot from SaaS Dashboard to Desk Appliance:**
  - Eliminated web SaaS card clutter, side-by-side widget grids, and permanent toolbars that distracted students reading books from 1–2 meters away.
  - Documented formal critique and architecture in [`docs/KIOSK_MINIMAL_SPEC.md`](file:///c:/Users/marj/Music/Study%20Station/docs/KIOSK_MINIMAL_SPEC.md).
- [x] **Screen 1: Zero-Distraction Ambient Kiosk Station:**
  - **Idle Mode (Default):** Shows only the medium mechanical split-flap flip clock, giant 38pt Swiss typography subject name, and a single-line rotating info carousel with a hairline progress bar. Zero borders, zero card boxes, zero permanent buttons.
  - **Hover Mode (Mouse Move):** Top navigation (`[ 📅 Schedule ]`, `[ 🎯 Targets ]`, `[ ✍ Log ]`, `[ ⚙ Settings ]`, `[ ⛶ ]`), primary focus action (`[ ▶ START FOCUS ]`), and carousel arrow pills smoothly fade in, then auto-hide after 3.5s of stillness.
- [x] **Screen 2: Visual Weekly Schedule Grid (`docs/grid.pdf` / Google Calendar Model):**
  - Implemented [`WeeklyScheduleGridDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/weekly_schedule_dialog.py) replicating the student's real university schedule (`docs/grid.pdf`).
  - Columns: `LUN`, `MAR`, `MER`, `JEU`, `VEN`, `SAM`.
  - Rows: Standard university time slots (`08:00 - 09:30`, `09:40 - 11:10`, `11:15 - 12:45`, `13:30 - 15:00`, `15:10 - 16:40`).
  - Each class card displays course format badge (`TP`, `COURS`, `TD`, `CI`), clean course title, room (`Lab 20`, `SC 3`), and `● NOW` real-time highlight.
  - 1-click subject switcher: Clicking any class card instantly sets the active subject.
  - Added `[ 📄 Original PDF ]` button to launch the original schedule PDF in the default OS viewer.
- [x] **Screen 3: Pure Concentration Focus Screen:**
  - Borderless, full-bleed dark focus mode.
  - Controls (`[ Pause ]`, `[ +5 Min ]`, `[ End Session ]`, shortcut hints) auto-hide when idle so the student sees only the subject name, massive 76pt countdown numerals, and session progress line.
- [x] **Secondary Screens Appliance Polish:**
  - Added quick duration preset pills (`15m`, `30m`, `45m`, `60m`) to `ManualLogDialog`.
  - Maintained preset pills and 92px spinboxes in `TargetsDialog`.
- [x] **Verification & Tests:**
  - 24/24 unit tests passing.

### Milestone 6.7: Comprehensive Aesthetics Overhaul Across ALL Screens `[COMPLETED]`
- [x] **Deep Obsidian Palette & Contrast Tuning (`theme.py`):**
  - Replaced harsh `#000000` pitch black with luxury deep obsidian (`#09090B`).
  - Elevated surfaces to `#121216`, subtle hairline borders to `#24242A`, off-white typography to `#F4F4F6`, and calm emerald `#10B981` accents.
- [x] **Full-Screen Schedule & Inline Class Editor (`schedule_screen_widget.py`):**
  - Replaced floating window dialog with a seamless full-screen station mode (`INDEX_SCHEDULE = 3`) fitting the 1366×768 canvas edge-to-edge.
  - Eliminated awkward "modal on top of modal" stacking: View Switcher allows switching between Calendar Grid mode and Inline Class Editor without spawning popup windows.
  - Full calendar grid based on university schedule (`docs/grid.pdf`): 6 day columns (`LUN`–`SAM`) × 5 slot rows with live active day/session highlights.
  - One-click subject selection: clicking any class block instantly selects the subject and returns to dashboard.
- [x] **Modal Scrim Backdrop Overlay (`main_window.py`):**
  - Implemented `QFrame#scrimOverlay` (`rgba(9, 9, 11, 0.96)`) covering the full client area whenever a secondary dialog is active.
  - Completely darkens the background, eliminating distracting text peek-through from the giant hero subject title.
- [x] **Typography & Micro-Interaction Polish:**
  - Screen 1 (Ambient): Cleaned carousel typography to pure status lines (`● 0 / 60 MIN COMPLETED · 0%`, `NEXT CLASS · Tomorrow at 08:00 · Lab 20`), refined hover pills, removed redundant hero buttons.
  - Screen 2 (Focus): True borderless full-bleed canvas, tracked uppercase subject header, sleek emerald/amber pill badge (`● FOCUSING`, `⏸ PAUSED`), 76pt countdown, auto-hiding controls.
  - Screen 3 (Targets): Widened to 660×540 with active preset pills (`30m`, `60m`, `90m`) illuminated in emerald.
  - Screen 4 (Log Time): Redesigned with 480×420 proportions, preset pills (`15m`, `30m`, `45m`, `60m`), and spacious input fields.
  - Screen 5 (Settings): Clean dark cards, emerald toggle states, and unified action pills.
- [x] **Verification & Visual Artifacts:**
  - Automated screen capture refreshed across all 8 states in `docs/screens/` and `docs/currentScreens/`:
    `main_noHover.png`, `main_hover.png`, `schedual.png`, `editSchedual.png`, `focus.png`, `target.png`, `log.png`, `settings.png`.
  - 100% test pass rate: 24/24 unit tests passing.

### Milestone 6.8: Evangelion Typography & NERV HUD System (`/docs/typography Evangelion.md`) `[COMPLETED]`
- [x] **Typographic Analysis & Dual Typeface Architecture:**
  - Studied `/docs/typography Evangelion.md` (Peiran Tan's study of Matisse EB display serif + tight-tracked Helvetica/grotesque telemetry).
  - Expanded `get_modern_font()` in `theme.py` with `eva_display` (high stroke contrast editorial serif with mechanical compression tracking at 96%) and `hud_telemetry` (tracked uppercase monospace/condensed grotesque).
- [x] **Settings & Themes:**
  - Added new **`NERV Terminal`** theme (`#050507` void canvas, NERV emergency orange/amber `#FF7700` telemetry accents).
  - Added a **`TYPOGRAPHY SYSTEM`** toggle in Settings allowing instant switching between `Evangelion Serif` and `Modern Sans`.
  - 2x2 theme grid displaying all 4 themes (`Classic Noir`, `Midnight Slate`, `Warm Espresso`, `NERV Terminal`).

### Milestone 6.9: Minimalist Text & Noise Elimination Overhaul `[COMPLETED]`
- [x] **Philosophy — Clean Typography Over ASCII Clutter:**
  - Addressed user critique: removed useless punctuation noise (`//`, `[...]`, `(...)`) while retaining the high-impact editorial display serif typography.
  - Achieved pure, distraction-free kiosk minimalism where letterforms carry visual weight instead of arbitrary punctuation.
- [x] **Screen 1 (Ambient Main Dashboard):**
  - Date header cleaned to pure `THURSDAY, OCT 15` (removed `//`).
  - Action button cleaned to bold `START FOCUS` and duration pill `25m` (removed `▶ ENGAGE FOCUS (Space)` and `[ 25M ]`).
  - Subtitle cleaned to `Click to open schedule` (removed `▼ SELECT MISSION // SCHEDULE GRID`).
  - Rotating carousel slides cleaned of `//` and brackets:
    - `● 0 / 60 MIN COMPLETED · 0%`
    - `NEXT CLASS · Tomorrow at 08:00`
    - `TP · Salle 5`
- [x] **Screen 2 (Weekly Schedule Grid):**
  - Header title: `WEEKLY SCHEDULE` (removed `// OPERATION GRID`).
  - Mode toggle: `Grid View` | `Edit Classes` (removed unicode glyphs and brackets).
  - PDF button: `Original PDF` (clean label).
  - Corner header: `TIME` (removed `// SLOT`).
  - Day columns: `LUN`, `MAR`, `MER`, `JEU`, `VEN`, `SAM` (removed `//`).
  - Grid cards: format badges `TP`, `COURS`, `TD`, `CI` (removed `[TP]`, `[COURS]`); clean room labels `Lab 20` (removed `[Lab 20]`); active badge `● NOW` (removed `● ACTIVE`).
  - Inline class editor: cleaned placeholder times to `08:00` and `09:30` (removed `(08:00)` and `(09:30)`).
- [x] **Screen 3 (Focus Screen):**
  - Status badge: `● FOCUSING` in emerald / `⏸ PAUSED` in amber (removed `ACTIVE //` and `SUSPENDED //`).
  - Shortcuts hint: `Space to pause · +5m · Esc to end` (removed `SPACE // PAUSE · [+] // +5M · ESC // ABORT`).
- [x] **Screen 4 (Subject Targets Dialog):**
  - Dialog title: `SUBJECT TARGETS` (removed `// PROTOCOL CONFIG`).
- [x] **Screen 5 (Manual Log Dialog):**
  - Dialog title: `LOG STUDY TIME` (removed `// OFFLINE SESSION`).
  - Subtitle: `Record review completed away from the screen.` (removed `(books, paper, library)`).
- [x] **Screen 6 (Settings Dialog):**
  - Time format options: clean `24-Hour` and `12-Hour` (removed `(21:08)` and `(9:08 PM)`).
  - Typography options: `Evangelion Serif` and `Modern Sans` (removed `//` and `HUD`).
- [x] **Verification & Test Suite:**
  - 100% test pass rate: 24/24 unit tests passing.
  - Automated screen captures updated and verified across `docs/screens/` and `docs/currentScreens/`:
    `main_no_hover.png`, `main_with_hover.png`, `focus.png`, `grid_schedual.png`, `editSchedual.png`, `targets.png`, `log.png`, `settings.png`.

### Milestone 6.10: Focus Screen Circular Ring Gauge (Phase A) `[COMPLETED]`
- [x] **Visual Presence & Appliance Geometry:**
  - Designed and implemented [`FocusRingGaugeWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/focus_ring_gauge.py) using custom antialiased `QPainter`.
  - Replaced flat horizontal progress bar with an authentic dual-concentric radial arc gauge.
  - **Outer Arc:** Dynamic session countdown ring (depletes clockwise with smooth rounded caps; emerald `#10B981` during focus, amber `#F59E0B` when paused, orange `#FF7700` in NERV mode).
  - **Inner Arc:** Multi-day subject review cycle goal tracker (slate cyan `#38BDF8` filling toward 100% target).
  - **Center Hub:** Unified center layout containing pill status badge (`● FOCUSING` / `⏸ PAUSED`), 52pt tabular monospace numerals, and cycle progress subtitle.
- [x] **Integration & Theme Synchronization:**
  - Embedded seamlessly into [`FocusWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/focus_widget.py) while maintaining 100% backward compatibility for all properties.
  - Linked theme and typography switching via `apply_settings()` in `MainWindow`.
- [x] **Verification & Tests:**
  - Added dedicated unit test suite in [`tests/test_focus_ring_gauge.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_focus_ring_gauge.py).
  - 100% test pass rate maintained: 28/28 unit tests passing.
### Milestone 6.11: Date-Anchored Calendar Grid & Week Navigator (Phase B — Part 1) `[COMPLETED]`
- [x] **Deterministic Calendar Engine Calculations:**
  - Added `get_week_start(ref_date)` returning Monday date across months and years.
  - Added `get_week_dates(ref_date, days_count=6)` computing the 6 academic calendar dates (Monday to Saturday).
  - Added `format_week_range(ref_date)` producing formatted headers (e.g. `12 – 17 OCT 2026`, `28 SEP – 03 OCT 2026`).
  - Added `get_day_date(day_code, ref_date)` resolving specific calendar dates for any weekday abbreviation.
- [x] **Visual Calendar Navigation Bar:**
  - Added tactical week switcher in the header: `[ ‹ ]`, `12 – 17 OCT 2026`, `[ › ]`.
  - Added dynamic `[ Today ]` shortcut button that illuminates when looking at past/future weeks and auto-hides when on the current week.
- [x] **Calendar Day Columns with Real Dates:**
  - Transformed static day headers into dual-line cards showing Day Code (`LUN`, `MAR`...) and Real Calendar Date (`12 OCT`, `13 OCT`...).
  - Today's column is highlighted with an emerald glowing border (`border: 1px solid #059669; background: #14221D;`), bright green typography, and an emerald `TODAY` badge.
  - Active session indicator (`● NOW`) only triggers when viewing the actual current day.
- [x] **Verification & Test Suite:**
  - Added unit test coverage for date calculations in [`tests/test_engine.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_engine.py).
  - Added unit test for week navigation in [`tests/test_secondary_dialogs.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_secondary_dialogs.py).
  - Refreshed screen capture in [`docs/screens/grid_schedual.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/grid_schedual.png).

### Milestone 6.12: Direct Visual Schedule Management (Phase B — Part 2) `[COMPLETED]`
- [x] **Direct Card Interaction on the Calendar Grid:**
  - Clicking any class block on the calendar opens [`ClassSessionDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/class_session_dialog.py) with dark backdrop scrim.
  - Allows 1-click **Start Focus** on that subject, in-place editing of session details (Day, Start/End times, Subject name, Core type, Room), or deleting the class.
  - Changes persist immediately to SQLite and update the calendar grid in real time.
- [x] **Click-to-Add on Empty Slots:**
  - Implemented interactive [`EmptyGridSlot`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/schedule_screen_widget.py#L45-L84) cards: calm dark obsidian by default, reveals a subtle emerald `+` on hover.
  - Clicking any empty slot opens `ClassSessionDialog` pre-filled with that column's day and that slot's start/end times.
  - Eliminates the need to switch to the raw developer database spreadsheet table.
- [x] **Verification & Test Suite:**
  - Added unit test suite in [`tests/test_class_session_dialog.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_class_session_dialog.py) covering add, edit, delete, focus start, and widget signal pipelines.
  - 100% test pass rate maintained: 36/36 unit tests passing.
  - Refreshed screen capture in [`docs/screens/editSchedual.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/editSchedual.png).

### Milestone 6.13: Ambient Station Spatial Balance & Date Visibility (Phase C) `[COMPLETED]`
- [x] **Permanent Ambient Date Anchoring:**
  - Separated top bar date label (`self.lbl_date`) from navigation action buttons (`self.nav_container`).
  - In idle glance mode, `lbl_date` (`THURSDAY, OCT 15` in `#71717A`, tracking 1.5px) remains permanently visible in the top-left corner, anchoring the upper third of the station.
  - Navigation action buttons (`Schedule`, `Targets`, `Log`, `Settings`, `⛶`) auto-reveal smoothly on mouse interaction.
- [x] **Ambient Today's Timeline Strip:**
  - Implemented [`_create_timeline_strip`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/dashboard_widget.py) along the bottom of the dashboard screen.
  - Grounding the bottom 30% of the canvas with today's scheduled classes in chronological order:
    - `✓` Dimmed past classes (`✓ 08:00 Sécurité...`, `✓ 09:40 Entrepôts...`).
    - `● NOW` Highlighted active class in emerald pill (`● NOW 15:10 – 16:40 tests logiciels (SC V)`).
    - Neutral cards for upcoming classes with start times and room numbers.
    - Graceful fallback for non-school days (`NO CLASSES SCHEDULED TODAY · FREE STUDY & REVIEW`).
  - Clickable tactile capsules allowing direct subject switching or focus from the ambient strip.
- [x] **Live Updates & Deterministic Engine Helpers:**
  - Added `ScheduleEngine.get_day_sessions()` for sorted chronological day session queries.
  - Added 30-second periodic status timer updating live class states and date roll-overs in real time.
- [x] **Verification & Test Suite:**
  - 100% test pass rate: **39/39 passing unit tests** across all 8 test modules.
  - Screen captures re-generated and verified at 1366×768:
    - [`docs/screens/main_no_hover.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/main_no_hover.png) (idle mode: balanced clock, subject, date, and today's timeline).
    - [`docs/screens/main_with_hover.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/main_with_hover.png) (interactive mode: revealing top nav micro-pills, action buttons, and hint).

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

### Milestone 7: Study History & Cycle Statistics `[COMPLETED]`
- [x] **Study History & Statistics Dialog ([`history_dialog.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/history_dialog.py)):**
  - Designed in obsidian minimal aesthetic (`#121215` canvas with `#27272A` borders) and dark scrim backdrop overlay.
  - **Overview KPI Cards:**
    - `THIS WEEK`: Formatted volume in emerald (e.g. `4h 15m`).
    - `ALL-TIME TOTAL`: Total completed study volume across all subjects.
    - `CYCLE COMPLETION`: Real-time percentage of active subject review cycles meeting their targets (e.g. `75% · 3 of 4 cycles on target`).
  - **Multi-Criteria Filtering:**
    - Dynamic subject filter: `All Subjects` or individual enrolled subject.
    - Source filter: `All Sources`, `Timer (Focus)`, `Manual (Offline)`.
    - Session counter badge (`X sessions recorded`).
  - **Chronological History Table:**
    - 5 columns: `DATE & TIME`, `SUBJECT`, `DURATION` (`+25m` emerald pill), `SOURCE` (blue `TIMER` or purple `MANUAL`), `ACTIONS`.
    - Human-friendly timestamps: `Today, 14:30`, `Yesterday, 09:15`, or `14 Oct, 11:00`.
- [x] **In-Place Log Correction & Mistake Recovery:**
  - Implemented [`EditStudyLogDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/history_dialog.py#L65-L165): allows editing duration (with preset pills `15m`, `25m`, `30m`, `45m`, `60m`) or re-assigning subject.
  - Interactive deletion confirmation with instant recalculation: removing mistaken logs automatically updates active study cycle progress and dashboard widgets without app restart.
- [x] **Persistence & Engine Upgrades:**
  - Added `delete_study_log()` and `update_study_log()` to [`StudyStationRepository`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/persistence/repository.py) and [`ScheduleEngine`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/engine.py).
  - Added deterministic stats helpers: `get_weekly_study_minutes()`, `get_weekly_study_by_subject()`, `get_total_study_minutes()`, and `get_cycle_completion_stats()`.
  - Added distinct `source="manual"` vs `source="timer"` tracking across `MainWindow._on_session_finished()`.
- [x] **Top Bar Navigation & Shortcuts:**
  - Added `[ History ]` button in the top navigation bar of [`SubjectDashboardWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/dashboard_widget.py).
  - Dedicated keyboard shortcut: <kbd>H</kbd> in ambient mode instantly opens the history dialog.
- [x] **Verification & Test Suite:**
  - Added dedicated unit test suite in [`tests/test_history_dialog.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_history_dialog.py) covering dialog creation, KPIs, filtering, editing, and deletion.
  - Expanded `tests/test_persistence.py`, `tests/test_engine.py`, and `tests/test_dashboard_ui.py`.
  - 100% test pass rate maintained: **49/49 passing unit tests** across all 9 test suites.
  - Screen capture refreshed in [`docs/screens/history.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/history.png) and [`docs/screens/main_with_hover.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/main_with_hover.png).

---

## Key Decisions & Guiding Rules
1. **Subject first (not Time first):** Study Station is a dedicated study machine; the Subject, its study cycle review progress, and the class schedule are the visual and functional centerpiece. The split-flap clock is a calm, glanceable companion.
2. **One question per screen:**
   - *Dashboard:* What subject am I reviewing, what is my cycle progress, and when is my next class?
   - *Focus:* What am I working on right now?
   - *Completion:* Did my effort count toward my subject goal?
   - *History:* How much study effort have I accumulated this week and did I hit my cycle goals?
3. **No guilt debt:** Unfinished review minutes do not accumulate as overdue debt across class cycles.
4. **Deterministic core:** Engine, models, and timer logic remain pure and unit-testable independently of Qt UI.

---

### Milestone 8: Audio Cues & Calm Feedback `[COMPLETED]`
- [x] **Harmonic Synthesis Engine ([`sound_manager.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/sound_manager.py)):**
  - Pure Python additive harmonic chime synthesizer (16-bit 44.1kHz mono PCM WAV):
    - Multi-layer chime: C5 (523.25 Hz) fundamental, E5 (659.25 Hz) major third, G5 (783.99 Hz) fifth, and C6 (1046.50 Hz) sparkle.
    - 15ms smooth attack envelope eliminating audio onset clicks, followed by gentle exponential decay over 1.4s.
    - Zero external audio binary dependencies (pure Python `wave` + `struct` + `math`).
    - Stored at `src/study_station/assets/sounds/completion_chime.wav` with deterministic auto-generation if missing.
- [x] **Cross-Platform Non-Blocking Playback:**
  - Asynchronous background thread playback preventing any UI thread stutter or frame drops:
    - **Windows:** Native `winsound.PlaySound` (asynchronous zero-latency).
    - **Linux (Fedora / X11):** Direct pipe to `pw-play` (PipeWire), `paplay` (PulseAudio), `aplay` (ALSA), or `canberra-gtk-play`.
    - **macOS:** Native `afplay`.
    - Graceful fallback for headless CI and audio-disabled systems.
- [x] **Settings & Persistence Integration:**
  - Added `sound_enabled: bool = True` to [`AppSettings`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/settings.py).
  - Persisted in SQLite settings table with backward-compatible deserialization defaults.
- [x] **Settings UI ([`customization_dialog.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/customization_dialog.py)):**
  - Added **`AUDIO & CALM CUES`** section.
  - Emerald toggle: `Focus completion chime`.
  - Interactive `[ ▶ Test Chime ]` preview pill button allowing instant testing of the acoustic feedback.
  - Sized to 500×680 to fit all sections cleanly.
- [x] **Focus Session Flow Integration ([`main_window.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/main_window.py)):**
  - Focus countdown ending at 00:00 automatically triggers the calm completion chime when `sound_enabled` is active.
- [x] **Bug Fixes & UI Polishing:**
  - **Main Screen Flip Clock Layout:** Re-engineered `SplitFlapClockWidget._get_layout_metrics` to enforce mathematically symmetrical card and colon spacing (`Card 1` → `gap` → `Colon 1` → `gap` → `Card 2` → `gap` → `Colon 2` → `gap` → `Card 3`). Re-balanced digit font scaling ratio to 0.62× to prevent digit clipping on side notches and center fold creases.
  - **Console Font Size Warning:** Eliminated `QFont::setPointSize: Point size <= 0 (-1)` by replacing item-level font overrides on `QTableWidgetItem` with stylesheet-level table font rules (`QTableWidget { font-size: 13px; }`) in `history_dialog.py` and `schedule_screen_widget.py`.
  - **History UI Polishing:** Prevented label wrapping in `ALL-TIME TOTAL` telemetry card.
- [x] **Verification & Test Suite:**
  - Added dedicated unit test suite in [`tests/test_sound_manager.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_sound_manager.py) covering WAV format, synthesis, playback, settings toggling, and dialog button invocation.
  - **100% test pass rate:** **55/55 passing unit tests** across all 10 test suites.
  - Refreshed screenshots in `docs/screens/`: [`settings.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/settings.png), [`history.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/history.png), [`main_with_hover.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/main_with_hover.png), and `main_no_hover.png`.

---

### Milestone 9: Timetable Portability (Import & Export) `[COMPLETED]`
- [x] **Core Serialization & Portability Engine ([`timetable_portability.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/timetable_portability.py)):**
  - **Structured JSON Export & Import:**
    - Exports weekly class schedule matching official `docs/example.json` schema (`sessions: [...]`) with timestamp and session count metadata.
    - Full schema validation on import with descriptive warnings for malformed entries.
  - **RFC 4180 CSV Export & Import:**
    - Standard tabular format: `Day,Start,End,Subject,Core,Location`.
    - Encoded with UTF-8 BOM (`utf-8-sig`) so Excel and spreadsheet viewers display French accents without character mojibake.
    - Automatic delimiter sniffing: supports both comma (`,`) and French semicolon (`;`) delimited files.
    - Flexible header detection supporting both French (`Jour`, `Début`, `Fin`, `Matière`, `Salle`) and English (`Day`, `Start`, `End`, `Subject`, `Location`).
  - **Direct PDF Schedule Extraction:**
    - Pure Python PDF text extraction powered by `pypdf`.
    - Parses university grid timetables (matching `docs/grid.pdf`), extracting day blocks, course formats (`TP`, `COURS`, `TD`, `CI`), clean subject names, and rooms.
  - **Collision Detection & Duplicate Prevention:**
    - Deterministic time-overlap detection on identical weekdays:
      $$\text{Overlap} \iff (\text{start}_1 < \text{end}_2) \land (\text{start}_2 < \text{end}_1)$$
    - Duplicate-safe merging: ignores identical recurring sessions while adding new classes.
    - Support for both **Replace Schedule** (clean overwrite) and **Merge Schedule** (keep current, add new) modes.
- [x] **Timetable Portability Modal ([`ImportExportDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/import_export_dialog.py)):**
  - Designed in obsidian minimal aesthetic (`#121215` canvas, `#27272A` borders) with dark scrim backdrop overlay:
    - **Export Card:** Displays current class count, with 1-click `[ Export JSON ]` and `[ Export CSV ]` triggers.
    - **Import Card:** File picker supporting `.json`, `.csv`, `.pdf` files.
    - Pre-import validation preview showing detected session count, warnings, and an amber collision warning banner (`⚠️ X time overlap(s) detected`).
    - Radio toggles for `Replace current schedule` vs `Merge and add new classes`.
- [x] **UI & Screen Navigation Integration:**
  - Added `[ ⇄ Import / Export ]` button in the top navigation bar of [`ScheduleScreenWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/schedule_screen_widget.py#L364-L370).
  - Added `[ Import / Export ]` action in the `STUDY MANAGEMENT` section of [`CustomizationDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/customization_dialog.py).
  - Added global keyboard shortcut: <kbd>I</kbd> in Dashboard and Weekly Schedule screens opens the portability modal.
  - Live synchronization: imported sessions immediately update the active calendar grid, editor table, and ambient subject dashboard without app restart.
- [x] **Verification & Test Suite:**
  - Added comprehensive test suite in [`tests/test_timetable_portability.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_timetable_portability.py) (9 tests) covering JSON round-trips, CSV round-trips, French semicolon CSVs, collisions, duplicates, PDF parsing with `docs/grid.pdf`, engine integration, and dialog workflows.
  - **100% test pass rate:** **64/64 passing unit tests** across all 11 test suites.
  - Screenshots updated and verified: [`docs/screens/import_export.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/import_export.png) and [`docs/screens/grid_schedual.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/grid_schedual.png).

---

## Next Steps Roadmap: Academic Preparation & Nightly Desk Station

Based on the architectural pivot documented in [`docs/ACADEMIC_PREPARATION_SPEC.md`](file:///c:/Users/marj/Music/Study%20Station/docs/ACADEMIC_PREPARATION_SPEC.md):

### Milestone 10: Academic Todo Engine & Schema `[COMPLETED]`
- [x] Implemented `StudyTodo` dataclass in [`src/study_station/core/models.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/models.py) with `id`, `subject_name`, `title`, `notes`, `due_date`, `status`, `confidence`, `next_class_question`, `session_ref_id`, `is_completed`, `is_overdue`, and `is_due_soon`.
- [x] Updated `StudyLog` model to accept optional `todo_id: str | None` for task-level time attribution.
- [x] Expanded `SubjectSummary` to include `pending_todos_count` and `questions_count`.
- [x] Created `study_todos` table and indexes (`idx_study_todos_subject`, `idx_study_todos_status`, `idx_study_todos_due`) with automatic schema migration in [`src/study_station/persistence/database.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/persistence/database.py).
- [x] Added `todo_id` column migration to existing `study_logs` tables in SQLite.
- [x] Implemented full CRUD and query operations in [`StudyStationRepository`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/persistence/repository.py): `add_todo`, `update_todo`, `delete_todo`, `get_todo_by_id`, `get_all_todos`, `get_todos_by_subject`, `get_pending_todos`, `mark_todo_completed`, `get_questions_by_subject`.
- [x] Integrated Todo operations and queries into [`ScheduleEngine`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/engine.py): `add_todo`, `update_todo`, `delete_todo`, `mark_todo_completed`, `get_todos`, `get_pending_todos`, `get_todos_due_before`, `get_subject_pending_todos_count`, `get_subject_questions`, and `get_next_class_deadline_for_subject`.
- [x] Added dedicated unit test suite in [`tests/test_todo_engine.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_todo_engine.py).
- [x] **100% test pass rate:** **74/74 unit tests passing** across 12 test suites.

### Milestone 11: Nightly Desk Debrief & Questionnaire `[COMPLETED]`
- [x] Built [`DebriefDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/debrief_dialog.py) auto-populated with today's attended classes via `ScheduleEngine.get_day_sessions()`.
- [x] Built focused stepper workflow: steps through today's attended subjects one-by-one to minimize cognitive fatigue at night.
- [x] Integrated quick-category template buttons (`💻 Lab Fix`, `📖 Slides`, `📝 TD Problem`, `🎯 Exam Prep`, `🚀 Project`).
- [x] Automatic deadline resolution: calculates next occurrence start datetime via `get_next_class_deadline_for_subject()`, with an optional custom date picker.
- [x] Support for adding multiple tasks per subject (`+ Add Another Task`) and skipping subjects (`Skip Subject`).
- [x] Free study day fallback: gracefully handles days with no scheduled classes by offering subject selection from enrolled modules.
- [x] Connected to [`MainWindow`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/main_window.py): added dedicated keyboard shortcut <kbd>D</kbd> and top bar `[ Debrief ]` button.
- [x] Added dedicated unit test suite in [`tests/test_debrief_dialog.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_debrief_dialog.py).
- [x] **100% test pass rate:** **80/80 unit tests passing** across 13 test suites.

### Milestone 12: Grid as Main Station (Academic Cockpit) `[COMPLETED]`
- [x] Set `ScheduleScreenWidget` as the primary default main station view (`INDEX_GRID = 0`, `INDEX_DASHBOARD = 0` alias).
- [x] Transformed Ambient Split-Flap Clock into a dedicated screensaver mode (`INDEX_AMBIENT_CLOCK = 3`), accessible via top-bar `[ ⏱ Clock Station ]` button or keyboard shortcuts <kbd>C</kbd> / <kbd>A</kbd>.
- [x] Added `[ ⚡ Debrief Today ]` button in the Weekly Schedule top bar connecting directly to `DebriefDialog`.
- [x] Dynamic preparation badge rendering on `ClassGridCard`:
  - `● X DUE` (amber/red) when pending tasks are overdue or due before next session (< 24h).
  - `● X TODO` (slate blue) when pending tasks exist.
  - `✓ READY` (emerald) when all tasks for that subject are completed.
  - `❓ X` (sky blue) when in-class questions have been formulated.
- [x] Built [`SubjectPreparationSheet`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/subject_preparation_sheet.py) drawer dialog:
  - Subject header with core badge and room number.
  - Next class occurrence countdown (`NEXT CLASS: Thursday at 08:00 (in 3 days)`).
  - Preparation tasks checklist with inline check-offs.
  - 1-click focus launcher tethered to that task (`▶ 15m`).
  - Quick inline task addition with automatic next-class deadline calculation.
  - Direct access to class time/room timetable editor via `ClassSessionDialog`.
- [x] Updated `MainWindow` focus loop to track `_active_todo` and attribute focus sessions to `StudyLog.todo_id`.
- [x] Added dedicated unit test suite in [`tests/test_grid_main_screen.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_grid_main_screen.py) (4 tests).
- [x] **100% test pass rate:** **84/84 unit tests passing** across 14 test suites.

### Milestone 13: Todo-Driven Focus Loop & Cognitive Exit Ticket `[COMPLETED]`
- [x] Defined `ExitTicketResult` dataclass in [`src/study_station/core/models.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/models.py).
- [x] Updated [`FocusWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/focus_widget.py) to accept active `StudyTodo` alongside the subject name:
  - Displays actionable task title in slate cyan badge (`Task: Fix Star Schema join exercise`).
  - Displays relative/calendar deadline context underneath radial ring gauge (`Due: Thursday, Oct 22 at 09:40`).
- [x] Built [`ExitTicketDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/exit_ticket_dialog.py):
  - **Completion Prompt**: `[ ✓ Complete Task ]` (marks todo finished), `[ +10m Need More Time ]` (continuation sprint), `[ ⏸ Put Aside for Later ]` (keeps task pending with saved progress).
  - **Cognitive Confidence Rating**: Traffic-light pill buttons with distinct color coding:
    - `🔴 Foggy / Stuck` (`#451A1A` / `#F87171`)
    - `🟡 Getting There` (`#451A03` / `#FCD34D`)
    - `🟢 Solid` (`#064E3B` / `#34D399`)
  - **In-Class Question Formulation**: Formulate 1 question for next lecture, automatically pinned to next class card (`❓ X` badge).
  - **1-Sentence Feynman Takeaway**: Concise one-sentence summary saved to task notes.
- [x] Updated [`CompletionWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/completion_widget.py) to display task title and confidence badge.
- [x] Wired seamless execution flow in [`MainWindow`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/main_window.py):
  - Automatically prompts `ExitTicketDialog` on timer completion or session finish.
  - Automatically handles `+10m` continuation sprint without losing already completed focus minutes.
  - Attributes focus minutes to `StudyLog.todo_id` in SQLite.
- [x] Added dedicated unit test suite in [`tests/test_exit_ticket.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_exit_ticket.py) (6 tests).
- [x] **100% test pass rate:** **90/90 unit tests passing** across 15 test suites.

### Milestone 14: Night Routine Ambient UX & In-Class Payoff `[COMPLETED]`
- [x] **Evening Desk Mode & Debrief Decision Engine**:
  - Implemented `should_prompt_nightly_debrief(current_dt)` in `ScheduleEngine`: checks for evening desk hours (after 18:00 local time), verifies that classes were scheduled/attended today, and confirms that today has not yet been debriefed.
  - Implemented debrief persistence in `StudyStationRepository` and `ScheduleEngine`: `mark_day_debriefed(ref_date)` and `is_day_debriefed(ref_date)` tracking completion in SQLite `app_settings`.
- [x] **Prominent Cockpit Ambient Debrief Banner**:
  - Built `debrief_banner` in [`ScheduleScreenWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/schedule_screen_widget.py) positioned prominently at the top of the Weekly Schedule Cockpit.
  - Shows clear, actionable prompt: `🌙 EVENING DESK ROUTINE · Nightly Debrief Ready` with `[ ⚡ Start Debrief ]` quick launch and dismiss `[ ✕ ]` button.
  - Automatically hidden once debrief is marked completed or dismissed for the session.
- [x] **Tonight's Priority Task Hero Capsule & 1-Click Focus**:
  - Implemented `get_priority_study_todo(current_dt)` in `ScheduleEngine` with deterministic academic urgency ranking (overdue tasks prioritized first, followed by nearest upcoming due date).
  - Built `priority_task_card` in `ScheduleScreenWidget` rendering:
    - Glowing indigo badge: `TONIGHT'S PRIORITY FOCUS`.
    - Active subject and task title: e.g. `Sécurité logicielle · Complete buffer overflow exploitation exercise`.
    - Due context: `Due before next class: Fri, Oct 16 at 09:09` (or red `⚠️ OVERDUE` callout).
    - 1-click focus start button: `[ ▶ 15m Focus ]` directly initiating a task-tethered sprint via `start_todo_focus_requested`.
- [x] **In-Class HUD & Question Resolution Payoff**:
  - Enhanced `ClassGridCard` to display prominent glowing badge `❓ ASK IN CLASS (X)` when the session is currently in progress (`is_current=True`) and has formulated questions.
  - Expanded [`SubjectPreparationSheet`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/subject_preparation_sheet.py) with dedicated `IN-CLASS PAYOFF: QUESTIONS TO ASK PROFESSOR` section:
    - Lists all questions formulated during nightly exit tickets for that course.
    - `[ 📋 Copy ]` button to instantly copy the question to system clipboard.
    - `[ ✓ Asked ]` button to immediately resolve the question in SQLite and live memory, clearing the badge from the cockpit grid.
  - Added `resolve_subject_question` in `ScheduleEngine` and `clear_subject_question` in `StudyStationRepository`.
- [x] **Automated Screen Capture Refresh**:
  - Created [`scripts/capture_screens.py`](file:///c:/Users/marj/Music/Study%20Station/scripts/capture_screens.py) to programmatically render and capture high-resolution screenshots with real academic subjects and state models:
    - [`grid_schedual.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/grid_schedual.png): Cockpit grid with Evening Debrief banner, Tonight's Priority Task card, and live preparation badges.
    - [`debrief_modal.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/debrief_modal.png): Multi-step nightly debrief check-in wizard.
    - [`exit_ticket.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/exit_ticket.png): Cognitive exit ticket modal with traffic-light confidence and next-class question input.
    - [`preparation_sheet.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/preparation_sheet.png): Subject preparation sheet showing tasks checklist and in-class question resolution buttons.
    - [`focus.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/focus.png): Task-tethered focus countdown ring with due date context.
- [x] **Verification & Test Suite**:
  - Added dedicated unit test suite in [`tests/test_night_routine_hud.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_night_routine_hud.py) (6 tests) covering prompt logic, debrief persistence, priority task ranking, question resolution, banner dismissals, and in-class card HUD badges.
  - **100% test pass rate:** **96/96 unit tests passing** across 16 test suites.

### Milestone 15: Academic Task Backlog & Comprehensive Todo CRUD `[COMPLETED]`
- [x] **Full Task Lifecycle & Reversible Check-offs**:
  - Implemented `mark_todo_pending(todo_id)` in [`StudyStationRepository`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/persistence/repository.py) and [`ScheduleEngine`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/engine.py), enabling completed tasks to be unchecked/reopened.
- [x] **Individual Task Edit & Create Modal ([`EditTodoDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/edit_todo_dialog.py))**:
  - Dual-mode modal supporting both creating new tasks and editing existing tasks.
  - Actionable title and context notes editing.
  - Subject selector dropdown (enrolled subjects + free-form typing).
  - Due date selector with quick presets (`Next Class`, `Tomorrow`, `+3 Days`, `+1 Wk`, and calendar popup).
  - Status toggle (`Pending` vs `Completed`).
  - Next-class formulated question viewing and editing.
  - Safe task deletion with `QMessageBox` confirmation.
- [x] **Centralized Academic Task Backlog ([`TasksDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/tasks_dialog.py))**:
  - Accessible via top navigation bar `[ ✓ Tasks ]` or dedicated keyboard shortcut <kbd>T</kbd>.
  - **KPI Telemetry Cards**: Real-time counts for `TOTAL PENDING`, `DUE THIS WEEK`, `OVERDUE`, and `COMPLETED`.
  - **Multi-Criteria Filter Bar**:
    - Live search box filtering by title, notes, and course.
    - Subject dropdown (`All Subjects` + distinct courses).
    - Status segmented filter pills (`All`, `Pending`, `Due Soon (<24h)`, `Overdue`, `Completed`).
  - **Task Row Actions**:
    - Reversible completion checkbox.
    - Subject module pill badge (`[ENTREPÔTS]`, `[DATA VIS]`).
    - Relative due date badges with dynamic color coding (`⚠️ OVERDUE`, `● Due Soon`, `Due: Thu, Oct 22`).
    - 1-click focus launcher pill `[ ▶ 15m ]` directly engaging a task-tethered focus sprint.
    - In-place `[ ✏ ]` Edit button opening `EditTodoDialog`.
    - In-place `[ ✕ ]` Delete button with confirmation.
- [x] **In-Place Drawer CRUD in [`SubjectPreparationSheet`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/subject_preparation_sheet.py)**:
  - Enabled reversible check-offs on all task items.
  - Added `[ ✏ ]` and `[ ✕ ]` buttons on every preparation task row.
  - Added `todo_changed` signal triggering automatic real-time updates of cockpit grid badges (`● X TODO`, `● X DUE`, `✓ READY`) and tonight's priority task card.
- [x] **Top Navigation & Keyboard Shortcuts**:
  - Added `[ ✓ Tasks ]` button to the `ScheduleScreenWidget` top header.
  - Added `[ Tasks ]` button to the `SubjectDashboardWidget` top navigation bar.
  - Connected global keyboard shortcut <kbd>T</kbd> in `MainWindow` for instant backlog access.
- [x] **Verification & Test Suite**:
  - Added dedicated unit test suite in [`tests/test_tasks_dialog.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_tasks_dialog.py) (12 tests) covering KPI calculations, subject filters, status filters, search filters, completion toggling, 1-click focus signals, EditTodoDialog save/update/delete, and SubjectPreparationSheet in-place CRUD.
  - **100% test pass rate:** **108/108 unit tests passing** across 17 test suites.
### Milestone 15.5: Runtime Stability, Academic Task Backlog Overhaul & Upcoming Class Resolution `[COMPLETED]`
- [x] **Runtime Stability & Signal Lifecycle Fix**:
  - Eliminated `RuntimeError: Signal source has been deleted` by removing legacy unhandled signal `clicked_session` and wrapping `_open_session_manager` execution in `QTimer.singleShot(0, ...)` in [`ScheduleScreenWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/schedule_screen_widget.py).
  - Fixed `QFont::setPointSize: Point size <= 0 (-1)` Qt font evaluation warning by switching `get_modern_font()` in [`theme.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/theme.py) from `font.setPixelSize()` to `font.setPointSize()`.
- [x] **Upcoming Class Calculation & Timeline Architecture**:
  - **Accent & Spelling Normalization**: Fixed accent variance (`accées` vs `accès`, `controle` vs `contrôle`) across `get_next_occurrence_of_subject`, `get_active_cycle`, `get_subject_summary`, `get_todos`, and `get_distinct_subjects` in [`ScheduleEngine`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/engine.py), ensuring next occurrences always resolve cleanly regardless of formatting.
  - **Weekend Boundary Lookahead**: Expanded lookahead to 3 weeks (`week_offset in (0, 1, 2)`) to eliminate weekend boundary disconnects (e.g. from Friday evening to next Monday morning).
  - **Robust Day Index Map**: Upgraded `DAY_INDEX_MAP` in [`models.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/core/models.py) to support case-insensitive full, short, French, and English day names (`lun`, `lundi`, `mon`, `monday`, etc.).
  - **Timeline Strip Polish**: Refined dashboard timeline strip to cleanly format today's active schedule and next session indicators.
- [x] **Academic Task Backlog Overhaul ([`TasksDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/tasks_dialog.py))**:
  - **Header Telemetry Pill**: Added real-time badge (`● N PENDING` or `✓ ALL CAUGHT UP`) in the modal title bar.
  - **Tonight's Priority Focus Hero Banner**: Built highlighted priority banner at the top of the backlog featuring active subject, deliverable title, relative due date, and 1-click sprint launchers (`[ ▶ 15m Focus ]` and `[ 25m ]`).
  - **Status Pill Live Counters**: Dynamic counts on all filter pills (`All (3)`, `Pending (2)`, `Due Soon (1)`, `Overdue (0)`, `Completed (1)`).
  - **Intelligent Human Due Dates**: Replaced raw ISO dates with relative formatting (`⚠️ OVERDUE by 3h`, `● Due Today at 18:00`, `● Due Tomorrow at 09:40`, `Due in 3 days`).
  - **1-Click Quick-Add Presets**: Interactive empty state with 4 common academic deliverables (`+ Prepare Next Class Notes`, `+ Complete Lab Exercise`, `+ Review Lecture Slides`, `+ Exam Revision Sprint`) opening `EditTodoDialog` pre-filled.
  - **Search Box Instant Clear**: Quick `✕` button to instantly reset filters.
  - **Core Badge Color Coding**: Module badges colored by core type (TP: Emerald, Cours: Slate, TD: Indigo, CI: Amber).
  - **Keyboard Ergonomics**: <kbd>/</kbd> to focus search filter, <kbd>N</kbd> or <kbd>Ctrl+N</kbd> to create a new task, <kbd>Esc</kbd> to dismiss.
- [x] **Verification & Test Suite**:
  - **113/113 unit tests passing** across 17 test suites (added 5 new tests covering priority banners, search clearing, relative due date formatting, and spelling-invariant upcoming sessions).
  - Re-captured all high-resolution UI screenshots: [`docs/screens/tasks_modal.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/tasks_modal.png) and [`docs/screens/preparation_sheet.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/preparation_sheet.png).

---

### Milestone 16: UI Professionalization, Customization Engine & Academic Sprint Launchpad `[COMPLETED]`
- [x] **Split-Flap Mechanical Flip Clock Overhaul (`SplitFlapClockWidget`)**:
  - Rescaled card dimensions to 160×138px (300×168px default / 454×168px with seconds) with authentic desktop flip-card proportions.
  - Implemented authentic horizontal split crease with lighting depth and subtle gradient shadows.
  - Added authentic drum cutouts with center pivot pins along outer card edges.
  - Upgraded typography from retro/decorative serif to crisp, ultra-legible modern sans-serif (`sans`).
  - Removed colon (`:`) separator between flap cards to create a unified, minimalist mechanical clock aesthetic.
- [x] **Class Session Management Optimization (`ScheduleScreenWidget`)**:
  - Eliminated cramped inline add inputs from the Edit Classes view, reclaiming 100% vertical space for the sessions table.
  - Unified session additions and modifications through the modal `ClassSessionDialog`, eliminating layout overflow on 1366×768 displays.
  - Retained headless backwards-compatible attributes on `ScheduleScreenWidget` preserving 100% test pass rate.
- [x] **Dynamic UI Customization Engine (`CustomizationDialog` & `AppSettings`)**:
  - Expanded `AppSettings` with customizable `accent_color: str = "#10B981"` and `bg_color: str = "#09090B"` with SQLite persistence.
  - Added curated theme color palettes (`PRESET_ACCENTS`: Emerald, Electric Cyan, Violet, Amber, Coral, Minimal White; `PRESET_BACKGROUNDS`: Midnight Noir, Deep Slate, Espresso, Void Black).
  - Designed interactive color swatches with active selection indicator rings, native `QColorDialog` custom hex color picker, and dark background scrim.
  - Real-time live propagation of accents and background canvas colors across `MainWindow`, split-flap cards, hero banners, progress bars, and schedule views.
- [x] **Active Academic Sprint Launchpad (`SubjectDashboardWidget`)**:
  - **Stylish Date Pill Badge (`lbl_date`)**: Positioned directly above the split-flap clock featuring dynamic theme accent weekday, separator bullet, and crisp off-white month & day (`THURSDAY • OCTOBER 15`).
  - **Clean Centered Composition**: Removed the bottom schedule strip from the layout, creating a perfectly balanced, distraction-free vertical composition on 1366×768 displays.
  - **Urgent Deadline Kicker Badge (`lbl_task_kicker`)**: Displays relative deadline proximity (e.g. `🎯 PRIORITY TASK · DUE IN 14h` or `⚠ OVERDUE · WAS DUE 2h AGO`).
  - **Actionable Task Headline (`lbl_task_title`)**: High-legibility 22px bold modern sans-serif headline displaying the concrete task (e.g. `Complete buffer overflow exploitation exercise`), with 740px layout width to prevent clipping, and 1-click access to the task backlog.
  - **1-Click Sprint Launchers**:
    - `▶ START 15m SPRINT`: 1-click micro-sprint directly tethered to the active task.
    - `25m POMODORO`: Standard 25-minute Pomodoro study block.
    - `TASKS`: Quick button to open the Academic Task Backlog modal.
  - **Cognitive Exit Ticket Tethering**: Emits `start_todo_focus_requested` to `MainWindow`, ensuring the session completion ticket evaluates progress on that exact task upon timer completion.
  - **Ambient Inactivity Auto-Hide**: Peaceful idle glance mode hiding controls after 3.5s; instantly reveals navigation and sprint buttons on mouse movement or interaction.
- [x] **Verification & Test Suite**:
  - **114/114 unit tests passing** (100% pass rate) across all 17 test suites.
  - Regenerated and verified all high-resolution documentation screenshots in both `docs/screens/` and `docs/SCREENSS/`.

---

### Milestone 17: Multi-User Profile Architecture, Zero-Password Database Isolation & Clean Slate Options `[COMPLETED]`
- [x] **Lightweight User & Profile Manager (`UserManager`)**:
  - Built `UserManager` in [`src/study_station/persistence/user_manager.py`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/persistence/user_manager.py).
  - Maintains `profiles.json` tracking registered user profiles and active user.
  - **100% Backward Compatibility**: Legacy `studystation.db` is automatically mapped as the `"Default"` user profile so existing student records, tasks, and settings are never lost.
  - Separate database files per user: `%APPDATA%/study_station/users/{username}.db`.
  - Robust username filesystem sanitization (`sanitize_username`).
- [x] **Frictionless Kiosk User Switch Dialog (`UserSwitchDialog`)**:
  - Designed and built [`UserSwitchDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/user_switch_dialog.py) and [`UserProfileCard`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/user_switch_dialog.py#L30-L128).
  - Modern obsidian aesthetic matching the kiosk dark design system.
  - Emerald `● ACTIVE` badge for the current profile.
  - 1-click user switching (`Switch` button or clicking the card).
  - Safe deletion for secondary profiles with confirmation modal.
  - Inline input field to create a new user profile with `[ + Create & Switch ]` button.
  - **Explicit Clean Slate vs Template Choice**:
    - **Start empty (clean schedule & tasks)** (Default): Newly created users start with a completely empty schedule and empty task backlog.
    - **Load sample timetable template**: Optional choice for students wanting the pre-loaded university timetable.
- [x] **Live State Switching & Zero-Restart Persistence (`MainWindow`)**:
  - Integrated `switch_user(new_username, load_sample=False)` in [`MainWindow`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/main_window.py):
    - Safely pauses/persists any active focus timer to prevent lost effort.
    - Closes previous SQLite connection.
    - Connects to target user's SQLite database.
    - Only seeds timetable if `load_sample=True` is explicitly chosen; otherwise provides a pure clean slate.
    - Re-instantiates `StudyStationRepository` and `ScheduleEngine`.
    - Reloads user appearance settings (`AppSettings`) and updates window palette.
    - Dynamically refreshes Weekly Schedule Cockpit, Flip Clock launchpad, and task backlogs.
- [x] **On-Demand "Empty Schedule" & "Empty Tasks" Actions**:
  - **Empty Schedule**: Added `[ 🗑 Empty Schedule ]` button in [`ScheduleScreenWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/schedule_screen_widget.py) class editor toolbar with confirmation modal, clearing all scheduled sessions from repository and updating the calendar grid.
  - **Dynamic Empty Schedule Hint**: Weekly schedule header displays `"Schedule is empty · Click any '+' slot to add a class, or use Import / Export"` when 0 classes exist.
  - **Empty Tasks**: Added `[ Empty Tasks ]` button in [`TasksDialog`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/tasks_dialog.py) backlog header with confirmation modal, allowing students to clear all deliverables on demand.
- [x] **Top Navigation & Keyboard Ergonomics**:
  - Added `[ 👤 {Username} ]` button in the top navigation bar of [`ScheduleScreenWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/schedule_screen_widget.py).
  - Added `[ 👤 {Username} ]` button in the auto-revealing navigation bar of [`SubjectDashboardWidget`](file:///c:/Users/marj/Music/Study%20Station/src/study_station/ui/dashboard_widget.py).
  - Connected global keyboard shortcut <kbd>U</kbd> in `MainWindow` for instant modal access from both grid and clock screens.
- [x] **Verification & Test Suite**:
  - Added dedicated unit test suite in [`tests/test_multi_user.py`](file:///c:/Users/marj/Music/Study%20Station/tests/test_multi_user.py) covering user initialization, path isolation, separate todo databases, clean slate vs sample template choices, empty schedule clearing, and empty tasks clearing.
  - **100% test pass rate:** **129/129 unit tests passing** (up from 114).
  - Generated and verified high-resolution screenshots in [`docs/screens/switch_user_modal.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/switch_user_modal.png), [`docs/screens/editSchedual.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/editSchedual.png), and [`docs/screens/tasks_modal.png`](file:///c:/Users/marj/Music/Study%20Station/docs/screens/tasks_modal.png).

---

### Milestone 18: Immediate UX Polish & Anti-Fatigue Workflows (Tier 1 Roadmap) `[COMPLETED]`
- [x] **Settings & Customization Dialog Layout Overhaul (`CustomizationDialog`)**:
  - Resized dialog container to 510×740px to eliminate vertical clipping of the Study Management section.
  - Tightened content spacing and divider heights; styled scrollbar with smooth background track.
  - Sized `[ Done ]` button to 140×32px with dedicated top margin, preventing overlap with controls.
- [x] **Cognitive Exit Ticket Anti-Fatigue Adaptive Workflow (`ExitTicketDialog`)**:
  - **Instant Continuation Sprint**: Clicking `[ +10m Need More Time ]` adaptively collapses questions 3 & 4 and updates save trigger to `[ ▶ Resume +10m Focus ]`.
  - **Adaptive Question Revelation**: If `🟢 Solid` confidence is chosen, Question 3 ("Formulate Question for Professor") is automatically hidden unless existing question text is present, cutting questionnaire cognitive fatigue by over 50%.
  - When `🔴 Foggy` is selected, Question 3 expands prominently with an amber/red reminder banner.
  - Renamed bottom dismiss action from ambiguous `Skip Debrief` to `Skip Ticket`.
- [x] **Weekly Schedule Cockpit 3-Cluster Top-Bar Architecture (`ScheduleScreenWidget`)**:
  - Organized previously crowded 9-item top bar into 3 balanced visual clusters:
    - **Left Cluster (Identity & Rituals):** `[ 👤 {Username} ]`, `[ ⚡ Debrief ]`, `[ ✓ Tasks ]`.
    - **Center Cluster (Academic Calendar):** `WEEKLY SCHEDULE` + `[ ‹ ]  12 – 17 OCT 2026  [ › ]  [ Today ]`.
    - **Right Cluster (Station Views & Tools):** `[ ⏱ Clock ]`, `[ Grid View | Edit Classes ]`, `[ ⇄ Import / Export ]`, `[ PDF ]`.
  - Stretched layout spacers between clusters preventing horizontal squeeze on 1366×768 displays.
- [x] **Dismissible Priority Task Capsule (`ScheduleScreenWidget`)**:
  - Added discrete `[ ✕ ]` dismiss button to `priority_task_card` and implemented `_dismiss_priority_card()` allowing students to easily reclaim full 768p vertical height for afternoon class rows on demand.
- [x] **Positive Target Framing on Ambient Flip Clock (`SubjectDashboardWidget`)**:
  - Eliminated guilt-inducing `● 0 / 60 MIN COMPLETED · 0%` when 0 minutes are logged.
  - Formatted 0-minute state as `🎯 {tgt} MIN TARGET · READY TO FOCUS`.
- [x] **High-Contrast Abort Button & Clean Due Date Context**:
  - Upgraded `BUTTON_DANGER_STYLE` in `theme.py` to `#201315` container with `#5C1D24` border and `#FCA5A5` text.
  - Filtered off-hour midnight minutes in `FocusWidget` (`Due: Sun, Oct 18` instead of `at 00:05`).
- [x] **Typo Normalization & Documentation Sync**:
  - Renamed screenshot outputs to `grid_schedule.png` and `edit_schedule.png` with backwards-compatible aliases.
  - Synchronized `README.md` test counter badge and summary to 129/129 tests passing.
  - Documented full 3-tier roadmap in [`docs/ROADMAP_TIERS.md`](docs/ROADMAP_TIERS.md).

### Milestone 19: Academic Urgency Engine, Backlog Sorting & Special Period Overrides (Tier 2 Roadmap) `[COMPLETED]`
- [x] **Tomorrow-Morning Class Proximity Bias (`ScheduleEngine`)**:
  - Implemented `calculate_todo_urgency_score(todo, current_dt)` prioritizing overdue tasks (score >= 100,000) and tasks due for tomorrow morning's earliest lectures over distant deadlines.
  - Formula dynamically integrates due date urgency and next class proximity ($Score = \frac{1000}{\Delta t_{due} + 1} + \frac{2500}{\Delta t_{class} + 1}$).
  - Upgraded `get_priority_study_todo` to automatically rank by urgency score descending.
- [x] **Special Academic Overrides Engine & Persistence (`SpecialPeriod`)**:
  - Created `SpecialPeriod` dataclass modeling override periods (`1 Day`, `3 Days`, `1 Week`, `2 Weeks`, custom) covering Exams/DS, Revision/Dead weeks, Intensive Project Sprints, and Breaks.
  - Added `special_periods` SQLite table with index on date ranges and full CRUD in `StudyStationRepository`.
  - Added `get_special_period_for_date`, `get_special_periods_for_week`, `is_schedule_overridden` in `ScheduleEngine`.
- [x] **Academic Period Overrides Modal (`SpecialPeriodDialog`)**:
  - Developed `SpecialPeriodDialog` with 1-click presets (`1 Day`, `3 Days`, `1 Week`, `2 Weeks`), period type selector, date range pickers with live duration label (`Duration: 1 Week`), and scheduled periods management list.
- [x] **Weekly Schedule Screen Cockpit Integration (`ScheduleScreenWidget`)**:
  - Added `[ ⚡ Period Mode ]` / `[ ⚡ 1 WEEK: Devoirs Surveillés ]` trigger button in top bar view tools.
  - Added prominent `⚡ SPECIAL ACADEMIC PERIOD ACTIVE` banner above calendar grid with `[ Manage Periods ]` and `[ ✕ ]`.
  - Highlighted calendar day headers (`LUN [ ⚡ EXAM ] 12 OCT`) and session cards (`[ ⚡ OVERRIDDEN ]`) with amber override styling when active.
- [x] **Multi-Criteria Backlog Sorting & Safe Actions (`TasksDialog`)**:
  - Added Sort dropdown: `Sort: Deadline (Earliest)`, `Sort: Academic Urgency`, `Sort: Subject (A–Z)`, `Sort: Title (A–Z)`.
  - Relocated nuclear `[ Empty Tasks ]` button out of the primary header to a guarded footer utility action (`🗑 Clear All Tasks...`) with safe confirmation.
- [x] **Debrief Wizard Active Template Highlights (`DebriefDialog`)**:
  - Added dynamic active template pill highlights with emerald border (`#10B981`) and glowing background.
- [x] **Verification & Test Telemetry**:
  - 141/141 tests passing across 19 test suites with 100% pass rate.
  - Added dedicated test suite `tests/test_tier2_special_periods.py` covering model, persistence, urgency heuristic, sorting, and UI presets.
  - Re-captured and verified all 14 documentation screenshots in `docs/screens/` and `docs/SCREENSS/`.

---

## Complete Academic Station Milestone Summary

Study Station is fully realized across 22 comprehensive development milestones:
1. **Milestone 1: Project Foundation & Screen Framework** `[COMPLETED]` — Window lifecycle, fullscreen, Linux X11/Xfce support.
2. **Milestone 2: Ambient Flip Clock & Schedule Engine** `[COMPLETED]` — Retro minimal typography, ScheduleEngine timetable parsing.
3. **Milestone 2.5: Modern UI Redesign & Calm Discipline** `[COMPLETED]` — 3D flip card animations, auto-hiding action bars.
4. **Milestone 3: Focus Timer & Completion Screens** `[COMPLETED]` — Focus timer engine, micro-durations, celebration feedback.
5. **Milestone 4: Local Persistence & State Recovery** `[COMPLETED]` — SQLite WAL database, crash/sleep recovery.
6. **Milestone 5: Secondary Screens** `[COMPLETED]` — Timetable editor, review targets, offline manual logger.
7. **Milestone 6: Subject-Centric UI Rework** `[COMPLETED]` — Subject summaries, hero subject card, carousel shelf.
8. **Milestone 6.5: Professional UI Polish** `[COMPLETED]` — Integrated split-station cockpit, upcoming timeline, modern QSS reset.
9. **Milestone 7: Study Logs & History** `[COMPLETED]` — Full session log viewer, filtering, summary stats.
10. **Milestone 8: Calibrated Sound Manager** `[COMPLETED]` — Synthesized acoustic harmonic completion chime.
11. **Milestone 9: Timetable Portability** `[COMPLETED]` — University PDF parsing, RFC 4180 CSV, JSON import/export.
12. **Milestone 10: Academic Todo Engine & Schema** `[COMPLETED]` — Granular task models, SQLite migrations, `StudyLog.todo_id` attribution.
13. **Milestone 11: Nightly Desk Debrief & Questionnaire** `[COMPLETED]` — Automatic evening check-in wizard with auto-deadlines.
14. **Milestone 12: Grid as Main Station (Academic Cockpit)** `[COMPLETED]` — Weekly calendar grid as default home screen, live preparation badges.
15. **Milestone 13: Todo-Driven Focus Loop & Cognitive Exit Ticket** `[COMPLETED]` — Task-tethered focus gauge, traffic-light confidence ratings, continuation sprints.
16. **Milestone 14: Night Routine Ambient UX & In-Class Payoff** `[COMPLETED]` — Evening desk mode, prominent debrief banner, Tonight's Priority Task capsule.
17. **Milestone 15: Academic Task Backlog & Comprehensive CRUD** `[COMPLETED]` — Central backlog (<kbd>T</kbd>), EditTodoDialog, reversible check-offs.
18. **Milestone 15.5: Runtime Stability & Backlog Polish** `[COMPLETED]` — Signal lifecycle stability, font sizing evaluation, upcoming class calculations.
19. **Milestone 16: UI Professionalization, Customization Engine & Academic Sprint Launchpad** `[COMPLETED]` — Mechanical clock overhaul, dynamic UI themes, reclaimed session space, and active task sprint launcher.
20. **Milestone 17: Multi-User Profile Architecture, Zero-Password Database Isolation & Clean Slate Options** `[COMPLETED]` — Zero-password user switching, isolated SQLite databases, clean slate default with optional template loading, on-demand Empty Schedule & Empty Tasks actions, and top-bar switch button.
21. **Milestone 18: Immediate UX Polish & Anti-Fatigue Workflows (Tier 1 Roadmap)** `[COMPLETED]` — Top-bar clustering, adaptive exit ticket, priority dismiss, positive clock framing, and test telemetry sync.
22. **Milestone 19: Academic Urgency Engine, Backlog Sorting & Special Period Overrides (Tier 2 Roadmap)** `[COMPLETED]` — Tomorrow-morning proximity bias, backlog sorting, safe purge, and Special Academic Overrides (day/x days/weeks/x weeks).






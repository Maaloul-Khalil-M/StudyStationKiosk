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

## Next Steps Roadmap & Recommended Work

### Milestone 9: Timetable Portability (Import & Export) `[RECOMMENDED NEXT]`
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



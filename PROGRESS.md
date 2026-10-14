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

### Milestone 4: Local Persistence & State Recovery `[NEXT]`
- [ ] Local storage (SQLite or JSON files in user data directory) for:
  - Timetable data
  - Study logs (history of completed sessions)
  - Subject target overrides
  - Active timer state (for crash / restart recovery)
- [ ] Timetable validation and editable targets.

### Milestone 5: Secondary Screens (Qt Designer) `[PENDING]`
- [ ] Timetable viewer / editor dialog.
- [ ] Subject review target configuration dialog.
- [ ] Manual study time entry form (for offline study sessions).
- [ ] Preferences dialog (theme, default session length, 12/24h default).

---

## Key Decisions & Guiding Rules
1. **Time first:** Ambient clock is the visual centerpiece; study progress remains discreet.
2. **One question per screen:**
   - *Ambient Clock:* What time is it, and how am I progressing?
   - *Focus:* What am I working on right now?
   - *Completion:* Did my effort count?
3. **No guilt debt:** Unfinished review minutes do not accumulate as overdue debt across class cycles.
4. **Deterministic core:** Engine and timer logic remain pure and unit-testable independently of Qt UI.

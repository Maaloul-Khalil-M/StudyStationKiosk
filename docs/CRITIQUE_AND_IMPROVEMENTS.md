# Comprehensive Analysis & Critique: Current Progress & UI States

**Date:** October 15, 2026  
**Document Target:** Study Station — Post-Milestone 6.9 Review  
**Subject:** Visual audit of `docs/screens/`, UX analysis, and structural roadmap for essential improvements (Calendar with Dates, Schedule Management, Focus Ring Gauge, Spatial Balance).

---

## 1. Executive Summary & Core Assessment

Study Station has established a strong technical foundation: a clean PySide6 architecture, robust deterministic schedule engine, SQLite persistence with WAL mode and crash recovery, and 24/24 passing unit tests.

However, an audit of the current screen captures (`docs/screens/`) reveals that **the pendulum swung too far into extreme minimalism**, resulting in visual emptiness and critical functional gaps. Specifically:

1. **The "Calendar" is Not a Calendar:** The weekly grid displays abstract recurring day tokens (`LUN`, `MAR`, `MER`...) without real calendar dates, month context, or week navigation. Students live in dates (October 12–18), deadlines, holidays, and exam periods—not in timeless 2D matrices.
2. **Schedule Management is Awkward and Disconnected:** Changing the schedule forces the user out of the calendar grid into a raw, flat database table (`editSchedual.png`) with a cramped bottom input bar. There is no direct in-place editing, no slot-click creation, and no ability to handle date-specific schedule changes (cancelled classes, room changes, rescheduled slots).
3. **Focus Screen Lacks Presence & Physicality:** The focus timer is merely text digits over a flat horizontal line. It wastes the 1366×768 canvas and lacks the tactile, glanceable satisfaction of a physical study appliance. The user's proposal for a **Ring Gauge (radial arc timer)** is the exact missing link.
4. **The Ambient Screen Has a 60% Void:** The idle dashboard stacks elements in the upper-middle, leaving over half of the screen as pitch-black dead space. Furthermore, hiding the date in idle mode defeats the purpose of an ambient desk clock.

> **Strategic Recommendation:** Pause the planned future milestones (Milestones 7–10: statistics, audio, export) to **deeply refine the core appliance experience** (Milestones 2, 3, and 6) so that the day-to-day study workflow feels effortless, tactile, and indispensable.

---

## 2. In-Depth Visual & UX Critique of `docs/screens/`

### Screen 1: Ambient Station (`main_no_hover.png` & `main_with_hover.png`)

![Main No Hover](file:///c:/Users/marj/Music/Study%20Station/docs/screens/main_no_hover.png)
![Main With Hover](file:///c:/Users/marj/Music/Study%20Station/docs/screens/main_with_hover.png)

| Aspect | Current Observation | Critical Flaw & Impact | Required Improvement |
| :--- | :--- | :--- | :--- |
| **Spatial Composition** | Clock and subject sit in the upper-middle (y: 200–380px). Bottom 55–60% of the display is completely black void. | Looks like an unrendered or half-loaded webpage on a 1366×768 display. Feels empty rather than intentional. | Balance vertical distribution. Ground the bottom with an ambient hairline daily schedule strip or upcoming class timeline. |
| **Glanceability of Date** | Date header (`THURSDAY, OCT 15`) only appears when hovering the mouse. Idle mode is completely dateless. | An ambient desk clock appliance must answer "What day is it today?" without demanding mouse movement from across the room. | Always display the date in calm, low-contrast typography (`#71717A`) in idle mode at the top left. |
| **Carousel Readability** | Single line under the subject (`NEXT CLASS · Tue at 15:10 (in 5 days)`) is rendered in ~13–14px font. | Illegible from a 1.5–2 meter viewing distance when sitting back or reading physical textbooks. | Increase hierarchy: make status badges distinct, increase font weight, and use clear iconography/typography tokens. |
| **Subject Selection Friction** | User must hover, click the tiny subtitle "Click to open schedule", or click "Schedule" in top nav. | Subject discovery is opaque; users don't realize the entire study tracking context is bound to this subject. | Provide clear affordances: intuitive keyboard shortcuts (`Tab`/arrows to cycle subjects) and direct schedule access. |

---

### Screen 2: Focus Screen (`focus.png`)

![Focus Screen](file:///c:/Users/marj/Music/Study%20Station/docs/screens/focus.png)

| Aspect | Current Observation | Critical Flaw & Impact | Required Improvement |
| :--- | :--- | :--- | :--- |
| **Timer Visualization** | Pure numeric text (`24:53`) centered above a 4px horizontal progress bar with `0 / 60 MIN`. | **Lacks presence, geometry, and temporal intuition.** A horizontal bar is a loading bar, not a timer. From across the room, reading digits requires squinting. | **Implement a custom `QPainter` Circular Ring Gauge.** A sweeping radial arc provides immediate peripheral awareness of time remaining. |
| **Information Density** | "● FOCUSING" green pill is floating high above; subject title is isolated at the top; buttons are far down. | Fragmented vertical stack with large empty bands between elements. | Unify within the ring gauge: the ring frames the countdown, with status and subject integrated harmoniously into the center hub. |
| **Dual Progress Awareness** | Only displays the current session progress and a static cycle text (`0 / 60 MIN`). | The student cannot visually compare *this session's contribution* against their *overall subject cycle goal*. | **Concentric or dual-arc gauge:** Outer thick arc shows remaining session time (e.g., 25m countdown); inner subtle track shows cycle completion (e.g., 25/60m). |
| **Controls & Ergonomics** | "Pause", "+5 MIN", "END SESSION" pills appear below on hover. | Good hover auto-hide behavior, but the buttons are small and lack visual hierarchy. | Enlarged tactile buttons with clear keyboard shortcuts labeled directly on them (`[ Pause (Space) ]`, `[ +5m (+) ]`, `[ End (Esc) ]`). |

---

### Screen 3: Weekly Schedule Grid (`grid_schedual.png`)

![Weekly Schedule Grid](file:///c:/Users/marj/Music/Study%20Station/docs/screens/grid_schedual.png)

| Aspect | Current Observation | Critical Flaw & Impact | Required Improvement |
| :--- | :--- | :--- | :--- |
| **Missing Real Dates** | Column headers only say `LUN`, `MAR`, `MER`, `JEU`, `VEN`, `SAM`. | **It is a static timetable template, not a real calendar.** It has no concept of what week you are looking at (e.g., Oct 12–18). | Add dynamic calendar dates to headers (`LUN 12 OCT`, `MAR 13 OCT`, ...). Add week navigation (`< Previous Week`, `This Week`, `Next Week >`). |
| **Zero Calendar Overrides** | All weeks are identical forever. | Real university life has cancelled lectures, makeup sessions on Saturdays, holidays, and exam weeks. Currently impossible to represent. | Support date-specific calendar exceptions: mark a session as "Cancelled this week", "Rescheduled", or "Exam". |
| **Grid Cell Interaction** | Clicking a class card immediately selects the subject and closes the schedule screen back to dashboard. | **You cannot edit, move, or inspect a class from the grid!** If you want to know teacher notes or change the room, you are booted to the home screen. | Clicking a card should offer: `[ Start Focus ]`, `[ Edit Class ]`, `[ Cancel this Week ]`, or double-click to edit inline. |
| **Empty Slot Interaction** | Empty slots are blank, dead gray boxes (`#0E0E12`). | Clicking an empty time slot does nothing. | Clicking an empty slot should allow instantly adding a class or study block at that exact day and time! |
| **Typography & Spacing** | French titles in cards wrap aggressively (e.g. `tests logiciels (Certification ISTQB)`). | Uneven vertical padding and cramped text in smaller slots. | Better typography truncation, consistent badge positioning, and balanced card padding. |

---

### Screen 4: Schedule Editor (`editSchedual.png`)

![Schedule Editor](file:///c:/Users/marj/Music/Study%20Station/docs/screens/editSchedual.png)

| Aspect | Current Observation | Critical Flaw & Impact | Required Improvement |
| :--- | :--- | :--- | :--- |
| **CRUD Spreadsheet Anti-Pattern** | "Edit Classes" transforms the beautiful visual calendar into a generic developer `QTableWidget`. | Destroys the student's spatial mental model. University students think in terms of "Thursday afternoon after lunch", not row index 12 in a database table. | **Eliminate the raw database table view.** Implement editing directly on the Visual Grid via interactive modal cards or slide-out sheets. |
| **In-Place Modification Impossible** | To change a single typo in a room number (e.g., Lab 20 to Lab 21), the user must delete the entire row and re-enter all fields. | Horrible user friction and risk of accidental data loss. | Direct in-place editing: click any session on the calendar to open an "Edit Class" dialog pre-filled with its parameters. |
| **Add Class Ergonomics** | Inputs are compressed into a single horizontal row at the bottom with 6 tiny fields. | Low discoverability, awkward tab navigation, and easy to miss validation errors. | Clean modal dialog: `Add Class to [Day] [Time Slot]` with smart auto-completion of existing subjects and rooms. |
| **Naming Consistency** | File is named `editSchedual.png` and `grid_schedual.png` with a misspelling ("schedual"). | Minor technical debt, but reflects lack of polish in file naming and route keys. | Normalize spelling to `schedule` across all routes and assets. |

---

### Screens 5–7: Secondary Screens (`targets.png`, `log.png`, `settings.png`)

![Targets](file:///c:/Users/marj/Music/Study%20Station/docs/screens/targets.png)
![Log Time](file:///c:/Users/marj/Music/Study%20Station/docs/screens/log.png)
![Settings](file:///c:/Users/marj/Music/Study%20Station/docs/screens/settings.png)

1. **Targets Dialog (`targets.png`):**
   - *Good:* Preset pills (`30m`, `60m`, `90m`) and clean spinboxes.
   - *Missing:* Doesn't show how many minutes the user actually achieved in past cycles. It's set in a vacuum without historical context.
2. **Manual Log Dialog (`log.png`):**
   - *Critical Flaw:* Defaults to `datetime.now()` with **no date or time picker**. If a student reviewed flashcards on the train yesterday or in the library this morning, they cannot record when it actually happened!
   - *Missing:* Quick preset pills for date (`Today`, `Yesterday`).
3. **Settings Dialog (`settings.png`):**
   - *Good:* Theme grid, Evangelion typography toggle, 12h/24h toggle.
   - *Refinement:* Could include configuration for the new Focus Ring Gauge (e.g., Ring thickness, Glow intensity, Dual-arc mode).

---

## 3. High-Priority Architectural Blueprint

To solve these issues definitively before starting new milestones, the following four architectural upgrades are required:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        UPGRADE ROADMAP                                 │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Focus Ring Gauge      │ Custom QPainter radial countdown arc        │
│    (Visual Core)         │ Dual concentric rings (Session + Cycle)    │
│                          │ Breathing pause/resume & glowing sweep      │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 2. Calendar with Dates   │ Dynamic calendar week (Oct 12–18, 2026)    │
│    (Domain & UI)         │ Week navigation (< Previous / Next Week >) │
│                          │ Date headers (LUN 12, MAR 13, ...)          │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 3. Direct Schedule Edit  │ Click cell in visual grid to edit/move/add  │
│    (Eliminate Raw Table) │ Date-specific exceptions (cancellations)    │
│                          │ Modal popover for class attributes          │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 4. Ambient Station Void  │ Visible date in idle mode                   │
│    (Spatial Balance)     │ Hairline ambient daily schedule preview     │
│                          │ Proportional flip-clock scaling             │
└──────────────────────────┴─────────────────────────────────────────────┘
```

---

### Detailed Design 1: The Focus Ring Gauge (`FocusRingGaugeWidget`)

Replace the flat horizontal line in `FocusWidget` with a dedicated `QPainter` widget:

```
              ┌───────────────────────────┐
              │  ENTREPÔTS DE DONNÉES     │
              │                           │
              │         ╭───────╮         │
              │       ╱   ● REC   ╲       │  ← Outer Ring: 25m Session Countdown
              │      │             │      │  ← Inner Ring: 40/60m Cycle Progress
              │      │    24:53    │      │
              │      │  REMAINING  │      │
              │       ╲           ╱       │
              │         ╰───────╯         │
              │                           │
              │   [ Pause ]   [ +5m ]     │
              └───────────────────────────┘
```

#### Technical Specifications:
- **Widget Class:** `FocusRingGaugeWidget(QWidget)`
- **Render Engine:** Antialiased `QPainter` using `drawArc()` and `QConicalGradient` / smooth brush caps (`Qt.PenCapStyle.RoundCap`).
- **Outer Ring (Session Countdown):**
  - Diameter: 320px.
  - Track background: Subtle dark obsidian `#18181F` (8px pen).
  - Active sweep: High-contrast emerald `#10B981` (active) / amber `#F59E0B` (paused) (8px pen with rounded caps).
  - Sweeps counter-clockwise or clockwise from top (-90°).
- **Inner Ring (Subject Cycle Goal):**
  - Diameter: 284px (4px gap).
  - Muted slate/cyan `#38BDF8` (4px pen).
  - Shows progress toward the multi-day review target (e.g., 25 / 60 min = 42%).
- **Center Hub:**
  - Massive tabular monospace countdown numerals (52–56pt).
  - Pill status indicator (`● FOCUSING` / `⏸ PAUSED`).
  - Small cycle summary (`25 / 60 MIN`).

---

### Detailed Design 2: Calendar with Dates (`CalendarWeek` & Grid 2.0)

Upgrade the schedule model from an abstract 7-day loop to a real date-anchored calendar:

```
┌────────────────────────────────────────────────────────────────────────┐
│ ← Station    WEEKLY SCHEDULE           ◄  OCT 12 – 18, 2026  ► [Today] │
│                                                                        │
│  TIME        LUN 12     MAR 13     MER 14     JEU 15*    VEN 16    SAM 17
│ ────────────────────────────────────────────────────────────────────── │
│ 08h-09h30 ┌──────────┐┌──────────┐          ┌──────────┐          ┌───┐│
│           │Visualis. ││Cybercrim.│          │Sécurité  │          │...││
│           │Lab 20    ││SC 1      │          │Lab 5     │          └───┘│
│           └──────────┘└──────────┘          └──────────┘               │
└────────────────────────────────────────────────────────────────────────┘
  * Highlights today's date with emerald border and badge
```

#### Technical Specifications:
- **Model Expansion:**
  - `ScheduleEngine` tracks a `current_view_date: date` (defaults to `date.today()`).
  - Method `get_week_dates(ref_date: date) -> list[date]` returning the 6 Monday–Saturday calendar dates.
  - Formatted headers: `LUN 12 OCT`, `MAR 13 OCT`, etc.
  - Top bar controls: `◄ Prev Week`, `Next Week ►`, and `[ Today ]` shortcut pill.
- **Date-Specific Class Overrides Table:**
  - New SQLite table `calendar_overrides`:
    `(session_id, specific_date, override_type, note)`
    - `cancelled`: Class does not take place on this date (rendered with strikethrough / dim red badge).
    - `rescheduled`: Moved to a different time slot for this date only.
    - `exam`: Marked as an exam / evaluation session (rendered in amber/gold).

---

### Detailed Design 3: Direct Visual Schedule Management

Eliminate the raw `QTableWidget` in `editSchedual.png`:

#### 1. Click-to-Edit on Existing Class Cards:
- Clicking a card in the grid displays an action popover or modal:
  - `[ ▶ Start Focus ]`
  - `[ ✏ Edit Details ]` (Edit title, format, room, start/end time)
  - `[ 🚫 Cancel for this Date ]`
  - `[ 🗑 Delete Class ]`
- No need to switch screens to make a quick adjustment.

#### 2. Click-to-Add on Empty Grid Slots:
- Clicking an empty slot opens the `ClassEditorDialog` pre-populated with that day and time slot!
- The student simply enters the Subject Name and Room and clicks `Save`.

---

### Detailed Design 4: Curing the Ambient Station Void

Address the visual imbalance in `main_no_hover.png`:

1. **Always-On Low-Contrast Date Header:**
   - Display `THURSDAY, OCT 15` in the top left in idle mode (`#71717A`, 12px, tracking 1.5px). It anchors the upper-left of the display.
2. **Proportional Clock Sizing:**
   - Give the split-flap flip cards slightly more visual breathing room and height (~140px).
3. **Glanceable Bottom Daily Strip:**
   - Along the bottom of the screen, render a calm, subtle horizontal hairline timeline of today's schedule:
     `08:00 Visualisation · 09:40 Prévision · 13:30 Veille (Lab 11)`
   - This informs the student what classes they have today at a glance without having to open the full calendar, elegantly grounding the bottom 30% of the canvas.

---

## 4. Implementation Status
 
All four improvement phases have been executed, tested, and verified:

1. **Phase A: Focus Screen Ring Gauge `[COMPLETED]`**
   - Built custom `FocusRingGaugeWidget` (`src/study_station/ui/focus_ring_gauge.py`) with antialiased concentric dual arcs, tabular numerals, and status pill.
   - Integrated into `FocusWidget`.
   - Verified via `tests/test_focus_ring_gauge.py`. Screen capture updated: `docs/screens/focus.png`.
2. **Phase B — Part 1: Real Calendar Dates & Week Navigation `[COMPLETED]`**
   - Added deterministic date calculations to `ScheduleEngine` (`get_week_start`, `get_week_dates`, `format_week_range`, `get_day_date`).
   - Added week navigation bar (`[ ‹ ] 12 – 17 OCT 2026 [ › ] [ Today ]`) and real day dates with today's emerald highlight.
   - Verified via `tests/test_engine.py` and `tests/test_secondary_dialogs.py`. Screen capture updated: `docs/screens/grid_schedual.png`.
3. **Phase B — Part 2: Direct Visual Schedule Editing `[COMPLETED]`**
   - Implemented `ClassSessionDialog` (`src/study_station/ui/class_session_dialog.py`) with 1-click focus, class editing, and deletion.
   - Implemented interactive `EmptyGridSlot` cards with hover `+` trigger for instant session creation.
   - Verified via `tests/test_class_session_dialog.py`. Screen capture updated: `docs/screens/editSchedual.png`.
4. **Phase C: Ambient Station Spatial Balance & Date Visibility `[COMPLETED]`**
   - Kept date header (`THURSDAY, OCT 15`) permanently visible in idle mode; only navigation action buttons auto-hide.
   - Implemented ambient `_create_timeline_strip` along the bottom with live classes (`✓` past, `● NOW` emerald active, upcoming neutral).
   - Re-captured and verified `docs/screens/main_no_hover.png` and `docs/screens/main_with_hover.png` at 1366×768 resolution.

---

*Authored by Antigravity Pairing Assistant for Study Station.*


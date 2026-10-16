# Study Station: Architectural & UX Enhancement Roadmap

**Date:** October 16, 2026  
**Status:** Tier 1 & Tier 2 Completed (Tier 3 Next)  
**Scope:** Synthesis of UI audits, pedagogical specs, and student workstation workflow optimization.

---

## 1. Roadmap Architecture Overview

Study Station has completed its foundational academic pivot (Milestones 1–17: Local SQLite WAL, Academic Cockpit Grid, Nightly Debrief Wizard, Task-Tethered Focus Gauge, In-Class Question HUD, Backlog CRUD, and Zero-Password Multi-User DB Isolation), Tier 1 UX Polish (Milestone 18), and Tier 2 Academic Urgency Engine & Special Override Periods (Milestone 19).

This roadmap structures the critique and enhancements into **3 focused tiers**:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               DEVELOPMENT TIERS                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│ TIER 1: Immediate UX, Layout Polish & Anti-Fatigue Rituals [COMPLETED]           │
│ - Fixed SettingsDialog container height & vertical clipping                      │
│ - Implemented anti-fatigue conditional exit ticket (instant extend, adaptive Qs) │
│ - Reorganized Cockpit Top Bar into 3 balanced visual clusters                    │
│ - Added dismiss/collapse to Tonight's Priority Task capsule                      │
│ - Eliminated deficit metric (0% guilt framing) on Ambient Clock                  │
│ - Fixed asset filename typos and synced README test telemetry (129 tests)        │
├──────────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: Academic Urgency Engine & Special Override Periods [COMPLETED]           │
│ - Urgency heuristic upgrade: Tomorrow morning (08:00) lecture bias               │
│ - Special Academic Override Periods ("day / x days / weeks / x weeks"):         │
│   • SpecialPeriod model, SQLite table & repository CRUD                          │
│   • SpecialPeriodDialog with 1-click presets, type chips & overwrite switch      │
│   • Weekly Schedule hero banner, day header badges & card override indicators    │
│ - Multi-criteria Backlog Sorting (Deadline, Academic Urgency, Subject, Title)   │
│ - Relocated nuclear [Empty Tasks] to safe guarded footer utility                 │
│ - Debrief wizard active template button states & unambiguous step buttons        │
├──────────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: Academic Semester Realities & Dedicated In-Class HUD [NEXT]              │
│ - Slot-Specific Calendar Overrides (Cancelled classes, Makeups/Rattrapages)      │
│ - Fullscreen In-Class Lecture HUD with extra-large [Copy] & [Asked] triggers    │
│ - Export semester review report & printable revision checklist                   │
│ - SQLite connection lifecycle audit (zero ResourceWarnings)                      │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tier 1: Immediate UX, Layout Polish & Anti-Fatigue Workflows

### 2.1 Settings & Customization Dialog Layout Overhaul
- **Problem:** The `STUDY MANAGEMENT` section is sliced off at the bottom of the modal, and the `Done` button overlaps cropped widgets.
- **Solution:** 
  - Restructure dialog layout to cleanly fit the 500×680 envelope.
  - Convert `STUDY MANAGEMENT` into a compact, unified tool grid.
  - Configure the scroll area with auto-managed vertical scrollbar and comfortable bottom padding.

### 2.2 Cognitive Exit Ticket Anti-Fatigue Logic
- **Problem:** Forcing a 4-step questionnaire after every 15-minute micro-sprint causes survey fatigue.
- **Solution:**
  - **Instant Continuation:** Clicking `[ +10m Need More Time ]` dynamically transforms the modal into an immediate continuation confirmation (`▶ Resume +10m Focus`) and collapses questions 3 & 4.
  - **Adaptive Question Revelation:** 
    - When `🟢 Solid` confidence is selected: Question 3 ("Formulate 1 Question for Next Class") is collapsed into an optional link, because solid comprehension means no questions are pending.
    - When `🔴 Foggy` or `🟡 Getting There` is selected: Question 3 expands with high-visibility guidance to capture what made the student pause.
  - **Rename Action:** Change `Skip Debrief` to `Skip Ticket` / `Close`.

### 2.3 Cockpit Top-Bar Clustering (1366×768 Balance)
- **Problem:** 9 disparate buttons and labels are squeezed into a single row on the Weekly Schedule Cockpit.
- **Solution:**
  - **Left Cluster (Student Identity & Rituals):** `[ 👤 {User} ]` `[ ⚡ Debrief ]` `[ ✓ Tasks ]`
  - **Center Cluster (Calendar & Navigation):** `WEEKLY SCHEDULE` + `[ ‹ ]  12 – 17 OCT 2026  [ › ]  [ Today ]`
  - **Right Cluster (Station Views & Tools):** `[ ⏱ Clock ]` `[ Grid | Edit ]` `[ ⇄ Import / Export ]` `[ PDF ]`
  - Clear layout stretches between clusters preventing visual crowding.

### 2.4 Dismissible Priority Task Capsule
- **Problem:** Debrief Banner (~50px) + Priority Card (~60px) take over 110px above the grid, compressing afternoon class rows on 768p laptop displays.
- **Solution:** Add a dismiss `[ ✕ ]` button to `priority_task_card` (matching the debrief banner), allowing students to maximize vertical grid space on demand.

### 2.5 Positive Milestone Framing on Flip Clock
- **Problem:** `● 0 / 60 MIN COMPLETED · 0%` reinforces deficit framing on the ambient clock.
- **Solution:** When 0 minutes are logged, render `🎯 {tgt} MIN TARGET · READY TO FOCUS`. When completed minutes exist, render `● {comp} / {tgt} MIN COMPLETED · {pct}%`.

### 2.6 Typo Corrections & Documentation Telemetry
- **Fixes:**
  - Rename `grid_schedual.png` → `grid_schedule.png` and `editSchedual.png` → `edit_schedule.png` (with backwards-compatible aliases).
  - Update `README.md` test counter badge and summary to `129/129 tests passing across 18 test suites`.

---

## 3. Tier 2: Academic Urgency Engine & Special Academic Override Periods [COMPLETED]

### 3.1 Academic Urgency Heuristic (Tomorrow-Morning Proximity Bias)
- **Problem:** Chronological deadlines fail to prioritize urgent academic preparation. A task due tomorrow morning at 08:00 must outrank tasks due later in the week.
- **Implementation:**
  - Implemented `calculate_todo_urgency_score(todo, current_dt)` in `ScheduleEngine`.
  - Overdue items are given priority scores $\ge 100,000$ scaled by elapsed overdue minutes.
  - Active pending items compute proximity score:
    $$\text{UrgencyScore} = \frac{1000}{\Delta t_{\text{due}} + 1} + \frac{2500}{\Delta t_{\text{class}} + 1}$$
  - Connects to `get_priority_study_todo()` so the Weekly Cockpit Priority Card automatically elevates tomorrow morning deliverables.

### 3.2 Special Academic Override Periods ("day / x days / weeks / x weeks")
- **Problem:** Academic semesters encounter exceptional periods—Devoirs Surveillés (DS week), revision periods, sprint weeks, or holidays—where standard recurring weekly timetables must be overridden or visually contextualized.
- **Implementation:**
  - **Data Model & Persistence:** `SpecialPeriod` dataclass with `name`, `period_type` (`exam`, `revision`, `sprint`, `holiday`, `custom`), `start_date`, `end_date`, `overwrite_schedule` (bool), and `notes`.
  - **Auto-Calculated Durations:** Supports exact day and week labeling (`1 Day`, `X Days`, `1 Week`, `2 Weeks`) handling both 6-day academic and 7-day calendar weeks.
  - **Dedicated UI (`SpecialPeriodDialog`):**
    - One-click duration presets: `1 Day (Today)`, `3 Days (Sprint)`, `1 Week (This Week)`, `2 Weeks (Exams)`.
    - Period type selector chips with distinctive visual badges.
    - Start & End date pickers with live calculated duration counter.
    - `Overwrite regular class timetable during this period` toggle.
    - Active periods list with in-place delete buttons.
  - **Cockpit Calendar Integration:**
    - Top-bar trigger pill: `[ ⚡ Period Mode ]` or active summary badge `[ ⚡ 1 WEEK: Devoirs Surveillés (DS Week) ]`.
    - Amber hero banner above the grid: `⚡ SPECIAL ACADEMIC PERIOD ACTIVE: {name} ({duration}) — Timetable Overwritten`.
    - Day headers dynamically display badges: e.g., `LUN [ ⚡ EXAM ] 12 OCT`.
    - When `overwrite_schedule` is active, regular calendar cards render with amber dashed borders and `⚡ OVERRIDDEN` badges.

### 3.3 Backlog Sorting & Guarded Backlog Purge
- **Problem:** Students with 20+ deliverables had no way to sort tasks, and the destructive `[ Empty Tasks ]` button was dangerously placed in the top header row.
- **Implementation:**
  - Added multi-criteria sort dropdown in `TasksDialog`: `Sort: Deadline (Earliest)`, `Sort: Academic Urgency`, `Sort: Subject (A–Z)`, `Sort: Title (A–Z)`.
  - Moved nuclear clear button out of the top header to a guarded footer utility: `🗑 Clear All Tasks...` with a mandatory two-step confirmation popup.

### 3.4 Debrief Wizard Active Template Highlighting
- **Problem:** In `DebriefDialog`, students clicking quick template prompts had no visual feedback indicating which template was selected.
- **Implementation:**
  - Dynamic emerald styling (`border: 1px solid #10B981; background: #14221D; color: #10B981;`) applied to whichever template matches the input field prefix.
  - Renamed bottom stepper actions for unambiguous intent (`Finish Debrief ✓`).

---

## 4. Tier 3: Semester Overrides & Dedicated In-Class HUD

### 4.1 Date-Specific Calendar Overrides
- Database table `calendar_overrides (session_id, specific_date, override_type, notes)`:
  - `cancelled`: Class does not take place on this date (strikethrough card).
  - `rescheduled`: Slot time/room change for one specific date.
  - `exam`: Devoir surveillé / exam session (amber highlighted card).

### 4.2 Dedicated In-Class Lecture HUD
- Full-screen, high-contrast sheet during lecture hours displaying only the questions formulated for that specific subject with large touch/click targets:
  - `[ 📋 Copy Question to Clipboard ]`
  - `[ ✓ Asked in Class ]` (resolves question and marks todo verified)

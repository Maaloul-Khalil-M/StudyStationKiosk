# Study Station: Architectural & UX Enhancement Roadmap

**Date:** October 16, 2026  
**Status:** In Execution (Tier 1 Active)  
**Scope:** Synthesis of UI audits, pedagogical specs, and student workstation workflow optimization.

---

## 1. Roadmap Architecture Overview

Study Station has completed its foundational academic pivot (Milestones 1–17: Local SQLite WAL, Academic Cockpit Grid, Nightly Debrief Wizard, Task-Tethered Focus Gauge, In-Class Question HUD, Backlog CRUD, and Zero-Password Multi-User DB Isolation).

This roadmap structures the critique and enhancements into **3 focused tiers**:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               DEVELOPMENT TIERS                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│ TIER 1: Immediate UX, Layout Polish & Anti-Fatigue Rituals (ACTIVE)              │
│ - Fix SettingsDialog container height & vertical clipping                        │
│ - Implement anti-fatigue conditional exit ticket (instant extend, adaptive Qs)   │
│ - Reorganize Cockpit Top Bar into 3 balanced visual clusters                     │
│ - Add dismiss/collapse to Tonight's Priority Task capsule                        │
│ - Eliminate deficit metric (0% guilt framing) on Ambient Clock                   │
│ - Fix asset filename typos and sync README test telemetry (129 tests)            │
├──────────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: Academic Urgency Engine & Backlog Ergonomics (NEXT)                      │
│ - Urgency heuristic upgrade: Tomorrow morning (08:00) bias                       │
│ - Multi-criteria Backlog Sorting (Due Date earliest, Subject A-Z, Urgency)      │
│ - Relocate nuclear [Empty Tasks] out of primary header                           │
│ - Debrief wizard active template button states & unambiguous step buttons        │
│ - User profile avatar tokens & inline renaming                                   │
├──────────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: Academic Semester Realities & Dedicated In-Class HUD (FUTURE)            │
│ - Date-Specific Calendar Overrides (Cancelled classes, Makeups/Rattrapages, DS) │
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

## 3. Tier 2: Academic Urgency Engine & Backlog Ergonomics

### 3.1 Academic Urgency Heuristic (Tomorrow Morning Bias)
- Calculate urgency with class proximity weighting:
  $$\text{UrgencyScore} = \text{OverdueFactor} \times 1000 + \frac{1}{\Delta t_{\text{next class}} + 1}$$
- Tasks due for tomorrow morning's 08:00 session automatically outrank tasks due next Thursday, even if created later.

### 3.2 Backlog Sorting & Safe Actions
- Add segmented sort pills in `TasksDialog`:
  - `Sort: Deadline (Earliest)`
  - `Sort: Subject (A–Z)`
- Move nuclear `[ Empty Tasks ]` button to an action menu (`...`) with explicit two-step confirmation.

### 3.3 Debrief Wizard Polish
- Highlight active template pills (`[ 💻 Lab Fix ]`, `[ 📖 Slides ]`) with emerald border when clicked.
- Rename bottom stepper button from `Skip Finish` to `Skip Subject` / `Finish Debrief ✓`.

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

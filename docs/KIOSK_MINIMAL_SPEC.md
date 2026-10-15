# Study Station: Kiosk & Ambient Study Appliance Specification

## 1. Executive Summary & Core Critique

### The Misstep of the "SaaS Dashboard" Approach
In Milestone 6 & 6.5, the interface attempted to solve information density by adopting patterns from modern web applications (Linear, Notion, Jira):
- Side-by-side widget cards (Hero Card + Upcoming Timeline).
- Multi-button toolbars (`Start Focus`, `25m`, `Log Time`, `Edit Target`).
- Horizontal chip carousels along the bottom.
- Dense data tables and standard desktop form popups.

While visually orderly on a laptop at a 40cm viewing distance, this violated the core premise of Study Station: **a dedicated kiosk / ambient study monitor sitting on a desk 1–2 meters away while a student reads physical books, solves problem sets, or attends online lectures.**

### The Reality of Desk-Kiosk Appliance UX
From 1.5 meters away:
- **Zero Distraction:** Unnecessary borders, multiple cards, and visible buttons create cognitive drag.
- **Glance Test (3 Seconds):** The student only needs to know:
  1. *What time is it?* (Medium mechanical flip clock)
  2. *What subject is active / What is my goal?* (Giant bold Swiss typography)
  3. *How am I doing in this cycle?* (Single-line info carousel)
- **Hover-to-Interact:** All interactive controls (start button, top navigation, schedule buttons) are **hidden by default** during idle contemplation and smoothly fade in only when the mouse moves.
- **The Student's Mental Model is the Weekly Grid:** Rather than a random horizontal chip carousel or an Excel-like database table, a university student navigates by their timetable grid (as seen in `docs/grid.pdf`). Clicking the subject or schedule reveals an interactive, visual weekly grid (Google Calendar style).

---

## 2. Screen-by-Screen Architecture

### Screen 1: The Main Ambient Station (Home)

#### A. Idle State (Default — Standing at Desk)
No visible buttons, no top navigation, no borders, no bottom dock. Deep obsidian `#0C0C0E` background.
```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│                          ┌───┐ ┌───┐ : ┌───┐ ┌───┐                     │
│                          │ 1 │ │ 0 │ : │ 4 │ │ 2 │                     │
│                          └───┘ └───┘ : └───┘ └───┘                     │
│                                                                        │
│                                                                        │
│                   VISUALISATION DES DONNÉES                            │
│                                                                        │
│                ● 25 / 60 MIN COMPLETED  (42%)                          │
│                                                                        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```
- **Clock:** Authentic mechanical split-flap flip clock, sized moderately (`~120–135px` height). Commanding and physical, but balanced.
- **Subject Name:** Giant 34–38pt Swiss off-white typography (`#F4F4F5`).
- **Single-Line Info Carousel:** Directly below the subject, rotates smoothly every 7s between:
  - *Slide 1 (Progress):* `● 25 / 60 MIN COMPLETED (42%)` with a slim, high-contrast fill gauge.
  - *Slide 2 (Next Class):* `📅 NEXT CLASS: Friday at 08:00 · Lab 20 (in 2 days)`.
  - *Slide 3 (Format & Instructor):* `📍 TP · 1.5h · Ben Moussa Iteb · Lab 20`.

#### B. Active / Hover State (Mouse Moved)
Controls smoothly fade in; auto-fades back to Idle after 3.5 seconds of inactivity.
```
┌────────────────────────────────────────────────────────────────────────┐
│  WEDNESDAY, OCT 14                     [📅 SCHEDULE]  [🎯] [✍] [⚙] [⛶] │
│                                                                        │
│                          ┌───┐ ┌───┐ : ┌───┐ ┌───┐                     │
│                          │ 1 │ │ 0 │ : │ 4 │ │ 2 │                     │
│                          └───┘ └───┘ : └───┘ └───┘                     │
│                                                                        │
│                   VISUALISATION DES DONNÉES  ▾                         │
│                                                                        │
│            ◄   ● 25 / 60 MIN COMPLETED  (42%)   ►                      │
│                                                                        │
│                      [ ▶ START FOCUS ]   (Space)                       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```
- **Top Navigation Bar:** Tactile hardware pill switches:
  - `[ 📅 Schedule ]` (Opens Weekly Grid)
  - `[ 🎯 Targets ]` (Opens Subject Targets Sheet)
  - `[ ✍ Log ]` (Opens Quick Log Sheet)
  - `[ ⚙ Settings ]`
  - `[ ⛶ Fullscreen ]`
- **Primary Focus Button:** One high-contrast pill button centered under the carousel: `[ ▶ START FOCUS ] (or Space)`.
- **Subject Picker Trigger:** Clicking the subject name (or `[ 📅 Schedule ]`) opens the Weekly Schedule Grid.

---

### Screen 2: The Weekly Schedule Grid (`docs/grid.pdf` / Google Calendar Model)

Replaces both the old spreadsheet timetable dialog and the bottom subject chip carousel with **the student's real schedule grid**.

```
┌────────────────────────────────────────────────────────────────────────┐
│  WEEKLY SCHEDULE                           [ + Add Class ]   [ ✕ Close ]│
│                                                                        │
│  TIME        LUN        MAR        MER        JEU        VEN       SAM │
│ ────────────────────────────────────────────────────────────────────── │
│ 08h-09h30 ┌──────────┐┌──────────┐          ┌──────────┐          ┌───┐│
│           │Visualis. ││Cybercrim.│          │Sécurité  │          │...││
│           │Lab 20    ││SC 1      │          │Lab 5     │          └───┘│
│           └──────────┘└──────────┘          └──────────┘               │
│ 09h40-11h10┌──────────┐┌──────────┐          ┌──────────┐┌──────────┐  │
│           │Prévision ││Entrepren.│          │Entrepôts ││NoSQL     │  │
│           │SC 3      ││SC 3      │          │SC 3      ││SC 3      │  │
│           └──────────┘└──────────┘          └──────────┘└──────────┘  │
│ 11h15-12h45                                 ┌──────────┐┌──────────┐  │
│                                             │Anglais 4 ││Tests Log.│  │
│ 13h30-15h ┌──────────┐┌──────────┐          │S 1       ││SC V      │  │
│           │Veille    ││NoSQL     │          └──────────┘└──────────┘  │
│ 15h10-16h40│Lab 11   ││Lab 20    │                                     │
│           └──────────┘└──────────┘                                     │
└────────────────────────────────────────────────────────────────────────┘
```
- **Grid Layout:**
  - Days: `LUN`, `MAR`, `MER`, `JEU`, `VEN`, `SAM`.
  - University Time Slots (from `grid.pdf`):
    - `08:00 - 09:30`
    - `09:40 - 11:10`
    - `11:15 - 12:45`
    - `13:30 - 15:00`
    - `15:10 - 16:40`
- **Interactive Subject Switcher:** Clicking *any* class card immediately selects that subject as the active subject for focus and returns to the home screen.
- **Current Class Indicator:** The session matching the current real-world time is framed with a glowing emerald pulse (`● IN CLASS NOW`).
- **Management:** Double-clicking or clicking `+ Add Class` opens a clean class editor; right-clicking or selecting lets you remove a class.

---

### Screen 3: Pure Concentration Focus Screen

During active focus, the student must be immersed:
```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│                        VISUALISATION DES DONNÉES                       │
│                                                                        │
│                                14 : 32                                 │
│                                                                        │
│                        ━━━━━━━━━━━━━━━━━━━━━                           │
│                                                                        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```
- **Idle (During Focus):**
  - Only the subject title, large 84pt tabular monospace countdown timer, and a hairline session progress gauge.
  - Zero button clutter.
- **Hover (During Focus):**
  - Smoothly reveals three minimal tactile pills: `[ Pause ] (Space)` · `[ +5 Min ] (+)` · `[ End Session ] (Esc)`.
  - Automatically fades back out when the cursor is still.

---

### Screen 4: Completion Screen (Effort Acknowledgment)

- **Pure Minimal Feedback:**
  - Giant green/amber typographic stamp: `+ 15 MIN`.
  - Subject Name + Cycle Status: `40 / 60 MIN COMPLETED (67%)`.
  - Hairline cycle progress animation filling to target.
  - Auto-dismisses back to Main Ambient Station after 4 seconds or any keypress.

---

### Screen 5: Appliance-Style Targets & Log Screens

- **Targets Configuration:**
  - Pure vertical list of subjects.
  - Large tactile preset pills: `[ 30m ]`, `[ 45m ]`, `[ 60m ]`, `[ 90m ]` + `[ − ] [ + ]` step buttons.
  - No database tables or tiny desktop spinboxes.
- **Quick Study Time Log:**
  - Pre-selected subject.
  - 4 quick-tap pills: `[ +15m ]`, `[ +30m ]`, `[ +45m ]`, `[ +1h ]`.
  - Single `[ CONFIRM LOG ]` action.

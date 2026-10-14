# Product Concept — Study Station

## 1. Overview

Study Station is a desktop application that turns a spare PC or laptop into an always-available study screen. It combines:

- a large, minimalist flip clock (the visual centrepiece),
- a lightweight focus timer with short flexible durations,
- a study-progress system driven by the student’s weekly school timetable.

The product is **not** primarily a timetable viewer. Its purpose is to help the student review material from one class before that subject returns, even when the student only has short, irregular periods available for studying.

**Guiding idea**

> A calm, always-available study clock that turns the gaps between classes into achievable review goals, allowing a student to make progress in small, irregular pockets of time.

The app must remain useful without demanding constant attention. The clock stays the visual centrepiece; the study system works quietly in the background.

## 2. Context and constraints

Original use case: a student with a spare older machine used as a dedicated display for a flip-clock + focus experience.

Key user constraints the product must respect:

- The student may rarely sit at a desk or may only study for limited periods.
- It must be easy to begin a short study session.
- Irregular sessions are accepted; a rigid routine is not required.
- Short sessions still contribute to progress.
- No guilt-inducing warnings or growing backlogs of missed minutes.
- Not all studying happens at the PC.
- The always-on display must stay useful without frequent interaction.

## 3. Problem

Classes happen at fixed times. Studying happens in the gaps between them. Those gaps can be unpredictable and short. A student can reach the next class without having reviewed the material from the previous one.

- A conventional clock only knows the time.
- A conventional Pomodoro timer only knows its countdown.
- A conventional timetable only knows when classes occur.

Study Station connects those pieces to support an ongoing review habit.

**Key user need**  
Help a student make enough progress reviewing a subject between one class and its next occurrence, without requiring long uninterrupted sessions or complex planning.

## 4. Product philosophy and visual style

Three related ideas:

- **Minimalist UI** — show only what is needed; restrained colours, clear typography, generous negative space.
- **Glanceable / ambient display** — information understandable in a quick glance, potentially from across the room.
- **Calm technology** — available and helpful while demanding as little attention as possible.

**Core interface rule**  
Every screen answers one question. Every visible element helps answer that question.

The clock remains the visual centrepiece. Timetable, configuration and statistics live behind deliberate interaction.

**Suggested default visual direction**  
Retro Minimal — large white flip-clock digits on a black background, one discreet secondary line for study progress.

Example idle screen (illustration only):

```
             21:08

       DATA VIS. · 25 / 60 MIN
```

## 5. Core concept: Study Cycles

The primary organising concept is the **study cycle** between two consecutive occurrences of the same subject, not the calendar day.

Example:

1. Monday — class completed → a new study cycle opens for that subject.
2. Tuesday — 10 minutes of review → minutes count toward the cycle goal.
3. Thursday — 15 minutes of review → progress increases.
4. Following Monday — next class → old cycle closes, new cycle begins.

If the target were 60 minutes, the student would have completed 25 of those 60 minutes before the next class. Targets are configurable and should be realistic per subject.

Important distinctions:

- The **timetable** records when a class occurs.
- The **study cycle** defines the review goal between consecutive occurrences of a subject.
- The **study log** records time actually spent studying.
- Attending a class does **not** automatically count as review time.
- The next class closes the previous cycle and starts the next one.

Unfinished goals are **not** carried forward as accumulating debt. The old cycle is closed, the result recorded, and a fresh cycle starts.

## 6. Minimal screens and states

Three main screen states. They are not separate applications.

### Screen 1 — Ambient Clock
**Question answered:** What time is it, and how am I progressing?

- Large flip clock.
- Optional date.
- One discreet subject / progress indicator where appropriate.
- No large timetable, task list, graph or collection of cards.
- Default state when the user is not interacting.

### Screen 2 — Focus
**Question answered:** What am I working on right now?

- One subject or selected study task.
- Large countdown.
- Simple focus-state label.
- Minimal controls to pause, end or resume.
- Support for short durations: 5, 10, 15, 25 minutes.

Starting a session must have very low friction.

### Screen 3 — Completion
**Question answered:** Did my effort count?

- Simple confirmation (e.g. `+10 MIN`).
- Updated progress (e.g. `35 / 60 MIN COMPLETED`).
- Return to the ambient clock automatically after a short interval or user action.

No over-use of rewards, streaks or gamification.

All other information (full timetable, subject settings, targets, weekly statistics) belongs behind deliberate interaction.

## 7. Behaviour required for short, irregular study periods

- Flexible micro-sessions (5 / 10 / 15 / 25 min).
- Low-friction start — when several subjects have unfinished goals, recommend one useful next action (not a complicated ranking).
- Easy pause and resumption with no penalty.
- Support for study done away from the PC via simple manual time entry (minimal in MVP).
- Reliable timer behaviour: store the target end timestamp; recover remaining time after refresh, restart or suspend/resume.
- Calm reminders only; no guilt language.

## 8. Naming and positioning

Possible names considered: Classclock, Study Station, Tempo, Deskwise, Between.

Suggested positioning:

> A quiet desktop companion for students. Your time, your timetable, your focus — all on one screen.

## 9. One-paragraph summary

Study Station is a minimalist, ambient flip-clock desktop application for a student who has a spare machine available as a dedicated screen and limited or irregular time to study. It stores a weekly timetable, identifies consecutive classes for each subject, and creates a study cycle between them. The student sets a realistic review-time target, completes flexible short sessions whenever possible, and sees progress reflected discreetly on the clock. The first version prioritises a clean glanceable interface, reliable timer behaviour, editable timetable data, local persistence, and validation with real use. Its central promise is not to display tomorrow’s schedule, but to help the student review today’s lessons before those subjects return.

# 10. example.json and the logic behind It

Schedule Parsing Architecture: From 2D Grid to JSON

This document outlines the conceptual data model used to transform a visual, two-dimensional PDF school timetable into a structured, machine-readable JSON format suitable for frontend application state management.

## The Grid: `ScheduleMatrix`

The visual schedule operates as a standard 6x7 matrix. We can conceptualize this container as the **`ScheduleMatrix`**.

* **X-Axis (Columns):** Represents the days of the academic week (Lun, Mar, Mer, Jeu, Ven, Sam).
* **Y-Axis (Rows):** Represents the predefined academic time slots (e.g., 08:00-09:30, 09:40-11:10).

While a 2D array (`Grid[Day][TimeSlot]`) directly mirrors the physical PDF layout, a flattened array of objects is far more efficient for data binding, filtering (e.g., querying all "TP" sessions, or filtering by a specific day), and feeding into UI components.

## The Grid Cell: `AcademicSession`

Each populated intersection in the `ScheduleMatrix` is a **cell**. In this data model, a cell represents a single, distinct event classified as an **`AcademicSession`**.

An empty cell means no session is scheduled for that coordinates. A populated cell is broken down into the following core properties:

### 1. Temporal Data (`day`, `timeSlot`)

The cell's physical position in the grid coordinates dictates its exact timing.

* **`day`**: A string representing the column header (e.g., "Lun", "Mar").
* **`timeSlot`**: An object containing the start and end times parsed from the row headers (e.g., `{"start": "08:00", "end": "09:30"}`).

### 2. Subject Definition (`subject`)

The bulk text inside the cell contains the academic information, abstracted into a `subject` object.

* **`name`**: The primary title of the module (e.g., "Visualisation des données", "Techniques de prévision").
* **`core`**: The pedagogical format of the session, parsed from the acronyms in the text:
* **COURS**: Theoretical lecture.
* **TD (Travaux Dirigés)**: Directed tutorials and problem-solving.
* **TP (Travaux Pratiques)**: Practical laboratory work (e.g., coding, PC practice).
* **CI (Cours Intégré)**: Integrated class blending theory and immediate application.



### 3. Spatial Data (`location`)

The final piece of critical data extracted from the bottom of the cell text.

* **`location`**: The physical room or lab where the session takes place (e.g., "Lab 20", "SC 3").

*(Note: The Professor's name and the redundant Class Name are intentionally stripped from the cell data during parsing to maintain a clean, normalized structure).*

## Example `AcademicSession` JSON Mapping

```json
{
  "day": "Lun",
  "timeSlot": {
    "start": "08:00",
    "end": "09:30"
  },
  "subject": {
    "name": "Visualisation des données",
    "core": "TP"
  },
  "location": "Lab 20"
}

```
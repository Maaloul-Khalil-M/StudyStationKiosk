# Study Station: Academic Preparation & Nightly Desk Specification

**Date:** October 15, 2026  
**Status:** Approved Architecture & Milestone Blueprint  
**Target:** Pivot to Nightly Desk Cockpit, Subject Preparation Todos, Grid-First Navigation, and Cognitive Comprehension  

---

## 1. Executive Summary & Context of Use

### 1.1 The Actual Student Reality
Study Station is used by an IT/Data Science university student (*T-LSI ADBD Cours 2*) taking cumulative, highly technical courses:
* *Bases de données NoSQL*
* *Techniques de prévision*
* *Entrepôts de données*
* *Sécurité et contrôle d'accès aux Big data*
* *tests logiciels (Certification ISTQB)*
* *Framework de développement web*

### 1.2 The Night Desk Routine
* **Not an all-day monitor:** The student does not interact with the app during lectures or casual breaks.
* **The Evening Desk Ritual:** The application is used **at night at the study desk** after returning home from university.
* **The Core Cognitive Dilemma:**  
  > *"Today / in the last days I had a hard subject and I feel demotivated to touch it again, but I am certain if I go to the next session next week without doing the focus minutes, I know that nothing will enter my brain."*

University technical subjects are strictly sequential. If a student falls behind on Monday's lab or lecture, next Monday's session becomes 90 minutes of incomprehensible noise. The app's primary purpose is to **bridge the gap between today's struggle and next week's lecture**, converting paralysis into small, actionable units of preparation.

---

## 2. The 5 Core Critiques & The Functional Pivot

### Critique A: The "Monolith Trap" — You Cannot Study a Noun
* **Old Behavior:** The app displayed a broad subject title (e.g., `ENTREPÔTS DE DONNÉES`).
* **The Failure:** A subject title is abstract and triggers dread. A student cannot sit down to study "Data Warehouses"—they must fix a broken ETL script, review slide 14, or write down a question. Starting a timer on a broad subject leaves the student paralyzed in front of a ticking clock.
* **The Pivot:**  
  1. The app introduces a **Nightly Debrief Questionnaire** triggered when sitting down at the desk.
  2. The debrief asks about the classes attended today and generates **actionable preparation TODOS**.
  3. Every task has a default deadline: **the exact start time of next week's session for that subject** (or a custom project deadline).
  4. Focus sessions are tethered to a **specific task**, not an abstract subject title.

---

### Critique B: The Suggestion Algorithm Prefers "Imminent" over "Vulnerable"
* **Old Behavior:** The engine auto-suggested whichever class occurred closest in the calendar (e.g., tomorrow morning's class).
* **The Failure:** If Monday's *Techniques de prévision* was difficult, but tomorrow is Thursday with *Sécurité Big Data*, the app buried Monday's subject and pushed Thursday's to the screen. The subject that caused dread was ignored until it was too late.
* **The Pivot:**  
  1. The algorithm is retired as the primary navigation driver.
  2. **The Weekly Schedule Grid becomes the Main Screen (Home).**
  3. The grid visually maps the student's entire academic week, displays real calendar dates, and embeds live **Todo Badges** on each class card.
  4. The student directly sees which subjects have pending preparation tasks and can engage any task with one click.

---

### Critique C: The Deficit Framing vs. Actionable Sprints
* **Old Behavior:** Displaying `● 0 / 60 MIN COMPLETED · 0%`.
* **The Failure:** To a demotivated student, `0%` feels like a failing grade before starting, and `60 MIN` feels like an insurmountable mountain.
* **The Pivot:**  
  1. Replace the deficit percentage with the **Active Task Sprint**: `[ ▶ FOCUS 15m ] ON: [Task Title]`.
  2. When the timer finishes (or is stopped early), the system prompts:
     * `[ ✓ Mark Completed ]` — Closes the task, records attribution, updates the grid.
     * `[ +10m More ]` — Seamlessly extends the countdown without breaking flow.
     * `[ ⏸ Put Aside ]` — Preserves the task for the next study session while capturing elapsed minutes in `StudyLog`.

---

### Critique D: The "Factory Punch-Clock" vs. "Brain Comprehension"
* **The Problem:** Logging 25 minutes of sitting in a chair does not guarantee comprehension. A student can stare blankly at slides for 25 minutes, hear the chime, see `+25 MIN`, and still know nothing when walking into class next week.
* **The Pivot — The 60-Second Cognitive Exit Ticket:**  
  At the conclusion of a focus session, the screen presents three lightweight cognitive checks:
  1. **3-Level Confidence Gauge (Traffic Light):**  
     `[ 🔴 Foggy / Stuck ]` · `[ 🟡 Getting There ]` · `[ 🟢 Solid ]`
  2. **The "Next Class Question" Anchor (The Dread Neutralizer):**  
     If the student selects 🔴 or 🟡, the system prompts:  
     *“What is the 1 specific question you need answered in next week's class?”*  
     This question is saved and pinned directly to next week's class card in the Schedule Grid. It turns confusion into an active academic strategy.
  3. **The 1-Sentence Feynman Takeaway:**  
     *“In one sentence, what did you just learn or fix?”*  
     Forces synthesis from short-term memory to long-term understanding.

---

### Critique E: The Ambient Passivity Barrier
* **Old Behavior:** In idle mode, all controls, navigation buttons, and action triggers faded into pitch black after 3.5 seconds.
* **The Failure:** For a student sitting at a desk at night avoiding a difficult subject, having to shake the mouse to see if anything can be done creates unnecessary friction. The screen felt passive and indifferent.
* **The Pivot — Night Desk Workstation Mode:**  
  1. **Evening Hours Activation (after 18:00):** The app operates in active desk mode.
  2. **Debrief Callout Banner:** If classes were held today and no debrief has occurred, a high-contrast banner appears at the top of the grid:  
     `⚡ NIGHTLY CHECK-IN: You had 2 classes today (Entrepôts, tests logiciels) · [ Debrief Today (2 min) ]`
  3. **Tonight's Priority Task Capsule:** The most urgent preparation task is pinned with a permanently visible, high-contrast `[ ▶ START FOCUS (15m) ]` button. Zero mouse-wiggling required.

---

## 3. Data Architecture & Domain Model

### 3.1 `StudyTodo` Model
```python
@dataclass
class StudyTodo:
    id: str                                  # UUID or deterministic hash
    subject_name: str                        # e.g., "Entrepôts de données"
    title: str                               # e.g., "Fix ETL connection error in Lab 2"
    notes: str = ""                          # Context or slide references
    created_at: datetime = field(default_factory=datetime.now)
    due_date: datetime                       # Default: next occurrence of subject; or custom date
    status: str = "pending"                  # "pending" | "in_progress" | "completed"
    completed_at: datetime | None = None
    confidence: str | None = None            # "foggy" | "getting_there" | "solid"
    next_class_question: str | None = None   # Question formulated for next session
    session_ref_id: str | None = None        # Link to AcademicSession that originated the task
```

### 3.2 Relational Schema (`studystation.db`)
```sql
CREATE TABLE IF NOT EXISTS study_todos (
    id TEXT PRIMARY KEY,
    subject_name TEXT NOT NULL,
    title TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    completed_at TEXT,
    confidence TEXT,
    next_class_question TEXT,
    session_ref_id TEXT,
    FOREIGN KEY(subject_name) REFERENCES subject_targets(subject_name)
);

CREATE INDEX IF NOT EXISTS idx_todos_subject ON study_todos(subject_name);
CREATE INDEX IF NOT EXISTS idx_todos_status ON study_todos(status);
CREATE INDEX IF NOT EXISTS idx_todos_due ON study_todos(due_date);
```

### 3.3 Updated `StudyLog` Linking
The `study_logs` table adds an optional foreign key `todo_id TEXT REFERENCES study_todos(id)`. When focus is engaged on a specific todo, all completed minutes are credited to both the subject and the specific task.

---

## 4. Screen-by-Screen UI Specification

### Screen 1: The Main Screen — Weekly Schedule Grid 2.0 (The Cockpit)

The Weekly Schedule Grid becomes `INDEX_MAIN = 0` (the default home screen).

```
┌────────────────────────────────────────────────────────────────────────┐
│  WEEKLY SCHEDULE        ◄  12 – 17 OCT 2026  ► [Today]   21:42  [⚙] [⛶]│
│  ⚡ TODAY'S DEBRIEF: 2 classes attended today  [ Complete Check-in ]   │
│                                                                        │
│  TIME        LUN 12     MAR 13     MER 14     JEU 15*    VEN 16    SAM │
│ ────────────────────────────────────────────────────────────────────── │
│ 08h-09h30 ┌──────────┐┌──────────┐          ┌──────────┐          ┌───┐│
│           │Visualis. ││Cybercrim.│          │Sécurité  │          │...││
│           │Lab 20    ││SC 1      │          │Lab 5     │          └───┘│
│           │● 1 TODO  ││          │          │✓ PREPARED│          └───┘│
│           └──────────┘└──────────┘          └──────────┘               │
│ 09h40-11h10┌──────────┐                     ┌──────────┐               │
│           │Prévision │                     │Entrepôts │               │
│           │SC 3      │                     │SC 3      │               │
│           │⚠️ 2 TODOS │                     │● 1 TODO  │               │
│           └──────────┘                     └──────────┘               │
└────────────────────────────────────────────────────────────────────────┘
```

#### Key Capabilities of Grid 2.0:
1. **Live Todo Badges on Class Cards:**
   * Red/Amber badge (`● 2 TODOS`): Pending preparation tasks due before this class.
   * Emerald badge (`✓ PREPARED`): All preparation tasks for this class are complete.
   * Blue question badge (`❓ 1 QUESTION`): A formulated question is saved, ready to ask.
2. **Class Card Interaction:**
   * Clicking any class card opens the **Subject Preparation Sheet**, listing its todos, next session details, and questions.
3. **Integrated Nightly Banner:**
   * Noticeable, high-contrast banner if today has past sessions without completed debriefs.

---

### Screen 2: The Nightly Debrief Modal (`DebriefDialog`)

Triggered via the banner or keyboard shortcut <kbd>D</kbd> during evening hours.

```
┌────────────────────────────────────────────────────────────────────────┐
│  NIGHTLY DESK DEBRIEF — THURSDAY, OCT 15                               │
│  Review today's classes to prepare before they return next week.       │
│ ────────────────────────────────────────────────────────────────────── │
│                                                                        │
│  [1/2] ENTREPÔTS DE DONNÉES (Cours · 09:40)                            │
│  Next Class: Thursday, Oct 22 at 09:40 (in 7 days)                     │
│                                                                        │
│  What needs to be done / reviewed before next class?                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Fix Star Schema join exercise in Lab 2 script                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  Quick Type: [ Lab Fix ] [ Lecture Slides ] [ TD Exercises ] [ Project ]│
│                                                                        │
│  Deadline: (●) Next Class (Thu 22 Oct 09:40)   ( ) Specific Date [...] │
│                                                                        │
│  ────────────────────────────────────────────────────────────────────  │
│  [ + Add Another Task for this Subject ]                               │
│                                                                        │
│                                              [ Skip ]  [ Save & Next ] │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 3: Todo-Driven Focus Screen (`FocusWidget` 2.0)

When focus is engaged on a specific todo:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ENTREPÔTS DE DONNÉES                            │
│                  Task: Fix Star Schema join exercise                   │
│                                                                        │
│                               ╭───────╮                                │
│                             ╱   ● REC   ╲                              │
│                            │    14:52    │                             │
│                             ╲           ╱                              │
│                               ╰───────╯                                │
│                       Due: Next Thursday, 09:40                        │
│                                                                        │
│               [ Pause (Space) ]   [ +5m (+) ]   [ Finish (Esc) ]       │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 4: The Cognitive Exit Ticket (`ExitTicketDialog`)

Triggered on timer expiration or user finish:

```
┌────────────────────────────────────────────────────────────────────────┐
│  SESSION COMPLETE (+15 MIN)                                            │
│  Task: Fix Star Schema join exercise                                   │
│ ────────────────────────────────────────────────────────────────────── │
│                                                                        │
│  1. Did you complete this task?                                        │
│     [ ✓ Complete Task ]     [ +10m Need More Time ]     [ ⏸ Put Aside ]│
│                                                                        │
│  2. How confident do you feel about this material?                     │
│     [ 🔴 Foggy / Stuck ]     [ 🟡 Getting There ]     [ 🟢 Solid ]     │
│                                                                        │
│  3. Formulate 1 Question for Next Class (Optional):                    │
│     ┌──────────────────────────────────────────────────────────────┐   │
│     │ Why does the dimension table require a synthetic surrogate?  │   │
│     └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
│                                                      [ Done & Save ]   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Milestone Implementation Roadmap

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NEW MILESTONE ROADMAP                           │
├──────────────────────────┬─────────────────────────────────────────────┤
│ Milestone 10             │ Academic Todo Engine & Schema               │
│ (Core Domain)            │ Data models, SQLite table, CRUD repository, │
│                          │ and StudyLog attribution                    │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Milestone 11             │ Nightly Desk Debrief & Questionnaire        │
│ (Input Ritual)           │ Automatic evening check-in modal based on   │
│                          │ today's attended classes                    │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Milestone 12             │ Grid as Main Station (Academic Cockpit)     │
│ (The New Home Screen)    │ Interactive Weekly Grid as default view     │
│                          │ Class cards with live Todo & Question Badges│
├──────────────────────────┼─────────────────────────────────────────────┤
│ Milestone 13             │ Todo-Driven Focus & Cognitive Exit Ticket   │
│ (Focus & Comprehension)  │ Task-tethered focus, 🔴🟡🟢 confidence,    │
│                          │ Next Class Question formulation             │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Milestone 14             │ Night Routine Ambient UX & In-Class Payoff  │
│ (Desk Optimization)      │ Evening desk mode, always-ready hero task,  │
│                          │ "Questions for Today's Class" in-class HUD  │
└──────────────────────────┴─────────────────────────────────────────────┘
```

### Detailed Breakdown of Milestones:

#### Milestone 10: Academic Todo Engine & Schema `[NEXT]`
- [ ] Implement `StudyTodo` dataclass in `src/study_station/core/models.py`.
- [ ] Create `study_todos` SQLite table and migration logic in `database.py`.
- [ ] Implement repository operations in `repository.py` (`add_todo`, `update_todo`, `delete_todo`, `get_todos_by_subject`, `get_pending_todos`, `get_questions_by_subject`).
- [ ] Wire `ScheduleEngine` with todo helpers: `get_subject_pending_todos()`, `get_todos_due_before()`, `get_next_class_questions()`.
- [ ] Update `StudyLog` model to accept `todo_id: str | None`.
- [ ] Create comprehensive unit test suite in `tests/test_todo_engine.py`.

#### Milestone 11: Nightly Desk Debrief & Questionnaire
- [ ] Create `DebriefDialog` in `src/study_station/ui/debrief_dialog.py`.
- [ ] Auto-populate with today's completed classes via `ScheduleEngine.get_day_sessions(today.weekday())`.
- [ ] Implement multi-step questionnaire: "What was covered?" + "What needs preparation before next class?".
- [ ] Auto-calculate default deadline using `get_next_occurrence_of_subject(name, now)`.
- [ ] Batch-save generated `StudyTodo` items to repository.
- [ ] Add unit test suite in `tests/test_debrief_dialog.py`.

#### Milestone 12: Grid as Main Station (Academic Cockpit)
- [ ] Reconfigure `MainWindow` stack so `ScheduleScreenWidget` is the primary default view (`INDEX_MAIN = 0`).
- [ ] Retain flip clock in a balanced upper status band of the grid view.
- [ ] Upgrade grid class cards to render dynamic badges:
  - `● X TODOS` (amber if pending, red if due within 24h).
  - `✓ READY` (emerald if all tasks complete).
  - `❓ X QUESTIONS` (cyan badge if questions are logged).
- [ ] Build `SubjectPreparationSheet` (slide-out or modal): view, check off, or add tasks for any clicked class card.
- [ ] Add unit test coverage in `tests/test_grid_main_screen.py`.

#### Milestone 13: Todo-Driven Focus Loop & Cognitive Exit Ticket
- [ ] Update `FocusWidget` to accept an active `StudyTodo` alongside the subject name.
- [ ] Render the specific task title within the `FocusRingGaugeWidget` center hub.
- [ ] Build `ExitTicketDialog` in `src/study_station/ui/exit_ticket_dialog.py`:
  - Completion prompt: `[ Complete ]`, `[ +10m More ]`, `[ Put Aside ]`.
  - Confidence rating: 🔴 Foggy, 🟡 Getting There, 🟢 Solid.
  - Next Class Question input box (saved to `StudyTodo.next_class_question`).
  - 1-sentence Feynman takeaway (saved to `StudyTodo.notes`).
- [ ] Attribute focus minutes in `StudyLog` with `todo_id`.
- [ ] Add unit test suite in `tests/test_exit_ticket.py`.

#### Milestone 14: Night Routine Ambient UX & In-Class Payoff
- [ ] Implement evening desk mode logic in `MainWindow` (active after 18:00 local time).
- [ ] Display prominent debrief banner if today's sessions are un-debriefed.
- [ ] Add "Tonight's Priority Task" quick-action card above the grid with 1-click `[ START FOCUS ]`.
- [ ] In-class HUD view: when viewing today's current class (`● NOW`), display all questions formulated during night study sessions for immediate asking in class.
- [ ] Automated screen capture refresh across all new states in `docs/screens/`.

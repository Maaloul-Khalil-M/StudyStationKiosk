# Domain Model

Keep timetable facts separate from study-tracking behaviour.

## AcademicSession

Represents a scheduled class.

Core fields:

- `day` — day label (e.g. `Lun`, `Mar`, …)
- `timeSlot.start` — start time `HH:MM`
- `timeSlot.end` — end time `HH:MM`
- `subject.name` — module / subject name
- `subject.core` — session type (see below)
- `location` — room or lab

Supported session types in the initial model:

- `COURS` — theoretical lecture
- `TD` — Travaux Dirigés (tutorials / problem-solving)
- `TP` — Travaux Pratiques (practical / laboratory)
- `CI` — Cours Intégré (integrated theory + application)

Professor names and redundant class names are intentionally omitted to keep the object focused on what the application needs.

Example:

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

## StudyCycle

Represents the review period between two consecutive occurrences of the same subject.

Likely properties:

- `id`
- `subjectId` (or normalised subject key)
- `startAt` — when the relevant class has occurred and the cycle opens
- `endAt` — the next occurrence of the subject (when known)
- `targetMinutes`
- `status` — e.g. `active` or `closed`

`completedMinutes` can be derived from associated study logs rather than stored redundantly.

## StudyLog

Records a study session or manually entered study time.

Likely properties:

- `id`
- `subjectId`
- `studyCycleId` (where applicable)
- `startedAt`
- `endedAt` or `durationMinutes`
- `source` — e.g. `timer` or `manual`

## Schedule Engine

A shared, deterministic component that answers questions from the current local time and the normalised schedule. The UI only displays the results; it does not re-interpret the timetable.

Questions the engine must answer:

- Which class is happening now, if any?
- When is the next occurrence of a given subject?
- What study cycle is currently active for each subject?
- How many minutes have been logged toward the active cycle’s target?
- Which unfinished cycle should be suggested next?
- How much time remains before the next class (when useful)?

Conceptual data flow:

```
Timetable (manual entry or verified import)
            │
            ▼
   Normalised Schedule data
            │
            ▼
      Schedule Engine
   ╱         │          ╲
  ▼          ▼           ▼
Clock    Study Cycles   Focus Timer
             │              │
             ▼              ▼
        Study Progress ← Study Logs
```

## Notes on future extensions (not required for MVP)

- Stable session IDs
- Date-specific cancellations or timetable changes
- Timetable variants / exceptional weeks
- Explicit dates when a pure weekly day-of-week model is insufficient

These can be added later without changing the core cycle concept.

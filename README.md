# Study Station

A minimal, schedule-aware study companion for students.

Study Station turns a spare PC or laptop into an always-available study screen.  
It centres on a large, calm flip clock and uses the student’s weekly timetable to create **study cycles** between consecutive classes of the same subject. Short, flexible focus sessions count toward those cycles.

**Core promise**  
Help a student review material from one class before that subject returns, even when study time is short and irregular.

## Technology

- **UI framework**: PySide6 (Qt Widgets) + Qt Designer  
- **Language**: Python 3  
- **Persistence**: local (SQLite or simple files)  
- **Target platform**: Linux (Fedora / Xfce / X11), full-screen dedicated display  

No web browser, no Electron, no cloud accounts for the MVP.

## Project documents

| File | Purpose |
|------|---------|
| [docs/01-product-concept.md](docs/01-product-concept.md) | Product intent, problem, philosophy, screens |
| [docs/02-domain-model.md](docs/02-domain-model.md) | AcademicSession, StudyCycle, StudyLog, Schedule Engine |
| [docs/03-mvp-scope.md](docs/03-mvp-scope.md) | Strict MVP checklist and explicit non-goals |
| [docs/04-technology.md](docs/04-technology.md) | Stack decisions, hardware notes, packaging options |

## Current status

This repository contains the product and technical starting point only.  
No application code has been written yet.

## Guiding principles (short)

1. Time first — the clock is the visual centrepiece.  
2. One question per screen.  
3. Glanceable, not dashboard-heavy.  
4. Progress over perfection — short sessions count.  
5. No accumulating debt of missed minutes.  
6. Schedule-aware, not schedule-dominated.  
7. Deterministic core logic.  
8. Local-first MVP.  
9. Validate with real use.  
10. Keep complexity behind the clock.

See the individual docs for the full rationale.

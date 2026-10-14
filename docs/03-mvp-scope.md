# MVP Scope

The first version exists to test whether the study-cycle mechanism actually helps. It does not need every feature described in the original concept.

## Must have (MVP)

- [ ] Full-screen flip clock with 12/24-hour setting
- [ ] Manual weekly timetable entry (and the ability to correct entries)
- [ ] Current / next class detection where relevant
- [ ] Automatic study-cycle creation between consecutive occurrences of each subject
- [ ] Editable target review minutes per subject / cycle
- [ ] Flexible focus sessions: 5, 10, 15, 25 minutes
- [ ] Persistent study logging and cycle progress
- [ ] Minimal Focus screen and Completion confirmation
- [ ] Local data persistence (survives restart)
- [ ] Reliable timer recovery after refresh, restart or suspend/resume (store target end timestamp)
- [ ] Full-screen operation suitable for a dedicated display
- [ ] Low-friction start of a study session
- [ ] Recommendation of one useful next subject when multiple cycles are unfinished

## Explicitly out of scope for MVP

- PDF timetable parsing (can be added later with a verification step)
- Accounts and cloud synchronisation
- Social features / leaderboards
- Complex analytics or dashboards
- AI-generated schedules or in-app AI recommendations
- Elaborate task-management system
- Ambient sounds / advanced themes (basic theme is enough)
- Exam countdowns
- Companion mobile interface
- Automatic detection of study done away from the PC (simple manual entry is acceptable if needed)

## Success criteria for the first real-use experiment

Possible measurable indicators:

1. Study-cycle completion rate — percentage of cycles whose targets were reached before the next class.
2. Session-start rate — how often the app helps the student start a session when there is an opportunity.
3. Review consistency — number of days or occasions on which study time is recorded (no streak requirement).
4. Perceived preparedness — whether the student feels better prepared for the next lesson.
5. Reliability — timer state and study logs persist correctly across restarts and suspend/resume.

Avoid treating time spent looking at the screen as a success metric. The goal is better study behaviour, not more app engagement.

## Open product decisions (do not block MVP)

These can be answered through a prototype and real use:

1. How should review targets be set?  
   Start with fixed, adjustable minutes per subject/cycle.

2. How should the app recommend a subject?  
   A transparent rule using time until the next class and remaining minutes is a good baseline.

3. How prominent should progress be on the idle screen?  
   Start with one discreet secondary line.

4. Should students be able to log studying done away from the PC?  
   Simple manual entry is sufficient for the first version.

5. How will exceptional timetable changes be handled?  
   Manual correction is enough for a prototype.

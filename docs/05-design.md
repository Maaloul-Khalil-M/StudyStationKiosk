# Design — Study Station

This document explains **how the user interface will be designed and built** with the chosen technology (PySide6 + Qt Designer).  
It is written for someone who is new to Qt.

## 1. Two different ways of building UI in Qt

Qt gives you two complementary approaches. We will use **both**.

### A. Qt Designer (visual editor)

- You drag and drop buttons, labels, layouts, etc. onto a form.
- You save the result as a `.ui` file (XML).
- At runtime Python loads the `.ui` file (or you convert it to Python code once).
- Best for **ordinary screens**: settings, timetable editor, dialogs, confirmation messages.

**You do not write layout code by hand for these screens.**

### B. Custom painting (code)

- You subclass a Qt widget (usually `QWidget`) and override its `paintEvent`.
- You draw the pixels yourself with `QPainter` (text, rectangles, rounded digits, etc.).
- Best for the **flip clock** itself, because a real flip-clock look cannot be achieved with standard widgets.

**The large ambient clock will be custom-painted.**  
Everything else (Focus screen controls, settings, timetable form, etc.) can stay in Qt Designer.

This separation is intentional:

- Clock → maximum visual control, minimal widgets.
- Secondary screens → fast to design and change with the visual editor.

## 2. What Qt Designer actually is

Qt Designer is a standalone program (and also integrated in Qt Creator).

Typical workflow:

1. Open Qt Designer.
2. Create a new `Widget` or `Dialog`.
3. Drag widgets from the left panel (Label, PushButton, LineEdit, ComboBox, Layouts…).
4. Arrange them with layouts (Vertical, Horizontal, Grid, Form). Layouts are important — they make the UI resize cleanly.
5. Set object names, text, fonts, size policies in the property editor on the right.
6. Save as `something.ui`.
7. In Python you load it with `uic.loadUi("something.ui", self)` or convert it once with `pyside6-uic`.

You almost never position widgets with absolute x/y coordinates. You put them inside layouts and let Qt calculate the positions.

## 3. Visual direction (product decision)

**Default theme: Retro Minimal**

- Large white flip-clock digits on a black (or near-black) background.
- One discreet secondary line under the clock for subject + progress.
- Very few colours.
- No decorative borders, cards, or shadows on the ambient screen.
- Typography: clean, highly legible, preferably a monospace or tabular-figure font for the digits so they do not jump.

The ambient clock must remain readable from across the room on a 1366×768 screen.

Secondary screens (settings, timetable editor) can be slightly more conventional — still minimal, but they are allowed to look like normal desktop dialogs.

## 4. The three main screens (design intent)

### Screen 1 — Ambient Clock (default, full-screen)

**Question it answers:** What time is it, and how am I progressing?

Layout sketch (conceptual):

```
┌─────────────────────────────────────────────┐
│                                             │
│                                             │
│                  2 1 : 0 8                  │  ← large custom-painted digits
│                                             │
│                                             │
│         DATA VIS.  ·  25 / 60 MIN           │  ← one small secondary line
│                                             │
└─────────────────────────────────────────────┘
```

- Almost the entire window is the clock.
- Secondary line is small, low-contrast, and can be hidden if there is nothing useful to show.
- No buttons visible in the normal state (interaction can be via keyboard shortcuts or a single click that reveals a thin control bar).
- This screen is **not** built in Qt Designer. It is a custom `QWidget` with its own `paintEvent`.

### Screen 2 — Focus

**Question it answers:** What am I working on right now?

- Large remaining time.
- Subject name.
- Simple state label (“Focusing”, “Paused”…).
- Three or four large, easy-to-hit controls: Pause / Resume, +5 min, End session.
- Can be designed mostly in Qt Designer (or a mix: Designer for the controls, custom painting for the big countdown if desired).

### Screen 3 — Completion

**Question it answers:** Did my effort count?

- Short confirmation: `+10 MIN`
- Updated progress: `35 / 60 MIN COMPLETED`
- Automatically returns to the Ambient Clock after a few seconds or on any key/click.
- Very simple — ideal for Qt Designer.

## 5. Secondary screens (all good candidates for Qt Designer)

These are shown only when the user deliberately opens them:

- Timetable editor (list or table of sessions + add/edit form)
- Subject / target settings (list of subjects + target minutes)
- Manual study-time entry
- Basic preferences (12/24 h, etc.)

They should follow normal desktop conventions: clear labels, OK/Cancel or Apply buttons, keyboard navigable. They do **not** need to look like the ambient clock.

## 6. Practical rules for this project

1. **Ambient clock = custom painting.** Do not try to fake a flip clock with standard labels and stylesheets only.
2. **Everything else = prefer Qt Designer.** It is faster and easier to iterate.
3. **One question per screen.** If a screen starts answering two questions, split it.
4. **Layouts, not absolute positions.** Always put widgets inside `QVBoxLayout`, `QHBoxLayout` or `QGridLayout`.
5. **Object names matter.** Give every important widget a clear object name in Designer (`btnPause`, `lblRemaining`, …). You will use those names from Python.
6. **Keep the ambient screen empty of chrome.** No menu bar, no status bar, no window frame if we go true full-screen.
7. **Test on the real 1366×768 screen early.** What looks fine on a large monitor can feel cramped or too small on the target machine.

## 7. What you do *not* need to learn yet

- QML / Qt Quick (that is a completely different UI technology)
- Complex stylesheets or CSS-like theming for the clock
- Graphics View framework
- OpenGL

For the MVP you only need:

- Basic widgets + layouts in Qt Designer
- Loading a `.ui` file from Python
- Subclassing `QWidget` and using `QPainter` for the clock digits
- Simple signals and slots (button clicked → call a Python method)

## 8. Suggested order of design work

1. Make a full-screen black window that stays on top (or true full-screen).
2. Draw the current time with `QPainter` in large digits (even if they are not yet “flipping”).
3. Add the secondary progress line.
4. Only then open Qt Designer and build the Focus and Completion screens.
5. Wire the buttons to the timer logic.
6. Add the settings / timetable editor last.

This order keeps the most important surface (the ambient clock) working first and avoids getting lost in form design.

## 9. Glossary (Qt terms you will meet)

| Term | Meaning |
|------|---------|
| Widget | Any UI element (window, button, label, custom clock…) |
| Layout | Invisible manager that positions and resizes child widgets |
| `.ui` file | XML file saved by Qt Designer |
| `uic` | Tool that turns a `.ui` file into Python code (or loads it at runtime) |
| Signal / Slot | Qt’s way of connecting events (button clicked) to functions |
| `paintEvent` | Method you override to draw custom content |
| `QPainter` | The drawing tool used inside `paintEvent` |
| Full-screen | Window that covers the entire screen, usually without decorations |

---

You do not need to become a Qt expert before starting.  
The design approach above deliberately keeps the hard visual part (the clock) isolated and the rest of the UI ordinary and Designer-friendly.

# Technology Decisions

## Chosen stack

| Layer            | Choice                          | Reason |
|------------------|----------------------------------|--------|
| Language         | Python 3                         | Familiarity, rapid iteration, good Qt bindings |
| UI framework     | PySide6 (Qt Widgets)             | Native full-screen, excellent painting control for the flip clock, reliable timers and event loop, low ongoing resource use |
| UI design tool   | Qt Designer                      | Fast layout of the few secondary screens (settings, timetable editor, etc.) |
| Persistence      | Local (SQLite preferred, or simple files) | No accounts, no cloud for MVP; survives restarts |
| Packaging (MVP)  | Python virtual environment + pip | Simplest for a single known Linux machine; freeze only if measurements justify it |

**Explicitly rejected for MVP**

- Browser / PWA / Electron / Tauri — unnecessary resource cost for an always-on dedicated display and more fragile suspend/resume behaviour.
- Full C++ Qt — lower runtime cost but higher development friction for the current scope.
- Any cloud backend or account system.

## Hardware and OS context (target machine)

- Fedora (recent), 64-bit, Xfce, X11
- ~4 GB RAM
- 5400 RPM HDD (cold start is the main risk)
- Intel i3-4005U + HD 4400
- Screen: 1366 × 768
- Laptop → lid-close, screen blanking and suspend/resume are normal daily events

Implications:

- 4 GB is comfortable for a small Qt Widgets application.
- Cold start (Python + Qt libraries from disk) is the likeliest slow point; measure it.
- The GPU is more than adequate; software rendering is fine. No OpenGL required.
- Timestamp-based timer recovery is a daily requirement, not an edge case.
- Prefer `PySide6-Essentials` over the full meta-package to keep the footprint smaller.

## Compatibility notes for PySide6 on this machine

- Qt’s prebuilt binaries require a reasonably recent glibc (Fedora is fine).
- PySide6 current releases support a range of Python 3 versions that should include Fedora’s default; verify with `python3 --version`.
- Common first-run issue on X11: missing `xcb-util-cursor` package → “could not load the xcb platform plugin”. Install it if the error appears.
- Fedora is not on Qt’s official “tested” Linux list, but PySide6 is widely used on Fedora.

## Packaging options (decide after measurement)

1. Plain virtual environment + `pip install PySide6-Essentials` (recommended starting point).
2. Fedora’s own PySide6 packages if the repositories carry a suitable version.
3. Frozen binary (PyInstaller / Nuitka / similar) only if cold-start or dependency management becomes painful.

Keep PDF parsing (and any heavy optional libraries) out of the always-on process.

## Reliability requirements that affect the stack

- Store timer target end timestamps; recalculate remaining time on wake / resume / restart.
- Persist study logs so completed work is never lost.
- Keep all time calculations in the machine’s local clock; be careful with system time changes.
- The schedule engine and cycle logic must be pure and deterministic (easy to unit-test without the UI).

## What this document deliberately does not decide

- Exact project layout / package structure
- Choice of SQLite vs JSON files vs other local store
- Concrete recommendation algorithm for “next subject”
- Visual theme implementation details beyond the Retro Minimal direction
- Whether a frozen binary will ultimately be needed

Those decisions can be made once a minimal full-screen clock + timer is running and measurements exist.

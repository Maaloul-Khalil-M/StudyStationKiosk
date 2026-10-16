# Linux OS-Level Hardening & Kiosk Appliance Architecture

## 1. Overview and Threat Model

While application-level password protection successfully guards window borders, full-screen toggles, and internal navigation, software running on a general-purpose operating system remains subject to the surrounding desktop environment. 

A user with physical access to a keyboard and mouse can attempt to bypass a full-screen window through system-level operations:
- Switching to Linux text virtual consoles
- Triggering desktop environment shell shortcuts (such as application menus, task switchers, or process managers)
- Issuing kernel-level emergency combinations
- Inserting external media that triggers auto-mounting file managers
- Allowing the operating system to enter power-saving suspend or screen-lock states that require standard desktop credentials

Transforming a Linux Fedora workstation into a resilient, tamper-resistant academic kiosk requires establishing clear boundaries across five structural layers: user permissions, display serving, input interception, process supervision, and power discipline.

---

## 2. Dedicated Least-Privilege Identity

A dedicated kiosk machine should never execute under a personal desktop user account or an administrative profile.

### User Account Isolation
- The station must run under a dedicated, unprivileged user profile created specifically for kiosk duties.
- This account must be stripped of administrative privileges, wheel group membership, and passwordless elevation capabilities.
- The user account should have automatic login configured so that physical machine power-on directly initializes the study station without a preliminary desktop display manager login prompt.

### Storage and File System Restrictions
- Write permissions for the kiosk identity should be restricted strictly to the designated application data directories.
- Critical system binaries, system configuration hierarchies, and foreign user home directories should remain completely inaccessible for writing or execution by the kiosk user.

---

## 3. Display Server Architecture: Wayland vs. Bare X11

The choice of display architecture determines how windowing, focus trapping, and desktop containment are enforced. Traditional desktop environments (such as GNOME Shell or Xfce) carry hundreds of background services, hotkeys, and notification panels that complicate kiosk lockdown. Bypassing the desktop environment entirely is the most robust approach.

### The Recommended Modern Approach: Wayland Dedicated Kiosk Compositor
Modern Fedora distributions run Wayland by default. In a standard desktop, the compositor is part of a complex shell. For an appliance, the recommended pattern is replacing the desktop shell with a dedicated kiosk compositor, such as Cage:
- Single-Window Discipline: A kiosk compositor accepts exactly one application and forces it to occupy the entire screen dimensions. There are no title bars, no minimizations, no background wallpapers, and no multi-window taskbars.
- Architectural Security: Wayland protocols strictly isolate graphical clients. Unlike legacy display servers, one application cannot inspect the input, monitor keypresses, or inject events into another application.
- Absence of Desktop Shells: Because no desktop environment is running behind the compositor, concepts like application launchers, panel applets, notification toasts, and window switcher menus do not exist in the session.

### The Legacy Alternative: Minimal Standalone X11 Session
On systems utilizing legacy X11:
- The graphical server is started directly with the application as the session leader, rather than launching a desktop environment.
- No desktop panel or file manager is started in the session startup script.
- If window management is required, a minimal, non-interactive window manager configured with zero keybindings is used. Without a desktop panel or desktop hotkeys, ordinary window escape vectors are eliminated.

---

## 4. Virtual Terminal and Physical Keyboard Suppression

Linux systems maintain multiple virtual consoles (TTYs) accessible via keyboard shortcuts. On a public or shared kiosk workstation, an inquisitive user could attempt to switch away from the graphical screen to a virtual console.

### Virtual Console Allocation
- Operating system session managers dynamically allocate virtual text terminals on demand.
- In a kiosk appliance configuration, automatic virtual terminal allocation should be disabled in the system session configuration.
- The system should be restricted to reserving only the single graphical terminal hosting the station, preventing console switching upon keypress.

### Kernel Emergency Operations (SysRq)
- The Linux kernel provides a low-level diagnostic mechanism known as the Magic System Request (SysRq) key combination.
- On a hardened machine, this low-level interface should be disabled via kernel system parameters, preventing physical keyboard combinations from abruptly killing active processes, remounting disks, or forcing an immediate reboot.

---

## 5. Process Lifecycle Supervision and Self-Healing

An appliance must be resilient against unexpected application exits, unhandled errors, or external signals.

### Service Supervision
- The study station should run under supervision of a system service manager configured at either the system or user level.
- Supervision guarantees that if the process exits for any reason (whether from an internal exception, an administrative close, or an external signal), the supervisor immediately relaunches the station in full-screen mode within seconds.
- Continuous restart limits and restart delays ensure the system remains stable without entering runaway restart loops.

### Dependency Ordering
- The service manager handles rigorous startup sequencing: initializing local storage, waiting for sound subsystems (such as PipeWire or PulseAudio), ensuring the display server socket is active, and only then launching the user interface.
- Upon system shutdown or restart, the service manager ensures SQLite databases receive clean shutdown notifications to guarantee write-ahead log integrity.

---

## 6. Desktop Shortcut and Shell Masking

If Study Station is deployed within a full desktop environment (such as GNOME, Xfce, or KDE) rather than a standalone compositor, active hotkey masking is required.

### Key Combination Interception
- Application Menu Keys: The Super (Windows) key must be unbound from triggering system application overviews or start menus.
- Window Management Keys: Standard window closure, minimization, and un-maximization keys must be stripped from the window manager settings.
- Task Switching: The task switcher combination must be disabled so users cannot cycle to background tasks or launch dialogs.
- System Action Keys: The standard attention combination for rebooting or task management must be masked to prevent triggering logout prompts or display manager restart screens.

### Cursor and Touch Feedback
- In an appliance context, mouse cursor visibility can be automatically suppressed during idle states.
- Context menus, right-click actions on desktop backgrounds, and edge-swipe gestures on touchscreens should be disabled at the window manager or touch driver layer.

---

## 7. Peripheral and Storage Discipline

Shared workstations in study halls or university desks are exposed to arbitrary peripheral connections.

### Removable Storage Handling
- Standard desktop environments automatically mount inserted USB flash drives and open graphical file browsers.
- On a kiosk installation, storage automount services should be disabled. The operating system must ignore newly connected USB mass storage devices to prevent unauthorized file browser windows from covering the academic screen.

### Network and Device Discovery
- Network configuration panels and wireless discovery notifications should be suppressed from displaying interactive prompts on the screen.
- Network connectivity should be configured at the system level so individual workstation users cannot disconnect or reconfigure interfaces.

---

## 8. Power Management and Continuous Display Discipline

Study Station is designed as an ambient, glanceable desk cockpit featuring an active split-flap clock and dynamic academic banners. Power management must align with this continuous operational model.

### Display Power Management (DPMS)
- Operating systems typically blank the screen or enter monitor power-down mode after ten to fifteen minutes of user inactivity.
- For a dedicated desk appliance, screen blanking and display sleep timers should be disabled in the display server configuration so the clock and timetable remain visible at all times.

### System Suspension and Hibernation
- System-wide sleep, suspension, and hibernation timers must be disabled.
- Power button behavior should be configured to ignore short presses or require sustained physical holding, preventing accidental session interruptions when students adjust the physical screen or desk workstation.

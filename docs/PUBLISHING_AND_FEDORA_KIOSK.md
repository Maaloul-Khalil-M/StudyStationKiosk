# Publishing to PyPI & Linux Fedora Kiosk Deployment Guide

This guide walks through:
1. **Publishing Study Station as a `pip` package** on PyPI.
2. **Deploying the app as a self-healing Kiosk** on Linux Fedora using user-space automation (no root or OS kernel hardening required).

---

## Part 1: Publishing to PyPI (Online Distribution)

The project includes standard PEP 517/518 build configuration ([`pyproject.toml`](../pyproject.toml)) and pre-built distribution archives in `dist/`.

### 1. Build Verification
Both source distribution (`.tar.gz`) and binary wheel (`.whl`) are validated:
```bash
# Validate metadata and README formatting
python -m twine check dist/*
```
*Expected output: `PASSED` for both `.whl` and `.tar.gz`.*

### 2. Test on TestPyPI (Recommended First Step)
To verify everything installs cleanly without affecting the official namespace:
```bash
python -m twine upload --repository testpypi dist/*
```
*You will be prompted for your TestPyPI API token (`__token__` username and your `pypi-...` password).*

Test installing from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple study-station
```

### 3. Publish to Official PyPI
Once satisfied, upload the distribution to PyPI:
```bash
python -m twine upload dist/*
```

Anyone worldwide (including your Fedora machine) can now install Study Station with:
```bash
pip install study-station
```
And launch it from the terminal via:
```bash
study-station
```

---

## Part 2: Deploying as a Kiosk on Linux Fedora (No OS-Level Hardening)

This setup uses user-space systemd supervision and the internal application password lock. It requires **no root permissions**, **no kernel modifications**, and **no display manager reconfiguration**.

### How It Works
1. **Application-Level Lock**: Prevents users from un-maximizing (<kbd>F11</kbd>), closing the window (<kbd>Q</kbd>, <kbd>Esc</kbd>, Alt+F4), or tampering with settings without entering your kiosk password.
2. **Systemd User Supervision (`study-station-kiosk.service`)**: Runs in the student's normal user session. If the app is ever killed, crashes, or closes, systemd automatically relaunches it in fullscreen mode in 2 seconds.
3. **Session Autostart**: Launches automatically when the user logs in or boots up the machine.

---

### Method A: Single-Command Automated Setup (Recommended)

Copy or clone the repository to your Fedora machine, then run:

```bash
chmod +x scripts/setup_fedora_kiosk.sh
./scripts/setup_fedora_kiosk.sh
```

The script will automatically:
- Install or upgrade `study-station` into `~/.local/bin/` via pip.
- Install the auto-restart runner script `~/.local/bin/study-station-kiosk-run`.
- Register and start the systemd user service `study-station-kiosk.service`.
- Create the desktop autostart entry `~/.config/autostart/study-station.desktop`.

---

### Method B: Manual Setup from Pip (Direct on Fedora)

If you installed via `pip install study-station` without cloning the repository, perform these 3 simple steps:

#### 1. Install Study Station
```bash
python3 -m pip install --user study-station
```

#### 2. Create the Systemd User Service
Create `~/.config/systemd/user/study-station-kiosk.service`:
```ini
[Unit]
Description=Study Station Kiosk Application
After=graphical-session.target sound.target network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/study-station
Restart=always
RestartSec=2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

#### 3. Enable and Start the Service
```bash
systemctl --user daemon-reload
systemctl --user enable --now study-station-kiosk.service
```

---

## Part 3: Controlling & Managing the Kiosk

You can manage the kiosk service at any time through standard user systemctl commands:

| Action | Command |
|:---|:---|
| **Start Kiosk** | `systemctl --user start study-station-kiosk` |
| **Stop Kiosk (for maintenance)** | `systemctl --user stop study-station-kiosk` |
| **Restart Kiosk** | `systemctl --user restart study-station-kiosk` |
| **Check Status** | `systemctl --user status study-station-kiosk` |
| **Inspect Live Logs** | `journalctl --user -u study-station-kiosk -f` |
| **Disable Autostart** | `systemctl --user disable study-station-kiosk` |

---

## Part 4: Setting the Kiosk Password in the UI

Once Study Station launches on your Fedora machine:
1. Click **⚙** in the top right header (or press <kbd>C</kbd>).
2. Scroll to **Section 6: KIOSK & SCREEN LOCK**.
3. Check **Enable Kiosk Mode (Exit & Fullscreen Protection)**.
4. Set an administrator password (e.g., your desk PIN).
5. Click **Save Password**.

Now:
- <kbd>F11</kbd> will prompt for password before leaving fullscreen.
- <kbd>Q</kbd>, <kbd>Esc</kbd>, and Alt+F4 will prompt for password before closing.
- Pressing <kbd>L</kbd> will lock the screen instantly with a full-screen shield overlay.
- If someone forces the window closed, systemd will relaunch it fullscreen in 2 seconds.

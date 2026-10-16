#!/usr/bin/env bash
# ==============================================================================
# Study Station — Fedora Kiosk Setup & Autostart Script
# ==============================================================================
# Configures a Linux Fedora machine to run the pip-installed Study Station
# app as a continuous, self-healing kiosk application.
#
# No root/sudo required — installs cleanly into user space via systemd user services.
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Study Station — Linux Fedora Kiosk Setup           ${NC}"
echo -e "${BLUE}======================================================${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

# 1. Verify Python & Pip
echo -e "\n${GREEN}[1/5] Checking Python environment...${NC}"
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}ERROR: python3 is not installed.${NC} Please run: sudo dnf install python3 python3-pip"
    exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "Found Python ${PYTHON_VER}."

# 2. Install or upgrade study-station via pip
echo -e "\n${GREEN}[2/5] Installing Study Station via pip...${NC}"
install_pkg() {
    local target="$1"
    if python3 -m pip install --user --upgrade "${target}" 2>/dev/null; then
        return 0
    elif python3 -m pip install --user --break-system-packages --upgrade "${target}" 2>/dev/null; then
        return 0
    elif command -v pipx >/dev/null 2>&1; then
        pipx install "${target}" --force
        return 0
    else
        python3 -m pip install --user "${target}"
    fi
}

if [ -f "${PROJECT_ROOT}/pyproject.toml" ]; then
    echo "Installing from local repository directory..."
    install_pkg "${PROJECT_ROOT}"
else
    echo "Installing latest version from PyPI..."
    install_pkg "study-station"
fi

# Ensure user binary path is available
USER_BIN="${HOME}/.local/bin"
export PATH="${USER_BIN}:${PATH}"

if command -v study-station >/dev/null 2>&1; then
    EXECUTABLE_PATH="$(command -v study-station)"
else
    EXECUTABLE_PATH="${USER_BIN}/study-station"
fi
echo -e "Study Station executable resolved at: ${BLUE}${EXECUTABLE_PATH}${NC}"

# 3. Create Runner Script
echo -e "\n${GREEN}[3/5] Installing Kiosk Runner script...${NC}"
RUNNER_PATH="${USER_BIN}/study-station-kiosk-run"
mkdir -p "${USER_BIN}"

cat > "${RUNNER_PATH}" << 'EOF'
#!/usr/bin/env bash
export PATH="${HOME}/.local/bin:${PATH}"

# Detect binary
if command -v study-station >/dev/null 2>&1; then
    BIN="study-station"
else
    BIN="python3 -m study_station.main"
fi

# Wait for display server socket
while [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; do
    sleep 1
done

# Continuous auto-restart loop
while true; do
    ${BIN}
    EXIT_CODE=$?
    # Exit loop on SIGTERM or Ctrl+C
    if [ ${EXIT_CODE} -eq 143 ] || [ ${EXIT_CODE} -eq 130 ]; then
        break
    fi
    sleep 2
done
EOF
chmod +x "${RUNNER_PATH}"
echo -e "Kiosk runner installed to ${RUNNER_PATH}"

# 4. Set up Systemd User Service (Self-Healing Autostart)
echo -e "\n${GREEN}[4/5] Setting up systemd user service...${NC}"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
mkdir -p "${SYSTEMD_USER_DIR}"

SERVICE_FILE="${SYSTEMD_USER_DIR}/study-station-kiosk.service"
cat > "${SERVICE_FILE}" << EOF
[Unit]
Description=Study Station Kiosk Application
After=graphical-session.target sound.target network.target

[Service]
Type=simple
ExecStart=${RUNNER_PATH}
Restart=always
RestartSec=2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable study-station-kiosk.service
echo -e "Systemd user service registered & enabled: ${BLUE}${SERVICE_FILE}${NC}"

# 5. Set up XDG Desktop Autostart Entry (Desktop Fallback)
echo -e "\n${GREEN}[5/5] Configuring desktop session autostart...${NC}"
AUTOSTART_DIR="${HOME}/.config/autostart"
mkdir -p "${AUTOSTART_DIR}"

DESKTOP_AUTOSTART="${AUTOSTART_DIR}/study-station.desktop"
cat > "${DESKTOP_AUTOSTART}" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Study Station
GenericName=Academic Kiosk Cockpit
Comment=Schedule-Aware Academic Cockpit & Focus Workstation
Exec=${EXECUTABLE_PATH}
Terminal=false
Categories=Education;Utility;
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF
chmod +x "${DESKTOP_AUTOSTART}"
echo -e "Desktop autostart entry written to ${DESKTOP_AUTOSTART}"

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}   Setup Complete! Study Station Kiosk is Ready      ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "\nControl commands:"
echo -e "  Start Kiosk now:     ${YELLOW}systemctl --user start study-station-kiosk${NC}"
echo -e "  Stop Kiosk:          ${YELLOW}systemctl --user stop study-station-kiosk${NC}"
echo -e "  Check Kiosk status:  ${YELLOW}systemctl --user status study-station-kiosk${NC}"
echo -e "  View live logs:      ${YELLOW}journalctl --user -u study-station-kiosk -f${NC}"
echo -e "\nOn next login / boot, Study Station will launch automatically in fullscreen mode!"

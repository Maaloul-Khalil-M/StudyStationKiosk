#!/usr/bin/env bash
# ==============================================================================
# Study Station — Dedicated Kiosk Runner for Linux Fedora
# ==============================================================================
# This script launches Study Station in full-screen mode and automatically
# relaunches it if the application exits, crashes, or is restarted.
# ==============================================================================

set -u

echo "[Study Station] Initializing kiosk runner..."

# 1. Resolve python and study-station executable
KIOSK_BIN=""

if command -v study-station >/dev/null 2>&1; then
    KIOSK_BIN="$(command -v study-station)"
elif [ -f "${HOME}/.local/bin/study-station" ]; then
    KIOSK_BIN="${HOME}/.local/bin/study-station"
elif [ -f "${HOME}/.venv/bin/study-station" ]; then
    KIOSK_BIN="${HOME}/.venv/bin/study-station"
fi

# Fallback: run via python module directly
if [ -z "${KIOSK_BIN}" ]; then
    if command -v python3 >/dev/null 2>&1; then
        KIOSK_BIN="python3 -m study_station.main"
    else
        echo "[Study Station] ERROR: Neither 'study-station' nor 'python3' was found in PATH." >&2
        exit 1
    fi
fi

echo "[Study Station] Using executable: ${KIOSK_BIN}"

# 2. Ensure Display socket is ready (X11 or Wayland)
MAX_WAIT=30
WAITED=0
while [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; do
    if [ ${WAITED} -ge ${MAX_WAIT} ]; then
        echo "[Study Station] WARNING: Display server not detected after ${MAX_WAIT}s. Proceeding anyway..."
        break
    fi
    echo "[Study Station] Waiting for display server socket..."
    sleep 1
    WAITED=$((WAITED + 1))
done

# 3. Continuous Kiosk Loop (Auto-restart on unexpected exit)
RESTART_DELAY=2

while true; do
    echo "[Study Station] Launching Study Station in fullscreen mode..."
    
    # Run the application
    ${KIOSK_BIN}
    EXIT_CODE=$?

    echo "[Study Station] Process exited with code ${EXIT_CODE}."

    # If intentionally stopped via SIGTERM (kill), break loop
    if [ ${EXIT_CODE} -eq 143 ] || [ ${EXIT_CODE} -eq 130 ]; then
        echo "[Study Station] Termination signal received. Stopping kiosk runner."
        break
    fi

    echo "[Study Station] Relaunching station in ${RESTART_DELAY} seconds..."
    sleep ${RESTART_DELAY}
done

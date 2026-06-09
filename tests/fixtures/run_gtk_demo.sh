#!/usr/bin/env bash
# Launch GTK demo for live AT-SPI control tests (GNOME Wayland needs X11 backend).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DISPLAY="${DISPLAY:-:0}"
export GTK_A11Y=1
export NO_AT_BRIDGE=0
export GDK_BACKEND=x11

exec /usr/bin/python3 "${SCRIPT_DIR}/gtk_demo_app.py"

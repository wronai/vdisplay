#!/usr/bin/env bash
# Run mirror demo on the host (required on GNOME Wayland).
# Docker ./run.sh forwards only the X11 socket and yields black PNGs on Wayland.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VDISPLAY_ROOT="$(cd "$ROOT/../.." && pwd)"
cd "$ROOT"

export VD_OUTPUT_DIR="${VD_OUTPUT_DIR:-$ROOT/output}"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-${HOME}/.Xauthority}"

if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
  echo "Wayland session: capture routes via vdisplay-agent + ScreenCast." >&2
  echo "Start broker: vdisplay agent serve" >&2
  echo "Then once:    vdisplay agent screencast start" >&2
fi

if ! python3 -c "import vdisplay" 2>/dev/null; then
  pip install -e "$VDISPLAY_ROOT[pillow]"
fi

mkdir -p "$VD_OUTPUT_DIR"
python3 "$ROOT/mirror_demo.py"

#!/usr/bin/env bash
# Run relay demo on the host session (required on GNOME Wayland).
# Docker ./run.sh uses X11 forwarding and produces black screenshots on Wayland.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VDISPLAY_ROOT="$(cd "$ROOT/../.." && pwd)"
cd "$ROOT"

export VD_OUTPUT_DIR="${VD_OUTPUT_DIR:-$ROOT/output}"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-${HOME}/.Xauthority}"

if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
  echo "Wayland session: capture uses gnome-screenshot/portal (not xwd/scrot)." >&2
  echo "Grant Screen Recording if prompted (Settings → Privacy)." >&2
fi

if ! python3 -c "import vdisplay" 2>/dev/null; then
  pip install -e "$VDISPLAY_ROOT[pillow]"
fi

mkdir -p "$VD_OUTPUT_DIR"
python3 "$ROOT/relay_demo.py"

#!/usr/bin/env bash
# One-time setup for autonomy loop (vision OCR + optional Cursor map).
#
# Usage:
#   bash examples/dev-workflow/setup-autonomy.sh
#   bash examples/dev-workflow/setup-autonomy.sh --build-map

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BUILD_MAP=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --build-map) BUILD_MAP="1" ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

if [[ -f "${ROOT}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
fi

export PYTHONPATH="${PYTHONPATH:-src:packages/vdisplay-agent/src}"

echo "Installing autonomy extras (observe=imgl+vql, vision OCR, auto planfile)…"
pip install -e ".[observe,auto,vision,dev]" -e "packages/vdisplay-agent[serve]"

if ! command -v tesseract >/dev/null 2>&1; then
  echo ""
  echo "warning: system tesseract not found — install for OCR:"
  echo "  sudo apt install tesseract-ocr   # Debian/Ubuntu"
fi

echo ""
echo "Vision deps OK. Test OCR path:"
echo "  vdisplay control find --backend vision --vision-anchor Ask --source DP-1"

MAP_OUT="${ROOT}/maps/cursor-chat.json"
if [[ -n "${BUILD_MAP}" ]]; then
  echo ""
  echo "Building Cursor chat map on DP-1 → ${MAP_OUT}"
  echo "Ensure Cursor chat is visible on DP-1, then confirm crop bounds if prompted."
  vdisplay map build --monitor DP-1 -o "${MAP_OUT}"
else
  echo ""
  echo "Optional: build Cursor map (fallback when OCR misses anchors):"
  echo "  bash examples/dev-workflow/setup-autonomy.sh --build-map"
  echo "  # or: vdisplay map build --monitor DP-1 -o maps/cursor-chat.json"
fi

echo ""
echo "Run autonomy planfile:"
echo "  export VDISPLAY_AGENT_URL=http://127.0.0.1:8765"
echo "  export VDISPLAY_OBSERVE=1"
echo "  vdisplay auto --project . --planfile examples/dev-workflow/planfile-autonomy.yaml --source yaml run"

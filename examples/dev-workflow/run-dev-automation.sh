#!/usr/bin/env bash
# Run vdisplay dev-workflow automation on the local GNOME Wayland host.
#
# Usage:
#   Terminal 1: vdisplay-agent serve
#   Terminal 2: bash examples/dev-workflow/run-dev-automation.sh
#
# Options:
#   --dry-run   List tasks without executing
#   --max N     Run at most N tasks (default: all pending)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

export VDISPLAY_AGENT_URL="${VDISPLAY_AGENT_URL:-http://127.0.0.1:8765}"
export PYTHONPATH="${PYTHONPATH:-src:packages/vdisplay-agent/src}"

PLANFILE="examples/dev-workflow/planfile.yaml"
DRY_RUN=""
MAX=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN="--dry-run" ;;
    --max) MAX="--max $2"; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

if ! curl -sf --max-time 3 "${VDISPLAY_AGENT_URL}/health" >/dev/null 2>&1; then
  echo "error: vdisplay-agent unreachable at ${VDISPLAY_AGENT_URL}" >&2
  echo "Start Terminal 1: vdisplay-agent serve" >&2
  exit 1
fi

echo "vdisplay dev-workflow — project=${ROOT}"
echo "agent: ${VDISPLAY_AGENT_URL}"
echo ""

if [[ -n "${DRY_RUN}" ]]; then
  vdisplay auto --project "$ROOT" --planfile "$PLANFILE" list
  exit 0
fi

# Ensure screencast is active (non-interactive if already running)
if ! vdisplay agent screencast status 2>/dev/null | grep -q '"ready": true'; then
  echo "screencast not ready — starting (choose All Screens in portal dialog)…"
  vdisplay agent screencast start --force
fi

vdisplay auto --project "$ROOT" --planfile "$PLANFILE" --source yaml run ${MAX:-}

echo ""
echo "Screenshots:"
ls -lh /tmp/vdisplay-dev-*.png 2>/dev/null || true

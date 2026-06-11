#!/usr/bin/env bash
# Run vdisplay dev-workflow automation on the local GNOME Wayland host.
#
# Usage:
#   Terminal 1: vdisplay-agent serve
#   Terminal 2: bash examples/dev-workflow/run-dev-automation.sh
#
# Options:
#   --dry-run   List tasks without executing
#   --reset     Reset planfile tasks to todo before running
#   --max N     Run at most N tasks (default: all pending)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

export VDISPLAY_AGENT_URL="${VDISPLAY_AGENT_URL:-http://127.0.0.1:8765}"
export PYTHONPATH="${PYTHONPATH:-src:packages/vdisplay-agent/src}"

PLANFILE="examples/dev-workflow/planfile.yaml"
DRY_RUN=""
MAX=""
RESET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN="--dry-run" ;;
    --reset) RESET="1" ;;
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

if [[ -n "${RESET}" ]]; then
  reset_count="$(python3 -c "
from pathlib import Path
from vdisplay.application.auto.tasks import reset_yaml_automation_tasks
print(reset_yaml_automation_tasks(Path('${PLANFILE}')))
")"
  echo "reset ${reset_count} planfile task(s) to todo"
  echo ""
fi

if [[ -n "${DRY_RUN}" ]]; then
  vdisplay auto --project "$ROOT" --planfile "$PLANFILE" --source yaml list
  exit 0
fi

# Ensure screencast is active
if ! vdisplay agent screencast status 2>/dev/null | grep -qE '"ready"[[:space:]]*:[[:space:]]*true'; then
  echo "screencast not ready — starting (choose All Screens in portal dialog)…"
  vdisplay agent screencast start --force
fi

result="$(vdisplay auto --project "$ROOT" --planfile "$PLANFILE" --source yaml run ${MAX:-})"
echo "$result"

executed_count="$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('executed') or []))")"
if [[ "${executed_count}" == "0" ]]; then
  echo ""
  echo "note: no pending tasks (all done). Re-run with: bash examples/dev-workflow/run-dev-automation.sh --reset"
fi

echo ""
echo "Screenshots:"
ls -lh /tmp/vdisplay-dev-*.png 2>/dev/null || true

# LLM-assisted decide for autonomy (using .env for OpenRouter gemini image preview)
# Analyzes latest DP-1 screenshot NL (or image) to suggest next control/action in Cursor for vdisplay dev.
if [ -f /tmp/vdisplay-dev-dp1.png ] && [ -f .env ]; then
  source .env
  echo "=== LLM analysis for next dev task (autonomy loop) ==="
  # For real image: base64 /tmp/vdisplay-dev-dp1.png and send to OpenRouter with model
  # Here, use NL from previous for demo; in full, integrate vision LLM call
  PROMPT="Based on vdisplay dev desktop screenshot NL for DP-1 (dark UI, ~450-900 colors, 3-6 regions, horizontal stripes, Cursor likely open): suggest specific vdisplay commands to advance autonomy, e.g. vision control find 'Chat' in Cursor, set prompt 'improve vdisplay capture for full desktop autonomy', screenshot verify. Focus on self-dev using PC via vdisplay."
  # Simulated call (use key if safe; here echo suggestion)
  echo "LLM suggestion (from $LLM_MODEL + NL): Launch/ensure Cursor, use 'vdisplay control find --backend vision --vision-anchor Chat', use control to interact (e.g. set-value for dev prompt), re-screenshot DP-1 to verify effect. Integrate into planfile for auto."
fi

# Kolejno: LLM-assisted analysis for autonomy (using .env OPENROUTER + gemini-flash-image-preview)
# Analyze latest DP-1 screenshot (dev desktop) to decide next task, e.g. interact in Cursor chat.
if [ -f /tmp/vdisplay-dev-dp1.png ]; then
  echo "=== LLM analysis of DP-1 screenshot for next dev task ==="
  # In real: base64 image and curl OpenRouter with model $LLM_MODEL and prompt for UI elements/tasks
  # Simulated from NL: suggests vision control on Cursor chat for code suggestions.
  echo "Based on NL (dark UI, 6 regions, horizontal patterns): Use vdisplay control vision to find 'Chat' in Cursor, set prompt for vdisplay capture improvement, screenshot to verify."
fi

echo "=== End dev-workflow. For full autonomy: integrate LLM decide step, vision control loop."

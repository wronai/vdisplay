#!/usr/bin/env bash
# Run vdisplay dev-workflow automation on the local GNOME Wayland host.
#
# Config: vdisplay.yaml (project root) + optional .vdisplay/vdisplay.override.yaml
# Metadata: .vdisplay/runs/, .vdisplay/observe/, .vdisplay/config/
#
# Usage:
#   Terminal 1: vdisplay-agent serve
#   Terminal 2: bash examples/dev-workflow/run-dev-automation.sh
#   bash examples/dev-workflow/run-dev-automation.sh --autonomy --setup-vision --reset
#   bash examples/dev-workflow/run-dev-automation.sh --cross-ide --reset

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

export VDISPLAY_AGENT_URL="${VDISPLAY_AGENT_URL:-http://127.0.0.1:8765}"
export PYTHONPATH="${PYTHONPATH:-src:packages/vdisplay-agent/src}"
export VDISPLAY_OBSERVE="${VDISPLAY_OBSERVE:-1}"

PLANFILE="examples/dev-workflow/planfile.yaml"
DRY_RUN=""
MAX=""
RESET=""
SETUP_VISION=""
AUTONOMY=""
CROSS_IDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN="--dry-run" ;;
    --reset) RESET="1" ;;
    --max) MAX="--max $2"; shift ;;
    --autonomy) AUTONOMY="1"; PLANFILE="examples/dev-workflow/planfile-autonomy.yaml" ;;
    --cross-ide) CROSS_IDE="1"; PLANFILE="examples/dev-workflow/planfile-cross-ide.yaml" ;;
    --setup-vision) SETUP_VISION="1" ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

echo "vdisplay dev-workflow — project=${ROOT}"
echo "config: vdisplay.yaml (+ .vdisplay/vdisplay.override.yaml if present)"
echo "metadata: .vdisplay/"
echo "agent: ${VDISPLAY_AGENT_URL}"
echo "planfile: ${PLANFILE}"
echo ""

if [[ -n "${SETUP_VISION}" ]]; then
  bash examples/dev-workflow/setup-autonomy.sh
  echo ""
fi

if [[ -n "${CROSS_IDE}" ]]; then
  _ensure_koru_daemon() {
    local instance="$1"
    local socket="/run/user/$(id -u)/koru-autopilot-${instance}.sock"
    if ! (
      cd "$ROOT"
      source .venv/bin/activate 2>/dev/null || true
      export KORU_AUTOPILOT_INSTANCE="${instance}"
      export KORU_AUTOPILOT_SOCKET="${socket}"
      koru autopilot status 2>/dev/null | grep -q '"ok"[[:space:]]*:[[:space:]]*true'
    ); then
      echo "starting koru autopilot daemon for ${instance}…"
      (
        cd "$ROOT"
        source .venv/bin/activate 2>/dev/null || true
        export KORU_AUTOPILOT_INSTANCE="${instance}"
        export KORU_AUTOPILOT_SOCKET="${socket}"
        nohup koru autopilot daemon >"/tmp/koru-autopilot-${instance}.log" 2>&1 &
      )
      sleep 2
    fi
  }
  _ensure_koru_daemon jetbrains
  _ensure_koru_daemon cursor
fi

if [[ -n "${AUTONOMY}" || -n "${CROSS_IDE}" ]]; then
  export KORU_VDISPLAY_CONTROL_FALLBACK="${KORU_VDISPLAY_CONTROL_FALLBACK:-1}"
  export KORU_VDISPLAY_USE_VQL_MOUSE_FOCUS="${KORU_VDISPLAY_USE_VQL_MOUSE_FOCUS:-1}"
  export KORU_VDISPLAY_PREFER_PHOTO_VQL="${KORU_VDISPLAY_PREFER_PHOTO_VQL:-1}"
  export KORU_VDISPLAY_PHOTO_VQL_REFRESH="${KORU_VDISPLAY_PHOTO_VQL_REFRESH:-auto}"
  export PYTHONPATH="${HOME}/github/semcod/koru/src:${PYTHONPATH}"
fi

if [[ -n "${RESET}" ]]; then
  reset_count="$(PYTHONPATH="${PYTHONPATH}" python3 -c '
from pathlib import Path
from vdisplay.application.auto.tasks import reset_yaml_automation_tasks
print(reset_yaml_automation_tasks(Path("'"${PLANFILE}"'")))
')"
  echo "reset ${reset_count} planfile task(s) to todo"
  echo ""
fi

if ! curl -sf --max-time 3 "${VDISPLAY_AGENT_URL}/health" >/dev/null 2>&1; then
  echo "error: vdisplay-agent unreachable at ${VDISPLAY_AGENT_URL}" >&2
  echo "Start Terminal 1: vdisplay-agent serve" >&2
  exit 1
fi

if [[ -n "${DRY_RUN}" ]]; then
  vdisplay auto --project "$ROOT" --planfile "$PLANFILE" --source yaml list
  exit 0
fi

if ! vdisplay agent screencast status 2>/dev/null | grep -qE '"ready"[[:space:]]*:[[:space:]]*true'; then
  echo "screencast not ready — starting (choose All Screens in portal dialog)…"
  vdisplay agent screencast start --force
fi

auto_exit=0
result="$(vdisplay auto --project "$ROOT" --planfile "$PLANFILE" --source yaml run ${MAX:-})" || auto_exit=$?
echo "$result"

executed_count="$(echo "$result" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("executed") or []))')"
run_id="$(echo "$result" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("run_id") or "")' 2>/dev/null || true)"
metadata_dir="$(echo "$result" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("metadata_dir") or ".vdisplay")' 2>/dev/null || true)"

if [[ "${executed_count}" == "0" ]]; then
  echo ""
  echo "note: no pending tasks (all done). Re-run with: bash examples/dev-workflow/run-dev-automation.sh --reset"
fi

echo ""
echo "Automation metadata: ${metadata_dir}"
if [[ -n "${run_id}" ]]; then
  echo "Latest run: ${metadata_dir}/runs/${run_id}/"
fi
ls -lh "${metadata_dir}"/observe/*.png 2>/dev/null | tail -5 || true

if [[ "${auto_exit:-0}" != "0" ]]; then
  echo ""
  echo "warning: vdisplay auto exited ${auto_exit} (see JSON above for failed task)"
  exit "${auto_exit}"
fi

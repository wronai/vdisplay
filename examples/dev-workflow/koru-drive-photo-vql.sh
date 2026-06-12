#!/usr/bin/env bash
# koru autopilot drive with photo VQL observe + sidecar (full autonomy loop entry).
#
# Usage:
#   bash examples/dev-workflow/koru-drive-photo-vql.sh --ide cursor --prompt "fix tests"
#   bash examples/dev-workflow/koru-drive-photo-vql.sh --ide jetbrains --source DP-2 --dry-run

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KORU_SRC="${KORU_SRC:-$HOME/github/semcod/koru/src}"
IMGL_SRC="${IMGL_SRC:-$HOME/github/semcod/imgl}"

cd "$ROOT"
if [[ -f "${ROOT}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
fi
if [[ -f "${ROOT}/.env" ]]; then
  while IFS= read -r line; do
    case "${line}" in
      OPENROUTER_API_KEY=*|LLM_MODEL=*|KORU_VDISPLAY_LLM_VISION_DECISION=*)
        export "${line}"
        ;;
    esac
  done < <(grep -E '^(OPENROUTER_API_KEY|LLM_MODEL|KORU_VDISPLAY_LLM_VISION_DECISION)=' "${ROOT}/.env" || true)
fi

IDE="cursor"
SOURCE=""
PROMPT=""
DRY=""
SUBMIT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ide) IDE="$2"; shift ;;
    --source) SOURCE="$2"; shift ;;
    --prompt) PROMPT="$2"; shift ;;
    --dry-run) DRY=1 ;;
    --submit) SUBMIT=1 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

if [[ -z "${PROMPT}" ]]; then
  echo "error: --prompt required" >&2
  exit 2
fi

export VDISPLAY_AGENT_URL="${VDISPLAY_AGENT_URL:-http://127.0.0.1:8765}"
export KORU_VDISPLAY_CONTROL_FALLBACK="${KORU_VDISPLAY_CONTROL_FALLBACK:-1}"
export KORU_VDISPLAY_USE_VQL_MOUSE_FOCUS="${KORU_VDISPLAY_USE_VQL_MOUSE_FOCUS:-1}"
# JetBrains: auto photo VQL+LLM when capture matches after ide control; else ide-prompt map.
case "${IDE}" in
  jetbrains|pycharm|idea)
    export KORU_VDISPLAY_PREFER_PHOTO_VQL="${KORU_VDISPLAY_PREFER_PHOTO_VQL:-auto}"
    export KORU_VDISPLAY_AUTO_OPEN_IDE="${KORU_VDISPLAY_AUTO_OPEN_IDE:-1}"
    ;;
  *)
    export KORU_VDISPLAY_PREFER_PHOTO_VQL="${KORU_VDISPLAY_PREFER_PHOTO_VQL:-1}"
    ;;
esac
export KORU_VDISPLAY_PHOTO_VQL_REFRESH="${KORU_VDISPLAY_PHOTO_VQL_REFRESH:-auto}"
export PYTHONPATH="${IMGL_SRC}:${KORU_SRC}:${ROOT}/src:${ROOT}/packages/vdisplay-agent/src${PYTHONPATH:+:$PYTHONPATH}"
export KORU_VDISPLAY_LLM_VISION_DECISION="${KORU_VDISPLAY_LLM_VISION_DECISION:-1}"
export KORU_VDISPLAY_AUTO_IDE_CONTROL="${KORU_VDISPLAY_AUTO_IDE_CONTROL:-1}"
export KORU_VDISPLAY_IDE_CONTROL_RETRIES="${KORU_VDISPLAY_IDE_CONTROL_RETRIES:-3}"
export KORU_VDISPLAY_RAISE_ALT_TAB="${KORU_VDISPLAY_RAISE_ALT_TAB:-0}"
export KORU_VDISPLAY_RAISE_ALT_TAB_CYCLES="${KORU_VDISPLAY_RAISE_ALT_TAB_CYCLES:-2}"
export VDISPLAY_POINTER_SAFE_MARGIN="${VDISPLAY_POINTER_SAFE_MARGIN:-140}"

export KORU_DRIVE_IDE="${IDE}"
export KORU_DRIVE_PROMPT="${PROMPT}"
export KORU_DRIVE_SUBMIT="${SUBMIT:-0}"
if [[ -n "${SOURCE}" ]]; then
  export KORU_VDISPLAY_SOURCE="${SOURCE}"
fi
if [[ -n "${DRY}" ]]; then
  export KORU_VDISPLAY_DRY_RUN=1
fi

python3 << 'PY'
import json
import os
import sys

from koru.integrations.vdisplay_client import prepare_photo_vql_for_drive, send_chat

ide = os.environ["KORU_DRIVE_IDE"]
prompt = os.environ["KORU_DRIVE_PROMPT"]
submit = os.environ.get("KORU_DRIVE_SUBMIT", "0") in {"1", "true", "yes"}

observe = prepare_photo_vql_for_drive(ide=ide)
print("photo_vql_observe:", json.dumps(observe, indent=2))

reply = send_chat(prompt, ide=ide, submit=submit, dry_run=os.environ.get("KORU_VDISPLAY_DRY_RUN", "").strip().lower() in {"1", "true", "yes"})
reply = reply or {"ok": False, "error": "no reply"}
reply.setdefault("photo_vql_observe", observe)
print("drive_reply:", json.dumps(reply, indent=2, default=str))
sys.exit(0 if reply.get("ok") else 1)
PY

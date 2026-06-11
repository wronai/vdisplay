#!/usr/bin/env bash
# Koru photo-VQL focus + edit via vdisplay sidecar (Cursor/JetBrains, IDE-agnostic coords).
#
# Prerequisites:
#   bash examples/dev-workflow/setup-autonomy.sh   # installs [observe,auto] incl. imgl
#   vdisplay-agent serve                           # VDISPLAY_AGENT_URL
#
# Usage:
#   bash examples/dev-workflow/koru-photo-vql.sh --dry-run
#   bash examples/dev-workflow/koru-photo-vql.sh --prompt "hello chat" --ide cursor
#   bash examples/dev-workflow/koru-photo-vql.sh --code-edit --prompt "# edit line" --source DP-1

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KORU_SRC="${KORU_SRC:-$HOME/github/semcod/koru/src}"

cd "$ROOT"
if [[ -f "${ROOT}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
fi

export VDISPLAY_AGENT_URL="${VDISPLAY_AGENT_URL:-http://127.0.0.1:8765}"
export KORU_VDISPLAY_CONTROL_FALLBACK="${KORU_VDISPLAY_CONTROL_FALLBACK:-1}"
export KORU_VDISPLAY_USE_VQL_MOUSE_FOCUS="${KORU_VDISPLAY_USE_VQL_MOUSE_FOCUS:-1}"
if [[ "${IDE}" == "jetbrains" || "${IDE}" == "pycharm" ]]; then
  export KORU_VDISPLAY_PREFER_PHOTO_VQL="${KORU_VDISPLAY_PREFER_PHOTO_VQL:-1}"
fi
export KORU_VDISPLAY_SOURCE="${KORU_VDISPLAY_SOURCE:-DP-1}"
export PYTHONPATH="${KORU_SRC}:${ROOT}/src:${ROOT}/packages/vdisplay-agent/src${PYTHONPATH:+:$PYTHONPATH}"

PROMPT=""
IDE="cursor"
SOURCE="${KORU_VDISPLAY_SOURCE}"
DRY=""
CODE_EDIT=""
SOURCE_SLUG="$(echo "${SOURCE}" | tr '[:upper:]' '[:lower:]' | tr '/' '-')"
SHOT="${ROOT}/.vdisplay/koru-cont-${SOURCE_SLUG}.png"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --code-edit) CODE_EDIT=1 ;;
    --prompt) PROMPT="$2"; shift ;;
    --ide) IDE="$2"; shift ;;
    --source) SOURCE="$2"; SOURCE_SLUG="$(echo "${SOURCE}" | tr '[:upper:]' '[:lower:]' | tr '/' '-')"; SHOT="${ROOT}/.vdisplay/koru-cont-${SOURCE_SLUG}.png"; export KORU_VDISPLAY_SOURCE="$SOURCE"; shift ;;
    --shot) SHOT="$2"; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

if [[ -z "${PROMPT}" ]]; then
  if [[ -n "${CODE_EDIT}" ]]; then
    PROMPT="# koru photo VQL edit"
  else
    PROMPT="koru photo VQL chat probe"
  fi
fi

if [[ -n "${DRY}" ]]; then
  export KORU_VDISPLAY_DRY_RUN=1
fi

export KORU_PHOTO_PROMPT="${PROMPT}"
export KORU_PHOTO_IDE="${IDE}"
export KORU_PHOTO_CODE_EDIT="${CODE_EDIT:-0}"

echo "screenshot → ${SHOT} (--source ${SOURCE})"
vdisplay screenshot -o "${SHOT}" --source "${SOURCE}"

export KORU_VDISPLAY_VQL_PATH="${SHOT}.vql.json"

python3 << 'PY'
import json
import os

from koru.integrations.vdisplay_client import (
    get_vql_chat_target_from_photo,
    get_vql_editor_target_from_photo,
    perform_photo_vql_focus_and_edit,
)

chat = get_vql_chat_target_from_photo()
editor = get_vql_editor_target_from_photo()
print("chat target:", chat.get("id"), chat.get("click_center"))
print("editor target:", editor.get("id"), editor.get("click_center"))

result = perform_photo_vql_focus_and_edit(
    os.environ["KORU_PHOTO_PROMPT"],
    ide=os.environ["KORU_PHOTO_IDE"],
    source=os.environ.get("KORU_VDISPLAY_SOURCE", "DP-1"),
    is_code_edit=os.environ.get("KORU_PHOTO_CODE_EDIT", "0") in {"1", "true", "yes"},
)
print(json.dumps(result, indent=2, default=str))
PY

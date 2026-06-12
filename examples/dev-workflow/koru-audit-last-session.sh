#!/usr/bin/env bash
# Audit the latest koru photo-VQL autonomy session under .vdisplay/YYYY-MM-DD/*__koru-{ide}/
#
# Usage:
#   bash examples/dev-workflow/koru-audit-last-session.sh
#   bash examples/dev-workflow/koru-audit-last-session.sh --ide jetbrains
#   SESSION=.vdisplay/2026-06-12/... bash examples/dev-workflow/koru-audit-last-session.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KORU_SRC="${KORU_SRC:-$HOME/github/semcod/koru/src}"
IDE="jetbrains"
export KORU_SRC VDISPLAY_METADATA_DIR="${VDISPLAY_METADATA_DIR:-.vdisplay}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ide) IDE="$2"; shift ;;
    --session) export SESSION="$2"; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

cd "$ROOT"

if [[ -z "${SESSION:-}" ]]; then
  SESSION=$(python3 << PY
from pathlib import Path
import os, sys
sys.path.insert(0, os.environ.get("KORU_SRC", os.path.expanduser("~/github/semcod/koru/src")))
from koru.integrations.autonomy_session import find_latest_koru_session
root = Path(os.environ.get("VDISPLAY_METADATA_DIR", ".vdisplay"))
s = find_latest_koru_session(ide="${IDE}", root=root)
print(s if s else "", end="")
PY
)
fi

if [[ -z "${SESSION}" || ! -d "${SESSION}" ]]; then
  echo "Brak sesji *__koru-${IDE} w .vdisplay/" >&2
  echo "  Po 'vdisplay config --project . clear' uruchom REAL drive (bez --dry-run):" >&2
  echo "  bash examples/dev-workflow/koru-drive-photo-vql.sh --ide ${IDE} --source DP-2 --prompt 'test'" >&2
  echo "  Dry-run tworzy tylko observe/prepare.json — decide/act wymagają pełnego perform." >&2
  exit 1
fi

echo "SESSION=${SESSION}"
echo "session.json: $(jq -r '.started_at // .kind // empty' "${SESSION}/session.json" 2>/dev/null || echo '?')"

audit_file() {
  local rel="$1"
  local label="$2"
  local path="${SESSION}/${rel}"
  echo ""
  echo "=== ${label} (${rel}) ==="
  if [[ ! -f "${path}" ]]; then
    echo "(brak — ${rel})"
    return 1
  fi
  if [[ "${path}" == *.jsonl ]]; then
    jq -s '.' "${path}"
  else
    jq '.' "${path}"
  fi
}

audit_file "decide/vql_chat_candidates.json" "1. Kandydaci VQL" || true
audit_file "decide/vql_chat_target_selected.json" "2. Wybrany target" || true
audit_file "act/cursor_positioning.jsonl" "3. Pozycjonowanie kursora" || true

echo ""
echo "=== 4. Plan komend (pre_act lub ostatni command_plan_*) ==="
PLAN="${SESSION}/act/command_plan_perform_photo_vql_pre_act.json"
if [[ ! -f "${PLAN}" ]]; then
  PLAN=$(find "${SESSION}/act" -name 'command_plan_*.json' 2>/dev/null | sort | tail -1 || true)
fi
if [[ -n "${PLAN}" && -f "${PLAN}" ]]; then
  jq '{final_local,final_global,warnings,commands,selection_method,inference_ok}' "${PLAN}"
else
  echo "(brak act/command_plan_*.json)"
fi

audit_file "act/drive_result.json" "5. Wynik drive" || true

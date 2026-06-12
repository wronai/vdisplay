#!/usr/bin/env bash
# koru autopilot drive with photo VQL observe + sidecar (full autonomy loop entry).
#
# Usage:
#   bash examples/dev-workflow/koru-drive-photo-vql.sh --ide cursor --prompt "fix tests"
#   bash examples/dev-workflow/koru-drive-photo-vql.sh --ide jetbrains --source DP-1 --dry-run

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KORU_SRC="${KORU_SRC:-$HOME/github/semcod/koru/src}"
IMGL_SRC="${IMGL_SRC:-$HOME/github/semcod/imgl}"
export KORU_SRC IMGL_SRC

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
    export VDISPLAY_CAPTURE_VALIDATE_IDE="${VDISPLAY_CAPTURE_VALIDATE_IDE:-jetbrains}"
    export KORU_VDISPLAY_IDE="${KORU_VDISPLAY_IDE:-jetbrains}"
    ;;
  *)
    export KORU_VDISPLAY_PREFER_PHOTO_VQL="${KORU_VDISPLAY_PREFER_PHOTO_VQL:-1}"
    ;;
esac
export KORU_VDISPLAY_PHOTO_VQL_REFRESH="${KORU_VDISPLAY_PHOTO_VQL_REFRESH:-auto}"
export PYTHONPATH="${IMGL_SRC}:${KORU_SRC}:${ROOT}/src:${ROOT}/packages/vdisplay-agent/src${PYTHONPATH:+:$PYTHONPATH}"
export KORU_VDISPLAY_LLM_VISION_DECISION="${KORU_VDISPLAY_LLM_VISION_DECISION:-1}"
export KORU_VDISPLAY_VQL_MAX_AGE_S="${KORU_VDISPLAY_VQL_MAX_AGE_S:-300}"
export VDISPLAY_SESSION="${VDISPLAY_SESSION:-1}"
export KORU_VDISPLAY_AUTO_IDE_CONTROL="${KORU_VDISPLAY_AUTO_IDE_CONTROL:-1}"
export KORU_VDISPLAY_IDE_CONTROL_RETRIES="${KORU_VDISPLAY_IDE_CONTROL_RETRIES:-3}"
# Alt+Tab focus recovery: default on for JetBrains (see _raise_alt_tab_enabled); off for other IDEs unless set.
case "${IDE}" in
  jetbrains|pycharm|idea) ;;
  *) export KORU_VDISPLAY_RAISE_ALT_TAB="${KORU_VDISPLAY_RAISE_ALT_TAB:-0}" ;;
esac
export KORU_VDISPLAY_RAISE_ALT_TAB_CYCLES="${KORU_VDISPLAY_RAISE_ALT_TAB_CYCLES:-2}"
export VDISPLAY_POINTER_SAFE_MARGIN="${VDISPLAY_POINTER_SAFE_MARGIN:-140}"
export VDISPLAY_ROOT="${ROOT}"
# Optional spoken + notify-send guidance: export KORU_VDISPLAY_USER_TTS=1
export KORU_VDISPLAY_USER_TTS="${KORU_VDISPLAY_USER_TTS:-0}"
# Enable ydotool literal typing on Wayland (more reliable than clipboard paste for PyCharm AI Chat)
export VDISPLAY_ALLOW_YDOTOOL_TYPING="${VDISPLAY_ALLOW_YDOTOOL_TYPING:-1}"

export KORU_DRIVE_IDE="${IDE}"
export KORU_DRIVE_PROMPT="${PROMPT}"
export KORU_DRIVE_SUBMIT="${SUBMIT:-0}"
export KORU_DRIVE_SOURCE_CLI="${SOURCE}"
if [[ -n "${SOURCE}" && "${SOURCE,,}" != "auto" ]]; then
  export KORU_VDISPLAY_SOURCE="${SOURCE}"
fi
if [[ -n "${DRY}" ]]; then
  export KORU_VDISPLAY_DRY_RUN=1
fi

echo "=== Koru photo-VQL drive ===" >&2
echo "  katalog:  ${ROOT}" >&2
echo "  skrypt:   $(basename "$0") (repo wronai/vdisplay, NIE semcod/koru)" >&2
echo "  KORU_SRC: ${KORU_SRC}" >&2
echo "  IMGL_SRC: ${IMGL_SRC}" >&2
echo "  IDE:      ${IDE}  source: ${SOURCE:-auto}  TTS: ${KORU_VDISPLAY_USER_TTS}" >&2
echo "  mowa:     export KORU_VDISPLAY_USER_TTS=1  # espeak/spd-say + notify-send" >&2

_preflight_ok=1
if [[ ! -f "${KORU_SRC}/koru/__init__.py" ]]; then
  echo "USER_SETUP: Brak koru w ${KORU_SRC}" >&2
  echo "  export KORU_SRC=\"\$HOME/github/semcod/koru/src\"" >&2
  _preflight_ok=0
fi
if [[ ! -f "${IMGL_SRC}/imgl/__init__.py" ]]; then
  echo "USER_SETUP: Brak imgl w ${IMGL_SRC}" >&2
  echo "  export IMGL_SRC=\"\$HOME/github/semcod/imgl\"" >&2
  _preflight_ok=0
fi
if [[ "${_preflight_ok}" -eq 0 ]]; then
  echo "" >&2
  echo "=== CO TERAZ ZROBIĆ (USER) ===" >&2
  echo "  1. cd ~/github/wronai/vdisplay" >&2
  echo "  2. export KORU_SRC=\"\$HOME/github/semcod/koru/src\"" >&2
  echo "  3. export IMGL_SRC=\"\$HOME/github/semcod/imgl\"" >&2
  echo "  4. bash examples/dev-workflow/koru-drive-photo-vql.sh --ide ${IDE} --prompt \"${PROMPT}\"" >&2
  echo "==============================" >&2
  exit 2
fi

if [[ -n "${SOURCE}" && "${SOURCE,,}" != "auto" ]]; then
python3 << 'PY'
import os
import shlex
import sys

source = os.environ.get("KORU_DRIVE_SOURCE_CLI", "").strip()
if not source:
    sys.exit(0)

try:
    from vdisplay.application.services.discovery import list_monitors_local

    payload = list_monitors_local()
except Exception as exc:
    print(f"monitor_preflight_warn: cannot list monitors ({exc})", file=sys.stderr)
    sys.exit(0)

names = [str(m.get("name")) for m in payload.get("monitors") or [] if m.get("name")]
if not names or source in names:
    sys.exit(0)

fallback = next((name for name in names if name.startswith("DP-")), names[0])
root = os.environ.get("VDISPLAY_ROOT", "").strip() or "."
ide = os.environ.get("KORU_DRIVE_IDE", "jetbrains").strip() or "jetbrains"
prompt = os.environ.get("KORU_DRIVE_PROMPT", "hello")
cmd_prefix = f"cd {shlex.quote(root)} && bash examples/dev-workflow/koru-drive-photo-vql.sh"
prompt_arg = shlex.quote(prompt)

print(
    f"prepare_aborted: requested monitor {source!r} not connected "
    f"(available: {names})",
    file=sys.stderr,
)
print("", file=sys.stderr)
print("=== CO TERAZ ZROBIĆ (USER) ===", file=sys.stderr)
print(f"  1. Aktualne monitory: {', '.join(names)}", file=sys.stderr)
print(
    f"  2. Auto-wybór źródła: {cmd_prefix} --ide {shlex.quote(ide)} "
    f"--source auto --prompt {prompt_arg}",
    file=sys.stderr,
)
print(
    f"  3. Jawnie dostępny monitor: {cmd_prefix} --ide {shlex.quote(ide)} "
    f"--source {shlex.quote(fallback)} --prompt {prompt_arg}",
    file=sys.stderr,
)
print(
    f"  4. Jeśli naprawdę potrzebujesz {source}, podłącz/aktywuj monitor "
    "i sprawdź: vdisplay monitors",
    file=sys.stderr,
)
print("==============================", file=sys.stderr)
sys.exit(1)
PY
fi

python3 << 'PY'
import json
import os
import sys
from pathlib import Path

from koru.integrations.autonomy_session import find_latest_koru_session, persist_autonomy_phase
from koru.integrations.photo_vql_drive import run_photo_vql_drive
from koru.integrations.photo_vql_user_guidance import emit_user_guidance, preflight_repo_paths

ide = os.environ["KORU_DRIVE_IDE"]
prompt = os.environ["KORU_DRIVE_PROMPT"]
submit = os.environ.get("KORU_DRIVE_SUBMIT", "0") in {"1", "true", "yes"}
dry_run = os.environ.get("KORU_VDISPLAY_DRY_RUN", "").strip().lower() in {"1", "true", "yes"}
source = os.environ.get("KORU_VDISPLAY_SOURCE", "").strip() or None
vdisplay_root = os.environ.get("VDISPLAY_ROOT", "").strip() or None

setup_issues = preflight_repo_paths()
if setup_issues:
    for msg in setup_issues:
        print(f"USER_SETUP: {msg}", file=sys.stderr)
    emit_user_guidance(
        ide=ide,
        reply={"ok": False, "error": setup_issues[0]},
        vdisplay_root=vdisplay_root,
    )
    sys.exit(2)

reply = run_photo_vql_drive(
    prompt,
    ide=ide,
    source=source,
    submit=submit,
    dry_run=dry_run,
    reuse_prepare=False,
)
observe = reply.get("photo_vql_observe") or {}
print("photo_vql_observe:", json.dumps(observe, indent=2))

probe = observe.get("desktop_probe") or {}
if probe:
    print("desktop_probe:", json.dumps({
        "ok": probe.get("ok"),
        "resolved_source": probe.get("resolved_source"),
        "source_auto_resolved": probe.get("source_auto_resolved"),
        "monitor_names": probe.get("monitor_names"),
        "window_count": probe.get("window_count"),
        "ide_process_count": len(probe.get("ide_processes") or []),
    }, indent=2))
if not observe.get("ok") and not reply.get("ok"):
    err = observe.get("error") or reply.get("error") or "prepare failed"
    print(f"prepare_aborted: {err}", file=sys.stderr)
    emit_user_guidance(
        ide=ide,
        observe=observe,
        reply=reply,
        source=source,
        vdisplay_root=vdisplay_root,
    )
    sys.exit(1)

prov = observe.get("capture_provenance") or reply.get("capture_provenance") or {}
if prov:
    print("capture_confirmation:", json.dumps({
        "capture_confirmed": prov.get("capture_confirmed"),
        "window_titles": prov.get("window_titles"),
        "png_mtime_iso": prov.get("png_mtime_iso"),
        "vql_mtime_iso": prov.get("vql_mtime_iso"),
    }, indent=2))

if observe.get("ide_window_warning"):
    print(
        "capture_warning: foreground window is not the target IDE - drive will abort unless "
        "KORU_VDISPLAY_ALLOW_MAP_ON_MISMATCH=1",
        file=sys.stderr,
    )
    if observe.get("competing_ide"):
        print(f"competing_ide: {observe['competing_ide']}", file=sys.stderr)

ide_control = observe.get("ide_control") or {}
visual_guard_failed = ide_control.get("visual_guard_failed")
allow_mismatch = os.environ.get("KORU_VDISPLAY_ALLOW_MAP_ON_MISMATCH", "").strip().lower() in {"1", "true", "yes", "on"} or os.environ.get("KORU_VDISPLAY_ALLOW_IDE_MISMATCH", "").strip().lower() in {"1", "true", "yes", "on"}
if visual_guard_failed and not allow_mismatch:
    print(
        "drive_aborted: capture IDE mismatch (visual_guard_failed=true). "
        f"window_titles={prov.get('window_titles')!r}.",
        file=sys.stderr,
    )
    emit_user_guidance(
        ide=ide,
        observe=observe,
        reply=reply,
        source=source,
        vdisplay_root=vdisplay_root,
    )
    sys.exit(1)

plan = (reply.get("photo_vql") or {}).get("vql_command_plan") or reply.get("vql_command_plan")
if plan:
    print("vql_command_plan:", json.dumps({
        "selection_method": plan.get("selection_method"),
        "final_local": plan.get("final_local"),
        "final_global": plan.get("final_global"),
        "warnings": plan.get("warnings"),
        "inference_ok": plan.get("inference_ok"),
        "capture_confirmed": plan.get("capture_confirmed"),
        "commands": plan.get("commands"),
    }, indent=2, default=str))
coords = reply.get("coords") or (reply.get("photo_vql") or {}).get("coords")
if coords:
    print("cursor_at_write_command:", json.dumps(coords, indent=2))

session = find_latest_koru_session(ide=ide, root=Path(os.environ.get("VDISPLAY_METADATA_DIR", ".vdisplay")))
if session is not None:
    persist_autonomy_phase(session, "act", "drive_result", reply)
    print(f"SESSION={session.resolve()}")
    print(f"# audit: bash examples/dev-workflow/koru-audit-last-session.sh --ide {ide}")
else:
    print("SESSION=none")

print("drive_reply:", json.dumps(reply, indent=2, default=str))
emit_user_guidance(
    ide=ide,
    observe=observe,
    reply=reply,
    source=source,
    vdisplay_root=vdisplay_root,
)
sys.exit(0 if reply.get("ok") else 1)
PY

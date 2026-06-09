#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMMON="$ROOT/examples/common"
cd "$ROOT"

VDISPLAY_BIN="${VDISPLAY_BIN:-$ROOT/.venv/bin/vdisplay}"
if [[ ! -x "$VDISPLAY_BIN" ]]; then
  VDISPLAY_BIN="$(command -v vdisplay || true)"
fi

validate_dir() {
  local dir="$1"
  python3 "$COMMON/validate_artifacts.py" "$dir"
}

clean_output() {
  local dir="$1"
  mkdir -p "$dir"
  docker run --rm -v "$ROOT/$dir:/output" alpine sh -c 'rm -rf /output/*' >/dev/null 2>&1 || rm -rf "$dir"/* 2>/dev/null || true
}

_agent_base_url() {
  printf '%s' "${VDISPLAY_AGENT_URL:-http://127.0.0.1:8765}"
}

_wayland_host_capture_ready() {
  local base
  base="$(_agent_base_url)"
  if ! curl -sf --max-time 2 "${base}/health" >/dev/null; then
    echo "skip: vdisplay-agent not running at ${base}" >&2
    echo "hint: terminal 1: vdisplay agent serve" >&2
    return 1
  fi
  export VDISPLAY_AGENT_URL="${base}"
  local active=""
  active="$(curl -sf --max-time 2 "${base}/session/screencast/status" \
    | python3 -c "import sys,json; d=json.load(sys.stdin).get('data',{}); print('1' if d.get('active') and d.get('ready') else '0')" \
    2>/dev/null || echo 0)"
  if [[ "${active}" != "1" ]]; then
    echo "note: starting ScreenCast (needs prior Screen Recording consent)..." >&2
    if [[ -z "${VDISPLAY_BIN}" ]]; then
      echo "skip: vdisplay CLI not found for screencast start" >&2
      return 1
    fi
    if ! "${VDISPLAY_BIN}" agent screencast start >/dev/null 2>&1; then
      echo "skip: ScreenCast not ready — run: vdisplay agent screencast start" >&2
      return 1
    fi
  fi
  return 0
}

_run_host_example() {
  local name="$1"
  shift
  if "$@"; then
    return 0
  fi
  echo "skipped ${name}: see hints above" >&2
  return 0
}

_run_host_mirror() {
  clean_output examples/host-mirror/output
  (
    cd examples/host-mirror
    ./run-host.sh
  )
  validate_dir examples/host-mirror/output
  ls -la examples/host-mirror/output/
}

_run_host_relay() {
  clean_output examples/host-relay/output
  (
    cd examples/host-relay
    ./run-host.sh
  )
  validate_dir examples/host-relay/output
  ls -la examples/host-relay/output/
}

_run_docker_host_mirror() {
  clean_output examples/host-mirror/output
  (
    cd examples/host-mirror
    ./run.sh --abort-on-container-exit --exit-code-from mirror
  )
  validate_dir examples/host-mirror/output
  ls -la examples/host-mirror/output/
}

_run_docker_host_relay() {
  clean_output examples/host-relay/output
  (
    cd examples/host-relay
    ./run.sh --abort-on-container-exit --exit-code-from relay
  )
  validate_dir examples/host-relay/output
  ls -la examples/host-relay/output/
}

echo "== headless-virtual =="
clean_output examples/headless-virtual/output
(
  cd examples/headless-virtual
  docker compose up --build --abort-on-container-exit --exit-code-from virtual
)
validate_dir examples/headless-virtual/output
ls -la examples/headless-virtual/output/

echo "== ci-agent =="
clean_output examples/ci-agent/output
(
  cd examples/ci-agent
  docker compose up --build --abort-on-container-exit --exit-code-from ci-agent
)
validate_dir examples/ci-agent/output
ls -la examples/ci-agent/output/

if [[ -S /tmp/.X11-unix/X0 || -S /tmp/.X11-unix/X1 ]]; then
  if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
    echo "== host-mirror (Wayland — host + agent) =="
    if _wayland_host_capture_ready; then
      _run_host_example host-mirror _run_host_mirror
    else
      echo "skipped host-mirror on Wayland (agent + ScreenCast required)" >&2
    fi

    echo "== host-relay (Wayland — host + agent) =="
    if _wayland_host_capture_ready; then
      _run_host_example host-relay _run_host_relay
    else
      echo "skipped host-relay on Wayland (agent + ScreenCast required)" >&2
    fi
  else
    echo "== host-mirror =="
    _run_docker_host_mirror

    echo "== host-relay =="
    _run_docker_host_relay
  fi
else
  echo "skip host-mirror/host-relay: no X11 socket"
fi

echo "== dev-workspace build =="
docker compose -f examples/dev-workspace/docker-compose.yml build

echo "all runnable examples completed"

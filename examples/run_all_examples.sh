#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMMON="$ROOT/examples/common"
cd "$ROOT"

validate_dir() {
  local dir="$1"
  python3 "$COMMON/validate_artifacts.py" "$dir"
}

clean_output() {
  local dir="$1"
  mkdir -p "$dir"
  docker run --rm -v "$ROOT/$dir:/output" alpine sh -c 'rm -rf /output/*' >/dev/null 2>&1 || rm -rf "$dir"/* 2>/dev/null || true
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
  echo "== host-mirror =="
  clean_output examples/host-mirror/output
  (
    cd examples/host-mirror
    ./run.sh --abort-on-container-exit --exit-code-from mirror
  )
  validate_dir examples/host-mirror/output
  ls -la examples/host-mirror/output/

  echo "== host-relay =="
  clean_output examples/host-relay/output
  (
    cd examples/host-relay
    ./run.sh --abort-on-container-exit --exit-code-from relay
  )
  validate_dir examples/host-relay/output
  ls -la examples/host-relay/output/
else
  echo "skip host-mirror/host-relay: no X11 socket"
fi

echo "== dev-workspace build =="
docker compose -f examples/dev-workspace/docker-compose.yml build

echo "all runnable examples completed"

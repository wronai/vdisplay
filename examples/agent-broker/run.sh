#!/usr/bin/env bash
# Demo: vdisplay-agent broker + clients (no Docker required).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PORT="${VD_AGENT_PORT:-8777}"
URL="http://127.0.0.1:${PORT}"

echo "==> Starting vdisplay-agent on ${URL}"
python3 -m vdisplay_agent.cli serve --host 127.0.0.1 --port "${PORT}" &
AGENT_PID=$!
cleanup() {
  kill "${AGENT_PID}" 2>/dev/null || true
  wait "${AGENT_PID}" 2>/dev/null || true
}
trap cleanup EXIT
sleep 1

export VDISPLAY_AGENT_URL="${URL}"
python3 examples/agent-broker/broker_demo.py

echo
echo "Optional — REST adapter (another terminal):"
echo "  VDISPLAY_AGENT_URL=${URL} rest2vdisplay serve --port 8216"

"""Broker demo — run via examples/agent-broker/run.sh or with agent already up."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from vdisplay.agent_config import resolve_agent_url
from vdisplay.client import AgentClient


def main() -> int:
    url = resolve_agent_url()
    if not url:
        print("Set VDISPLAY_AGENT_URL (run.sh sets it automatically)", file=sys.stderr)
        return 1

    client = AgentClient(url)
    print("==> health")
    print(json.dumps(client.health(), indent=2))

    print("\n==> monitors (/outputs)")
    outputs = client.outputs()
    print(f"monitor_count: {outputs.get('monitor_count')}")
    for monitor in outputs.get("monitors") or []:
        print(f"  - {monitor.get('name')} {monitor.get('geometry')}")

    print("\n==> virtual screenshot via agent")
    out = Path(tempfile.gettempdir()) / "vdisplay-agent-broker-demo.png"
    started = client.start_virtual(width=64, height=64, display=":195")
    session_id = started["session_id"]
    try:
        shot = client.capture_frame(session_id=session_id, output=str(out))
        print(json.dumps({k: v for k, v in shot.items() if k != "png_base64"}, indent=2))
        print(f"saved: {out} ({out.stat().st_size} bytes)" if out.is_file() else "missing file")
    finally:
        client.stop_session(session_id)

    sc = client.screencast_status()
    print("\n==> screencast status")
    print(json.dumps(sc, indent=2))
    if os.environ.get("XDG_SESSION_TYPE") == "wayland" and not sc.get("ready"):
        print(
            "\nWayland host capture: start ScreenCast once, then retry host screenshots:\n"
            f"  curl -X POST {url}/session/screencast/start "
            '-H "content-type: application/json" -d \'{"interactive": true}\'\n'
            "  vdisplay screenshot -o /tmp/host.png --source DP-1"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

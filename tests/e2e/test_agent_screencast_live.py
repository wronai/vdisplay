"""Live smoke test of the local-agent capture pipeline (portal ScreenCast).

Codifies the keeper-fallback path end-to-end: broker /health → screencast
ready → ``vdisplay screenshot`` over the portal stream → a real (non-uniform)
frame on disk → audit session recorded → ``session export`` zip is valid.

Requires a long-running broker with an active portal ScreenCast, started
from the local GUI session (Wayland portal consent lives there):

  export VDISPLAY_LIVE_EXTERNAL=1
  export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
  vdisplay-agent serve
  vdisplay agent screencast start
  pytest tests/e2e/test_agent_screencast_live.py -m live -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.live

SCREENSHOT_TIMEOUT_S = 120


def _agent_base() -> str:
    return os.environ.get("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765").rstrip("/")


def _external_live_requested() -> bool:
    return os.environ.get("VDISPLAY_LIVE_EXTERNAL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _fetch_json(path: str) -> dict:
    req = urllib.request.Request(f"{_agent_base()}{path}")
    token = os.environ.get("VDISPLAY_AGENT_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


@pytest.fixture(scope="module")
def live_broker() -> str:
    """Skip cleanly unless an external broker with a ready screencast is up."""
    if not _external_live_requested():
        pytest.skip("set VDISPLAY_LIVE_EXTERNAL=1 to run against a live broker")
    try:
        health = _fetch_json("/health")
    except (urllib.error.URLError, OSError) as exc:
        pytest.skip(f"vdisplay-agent unreachable at {_agent_base()}: {exc}")
    if not health.get("ok"):
        pytest.skip(f"broker health not ok: {health}")
    status = _fetch_json("/session/screencast/status").get("data") or {}
    if not (status.get("active") and status.get("ready")):
        pytest.skip(
            "portal screencast not ready — run: vdisplay agent screencast start "
            f"(status: active={status.get('active')} ready={status.get('ready')})"
        )
    return _agent_base()


def _run_vdisplay(args: list[str], *, env: dict[str, str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "vdisplay", *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def test_screencast_status_contract(live_broker: str) -> None:
    payload = _fetch_json("/session/screencast/status")
    assert payload["ok"] is True
    assert payload["action"] == "screencast_status"
    data = payload["data"]
    assert data["node_ids"], "expected at least one PipeWire stream node"
    assert len(data["streams"]) == len(data["node_ids"])


def test_screenshot_pipeline_end_to_end(live_broker: str, tmp_path: Path) -> None:
    pil_image = pytest.importorskip("PIL.Image")
    out_png = tmp_path / "frame.png"
    # VDISPLAY_SESSION_DIR is the session directory itself (not a root the
    # --session-id slug is appended to).
    session_dir = tmp_path / "audit" / "live-smoke"
    env = dict(os.environ)
    env["VDISPLAY_SESSION_DIR"] = str(session_dir)

    proc = _run_vdisplay(
        [
            "--session",
            "--session-id",
            "live-smoke",
            "screenshot",
            "--output",
            str(out_png),
        ],
        env=env,
        timeout=SCREENSHOT_TIMEOUT_S,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["method"].startswith("portal-screencast"), result["method"]

    # Frame is a real image of the declared size, not a black/uniform frame
    # (the most common portal failure mode).
    with pil_image.open(out_png) as img:
        assert (img.width, img.height) == (result["width"], result["height"])
        low, high = img.convert("L").getextrema()
        assert high - low > 10, f"frame looks uniform (luma range {low}..{high})"

    # Audit session recorded one ok SCREENSHOT step.
    step_result = json.loads((session_dir / "steps" / "0001" / "result.json").read_text())
    assert step_result.get("ok") is True
    index_lines = (session_dir / "index.jsonl").read_text().strip().splitlines()
    assert index_lines, "session index.jsonl is empty"

    # Export produces a valid zip containing the session manifest.
    out_zip = tmp_path / "live-smoke.zip"
    export = _run_vdisplay(
        ["session", "export", "--dir", str(session_dir), "--output", str(out_zip)],
        env=env,
        timeout=60,
    )
    assert export.returncode == 0, export.stderr
    with zipfile.ZipFile(out_zip) as archive:
        assert archive.testzip() is None
        assert any(name.endswith("session.json") for name in archive.namelist())

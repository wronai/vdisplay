from __future__ import annotations

import time
from pathlib import Path

import pytest


def test_agent_sampler_start_status_stop(agent_client, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    client, runtime = agent_client
    out_dir = tmp_path / "sampler-out"
    calls = {"n": 0}

    def fake_capture(output, **kwargs):
        calls["n"] += 1
        path = Path(output)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([calls["n"] % 250]) * 200)
        return {"path": str(path), "bytes": path.stat().st_size, "method": "portal-screencast"}

    monkeypatch.setattr(
        "vdisplay_agent.services.sampler.capture_host_to_file",
        fake_capture,
    )
    monkeypatch.setattr(
        "vdisplay.application.services.sampler_loop.assess_unattended_capture",
        lambda **kwargs: type(
            "C",
            (),
            {
                "supports_unattended_capture": True,
                "requires_user_consent": False,
                "to_dict": lambda self: {"supports_unattended_capture": True},
            },
        )(),
    )

    started = client.post(
        "/sampler/start",
        json={
            "interval_s": 0.1,
            "mode": "desktop",
            "out_dir": str(out_dir),
            "max_frames": 2,
            "format": "png",
        },
    ).json()
    assert started["ok"] is True
    assert started["data"]["running"] is True

    deadline = time.monotonic() + 3.0
    saved = 0
    while time.monotonic() < deadline:
        status = client.get("/sampler/status").json()
        saved = int(status["data"].get("frames_saved") or 0)
        if saved >= 2 or not status["data"].get("running"):
            break
        time.sleep(0.05)

    assert saved >= 2
    assert runtime.store.sampler is not None

    stopped = client.post("/sampler/stop").json()
    assert stopped["ok"] is True
    assert stopped["data"]["stopped"] is True
    assert runtime.store.sampler is None

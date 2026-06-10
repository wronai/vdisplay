from __future__ import annotations

import json
import urllib.error

import pytest

from vdisplay.agent_config import resolve_agent_url, use_agent
from vdisplay.client import AgentClient
from vdisplay.exceptions import VDisplayError


def test_use_agent_false_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    monkeypatch.setenv("VDISPLAY_AGENT_AUTO", "0")
    from vdisplay.agent_config import reset_agent_probe_cache

    reset_agent_probe_cache()
    assert use_agent() is False
    assert resolve_agent_url() is None
    assert resolve_agent_url(allow_auto=True) is None


def test_resolve_agent_url_auto_detects_live_agent(
    live_agent_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    monkeypatch.setenv("VDISPLAY_AGENT_AUTO", "1")
    from vdisplay.agent_config import reset_agent_probe_cache

    reset_agent_probe_cache()
    host = live_agent_url.rsplit(":", 1)[0].replace("http://", "")
    port = live_agent_url.rsplit(":", 1)[1]
    monkeypatch.setenv("VDISPLAY_AGENT_HOST", host)
    monkeypatch.setenv("VDISPLAY_AGENT_PORT", port)
    reset_agent_probe_cache()
    assert resolve_agent_url(allow_auto=True) == live_agent_url


def test_client_unreachable_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:1")
    client = AgentClient("http://127.0.0.1:1", timeout=0.5)
    with pytest.raises(VDisplayError, match="unreachable"):
        client.health()


def test_probe_rejects_non_vdisplay_health(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.agent_config import _probe_agent_url, reset_agent_probe_cache

    class FakeResponse:
        status = 200

        def read(self) -> bytes:
            return b'{"ok": true}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: FakeResponse())
    reset_agent_probe_cache()
    assert _probe_agent_url("http://127.0.0.1:8765") is None


def test_probe_retries_after_initial_miss(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    monkeypatch.setenv("VDISPLAY_AGENT_AUTO", "1")
    from vdisplay.agent_config import reset_agent_probe_cache

    reset_agent_probe_cache()
    calls = {"n": 0}

    def fake_probe(base_url: str, *, timeout: float = 0.2) -> str | None:
        calls["n"] += 1
        return None if calls["n"] == 1 else base_url.rstrip("/")

    monkeypatch.setattr("vdisplay.agent_config._probe_agent_url", fake_probe)
    assert resolve_agent_url(allow_auto=True) is None
    assert resolve_agent_url(allow_auto=True) == "http://127.0.0.1:8765"


def test_flatten_agent_envelope_without_vdisplay_agent_package() -> None:
    from vdisplay.agent_envelope import flatten_agent_envelope

    envelope = {
        "ok": True,
        "action": "virtual_start",
        "data": {"session_id": "virt-test", "mode": "virtual"},
        "meta": {"service": "vdisplay-agent"},
    }
    flat = flatten_agent_envelope(envelope)
    assert flat["session_id"] == "virt-test"
    assert flat["ok"] is True


def test_client_flattens_agent_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    envelope = json.dumps(
        {
            "ok": True,
            "action": "virtual_start",
            "data": {"session_id": "virt-flat", "mode": "virtual"},
        }
    ).encode("utf-8")

    class FakeResponse:
        def read(self) -> bytes:
            return envelope

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: FakeResponse())
    client = AgentClient("http://127.0.0.1:8765")
    started = client.start_virtual(display=":99")
    assert started["session_id"] == "virt-flat"


def test_virtual_screenshot_routes_local_when_agent_up(
    live_agent_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", live_agent_url)
    from vdisplay.application.commands import CommandRequest, CommandVerb
    from vdisplay.application.runtime import ExecutionPolicy

    cmd = CommandRequest(
        verb=CommandVerb.SCREENSHOT,
        mode="virtual",
        output="screen.png",
        vd_display=":99",
    )
    assert ExecutionPolicy().route(cmd) == "local"

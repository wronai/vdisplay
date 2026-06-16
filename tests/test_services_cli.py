"""CLI helpers for vdisplay services orchestrator."""

from __future__ import annotations

import argparse
import os

import pytest

from vdisplay.commands import services as svc


def _args(**kwargs):
    defaults = {
        "host": "127.0.0.1",
        "port": 8799,
        "timeout_s": 3.0,
        "instance": "jetbrains",
        "target": "jetbrains",
        "source": "HDMI-1",
        "agent_url": "http://127.0.0.1:8766",
        "no_agent_bridge": False,
        "mode": "full",
        "no_always_on_top": False,
        "ozone_platform": None,
        "startup_timeout_s": 25.0,
        "agent_startup_timeout_s": 15.0,
        "capture_timeout_s": 120.0,
        "wait_capture": False,
        "start_agent": True,
        "install": False,
        "auto_recover_capture": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_agent_host_port_defaults():
    host, port = svc._agent_host_port("http://127.0.0.1:8766")
    assert host == "127.0.0.1"
    assert port == 8766


def test_services_agent_url_prefers_explicit_arg_over_manager(monkeypatch):
    monkeypatch.setattr(
        svc,
        "_manager_get",
        lambda *_a, **_k: {"browser_bridge": {"agent_url": "http://127.0.0.1:8766"}},
    )
    assert svc._services_agent_url(_args(agent_url="http://127.0.0.1:9999")) == "http://127.0.0.1:9999"


def test_services_agent_url_uses_manager_before_stale_env(monkeypatch):
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765")
    monkeypatch.setattr(
        svc,
        "_manager_get",
        lambda *_a, **_k: {"browser_bridge": {"agent_url": "http://127.0.0.1:8766"}},
    )
    assert svc._services_agent_url(_args(agent_url=None)) == "http://127.0.0.1:8766"


def test_build_up_payload_agent_unreachable_without_start(monkeypatch):
    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: False)
    payload = svc.build_up_payload(_args(start_agent=False))
    assert payload["ok"] is False
    assert "agent not reachable" in payload["error"]


def test_stop_portal_screencast_skips_active_browser_bridge(monkeypatch):
    def _get(_url, path, **_k):
        assert path == "/session/screencast/status"
        return {
            "data": {
                "keeper_mode": "browser_bridge",
                "active": True,
                "browser_bridge": {"registered": True, "sharing": True},
            }
        }

    monkeypatch.setattr(svc, "_agent_get", _get)
    out = svc._stop_portal_screencast("http://127.0.0.1:8766")
    assert out["skipped"] is True
    assert out["reason"] == "browser_bridge_active"


def test_build_up_payload_capture_ready(monkeypatch):
    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_stop_portal_screencast", lambda *_a, **_k: {"ok": True, "skipped": True})
    monkeypatch.setattr(svc, "_clear_browser_bridge", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr(svc, "electron_up", lambda *_a, **_k: 0)
    monkeypatch.setattr(
        svc,
        "build_prepare_payload",
        lambda *_a, **_k: {
            "ok": True,
            "capture_ready": True,
            "manager": {"sharing": True},
        },
    )
    payload = svc.build_up_payload(_args())
    assert payload["ok"] is True
    assert payload["capture_ready"] is True
    assert "prepare-vdisplay" in payload["hint"]


def test_build_up_payload_clears_browser_bridge_before_screencast_stop(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_clear_browser_bridge", lambda *_a, **_k: calls.append("clear") or {"ok": True})
    monkeypatch.setattr(
        svc,
        "_stop_portal_screencast",
        lambda *_a, **_k: calls.append("stop") or {"ok": True, "skipped": True},
    )
    monkeypatch.setattr(svc, "electron_up", lambda *_a, **_k: 0)
    monkeypatch.setattr(
        svc,
        "build_prepare_payload",
        lambda *_a, **_k: {
            "ok": False,
            "capture_ready": False,
            "manager": {"ok": True, "sharing": False},
        },
    )

    payload = svc.build_up_payload(_args(wait_capture=False))

    assert payload["ok"] is True
    assert calls[:2] == ["clear", "stop"]


def test_build_up_payload_waits_for_capture(monkeypatch):
    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_stop_portal_screencast", lambda *_a, **_k: None)
    monkeypatch.setattr(svc, "_clear_browser_bridge", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr(svc, "electron_up", lambda *_a, **_k: 0)
    monkeypatch.setattr(svc, "_port_open", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_recover_electron_capture", lambda *_a, **_k: {"ok": True})
    calls = {"n": 0}

    def _prepare(*_a, **_k):
        calls["n"] += 1
        ready = calls["n"] >= 2
        return {
            "ok": ready,
            "capture_ready": ready,
            "manager": {"sharing": True},
        }

    monkeypatch.setattr(svc, "build_prepare_payload", _prepare)
    monkeypatch.setattr(svc.time, "sleep", lambda *_a, **_k: None)
    payload = svc.build_up_payload(_args(wait_capture=True, capture_timeout_s=10.0, auto_recover_capture=True))
    assert payload["ok"] is True
    assert payload["capture_ready"] is True
    assert calls["n"] >= 2
    assert os.environ["VDISPLAY_ELECTRON_REMOTE_START_CAPTURE"] == "0"
    assert os.environ["VDISPLAY_ELECTRON_ALLOW_REMOTE_START_CAPTURE"] == "0"
    assert os.environ["VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE"] == "0"
    assert os.environ["VDISPLAY_ELECTRON_ALLOW_AUTO_RESUME_CAPTURE"] == "0"
    assert os.environ["VDISPLAY_ELECTRON_UNSAFE_AUTO_CAPTURE"] == "0"


def test_build_up_payload_does_not_recover_capture_by_default(monkeypatch):
    monkeypatch.setenv("VDISPLAY_ELECTRON_REMOTE_START_CAPTURE", "1")
    monkeypatch.setenv("VDISPLAY_ELECTRON_ALLOW_REMOTE_START_CAPTURE", "1")
    monkeypatch.setenv("VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE", "1")
    monkeypatch.setenv("VDISPLAY_ELECTRON_ALLOW_AUTO_RESUME_CAPTURE", "1")
    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_stop_portal_screencast", lambda *_a, **_k: None)
    monkeypatch.setattr(svc, "_clear_browser_bridge", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr(svc, "electron_up", lambda *_a, **_k: 0)
    monkeypatch.setattr(svc, "_port_open", lambda *_a, **_k: True)
    monkeypatch.setattr(
        svc,
        "_recover_electron_capture",
        lambda *_a, **_k: pytest.fail("capture recovery must be opt-in"),
    )

    calls = {"n": 0}

    def _prepare(*_a, **_k):
        calls["n"] += 1
        return {
            "ok": False,
            "capture_ready": False,
            "manager": {"sharing": False},
        }

    monkeypatch.setattr(svc, "build_prepare_payload", _prepare)
    monkeypatch.setattr(svc.time, "sleep", lambda *_a, **_k: None)
    payload = svc.build_up_payload(_args(wait_capture=True, capture_timeout_s=0.1))
    assert payload["ok"] is False
    assert payload["capture_ready"] is False
    assert "capture_recover" not in payload
    assert os.environ["VDISPLAY_ELECTRON_REMOTE_START_CAPTURE"] == "0"
    assert os.environ["VDISPLAY_ELECTRON_ALLOW_REMOTE_START_CAPTURE"] == "0"
    assert os.environ["VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE"] == "0"
    assert os.environ["VDISPLAY_ELECTRON_ALLOW_AUTO_RESUME_CAPTURE"] == "0"
    assert os.environ["VDISPLAY_ELECTRON_UNSAFE_AUTO_CAPTURE"] == "0"


def test_build_up_payload_no_wait_succeeds_when_manager_ready_without_capture(monkeypatch):
    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_stop_portal_screencast", lambda *_a, **_k: None)
    monkeypatch.setattr(svc, "_clear_browser_bridge", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr(svc, "electron_up", lambda *_a, **_k: 0)
    monkeypatch.setattr(
        svc,
        "build_prepare_payload",
        lambda *_a, **_k: {
            "ok": False,
            "capture_ready": False,
            "manager": {"ok": True, "sharing": False},
        },
    )
    payload = svc.build_up_payload(_args(wait_capture=False))
    assert payload["ok"] is True
    assert payload["awaiting_capture"] is True
    assert payload["capture_ready"] is False


def test_build_resume_payload_triggers_main_capture(monkeypatch):
    monkeypatch.setattr(
        svc,
        "build_prepare_payload",
        lambda *_a, **_k: {"capture_ready": False, "manager": {"sharing": False, "sharedDisplayId": "33"}},
    )
    monkeypatch.setattr(svc, "_port_open", lambda *_a, **_k: True)
    monkeypatch.setattr(
        svc,
        "_recover_electron_capture",
        lambda *_a, **_k: {"ok": True, "main_capture": {"ok": True}},
    )
    monkeypatch.setattr(
        svc,
        "_capture_ready_from_prepare",
        lambda *_a, **_k: (True, {"capture_ready": True, "manager": {"sharing": True}}),
    )
    payload = svc.build_resume_payload(_args())
    assert payload["ok"] is True
    assert payload["capture_ready"] is True


def test_recover_electron_capture_keeps_already_active_stream(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(svc, "_port_open", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_trigger_electron_share_start", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr(
        svc,
        "_trigger_electron_share_stop",
        lambda *_a, **_k: calls.append("stop") or {"ok": True, "user_actions": [{"action": "x"}]},
    )

    def _main_capture(*_a, **_k):
        calls.append("main")
        return {"ok": True, "skipped": True, "already_active": True}

    monkeypatch.setattr(svc, "_trigger_electron_main_capture", _main_capture)

    out = svc._recover_electron_capture(_args(), {"sharedDisplayId": "35"})

    assert out["ok"] is True
    assert calls == ["main"]
    assert out["share_stop"] is None
    assert out["main_capture_retry"] is None


def test_compact_share_stop_drops_large_status_fields():
    out = svc._compact_share_stop(
        {
            "ok": True,
            "url": "http://127.0.0.1:8799",
            "sharing": False,
            "user_actions": [{"action": "button.share_monitor"}],
            "displays": [{"id": 35}],
            "frame": {"bytes": 123},
            "capture_stop": {"ok": True, "reason": "services-resume"},
            "renderer_status": {
                "sharing": False,
                "hint": "stopped",
                "error": "",
                "sharedDisplayId": "35",
            },
        }
    )

    assert out == {
        "ok": True,
        "share_url": "http://127.0.0.1:8799",
        "sharing": False,
        "capture_stop": {"ok": True, "reason": "services-resume"},
        "renderer_status": {
            "sharing": False,
            "hint": "stopped",
            "sharedDisplayId": "35",
        },
    }

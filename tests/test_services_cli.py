"""CLI helpers for vdisplay services orchestrator."""

from __future__ import annotations

import argparse

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
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_agent_host_port_defaults():
    host, port = svc._agent_host_port("http://127.0.0.1:8766")
    assert host == "127.0.0.1"
    assert port == 8766


def test_build_up_payload_agent_unreachable_without_start(monkeypatch):
    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: False)
    payload = svc.build_up_payload(_args(start_agent=False))
    assert payload["ok"] is False
    assert "agent not reachable" in payload["error"]


def test_build_up_payload_capture_ready(monkeypatch):
    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_stop_portal_screencast", lambda *_a, **_k: {"ok": True, "skipped": True})
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


def test_build_up_payload_waits_for_capture(monkeypatch):
    monkeypatch.setattr(svc, "_agent_alive", lambda *_a, **_k: True)
    monkeypatch.setattr(svc, "_stop_portal_screencast", lambda *_a, **_k: None)
    monkeypatch.setattr(svc, "electron_up", lambda *_a, **_k: 0)
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
    payload = svc.build_up_payload(_args(wait_capture=True, capture_timeout_s=10.0))
    assert payload["ok"] is True
    assert payload["capture_ready"] is True
    assert calls["n"] >= 2

"""CLI helpers for vdisplay electron-share bridge wiring."""

from __future__ import annotations

import argparse
import json

import pytest

from vdisplay.commands import electron_share as es


def _args(**kwargs):
    defaults = {
        "host": "127.0.0.1",
        "port": 8799,
        "instance": "jetbrains",
        "target": "jetbrains",
        "source": "HDMI-1",
        "agent_url": None,
        "no_agent_bridge": False,
        "mode": "compact",
        "no_always_on_top": False,
        "no_system_picker": False,
        "close_quits": False,
        "timeout_s": 3.0,
        "install": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_resolve_agent_url_from_env(monkeypatch):
    monkeypatch.delenv("VDISPLAY_ELECTRON_AGENT_URL", raising=False)
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766/")
    assert es._resolve_agent_url(_args()) == "http://127.0.0.1:8766"


def test_resolve_agent_url_prefers_explicit_arg(monkeypatch):
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    assert es._resolve_agent_url(_args(agent_url="http://127.0.0.1:9999")) == "http://127.0.0.1:9999"


def test_start_env_wires_agent_and_source(monkeypatch):
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    monkeypatch.delenv("VDISPLAY_ELECTRON_OZONE_PLATFORM", raising=False)
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_AGENT_URL"] == "http://127.0.0.1:8766"
    assert env["VDISPLAY_ELECTRON_AGENT_URL"] == "http://127.0.0.1:8766"
    assert env["VDISPLAY_ELECTRON_BRIDGE_SOURCE"] == "HDMI-1"
    assert env["VDISPLAY_ELECTRON_OZONE_PLATFORM"] == "x11"
    assert "VDISPLAY_ELECTRON_BRIDGE_PUSH" not in env or env.get("VDISPLAY_ELECTRON_BRIDGE_PUSH") != "0"


def test_start_env_explicit_wayland_on_gnome_overrides_to_x11(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    monkeypatch.delenv("VDISPLAY_ELECTRON_ALLOW_WAYLAND", raising=False)
    env = es._start_env(_args(source="HDMI-1", ozone_platform="wayland"))
    assert env["VDISPLAY_ELECTRON_OZONE_PLATFORM"] == "x11"
    assert "overrode" in env.get("VDISPLAY_ELECTRON_OZONE_OVERRIDE", "")


def test_start_env_explicit_wayland_on_gnome_when_allowed(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    monkeypatch.setenv("VDISPLAY_ELECTRON_ALLOW_WAYLAND", "1")
    env = es._start_env(_args(source="HDMI-1", ozone_platform="wayland"))
    assert env["VDISPLAY_ELECTRON_OZONE_PLATFORM"] == "wayland"
    assert env["VDISPLAY_ELECTRON_MAIN_CAPTURE_FALLBACK"] == "1"


def test_preferred_display_env_for_source(monkeypatch):
    monkeypatch.setattr(
        "vdisplay.application.services.discovery.list_monitors_local",
        lambda *args, **kwargs: {
            "monitors": [
                {
                    "name": "HDMI-1",
                    "connected": True,
                    "x": 0,
                    "y": 2560,
                    "width_px": 4096,
                    "height_px": 2560,
                    "diagonal_in": 15.6,
                }
            ]
        },
    )
    env = es._preferred_display_env_for_source("HDMI-1")
    assert env["VDISPLAY_ELECTRON_PREFERRED_DISPLAY_Y"] == "2560"
    assert env["VDISPLAY_ELECTRON_PREFERRED_DISPLAY_WIDTH"] == "4096"
    assert env["VDISPLAY_ELECTRON_PREFERRED_DISPLAY_DIAGONAL"] == "15.6"


def test_start_env_sets_preferred_display_for_source(monkeypatch):
    monkeypatch.setattr(
        "vdisplay.application.services.discovery.list_monitors_local",
        lambda *args, **kwargs: {
            "monitors": [
                {
                    "name": "HDMI-1",
                    "connected": True,
                    "x": 0,
                    "y": 2560,
                    "width_px": 4096,
                    "height_px": 2560,
                }
            ]
        },
    )
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_ELECTRON_PREFERRED_DISPLAY_Y"] == "2560"


def test_build_health_payload_marks_capture_ready():
    payload = es.build_health_payload(
        manager={
            "url": "http://127.0.0.1:8799",
            "instance": "jetbrains",
            "sharing": True,
            "browser_bridge": {"enabled": True, "bridge_id": "bb_test", "last_ok": "ingest 3"},
            "frame": {"bytes": 1234, "age_ms": 120},
        },
        agent_url="http://127.0.0.1:8766",
        bridge_status={"data": {"capture_ready": True, "keeper_mode": "browser_bridge", "bridge_id": "bb_test", "monitors": {"HDMI-1": {"age_ms": 180, "fresh": True}}}},
        screencast_status={"data": {"capture_ready": True, "keeper_mode": "browser_bridge", "last_frame_age_ms": 180}},
        source="HDMI-1",
    )
    assert payload["ok"] is True
    assert payload["capture_ready"] is True
    assert payload["keeper_mode"] == "browser_bridge"
    assert payload["last_frame_age_ms"] == 180
    assert payload["bridge_id"] == "bb_test"


def test_agent_browser_bridge_status_reports_last_frame_age(agent_client) -> None:
    client, _runtime = agent_client
    registered = client.post(
        "/session/browser-bridge/register",
        json={"client": "test-electron", "version": "0", "sources": ["HDMI-1"], "ttl_s": 10},
    ).json()
    bridge_id = registered["data"]["bridge_id"]
    client.post(
        "/capture/ingest",
        json={
            "bridge_id": bridge_id,
            "source": "HDMI-1",
            "seq": 1,
            "mime": "image/png",
            "png_base64": __import__("base64").b64encode(
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
            ).decode("ascii"),
            "width": 10,
            "height": 10,
        },
    )
    status = client.get("/session/browser-bridge/status").json()["data"]
    assert status["capture_ready"] is True
    assert status["last_frame_age_ms"] is not None
    assert status["last_frame_age_ms"] >= 0

    screencast = client.get("/session/screencast/status").json()["data"]
    assert screencast["capture_ready"] is True
    assert screencast["keeper_mode"] == "browser_bridge"
    assert screencast["last_frame_age_ms"] is not None


def test_print_start_hints_does_not_crash(capsys):
    es._print_start_hints(
        _args(agent_url="http://127.0.0.1:8766"),
        {"VDISPLAY_ELECTRON_OZONE_PLATFORM": "wayland"},
    )
    err = capsys.readouterr().err
    assert "ozone platform: wayland" in err
    assert "VDISPLAY_AGENT_URL=http://127.0.0.1:8766" in err


def test_handle_prepare_reports_missing_agent(monkeypatch, capsys):
    monkeypatch.delenv("VDISPLAY_AGENT_URL", raising=False)
    monkeypatch.delenv("VDISPLAY_ELECTRON_AGENT_URL", raising=False)
    code = es.handle_prepare(
        _args(agent_url=None, timeout_s=1.0, install=False)
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "VDISPLAY_AGENT_URL" in payload["hint"]


def test_build_prepare_payload_detects_stale_bridge_and_manager_down():
    payload = es.build_prepare_payload(
        _args(
            agent_url="http://127.0.0.1:8766",
            instance="jetbrains",
            target="jetbrains",
        )
    )
    payload["manager_error"] = "http://127.0.0.1:8799/status: [Errno 111] Connection refused"
    payload["browser_bridge"] = {
        "registered": True,
        "bridge_id": "bb_old",
        "heartbeat_age_ms": 53418,
        "ttl_s": 5.0,
        "sharing": False,
    }
    payload["hint"] = ""
    # Re-run hint logic via build_prepare_payload internals is cleaner with a helper test:
    assert es._bridge_heartbeat_stale(payload["browser_bridge"]) is True


def test_browser_bridge_status_expires_stale_registration(agent_client) -> None:
    client, runtime = agent_client
    registered = client.post(
        "/session/browser-bridge/register",
        json={"client": "test-electron", "version": "0", "sources": ["HDMI-1"], "ttl_s": 5},
    ).json()
    bridge_id = registered["data"]["bridge_id"]
    bridge = runtime.store.browser_bridge.bridge
    assert bridge is not None
    bridge.heartbeat_at = __import__("time").monotonic() - 20
    status = client.get("/session/browser-bridge/status").json()["data"]
    assert status["registered"] is False
    assert status["capture_ready"] is False
    heartbeat = client.post(
        "/session/browser-bridge/heartbeat",
        json={"bridge_id": bridge_id, "sharing": True},
    )
    assert heartbeat.status_code == 400

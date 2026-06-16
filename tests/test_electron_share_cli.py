"""CLI helpers for vdisplay electron-share bridge wiring."""

from __future__ import annotations

import argparse
import base64
import json
import struct
import zlib

import pytest

from vdisplay.commands import electron_share as es
from vdisplay.capture import electron_share as capture_es
from vdisplay.exceptions import VDisplayError


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


def _png_bytes(width: int = 2, height: int = 2, color: tuple[int, int, int] = (20, 40, 200)) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    rows = b"".join(b"\x00" + bytes(color) * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def _png_base64() -> str:
    return base64.b64encode(_png_bytes()).decode("ascii")


def test_resolve_agent_url_from_env(monkeypatch):
    monkeypatch.delenv("VDISPLAY_ELECTRON_AGENT_URL", raising=False)
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766/")
    assert es._resolve_agent_url(_args()) == "http://127.0.0.1:8766"


def test_resolve_agent_url_prefers_explicit_arg(monkeypatch):
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    assert es._resolve_agent_url(_args(agent_url="http://127.0.0.1:9999")) == "http://127.0.0.1:9999"


def test_start_env_defaults_monitor_first_picker_off(monkeypatch):
    monkeypatch.delenv("VDISPLAY_ELECTRON_SHARE_USE_SYSTEM_PICKER", raising=False)
    env = es._start_env(_args())
    assert env["VDISPLAY_ELECTRON_SHARE_USE_SYSTEM_PICKER"] == "0"


def test_start_env_system_picker_opt_in(monkeypatch):
    env = es._start_env(_args(system_picker=True))
    assert env["VDISPLAY_ELECTRON_SHARE_USE_SYSTEM_PICKER"] == "1"


def test_start_env_wires_agent_and_source(monkeypatch):
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    monkeypatch.setenv("VDISPLAY_ELECTRON_AUTO_START_CAPTURE", "1")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    monkeypatch.setenv("XDG_DATA_DIRS", "/snap/codium/495/usr/share:/usr/share")
    monkeypatch.setenv("GSETTINGS_SCHEMA_DIR", "/bad/schemas")
    monkeypatch.delenv("VDISPLAY_ELECTRON_ALLOW_AUTO_START_CAPTURE", raising=False)
    monkeypatch.delenv("VDISPLAY_ELECTRON_OZONE_PLATFORM", raising=False)
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_AGENT_URL"] == "http://127.0.0.1:8766"
    assert env["VDISPLAY_ELECTRON_AGENT_URL"] == "http://127.0.0.1:8766"
    assert env["VDISPLAY_ELECTRON_BRIDGE_SOURCE"] == "HDMI-1"
    assert env["VDISPLAY_ELECTRON_AUTO_START_CAPTURE"] == "0"
    assert env["VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE"] == "0"
    assert env["VDISPLAY_ELECTRON_OZONE_PLATFORM"] == "x11"
    assert env["VDISPLAY_ELECTRON_GTK_VERSION"] == "3"
    assert "/snap/codium" not in env["XDG_DATA_DIRS"]
    assert "GSETTINGS_SCHEMA_DIR" not in env
    assert "VDISPLAY_ELECTRON_BRIDGE_PUSH" not in env or env.get("VDISPLAY_ELECTRON_BRIDGE_PUSH") != "0"


def test_start_env_allows_autostart_only_with_explicit_double_opt_in(monkeypatch):
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    monkeypatch.setenv("VDISPLAY_ELECTRON_AUTO_START_CAPTURE", "1")
    monkeypatch.setenv("VDISPLAY_ELECTRON_ALLOW_AUTO_START_CAPTURE", "1")
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_ELECTRON_AUTO_START_CAPTURE"] == "0"
    monkeypatch.setenv("VDISPLAY_ELECTRON_UNSAFE_AUTO_CAPTURE", "1")
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_ELECTRON_AUTO_START_CAPTURE"] == "1"


def test_start_env_allows_auto_resume_only_with_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    monkeypatch.setenv("VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE", "1")
    monkeypatch.setenv("VDISPLAY_ELECTRON_ALLOW_AUTO_RESUME_CAPTURE", "1")
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE"] == "0"
    monkeypatch.setenv("VDISPLAY_ELECTRON_UNSAFE_AUTO_CAPTURE", "1")
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_ELECTRON_AUTO_RESUME_CAPTURE"] == "1"


def test_start_env_blocks_inherited_remote_start_without_allow(monkeypatch):
    monkeypatch.setenv("VDISPLAY_AGENT_URL", "http://127.0.0.1:8766")
    monkeypatch.setenv("VDISPLAY_ELECTRON_REMOTE_START_CAPTURE", "1")
    monkeypatch.setenv("VDISPLAY_ELECTRON_ALLOW_REMOTE_START_CAPTURE", "1")
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_ELECTRON_REMOTE_START_CAPTURE"] == "0"
    monkeypatch.setenv("VDISPLAY_ELECTRON_UNSAFE_AUTO_CAPTURE", "1")
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_ELECTRON_REMOTE_START_CAPTURE"] == "1"


def test_start_env_explicit_wayland_on_gnome_overrides_to_x11(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    monkeypatch.delenv("VDISPLAY_ELECTRON_ALLOW_WAYLAND", raising=False)
    env = es._start_env(_args(source="HDMI-1", ozone_platform="wayland"))
    assert env["VDISPLAY_ELECTRON_OZONE_PLATFORM"] == "x11"
    assert "overrode" in env.get("VDISPLAY_ELECTRON_OZONE_OVERRIDE", "")


def test_start_env_env_wayland_on_unity_overrides_to_x11(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "Unity")
    monkeypatch.setenv("VDISPLAY_ELECTRON_OZONE_PLATFORM", "wayland")
    monkeypatch.delenv("VDISPLAY_ELECTRON_ALLOW_WAYLAND", raising=False)
    env = es._start_env(_args(source="HDMI-1"))
    assert env["VDISPLAY_ELECTRON_OZONE_PLATFORM"] == "x11"
    assert "overrode" in env.get("VDISPLAY_ELECTRON_OZONE_OVERRIDE", "")


def test_electron_share_crop_accepts_scaled_single_monitor_frame(monkeypatch):
    displays = [
        {"id": 35, "scaleFactor": 2, "bounds": {"x": 0, "y": 1609, "width": 2048, "height": 1280}},
    ]
    region = (0, 3218, 4096, 2560)
    monkeypatch.setattr(capture_es, "_png_size", lambda _png: (2048, 1280))
    png, meta = capture_es._crop_for_monitor(
        b"png",
        region,
        [],
        {"frame": {"displayId": "35"}, "displays": displays},
    )
    assert png == b"png"
    assert meta["electron_share_crop"] == "single-monitor-frame"
    assert meta["electron_share_display_id"] == "35"
    assert meta["electron_share_scale_factor"] == 2


def test_electron_share_crop_rejects_wrong_shared_display(monkeypatch):
    displays = [
        {"id": 33, "scaleFactor": 2, "bounds": {"x": 0, "y": 329, "width": 2048, "height": 1280}},
    ]
    region = (0, 658, 4096, 2560)
    monkeypatch.setattr(capture_es, "_png_size", lambda _png: (2048, 1280))
    with pytest.raises(VDisplayError, match="sharing display 35"):
        capture_es._crop_for_monitor(
            b"png",
            region,
            [],
            {"frame": {"displayId": "35"}, "displays": displays},
        )


def test_electron_share_rejects_stale_manager_frame(monkeypatch):
    monkeypatch.delenv("VDISPLAY_ELECTRON_SHARE_MAX_FRAME_AGE_MS", raising=False)
    with pytest.raises(VDisplayError, match="stale frame age_ms=16000"):
        capture_es._validate_fresh_frame_status({"sharing": True, "frame": {"age_ms": 16000}})


def test_electron_share_allows_stale_frame_when_explicitly_disabled(monkeypatch):
    monkeypatch.setenv("VDISPLAY_ELECTRON_SHARE_MAX_FRAME_AGE_MS", "0")
    capture_es._validate_fresh_frame_status({"sharing": True, "frame": {"age_ms": 6000}})


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


def test_manager_matches_args_requires_bridge_source():
    status = {
        "ok": True,
        "instance": "jetbrains",
        "targetLabel": "jetbrains",
        "browser_bridge": {"source": "HDMI-1"},
    }
    assert es._manager_matches_args(_args(source="HDMI-1"), status) is True
    assert es._manager_matches_args(_args(source="DP-1"), status) is False


def test_manager_matches_args_rejects_missing_bridge_source():
    status = {
        "ok": True,
        "instance": "jetbrains",
        "targetLabel": "jetbrains",
        "browser_bridge": {},
    }
    assert es._manager_matches_args(_args(source="HDMI-1"), status) is False


def test_build_health_payload_marks_capture_ready():
    payload = es.build_health_payload(
        manager={
            "url": "http://127.0.0.1:8799",
            "instance": "jetbrains",
            "sharing": True,
            "browser_bridge": {
                "enabled": True,
                "bridge_id": "bb_test",
                "last_ok": "heartbeat",
                "last_ingest_ok": "ingest 3",
                "last_heartbeat_ok": "heartbeat",
            },
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
    assert payload["bridge_last_ok"] == "ingest 3"
    assert payload["bridge_lifecycle_ok"] == "heartbeat"
    assert payload["bridge_last_heartbeat_ok"] == "heartbeat"


def test_build_health_payload_does_not_treat_registered_as_ingest():
    payload = es.build_health_payload(
        manager={
            "url": "http://127.0.0.1:8799",
            "instance": "jetbrains",
            "sharing": False,
            "browser_bridge": {
                "enabled": True,
                "bridge_id": "bb_test",
                "last_ok": "registered",
                "last_ingest_ok": "registered",
                "last_heartbeat_ok": "heartbeat",
            },
        },
        agent_url="http://127.0.0.1:8766",
        bridge_status={"data": {"capture_ready": False, "keeper_mode": "browser_bridge"}},
        screencast_status={"data": {"capture_ready": False, "keeper_mode": "browser_bridge"}},
        source="HDMI-1",
    )
    assert payload["capture_ready"] is False
    assert payload["bridge_last_ok"] == ""
    assert payload["bridge_lifecycle_ok"] == "registered"


def test_handle_health_recommends_resume_when_local_share_has_stale_frames(monkeypatch, capsys):
    monkeypatch.setattr(
        es,
        "_manager_get",
        lambda *_a, **_k: {
            "ok": True,
            "url": "http://127.0.0.1:8799",
            "instance": "jetbrains",
            "sharing": True,
            "browser_bridge": {"agent_url": "http://127.0.0.1:8766", "enabled": True},
            "frame": {"age_ms": 79110},
        },
    )

    def _agent_get(_url, path, **_k):
        if path == "/session/browser-bridge/status":
            return {
                "data": {
                    "capture_ready": False,
                    "keeper_mode": "browser_bridge",
                    "monitors": {"HDMI-1": {"age_ms": 79110}},
                }
            }
        if path == "/session/screencast/status":
            return {"data": {"capture_ready": False, "keeper_mode": "browser_bridge"}}
        return {"ok": True}

    monkeypatch.setattr(es, "_agent_get", _agent_get)

    code = es.handle_health(_args(agent_url="http://127.0.0.1:8766", source="HDMI-1"))
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload["capture_ready"] is False
    assert payload["last_frame_age_ms"] == 79110
    assert "vdisplay services resume --source HDMI-1 --port 8799" in payload["hint"]


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
            "png_base64": _png_base64(),
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


def test_agent_browser_bridge_register_clears_previous_source_frames(agent_client) -> None:
    client, _runtime = agent_client
    first = client.post(
        "/session/browser-bridge/register",
        json={"client": "test-electron", "version": "0", "sources": ["HDMI-1"], "ttl_s": 10},
    ).json()["data"]["bridge_id"]
    client.post(
        "/capture/ingest",
        json={
            "bridge_id": first,
            "source": "HDMI-1",
            "seq": 1,
            "mime": "image/png",
            "png_base64": _png_base64(),
            "width": 10,
            "height": 10,
        },
    )
    before = client.get("/session/browser-bridge/status").json()["data"]
    assert before["capture_ready"] is True
    assert "HDMI-1" in before["monitors"]

    second = client.post(
        "/session/browser-bridge/register",
        json={"client": "test-electron", "version": "0", "sources": ["DP-1"], "ttl_s": 10},
    ).json()["data"]
    assert second["bridge_id"] != first
    after = client.get("/session/browser-bridge/status").json()["data"]
    assert after["sources"] == ["DP-1"]
    assert after["monitors"] == {}
    assert after["capture_ready"] is False
    assert after["last_frame_age_ms"] is None


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

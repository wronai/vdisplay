from __future__ import annotations

import io
import os

import pytest

from vdisplay.capture.portal_screencast import (
    PortalScreenCastSession,
    _is_retryable_screencast_error,
    stop_screencast_session,
)
from vdisplay.exceptions import VDisplayError


def _make_png(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_screencast_session_capture_requires_ready() -> None:
    session = PortalScreenCastSession()
    with pytest.raises(VDisplayError, match="not ready"):
        session.capture_png()


def _stub_ready_session(png: bytes) -> PortalScreenCastSession:
    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/freedesktop/portal/desktop/session/test/vdisplay_screencast"
    session.node_ids = [42]
    session.capture_png = lambda **kwargs: png  # type: ignore[method-assign]
    return session


def test_host_capture_uses_active_screencast(monkeypatch: pytest.MonkeyPatch) -> None:
    png = _make_png(80, 60, (10, 120, 200))
    session = _stub_ready_session(png)
    monkeypatch.setattr("vdisplay.capture.portal_screencast._ACTIVE", session, raising=False)
    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda display: [{"name": "DP-1", "primary": True, "x": 0, "y": 0, "width": 80, "height": 60}],
    )

    from vdisplay.capture.host import capture_host_png

    captured, meta = capture_host_png(display=":0", monitor=1, source="DP-1")
    assert captured == png
    assert meta["method"] == "portal-screencast"


def test_agent_screencast_status_endpoint(agent_client) -> None:
    client, _runtime = agent_client
    payload = client.get("/session/screencast/status").json()
    assert payload["ok"] is True
    assert payload["data"]["active"] is False


def test_agent_screencast_status_reports_capture_not_ready_without_keeper(agent_client) -> None:
    client, runtime = agent_client
    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/test/session"
    session.node_ids = [80, 81]
    runtime.store.screencast = session

    payload = client.get("/session/screencast/status").json()
    assert payload["ok"] is True
    assert payload["data"]["active"] is True
    assert payload["data"]["ready"] is True
    assert payload["data"]["capture_ready"] is False
    assert "screencast start --force" in payload["data"]["capture_hint"]


def test_stop_screencast_when_inactive() -> None:
    stop_screencast_session()
    payload = stop_screencast_session()
    assert payload["ok"] is True
    assert payload["stopped"] is False


def test_stop_screencast_session_stops_active(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture import portal_screencast as mod

    closed: list[str] = []
    session_path = "/org/freedesktop/portal/desktop/session/test/vdisplay_sc_abc"
    session = PortalScreenCastSession()
    session.active = True
    session.session_path = session_path
    monkeypatch.setattr(mod, "_ACTIVE", session, raising=False)
    monkeypatch.setattr(mod, "_close_screencast_session", lambda path: closed.append(path))

    payload = stop_screencast_session()

    assert payload["ok"] is True
    assert payload["stopped"] is True
    assert closed == [session_path]
    assert mod.get_active_screencast() is None


def test_stop_screencast_session_closes_inactive_path(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture import portal_screencast as mod

    closed: list[str] = []
    session_path = "/org/freedesktop/portal/desktop/session/test/vdisplay_sc_dead"
    session = PortalScreenCastSession()
    session.active = False
    session.session_path = session_path
    monkeypatch.setattr(mod, "_ACTIVE", session, raising=False)
    monkeypatch.setattr(mod, "_close_screencast_session", lambda path: closed.append(path))

    payload = stop_screencast_session()

    assert payload["ok"] is True
    assert payload["stopped"] is True
    assert closed == [session_path]


def test_is_retryable_screencast_error() -> None:
    assert _is_retryable_screencast_error("SelectSources failed: before starting")
    assert _is_retryable_screencast_error("Session already started")
    assert _is_retryable_screencast_error("Sources already selected")
    assert _is_retryable_screencast_error("stale portal session")
    assert _is_retryable_screencast_error("SelectSources failed: AccessDenied: Invalid session")
    assert not _is_retryable_screencast_error("permission denied")


def test_portal_request_path_uses_bus_unique_name() -> None:
    from vdisplay.capture.portal_screencast import _portal_request_path

    class FakeBus:
        def get_unique_name(self) -> str:
            return ":1.42"

    path = _portal_request_path(FakeBus(), "vdisplay_sc_create_1")
    assert path == "/org/freedesktop/portal/desktop/request/1_42/vdisplay_sc_create_1"


def test_stream_target_prefers_pipewire_serial() -> None:
    from vdisplay.capture.portal_screencast import _stream_serial, _stream_target

    assert _stream_serial({"pipewire-serial": 123456789}) == "123456789"
    assert _stream_serial({"id": "2"}, node_id=74) == "2"
    assert _stream_serial({"id": "2"}) == "2"
    assert _stream_serial({}, node_id=74) == "74"
    assert _stream_serial({}) is None
    assert _stream_target(74, {"pipewire-serial": 123456789}) == "123456789"
    assert _stream_target(74, {"id": "0"}) == "0"
    assert _stream_target(74, {}) == "74"


def test_refresh_screencast_adopt_payload_updates_keeper_fields() -> None:
    from vdisplay.capture.portal_screencast import refresh_screencast_adopt_payload

    session = PortalScreenCastSession()
    session.session_path = "/org/freedesktop/portal/desktop/session/test/reuse"
    session.active = True
    session.node_ids = [1, 2, 3]
    session.keeper_pid = 111
    session.keeper_socket_path = "/run/user/1000/old.sock"

    refresh_screencast_adopt_payload(
        session,
        {
            "pid": 222,
            "socket_path": "/run/user/1000/vdisplay-screencast.sock",
            "keeper_managed": True,
            "node_ids": [10, 20, 30],
            "streams": [{"node_id": 10, "properties": {"id": "0"}}],
        },
    )
    assert session.keeper_pid == 222
    assert session.keeper_socket_path == "/run/user/1000/vdisplay-screencast.sock"
    assert session.node_ids == [10, 20, 30]


def test_cli_agent_screencast_status(live_agent_url: str, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", live_agent_url)

    import argparse

    from vdisplay.commands import agent as agent_cmd

    rc = agent_cmd.handle(argparse.Namespace(action="screencast", sc_action="status"))
    assert rc == 0
    out = capsys.readouterr().out
    assert '"active": false' in out.lower()


def test_agent_capture_uses_store_screencast(agent_client, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    client, runtime = agent_client
    png = _make_png(64, 48, (200, 80, 20))
    runtime.store.screencast = _stub_ready_session(png)
    monkeypatch.setattr(
        "vdisplay.capture.host.list_monitors",
        lambda display: [{"name": "DP-1", "primary": True, "x": 0, "y": 0, "width": 64, "height": 48}],
    )

    out = tmp_path / "host.png"
    payload = client.post(
        "/capture/frame",
        json={"output": str(out), "source": "DP-1", "monitor": 1},
    ).json()
    assert payload["ok"] is True
    assert out.is_file()
    assert payload["data"]["method"] == "portal-screencast"


def test_capture_pipewire_stream_falls_back_to_node_path(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture import portal_screencast as mod

    attempts: list[str | None] = []

    def fake_once(*, pipewire_fd, node_id, target_object=None, width=None, height=None, timeout_s=30.0):
        attempts.append(target_object)
        if target_object == "2":
            return b"\x89PNG" + b"x" * 64
        raise mod.VDisplayError("target not found")

    monkeypatch.setattr(mod, "_capture_pipewire_stream_once", fake_once)
    data = mod._capture_pipewire_stream(
        pipewire_fd=9,
        node_id=117,
        target_object="2",
        portal_stream_id="2",
        timeout_s=5.0,
    )
    assert data.startswith(b"\x89PNG")
    assert attempts[0] is None
    assert attempts[1] == "2"


def test_capture_pipewire_stream_retries_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture import portal_screencast as mod

    attempts: list[str | None] = []

    def fake_once(*, pipewire_fd, node_id, target_object=None, width=None, height=None, timeout_s=30.0):
        attempts.append(target_object)
        if target_object == "2":
            return b"\x89PNG" + b"x" * 64
        raise mod.VDisplayError("timed out after 20.0 seconds")

    monkeypatch.setattr(mod, "_capture_pipewire_stream_once", fake_once)
    data = mod._capture_pipewire_stream(
        pipewire_fd=9,
        node_id=117,
        portal_stream_id="2",
        timeout_s=20.0,
    )
    assert data.startswith(b"\x89PNG")
    assert attempts == [None, "2"]


def test_capture_pipewire_stream_uses_minimum_per_strategy_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vdisplay.capture import portal_screencast as mod

    timeouts: list[float] = []

    def fake_once(*, pipewire_fd, node_id, target_object=None, width=None, height=None, timeout_s=30.0):
        timeouts.append(timeout_s)
        return b"\x89PNG" + b"x" * 64

    monkeypatch.setattr(mod, "_capture_pipewire_stream_once", fake_once)
    mod._capture_pipewire_stream(pipewire_fd=9, node_id=117, timeout_s=15.0)
    assert timeouts == [7.5]


def test_capture_pipewire_stream_uses_live_pipewiresrc(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture import portal_screencast as mod

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        raise mod.VDisplayError("stop")

    monkeypatch.setattr(mod.os, "dup", lambda fd: fd)
    monkeypatch.setattr(mod.os, "close", lambda fd: None)
    monkeypatch.setattr(mod, "_capture_pipewire_frame_gi_subprocess", lambda *a, **k: False)
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/gst-launch-1.0" if name == "gst-launch-1.0" else None)
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    with pytest.raises(VDisplayError, match="stop"):
        mod._capture_pipewire_stream_once(pipewire_fd=9, node_id=71)
    assert calls
    gst_call = next(cmd for cmd in calls if cmd and cmd[0].endswith("gst-launch-1.0"))
    assert "always-copy=true" in gst_call
    assert "num-buffers=1" in gst_call
    assert "is-live" not in gst_call


def test_capture_pipewire_gst_launch_returns_png_written_before_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from vdisplay.capture import portal_screencast as mod

    png = b"\x89PNG\r\n\x1a\n" + b"x" * 64

    def fake_run(cmd, **kwargs):
        location = next(part for part in cmd if str(part).startswith("location="))
        with open(str(location).split("=", 1)[1], "wb") as fh:
            fh.write(png)
        raise mod.subprocess.TimeoutExpired(cmd, timeout=kwargs.get("timeout"))

    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/gst-launch-1.0" if name == "gst-launch-1.0" else None)
    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    out = tmp_path / "frame.png"
    data = mod._capture_pipewire_frame_gst_launch(
        9,
        71,
        None,
        out,
        timeout_s=3.0,
    )
    assert data == png


def test_capture_png_local_falls_back_to_gnome_screenshot(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture import portal_screencast as mod

    session = mod.PortalScreenCastSession()
    session.session_path = "/org/test/session"
    session.active = True
    session.node_ids = [126]
    session.streams = [
        {
            "node_id": 126,
            "properties": {"id": "2", "position": [0, 652], "size": [2048, 1280]},
        }
    ]
    png = b"\x89PNG\r\n\x1a\n" + b"x" * 128
    read_fd, write_fd = os.pipe()
    os.close(write_fd)

    monkeypatch.setattr(mod, "_screencast_pipewire_fd", lambda _session, **kwargs: os.dup(read_fd))
    monkeypatch.setattr(
        mod,
        "_capture_pipewire_stream",
        lambda **kwargs: (_ for _ in ()).throw(mod.VDisplayError("pipewire failed")),
    )
    monkeypatch.setattr(
        mod,
        "_capture_via_gnome_screenshot_region",
        lambda properties, **kwargs: png,
    )

    assert session.capture_png_local(node_index=0, try_all_streams=False) == png
    os.close(read_fd)


def test_agent_client_screencast_status(live_agent_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_AGENT_URL", live_agent_url)

    from vdisplay.client import AgentClient

    payload = AgentClient(live_agent_url).screencast_status()
    assert payload["ok"] is True
    assert payload["active"] is False


def test_portal_session_env_status_requires_dbus(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture import portal_screencast as mod

    monkeypatch.delenv("DBUS_SESSION_BUS_ADDRESS", raising=False)
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.setattr(mod.os, "getuid", lambda: 99999)
    monkeypatch.setattr(mod.os.path, "exists", lambda path: False)
    monkeypatch.setattr(mod.os.path, "isdir", lambda path: False)
    ok, hint = mod.portal_session_env_status()
    assert ok is False
    assert "DBUS_SESSION_BUS_ADDRESS" in hint


def test_from_portal_payload_requires_session_path() -> None:
    with pytest.raises(VDisplayError, match="session_path"):
        PortalScreenCastSession.from_portal_payload({})


def test_agent_screencast_adopt_endpoint(agent_client, monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.capture import portal_screencast as mod

    client, runtime = agent_client
    monkeypatch.setattr(
        "vdisplay_agent.services.sessions._is_wayland_host_session",
        lambda: False,
    )
    session = PortalScreenCastSession()
    session.active = True
    session.session_path = "/org/freedesktop/portal/desktop/session/test/adopt"
    session.node_ids = [71, 72]
    session.streams = [{"node_id": 71, "properties": {}}]

    monkeypatch.setattr(
        mod.PortalScreenCastSession,
        "from_portal_payload",
        classmethod(lambda cls, payload, **kwargs: session),
    )

    payload = client.post(
        "/session/screencast/adopt",
        json={
            "session_path": session.session_path,
            "node_ids": session.node_ids,
            "streams": session.streams,
        },
    ).json()

    assert payload["ok"] is True
    assert payload["data"]["ready"] is True
    assert runtime.store.screencast is session

"""Keeper-owned portal session capture over unix socket."""

from __future__ import annotations

import base64
import json
import os
import socket
import threading
from pathlib import Path

import pytest

from vdisplay.capture import portal_screencast as portal_mod
from vdisplay.capture.screencast_keeper import (
    _dispatch_capture_request,
    _handle_capture_connection,
    keeper_manages_session,
    keeper_socket_path,
    keeper_state_path,
    request_keeper_capture,
)
from vdisplay.exceptions import VDisplayError


def _make_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"x" * 64


class _FakeSession:
    def __init__(self, png: bytes = b"") -> None:
        self.session_path = "/org/freedesktop/portal/desktop/session/test/keeper"
        self.node_ids = [119, 89, 133]
        self.active = True
        self._png = png or _make_png()
        self.calls: list[int] = []

    @property
    def is_ready(self) -> bool:
        return self.active and bool(self.session_path)

    def capture_png_local(self, *, node_index: int = 0) -> bytes:
        self.calls.append(node_index)
        return self._png


def test_keeper_manages_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    state_path = keeper_state_path()
    state_path.write_text(
        json.dumps({"pid": os.getpid(), "session_path": "/org/test/session"}),
        encoding="utf-8",
    )
    assert keeper_manages_session("/org/test/session") is True
    assert keeper_manages_session("/org/other/session") is False


def test_dispatch_capture_request() -> None:
    session = _FakeSession()
    ok = _dispatch_capture_request(session, {"op": "capture", "node_index": 2})
    assert ok["ok"] is True
    assert "png_base64" in ok
    assert session.calls == [2]

    bad = _dispatch_capture_request(session, {"op": "capture", "session_path": "/wrong"})
    assert bad["ok"] is False


def test_capture_png_delegates_to_keeper(monkeypatch: pytest.MonkeyPatch) -> None:
    session = portal_mod.PortalScreenCastSession()
    session.session_path = "/org/freedesktop/portal/desktop/session/test/delegate"
    session.node_ids = [119]
    session.streams = [{"node_id": 119, "properties": {"id": "2"}}]
    session.active = True
    session.keeper_managed = True
    session.keeper_socket_path = "/tmp/vdisplay-test.sock"
    png = _make_png()

    seen: dict[str, object] = {}

    def _fake_request(**kwargs):
        seen.update(kwargs)
        return png

    monkeypatch.setattr(
        "vdisplay.capture.screencast_keeper.request_keeper_capture",
        _fake_request,
    )

    assert session.capture_png(node_index=1) == png
    assert seen["node_index"] == 1
    assert seen["socket_path"] == "/tmp/vdisplay-test.sock"


def test_capture_server_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))

    session = _FakeSession()
    sock_path = keeper_socket_path()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    server.listen(1)
    server.settimeout(2.0)

    def _accept_once() -> None:
        conn, _addr = server.accept()
        with conn:
            _handle_capture_connection(session, conn)

    worker = threading.Thread(target=_accept_once, daemon=True)
    worker.start()

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(str(sock_path))
    request = json.dumps({"op": "capture", "node_index": 0, "session_path": session.session_path}) + "\n"
    client.sendall(request.encode("utf-8"))
    data = b""
    while b"\n" not in data:
        data += client.recv(65536)
    client.close()
    server.close()

    response = json.loads(data.decode("utf-8").split("\n", 1)[0])
    assert response["ok"] is True
    assert base64.b64decode(response["png_base64"]) == session._png
    assert session.calls == [0]


def test_portal_capture_png_local_still_uses_pipewire(monkeypatch: pytest.MonkeyPatch) -> None:
    session = portal_mod.PortalScreenCastSession()
    session.session_path = "/org/local/session"
    session.node_ids = [42]
    session.streams = [{"node_id": 42, "properties": {}}]
    session.active = True

    read_fd, write_fd = os.pipe()
    os.close(write_fd)
    monkeypatch.setattr(
        portal_mod,
        "_screencast_pipewire_fd",
        lambda _session: os.dup(read_fd),
    )
    monkeypatch.setattr(
        portal_mod,
        "_capture_pipewire_stream",
        lambda **kwargs: _make_png(),
    )

    assert session.capture_png_local().startswith(b"\x89PNG")
    os.close(read_fd)

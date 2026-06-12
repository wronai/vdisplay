"""Screencast start --force must not reuse stale keeper metadata."""

from __future__ import annotations

import pytest

from vdisplay.application.services.screencast_cli import (
    _start_via_keeper,
    _try_reuse_existing_screencast,
    _verify_keeper_running,
)
from vdisplay.exceptions import VDisplayError


def test_force_never_reuses_existing_screencast(monkeypatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.keeper_capture_ready",
        lambda *args, **kwargs: True,
    )
    status = {"active": True, "ready": True, "keeper_pid": 999}
    assert _try_reuse_existing_screencast(status, force=True) is None


def test_reuse_when_ready_and_not_forced(monkeypatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.keeper_capture_ready",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.read_keeper_state",
        lambda: {"pid": 4242, "socket_path": "/run/user/1000/vdisplay-screencast.sock"},
    )
    status = {"active": True, "ready": True, "session_path": "/org/test/session"}
    payload = _try_reuse_existing_screencast(status, force=False)
    assert payload is not None
    assert payload["reused"] is True
    assert payload["keeper_pid"] == 4242


def test_verify_keeper_running_requires_real_frame_capture(monkeypatch) -> None:
    stopped: list[bool] = []
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.read_keeper_state",
        lambda: {
            "pid": 4242,
            "socket_path": "/run/user/1000/vdisplay-screencast.sock",
            "session_path": "/org/test/session",
            "streams": [{"id": "0"}],
            "node_ids": [123],
        },
    )
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.keeper_capture_ready",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.request_keeper_capture",
        lambda *args, **kwargs: (_ for _ in ()).throw(VDisplayError("frame timeout")),
    )
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.stop_keeper",
        lambda: stopped.append(True),
    )

    with pytest.raises(VDisplayError, match="socket is ready but frame capture failed"):
        _verify_keeper_running(context="start")
    assert stopped == [True]


def test_verify_keeper_running_checks_every_advertised_stream(monkeypatch) -> None:
    calls: list[int] = []
    state = {
        "pid": 4242,
        "socket_path": "/run/user/1000/vdisplay-screencast.sock",
        "session_path": "/org/test/session",
        "streams": [{"id": "0"}, {"id": "1"}],
        "node_ids": [111, 222],
    }
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.read_keeper_state",
        lambda: state,
    )
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.keeper_capture_ready",
        lambda *args, **kwargs: True,
    )

    def fake_request_keeper_capture(*, node_index, **kwargs) -> bytes:
        calls.append(node_index)
        return b"\x89PNG\r\n\x1a\nfake"

    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.request_keeper_capture",
        fake_request_keeper_capture,
    )

    assert _verify_keeper_running(context="start") is state
    assert calls == [0, 1]


def test_start_via_keeper_rolls_back_agent_adopt_when_frame_verify_fails(
    monkeypatch,
) -> None:
    stopped: list[bool] = []

    class Client:
        def adopt_screencast(self, **kwargs):
            return {"active": True, "ready": True}

        def stop_screencast(self):
            stopped.append(True)
            return {"ok": True}

    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli.spawn_keeper",
        lambda **kwargs: {
            "session_path": "/org/test/session",
            "streams": [{"node_id": 1, "properties": {"id": "0"}}],
            "node_ids": [1],
            "stream_targets": ["0"],
            "socket_path": "/run/user/1000/vdisplay-screencast.sock",
            "runtime_dir": "/run/user/1000",
            "pid": 4242,
        },
    )
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli._verify_keeper_running",
        lambda **kwargs: (_ for _ in ()).throw(VDisplayError("frame verify failed")),
    )
    monkeypatch.setattr(
        "vdisplay.application.services.screencast_cli._mark_local_start_failure",
        lambda: None,
    )

    with pytest.raises(VDisplayError, match="frame verify failed"):
        _start_via_keeper(Client(), timeout_s=1.0, multiple=True)
    assert stopped == [True]

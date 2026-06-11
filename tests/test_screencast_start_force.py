"""Screencast start --force must not reuse stale keeper metadata."""

from __future__ import annotations

from vdisplay.application.services.screencast_cli import _try_reuse_existing_screencast


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

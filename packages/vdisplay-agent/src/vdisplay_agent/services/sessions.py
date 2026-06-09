"""Virtual, mirror, relay, and screencast session lifecycle."""

from __future__ import annotations

from typing import Any

from vdisplay import MirrorSession, VirtualDisplaySession, WindowRelaySession
from vdisplay.exceptions import VDisplayError

from ..session_store import SessionRecord, SessionStore


def _session_started(record, *, mode: str) -> dict[str, Any]:
    return {
        "ok": True,
        "session_id": record.session_id,
        "mode": mode,
        "info": record.handle.info(),
        "capabilities": record.handle.capabilities(),
    }


def start_virtual(
    store: SessionStore,
    *,
    width: int = 1280,
    height: int = 720,
    display: str = ":99",
) -> dict[str, Any]:
    session = VirtualDisplaySession.create(width=width, height=height, display=display)
    session.start()
    record = store.register(kind="virtual", handle=session, prefix="virt")
    return _session_started(record, mode="virtual")


def start_mirror(
    store: SessionStore,
    *,
    source: str = "primary",
    target: str | None = None,
    display: str | None = None,
) -> dict[str, Any]:
    session = MirrorSession.create(source=source, target=target, display=display)
    session.start()
    record = store.register(kind="mirror", handle=session, prefix="mir")
    return _session_started(record, mode="mirror")


def start_relay(store: SessionStore, *, display: str | None = None) -> dict[str, Any]:
    if store.relay is None:
        store.relay = WindowRelaySession.create(display=display)
        store.relay.start()
    record = store.register(kind="relay", handle=store.relay, prefix="relay")
    return _session_started(record, mode="relay")


def start_screencast(
    store: SessionStore,
    *,
    interactive: bool = True,
    timeout_s: float = 120.0,
    multiple: bool | None = None,
) -> dict[str, Any]:
    from vdisplay.capture.portal_screencast import _screencast_multiple, start_screencast_session

    allow_multiple = _screencast_multiple(multiple)
    session = start_screencast_session(
        interactive=interactive,
        timeout_s=timeout_s,
        multiple=allow_multiple,
    )
    store.screencast = session
    store.screencast_multiple = allow_multiple
    return {"ok": True, "multiple": allow_multiple, **session.status()}


def stop_screencast(store: SessionStore) -> dict[str, Any]:
    from vdisplay.capture.portal_screencast import get_active_screencast, stop_screencast_session

    session = store.screencast or get_active_screencast()
    store.screencast = None
    if session is None:
        return {"ok": True, "stopped": False}
    return session.stop()


def screencast_status(store: SessionStore) -> dict[str, Any]:
    from vdisplay.capture.portal_screencast import get_active_screencast

    session = store.screencast or get_active_screencast()
    if session is None:
        return {"ok": True, "active": False, "ready": False}
    return {"ok": True, **session.status()}


def start_terminal(
    store: SessionStore,
    *,
    command: str | None = None,
    session_id: str | None = None,
    rows: int = 24,
    cols: int = 80,
    lines: list[str] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    from vdisplay.control.providers.terminal_session import default_registry

    registry = default_registry()
    if command:
        session = registry.open_process(command, session_id=session_id, rows=rows, cols=cols, title=title)
    else:
        session = registry.open_mock(
            session_id=session_id,
            lines=lines or ["READY"],
            rows=rows,
            cols=cols,
            title=title,
        )
    record = SessionRecord(
        session_id=session.session_id,
        kind="terminal",
        handle=session,
    )
    store.sessions[session.session_id] = record
    return {
        "ok": True,
        "session_id": session.session_id,
        "mode": "terminal",
        "command": session.command,
        "title": session.title,
        "rows": rows,
        "cols": cols,
    }


def stop_session(store: SessionStore, session_id: str) -> dict[str, Any]:
    record = store.pop(session_id)
    if record.kind == "relay" and record.handle is store.relay:
        store.clear_relay()
    elif record.kind == "terminal":
        record.handle.close()
    else:
        record.handle.stop()
    return {"ok": True, "session_id": session_id, "stopped": True}


def shutdown(store: SessionStore) -> None:
    from vdisplay.capture.portal_screencast import stop_screencast_session

    from . import sampler as sampler_svc

    sampler_svc.stop_sampler(store)
    store.screencast = None
    store.screencast_multiple = False
    if store.virtual is not None:
        store.virtual.stop()
        store.virtual = None
        store.virtual_key = None
    stop_screencast_session()
    for session_id in list(store.sessions):
        try:
            stop_session(store, session_id)
        except VDisplayError:
            pass
    store.clear_relay()

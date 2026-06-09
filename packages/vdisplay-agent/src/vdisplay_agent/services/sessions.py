"""Virtual, mirror, relay, and screencast session lifecycle."""

from __future__ import annotations

from typing import Any

from vdisplay import MirrorSession, VirtualDisplaySession, WindowRelaySession
from vdisplay.exceptions import VDisplayError

from ..session_store import SessionStore


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
) -> dict[str, Any]:
    from vdisplay.capture.portal_screencast import start_screencast_session

    session = start_screencast_session(interactive=interactive, timeout_s=timeout_s)
    store.screencast = session
    return {"ok": True, **session.status()}


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


def stop_session(store: SessionStore, session_id: str) -> dict[str, Any]:
    record = store.pop(session_id)
    if record.kind == "relay" and record.handle is store.relay:
        store.clear_relay()
    else:
        record.handle.stop()
    return {"ok": True, "session_id": session_id, "stopped": True}


def shutdown(store: SessionStore) -> None:
    from vdisplay.capture.portal_screencast import stop_screencast_session

    store.screencast = None
    stop_screencast_session()
    for session_id in list(store.sessions):
        try:
            stop_session(store, session_id)
        except VDisplayError:
            pass
    store.clear_relay()

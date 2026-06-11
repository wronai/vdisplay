"""Virtual, mirror, relay, and screencast session lifecycle."""

from __future__ import annotations

from typing import Any

from vdisplay import MirrorSession, VirtualDisplaySession, WindowRelaySession
from vdisplay.exceptions import VDisplayError

from ..session_store import SessionRecord, SessionStore
from ..task_store import TaskStore
from . import tasks as task_svc


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
    task_store: TaskStore | None = None,
    broker_id: str = "",
) -> dict[str, Any]:
    session = VirtualDisplaySession.create(width=width, height=height, display=display)
    session.start()
    record = store.register(kind="virtual", handle=session, prefix="virt")
    if task_store is not None and broker_id:
        task_svc.register_session_task(task_store, broker_id=broker_id, record=record)
    return _session_started(record, mode="virtual")


def start_mirror(
    store: SessionStore,
    *,
    source: str = "primary",
    target: str | None = None,
    display: str | None = None,
    task_store: TaskStore | None = None,
    broker_id: str = "",
) -> dict[str, Any]:
    session = MirrorSession.create(source=source, target=target, display=display)
    session.start()
    record = store.register(kind="mirror", handle=session, prefix="mir")
    if task_store is not None and broker_id:
        task_svc.register_session_task(task_store, broker_id=broker_id, record=record)
    return _session_started(record, mode="mirror")


def start_relay(
    store: SessionStore,
    *,
    display: str | None = None,
    task_store: TaskStore | None = None,
    broker_id: str = "",
) -> dict[str, Any]:
    if store.relay is None:
        store.relay = WindowRelaySession.create(display=display)
        store.relay.start()
    record = store.register(kind="relay", handle=store.relay, prefix="relay")
    if task_store is not None and broker_id:
        task_svc.register_session_task(task_store, broker_id=broker_id, record=record)
    return _session_started(record, mode="relay")


def _screencast_payload(
    store: SessionStore,
    session: Any,
    *,
    allow_multiple: bool,
    reused: bool = False,
    task_store: TaskStore | None = None,
    broker_id: str = "",
    interactive: bool = True,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    store.screencast = session
    store.screencast_multiple = allow_multiple
    payload = {"ok": True, "multiple": allow_multiple, **session.status()}
    if reused:
        payload["reused"] = True
    if task_store is not None and broker_id and not (reused and store.screencast_task_id):
        store.screencast_task_id = task_svc.begin_screencast_task(
            task_store,
            broker_id=broker_id,
            config={
                "interactive": interactive,
                "timeout_s": timeout_s,
                "multiple": allow_multiple,
            },
        )
        payload["task_id"] = store.screencast_task_id
    return payload


def adopt_screencast(
    store: SessionStore,
    body: dict[str, Any],
    *,
    task_store: TaskStore | None = None,
    broker_id: str = "",
) -> dict[str, Any]:
    from vdisplay.capture.portal_screencast import (
        PortalScreenCastSession,
        _screencast_multiple,
        ensure_portal_session_env,
        get_active_screencast,
    )

    ensure_portal_session_env()
    allow_multiple = _screencast_multiple(body.get("multiple"))
    adopt_path = str(body.get("session_path") or "").strip()
    existing = store.screencast or get_active_screencast()
    if (
        existing is not None
        and existing.is_ready
        and adopt_path
        and adopt_path == existing.session_path
    ):
        return _screencast_payload(
            store,
            existing,
            allow_multiple=allow_multiple,
            reused=True,
            task_store=task_store,
            broker_id=broker_id,
        )

    _release_store_screencast_if_different(store, adopt_path, task_store=task_store)
    session = PortalScreenCastSession.from_portal_payload(body, verify_remote=False)
    return _screencast_payload(
        store,
        session,
        allow_multiple=allow_multiple,
        task_store=task_store,
        broker_id=broker_id,
    )


def _release_store_screencast_if_different(
    store: SessionStore,
    adopt_path: str,
    *,
    task_store: TaskStore | None = None,
) -> None:
    """Drop broker screencast without closing the portal session we are about to adopt."""
    from vdisplay.capture.portal_screencast import get_active_screencast

    session = store.screencast or get_active_screencast()
    store.screencast = None
    if task_store is not None and store.screencast_task_id:
        task_svc.end_screencast_task(task_store, store.screencast_task_id)
        store.screencast_task_id = None
    if session is None:
        return
    if adopt_path and str(session.session_path or "") == adopt_path:
        from vdisplay.capture.portal_screencast import _set_active, _set_active_if_self

        if _set_active_if_self(session):
            _set_active(None)
        return
    session.stop()


def start_screencast(
    store: SessionStore,
    *,
    interactive: bool = True,
    timeout_s: float = 120.0,
    multiple: bool | None = None,
    task_store: TaskStore | None = None,
    broker_id: str = "",
) -> dict[str, Any]:
    from vdisplay.capture.linux_xwd import is_blank_png
    from vdisplay.capture.portal_screencast import (
        _screencast_multiple,
        ensure_portal_session_env,
        get_active_screencast,
        portal_session_env_status,
        prepare_portal_screencast_start,
        start_screencast_session,
    )

    allow_multiple = _screencast_multiple(multiple)
    ensure_portal_session_env()
    portal_ok, portal_hint = portal_session_env_status()
    if not portal_ok:
        raise VDisplayError(
            f"agent portal session unavailable: {portal_hint}. "
            "Restart vdisplay-agent serve from a local GNOME terminal (not SSH/Cursor)."
        )

    prepare_portal_screencast_start()
    existing = store.screencast or get_active_screencast()
    if existing is not None and existing.is_ready:
        try:
            if not is_blank_png(existing.capture_png()):
                return _screencast_payload(
                    store,
                    existing,
                    allow_multiple=allow_multiple,
                    reused=True,
                    task_store=task_store,
                    broker_id=broker_id,
                    interactive=interactive,
                    timeout_s=timeout_s,
                )
        except VDisplayError:
            pass

    stop_screencast(store, task_store=task_store)
    session = start_screencast_session(
        interactive=interactive,
        timeout_s=timeout_s,
        multiple=allow_multiple,
    )
    payload = _screencast_payload(
        store,
        session,
        allow_multiple=allow_multiple,
        task_store=task_store,
        broker_id=broker_id,
        interactive=interactive,
        timeout_s=timeout_s,
    )
    try:
        from ..broker_events import log_broker_event

        log_broker_event(
            "screencast_start",
            ok=True,
            ready=bool(payload.get("ready")),
            session_path=payload.get("session_path"),
            node_ids=payload.get("node_ids"),
        )
    except Exception:
        pass
    return payload


def stop_screencast(store: SessionStore, *, task_store: TaskStore | None = None) -> dict[str, Any]:
    from vdisplay.capture.portal_screencast import get_active_screencast, stop_screencast_session

    session = store.screencast or get_active_screencast()
    store.screencast = None
    if task_store is not None and store.screencast_task_id:
        task_svc.end_screencast_task(task_store, store.screencast_task_id)
        store.screencast_task_id = None
    if session is None:
        return stop_screencast_session()
    payload = session.stop()
    stop_screencast_session()
    return payload


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
    task_store: TaskStore | None = None,
    broker_id: str = "",
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
    if task_store is not None and broker_id:
        task_svc.register_session_task(task_store, broker_id=broker_id, record=record)
    return {
        "ok": True,
        "session_id": session.session_id,
        "mode": "terminal",
        "command": session.command,
        "title": session.title,
        "rows": rows,
        "cols": cols,
    }


def start_browser(
    store: SessionStore,
    *,
    url: str,
    session_id: str | None = None,
    headless: bool = True,
    title: str | None = None,
    engine: str | None = None,
    task_store: TaskStore | None = None,
    broker_id: str = "",
) -> dict[str, Any]:
    from vdisplay.control.providers.browser_session import default_registry
    from vdisplay.control.providers.browser_sync_executor import run_browser_sync

    registry = default_registry()
    session = run_browser_sync(
        registry.open,
        url,
        session_id=session_id,
        headless=headless,
        title=title,
        engine=engine,
    )
    record = SessionRecord(
        session_id=session.session_id,
        kind="browser",
        handle=session,
    )
    store.sessions[session.session_id] = record
    if task_store is not None and broker_id:
        task_svc.register_session_task(task_store, broker_id=broker_id, record=record)
    return {
        "ok": True,
        "session_id": session.session_id,
        "mode": "browser",
        "url": session.url,
        "title": session.title,
        "headless": headless,
        "engine": session.engine,
        "profile_id": f"browser_{session.engine}",
    }


def stop_session(store: SessionStore, session_id: str, *, task_store: TaskStore | None = None) -> dict[str, Any]:
    record = store.pop(session_id)
    if task_store is not None:
        task_svc.unregister_session_task(task_store, session_id)
    if record.kind == "relay" and record.handle is store.relay:
        store.clear_relay()
    elif record.kind == "terminal":
        record.handle.close()
    elif record.kind == "browser":
        from vdisplay.control.providers.browser_session import default_registry

        default_registry().close(session_id)
        record.handle.close()
    else:
        record.handle.stop()
    return {"ok": True, "session_id": session_id, "stopped": True}


def list_sessions(store: SessionStore) -> dict[str, Any]:
    from vdisplay.control.session import build_catalog_from_agent_store

    catalog = build_catalog_from_agent_store(store)
    return {"ok": True, **catalog.to_dict()}


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
    from vdisplay.control.providers.browser_session import default_registry

    default_registry().close_all()

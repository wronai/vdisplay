"""Agent task lifecycle — persistence, heartbeat, recovery."""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from typing import Any

from vdisplay.control.session import parse_session_kind
from vdisplay.control.session_kind import SessionKind
from vdisplay.exceptions import VDisplayError

from ..session_store import SessionRecord, SessionStore
from ..task_store import TaskStatus, TaskStore, task_to_dict

_LOG = logging.getLogger(__name__)


def _best_effort_task_op(label: str, fn) -> None:
    try:
        fn()
    except Exception as exc:
        _LOG.warning("agent task %s skipped: %s", label, exc)


def recover_on_startup(task_store: TaskStore, broker_id: str) -> dict[str, Any]:
    stale_count = task_store.mark_orphan_running_as_stale(broker_id)
    return {"ok": True, "broker_id": broker_id, "stale_tasks": stale_count}


def list_tasks(
    task_store: TaskStore,
    *,
    status: str | None = None,
    kind: str | None = None,
) -> dict[str, Any]:
    rows = task_store.list_tasks(status=status, kind=kind)
    payloads = [task_to_dict(row) for row in rows]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return {"ok": True, "tasks": payloads, "counts": counts, "total": len(payloads)}


def get_task(task_store: TaskStore, task_id: str) -> dict[str, Any]:
    row = task_store.get_task(task_id)
    if row is None:
        raise VDisplayError(f"unknown task_id: {task_id}")
    return {"ok": True, **task_to_dict(row)}


def heartbeat_task(
    task_store: TaskStore,
    task_id: str,
    *,
    broker_id: str,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = task_store.heartbeat(task_id, broker_id=broker_id, state=state)
    if row is None:
        raise VDisplayError(f"unknown task_id: {task_id}")
    return {"ok": True, **task_to_dict(row)}


def stop_task(task_store: TaskStore, task_id: str, *, broker_id: str) -> dict[str, Any]:
    row = task_store.get_task(task_id)
    if row is None:
        raise VDisplayError(f"unknown task_id: {task_id}")
    if row.broker_id and row.broker_id != broker_id:
        raise VDisplayError(f"task owned by another broker: {row.broker_id}")
    updated = task_store.update_task(task_id, status=TaskStatus.STOPPED, heartbeat=True)
    assert updated is not None
    return {"ok": True, **task_to_dict(updated), "stopped": True}


def register_session_task(
    task_store: TaskStore,
    *,
    broker_id: str,
    record: SessionRecord,
) -> str:
    import os

    kind = parse_session_kind(record.kind).value
    task_id = record.session_id
    config: dict[str, Any] = {"session_kind": str(kind)}
    audit_dir = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
    if audit_dir:
        config["audit_session_dir"] = audit_dir
    audit_id = os.environ.get("VDISPLAY_SESSION_ID", "").strip()
    if audit_id:
        config["audit_session_id"] = audit_id
    existing = task_store.get_task(task_id)
    if existing is not None:
        task_store.update_task(
            task_id,
            status=TaskStatus.RUNNING,
            heartbeat=True,
            config=config,
        )
        return task_id
    task_store.create_task(
        task_id=task_id,
        kind=str(kind),
        broker_id=broker_id,
        status=TaskStatus.RUNNING,
        config=config,
        session_id=record.session_id,
    )
    return task_id


def unregister_session_task(task_store: TaskStore, task_id: str) -> None:
    task_store.update_task(task_id, status=TaskStatus.STOPPED, heartbeat=True)


def begin_sampler_task(
    task_store: TaskStore,
    *,
    broker_id: str,
    config: Any,
    task_id: str | None = None,
) -> str:
    tid = task_id or f"sampler-{uuid.uuid4().hex[:12]}"
    task_store.create_task(
        task_id=tid,
        kind=SessionKind.CAPTURE_SAMPLER.value,
        broker_id=broker_id,
        status=TaskStatus.RUNNING,
        config=asdict(config),
    )
    return tid


def touch_sampler_task(
    task_store: TaskStore,
    task_id: str,
    *,
    broker_id: str,
    state: dict[str, Any],
) -> None:
    task_store.heartbeat(task_id, broker_id=broker_id, state=state)


def end_sampler_task(task_store: TaskStore, task_id: str, *, state: dict[str, Any] | None = None) -> None:
    task_store.update_task(
        task_id,
        status=TaskStatus.STOPPED,
        state=state,
        heartbeat=True,
    )


def begin_screencast_task(
    task_store: TaskStore,
    *,
    broker_id: str,
    config: dict[str, Any],
    task_id: str = "screencast:active",
) -> str:
    existing = task_store.get_task(task_id)
    if existing is not None:
        task_store.update_task(
            task_id,
            status=TaskStatus.RUNNING,
            config=config,
            heartbeat=True,
        )
        return task_id
    task_store.create_task(
        task_id=task_id,
        kind=SessionKind.SCREENCAST.value,
        broker_id=broker_id,
        status=TaskStatus.RUNNING,
        config=config,
    )
    return task_id


def end_screencast_task(task_store: TaskStore, task_id: str = "screencast:active") -> None:
    _best_effort_task_op(
        "end_screencast",
        lambda: task_store.update_task(task_id, status=TaskStatus.STOPPED, heartbeat=True),
    )


def shutdown_tasks(
    task_store: TaskStore,
    store: SessionStore,
    *,
    broker_id: str,
) -> None:
    if store.sampler_task_id:
        state = store.sampler.status() if store.sampler is not None else None
        _best_effort_task_op(
            "end_sampler",
            lambda: end_sampler_task(task_store, store.sampler_task_id, state=state),
        )
        store.sampler_task_id = None
    if store.screencast_task_id:
        end_screencast_task(task_store, store.screencast_task_id)
        store.screencast_task_id = None
    for record in list(store.sessions.values()):
        _best_effort_task_op(
            f"unregister_session:{record.session_id}",
            lambda task_id=record.session_id: unregister_session_task(task_store, task_id),
        )
    _best_effort_task_op(
        "mark_orphan_running_as_stale",
        lambda: task_store.mark_orphan_running_as_stale(broker_id),
    )

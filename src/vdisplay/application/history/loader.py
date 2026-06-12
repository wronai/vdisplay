"""Load and discover history artifacts under ``.vdisplay/**``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import BrokerEvent, HistoryIndex, RunRecord, SessionRef, TaskRecord


def resolve_metadata_root(root: Path | str | None = None) -> Path:
    base = Path(root or ".vdisplay").expanduser()
    if not base.is_absolute():
        base = Path.cwd() / base
    return base


def discover_session_dirs(*, root: Path | None = None) -> list[Path]:
    """Return audit session dirs: flat ``.vdisplay/{ts}__*`` and ``runs/*/session``."""
    base = resolve_metadata_root(root)
    if not base.is_dir():
        return []
    sessions: list[Path] = []
    for path in base.iterdir():
        if path.is_dir() and (path / "session.json").is_file():
            sessions.append(path)
    runs_dir = base / "runs"
    if runs_dir.is_dir():
        for run_dir in runs_dir.iterdir():
            if not run_dir.is_dir():
                continue
            nested = run_dir / "session"
            if nested.is_dir() and (nested / "session.json").is_file():
                sessions.append(nested)
    return sorted(sessions, key=lambda item: item.stat().st_mtime, reverse=True)


def discover_run_dirs(*, root: Path | None = None) -> list[Path]:
    base = resolve_metadata_root(root)
    runs_dir = base / "runs"
    if not runs_dir.is_dir():
        return []
    runs = [path for path in runs_dir.iterdir() if path.is_dir() and (path / "manifest.json").is_file()]
    return sorted(runs, key=lambda item: item.stat().st_mtime, reverse=True)


def read_latest_run_id(root: Path) -> str | None:
    latest = root / "latest-run.txt"
    if not latest.is_file():
        return None
    value = latest.read_text(encoding="utf-8").strip()
    return value or None


def _parse_broker_line(stripped: str) -> BrokerEvent | None:
    """Parse a single broker.jsonl line into a BrokerEvent."""
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return BrokerEvent(
        ts=str(payload.get("ts") or ""),
        action=str(payload.get("action") or ""),
        ok=bool(payload.get("ok")),
        code=str(payload.get("code") or "") or None,
        status=int(payload["status"]) if payload.get("status") is not None else None,
        error=str(payload.get("error") or "") or None,
    )


def load_broker_events(root: Path, *, limit: int | None = None) -> list[BrokerEvent]:
    path = root / "broker.jsonl"
    if not path.is_file():
        return []
    rows: list[BrokerEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        event = _parse_broker_line(stripped)
        if event is not None:
            rows.append(event)
    if limit is not None and limit > 0:
        return rows[-limit:]
    return rows


def _session_summary(session_dir: Path) -> tuple[str, str, str, int, int, int]:
    session_json = session_dir / "session.json"
    if not session_json.is_file():
        return session_dir.name, "unknown", "", 0, 0, 0
    payload = json.loads(session_json.read_text(encoding="utf-8"))
    summary = payload.get("summary") or {}
    total = int(summary.get("total_steps") or len(payload.get("steps") or []))
    ok_steps = int(summary.get("ok_steps") or 0)
    failed = int(summary.get("failed_steps") or max(total - ok_steps, 0))
    return (
        str(payload.get("session_id") or session_dir.name),
        str(payload.get("source") or "cli"),
        str(payload.get("updated_at") or ""),
        total,
        ok_steps,
        failed,
    )


def _session_location(session_dir: Path) -> tuple[str, str | None]:
    if session_dir.name == "session" and session_dir.parent.name != "runs" and session_dir.parent.parent.name == "runs":
        return "run", session_dir.parent.name
    return "flat", None


def load_session_ref(session_dir: Path) -> SessionRef:
    session_id, source, updated_at, total, ok_steps, failed = _session_summary(session_dir)
    location, run_id = _session_location(session_dir)
    return SessionRef(
        path=session_dir,
        session_id=session_id,
        source=source,
        updated_at=updated_at,
        total_steps=total,
        ok_steps=ok_steps,
        failed_steps=failed,
        run_id=run_id,
        location=location,
    )


def _build_task_record(
    payload: dict[str, Any],
    *,
    task_path: Path,
    run_id: str,
) -> TaskRecord:
    """Construct a TaskRecord from the parsed payload dict."""
    inner = payload.get("payload") or {}
    task = inner.get("task") or {}
    feedback = inner.get("feedback") or {}
    decision = feedback.get("decision_data") or {}
    return TaskRecord(
        task_id=str(payload.get("task_id") or task.get("id") or task_path.stem),
        run_id=run_id,
        recorded_at=str(payload.get("recorded_at") or ""),
        ok=bool(inner.get("ok")),
        method=str(inner.get("method") or ""),
        command=str(task.get("command") or ""),
        monitor=str(task.get("monitor") or ""),
        observe_path=feedback.get("observe_path"),
        vql_path=feedback.get("vql_path"),
        vql_targets=len(decision.get("vql_targets") or []),
        session_dir=feedback.get("session_dir"),
        exit_code=inner.get("exit_code"),
        path=task_path,
    )


def load_task_record(task_path: Path, *, run_id: str) -> TaskRecord | None:
    if not task_path.is_file():
        return None
    try:
        payload = json.loads(task_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return _build_task_record(payload, task_path=task_path, run_id=run_id)


def load_run_record(run_dir: Path) -> RunRecord | None:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_id = str(manifest.get("run_id") or run_dir.name)
    tasks_dir = run_dir / "tasks"
    tasks_ok = 0
    tasks_failed = 0
    task_count = 0
    if tasks_dir.is_dir():
        for task_path in tasks_dir.glob("*.json"):
            record = load_task_record(task_path, run_id=run_id)
            if record is None:
                continue
            task_count += 1
            if record.ok:
                tasks_ok += 1
            else:
                tasks_failed += 1
    session_path = run_dir / "session"
    if not (session_path / "session.json").is_file():
        session_path = None
    return RunRecord(
        run_id=run_id,
        path=run_dir,
        started_at=str(manifest.get("started_at") or ""),
        project=str(manifest.get("project") or ""),
        task_count=task_count,
        tasks_ok=tasks_ok,
        tasks_failed=tasks_failed,
        session_path=session_path,
        manifest_path=manifest_path,
    )


def count_observe_pngs(root: Path) -> int:
    observe = root / "observe"
    if not observe.is_dir():
        return 0
    return sum(1 for path in observe.glob("*.png") if path.is_file())


def load_history_index(root: Path | str | None = None, *, broker_limit: int = 200) -> HistoryIndex:
    base = resolve_metadata_root(root)
    runs = [record for path in discover_run_dirs(root=base) if (record := load_run_record(path))]
    sessions = [load_session_ref(path) for path in discover_session_dirs(root=base)]
    tasks: list[TaskRecord] = []
    for run in runs:
        tasks_dir = run.path / "tasks"
        if not tasks_dir.is_dir():
            continue
        for task_path in sorted(tasks_dir.glob("*.json")):
            record = load_task_record(task_path, run_id=run.run_id)
            if record is not None:
                tasks.append(record)
    return HistoryIndex(
        root=base,
        latest_run_id=read_latest_run_id(base),
        runs=runs,
        sessions=sessions,
        tasks=tasks,
        broker_events=load_broker_events(base, limit=broker_limit),
        observe_png_count=count_observe_pngs(base),
    )


def load_run_detail(run_id: str, *, root: Path | str | None = None) -> dict[str, Any] | None:
    base = resolve_metadata_root(root)
    run_dir = base / "runs" / run_id
    record = load_run_record(run_dir)
    if record is None:
        return None
    manifest = json.loads(record.manifest_path.read_text(encoding="utf-8"))
    tasks = [
        item.to_dict()
        for path in sorted((run_dir / "tasks").glob("*.json"))
        if (item := load_task_record(path, run_id=run_id)) is not None
    ]
    session: dict[str, Any] | None = None
    if record.session_path is not None:
        session = load_session_ref(record.session_path).to_dict()
    return {
        "run": record.to_dict(),
        "manifest": manifest,
        "tasks": tasks,
        "session": session,
    }


def iter_session_events(session_dir: Path) -> list[dict[str, Any]]:
    index_path = session_dir / "index.jsonl"
    if not index_path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events

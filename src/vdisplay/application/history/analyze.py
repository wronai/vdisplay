"""Cross-run analysis of ``.vdisplay/**`` event history."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from ..event_store import read_events
from .loader import (
    discover_session_dirs,
    iter_session_events,
    load_history_index,
    resolve_metadata_root,
)
from .models import AnalyzeReport


def _compute_task_stats(tasks: list[Any]) -> dict[str, dict[str, int]]:
    """Aggregate task success/failure counts keyed by task_id."""
    task_by_id: dict[str, dict[str, int]] = {}
    for task in tasks:
        bucket = task_by_id.setdefault(task.task_id, {"runs": 0, "ok": 0, "failed": 0})
        bucket["runs"] += 1
        if task.ok:
            bucket["ok"] += 1
        else:
            bucket["failed"] += 1
    return task_by_id


def _analyze_session(
    session_dir: Path,
    event_histogram: Counter[str],
    backends_used: Counter[str],
) -> dict[str, Any]:
    """Collect session ref, events, and backend usage for a single session."""
    from .loader import load_session_ref

    ref_obj = load_session_ref(session_dir)
    events = list(iter_session_events(session_dir))
    for event in events:
        event_histogram[str(event.get("event_type") or "Unknown")] += 1
        body = event.get("body") or {}
        backend = body.get("backend") or body.get("selected_provider") or body.get("provider")
        if backend:
            backends_used[str(backend)] += 1
    return {
        **ref_obj.to_dict(),
        "event_count": len(events),
        "event_types": dict(Counter(str(e.get("event_type") or "Unknown") for e in events)),
    }


def _collect_domain_backends(session_dir: Path, backends_used: Counter[str]) -> None:
    """Read domain events from a session and tally backend usage."""
    try:
        domain_events = read_events(session_dir)
    except Exception:
        return
    for event in domain_events:
        body = event.body or {}
        provider = body.get("selected_provider") or body.get("provider") or body.get("backend")
        if provider:
            backends_used[str(provider)] += 1


def _collect_projection_backends(session_dir: Path, backends_used: Counter[str]) -> None:
    """Read backend_scores.json projections and tally profile/provider usage."""
    projections = session_dir / "projections" / "backend_scores.json"
    if not projections.is_file():
        return
    import json

    try:
        scores = json.loads(projections.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(scores, dict):
        return
    for profile, providers in scores.items():
        if not isinstance(providers, dict):
            continue
        for provider in providers:
            backends_used[f"{profile}/{provider}"] += 1


def _count_observe_artifacts(base: Path, index: Any) -> dict[str, int]:
    """Count observe directory artifacts."""
    observe_dir = base / "observe"
    if observe_dir.is_dir():
        return {
            "png": index.observe_png_count,
            "context_json": len(list(observe_dir.glob("*.context.json"))),
            "vql_json": len(list(observe_dir.glob("*.vql.json"))),
        }
    return {"png": index.observe_png_count, "context_json": 0, "vql_json": 0}


def _build_summary(
    index: Any,
    *,
    total_events: int,
    broker_errors: list[dict[str, Any]],
    observe_artifacts: dict[str, int],
) -> dict[str, Any]:
    """Build the summary dict for an AnalyzeReport."""
    total_tasks_ok = sum(1 for task in index.tasks if task.ok)
    total_tasks_failed = sum(1 for task in index.tasks if not task.ok)
    return {
        "runs": len(index.runs),
        "sessions": len(index.sessions),
        "tasks": len(index.tasks),
        "tasks_ok": total_tasks_ok,
        "tasks_failed": total_tasks_failed,
        "events": total_events,
        "broker_events": len(index.broker_events),
        "broker_errors": sum(1 for item in index.broker_events if not item.ok),
        "latest_run_id": index.latest_run_id,
        "observe_png": observe_artifacts.get("png", index.observe_png_count),
    }


def analyze_history(
    root: Path | str | None = None,
    *,
    run_limit: int = 50,
    broker_error_limit: int = 20,
) -> AnalyzeReport:
    base = resolve_metadata_root(root)
    index = load_history_index(base)

    runs = index.runs[:run_limit] if run_limit > 0 else index.runs
    run_rows = [run.to_dict() for run in runs]
    task_by_id = _compute_task_stats(index.tasks)

    event_histogram: Counter[str] = Counter()
    backends_used: Counter[str] = Counter()
    session_rows: list[dict[str, Any]] = []

    for session_dir in discover_session_dirs(root=base):
        session_rows.append(_analyze_session(session_dir, event_histogram, backends_used))
        _collect_domain_backends(session_dir, backends_used)
        _collect_projection_backends(session_dir, backends_used)

    broker_errors = [
        item.to_dict()
        for item in index.broker_events
        if not item.ok
    ][-broker_error_limit:]

    observe_artifacts = _count_observe_artifacts(base, index)
    summary = _build_summary(index, total_events=sum(event_histogram.values()), broker_errors=broker_errors, observe_artifacts=observe_artifacts)

    return AnalyzeReport(
        root=base,
        summary=summary,
        runs=run_rows,
        task_stats={"by_task_id": task_by_id},
        event_histogram=dict(sorted(event_histogram.items(), key=lambda item: (-item[1], item[0]))),
        backends_used=dict(sorted(backends_used.items(), key=lambda item: (-item[1], item[0]))),
        broker_errors=broker_errors,
        observe_artifacts=observe_artifacts,
        sessions=session_rows[:run_limit] if run_limit > 0 else session_rows,
    )


def collect_events(
    *,
    root: Path | str | None = None,
    run_id: str | None = None,
    session_dir: Path | str | None = None,
    event_type: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    base = resolve_metadata_root(root)
    session_paths: list[Path] = []

    if session_dir:
        path = Path(session_dir).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        session_paths = [path]
    elif run_id:
        nested = base / "runs" / run_id / "session"
        if nested.is_dir() and (nested / "session.json").is_file():
            session_paths = [nested]
    else:
        session_paths = discover_session_dirs(root=base)

    rows: list[dict[str, Any]] = []
    for path in session_paths:
        location, linked_run = _session_location_for_events(path)
        for event in iter_session_events(path):
            etype = str(event.get("event_type") or "")
            if event_type and etype != event_type:
                continue
            rows.append(
                {
                    **event,
                    "session_path": str(path),
                    "session_location": location,
                    "run_id": linked_run,
                }
            )
    rows.sort(key=lambda item: int(item.get("occurred_at_ms") or 0))
    if limit > 0:
        return rows[-limit:]
    return rows


def _session_location_for_events(session_dir: Path) -> tuple[str, str | None]:
    parts = session_dir.parts
    if "runs" in parts:
        idx = parts.index("runs")
        if idx + 1 < len(parts):
            return "run", parts[idx + 1]
    return "flat", None

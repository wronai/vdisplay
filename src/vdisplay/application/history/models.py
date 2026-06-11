"""Typed views over ``.vdisplay/**`` history artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SessionRef:
    path: Path
    session_id: str
    source: str
    updated_at: str
    total_steps: int
    ok_steps: int
    failed_steps: int
    run_id: str | None = None
    location: str = "flat"  # flat | run

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "session_id": self.session_id,
            "source": self.source,
            "updated_at": self.updated_at,
            "total_steps": self.total_steps,
            "ok_steps": self.ok_steps,
            "failed_steps": self.failed_steps,
            "run_id": self.run_id,
            "location": self.location,
        }


@dataclass
class TaskRecord:
    task_id: str
    run_id: str
    recorded_at: str
    ok: bool
    method: str
    command: str
    monitor: str
    observe_path: str | None
    vql_path: str | None
    vql_targets: int
    session_dir: str | None
    exit_code: int | None
    path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "recorded_at": self.recorded_at,
            "ok": self.ok,
            "method": self.method,
            "command": self.command,
            "monitor": self.monitor,
            "observe_path": self.observe_path,
            "vql_path": self.vql_path,
            "vql_targets": self.vql_targets,
            "session_dir": self.session_dir,
            "exit_code": self.exit_code,
            "path": str(self.path),
        }


@dataclass
class RunRecord:
    run_id: str
    path: Path
    started_at: str
    project: str
    task_count: int
    tasks_ok: int
    tasks_failed: int
    session_path: Path | None
    manifest_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "path": str(self.path),
            "started_at": self.started_at,
            "project": self.project,
            "task_count": self.task_count,
            "tasks_ok": self.tasks_ok,
            "tasks_failed": self.tasks_failed,
            "session_path": str(self.session_path) if self.session_path else None,
            "manifest_path": str(self.manifest_path),
        }


@dataclass
class BrokerEvent:
    ts: str
    action: str
    ok: bool
    code: str | None = None
    status: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "action": self.action,
            "ok": self.ok,
            "code": self.code,
            "status": self.status,
            "error": self.error,
        }


@dataclass
class HistoryIndex:
    root: Path
    latest_run_id: str | None
    runs: list[RunRecord] = field(default_factory=list)
    sessions: list[SessionRef] = field(default_factory=list)
    tasks: list[TaskRecord] = field(default_factory=list)
    broker_events: list[BrokerEvent] = field(default_factory=list)
    observe_png_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "latest_run_id": self.latest_run_id,
            "counts": {
                "runs": len(self.runs),
                "sessions": len(self.sessions),
                "tasks": len(self.tasks),
                "broker_events": len(self.broker_events),
                "observe_png": self.observe_png_count,
            },
            "runs": [item.to_dict() for item in self.runs],
            "sessions": [item.to_dict() for item in self.sessions],
            "tasks": [item.to_dict() for item in self.tasks],
            "broker_events": [item.to_dict() for item in self.broker_events[-50:]],
        }


@dataclass
class AnalyzeReport:
    root: Path
    summary: dict[str, Any]
    runs: list[dict[str, Any]] = field(default_factory=list)
    task_stats: dict[str, Any] = field(default_factory=dict)
    event_histogram: dict[str, int] = field(default_factory=dict)
    backends_used: dict[str, int] = field(default_factory=dict)
    broker_errors: list[dict[str, Any]] = field(default_factory=list)
    observe_artifacts: dict[str, int] = field(default_factory=dict)
    sessions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "summary": self.summary,
            "runs": self.runs,
            "task_stats": self.task_stats,
            "event_histogram": self.event_histogram,
            "backends_used": self.backends_used,
            "broker_errors": self.broker_errors,
            "observe_artifacts": self.observe_artifacts,
            "sessions": self.sessions,
        }

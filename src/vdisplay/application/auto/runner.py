"""Run planfile automation tasks sequentially."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ...exceptions import VDisplayError
from .executor import ExecuteResult, execute_task_command
from .feedback import finalize_result_ok, preflight_observe, prepare_command, task_execution_env
from .tasks import AutoSource, AutoTask, load_auto_tasks, next_auto_task, resolve_planfile_path, write_yaml_task_status

AutoAction = Literal["run", "once", "list", "next"]


@dataclass
class AutoRunResult:
    ok: bool
    action: str
    executed: list[dict[str, Any]] = field(default_factory=list)
    pending: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "action": self.action,
            "executed": self.executed,
            "pending": self.pending,
            "error": self.error,
        }


def run_auto_once(
    *,
    project: str | Path = ".",
    planfile: str | Path | None = None,
    source: AutoSource = "auto",
    dry_run: bool = False,
    assigned_to: str = "vdisplay-auto",
) -> AutoRunResult:
    root = Path(project).expanduser().resolve()
    tasks = load_auto_tasks(project=root, planfile=planfile, source=source)
    task = next_auto_task(tasks)
    if task is None:
        return AutoRunResult(ok=True, action="once", pending=[])

    executed = [_execute_one(task, project=root, planfile=planfile, dry_run=dry_run, assigned_to=assigned_to)]
    return AutoRunResult(
        ok=bool(executed[0]["ok"]),
        action="once",
        executed=executed,
        pending=[item.to_dict() for item in tasks if item.id != task.id],
        error="" if executed[0]["ok"] else str(executed[0].get("error") or ""),
    )


def run_auto_loop(
    *,
    project: str | Path = ".",
    planfile: str | Path | None = None,
    source: AutoSource = "auto",
    max_tasks: int = 0,
    dry_run: bool = False,
    assigned_to: str = "vdisplay-auto",
) -> AutoRunResult:
    root = Path(project).expanduser().resolve()
    executed: list[dict[str, Any]] = []
    limit = max(0, int(max_tasks))
    last_completed_id: str | None = None

    while True:
        tasks = load_auto_tasks(project=root, planfile=planfile, source=source)
        task = next_auto_task(tasks)
        if task is None:
            break
        if limit and len(executed) >= limit:
            break
        if task.id == last_completed_id:
            pending = [item.to_dict() for item in tasks]
            return AutoRunResult(
                ok=False,
                action="run",
                executed=executed,
                pending=pending,
                error=(
                    f"task {task.id!r} did not advance after success "
                    "(planfile status not updated — check write_yaml_task_status)"
                ),
            )
        result = _execute_one(task, project=root, planfile=planfile, dry_run=dry_run, assigned_to=assigned_to)
        executed.append(result)
        if not result["ok"]:
            pending = [item.to_dict() for item in load_auto_tasks(project=root, planfile=planfile, source=source)]
            return AutoRunResult(
                ok=False,
                action="run",
                executed=executed,
                pending=pending,
                error=str(result.get("error") or "task failed"),
            )
        last_completed_id = task.id

    pending = [item.to_dict() for item in load_auto_tasks(project=root, planfile=planfile, source=source)]
    return AutoRunResult(ok=True, action="run", executed=executed, pending=pending)


def list_auto_tasks(
    *,
    project: str | Path = ".",
    planfile: str | Path | None = None,
    source: AutoSource = "auto",
) -> dict[str, Any]:
    tasks = load_auto_tasks(project=project, planfile=planfile, source=source)
    return {
        "ok": True,
        "count": len(tasks),
        "tasks": [task.to_dict() for task in tasks],
        "next": next_auto_task(tasks).to_dict() if next_auto_task(tasks) else None,
    }


def _update_task_status(
    task: AutoTask,
    result: ExecuteResult,
    pf: Any | None,
    project: Path,
    planfile: str | Path | None,
) -> None:
    if pf is not None and task.ticket_id:
        note = result.output or result.error or result.method
        if result.ok:
            pf.complete_ticket(task.ticket_id, note=note[:4000])
        else:
            pf.fail_ticket(task.ticket_id, error=note[:4000])
    elif task.source.startswith("planfile.yaml"):
        yaml_path = resolve_planfile_path(project, planfile)
        if yaml_path.is_file():
            write_yaml_task_status(
                yaml_path,
                task.id,
                status="done" if result.ok else "failed",
                note=result.output or result.error,
            )


def _planfile_for_task(task: AutoTask, project: Path, dry_run: bool) -> Any:
    if task.source == ".planfile" and task.ticket_id and not dry_run:
        return _planfile_client(project)
    return None


def _build_execute_payload(result: ExecuteResult, task: AutoTask, feedback: Any | None = None) -> dict[str, Any]:
    payload = {
        "ok": result.ok,
        "task": task.to_dict(),
        "method": result.method,
        "output": result.output,
        "error": result.error,
        "exit_code": result.exit_code,
    }
    if feedback is not None:
        payload["feedback"] = feedback.to_dict()
    return payload


def _handle_execute_exception(
    task: AutoTask,
    pf: Any,
    exc: Exception,
) -> dict[str, Any]:
    if pf is not None and task.ticket_id:
        try:
            pf.fail_ticket(task.ticket_id, error=str(exc))
        except Exception:
            pass
    return {
        "ok": False,
        "task": task.to_dict(),
        "method": "error",
        "error": str(exc),
    }


def _execute_one(
    task: AutoTask,
    *,
    project: Path,
    planfile: str | Path | None,
    dry_run: bool,
    assigned_to: str,
) -> dict[str, Any]:
    pf = _planfile_for_task(task, project, dry_run)

    try:
        if pf is not None:
            pf.claim_ticket(task.ticket_id, assigned_to=assigned_to)
            pf.start_ticket(task.ticket_id)

        observe_feedback = preflight_observe(
            task,
            project=str(project),
            execute_fn=lambda cmd, **kwargs: execute_task_command(cmd, project=str(project), **kwargs),
        )
        prepared, prep_feedback = prepare_command(task.command, task)
        observe_feedback.prepared_command = prepared
        observe_feedback.verify_requested = prep_feedback.verify_requested or observe_feedback.verify_requested

        if dry_run:
            return _build_execute_payload(
                ExecuteResult(ok=True, method="dry-run", output=prepared),
                task,
                observe_feedback,
            )

        with task_execution_env(task, observe_feedback):
            result = execute_task_command(prepared, project=str(project), task=task)
        result.ok = finalize_result_ok(result, observe_feedback)
        if not result.ok and observe_feedback.verify_passed is False:
            result.error = (result.error or "verify failed").strip()

        payload = _build_execute_payload(result, task, observe_feedback)

        _update_task_status(task, result, pf, project, planfile)
        return payload
    except Exception as exc:
        return _handle_execute_exception(task, pf, exc)


def _planfile_client(project: Path) -> Any:
    try:
        from planfile import Planfile
    except ImportError as exc:
        raise VDisplayError(
            "planfile package required — install: pip install -e /path/to/semcod/planfile"
        ) from exc
    return Planfile(str(project))

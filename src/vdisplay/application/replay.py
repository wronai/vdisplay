"""Replay recorded `.vdisplay` audit sessions (CONTROL_* steps)."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .commands import CommandRequest, CommandResult, CommandVerb
from .executor import execute
from .commands.verbs import COMMAND_VERBS

REPLAYABLE_VERBS = frozenset(
    {
        CommandVerb.CONTROL_CLICK,
        CommandVerb.CONTROL_FOCUS,
        CommandVerb.CONTROL_SET_VALUE,
    }
)

_JOB_LOCK = threading.Lock()
_REPLAY_JOBS: dict[str, dict[str, Any]] = {}


@dataclass
class ReplayStepPlan:
    step_id: str
    verb: str
    action: str
    request_path: str


@dataclass
class ReplayStepResult:
    step_id: str
    verb: str
    ok: bool
    action: str
    error: str | None = None
    skipped: bool = False


@dataclass
class ReplayReport:
    session_id: str
    session_path: str
    dry_run: bool
    steps_total: int
    steps_replayable: int
    steps_executed: int
    steps_ok: int
    steps_failed: int
    steps_skipped: int
    results: list[ReplayStepResult] = field(default_factory=list)
    plan: list[ReplayStepPlan] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_path": self.session_path,
            "dry_run": self.dry_run,
            "steps_total": self.steps_total,
            "steps_replayable": self.steps_replayable,
            "steps_executed": self.steps_executed,
            "steps_ok": self.steps_ok,
            "steps_failed": self.steps_failed,
            "steps_skipped": self.steps_skipped,
            "results": [
                {
                    "step_id": item.step_id,
                    "verb": item.verb,
                    "ok": item.ok,
                    "action": item.action,
                    "error": item.error,
                    "skipped": item.skipped,
                }
                for item in self.results
            ],
            "plan": [
                {
                    "step_id": item.step_id,
                    "verb": item.verb,
                    "action": item.action,
                    "request_path": item.request_path,
                }
                for item in self.plan
            ],
        }


def command_request_from_audit(payload: dict[str, Any]) -> CommandRequest:
    """Rebuild ``CommandRequest`` from ``steps/*/request.json`` audit payload."""
    raw = dict(payload)
    verb_raw = str(raw.pop("verb") or "").strip()
    if not verb_raw:
        raise ValueError("missing verb in audit request")
    request_id = raw.pop("request_id", None)
    cmd = CommandRequest(verb=CommandVerb(verb_raw), **raw)
    if request_id:
        cmd.request_id = str(request_id)
    return cmd


def iter_replay_step_dirs(session_dir: Path) -> list[Path]:
    steps_root = session_dir / "steps"
    if not steps_root.is_dir():
        return []
    return sorted(
        (path for path in steps_root.iterdir() if path.is_dir() and (path / "request.json").is_file()),
        key=lambda item: item.name,
    )


def load_step_request(step_dir: Path) -> dict[str, Any]:
    payload = json.loads((step_dir / "request.json").read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid request.json in {step_dir}")
    return payload


def _load_session_metadata(root: Path) -> str:
    session_id = root.name
    session_json = root / "session.json"
    if session_json.is_file():
        try:
            meta = json.loads(session_json.read_text(encoding="utf-8"))
            session_id = str(meta.get("session_id") or session_id)
        except json.JSONDecodeError:
            pass
    return session_id


def _classify_step(payload: dict[str, Any]) -> tuple[CommandVerb | None, str, bool]:
    verb_raw = str(payload.get("verb") or "")
    try:
        verb = CommandVerb(verb_raw)
    except ValueError:
        return None, verb_raw, True  # unknown -> skip
    if verb not in REPLAYABLE_VERBS:
        return verb, verb.value, True
    return verb, verb.value, False


def _process_unknown_verb(
    step_id: str, verb_str: str, results: list[ReplayStepResult], skipped: list[int]
) -> None:
    skipped[0] += 1
    results.append(
        ReplayStepResult(step_id=step_id, verb=verb_str, ok=False, action="", error="unknown verb", skipped=True)
    )


def _process_skipped_step(
    step_id: str, verb_str: str, action: str, results: list[ReplayStepResult], skipped: list[int]
) -> None:
    skipped[0] += 1
    results.append(
        ReplayStepResult(step_id=step_id, verb=verb_str, ok=True, action=action, skipped=True)
    )


def _execute_replay_step(
    step_id: str,
    verb: CommandVerb,
    cmd: CommandRequest,
    *,
    run: Callable[[CommandRequest], CommandResult],
    stop_on_error: bool,
    delay: float,
    results: list[ReplayStepResult],
    counters: dict[str, int],
) -> bool:
    counters["executed"] += 1
    replay_cmd = _fresh_replay_request(cmd)
    result = run(replay_cmd)
    if result.ok:
        counters["ok_count"] += 1
        results.append(
            ReplayStepResult(step_id=step_id, verb=verb.value, ok=True, action=result.action)
        )
    else:
        counters["failed"] += 1
        message = result.error.message if result.error else "replay step failed"
        results.append(
            ReplayStepResult(
                step_id=step_id,
                verb=verb.value,
                ok=False,
                action=result.action,
                error=message,
            )
        )
        if stop_on_error:
            return False
    if delay > 0:
        time.sleep(delay)
    return True


def replay_session(
    session_dir: Path | str,
    *,
    dry_run: bool = False,
    stop_on_error: bool = True,
    step_delay_s: float | None = None,
    executor: Callable[[CommandRequest], CommandResult] | None = None,
) -> ReplayReport:
    """Replay CONTROL_* steps from a recorded session directory."""
    root = Path(session_dir).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"session directory not found: {root}")

    session_id = _load_session_metadata(root)
    delay = _step_delay(step_delay_s)
    run = executor or execute
    step_dirs = iter_replay_step_dirs(root)
    plan: list[ReplayStepPlan] = []
    results: list[ReplayStepResult] = []
    counters: dict[str, int] = {"executed": 0, "ok_count": 0, "failed": 0, "skipped": 0}

    for step_dir in step_dirs:
        step_id = step_dir.name
        payload = load_step_request(step_dir)
        verb, verb_str, is_skip = _classify_step(payload)

        if verb is None:
            _process_unknown_verb(step_id, verb_str, results, [counters["skipped"]])
            continue

        cmd = command_request_from_audit(payload)
        plan.append(
            ReplayStepPlan(
                step_id=step_id,
                verb=verb_str,
                action=cmd.action,
                request_path=str(step_dir / "request.json"),
            )
        )

        if is_skip:
            _process_skipped_step(step_id, verb_str, cmd.action, results, [counters["skipped"]])
            continue

        if dry_run:
            continue

        should_continue = _execute_replay_step(
            step_id, verb, cmd, run=run, stop_on_error=stop_on_error, delay=delay,
            results=results, counters=counters,
        )
        if not should_continue:
            break

    replayable = sum(1 for item in plan if item.verb in {verb.value for verb in REPLAYABLE_VERBS})
    return ReplayReport(
        session_id=session_id,
        session_path=str(root),
        dry_run=dry_run,
        steps_total=len(step_dirs),
        steps_replayable=replayable,
        steps_executed=counters["executed"],
        steps_ok=counters["ok_count"],
        steps_failed=counters["failed"],
        steps_skipped=counters["skipped"],
        results=results,
        plan=plan,
    )


def _run_background_replay(
    job_id: str,
    root: Path,
    *,
    stop_on_error: bool,
    step_delay_s: float | None,
    executor: Callable[[CommandRequest], CommandResult] | None,
) -> None:
    with _JOB_LOCK:
        _REPLAY_JOBS[job_id]["status"] = "running"
    try:
        report = replay_session(
            root,
            dry_run=False,
            stop_on_error=stop_on_error,
            step_delay_s=step_delay_s,
            executor=executor,
        )
        payload = report.to_dict()
        payload["ok"] = report.steps_failed == 0
        with _JOB_LOCK:
            _REPLAY_JOBS[job_id].update({"status": "completed", "report": payload})
    except Exception as exc:
        with _JOB_LOCK:
            _REPLAY_JOBS[job_id].update({"status": "failed", "error": str(exc)})


def queue_session_replay(
    session_dir: Path | str,
    *,
    stop_on_error: bool = True,
    step_delay_s: float | None = None,
    executor: Callable[[CommandRequest], CommandResult] | None = None,
) -> dict[str, Any]:
    """Start background replay; returns job metadata immediately."""
    root = Path(session_dir).expanduser().resolve()
    preview = replay_session(root, dry_run=True)
    job_id = uuid.uuid4().hex[:12]

    with _JOB_LOCK:
        _REPLAY_JOBS[job_id] = {
            "job_id": job_id,
            "session_id": preview.session_id,
            "session_path": str(root),
            "status": "queued",
            "queued_at": time.time(),
        }

    threading.Thread(
        target=_run_background_replay,
        args=(job_id, root),
        kwargs={"stop_on_error": stop_on_error, "step_delay_s": step_delay_s, "executor": executor},
        daemon=True,
        name=f"vdisplay-replay-{job_id}",
    ).start()
    return {
        "ok": True,
        "queued": True,
        "job_id": job_id,
        "session_id": preview.session_id,
        "session_path": str(root),
        "steps": preview.steps_total,
        "steps_replayable": preview.steps_replayable,
        "plan": [item.__dict__ for item in preview.plan if item.verb in {v.value for v in REPLAYABLE_VERBS}],
        "message": "Replay started in background.",
    }


def replay_job_status(job_id: str) -> dict[str, Any] | None:
    with _JOB_LOCK:
        job = _REPLAY_JOBS.get(job_id)
        return dict(job) if job else None


def _fresh_replay_request(cmd: CommandRequest) -> CommandRequest:
    """Clone audit request with a new request id (avoid duplicate-id confusion)."""
    payload = json.loads(json.dumps(_request_payload(cmd)))
    payload["request_id"] = uuid.uuid4().hex
    payload["request_source"] = "replay"
    return command_request_from_audit(payload)


def _request_payload(cmd: CommandRequest) -> dict[str, Any]:
    from dataclasses import asdict

    payload = asdict(cmd)
    payload["verb"] = cmd.verb.value
    return payload


def _step_delay(step_delay_s: float | None) -> float:
    if step_delay_s is not None:
        return max(0.0, float(step_delay_s))
    raw = os.environ.get("VDISPLAY_REPLAY_DELAY_S", "0.25").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.25

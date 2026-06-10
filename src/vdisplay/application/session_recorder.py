"""Session recorder — audit trail from application.executor (CLI/DSL/REST/MCP)."""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import time
import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .commands import ArtifactRef, CommandRequest, CommandResult, CommandVerb

_current_recorder: ContextVar[SessionRecorder | None] = ContextVar("vdisplay_session_recorder", default=None)

_SECRET_ENV_RE = re.compile(r"(token|secret|password|api[_-]?key)", re.I)
_ARTIFACT_PATH_KEYS = (
    "path",
    "preview_path",
    "output",
    "json",
    "md",
    "svg",
    "before",
    "after",
    "diff",
)


def session_recording_enabled() -> bool:
    if os.environ.get("VDISPLAY_SESSION_DIR", "").strip():
        return True
    return os.environ.get("VDISPLAY_SESSION", "").strip().lower() in {"1", "true", "yes"}


def _redact_env(env: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in env.items():
        if not key.startswith("VDISPLAY") and key not in {"DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE"}:
            continue
        if _SECRET_ENV_RE.search(key):
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted


def _collect_env_snapshot() -> dict[str, str]:
    keys = (
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XDG_SESSION_TYPE",
        "VDISPLAY_AGENT_URL",
        "VDISPLAY_SESSION",
        "VDISPLAY_SESSION_DIR",
        "VDISPLAY_SESSION_ID",
        "YDOTOOL_SOCKET",
    )
    return _redact_env({key: os.environ[key] for key in keys if os.environ.get(key)})


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return slug[:64] or "session"


def _default_session_name(*, source: str, route: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    slug = os.environ.get("VDISPLAY_SESSION_ID", "").strip()
    if slug:
        return f"{ts}__{_slugify(slug)}"
    return f"{ts}__{route}__{source}"


@dataclass
class StepRecord:
    index: int
    step_id: str
    request_id: str
    timestamp: str
    duration_ms: int
    source: str
    route: str
    verb: str
    action: str
    command_line: str
    ok: bool
    request_path: str
    result_path: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionDocument:
    version: int = 1
    session_id: str = ""
    started_at: str = ""
    updated_at: str = ""
    source: str = "cli"
    route_default: str = "local"
    host: str = ""
    cwd: str = ""
    pid: int = 0
    env: dict[str, str] = field(default_factory=dict)
    steps: list[StepRecord] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["steps"] = [asdict(step) for step in self.steps]
        return payload


class SessionRecorder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "steps").mkdir(exist_ok=True)
        self._step_index = 0
        self._document = self._load_or_create_document()

    @property
    def session_dir(self) -> Path:
        return self.root

    def _load_or_create_document(self) -> SessionDocument:
        session_json = self.root / "session.json"
        if session_json.is_file():
            payload = json.loads(session_json.read_text(encoding="utf-8"))
            steps = [StepRecord(**item) for item in payload.get("steps", [])]
            doc = SessionDocument(
                version=int(payload.get("version", 1)),
                session_id=str(payload.get("session_id") or self.root.name),
                started_at=str(payload.get("started_at") or ""),
                updated_at=str(payload.get("updated_at") or ""),
                source=str(payload.get("source") or "cli"),
                route_default=str(payload.get("route_default") or "local"),
                host=str(payload.get("host") or ""),
                cwd=str(payload.get("cwd") or ""),
                pid=int(payload.get("pid") or 0),
                env=dict(payload.get("env") or {}),
                steps=steps,
                summary=dict(payload.get("summary") or {}),
            )
            self._step_index = len(steps)
            return doc

        now = _utc_now()
        doc = SessionDocument(
            session_id=self.root.name,
            started_at=now,
            updated_at=now,
            host=socket.gethostname(),
            cwd=str(Path.cwd()),
            pid=os.getpid(),
            env=_collect_env_snapshot(),
        )
        (self.root / "env.json").write_text(json.dumps(doc.env, indent=2), encoding="utf-8")
        return doc

    def record(
        self,
        cmd: CommandRequest,
        result: CommandResult,
        *,
        route: str,
        duration_ms: int,
    ) -> StepRecord:
        self._step_index += 1
        step_id = f"{self._step_index:04d}"
        step_dir = self.root / "steps" / step_id
        step_dir.mkdir(parents=True, exist_ok=True)

        request_id = cmd.request_id or str(uuid.uuid4())
        request_payload = request_to_dict(cmd, request_id=request_id)
        result_payload = result_to_dict(result, request_id=request_id)

        (step_dir / "request.json").write_text(
            json.dumps(request_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (step_dir / "result.json").write_text(
            json.dumps(result_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if cmd.line:
            (step_dir / "command.dsl.txt").write_text(cmd.line.strip() + "\n", encoding="utf-8")

        artifacts = collect_artifacts(result)
        copied: list[dict[str, Any]] = []
        for artifact in artifacts:
            copied_path = copy_artifact(step_dir, artifact)
            if copied_path is not None:
                copied.append({**artifact.to_dict(), "session_path": copied_path})

        diagnostics = extract_diagnostics(result)
        step = StepRecord(
            index=self._step_index,
            step_id=step_id,
            request_id=request_id,
            timestamp=_utc_now(),
            duration_ms=duration_ms,
            source=cmd.request_source,
            route=route,
            verb=str(cmd.verb.value),
            action=result.action,
            command_line=cmd.line,
            ok=result.ok,
            request_path=f"steps/{step_id}/request.json",
            result_path=f"steps/{step_id}/result.json",
            artifacts=copied,
            diagnostics=diagnostics,
        )
        self._document.source = cmd.request_source
        self._document.route_default = route
        self._document.steps.append(step)
        self._document.updated_at = step.timestamp
        self._document.summary = _build_summary(self._document.steps)
        self.flush()
        return step

    def flush(self) -> None:
        (self.root / "session.json").write_text(
            json.dumps(self._document.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (self.root / "README.md").write_text(render_readme(self._document), encoding="utf-8")


def resolve_session_root(cmd: CommandRequest) -> Path | None:
    if not session_recording_enabled():
        return None
    explicit = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path
    current = _current_recorder.get()
    if current is not None:
        return current.session_dir
    name = cmd.session_id or _default_session_name(source=cmd.request_source, route="local")
    return Path.cwd() / ".vdisplay" / name


def get_session_recorder(cmd: CommandRequest) -> SessionRecorder | None:
    root = resolve_session_root(cmd)
    if root is None:
        return None
    current = _current_recorder.get()
    if current is not None and current.session_dir == root:
        return current
    recorder = SessionRecorder(root)
    _current_recorder.set(recorder)
    return recorder


def record_execution(
    cmd: CommandRequest,
    result: CommandResult,
    *,
    route: str,
    duration_ms: int,
) -> Path | None:
    recorder = get_session_recorder(cmd)
    if recorder is None:
        return None
    if cmd.session_id and not os.environ.get("VDISPLAY_SESSION_DIR"):
        recorder._document.session_id = cmd.session_id
    step = recorder.record(cmd, result, route=route, duration_ms=duration_ms)
    result.session_id = recorder._document.session_id
    result.request_id = step.request_id
    if result.meta is not None:
        result.meta["session_dir"] = str(recorder.session_dir)
        result.meta["session_step"] = step.step_id
    return recorder.session_dir


def request_to_dict(cmd: CommandRequest, *, request_id: str) -> dict[str, Any]:
    payload = asdict(cmd)
    payload["verb"] = str(cmd.verb.value)
    payload["request_id"] = request_id
    return payload


def result_to_dict(result: CommandResult, *, request_id: str) -> dict[str, Any]:
    payload = result.to_dict()
    payload["request_id"] = request_id
    payload["artifacts"] = [artifact.to_dict() for artifact in result.artifacts]
    payload["diagnostics"] = dict(result.diagnostics)
    return payload


def collect_artifacts(result: CommandResult) -> list[ArtifactRef]:
    seen: set[str] = set()
    artifacts: list[ArtifactRef] = []
    for item in result.artifacts:
        if item.path and item.path not in seen:
            seen.add(item.path)
            artifacts.append(item)
    for item in _artifacts_from_data(result.data):
        if item.path not in seen:
            seen.add(item.path)
            artifacts.append(item)
    return artifacts


def _artifacts_from_data(data: dict[str, Any]) -> list[ArtifactRef]:
    found: list[ArtifactRef] = []

    def add(kind: str, path: str | None, *, label: str | None = None) -> None:
        if not path or not isinstance(path, str):
            return
        candidate = Path(path)
        if not candidate.is_file():
            return
        found.append(ArtifactRef(kind=kind, path=str(candidate), label=label))

    _collect_top_level_artifacts(data, add)
    _collect_block_artifacts(data, add)
    _collect_routing_artifacts(data, add)
    return found


def _collect_top_level_artifacts(
    data: dict[str, Any],
    add: Callable[..., None],
) -> None:
    for key in ("path", "preview_path", "output"):
        add("screenshot" if key == "path" else key.removesuffix("_path"), data.get(key), label=key)

    preview = data.get("preview")
    if isinstance(preview, dict):
        add("preview", preview.get("preview_path"), label="preview")

    artifacts_block = data.get("artifacts")
    if isinstance(artifacts_block, dict):
        for kind, path in artifacts_block.items():
            add(str(kind), path if isinstance(path, str) else None, label=str(kind))


def _collect_block_artifacts(
    data: dict[str, Any],
    add: Callable[..., None],
) -> None:
    for block_key, kind in (
        ("screenshot_diff", "diff"),
        ("verification", "verify"),
    ):
        block = data.get(block_key)
        if not isinstance(block, dict):
            continue
        capture = block.get("capture") or {}
        if isinstance(capture, dict):
            add(kind, capture.get("path"), label=block_key)
        for side in ("before", "after"):
            side_capture = block.get(side)
            if isinstance(side_capture, dict):
                add(side, side_capture.get("path"), label=side)


def _collect_routing_artifacts(
    data: dict[str, Any],
    add: Callable[..., None],
) -> None:
    routing = data.get("routing")
    if isinstance(routing, dict):
        for key in _ARTIFACT_PATH_KEYS:
            add("json", routing.get(key), label=f"routing.{key}")


def copy_artifact(step_dir: Path, artifact: ArtifactRef) -> str | None:
    src = Path(artifact.path)
    if not src.is_file():
        return None
    suffix = src.suffix or ".bin"
    dest_name = artifact.kind
    if artifact.label and artifact.label not in dest_name:
        dest_name = f"{artifact.kind}-{artifact.label}"
    dest_name = _slugify(dest_name.replace("/", "-")) + suffix
    dest = step_dir / dest_name
    if dest.exists():
        return dest.relative_to(step_dir.parent.parent).as_posix()
    shutil.copy2(src, dest)
    return dest.relative_to(step_dir.parent.parent).as_posix()


def extract_diagnostics(result: CommandResult) -> dict[str, Any]:
    if result.diagnostics:
        return dict(result.diagnostics)
    data = result.data
    diagnostics: dict[str, Any] = {}
    routing = data.get("routing")
    if isinstance(routing, dict):
        diagnostics["routing"] = {
            "selected_provider": routing.get("selected_provider"),
            "verify_mode": routing.get("verify_mode"),
            "why_selected": routing.get("why_selected"),
        }
    for key in ("verified", "verify_mode", "verify_confidence", "verify_reasons", "method", "reason"):
        if key in data:
            diagnostics.setdefault("verify", {})[key] = data[key]
    return diagnostics


def _build_summary(steps: list[StepRecord]) -> dict[str, Any]:
    ok_steps = sum(1 for step in steps if step.ok)
    failed = len(steps) - ok_steps
    backends: set[str] = set()
    for step in steps:
        provider = (step.diagnostics.get("routing") or {}).get("selected_provider")
        if provider:
            backends.add(str(provider))
    return {
        "total_steps": len(steps),
        "ok_steps": ok_steps,
        "failed_steps": failed,
        "backends_used": sorted(backends),
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def render_readme(doc: SessionDocument) -> str:
    lines = [
        f"# vdisplay session {doc.session_id}",
        "",
        "## Session metadata",
        "",
        "| Key | Value |",
        "|-----|-------|",
        f"| Session ID | `{doc.session_id}` |",
        f"| Started | `{doc.started_at}` |",
        f"| Updated | `{doc.updated_at}` |",
        f"| Source | `{doc.source}` |",
        f"| Route | `{doc.route_default}` |",
        f"| Host | `{doc.host}` |",
        f"| Steps | {doc.summary.get('total_steps', 0)} ({doc.summary.get('ok_steps', 0)} ok, {doc.summary.get('failed_steps', 0)} failed) |",
        "",
        "## Steps",
        "",
    ]
    for step in doc.steps:
        title = step.verb.replace("_", " ")
        lines.append(f"- [Step {step.step_id} — {title}](#step-{step.step_id}--{title.lower().replace(' ', '-')})")
    lines.append("")

    for step in doc.steps:
        title = step.verb.replace("_", " ")
        anchor = title.lower().replace(" ", "-")
        lines.extend(
            [
                f"## Step {step.step_id} — {title}",
                "",
                f"- **Time:** `{step.timestamp}` ({step.duration_ms} ms)",
                f"- **Source:** `{step.source}` · **Route:** `{step.route}`",
                f"- **Action:** `{step.action}` · **Result:** `{'ok' if step.ok else 'fail'}`",
            ]
        )
        if step.command_line:
            lines.append(f"- **Command:** `{step.command_line}`")
        routing = step.diagnostics.get("routing") or {}
        if routing.get("selected_provider"):
            lines.append(f"- **Backend:** `{routing.get('selected_provider')}`")
        if routing.get("why_selected"):
            lines.append(f"- **Routing:** {'; '.join(str(x) for x in routing.get('why_selected', [])[:3])}")
        verify = step.diagnostics.get("verify") or {}
        if verify:
            lines.append(
                f"- **Verify:** mode `{verify.get('verify_mode', '-')}` · "
                f"verified `{verify.get('verified', '-')}`"
            )
        lines.extend(
            [
                "- **Files:**",
                f"  - [{step.request_path}]({step.request_path})",
                f"  - [{step.result_path}]({step.result_path})",
            ]
        )
        for artifact in step.artifacts:
            rel = artifact.get("session_path")
            if rel:
                kind = artifact.get("kind", "artifact")
                lines.append(f"  - [{kind}]({rel})")
        lines.append("")

    return "\n".join(lines)

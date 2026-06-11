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
from .session_recorder_diagnostics import extract_diagnostics
from .session_recorder_readme import render_readme

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
    maps: list[dict[str, Any]] = field(default_factory=list)

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
                maps=list(payload.get("maps") or []),
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
        else:
            dsl_text = command_request_to_dsl_text(cmd)
            if dsl_text:
                (step_dir / "command.dsl.txt").write_text(dsl_text.strip() + "\n", encoding="utf-8")

        artifacts = collect_artifacts(result)
        copied: list[dict[str, Any]] = []
        for artifact in artifacts:
            copied_path = copy_artifact(step_dir, artifact)
            if copied_path is not None:
                copied.append({**artifact.to_dict(), "session_path": copied_path})

        diagnostics = extract_diagnostics(result)
        (step_dir / "diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        map_entries = archive_map_artifacts(self.root, cmd, result, diagnostics)
        for entry in map_entries:
            copied.append(entry)
            session_path = entry.get("session_path")
            if not session_path:
                continue
            if not any(item.get("session_path") == session_path for item in self._document.maps):
                self._document.maps.append(
                    {
                        "kind": entry.get("kind"),
                        "session_path": session_path,
                        "source": entry.get("source"),
                    }
                )
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
        self._emit_step_events(step, cmd, result, diagnostics)
        return step

    def _emit_step_events(
        self,
        step: StepRecord,
        cmd: CommandRequest,
        result: CommandResult,
        diagnostics: dict[str, Any],
    ) -> None:
        from .event_store import append_events, event_store_enabled
        from .events import control_events_from_diagnostics, map_events_from_diagnostics, session_started, step_recorded

        if not event_store_enabled():
            return

        events = []
        if step.index == 1:
            events.append(
                session_started(
                    session_id=self._document.session_id,
                    source=cmd.request_source,
                    route=step.route,
                    env=dict(self._document.env),
                )
            )
        events.append(
            step_recorded(
                session_id=self._document.session_id,
                request_id=step.request_id,
                step_id=step.step_id,
                route=step.route,
                verb=step.verb,
                ok=step.ok,
                duration_ms=step.duration_ms,
                request_path=step.request_path,
                result_path=step.result_path,
                diagnostics=diagnostics,
            )
        )
        events.extend(
            control_events_from_diagnostics(
                session_id=self._document.session_id,
                request_id=step.request_id,
                verb=step.verb,
                diagnostics=diagnostics,
                ok=step.ok,
            )
        )
        events.extend(
            map_events_from_diagnostics(
                session_id=self._document.session_id,
                request_id=step.request_id,
                diagnostics=diagnostics,
            )
        )
        append_events(self.root, events)

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


def command_request_to_dsl_text(cmd: CommandRequest) -> str | None:
    try:
        from dsl2vdisplay.grammar import to_text
    except ImportError:
        return None
    payload = request_to_dict(cmd, request_id=cmd.request_id or "")
    payload.pop("request_id", None)
    text = to_text(payload).strip()
    return text or None


def resolve_map_path(
    cmd: CommandRequest,
    result: CommandResult,
    diagnostics: dict[str, Any],
) -> Path | None:
    control = diagnostics.get("control") or {}
    map_block = control.get("map") if isinstance(control.get("map"), dict) else {}
    candidates = (
        result.data.get("map_path"),
        map_block.get("path"),
        (cmd.extra or {}).get("map_path"),
    )
    for raw in candidates:
        if not raw:
            continue
        path = Path(str(raw)).expanduser()
        if path.is_file():
            return path
    return None


def archive_map_artifacts(
    session_root: Path,
    cmd: CommandRequest,
    result: CommandResult,
    diagnostics: dict[str, Any],
) -> list[dict[str, Any]]:
    map_path = resolve_map_path(cmd, result, diagnostics)
    if map_path is None:
        return []

    maps_dir = session_root / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    stem = _slugify(map_path.stem)
    dest_json = maps_dir / f"{stem}.json"
    shutil.copy2(map_path, dest_json)

    dest_md = maps_dir / f"{stem}.md"
    try:
        from ..control.gui_map import load_gui_map
        from ..control.gui_map_export import write_map_artifacts

        pack = load_gui_map(map_path)
        write_map_artifacts(pack, json_path=dest_json, md_path=dest_md, title=stem)
    except Exception:
        sibling_md = map_path.with_suffix(".md")
        if sibling_md.is_file():
            shutil.copy2(sibling_md, dest_md)

    dest_svg = maps_dir / f"{stem}.svg"
    sibling_svg = map_path.with_suffix(".svg")
    if sibling_svg.is_file():
        shutil.copy2(sibling_svg, dest_svg)

    entries: list[dict[str, Any]] = []
    for suffix, kind in ((".json", "map"), (".md", "map-md"), (".svg", "map-svg")):
        path = maps_dir / f"{stem}{suffix}"
        if not path.is_file():
            continue
        entries.append(
            {
                "kind": kind,
                "path": str(path),
                "session_path": path.relative_to(session_root).as_posix(),
                "source": str(map_path),
            }
        )
    if entries:
        try:
            from ..gui_map_events import record_gui_map_built
            from ..control.gui_map import load_gui_map

            pack = load_gui_map(dest_json)
            record_gui_map_built(
                map_path=str(dest_json),
                element_count=len(pack.elements),
                region_count=len(pack.regions),
                scope_ids=list(pack.regions.keys()),
            )
        except Exception:
            pass
    return entries


def _reprocess_steps(doc: SessionDocument, session_dir: Path) -> tuple[dict[str, dict[str, Any]], int]:
    from .commands import CommandResult

    diagnostics_by_request: dict[str, dict[str, Any]] = {}
    updated_steps = 0
    for step in doc.steps:
        result_path = session_dir / step.result_path
        if not result_path.is_file():
            continue
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        result = CommandResult(
            ok=bool(payload.get("ok")),
            action=str(payload.get("action") or ""),
            data=dict(payload.get("data") or {}),
            command=str(payload.get("command") or ""),
            diagnostics=dict(payload.get("diagnostics") or {}),
        )
        diagnostics = extract_diagnostics(result)
        if diagnostics != step.diagnostics:
            updated_steps += 1
        step.diagnostics = diagnostics
        diagnostics_by_request[step.request_id] = diagnostics
        diag_path = session_dir / "steps" / step.step_id / "diagnostics.json"
        diag_path.parent.mkdir(parents=True, exist_ok=True)
        diag_path.write_text(
            json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return diagnostics_by_request, updated_steps


def _reprocess_events(
    doc: SessionDocument,
    session_dir: Path,
    diagnostics_by_request: dict[str, dict[str, Any]],
) -> tuple[int, int]:
    from .event_store import read_events
    from .events import DomainEvent, control_events_from_diagnostics, map_events_from_diagnostics

    added_control_events = 0
    added_map_events = 0
    index_path = session_dir / "index.jsonl"
    if not index_path.is_file():
        return 0, 0

    events = read_events(session_dir)
    patched: list[DomainEvent] = []
    for event in events:
        if event.event_type.startswith("Control") or event.event_type.startswith("GuiMap"):
            continue
        if event.request_id in diagnostics_by_request and event.event_type in {
            "StepRecorded",
            "CommandCompleted",
        }:
            body = dict(event.body)
            body["diagnostics"] = diagnostics_by_request[event.request_id]
            event = DomainEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                occurred_at_ms=event.occurred_at_ms,
                session_id=event.session_id,
                request_id=event.request_id,
                aggregate=event.aggregate,
                body=body,
            )
        patched.append(event)
        if event.event_type == "StepRecorded" and event.request_id:
            step = next((item for item in doc.steps if item.request_id == event.request_id), None)
            if step is None:
                continue
            diagnostics = diagnostics_by_request.get(step.request_id, {})
            control_events = control_events_from_diagnostics(
                session_id=doc.session_id,
                request_id=step.request_id,
                verb=step.verb,
                diagnostics=diagnostics,
                ok=step.ok,
            )
            patched.extend(control_events)
            added_control_events += len(control_events)
            map_events = map_events_from_diagnostics(
                session_id=doc.session_id,
                request_id=step.request_id,
                diagnostics=diagnostics,
            )
            patched.extend(map_events)
            added_map_events += len(map_events)

    index_path.write_text(
        "\n".join(json.dumps(event.to_dict(), ensure_ascii=False) for event in patched) + "\n",
        encoding="utf-8",
    )
    return added_control_events, added_map_events


def _update_session_files(doc: SessionDocument, session_dir: Path) -> None:
    doc.summary = _build_summary(doc.steps)
    (session_dir / "session.json").write_text(
        json.dumps(doc.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (session_dir / "README.md").write_text(render_readme(doc), encoding="utf-8")


def reprocess_session_diagnostics(session_dir: Path) -> dict[str, Any]:
    """Re-extract diagnostics from stored step results and refresh session artifacts."""
    from .projections import refresh_projections

    session_dir = session_dir.expanduser()
    if not session_dir.is_absolute():
        session_dir = Path.cwd() / session_dir
    if not (session_dir / "session.json").is_file():
        raise FileNotFoundError(f"not a session directory: {session_dir}")

    doc = load_session_document(session_dir)
    diagnostics_by_request, updated_steps = _reprocess_steps(doc, session_dir)
    _update_session_files(doc, session_dir)
    added_control_events, added_map_events = _reprocess_events(doc, session_dir, diagnostics_by_request)

    refresh_projections(session_dir)
    return {
        "session_id": doc.session_id,
        "session_dir": str(session_dir),
        "updated_steps": updated_steps,
        "added_control_events": added_control_events,
        "added_map_events": added_map_events,
        "backends_used": doc.summary.get("backends_used", []),
    }


def discover_session_dirs(*, root: Path | None = None) -> list[Path]:
    from .history.loader import discover_session_dirs as _discover_all

    return _discover_all(root=root)


def load_session_document(session_dir: Path) -> SessionDocument:
    payload = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    steps = [StepRecord(**item) for item in payload.get("steps", [])]
    return SessionDocument(
        version=int(payload.get("version", 1)),
        session_id=str(payload.get("session_id") or session_dir.name),
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
        maps=list(payload.get("maps") or []),
    )


def export_session_zip(session_dir: Path, output: Path) -> Path:
    import zipfile

    output = output.expanduser()
    if output.suffix != ".zip":
        output = output.with_suffix(".zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        prefix = session_dir.name
        for path in sorted(session_dir.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=f"{prefix}/{path.relative_to(session_dir).as_posix()}")
    return output


def _build_summary(steps: list[StepRecord]) -> dict[str, Any]:
    ok_steps = sum(1 for step in steps if step.ok)
    failed = len(steps) - ok_steps
    backends: set[str] = set()
    for step in steps:
        routing = step.diagnostics.get("routing") or (step.diagnostics.get("control") or {}).get("routing") or {}
        provider = routing.get("selected_provider")
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
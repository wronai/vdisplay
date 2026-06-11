"""Observe → act → verify helpers for planfile automation."""

from __future__ import annotations

import json
import os
import re
import shlex
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from ..config_options import ConfigOptions, get_runtime_options
from ..project_config import ProjectConfig
from .metadata import artifact_paths, copy_sidecar
from .tasks import AutoTask


def _control_markers(options: ConfigOptions | None = None) -> tuple[str, ...]:
    return tuple((options or ConfigOptions.defaults()).control_actuation_markers)


@dataclass
class TaskFeedback:
    """Sidecar metadata from observe preflight and post-action verify parsing."""

    observe_path: str | None = None
    screen_context_path: str | None = None
    vql_path: str | None = None
    prepared_command: str = ""
    verify_requested: bool = False
    verify_passed: bool | None = None
    vision_stub: bool = False
    post_verify_path: str | None = None
    session_dir: str | None = None
    decision_data: dict[str, Any] = field(default_factory=dict)
    metadata_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observe_path": self.observe_path,
            "screen_context_path": self.screen_context_path,
            "vql_path": self.vql_path,
            "prepared_command": self.prepared_command,
            "verify_requested": self.verify_requested,
            "verify_passed": self.verify_passed,
            "vision_stub": self.vision_stub,
            "post_verify_path": self.post_verify_path,
            "session_dir": self.session_dir,
            "decision_data": self.decision_data,
            "metadata_paths": self.metadata_paths,
            "notes": self.notes,
        }


def is_control_command(command: str, *, options: ConfigOptions | None = None) -> bool:
    lowered = command.strip().lower()
    return any(marker.lower() in lowered for marker in _control_markers(options))


def is_control_actuation(command: str, *, options: ConfigOptions | None = None) -> bool:
    """Commands that require real coordinates (not find/list diagnostics)."""
    lowered = command.strip().lower()
    if not is_control_command(lowered, options=options):
        return False
    if "control find" in lowered or "controls_find" in lowered or "control list" in lowered:
        return False
    return True


def wants_observe(task: AutoTask, config: ProjectConfig | None = None) -> bool:
    """Preflight screenshot+sidecar before control actuation or when explicitly requested."""
    raw = task.raw or {}
    options = config.options if config is not None else None
    if raw.get("observe") in {True, "true", "1", 1}:
        return True
    if config is not None and config.automation.observe and is_control_command(task.command, options=options):
        return True
    if not is_control_command(task.command, options=options):
        return bool(raw.get("observe") in {True, "true", "1", 1})
    return bool(task.verify)


def wants_observe_on_screenshot(config: ProjectConfig | None) -> bool:
    if config is None:
        return os.environ.get("VDISPLAY_OBSERVE", "").strip().lower() in {"1", "true", "yes"}
    return config.automation.observe_on_screenshot


def _inject_monitor(cmd_line: str, lowered: str, monitor: str, *, options: ConfigOptions | None = None) -> str:
    if "screenshot" in lowered and "--source" not in lowered:
        cmd_line = f"{cmd_line} --source {shlex.quote(monitor)}"
    if is_control_command(cmd_line, options=options):
        os.environ.setdefault("VDISPLAY_CAPTURE_SOURCE", monitor)
    return cmd_line


def _inject_map(cmd_line: str, lowered: str, map_path: str, *, options: ConfigOptions | None = None) -> str:
    if map_path and is_control_command(cmd_line, options=options) and "--map" not in lowered:
        cmd_line = f"{cmd_line} --map {shlex.quote(map_path)}"
    return cmd_line


def _inject_verify(
    cmd_line: str,
    lowered: str,
    verify: bool,
    feedback: TaskFeedback,
    *,
    options: ConfigOptions | None = None,
) -> tuple[str, TaskFeedback]:
    if verify and is_control_command(cmd_line, options=options) and "--verify" not in lowered:
        cmd_line = f"{cmd_line} --verify"
        feedback.verify_requested = True
    return cmd_line, feedback


def _inject_observe(config: ProjectConfig | None, lowered: str) -> None:
    if wants_observe_on_screenshot(config) and "screenshot" in lowered:
        os.environ.setdefault("VDISPLAY_OBSERVE", "1")


def prepare_command(
    command: str,
    task: AutoTask,
    *,
    config: ProjectConfig | None = None,
) -> tuple[str, TaskFeedback]:
    """Inject monitor/map/verify flags from planfile task + vdisplay.yaml."""
    feedback = TaskFeedback(prepared_command=command.strip(), verify_requested=bool(task.verify))
    parts = shlex.split(command)
    if not parts:
        return command, feedback

    cmd_line = command.strip()
    lowered = cmd_line.lower()
    options = config.options if config is not None else None

    monitor = task.monitor or (config.default_monitor if config else None)
    if monitor:
        cmd_line = _inject_monitor(cmd_line, lowered, monitor, options=options)

    map_path = task.map_path
    if config and map_path:
        map_path = config.resolve_map_path(map_path) or map_path
    if map_path:
        cmd_line = _inject_map(cmd_line, lowered, map_path, options=options)

    verify = task.verify
    if config and config.automation.verify_strict and is_control_command(cmd_line, options=options):
        verify = verify or task.verify
    cmd_line, feedback = _inject_verify(cmd_line, lowered, verify, feedback, options=options)

    _inject_observe(config, lowered)

    feedback.prepared_command = cmd_line
    return cmd_line, feedback


def _try_extract_verify_from_chunk(chunk: dict[str, Any]) -> bool | None:
    for key in ("verified", "verify_ok", "verify_passed"):
        if key in chunk:
            return bool(chunk[key])
    verify = chunk.get("verify")
    if isinstance(verify, dict) and "verified" in verify:
        return bool(verify["verified"])
    diagnostics = chunk.get("diagnostics")
    if isinstance(diagnostics, dict):
        control = diagnostics.get("control") or {}
        verify_block = control.get("verify") or {}
        if isinstance(verify_block, dict) and "verified" in verify_block:
            return bool(verify_block["verified"])
    return None


def parse_verify_from_output(output: str) -> bool | None:
    """Return verify pass/fail when JSON output exposes it."""
    text = (output or "").strip()
    if not text:
        return None
    for chunk in _json_chunks(text):
        result = _try_extract_verify_from_chunk(chunk)
        if result is not None:
            return result
    if re.search(r'"verified"\s*:\s*false', text, re.I):
        return False
    if re.search(r'"verified"\s*:\s*true', text, re.I):
        return True
    return None


def parse_vision_stub_from_output(output: str) -> bool:
    """Detect vision find/control results with zero bounds or explicit stub flag."""
    for chunk in _json_chunks(output or ""):
        for key in ("selected", "match"):
            node = chunk.get(key)
            if isinstance(node, dict) and _node_is_vision_stub(node):
                return True
        for node in chunk.get("matches") or []:
            if isinstance(node, dict) and _node_is_vision_stub(node):
                return True
    return bool(re.search(r'"stub"\s*:\s*true', output or "", re.I))


def _node_is_vision_stub(node: dict[str, Any]) -> bool:
    state = node.get("state") or {}
    if isinstance(state, dict) and state.get("stub"):
        return True
    bounds = node.get("bounds") or {}
    if not isinstance(bounds, dict):
        return False
    width = int(bounds.get("width") or 0)
    height = int(bounds.get("height") or 0)
    return width <= 0 and height <= 0 and str(node.get("backend") or "") == "vision"


def _json_chunks(text: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            chunks.append(payload)
            data = payload.get("data")
            if isinstance(data, dict):
                chunks.append(data)
    except json.JSONDecodeError:
        pass
    return chunks


@contextmanager
def task_execution_env(
    task: AutoTask,
    feedback: TaskFeedback,
    *,
    config: ProjectConfig | None = None,
) -> Iterator[None]:
    """Scope capture/control/session env to planfile + vdisplay.yaml."""
    saved: dict[str, str | None] = {}
    keys = (
        "VDISPLAY_CAPTURE_SOURCE",
        "VDISPLAY_SCREEN_CONTEXT_PATH",
        "VDISPLAY_OBSERVE",
        "VDISPLAY_SESSION",
        "VDISPLAY_SESSION_DIR",
        "VDISPLAY_SESSION_ID",
        "VDISPLAY_SESSION_BASE",
        "KORU_AUTOPILOT_INSTANCE",
        "KORU_AUTOPILOT_SOCKET",
        "KORU_VDISPLAY_AGENT_URL",
    )
    for key in keys:
        saved[key] = os.environ.get(key)

    try:
        monitor = task.monitor or (config.default_monitor if config else None)
        if monitor:
            os.environ["VDISPLAY_CAPTURE_SOURCE"] = monitor
        if feedback.screen_context_path:
            os.environ["VDISPLAY_SCREEN_CONTEXT_PATH"] = feedback.screen_context_path
        if wants_observe_on_screenshot(config):
            os.environ.setdefault("VDISPLAY_OBSERVE", "1")
        if config is not None and config.automation.session:
            os.environ.setdefault("VDISPLAY_SESSION", "1")
            os.environ.setdefault("VDISPLAY_SESSION_BASE", str(config.metadata_dir))
            if feedback.session_dir:
                os.environ["VDISPLAY_SESSION_DIR"] = feedback.session_dir
        _apply_koru_env(task)
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def preflight_observe(
    task: AutoTask,
    *,
    project: str | None,
    execute_fn,
    config: ProjectConfig | None = None,
) -> TaskFeedback:
    """Capture + observe before control actuation (feeds OCR cache for verify)."""
    feedback = TaskFeedback(verify_requested=bool(task.verify))
    if not wants_observe(task, config):
        return feedback

    monitor = task.monitor or (config.default_monitor if config else "DP-1")
    if config is not None:
        dest = artifact_paths(config, task_id=task.id, kind="observe")
        out_path = str(dest.with_suffix(".png"))
    else:
        out_path = f"/tmp/vdisplay-auto-observe-{task.id}.png"

    cmd = f"vdisplay screenshot -o {shlex.quote(out_path)} --source {shlex.quote(monitor)}"
    prev_observe = os.environ.get("VDISPLAY_OBSERVE")
    os.environ["VDISPLAY_OBSERVE"] = "1"
    try:
        result = execute_fn(cmd, dry_run=False)
    finally:
        if prev_observe is None:
            os.environ.pop("VDISPLAY_OBSERVE", None)
        else:
            os.environ["VDISPLAY_OBSERVE"] = prev_observe

    feedback.observe_path = out_path
    if not result.ok:
        feedback.notes.append(f"observe preflight failed: {result.error or result.output}")
        return feedback

    sidecar = _sidecar_from_screenshot_output(result.output)
    if sidecar:
        feedback.screen_context_path = sidecar
        feedback.notes.append(f"observe sidecar: {sidecar}")
    vql = _vql_from_screenshot_output(result.output, out_path)
    if vql:
        feedback.vql_path = vql
        feedback.notes.append(f"observe vql: {vql}")

    png_path = Path(out_path)
    if png_path.is_file() and config is not None:
        copied = copy_sidecar(png_path, png_path, options=config.options if config else None)
        feedback.metadata_paths.extend(copied)

    if not sidecar:
        feedback.notes.append("observe preflight screenshot ok (no sidecar path)")
    return feedback


def _sidecar_from_screenshot_output(output: str) -> str | None:
    for chunk in _json_chunks(output or ""):
        for key in ("screen_context_path", "context_path"):
            value = chunk.get(key)
            if value:
                return str(value)
        artifacts = chunk.get("artifacts") or chunk.get("screen_context") or {}
        if isinstance(artifacts, dict):
            ctx_path = artifacts.get("context") or artifacts.get("path")
            if ctx_path:
                return str(ctx_path)
    return None


def _vql_from_screenshot_output(output: str, png_path: str) -> str | None:
    for chunk in _json_chunks(output or ""):
        for key in ("vql_path", "vql"):
            value = chunk.get(key)
            if isinstance(value, str) and value:
                return value
            if isinstance(value, dict):
                path = value.get("path")
                if path:
                    return str(path)
        artifacts = chunk.get("artifacts") or {}
        if isinstance(artifacts, dict):
            vql_path = artifacts.get("vql")
            if vql_path:
                return str(vql_path)
    candidate = Path(png_path).with_suffix(Path(png_path).suffix + ".vql.json")
    return str(candidate) if candidate.is_file() else None


def finalize_result_ok(
    result,
    feedback: TaskFeedback,
    *,
    config: ProjectConfig | None = None,
) -> bool:
    """Combine exit code with verify flags and vision stub rejection."""
    if not result.ok:
        return False

    if parse_vision_stub_from_output(result.output):
        feedback.vision_stub = True
        reject = config.automation.reject_vision_stubs if config else True
        if reject and is_control_actuation(
            feedback.prepared_command or "",
            options=config.options if config else None,
        ):
            feedback.notes.append("vision stub detected (zero bounds) — actuation metadata missing")
            return False

    if not feedback.verify_requested:
        return True

    parsed = parse_verify_from_output(result.output)
    feedback.verify_passed = parsed
    if parsed is False:
        return False
    strict = config.automation.verify_strict if config else True
    if strict and parsed is None:
        feedback.notes.append("verify requested but no verified field in output")
        return False
    return True


def attach_session_dir(feedback: TaskFeedback, session_dir: Path | str | None) -> None:
    if session_dir:
        feedback.session_dir = str(session_dir)


def _apply_koru_env(task: AutoTask) -> None:
    """Scope koru autopilot socket/instance for cross-IDE planfile tasks."""
    raw = task.raw or {}
    instance = str(raw.get("koru_instance") or raw.get("koru") or "").strip()
    if not instance:
        return
    socket = str(raw.get("koru_socket") or f"/run/user/{os.getuid()}/koru-autopilot-{instance}.sock")
    os.environ["KORU_AUTOPILOT_INSTANCE"] = instance
    os.environ["KORU_AUTOPILOT_SOCKET"] = socket
    agent_url = os.environ.get("VDISPLAY_AGENT_URL") or os.environ.get("KORU_VDISPLAY_AGENT_URL")
    if agent_url:
        os.environ.setdefault("KORU_VDISPLAY_AGENT_URL", agent_url)


def _map_path_from_command(command: str) -> str | None:
    parts = shlex.split(command)
    for index, part in enumerate(parts):
        if part == "--map" and index + 1 < len(parts):
            return parts[index + 1]
    return None


def preflight_actuation(
    task: AutoTask,
    feedback: TaskFeedback,
    *,
    prepared_command: str,
    config: ProjectConfig | None,
) -> bool:
    """Fail fast when vision actuation has neither OCR nor a built map."""
    cmd = prepared_command or task.command
    if not is_control_actuation(cmd, options=config.options if config else None):
        return True

    lowered = cmd.lower()
    uses_vision = "vision" in lowered or "--backend" not in lowered
    if not uses_vision:
        return True

    map_path = task.map_path or _map_path_from_command(cmd)
    if map_path and Path(map_path).is_file():
        feedback.notes.append(f"actuation preflight: map {map_path}")
        return True

    try:
        from ...control.vision_ocr import ocr_available

        ocr_ok, ocr_reason = ocr_available()
    except Exception as exc:
        ocr_ok, ocr_reason = False, str(exc)

    if ocr_ok:
        feedback.notes.append(f"actuation preflight: OCR ready ({ocr_reason})")
        return True

    hint = "bash examples/dev-workflow/setup-autonomy.sh"
    feedback.notes.append(
        f"actuation preflight failed: no map file and OCR unavailable ({ocr_reason}). Run: {hint}"
    )
    reject = config.automation.reject_vision_stubs if config else True
    return not reject


def _should_post_verify(
    feedback: TaskFeedback,
    task: AutoTask,
    config: ProjectConfig | None,
) -> str | None:
    if not feedback.verify_requested:
        return None
    if feedback.verify_passed is False:
        return None
    if config is None or not config.automation.post_act_verify:
        return None
    if not is_control_actuation(
        feedback.prepared_command or task.command,
        options=config.options if config else None,
    ):
        return None
    return task.monitor or (config.default_monitor if config else None)


def _run_post_verify_screenshot(
    monitor: str,
    out_path: str,
    config: ProjectConfig | None,
    execute_fn,
) -> tuple[bool, str]:
    cmd = f"vdisplay screenshot -o {shlex.quote(out_path)} --source {shlex.quote(monitor)}"
    prev_observe = os.environ.get("VDISPLAY_OBSERVE")
    if wants_observe_on_screenshot(config):
        os.environ["VDISPLAY_OBSERVE"] = "1"
    try:
        result = execute_fn(cmd, dry_run=False)
    finally:
        if prev_observe is None:
            os.environ.pop("VDISPLAY_OBSERVE", None)
        else:
            os.environ["VDISPLAY_OBSERVE"] = prev_observe
    if not result.ok:
        return False, f"post-act verify screenshot failed: {result.error or result.output}"
    return True, ""


def post_act_verify_screenshot(
    feedback: TaskFeedback,
    task: AutoTask,
    *,
    config: ProjectConfig | None,
    execute_fn,
) -> None:
    """Capture post-actuation screenshot when verify was requested and actuation succeeded."""
    monitor = _should_post_verify(feedback, task, config)
    if not monitor:
        return

    dest = artifact_paths(config, task_id=f"{task.id}-post-verify", kind="observe")
    out_path = str(dest.with_suffix(".png"))
    ok, note = _run_post_verify_screenshot(monitor, out_path, config, execute_fn)
    if not ok:
        feedback.notes.append(note)
        return

    png_path = Path(out_path)
    if png_path.is_file():
        copied = copy_sidecar(png_path, png_path, options=config.options if config else None)
        feedback.post_verify_path = out_path
        feedback.metadata_paths.extend(copied)
        feedback.notes.append(f"post-act verify screenshot: {out_path}")

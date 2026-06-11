"""Observe → act → verify helpers for planfile automation."""

from __future__ import annotations

import json
import os
import re
import shlex
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

from .tasks import AutoTask

_CONTROL_MARKERS = (
    "control click",
    "control focus",
    "control set-value",
    "control find",
    "control list",
    "ide prompt",
    "CONTROL_CLICK",
    "CONTROL_FOCUS",
    "CONTROL_SET_VALUE",
    "CONTROLS_FIND",
    "CONTROLS_LIST",
)


@dataclass
class TaskFeedback:
    """Sidecar metadata from observe preflight and post-action verify parsing."""

    observe_path: str | None = None
    screen_context_path: str | None = None
    prepared_command: str = ""
    verify_requested: bool = False
    verify_passed: bool | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observe_path": self.observe_path,
            "screen_context_path": self.screen_context_path,
            "prepared_command": self.prepared_command,
            "verify_requested": self.verify_requested,
            "verify_passed": self.verify_passed,
            "notes": self.notes,
        }


def is_control_command(command: str) -> bool:
    lowered = command.strip().lower()
    return any(marker.lower() in lowered for marker in _CONTROL_MARKERS)


def wants_observe(task: AutoTask) -> bool:
    """Preflight screenshot+sidecar only before control actuation."""
    if not is_control_command(task.command):
        return False
    raw = task.raw or {}
    if raw.get("observe") in {True, "true", "1", 1}:
        return True
    return bool(task.verify)


def prepare_command(command: str, task: AutoTask) -> tuple[str, TaskFeedback]:
    """Inject monitor/map/verify flags from planfile task metadata."""
    feedback = TaskFeedback(prepared_command=command.strip(), verify_requested=bool(task.verify))
    parts = shlex.split(command)
    if not parts:
        return command, feedback

    cmd_line = command.strip()
    lowered = cmd_line.lower()

    if task.monitor:
        if "screenshot" in lowered and "--source" not in lowered:
            cmd_line = f"{cmd_line} --source {shlex.quote(task.monitor)}"
        if is_control_command(cmd_line) and "--display" not in lowered:
            os.environ.setdefault("VDISPLAY_CAPTURE_SOURCE", task.monitor)

    if task.map_path and is_control_command(cmd_line):
        if "--map" not in lowered:
            cmd_line = f"{cmd_line} --map {shlex.quote(task.map_path)}"

    if task.verify and is_control_command(cmd_line) and "--verify" not in lowered:
        cmd_line = f"{cmd_line} --verify"

    feedback.prepared_command = cmd_line
    return cmd_line, feedback


def parse_verify_from_output(output: str) -> bool | None:
    """Return verify pass/fail when JSON output exposes it."""
    text = (output or "").strip()
    if not text:
        return None
    for chunk in _json_chunks(text):
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
    if re.search(r'"verified"\s*:\s*false', text, re.I):
        return False
    if re.search(r'"verified"\s*:\s*true', text, re.I):
        return True
    return None


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
def task_execution_env(task: AutoTask, feedback: TaskFeedback) -> Iterator[None]:
    """Temporarily scope capture/control env to planfile monitor + observe sidecar."""
    saved: dict[str, str | None] = {}
    keys = {
        "VDISPLAY_CAPTURE_SOURCE": os.environ.get("VDISPLAY_CAPTURE_SOURCE"),
        "VDISPLAY_SCREEN_CONTEXT_PATH": os.environ.get("VDISPLAY_SCREEN_CONTEXT_PATH"),
        "VDISPLAY_OBSERVE": os.environ.get("VDISPLAY_OBSERVE"),
    }
    try:
        if task.monitor:
            os.environ["VDISPLAY_CAPTURE_SOURCE"] = task.monitor
        if feedback.screen_context_path:
            os.environ["VDISPLAY_SCREEN_CONTEXT_PATH"] = feedback.screen_context_path
        yield
    finally:
        for key, value in keys.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def preflight_observe(task: AutoTask, *, project: str | None, execute_fn) -> TaskFeedback:
    """Capture + observe before control actuation (feeds OCR cache for verify)."""
    feedback = TaskFeedback(verify_requested=bool(task.verify))
    if not wants_observe(task):
        return feedback

    monitor = task.monitor or "DP-1"
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
    else:
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


def finalize_result_ok(result, feedback: TaskFeedback) -> bool:
    """Combine exit code with explicit verify flags in JSON output."""
    if not result.ok:
        return False
    if not feedback.verify_requested:
        return True
    parsed = parse_verify_from_output(result.output)
    feedback.verify_passed = parsed
    if parsed is False:
        return False
    return True

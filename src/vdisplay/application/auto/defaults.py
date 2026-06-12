"""Apply vdisplay.yaml defaults to automation tasks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config_options import ConfigOptions, VqlOptions
from ..project_config import ActionSpec, ProjectConfig
from .feedback import is_control_command
from .tasks import AutoTask


def _resolve_action_map(config: ProjectConfig, action_spec: ActionSpec | None) -> str | None:
    """Resolve map from action spec or conventional maps/{app}-chat.json."""
    if action_spec is None:
        return None
    if action_spec.map_path:
        resolved = config.resolve_map_path(action_spec.map_path)
        if resolved and Path(resolved).is_file():
            return resolved
    if not action_spec.app:
        return None
    templates = config.options.action_map_templates
    for template in templates:
        candidate = template.format(
            app=action_spec.app,
            id=action_spec.id,
            id_dash=action_spec.id.replace("_", "-"),
        )
        resolved = config.resolve_map_path(candidate)
        if resolved and Path(resolved).is_file():
            return resolved
    return None


def _resolve_task_monitor(task: AutoTask, config: ProjectConfig, action_spec: ActionSpec | None) -> str | None:
    monitor = task.monitor or (action_spec.monitor if action_spec and action_spec.monitor else None)
    if not monitor:
        monitor = config.default_monitor
    return monitor


def _resolve_task_map_path(task: AutoTask, config: ProjectConfig, action_spec: ActionSpec | None) -> str | None:
    map_path = task.map_path or _resolve_action_map(config, action_spec)
    if not map_path and config.automation.default_map:
        map_path = config.resolve_map_path(config.automation.default_map)
    return map_path


def _resolve_task_command(task: AutoTask, action_spec: ActionSpec | None, config: ProjectConfig) -> str:
    command = task.command
    if action_spec and action_spec.command and not command.strip():
        command = action_spec.command
    elif action_spec and action_spec.vision_anchor and _wants_vision_injection(command, config.options):
        command = _inject_vision_anchor(command, action_spec)
    return command


def apply_project_defaults(task: AutoTask, config: ProjectConfig) -> AutoTask:
    """Merge project vdisplay.yaml monitors/actions into a planfile task."""
    raw = dict(task.raw or {})
    action_ref = str(raw.get("action_ref") or raw.get("action") or "").strip()
    action_spec: ActionSpec | None = config.action(action_ref) if action_ref else None

    monitor = _resolve_task_monitor(task, config, action_spec)
    map_path = _resolve_task_map_path(task, config, action_spec)
    verify = task.verify or (action_spec.verify if action_spec else False)
    if action_spec and action_spec.observe:
        raw["observe"] = True
    command = _resolve_task_command(task, action_spec, config)
    raw.setdefault("observe", config.automation.observe)

    return AutoTask(
        id=task.id,
        title=task.title,
        command=command,
        source=task.source,
        priority=task.priority,
        status=task.status,
        description=task.description,
        monitor=monitor,
        map_path=map_path,
        verify=verify,
        raw=raw,
        ticket_id=task.ticket_id,
    )


def _wants_vision_injection(command: str, options: ConfigOptions | None = None) -> bool:
    """Inject vision anchors only on control actuation/find, not ide prompt."""
    opts = options or ConfigOptions.defaults()
    lowered = command.strip().lower()
    if "ide prompt" in lowered:
        return False
    return any(token in lowered for token in opts.vision_injection_commands)


def _inject_vision_anchor(command: str, spec: ActionSpec) -> str:
    import shlex

    parts = shlex.split(command)
    joined = " ".join(parts).lower()
    if "--vision-anchor" in joined:
        return command
    extras = [f"--vision-anchor {shlex.quote(spec.vision_anchor)}"]
    if spec.vision_anchor_rel:
        extras.append(f"--vision-anchor-rel {shlex.quote(spec.vision_anchor_rel)}")
    if spec.backend and spec.backend != "auto" and "--backend" not in joined:
        extras.append(f"--backend {shlex.quote(spec.backend)}")
    return f"{command} {' '.join(extras)}".strip()


def _vql_layers_from_program(program: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = program.get("metadata") or {}
    render_intent = metadata.get("render_intent") or {}
    layers = render_intent.get("layers") or []
    if layers:
        return layers
    scene = program.get("scene") or {}
    return scene.get("layers") or []


def _vql_target_entry(layer: dict[str, Any], *, options: VqlOptions | None = None) -> dict[str, Any] | None:
    opts = options or VqlOptions()
    center = layer.get("click_center") or layer.get("center")
    if not isinstance(center, dict):
        return None
    text = str(layer.get("text") or "").strip()
    kind = str(layer.get("kind") or "element")
    if kind == "ocr" and (not text or len(text) > opts.ocr_text_max_len):
        return None
    entry: dict[str, Any] = {
        "kind": kind,
        "click_center": {"x": int(center["x"]), "y": int(center["y"])},
    }
    if layer.get("id"):
        entry["id"] = layer["id"]
    if text:
        entry["text"] = text
    bbox = layer.get("bbox")
    if isinstance(bbox, dict):
        entry["bbox"] = bbox
    return entry


def vql_decision_slice(
    vql_path: str | Path | None,
    *,
    options: ConfigOptions | None = None,
) -> dict[str, Any]:
    """Compact VQL targets for decide/act (centers, kinds, labels)."""
    opts = options or ConfigOptions.defaults()
    vql_opts = opts.vql
    if not vql_path:
        return {}
    path = Path(vql_path).expanduser()
    if not path.is_file():
        return {}
    try:
        program = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    layers = _vql_layers_from_program(program)
    priority = vql_opts.kind_priority
    targets: list[dict[str, Any]] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        entry = _vql_target_entry(layer, options=vql_opts)
        if entry:
            targets.append(entry)
    targets.sort(key=lambda item: priority.get(str(item.get("kind")), 9))
    return {
        "vql_path": str(path.resolve()),
        "vql_layer_count": len(layers),
        "vql_targets": targets[: vql_opts.target_limit],
    }


def _check_ocr_status() -> tuple[bool, str]:
    """Best-effort check whether OCR is available."""
    try:
        from ...control.vision_ocr import ocr_available

        return ocr_available()
    except Exception as exc:
        return False, str(exc)


def _build_base_decision_data(
    task: AutoTask,
    config: ProjectConfig,
    *,
    action_ref: str,
    action_spec: ActionSpec | None,
    prepared_command: str,
    ocr_ready: bool,
    ocr_reason: str,
) -> dict[str, Any]:
    """Assemble the base decision data dict (before VQL slice)."""
    raw = task.raw or {}
    map_path = task.map_path
    map_available = bool(map_path and Path(map_path).is_file())
    base = config.metadata_dir
    return {
        "action_ref": action_ref or None,
        "koru_instance": str(raw.get("koru_instance") or raw.get("koru") or "") or None,
        "monitor": task.monitor,
        "map_path": map_path,
        "map_available": map_available,
        "vision_anchor": action_spec.vision_anchor if action_spec else None,
        "vision_anchor_rel": action_spec.vision_anchor_rel if action_spec else None,
        "backend": action_spec.backend if action_spec else None,
        "verify": bool(task.verify),
        "observe": bool(raw.get("observe")),
        "ocr_ready": ocr_ready,
        "ocr_reason": ocr_reason,
        "prepared_command": prepared_command or task.command,
        "data_locations": config.options.data_location_paths(base),
    }


def build_decision_data(
    task: AutoTask,
    config: ProjectConfig,
    *,
    prepared_command: str = "",
    vql_path: str | Path | None = None,
) -> dict[str, Any]:
    """Audit record: which defaults and actuation paths apply to this task."""
    raw = task.raw or {}
    action_ref = str(raw.get("action_ref") or raw.get("action") or "").strip()
    action_spec: ActionSpec | None = config.action(action_ref) if action_ref else None
    ocr_ready, ocr_reason = _check_ocr_status()
    data = _build_base_decision_data(
        task,
        config,
        action_ref=action_ref,
        action_spec=action_spec,
        prepared_command=prepared_command,
        ocr_ready=ocr_ready,
        ocr_reason=ocr_reason,
    )
    data.update(vql_decision_slice(vql_path, options=config.options))
    return data

"""Load runnable automation tasks from planfile.yaml or .planfile tickets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ...exceptions import VDisplayError
from ..config_options import ConfigOptions, get_runtime_options


def _yaml():
    try:
        import yaml
    except ImportError:
        try:
            from ...utils import auto_install_package

            auto_install_package("PyYAML>=6.0")
            import yaml
        except Exception as exc:
            raise VDisplayError(
                f"PyYAML required for planfile automation — auto-install failed: {exc}"
            ) from exc
    return yaml


def ensure_auto_dependencies(*, source: AutoSource = "auto") -> None:
    """Install optional auto extras on demand (PyYAML, planfile ticket queue)."""
    if source in {"auto", "yaml"}:
        _yaml()
        return
    if source == "tickets":
        _yaml()
        try:
            import planfile  # noqa: F401
        except ImportError:
            try:
                from ...utils import auto_install_package

                auto_install_package("planfile>=0.1.103")
            except Exception as exc:
                raise VDisplayError(
                    f"planfile package required for ticket queue — auto-install failed: {exc}"
                ) from exc

AutoSource = Literal["auto", "yaml", "tickets"]


def _task_options(project: Path) -> ConfigOptions:
    return get_runtime_options(project)


def _legacy_planfile_keys(options: ConfigOptions) -> list[str]:
    return [key for key in options.planfile_task_keys if key != "tasks"]


@dataclass
class AutoTask:
    id: str
    title: str
    command: str
    source: str
    priority: str = "normal"
    status: str = "todo"
    description: str = ""
    monitor: str | None = None
    map_path: str | None = None
    verify: bool = False
    raw: dict[str, Any] = field(default_factory=dict)
    ticket_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "command": self.command,
            "source": self.source,
            "priority": self.priority,
            "status": self.status,
            "description": self.description,
            "monitor": self.monitor,
            "map_path": self.map_path,
            "verify": self.verify,
            "ticket_id": self.ticket_id,
        }


def resolve_planfile_path(project: str | Path, planfile: str | Path | None) -> Path:
    root = Path(project).expanduser().resolve()
    if planfile:
        path = Path(planfile).expanduser()
        if not path.is_absolute():
            path = root / path
        return path.resolve()
    return root / "planfile.yaml"


def load_auto_tasks(
    *,
    project: str | Path = ".",
    planfile: str | Path | None = None,
    source: AutoSource = "auto",
) -> list[AutoTask]:
    root = Path(project).expanduser().resolve()
    yaml_path = resolve_planfile_path(root, planfile)
    options = _task_options(root)

    yaml_tasks: list[AutoTask] = []
    if source in {"auto", "yaml"} and yaml_path.is_file():
        yaml_tasks = _load_yaml_tasks(yaml_path, options)

    if source == "yaml":
        return _sort_tasks(yaml_tasks, options)

    if yaml_tasks:
        return _sort_tasks(yaml_tasks, options)

    if source in {"auto", "tickets"}:
        return _sort_tasks(_load_ticket_tasks(root, options), options)
    return []


def next_auto_task(tasks: list[AutoTask], *, options: ConfigOptions | None = None) -> AutoTask | None:
    opts = options or ConfigOptions.defaults()
    runnable = [
        task
        for task in tasks
        if task.status.lower() in opts.runnable_statuses() and task.command.strip()
    ]
    if not runnable:
        return None
    return _sort_tasks(runnable, opts)[0]


def _sort_tasks(tasks: list[AutoTask], options: ConfigOptions) -> list[AutoTask]:
    return sorted(
        tasks,
        key=lambda task: (
            options.priority_rank(task.priority),
            task.id,
        ),
    )


def _load_yaml_tasks(path: Path, options: ConfigOptions) -> list[AutoTask]:
    data = _yaml().safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise VDisplayError(f"planfile YAML root must be a mapping: {path}")

    tasks: list[AutoTask] = []
    if str(data.get("schema", "")).strip() == "1.1" and isinstance(data.get("tasks"), list):
        for index, item in enumerate(data["tasks"]):
            if not isinstance(item, dict):
                continue
            task = _task_from_mapping(item, source=f"planfile.yaml:{path.name}", default_id=f"task-{index + 1}")
            if task is not None:
                tasks.append(task)
        return tasks

    for key in _legacy_planfile_keys(options):
        items = data.get(key)
        if isinstance(items, list):
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                task = _task_from_mapping(item, source=f"planfile.yaml:{key}", default_id=f"{key}-{index + 1}")
                if task is not None:
                    tasks.append(task)
    return tasks


def _load_ticket_tasks(root: Path, options: ConfigOptions) -> list[AutoTask]:
    if not (root / ".planfile").is_dir():
        return []
    try:
        from planfile import Planfile
    except ImportError as exc:
        raise VDisplayError(
            "planfile package required for ticket queue — install: "
            "pip install -e /path/to/semcod/planfile"
        ) from exc

    pf = Planfile(str(root))
    tasks: list[AutoTask] = []
    for ticket in pf.list_tickets(status="open"):
        command = _ticket_command(ticket)
        if not command:
            continue
        execution_state = (ticket.execution.state if ticket.execution else "") or ""
        if execution_state not in options.runnable_statuses():
            continue
        tasks.append(
            AutoTask(
                id=str(ticket.id),
                ticket_id=str(ticket.id),
                title=str(ticket.name),
                command=command,
                source=".planfile",
                priority=str(ticket.priority or "normal"),
                status=str(ticket.status.value if hasattr(ticket.status, "value") else ticket.status),
                description=str(ticket.description or ""),
                raw=ticket.model_dump(mode="json") if hasattr(ticket, "model_dump") else {},
            )
        )
    return tasks


def _first_string(item: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _executor_command(item: dict[str, Any]) -> str | None:
    executor = item.get("executor")
    if not isinstance(executor, dict):
        return None
    handler = executor.get("handler")
    if isinstance(handler, str) and handler.strip():
        return handler.strip()
    return _first_string(executor, ("script", "command", "dsl", "vdisplay"))


def _inputs_command(item: dict[str, Any]) -> str | None:
    inputs = item.get("inputs")
    if not isinstance(inputs, dict):
        return None
    return _first_string(inputs, ("script", "command", "dsl", "vdisplay"))


def _action_command(item: dict[str, Any]) -> str | None:
    action = item.get("action")
    if not isinstance(action, str) or action.strip().lower() not in {"vdisplay", "dsl"}:
        return None
    nested = item.get("args") or item.get("params")
    if isinstance(nested, dict) and nested:
        return json.dumps(nested)
    return None


def _mapping_command(item: dict[str, Any], *, allow_action_only: bool = True) -> str | None:
    command = _first_string(item, ("handler", "command", "script", "vdisplay", "dsl"))
    if command:
        return command
    command = _executor_command(item)
    if command:
        return command
    command = _inputs_command(item)
    if command:
        return command
    if allow_action_only:
        return _action_command(item)
    return None


def _is_skipped_status(status: str) -> bool:
    return status.lower() in {"done", "failed", "skipped", "canceled", "cancelled"}


def _is_valid_planfile_action(source: str, action: str, labels: set[str]) -> bool:
    if not source.startswith("planfile.yaml:planfile.yaml"):
        return True
    if not action:
        return True
    if action in {"vdisplay", "control", "desktop", "automation", "dsl"}:
        return True
    return bool(labels & {"desktop", "automation", "vdisplay"})


def _validate_mapping_task(item: dict[str, Any], source: str) -> str | None:
    """Return the command string if the mapping item is a valid runnable task, else None."""
    command = _mapping_command(item)
    if not command:
        return None
    status = str(item.get("status") or "todo").lower()
    if _is_skipped_status(status):
        return None
    action = str(item.get("action") or "").lower()
    labels = {str(label).lower() for label in (item.get("labels") or []) if label}
    has_command = bool(_mapping_command(item, allow_action_only=False))
    if not has_command:
        return None
    if not _is_valid_planfile_action(source, action, labels):
        return None
    return command


def _task_title(item: dict[str, Any], default_id: str) -> str:
    return str(item.get("title") or item.get("name") or default_id)


def _task_priority(item: dict[str, Any]) -> str:
    return str(item.get("priority") or item.get("priority_label") or "normal")


def _task_monitor(item: dict[str, Any]) -> str | None:
    return str(item.get("monitor") or item.get("source") or "") or None


def _task_map_path(item: dict[str, Any]) -> str | None:
    return str(item.get("map") or item.get("map_path") or "") or None


def _task_verify(item: dict[str, Any]) -> bool:
    verify_raw = item.get("verify")
    return verify_raw in {True, "true", "1", 1, "yes", "on"}


def _task_from_mapping(item: dict[str, Any], *, source: str, default_id: str) -> AutoTask | None:
    command = _validate_mapping_task(item, source)
    if not command:
        return None
    return AutoTask(
        id=str(item.get("id") or default_id),
        title=_task_title(item, default_id),
        command=command,
        source=source,
        priority=_task_priority(item),
        status=str(item.get("status") or "todo").lower(),
        description=str(item.get("description") or ""),
        monitor=_task_monitor(item),
        map_path=_task_map_path(item),
        verify=_task_verify(item),
        raw=dict(item),
    )


def _api_endpoint_command(inputs: dict[str, Any]) -> str | None:
    endpoint = inputs.get("api_endpoint")
    if not endpoint:
        return None
    return f"__api__:{json.dumps({'endpoint': endpoint, 'method': inputs.get('api_method', 'GET'), 'body': inputs.get('api_body'), 'headers': inputs.get('api_headers', {})})}"


def _ticket_command(ticket: Any) -> str | None:
    payload = ticket.model_dump(mode="json") if hasattr(ticket, "model_dump") else {}
    command = _mapping_command(payload)
    if command:
        return command
    executor = payload.get("executor") or {}
    kind = str(executor.get("kind") or "human").lower()
    if kind == "api":
        return _api_endpoint_command(payload.get("inputs") or {})
    if kind in {"human", "llm", "mcp"}:
        return None
    return None


def _update_task_list(items: list[Any], task_id: str, *, status: str, note: str) -> bool:
    for item in items:
        if isinstance(item, dict) and str(item.get("id")) == task_id:
            item["status"] = status
            if note:
                item["last_run_note"] = note[:4000]
            return True
    return False


def write_yaml_task_status(
    path: Path,
    task_id: str,
    *,
    status: str,
    note: str = "",
    options: ConfigOptions | None = None,
) -> None:
    yaml = _yaml()
    opts = options or get_runtime_options(path.parent)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return

    updated = False
    if isinstance(data.get("tasks"), list):
        updated = _update_task_list(data["tasks"], task_id, status=status, note=note)

    for key in opts.planfile_task_keys:
        items = data.get(key)
        if isinstance(items, list) and _update_task_list(items, task_id, status=status, note=note):
            updated = True

    if updated:
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")



def reset_yaml_automation_tasks(path: Path, *, options: ConfigOptions | None = None) -> int:
    """Reset all planfile automation tasks to todo (clears last_run_note)."""
    yaml = _yaml()
    opts = options or get_runtime_options(path.parent)
    if not path.is_file():
        return 0
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return 0
    count = 0
    for key in opts.planfile_task_keys:
        items = data.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            item["status"] = "todo"
            item.pop("last_run_note", None)
            count += 1
    if count:
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return count

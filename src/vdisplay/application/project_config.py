"""Project-level vdisplay.yaml — monitors, windows, actions, automation defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config_options import ConfigOptions
from .env_loader import env_bool, env_str, load_project_env


def _yaml():
    try:
        import yaml
    except ImportError:
        from ..utils import auto_install_package

        auto_install_package("PyYAML>=6.0")
        import yaml
    return yaml


@dataclass
class MonitorSpec:
    name: str
    role: str = ""
    default: bool = False
    notes: str = ""

    @classmethod
    def from_mapping(cls, item: dict[str, Any]) -> MonitorSpec | None:
        name = str(item.get("name") or item.get("monitor") or "").strip()
        if not name:
            return None
        return cls(
            name=name,
            role=str(item.get("role") or ""),
            default=_bool_from_config(item.get("default") or item.get("primary_capture"), False),
            notes=str(item.get("notes") or item.get("nl") or ""),
        )


@dataclass
class WindowSpec:
    app: str = ""
    title_contains: str = ""
    wm_class: str = ""
    preferred_monitor: str = ""
    notes: str = ""

    @classmethod
    def from_mapping(cls, item: dict[str, Any]) -> WindowSpec:
        return cls(
            app=str(item.get("app") or item.get("app_id") or ""),
            title_contains=str(item.get("title_contains") or item.get("title") or ""),
            wm_class=str(item.get("wm_class") or item.get("class") or ""),
            preferred_monitor=str(item.get("preferred_monitor") or item.get("monitor") or ""),
            notes=str(item.get("notes") or ""),
        )


@dataclass
class ActionSpec:
    id: str
    app: str = ""
    monitor: str = ""
    map_path: str = ""
    backend: str = "auto"
    vision_anchor: str = ""
    vision_anchor_rel: str = ""
    verify: bool = False
    observe: bool = False
    command: str = ""
    notes: str = ""

    @classmethod
    def from_mapping(cls, action_id: str, item: dict[str, Any]) -> ActionSpec:
        return cls(
            id=action_id,
            app=_action_field(item, "app", "app_id"),
            monitor=_action_field(item, "monitor", "source"),
            map_path=_action_field(item, "map", "map_path"),
            backend=_action_field(item, "backend", "control_backend", default="auto"),
            vision_anchor=_action_field(item, "vision_anchor", "anchor"),
            vision_anchor_rel=_action_field(item, "vision_anchor_rel", "anchor_rel"),
            verify=bool(item.get("verify")),
            observe=bool(item.get("observe")),
            command=_action_field(item, "command", "handler"),
            notes=_action_field(item, "notes", "description"),
        )


def _action_field(item: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = item.get(key)
        if value:
            return str(value)
    return default


def _bool_from_config(value: Any, default: bool = True) -> bool:
    return value not in {False, "false", "0", 0} if value is not None else default


def _resolve_bool(yaml_value: Any, env_key: str, default: bool) -> bool:
    if yaml_value is not None:
        return _bool_from_config(yaml_value, default)
    env_value = env_bool(env_key)
    if env_value is not None:
        return env_value
    return default


def _resolve_str(yaml_value: Any, env_key: str, default: str) -> str:
    if yaml_value is not None and str(yaml_value).strip():
        return str(yaml_value).strip()
    env_value = env_str(env_key)
    if env_value is not None and env_value.strip():
        return env_value.strip()
    return default


@dataclass
class AutomationDefaults:
    observe: bool = True
    observe_on_screenshot: bool = True
    verify_strict: bool = True
    reject_vision_stubs: bool = True
    session: bool = True
    post_act_verify: bool = True
    metadata_dir: str = ".vdisplay"
    default_monitor: str = "DP-1"
    default_map: str = ""
    planfile: str = "planfile.yaml"

    @classmethod
    def from_mapping(cls, item: dict[str, Any] | None, capture: dict[str, Any] | None) -> AutomationDefaults:
        auto = dict(item or {})
        cap = dict(capture or {})
        observe_yaml = auto.get("observe")
        observe_cap = cap.get("observe_on_screenshot")
        return cls(
            observe=_resolve_bool(observe_yaml, "VDISPLAY_AUTOMATION_OBSERVE", True),
            observe_on_screenshot=_resolve_bool(
                auto.get("observe_on_screenshot", observe_cap),
                "VDISPLAY_AUTOMATION_OBSERVE_ON_SCREENSHOT",
                True,
            ),
            verify_strict=_resolve_bool(auto.get("verify_strict"), "VDISPLAY_AUTOMATION_VERIFY_STRICT", True),
            reject_vision_stubs=_resolve_bool(
                auto.get("reject_vision_stubs"),
                "VDISPLAY_AUTOMATION_REJECT_VISION_STUBS",
                True,
            ),
            session=_resolve_bool(auto.get("session"), "VDISPLAY_AUTOMATION_SESSION", True),
            post_act_verify=_resolve_bool(auto.get("post_act_verify"), "VDISPLAY_AUTOMATION_POST_ACT_VERIFY", True),
            metadata_dir=_resolve_str(auto.get("metadata_dir"), "VDISPLAY_METADATA_DIR", ".vdisplay"),
            default_monitor=_resolve_str(
                auto.get("default_monitor") or cap.get("default_monitor"),
                "VDISPLAY_DEFAULT_MONITOR",
                "DP-1",
            ),
            default_map=_resolve_str(auto.get("default_map") or auto.get("map"), "VDISPLAY_DEFAULT_MAP", ""),
            planfile=_resolve_str(auto.get("planfile"), "VDISPLAY_PLANFILE", "planfile.yaml"),
        )


@dataclass
class ProjectConfig:
    version: str = "1"
    project_name: str = ""
    root: Path = field(default_factory=lambda: Path("."))
    config_path: Path | None = None
    automation: AutomationDefaults = field(default_factory=AutomationDefaults)
    monitors: list[MonitorSpec] = field(default_factory=list)
    windows: list[WindowSpec] = field(default_factory=list)
    actions: dict[str, ActionSpec] = field(default_factory=dict)
    options: ConfigOptions = field(default_factory=ConfigOptions.defaults)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def metadata_dir(self) -> Path:
        path = Path(self.automation.metadata_dir)
        if not path.is_absolute():
            path = self.root / path
        return path

    @property
    def default_monitor(self) -> str:
        for monitor in self.monitors:
            if monitor.default:
                return monitor.name
        if self.automation.default_monitor:
            return self.automation.default_monitor
        if self.monitors:
            return self.monitors[0].name
        return _resolve_str(None, "VDISPLAY_DEFAULT_MONITOR", "DP-1")

    def action(self, action_id: str) -> ActionSpec | None:
        return self.actions.get(action_id)

    def resolve_map_path(self, value: str | None) -> str | None:
        if value:
            path = Path(value)
            if not path.is_absolute():
                path = self.root / path
            return str(path) if path.is_file() else str(self.root / value)
        if self.automation.default_map:
            return self.resolve_map_path(self.automation.default_map)
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "project": {"name": self.project_name},
            "config_path": str(self.config_path) if self.config_path else None,
            "automation": {
                "observe": self.automation.observe,
                "observe_on_screenshot": self.automation.observe_on_screenshot,
                "verify_strict": self.automation.verify_strict,
                "reject_vision_stubs": self.automation.reject_vision_stubs,
                "session": self.automation.session,
                "post_act_verify": self.automation.post_act_verify,
                "metadata_dir": self.automation.metadata_dir,
                "default_monitor": self.automation.default_monitor,
                "default_map": self.automation.default_map,
            },
            "monitors": [
                {"name": m.name, "role": m.role, "default": m.default, "notes": m.notes} for m in self.monitors
            ],
            "windows": [
                {
                    "app": w.app,
                    "title_contains": w.title_contains,
                    "wm_class": w.wm_class,
                    "preferred_monitor": w.preferred_monitor,
                    "notes": w.notes,
                }
                for w in self.windows
            ],
            "actions": {
                key: {
                    "app": spec.app,
                    "monitor": spec.monitor,
                    "map": spec.map_path,
                    "backend": spec.backend,
                    "vision_anchor": spec.vision_anchor,
                    "vision_anchor_rel": spec.vision_anchor_rel,
                    "verify": spec.verify,
                    "observe": spec.observe,
                    "command": spec.command,
                }
                for key, spec in self.actions.items()
            },
            "options": self.options.to_dict(),
        }


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = _yaml().safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def discover_config_paths(project: Path) -> list[Path]:
    root = project.expanduser().resolve()
    paths: list[Path] = []
    env_path = os.environ.get("VDISPLAY_CONFIG", "").strip()
    if env_path:
        paths.append(Path(env_path).expanduser())
    paths.append(root / "vdisplay.yaml")
    override = root / ".vdisplay" / "vdisplay.override.yaml"
    if override.is_file():
        paths.append(override)
    return paths


def _build_specs(merged: dict[str, Any]) -> tuple[list[MonitorSpec], list[WindowSpec], dict[str, ActionSpec]]:
    monitors: list[MonitorSpec] = []
    for item in merged.get("monitors") or []:
        if isinstance(item, dict):
            spec = MonitorSpec.from_mapping(item)
            if spec is not None:
                monitors.append(spec)

    windows: list[WindowSpec] = []
    for item in merged.get("windows") or []:
        if isinstance(item, dict):
            windows.append(WindowSpec.from_mapping(item))

    actions: dict[str, ActionSpec] = {}
    raw_actions = merged.get("actions") or {}
    if isinstance(raw_actions, dict):
        for action_id, item in raw_actions.items():
            if isinstance(item, dict):
                actions[str(action_id)] = ActionSpec.from_mapping(str(action_id), item)

    return monitors, windows, actions


def load_project_config(project: str | Path = ".") -> ProjectConfig:
    root = Path(project).expanduser().resolve()
    load_project_env(root)
    merged: dict[str, Any] = {}
    loaded_path: Path | None = None
    for path in discover_config_paths(root):
        if not path.is_file():
            continue
        if path.is_relative_to(root) or path.parent == root:
            rel = path
        else:
            rel = path
        payload = _load_yaml_file(path)
        if payload:
            merged = _deep_merge(merged, payload)
            loaded_path = rel if path.name == "vdisplay.yaml" else (loaded_path or path)

    if not merged:
        return ProjectConfig(
            root=root,
            config_path=None,
            automation=AutomationDefaults.from_mapping(None, None),
            options=ConfigOptions.from_mapping(None),
        )

    monitors, windows, actions = _build_specs(merged)
    project_block = merged.get("project") or {}
    project_name = ""
    if isinstance(project_block, dict):
        project_name = str(project_block.get("name") or "")

    return ProjectConfig(
        version=str(merged.get("version") or "1"),
        project_name=project_name,
        root=root,
        config_path=loaded_path,
        automation=AutomationDefaults.from_mapping(merged.get("automation"), merged.get("capture")),
        monitors=monitors,
        windows=windows,
        actions=actions,
        options=ConfigOptions.from_mapping(merged.get("options") if isinstance(merged.get("options"), dict) else None),
        raw=merged,
    )


def ensure_metadata_layout(project: Path | str, config: ProjectConfig | None = None) -> Path:
    cfg = config or load_project_config(project)
    base = cfg.metadata_dir
    for sub in cfg.options.metadata_subdirs:
        (base / sub).mkdir(parents=True, exist_ok=True)
    snapshot = base / "config" / "vdisplay.effective.json"
    snapshot.write_text(
        __import__("json").dumps(cfg.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    readme = base / "README.md"
    if not readme.is_file():
        readme.write_text(
            """# vdisplay runtime metadata (gitignored)

Generated by `vdisplay auto` and observe preflight. Do not commit.

| Path | Purpose |
|------|---------|
| `config/vdisplay.effective.json` | merged vdisplay.yaml snapshot |
| `observe/` | task screenshots + post-verify PNGs |
| `context/`, `vql/` | sidecars from observe |
| `runs/{timestamp}/` | per-run manifest, tasks, session |
| `latest-run.txt` | most recent run id |
| `broker.jsonl` | agent broker / screencast lifecycle log |
| `YYYY-MM-DD/` | koru autonomy sessions (observe/decide/act) |

Inspect history: `vdisplay history list`, `vdisplay history analyze --format summary`
Reset runtime artifacts: `vdisplay config clear --project .`
""",
            encoding="utf-8",
        )
    return base


_METADATA_PRESERVE_NAMES = frozenset(
    {
        "vdisplay.override.yaml",
        "vdisplay.override.yml",
        ".gitkeep",
    }
)


def clear_metadata_dir(
    project: Path | str,
    *,
    config: ProjectConfig | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Remove all runtime artifacts under ``.vdisplay/`` (sessions, captures, broker log).

    Preserves user override files (``vdisplay.override.yaml``). Recreates standard layout via
    ``ensure_metadata_layout`` unless ``dry_run=True``.
    """
    import shutil

    cfg = config or load_project_config(project)
    base = cfg.metadata_dir
    removed: list[str] = []
    preserved: list[str] = []
    errors: list[str] = []

    if not base.is_dir():
        if not dry_run:
            ensure_metadata_layout(project, cfg)
        return {
            "ok": True,
            "metadata_dir": str(base),
            "removed": removed,
            "preserved": preserved,
            "recreated_layout": not dry_run,
            "dry_run": dry_run,
        }

    for child in sorted(base.iterdir(), key=lambda p: p.name):
        if child.name in _METADATA_PRESERVE_NAMES:
            preserved.append(child.name)
            continue
        removed.append(child.name)
        if dry_run:
            continue
        try:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        except OSError as exc:
            errors.append(f"{child.name}: {exc}")

    recreated = False
    if not dry_run:
        ensure_metadata_layout(project, cfg)
        recreated = True

    return {
        "ok": not errors,
        "metadata_dir": str(base.resolve()),
        "removed": removed,
        "preserved": preserved,
        "removed_count": len(removed),
        "recreated_layout": recreated,
        "dry_run": dry_run,
        "errors": errors,
    }

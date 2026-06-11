"""User-extensible option catalogs — precedence: vdisplay.yaml > .env > fallbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from .env_loader import env_csv, env_dict_int, env_int, load_project_env

# .env variable names (UPPERCASE)
VDISPLAY_CONTROL_BACKENDS = "VDISPLAY_CONTROL_BACKENDS"
VDISPLAY_CONTROL_ENVIRONMENTS = "VDISPLAY_CONTROL_ENVIRONMENTS"
VDISPLAY_VISION_ANCHOR_RELATIONS = "VDISPLAY_VISION_ANCHOR_RELATIONS"
VDISPLAY_AUTO_SOURCES = "VDISPLAY_AUTO_SOURCES"
VDISPLAY_RUNNABLE_TASK_STATUSES = "VDISPLAY_RUNNABLE_TASK_STATUSES"
VDISPLAY_TASK_PRIORITIES = "VDISPLAY_TASK_PRIORITIES"
VDISPLAY_PLANFILE_TASK_KEYS = "VDISPLAY_PLANFILE_TASK_KEYS"
VDISPLAY_CONTROL_ACTUATION_MARKERS = "VDISPLAY_CONTROL_ACTUATION_MARKERS"
VDISPLAY_VISION_INJECTION_COMMANDS = "VDISPLAY_VISION_INJECTION_COMMANDS"
VDISPLAY_ACTION_MAP_TEMPLATES = "VDISPLAY_ACTION_MAP_TEMPLATES"
VDISPLAY_METADATA_SUBDIRS = "VDISPLAY_METADATA_SUBDIRS"
VDISPLAY_OBSERVE_SIDECAR_SUFFIXES = "VDISPLAY_OBSERVE_SIDECAR_SUFFIXES"
VDISPLAY_IDE_APPS = "VDISPLAY_IDE_APPS"
VDISPLAY_VQL_TARGET_LIMIT = "VDISPLAY_VQL_TARGET_LIMIT"
VDISPLAY_VQL_LAYER_EXPORT_LIMIT = "VDISPLAY_VQL_LAYER_EXPORT_LIMIT"
VDISPLAY_VQL_MAP_TARGET_LIMIT = "VDISPLAY_VQL_MAP_TARGET_LIMIT"
VDISPLAY_VQL_OCR_TEXT_MAX_LEN = "VDISPLAY_VQL_OCR_TEXT_MAX_LEN"
VDISPLAY_VQL_KIND_PRIORITY = "VDISPLAY_VQL_KIND_PRIORITY"
VDISPLAY_CONTROL_LIST_FORMATS = "VDISPLAY_CONTROL_LIST_FORMATS"
VDISPLAY_OBSERVE_OUTPUT_FORMATS = "VDISPLAY_OBSERVE_OUTPUT_FORMATS"
VDISPLAY_SAMPLER_CAPTURE_MODES = "VDISPLAY_SAMPLER_CAPTURE_MODES"
VDISPLAY_SAMPLER_FRAME_FORMATS = "VDISPLAY_SAMPLER_FRAME_FORMATS"
VDISPLAY_DIAGNOSE_MODES = "VDISPLAY_DIAGNOSE_MODES"
VDISPLAY_BROWSER_VENDORS = "VDISPLAY_BROWSER_VENDORS"
VDISPLAY_SESSION_EXPORT_FORMATS = "VDISPLAY_SESSION_EXPORT_FORMATS"
VDISPLAY_CONTROL_RETRY_STRATEGIES = "VDISPLAY_CONTROL_RETRY_STRATEGIES"
VDISPLAY_SCREENSHOT_SOURCES = "VDISPLAY_SCREENSHOT_SOURCES"

_FALLBACK_CONTROL_BACKENDS = ("auto", "atspi", "x11", "browser", "terminal", "vision")
_FALLBACK_CONTROL_ENVIRONMENTS = ("desktop", "browser", "terminal", "vision")
_FALLBACK_VISION_ANCHOR_RELATIONS = ("right_of", "below", "near", "left_of", "above")
_FALLBACK_AUTO_SOURCES = ("auto", "yaml", "tickets")
_FALLBACK_RUNNABLE_TASK_STATUSES = ("todo", "open", "ready", "pending", "")
_FALLBACK_TASK_PRIORITIES: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "normal": 2,
    "medium": 3,
    "low": 4,
}
_FALLBACK_PLANFILE_TASK_KEYS = (
    "automation",
    "automation_tasks",
    "control_tasks",
    "desktop_tasks",
    "tasks",
)
_FALLBACK_CONTROL_ACTUATION_MARKERS = (
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
_FALLBACK_VISION_INJECTION_COMMANDS = (
    "control find",
    "control focus",
    "control click",
    "control set-value",
    "controls_find",
)
_FALLBACK_ACTION_MAP_TEMPLATES = (
    "maps/{app}-chat.json",
    "maps/{id}.json",
    "maps/{id_dash}.json",
)
_FALLBACK_METADATA_SUBDIRS = ("runs", "observe", "vql", "context", "config")
_FALLBACK_OBSERVE_SIDECAR_SUFFIXES = (".context.json", ".vql.json", ".vql.svg")
_FALLBACK_VQL_KIND_PRIORITY: dict[str, int] = {
    "input": 0,
    "button": 1,
    "window": 2,
    "element": 3,
    "ocr": 4,
}
_FALLBACK_IDE_APPS = ("cursor", "jetbrains", "pycharm", "vscode", "idea")
_FALLBACK_CONTROL_LIST_FORMATS = ("flat", "tree")
_FALLBACK_OBSERVE_OUTPUT_FORMATS = ("json", "vql", "summary")
_FALLBACK_SAMPLER_CAPTURE_MODES = ("desktop", "strict", "unattended", "best-effort")
_FALLBACK_SAMPLER_FRAME_FORMATS = ("png", "webp", "jpeg")
_FALLBACK_DIAGNOSE_MODES = ("control", "unattended")
_FALLBACK_BROWSER_VENDORS = ("chromium", "firefox")
_FALLBACK_SESSION_EXPORT_FORMATS = ("readme", "json", "summary")
_FALLBACK_CONTROL_RETRY_STRATEGIES = ("retry_scope", "fallback_backend", "refresh_map")
_FALLBACK_SCREENSHOT_SOURCES = ("host", "mirror", "virtual", "relay")


def _list_from(
    raw: dict[str, Any],
    key: str,
    env_key: str,
    fallback: tuple[str, ...] | list[str],
) -> list[str]:
    value = raw.get(key)
    if isinstance(value, list) and value:
        return [str(item) for item in value]
    env_value = env_csv(env_key)
    if env_value is not None:
        return env_value
    return list(fallback)


def _dict_from(
    raw: dict[str, Any],
    key: str,
    env_key: str,
    fallback: dict[str, int],
) -> dict[str, int]:
    value = raw.get(key)
    if isinstance(value, dict) and value:
        merged = dict(fallback)
        for item_key, item_value in value.items():
            try:
                merged[str(item_key)] = int(item_value)
            except (TypeError, ValueError):
                continue
        return merged
    env_value = env_dict_int(env_key)
    if env_value is not None:
        merged = dict(fallback)
        merged.update(env_value)
        return merged
    return dict(fallback)


def _int_from(raw: dict[str, Any], key: str, env_key: str, fallback: int) -> int:
    value = raw.get(key)
    if value is not None:
        try:
            return int(value)
        except (TypeError, ValueError):
            pass
    env_value = env_int(env_key)
    if env_value is not None:
        return env_value
    return fallback


@dataclass
class VqlOptions:
    target_limit: int = 32
    layer_export_limit: int = 128
    map_target_limit: int = 32
    ocr_text_max_len: int = 48
    kind_priority: dict[str, int] = field(default_factory=lambda: dict(_FALLBACK_VQL_KIND_PRIORITY))

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> VqlOptions:
        block = dict(raw or {})
        return cls(
            target_limit=_int_from(block, "target_limit", VDISPLAY_VQL_TARGET_LIMIT, 32),
            layer_export_limit=_int_from(block, "layer_export_limit", VDISPLAY_VQL_LAYER_EXPORT_LIMIT, 128),
            map_target_limit=_int_from(block, "map_target_limit", VDISPLAY_VQL_MAP_TARGET_LIMIT, 32),
            ocr_text_max_len=_int_from(block, "ocr_text_max_len", VDISPLAY_VQL_OCR_TEXT_MAX_LEN, 48),
            kind_priority=_dict_from(block, "kind_priority", VDISPLAY_VQL_KIND_PRIORITY, _FALLBACK_VQL_KIND_PRIORITY),
        )


@dataclass
class ConfigOptions:
    """Catalogs merged from vdisplay.yaml ``options:`` + ``VDISPLAY_*`` env (user-extensible)."""

    control_backends: list[str] = field(default_factory=lambda: list(_FALLBACK_CONTROL_BACKENDS))
    control_environments: list[str] = field(default_factory=lambda: list(_FALLBACK_CONTROL_ENVIRONMENTS))
    vision_anchor_relations: list[str] = field(default_factory=lambda: list(_FALLBACK_VISION_ANCHOR_RELATIONS))
    auto_sources: list[str] = field(default_factory=lambda: list(_FALLBACK_AUTO_SOURCES))
    runnable_task_statuses: list[str] = field(default_factory=lambda: list(_FALLBACK_RUNNABLE_TASK_STATUSES))
    task_priorities: dict[str, int] = field(default_factory=lambda: dict(_FALLBACK_TASK_PRIORITIES))
    planfile_task_keys: list[str] = field(default_factory=lambda: list(_FALLBACK_PLANFILE_TASK_KEYS))
    control_actuation_markers: list[str] = field(default_factory=lambda: list(_FALLBACK_CONTROL_ACTUATION_MARKERS))
    vision_injection_commands: list[str] = field(default_factory=lambda: list(_FALLBACK_VISION_INJECTION_COMMANDS))
    action_map_templates: list[str] = field(default_factory=lambda: list(_FALLBACK_ACTION_MAP_TEMPLATES))
    metadata_subdirs: list[str] = field(default_factory=lambda: list(_FALLBACK_METADATA_SUBDIRS))
    observe_sidecar_suffixes: list[str] = field(default_factory=lambda: list(_FALLBACK_OBSERVE_SIDECAR_SUFFIXES))
    ide_apps: list[str] = field(default_factory=lambda: list(_FALLBACK_IDE_APPS))
    control_list_formats: list[str] = field(default_factory=lambda: list(_FALLBACK_CONTROL_LIST_FORMATS))
    observe_output_formats: list[str] = field(default_factory=lambda: list(_FALLBACK_OBSERVE_OUTPUT_FORMATS))
    sampler_capture_modes: list[str] = field(default_factory=lambda: list(_FALLBACK_SAMPLER_CAPTURE_MODES))
    sampler_frame_formats: list[str] = field(default_factory=lambda: list(_FALLBACK_SAMPLER_FRAME_FORMATS))
    diagnose_modes: list[str] = field(default_factory=lambda: list(_FALLBACK_DIAGNOSE_MODES))
    browser_vendors: list[str] = field(default_factory=lambda: list(_FALLBACK_BROWSER_VENDORS))
    session_export_formats: list[str] = field(default_factory=lambda: list(_FALLBACK_SESSION_EXPORT_FORMATS))
    control_retry_strategies: list[str] = field(default_factory=lambda: list(_FALLBACK_CONTROL_RETRY_STRATEGIES))
    screenshot_sources: list[str] = field(default_factory=lambda: list(_FALLBACK_SCREENSHOT_SOURCES))
    vql: VqlOptions = field(default_factory=VqlOptions)

    @classmethod
    def defaults(cls) -> ConfigOptions:
        return cls.from_mapping(None)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> ConfigOptions:
        block = dict(raw or {})
        vql_block = block.get("vql")
        vql = VqlOptions.from_mapping(vql_block if isinstance(vql_block, dict) else None)
        return cls(
            control_backends=_list_from(block, "control_backends", VDISPLAY_CONTROL_BACKENDS, _FALLBACK_CONTROL_BACKENDS),
            control_environments=_list_from(
                block, "control_environments", VDISPLAY_CONTROL_ENVIRONMENTS, _FALLBACK_CONTROL_ENVIRONMENTS
            ),
            vision_anchor_relations=_list_from(
                block, "vision_anchor_relations", VDISPLAY_VISION_ANCHOR_RELATIONS, _FALLBACK_VISION_ANCHOR_RELATIONS
            ),
            auto_sources=_list_from(block, "auto_sources", VDISPLAY_AUTO_SOURCES, _FALLBACK_AUTO_SOURCES),
            runnable_task_statuses=_list_from(
                block, "runnable_task_statuses", VDISPLAY_RUNNABLE_TASK_STATUSES, _FALLBACK_RUNNABLE_TASK_STATUSES
            ),
            task_priorities=_dict_from(block, "task_priorities", VDISPLAY_TASK_PRIORITIES, _FALLBACK_TASK_PRIORITIES),
            planfile_task_keys=_list_from(
                block, "planfile_task_keys", VDISPLAY_PLANFILE_TASK_KEYS, _FALLBACK_PLANFILE_TASK_KEYS
            ),
            control_actuation_markers=_list_from(
                block, "control_actuation_markers", VDISPLAY_CONTROL_ACTUATION_MARKERS, _FALLBACK_CONTROL_ACTUATION_MARKERS
            ),
            vision_injection_commands=_list_from(
                block,
                "vision_injection_commands",
                VDISPLAY_VISION_INJECTION_COMMANDS,
                _FALLBACK_VISION_INJECTION_COMMANDS,
            ),
            action_map_templates=_list_from(
                block, "action_map_templates", VDISPLAY_ACTION_MAP_TEMPLATES, _FALLBACK_ACTION_MAP_TEMPLATES
            ),
            metadata_subdirs=_list_from(block, "metadata_subdirs", VDISPLAY_METADATA_SUBDIRS, _FALLBACK_METADATA_SUBDIRS),
            observe_sidecar_suffixes=_list_from(
                block, "observe_sidecar_suffixes", VDISPLAY_OBSERVE_SIDECAR_SUFFIXES, _FALLBACK_OBSERVE_SIDECAR_SUFFIXES
            ),
            ide_apps=_list_from(block, "ide_apps", VDISPLAY_IDE_APPS, _FALLBACK_IDE_APPS),
            control_list_formats=_list_from(
                block, "control_list_formats", VDISPLAY_CONTROL_LIST_FORMATS, _FALLBACK_CONTROL_LIST_FORMATS
            ),
            observe_output_formats=_list_from(
                block, "observe_output_formats", VDISPLAY_OBSERVE_OUTPUT_FORMATS, _FALLBACK_OBSERVE_OUTPUT_FORMATS
            ),
            sampler_capture_modes=_list_from(
                block, "sampler_capture_modes", VDISPLAY_SAMPLER_CAPTURE_MODES, _FALLBACK_SAMPLER_CAPTURE_MODES
            ),
            sampler_frame_formats=_list_from(
                block, "sampler_frame_formats", VDISPLAY_SAMPLER_FRAME_FORMATS, _FALLBACK_SAMPLER_FRAME_FORMATS
            ),
            diagnose_modes=_list_from(block, "diagnose_modes", VDISPLAY_DIAGNOSE_MODES, _FALLBACK_DIAGNOSE_MODES),
            browser_vendors=_list_from(block, "browser_vendors", VDISPLAY_BROWSER_VENDORS, _FALLBACK_BROWSER_VENDORS),
            session_export_formats=_list_from(
                block, "session_export_formats", VDISPLAY_SESSION_EXPORT_FORMATS, _FALLBACK_SESSION_EXPORT_FORMATS
            ),
            control_retry_strategies=_list_from(
                block,
                "control_retry_strategies",
                VDISPLAY_CONTROL_RETRY_STRATEGIES,
                _FALLBACK_CONTROL_RETRY_STRATEGIES,
            ),
            screenshot_sources=_list_from(
                block, "screenshot_sources", VDISPLAY_SCREENSHOT_SOURCES, _FALLBACK_SCREENSHOT_SOURCES
            ),
            vql=vql,
        )

    def runnable_statuses(self) -> frozenset[str]:
        return frozenset(self.runnable_task_statuses)

    def priority_rank(self, label: str) -> int:
        return self.task_priorities.get(str(label).lower(), 99)

    def data_location_paths(self, metadata_dir: Path) -> dict[str, str]:
        locations: dict[str, str] = {"metadata_dir": str(metadata_dir)}
        for name in self.metadata_subdirs:
            locations[name] = str(metadata_dir / name)
        return locations

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_backends": self.control_backends,
            "control_environments": self.control_environments,
            "vision_anchor_relations": self.vision_anchor_relations,
            "auto_sources": self.auto_sources,
            "runnable_task_statuses": self.runnable_task_statuses,
            "task_priorities": self.task_priorities,
            "planfile_task_keys": self.planfile_task_keys,
            "control_actuation_markers": self.control_actuation_markers,
            "vision_injection_commands": self.vision_injection_commands,
            "action_map_templates": self.action_map_templates,
            "metadata_subdirs": self.metadata_subdirs,
            "observe_sidecar_suffixes": self.observe_sidecar_suffixes,
            "ide_apps": self.ide_apps,
            "control_list_formats": self.control_list_formats,
            "observe_output_formats": self.observe_output_formats,
            "sampler_capture_modes": self.sampler_capture_modes,
            "sampler_frame_formats": self.sampler_frame_formats,
            "diagnose_modes": self.diagnose_modes,
            "browser_vendors": self.browser_vendors,
            "session_export_formats": self.session_export_formats,
            "control_retry_strategies": self.control_retry_strategies,
            "screenshot_sources": self.screenshot_sources,
            "vql": {
                "target_limit": self.vql.target_limit,
                "layer_export_limit": self.vql.layer_export_limit,
                "map_target_limit": self.vql.map_target_limit,
                "ocr_text_max_len": self.vql.ocr_text_max_len,
                "kind_priority": self.vql.kind_priority,
            },
        }


@lru_cache(maxsize=4)
def get_runtime_options(project: str | Path = ".") -> ConfigOptions:
    """Load options from project vdisplay.yaml + .env (cached); fall back to env/fallbacks."""
    root = Path(project).expanduser().resolve()
    load_project_env(root)
    try:
        from .project_config import load_project_config

        return load_project_config(root).options
    except Exception:
        return ConfigOptions.from_mapping(None)

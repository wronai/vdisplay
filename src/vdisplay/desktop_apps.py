"""Desktop application registry for launch + IDE control hints."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_XWAYLAND_ENV = {
    "WAYLAND_DISPLAY": "",
    "XDG_SESSION_TYPE": "",
    "DISPLAY": ":0",
    "GDK_BACKEND": "x11",
}


@dataclass(frozen=True)
class LaunchVariant:
    """One way to start an application."""

    variant_id: str
    label: str
    argv: tuple[str, ...]
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DesktopApp:
    """Known desktop/IDE app with launch commands and control hints."""

    app_id: str
    label: str
    variants: tuple[LaunchVariant, ...]
    app_hint: str
    window_title_contains: str
    preferred_backend: str = "auto"
    chat_selectors: tuple[dict[str, str], ...] = ()
    submit_selectors: tuple[dict[str, str], ...] = ()
    map_template: str | None = None
    map_targets: dict[str, str] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["variants"] = [item.to_dict() for item in self.variants]
        return payload

    def default_variant(self) -> LaunchVariant:
        return self.variants[0]

    def variant(self, variant_id: str | None) -> LaunchVariant:
        if not variant_id:
            return self.default_variant()
        normalized = variant_id.strip().lower()
        if normalized == "xwayland":
            for item in self.variants:
                if item.variant_id.endswith("-xwayland"):
                    return item
            raise KeyError(f"no XWayland launch variant for app {self.app_id!r}")
        for item in self.variants:
            if item.variant_id == normalized:
                return item
        raise KeyError(f"unknown launch variant {variant_id!r} for app {self.app_id!r}")


def _desktop_launch(desktop_id: str) -> LaunchVariant | None:
    if shutil.which("gtk-launch"):
        return LaunchVariant("desktop", f"gtk-launch {desktop_id}", ("gtk-launch", desktop_id))
    return None


def _binary_launch(binary: str, *, variant_id: str = "default", label: str | None = None) -> LaunchVariant | None:
    path = shutil.which(binary)
    if not path:
        return None
    return LaunchVariant(variant_id, label or binary, (path,))


def _xwayland_variant(base: LaunchVariant) -> LaunchVariant:
    env = dict(_XWAYLAND_ENV)
    env.update(base.env)
    return LaunchVariant(
        f"{base.variant_id}-xwayland",
        f"{base.label} (XWayland)",
        base.argv,
        env=env,
        cwd=base.cwd,
    )


def _variants_for(
    *,
    binary: str | None = None,
    desktop_id: str | None = None,
    extra_argv: tuple[str, ...] = (),
) -> tuple[LaunchVariant, ...]:
    items: list[LaunchVariant] = []
    if desktop_id:
        desktop = _desktop_launch(desktop_id)
        if desktop is not None:
            if extra_argv:
                items.append(
                    LaunchVariant(
                        desktop.variant_id,
                        desktop.label,
                        desktop.argv + extra_argv,
                        env=desktop.env,
                        cwd=desktop.cwd,
                    )
                )
            else:
                items.append(desktop)
    if binary:
        found = _binary_launch(binary)
        if found is not None:
            argv = found.argv + extra_argv if extra_argv else found.argv
            items.append(LaunchVariant(found.variant_id, found.label, argv))
    deduped: list[LaunchVariant] = []
    seen: set[tuple[str, ...]] = set()
    for item in items:
        key = item.argv
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return tuple(deduped)


_COMMON_CHAT_SELECTORS: tuple[dict[str, str], ...] = (
    {"role": "input", "name_contains": "Chat"},
    {"role": "input", "name_contains": "chat"},
    {"role": "input", "name_contains": "Ask"},
    {"role": "input", "name_contains": "Composer"},
    {"role": "input", "name_contains": "Message"},
    {"role": "input", "name_contains": "Prompt"},
    {"role": "entry", "name_contains": "Chat"},
    {"role": "entry", "name_contains": "chat"},
    {"role": "text", "name_contains": "Chat"},
    {"role": "input"},
    {"role": "entry"},
)

_COMMON_SUBMIT_SELECTORS: tuple[dict[str, str], ...] = (
    {"role": "button", "name_contains": "Send"},
    {"role": "button", "name_contains": "Submit"},
    {"role": "button", "name_contains": "Run"},
)

_CURSOR_CHAT_SELECTORS: tuple[dict[str, str], ...] = _COMMON_CHAT_SELECTORS + (
    {"role": "text", "name_contains": "Ask"},
    {"role": "text", "name_contains": "Composer"},
    {"environment": "vision", "vision_anchor": "Ask", "vision_anchor_rel": "below"},
    {"environment": "vision", "vision_anchor": "Chat", "vision_anchor_rel": "below"},
)

_PYCHARM_CHAT_SELECTORS: tuple[dict[str, str], ...] = (
    {"role": "entry", "name_contains": "Chat"},
    {"role": "entry", "name_contains": "chat"},
    {"role": "entry", "name_contains": "Ask"},
    {"role": "entry", "name_contains": "AI"},
    {"role": "text", "name_contains": "Chat"},
    {"role": "entry"},
    {"environment": "vision", "vision_anchor": "AI", "vision_anchor_rel": "below"},
    {"environment": "vision", "vision_anchor": "Chat", "vision_anchor_rel": "below"},
)

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "maps" / "templates"


def _template_path(name: str) -> str:
    return str(_TEMPLATES_DIR / name)


def _expand_variants(base: tuple[LaunchVariant, ...]) -> tuple[LaunchVariant, ...]:
    expanded = list(base)
    for item in base:
        if "xwayland" not in item.variant_id:
            expanded.append(_xwayland_variant(item))
    return tuple(expanded)


def _build_registry() -> dict[str, DesktopApp]:
    cursor_variants = _variants_for(binary="cursor", desktop_id="cursor.desktop")
    pycharm_variants = _variants_for(
        binary="pycharm-professional",
        desktop_id="jetbrains-pycharm-professional.desktop",
    )
    if not pycharm_variants:
        pycharm_variants = _variants_for(binary="pycharm", desktop_id="jetbrains-pycharm.desktop")

    vscode_variants = _variants_for(binary="code", desktop_id="code.desktop")
    apps: list[DesktopApp] = []

    if cursor_variants:
        apps.append(
            DesktopApp(
                app_id="cursor",
                label="Cursor",
                variants=_expand_variants(cursor_variants),
                app_hint="Cursor",
                window_title_contains="Cursor",
                preferred_backend="vision",
                chat_selectors=_CURSOR_CHAT_SELECTORS,
                submit_selectors=_COMMON_SUBMIT_SELECTORS,
                map_template=_template_path("cursor-chat.manifest.json"),
                map_targets={"chat": "chat-focus", "message": "chat-input", "send": "chat-send"},
                notes="Native Wayland chat is not in AT-SPI; prefer koru plugin or vision+map.",
            )
        )

    if pycharm_variants:
        apps.append(
            DesktopApp(
                app_id="pycharm",
                label="PyCharm",
                variants=_expand_variants(pycharm_variants),
                app_hint="pycharm",
                window_title_contains="PyCharm",
                preferred_backend="vision",
                chat_selectors=_PYCHARM_CHAT_SELECTORS,
                submit_selectors=_COMMON_SUBMIT_SELECTORS,
                map_template=_template_path("pycharm-chat.manifest.json"),
                map_targets={"chat": "ai-chat-panel", "message": "ai-chat-input", "send": "ai-chat-send"},
                notes="Native Wayland: build GUI map once; XWayland variant improves AT-SPI.",
            )
        )

    if vscode_variants:
        apps.append(
            DesktopApp(
                app_id="vscode",
                label="Visual Studio Code",
                variants=_expand_variants(vscode_variants),
                app_hint="code",
                window_title_contains="Visual Studio Code",
                preferred_backend="auto",
                chat_selectors=_COMMON_CHAT_SELECTORS,
                submit_selectors=_COMMON_SUBMIT_SELECTORS,
                map_template=_template_path("vscode-chat.manifest.json"),
                map_targets={"chat": "chat-focus", "message": "chat-input", "send": "chat-send"},
            )
        )

    for binary, app_id, label, title in (
        ("windsurf", "windsurf", "Windsurf", "Windsurf"),
        ("zed", "zed", "Zed", "Zed"),
        ("codium", "vscodium", "VSCodium", "VSCodium"),
    ):
        variants = _variants_for(binary=binary)
        if variants:
            apps.append(
                DesktopApp(
                    app_id=app_id,
                    label=label,
                    variants=_expand_variants(variants),
                    app_hint=binary,
                    window_title_contains=title,
                    chat_selectors=_COMMON_CHAT_SELECTORS,
                    submit_selectors=_COMMON_SUBMIT_SELECTORS,
                )
            )

    return {item.app_id: item for item in apps}


DESKTOP_APPS: dict[str, DesktopApp] = _build_registry()


def list_desktop_apps() -> list[dict[str, Any]]:
    return [app.to_dict() for app in DESKTOP_APPS.values()]


def get_desktop_app(app_id: str) -> DesktopApp:
    normalized = app_id.strip().lower()
    aliases = {
        "pycharm-professional": "pycharm",
        "pycharm-community": "pycharm",
        "jetbrains": "pycharm",
        "visual-studio-code": "vscode",
        "code": "vscode",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in DESKTOP_APPS:
        known = ", ".join(sorted(DESKTOP_APPS))
        raise KeyError(f"unknown app {app_id!r}; known: {known or '(none installed)'}")
    return DESKTOP_APPS[normalized]


def ide_hints_for(app_id: str) -> dict[str, str]:
    app = get_desktop_app(app_id)
    return {
        "app": app.app_hint,
        "window_title_contains": app.window_title_contains,
        "preferred_backend": app.preferred_backend,
    }


def chat_selectors_for(app_id: str) -> tuple[dict[str, str], ...]:
    return get_desktop_app(app_id).chat_selectors or _COMMON_CHAT_SELECTORS


def submit_selectors_for(app_id: str) -> tuple[dict[str, str], ...]:
    return get_desktop_app(app_id).submit_selectors or _COMMON_SUBMIT_SELECTORS


def _is_gui_map_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.name.endswith(".manifest.json"):
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and bool(data.get("regions") or data.get("elements"))


def map_manifest_path(app_id: str) -> str | None:
    app = get_desktop_app(app_id)
    if not app.map_template:
        return None
    template = Path(app.map_template).expanduser()
    return str(template.resolve()) if template.is_file() else None


def _default_map_candidates(app_id: str) -> tuple[Path, ...]:
    app = get_desktop_app(app_id)
    candidates: list[Path] = []
    if app.map_template:
        template = Path(app.map_template).expanduser()
        stem = template.name.replace(".manifest.json", "")
        candidates.append(template.parent / f"{stem}.json")
        if stem.endswith("-chat"):
            candidates.append(template.parent / stem.replace("-chat", ".json"))
    candidates.extend(
        [
            Path("maps") / f"{app_id}-chat.json",
            Path.cwd() / "maps" / f"{app_id}-chat.json",
            Path(__file__).resolve().parents[2] / "maps" / f"{app_id}-chat.json",
        ]
    )
    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(resolved)
    return tuple(deduped)


def resolve_map_path(app_id: str, explicit: str | None = None) -> str | None:
    if explicit:
        path = Path(explicit).expanduser()
        if _is_gui_map_file(path):
            return str(path.resolve())
        return None
    for candidate in _default_map_candidates(app_id):
        if _is_gui_map_file(candidate):
            return str(candidate.resolve())
    return None


def map_input_target_candidates(app_id: str, explicit: str | None = None) -> tuple[str, ...]:
    app = get_desktop_app(app_id)
    ordered: list[str] = []
    for value in (
        explicit,
        app.map_targets.get("message"),
        "message",
        "ask",
        "prompt",
        "chat",
        "composer",
    ):
        if value and value not in ordered:
            ordered.append(value)
    return tuple(ordered)


def map_submit_target_candidates(app_id: str, explicit: str | None = None) -> tuple[str, ...]:
    app = get_desktop_app(app_id)
    ordered: list[str] = []
    for value in (
        explicit,
        app.map_targets.get("send"),
        "send",
        "submit",
        "run",
        "continue",
    ):
        if value and value not in ordered:
            ordered.append(value)
    return tuple(ordered)


def map_target_candidates(app_id: str, explicit: str | None = None) -> tuple[str, ...]:
    """Backward-compatible alias for chat input targets."""
    return map_input_target_candidates(app_id, explicit)


def launch_env_for(variant: LaunchVariant) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in variant.env.items():
        if value == "":
            env.pop(key, None)
        else:
            env[key] = value
    return env


__all__ = [
    "DESKTOP_APPS",
    "DesktopApp",
    "LaunchVariant",
    "chat_selectors_for",
    "get_desktop_app",
    "ide_hints_for",
    "launch_env_for",
    "list_desktop_apps",
    "map_manifest_path",
    "map_input_target_candidates",
    "map_submit_target_candidates",
    "map_target_candidates",
    "resolve_map_path",
    "submit_selectors_for",
]
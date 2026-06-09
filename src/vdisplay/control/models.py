"""Neutral control-plane models (backend-agnostic)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class EnvironmentKind(StrEnum):
    """Target automation environment for provider routing."""

    DESKTOP = "desktop"
    BROWSER = "browser"
    TERMINAL = "terminal"
    VISION = "vision"
    MOBILE = "mobile"


class ControlRole(StrEnum):
    BUTTON = "button"
    INPUT = "input"
    CHECKBOX = "checkbox"
    COMBOBOX = "combobox"
    MENUITEM = "menuitem"
    LABEL = "label"
    PANEL = "panel"
    WINDOW = "window"
    UNKNOWN = "unknown"


class ControlActionKind(StrEnum):
    INVOKE = "invoke"
    FOCUS = "focus"
    SET_VALUE = "set_value"
    PRESS = "press"
    EXPAND = "expand"
    COLLAPSE = "collapse"
    SELECT = "select"
    TOGGLE = "toggle"
    TYPE = "type"
    SUBMIT = "submit"


@dataclass(frozen=True)
class ControlBounds:
    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2


@dataclass(frozen=True)
class ControlAction:
    kind: ControlActionKind
    name: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "name": self.name,
            "description": self.description,
        }


@dataclass(frozen=True)
class ElementCapabilities:
    """Backend-agnostic capability flags for a control element."""

    activate: bool = False
    focus: bool = False
    set_value: bool = False
    text_read: bool = False
    text_write: bool = False
    select: bool = False
    toggle: bool = False
    expand: bool = False

    def to_dict(self) -> dict[str, bool]:
        return {
            "activate": self.activate,
            "focus": self.focus,
            "set_value": self.set_value,
            "text_read": self.text_read,
            "text_write": self.text_write,
            "select": self.select,
            "toggle": self.toggle,
            "expand": self.expand,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> ElementCapabilities:
        if not payload:
            return cls()
        return cls(
            activate=bool(payload.get("activate")),
            focus=bool(payload.get("focus")),
            set_value=bool(payload.get("set_value")),
            text_read=bool(payload.get("text_read")),
            text_write=bool(payload.get("text_write")),
            select=bool(payload.get("select")),
            toggle=bool(payload.get("toggle")),
            expand=bool(payload.get("expand")),
        )


@dataclass
class ControlNode:
    id: str
    backend: str
    role: ControlRole
    name: str | None = None
    description: str | None = None
    bounds: ControlBounds | None = None
    window_id: str | None = None
    app_label: str | None = None
    window_title: str | None = None
    provider_ref: str | None = None
    state: dict[str, Any] = field(default_factory=dict)
    actions: list[ControlAction] = field(default_factory=list)
    capabilities: ElementCapabilities | None = None
    text_value: str | None = None
    parent_id: str | None = None
    children_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "backend": self.backend,
            "role": self.role.value,
            "name": self.name,
            "description": self.description,
            "window_id": self.window_id,
            "app_label": self.app_label,
            "window_title": self.window_title,
            "provider_ref": self.provider_ref,
            "state": self.state,
            "actions": [item.to_dict() for item in self.actions],
            "text_value": self.text_value,
            "parent_id": self.parent_id,
            "children_ids": list(self.children_ids),
        }
        if self.capabilities is not None:
            payload["capabilities"] = self.capabilities.to_dict()
        if self.bounds is not None:
            payload["bounds"] = self.bounds.to_dict()
        return payload


@dataclass
class ControlSnapshot:
    backend: str
    window_id: str | None
    app_label: str | None
    nodes: dict[str, ControlNode]
    root_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "window_id": self.window_id,
            "app_label": self.app_label,
            "root_ids": list(self.root_ids),
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "count": len(self.nodes),
        }


@dataclass
class ActionResult:
    ok: bool
    action: str
    element_id: str
    backend: str
    state_diff: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

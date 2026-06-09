"""Neutral control-plane models (backend-agnostic)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


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
    SELECT = "select"


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
    state: dict[str, Any] = field(default_factory=dict)
    actions: list[ControlAction] = field(default_factory=list)
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
            "state": self.state,
            "actions": [item.to_dict() for item in self.actions],
            "text_value": self.text_value,
            "parent_id": self.parent_id,
            "children_ids": list(self.children_ids),
        }
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

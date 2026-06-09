"""High-level control selectors and matching."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ControlNode, ControlRole


@dataclass(frozen=True)
class ControlSelector:
    role: str | None = None
    name: str | None = None
    name_contains: str | None = None
    app: str | None = None
    window_id: str | None = None
    window_title: str | None = None
    index: int = 0

    @classmethod
    def from_dict(cls, payload: dict) -> ControlSelector:
        return cls(
            role=payload.get("role"),
            name=payload.get("name"),
            name_contains=payload.get("name_contains"),
            app=payload.get("app"),
            window_id=payload.get("window_id"),
            window_title=payload.get("window_title"),
            index=int(payload.get("index") or 0),
        )


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _role_matches(node: ControlNode, role: str | None) -> bool:
    if not role:
        return True
    wanted = _normalize(role)
    return node.role.value == wanted or _normalize(node.role.name) == wanted


def _name_matches(node: ControlNode, *, exact: str | None, contains: str | None) -> bool:
    node_name = _normalize(node.name)
    if exact is not None and node_name != _normalize(exact):
        return False
    if contains is not None and _normalize(contains) not in node_name:
        return False
    return True


def _score(node: ControlNode, selector: ControlSelector) -> int:
    score = 0
    if selector.role and node.role.value == _normalize(selector.role):
        score += 40
    if selector.name and _normalize(node.name) == _normalize(selector.name):
        score += 50
    if selector.name_contains and _normalize(selector.name_contains) in _normalize(node.name or ""):
        score += 20
    if selector.app and _normalize(node.app_label) == _normalize(selector.app):
        score += 10
    if node.bounds is not None and node.bounds.width > 0 and node.bounds.height > 0:
        score += 5
    return score


def find_matches(nodes: dict[str, ControlNode], selector: ControlSelector) -> list[ControlNode]:
    matches: list[ControlNode] = []
    for node in nodes.values():
        if not _role_matches(node, selector.role):
            continue
        if not _name_matches(node, exact=selector.name, contains=selector.name_contains):
            continue
        if selector.app and _normalize(node.app_label) != _normalize(selector.app):
            continue
        if selector.window_id and str(node.window_id) != str(selector.window_id):
            continue
        if selector.window_title and _normalize(selector.window_title) not in _normalize(node.name):
            continue
        matches.append(node)
    matches.sort(key=lambda item: _score(item, selector), reverse=True)
    return matches


def pick_match(nodes: dict[str, ControlNode], selector: ControlSelector) -> ControlNode | None:
    matches = find_matches(nodes, selector)
    if not matches:
        return None
    index = max(0, selector.index)
    if index >= len(matches):
        return None
    return matches[index]


_ROLE_ALIASES = {
    "button": ControlRole.BUTTON,
    "push button": ControlRole.BUTTON,
    "input": ControlRole.INPUT,
    "entry": ControlRole.INPUT,
    "text": ControlRole.INPUT,
    "checkbox": ControlRole.CHECKBOX,
    "check box": ControlRole.CHECKBOX,
    "combobox": ControlRole.COMBOBOX,
    "combo box": ControlRole.COMBOBOX,
    "menuitem": ControlRole.MENUITEM,
    "menu item": ControlRole.MENUITEM,
    "label": ControlRole.LABEL,
    "panel": ControlRole.PANEL,
    "window": ControlRole.WINDOW,
}


def parse_role(value: str | None) -> ControlRole | None:
    if not value:
        return None
    return _ROLE_ALIASES.get(_normalize(value))


_SIMPLE_SELECTOR = re.compile(
    r"^(?P<role>[a-z_]+)(?:\[(?P<attrs>[^\]]+)\])?$",
    re.IGNORECASE,
)
_ATTR = re.compile(r'(?P<key>name|app)(?P<op>=|~)["\'](?P<val>[^"\']+)["\']')


def parse_selector(expr: str) -> ControlSelector:
    text = (expr or "").strip()
    if not text:
        return ControlSelector()
    match = _SIMPLE_SELECTOR.match(text)
    if not match:
        return ControlSelector(name=text)
    role = match.group("role")
    attrs = match.group("attrs") or ""
    selector = ControlSelector(role=role)
    for attr in _ATTR.finditer(attrs):
        key, op, val = attr.group("key"), attr.group("op"), attr.group("val")
        if key == "name" and op == "=":
            selector = ControlSelector(
                role=selector.role,
                name=val,
                app=selector.app,
                index=selector.index,
            )
        elif key == "name" and op == "~":
            selector = ControlSelector(
                role=selector.role,
                name_contains=val,
                app=selector.app,
                index=selector.index,
            )
        elif key == "app":
            selector = ControlSelector(
                role=selector.role,
                name=selector.name,
                name_contains=selector.name_contains,
                app=val,
                index=selector.index,
            )
    return selector

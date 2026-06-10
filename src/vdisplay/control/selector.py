"""High-level control selectors and matching."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from .models import ControlNode, ControlRole


@dataclass(frozen=True)
class ControlSelector:
    """Unified selector for desktop, browser, terminal, and vision backends."""

    role: str | None = None
    name: str | None = None
    name_contains: str | None = None
    app: str | None = None
    window_id: str | None = None
    window_title: str | None = None
    index: int = 0
    backend: str | None = None
    environment: str | None = None
    text: str | None = None
    text_contains: str | None = None
    value: str | None = None
    accessibility_id: str | None = None
    path: str | None = None
    dom_css: str | None = None
    dom_xpath: str | None = None
    terminal_line: int | None = None
    terminal_col: int | None = None
    session_id: str | None = None
    vision_anchor: str | None = None
    vision_template: str | None = None
    vision_anchor_rel: str | None = None
    vision_target: str | None = None
    vision_min_confidence: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict) -> ControlSelector:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        extra = dict(payload.get("extra") or {})
        extra.update({k: v for k, v in payload.items() if k not in known})
        return cls(
            role=payload.get("role"),
            name=payload.get("name"),
            name_contains=payload.get("name_contains"),
            app=payload.get("app"),
            window_id=payload.get("window_id"),
            window_title=payload.get("window_title"),
            index=int(payload.get("index") or 0),
            backend=payload.get("backend"),
            environment=payload.get("environment"),
            text=payload.get("text"),
            text_contains=payload.get("text_contains"),
            value=payload.get("value"),
            accessibility_id=payload.get("accessibility_id"),
            path=payload.get("path"),
            dom_css=payload.get("dom_css"),
            dom_xpath=payload.get("dom_xpath"),
            terminal_line=payload.get("terminal_line"),
            terminal_col=payload.get("terminal_col"),
            session_id=payload.get("session_id"),
            vision_anchor=payload.get("vision_anchor"),
            vision_template=payload.get("vision_template"),
            vision_anchor_rel=payload.get("vision_anchor_rel"),
            vision_target=payload.get("vision_target"),
            vision_min_confidence=(
                float(payload["vision_min_confidence"])
                if payload.get("vision_min_confidence") is not None
                else None
            ),
            extra=extra,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        extra = payload.pop("extra", None) or {}
        result = {key: value for key, value in payload.items() if value is not None and value != ""}
        if extra:
            result["extra"] = extra
        return result

    def active_fields(self) -> set[str]:
        """Return selector dimensions set for the current target environment."""
        fields = {
            key for key, value in self.to_dict().items()
            if key not in {"index", "extra"} and value is not None and value != ""
        }
        if self.index:
            fields.add("index")

        env_match = _infer_selector_environment(self)
        if env_match in _ENV_FIELD_HINTS:
            return fields | {k for k in _ENV_FIELD_HINTS[env_match] if getattr(self, k, None)}

        return fields


_ENV_FIELD_HINTS = {
    "browser": ("dom_css", "dom_xpath", "text", "text_contains", "role", "name"),
    "terminal": ("terminal_line", "terminal_col", "session_id", "text", "text_contains"),
    "vision": (
        "vision_anchor",
        "vision_template",
        "vision_anchor_rel",
        "vision_target",
        "vision_min_confidence",
        "text",
        "text_contains",
    ),
}


def _infer_selector_environment(selector: ControlSelector) -> str | None:
    if selector.environment:
        return selector.environment
    if selector.dom_css or selector.dom_xpath:
        return "browser"
    if selector.terminal_line is not None:
        return "terminal"
    if selector.vision_anchor or selector.vision_template or selector.vision_anchor_rel:
        return "vision"
    return None


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _role_matches(node: ControlNode, role: str | None) -> bool:
    if not role:
        return True
    wanted = _normalize(role)
    return node.role.value == wanted or _normalize(node.role.name) == wanted


def _app_matches(node: ControlNode, app: str | None) -> bool:
    if not app:
        return True
    needle = _normalize(app)
    if needle in _normalize(node.app_label):
        return True
    if needle in _normalize(node.window_title):
        return True
    return False


def _window_title_matches(node: ControlNode, window_title: str | None) -> bool:
    if not window_title:
        return True
    needle = _normalize(window_title)
    if needle in _normalize(node.window_title):
        return True
    if node.role == ControlRole.WINDOW and needle in _normalize(node.name):
        return True
    return False


def _name_matches(node: ControlNode, *, exact: str | None, contains: str | None) -> bool:
    node_name = _normalize(node.name)
    if exact is not None and node_name != _normalize(exact):
        return False
    if contains is not None and _normalize(contains) not in node_name:
        return False
    return True


def _text_matches(node: ControlNode, *, exact: str | None, contains: str | None) -> bool:
    if exact is None and contains is None:
        return True
    text = _normalize(node.text_value or node.name)
    if exact is not None and text != _normalize(exact):
        return False
    if contains is not None and _normalize(contains) not in text:
        return False
    return True


def _terminal_line_matches(node: ControlNode, line: int | None) -> bool:
    if line is None:
        return True
    node_line = node.state.get("terminal_line")
    if node_line is None:
        return False
    return int(node_line) == int(line)


def _terminal_col_matches(node: ControlNode, col: int | None) -> bool:
    if col is None:
        return True
    node_col = node.state.get("terminal_col")
    if node_col is None:
        return True
    return int(node_col) == int(col)


def _score(node: ControlNode, selector: ControlSelector) -> int:
    score = 0
    def _add_if(cond, check_fn, points):
        if cond and check_fn():
            return points
        return 0

    score += _add_if(selector.role, lambda: node.role.value == _normalize(selector.role), 40)
    score += _add_if(selector.name, lambda: _normalize(node.name) == _normalize(selector.name), 50)
    score += _add_if(selector.name_contains, lambda: _normalize(selector.name_contains) in _normalize(node.name or ""), 20)
    score += _add_if(selector.app, lambda: _app_matches(node, selector.app), 10)
    score += _add_if(selector.window_title, lambda: _window_title_matches(node, selector.window_title), 15)
    score += _add_if(selector.text, lambda: _normalize(node.text_value or node.name) == _normalize(selector.text), 25)
    score += _add_if(selector.terminal_line, lambda: node.state.get("terminal_line") == selector.terminal_line, 35)
    score += _add_if(selector.terminal_col, lambda: node.state.get("terminal_col") == selector.terminal_col, 20)
    score += _add_if(selector.accessibility_id, lambda: selector.accessibility_id == node.provider_ref, 60)

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
        if not _text_matches(node, exact=selector.text, contains=selector.text_contains):
            continue
        if selector.accessibility_id and selector.accessibility_id != node.provider_ref:
            continue
        if not _app_matches(node, selector.app):
            continue
        if selector.window_id and str(node.window_id) != str(selector.window_id):
            continue
        if not _window_title_matches(node, selector.window_title):
            continue
        if not _terminal_line_matches(node, selector.terminal_line):
            continue
        if not _terminal_col_matches(node, selector.terminal_col):
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
    "link": ControlRole.UNKNOWN,
    "tab": ControlRole.UNKNOWN,
}


def parse_role(value: str | None) -> ControlRole | None:
    if not value:
        return None
    return _ROLE_ALIASES.get(_normalize(value))


_ROLE_PREFIX = re.compile(r"^([a-z_]+)", re.IGNORECASE)
_BRACKET_ATTRS = re.compile(r"\[([^\]]+)\]")
_ATTR = re.compile(
    r'(?P<key>name|app|window_title|text|css|xpath|id|line|col)(?P<op>=|~)?["\'](?P<val>[^"\']+)["\']'
)
_LINE_PREFIX = re.compile(r"^line\[(\d+)\]", re.IGNORECASE)


def _apply_attr(selector: ControlSelector, key: str, op: str | None, val: str) -> ControlSelector:
    kwargs = {}
    if key == "name":
        kwargs["name" if op == "=" else "name_contains"] = val
    elif key == "text":
        kwargs["text" if op == "=" else "text_contains"] = val
    elif key == "app":
        kwargs["app"] = val
    elif key == "window_title":
        kwargs["window_title"] = val
    elif key == "css":
        kwargs["dom_css"] = val
        kwargs["environment"] = "browser"
    elif key == "xpath":
        kwargs["dom_xpath"] = val
        kwargs["environment"] = "browser"
    elif key == "id":
        kwargs["accessibility_id"] = val
    elif key == "line":
        kwargs["terminal_line"] = int(val)
        kwargs["environment"] = "terminal"
    elif key == "col":
        kwargs["terminal_col"] = int(val)
        kwargs["environment"] = "terminal"

    return replace(selector, **kwargs) if kwargs else selector


def parse_selector(expr: str) -> ControlSelector:
    text = (expr or "").strip()
    if not text:
        return ControlSelector()
    if text.startswith("#") or text.startswith("."):
        return ControlSelector(dom_css=text, environment="browser")
    if text.startswith("//") or text.startswith("(/"):
        return ControlSelector(dom_xpath=text, environment="browser")
        
    line_match = _LINE_PREFIX.match(text)
    role_match = _ROLE_PREFIX.match(text)
    
    rest = text
    if line_match:
        selector = ControlSelector(terminal_line=int(line_match.group(1)), environment="terminal")
        rest = text[line_match.end() :]
    elif not role_match or "[" not in text:
        if role_match and role_match.group(0) == text:
            return ControlSelector(role=role_match.group(0))
        return ControlSelector(name=text)
    else:
        selector = ControlSelector(role=role_match.group(0))
        
    for bracket in _BRACKET_ATTRS.finditer(rest):
        for attr in _ATTR.finditer(bracket.group(1)):
            selector = _apply_attr(selector, attr.group("key"), attr.group("op"), attr.group("val"))
    return selector

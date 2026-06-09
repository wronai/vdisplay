"""Terminal/TUI control provider (PTY + screen buffer)."""

from __future__ import annotations

from typing import Any

from ..base import ControlProvider
from ..models import ControlBounds, ControlNode, ControlSnapshot
from ..selector import ControlSelector, find_matches
from .terminal_screen import nodes_from_screen
from .terminal_session import TerminalSessionRegistry, default_registry


def _terminal_deps_available() -> tuple[bool, str]:
    return True, "terminal provider available (pyte/pexpect optional)"


def _parse_ref(element_id: str) -> tuple[str | None, str | None]:
    if element_id.startswith("terminal:"):
        parts = element_id.split(":")
        if len(parts) >= 4 and parts[2] == "line":
            return parts[1], "line"
        if len(parts) >= 3 and parts[2] == "cursor":
            return parts[1], "cursor"
        if len(parts) >= 3 and parts[2] == "screen":
            return parts[1], "screen"
    return None, None


class TerminalControlProvider(ControlProvider):
    name = "terminal"

    def __init__(
        self,
        *,
        session_id: str | None = None,
        registry: TerminalSessionRegistry | None = None,
    ) -> None:
        self._session_id = session_id
        self._registry = registry or default_registry()
        self._cache: ControlSnapshot | None = None

    def available(self) -> tuple[bool, str]:
        return _terminal_deps_available()

    def _resolve_session_id(self, *, app: str | None = None, window_id: str | None = None) -> str:
        if self._session_id:
            return self._session_id
        if window_id:
            return window_id
        if app:
            return app
        sessions = self._registry.list_ids()
        if not sessions:
            raise RuntimeError("no terminal session open; use --session-id or open a PTY session first")
        return sessions[-1]

    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        del max_depth
        session_id = self._resolve_session_id(app=app, window_id=window_id)
        session = self._registry.require(session_id)
        screen = session.screen.snapshot()
        snapshot = nodes_from_screen(screen, session_id=session_id, backend=self.name)
        self._cache = snapshot
        return snapshot

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        snapshot = self._cache
        if snapshot is None:
            snapshot = self.snapshot(app=selector.app, window_id=selector.window_id)
        matches = find_matches(snapshot.nodes, selector)
        if matches:
            return matches
        if selector.terminal_line is not None or selector.environment == "terminal":
            return _find_terminal_nodes(snapshot.nodes, selector)
        return []

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        del action
        session_id, kind = _parse_ref(element_id)
        if session_id is None:
            raise ValueError(f"unknown terminal element: {element_id}")
        session = self._registry.require(session_id)
        session.send_enter()
        self._cache = None
        return {"ok": True, "element_id": element_id, "action": "invoke", "sent": "enter"}

    def focus(self, element_id: str) -> dict[str, Any]:
        session_id, kind = _parse_ref(element_id)
        if session_id is None:
            raise ValueError(f"unknown terminal element: {element_id}")
        if kind == "cursor":
            return {"ok": True, "element_id": element_id, "action": "focus"}
        if kind == "line":
            parts = element_id.split(":")
            line_no = int(parts[-1])
            session = self._registry.require(session_id)
            session.screen.cursor_row = max(0, line_no - 1)
            session.screen.cursor_col = 0
            self._cache = None
            return {"ok": True, "element_id": element_id, "action": "focus", "cursor_row": line_no}
        return {"ok": True, "element_id": element_id, "action": "focus"}

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        session_id, _kind = _parse_ref(element_id)
        if session_id is None:
            raise ValueError(f"unknown terminal element: {element_id}")
        session = self._registry.require(session_id)
        session.write(value)
        self._cache = None
        return {"ok": True, "element_id": element_id, "action": "set_value", "value": value}

    def bounds(self, element_id: str) -> ControlBounds | None:
        snapshot = self._cache or self.snapshot()
        node = snapshot.nodes.get(element_id)
        return node.bounds if node else None


def _matches_terminal_node(node: ControlNode, selector: ControlSelector) -> bool:
    line_no = node.state.get("terminal_line")
    if selector.terminal_line is not None and line_no != selector.terminal_line:
        return False
    if selector.terminal_col is not None:
        col = node.state.get("terminal_col")
        if col is not None and col != selector.terminal_col:
            return False
    if selector.text and (node.text_value or "").strip() != selector.text.strip():
        return False
    if selector.text_contains and selector.text_contains not in (node.text_value or ""):
        return False
    if selector.role and node.role.value != selector.role:
        return False
    return True

def _find_terminal_nodes(nodes: dict[str, ControlNode], selector: ControlSelector) -> list[ControlNode]:
    return [node for node in nodes.values() if _matches_terminal_node(node, selector)]

"""Terminal screen buffer model and node projection."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..models import (
    ControlAction,
    ControlActionKind,
    ControlNode,
    ControlRole,
    ControlSnapshot,
    ElementCapabilities,
)

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\].*?(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")

_LINE_CAPABILITIES = ElementCapabilities(
    text_read=True,
    focus=True,
    activate=True,
)
_CURSOR_CAPABILITIES = ElementCapabilities(
    text_read=True,
    text_write=True,
    focus=True,
    set_value=True,
)


@dataclass
class ScreenLine:
    """One terminal row (1-based line number)."""

    number: int
    text: str
    cursor_col: int | None = None

    def stripped(self) -> str:
        return self.text.rstrip()


@dataclass
class ScreenSnapshot:
    """Parsed terminal screen state."""

    rows: int
    cols: int
    cursor_row: int
    cursor_col: int
    lines: list[ScreenLine] = field(default_factory=list)
    title: str | None = None

    def line_at(self, number: int) -> ScreenLine | None:
        for line in self.lines:
            if line.number == number:
                return line
        return None


class ScreenBuffer:
    """Mutable terminal screen fed by PTY output bytes."""

    def __init__(self, *, rows: int = 24, cols: int = 80, title: str | None = None) -> None:
        self.rows = max(1, rows)
        self.cols = max(1, cols)
        self.title = title
        self._grid: list[list[str]] = [[" "] * self.cols for _ in range(self.rows)]
        self.cursor_row = 0
        self.cursor_col = 0
        self._pyte_screen: Any | None = None
        self._pyte_stream: Any | None = None
        self._init_pyte()

    def _init_pyte(self) -> None:
        try:
            import pyte

            self._pyte_screen = pyte.Screen(self.cols, self.rows)
            self._pyte_stream = pyte.Stream(self._pyte_screen)
        except ImportError:
            self._pyte_screen = None
            self._pyte_stream = None

    def resize(self, *, rows: int | None = None, cols: int | None = None) -> None:
        if rows is not None:
            self.rows = max(1, rows)
        if cols is not None:
            self.cols = max(1, cols)
        if self._pyte_screen is not None:
            self._pyte_screen.resize(self.rows, self.cols)
        else:
            self._grid = [[" "] * self.cols for _ in range(self.rows)]
            self.cursor_row = min(self.cursor_row, self.rows - 1)
            self.cursor_col = min(self.cursor_col, self.cols - 1)

    def feed(self, data: str | bytes) -> None:
        if isinstance(data, bytes):
            text = data.decode("utf-8", errors="replace")
        else:
            text = data
        if not text:
            return
        if self._pyte_stream is not None and self._pyte_screen is not None:
            self._pyte_stream.feed(text)
            self.cursor_row = min(self._pyte_screen.cursor.y, self.rows - 1)
            self.cursor_col = min(self._pyte_screen.cursor.x, self.cols - 1)
            self._sync_from_pyte()
            return
        self._feed_simple(text)

    def _sync_from_pyte(self) -> None:
        if self._pyte_screen is None:
            return
        display = self._pyte_screen.display
        self._grid = []
        for row in range(self.rows):
            line = display[row] if row < len(display) else ""
            padded = (line + " " * self.cols)[: self.cols]
            self._grid.append(list(padded))

    def _feed_simple(self, text: str) -> None:
        cleaned = _ANSI_ESCAPE.sub("", text)
        for chunk in cleaned.split("\n"):
            if "\r" in chunk:
                chunk = chunk.split("\r")[-1]
            row = self._grid[self.cursor_row]
            for char in chunk:
                if self.cursor_col >= self.cols:
                    break
                row[self.cursor_col] = char
                self.cursor_col += 1
            if text.endswith("\n") or "\n" in cleaned:
                self.cursor_row = min(self.cursor_row + 1, self.rows - 1)
                self.cursor_col = 0

    def set_lines(self, lines: list[str], *, cursor_row: int = 0, cursor_col: int = 0) -> None:
        """Seed buffer directly (tests and mock sessions)."""
        self._grid = [[" "] * self.cols for _ in range(self.rows)]
        for index, line in enumerate(lines[: self.rows]):
            padded = (line + " " * self.cols)[: self.cols]
            self._grid[index] = list(padded)
        self.cursor_row = min(max(0, cursor_row), self.rows - 1)
        self.cursor_col = min(max(0, cursor_col), self.cols - 1)

    def snapshot(self) -> ScreenSnapshot:
        lines: list[ScreenLine] = []
        for index in range(self.rows):
            text = "".join(self._grid[index]).rstrip()
            line_no = index + 1
            cursor_col = self.cursor_col if index == self.cursor_row else None
            if text or cursor_col is not None:
                lines.append(ScreenLine(number=line_no, text=text, cursor_col=cursor_col))
        return ScreenSnapshot(
            rows=self.rows,
            cols=self.cols,
            cursor_row=self.cursor_row + 1,
            cursor_col=self.cursor_col,
            lines=lines,
            title=self.title,
        )


def _line_node_id(session_id: str, line_no: int) -> str:
    return f"terminal:{session_id}:line:{line_no}"


def _cursor_node_id(session_id: str) -> str:
    return f"terminal:{session_id}:cursor"


def nodes_from_screen(
    screen: ScreenSnapshot,
    *,
    session_id: str,
    backend: str = "terminal",
) -> ControlSnapshot:
    nodes: dict[str, ControlNode] = {}
    root_ids: list[str] = []

    screen_root_id = f"terminal:{session_id}:screen"
    nodes[screen_root_id] = ControlNode(
        id=screen_root_id,
        backend=backend,
        role=ControlRole.PANEL,
        name=screen.title or f"terminal:{session_id}",
        app_label=session_id,
        window_title=screen.title,
        provider_ref=f"terminal:screen:{session_id}",
        state={
            "terminal_rows": screen.rows,
            "terminal_cols": screen.cols,
            "cursor_row": screen.cursor_row,
            "cursor_col": screen.cursor_col,
        },
        capabilities=ElementCapabilities(text_read=True),
        children_ids=[],
    )
    root_ids.append(screen_root_id)

    for line in screen.lines:
        node_id = _line_node_id(session_id, line.number)
        nodes[node_id] = ControlNode(
            id=node_id,
            backend=backend,
            role=ControlRole.LABEL,
            name=f"line {line.number}",
            text_value=line.text,
            app_label=session_id,
            provider_ref=f"terminal:{session_id}:line:{line.number}",
            parent_id=screen_root_id,
            state={
                "terminal_line": line.number,
                "terminal_col": line.cursor_col,
            },
            capabilities=_LINE_CAPABILITIES,
            actions=[ControlAction(kind=ControlActionKind.INVOKE, name="enter")],
            bounds=None,
        )
        nodes[screen_root_id].children_ids.append(node_id)

    cursor_id = _cursor_node_id(session_id)
    cursor_line = screen.line_at(screen.cursor_row) or ScreenLine(screen.cursor_row, "")
    nodes[cursor_id] = ControlNode(
        id=cursor_id,
        backend=backend,
        role=ControlRole.INPUT,
        name="cursor",
        text_value=cursor_line.text,
        app_label=session_id,
        provider_ref=f"terminal:{session_id}:cursor",
        parent_id=screen_root_id,
        state={
            "terminal_line": screen.cursor_row,
            "terminal_col": screen.cursor_col,
        },
        capabilities=_CURSOR_CAPABILITIES,
        actions=[
            ControlAction(kind=ControlActionKind.FOCUS, name="focus"),
            ControlAction(kind=ControlActionKind.SET_VALUE, name="type"),
            ControlAction(kind=ControlActionKind.PRESS, name="enter"),
        ],
        bounds=None,
    )
    nodes[screen_root_id].children_ids.append(cursor_id)

    return ControlSnapshot(
        backend=backend,
        window_id=session_id,
        app_label=session_id,
        nodes=nodes,
        root_ids=root_ids,
    )


def new_session_id() -> str:
    return f"pty-{uuid.uuid4().hex[:8]}"

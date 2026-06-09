"""PTY session registry for terminal control provider."""

from __future__ import annotations

import shlex
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Any

from .terminal_screen import ScreenBuffer, new_session_id


@dataclass
class TerminalSession:
    """One controllable terminal session."""

    session_id: str
    screen: ScreenBuffer
    command: str | None = None
    title: str | None = None
    _process: subprocess.Popen[bytes] | None = field(default=None, repr=False)
    _sent: list[str] = field(default_factory=list)
    _reader: threading.Thread | None = field(default=None, repr=False)
    _alive: bool = True

    def write(self, text: str) -> None:
        self._sent.append(text)
        if self._process is not None and self._process.stdin is not None:
            payload = text.encode("utf-8", errors="replace")
            self._process.stdin.write(payload)
            self._process.stdin.flush()
            return
        if text and text not in {"\r", "\n"}:
            row = self.screen.cursor_row
            col = self.screen.cursor_col
            line = "".join(self.screen._grid[row]).rstrip()  # noqa: SLF001
            padded = (line + " " * self.screen.cols)[: self.screen.cols]
            chars = list(padded)
            for char in text:
                if col >= self.screen.cols:
                    break
                chars[col] = char
                col += 1
            self.screen._grid[row] = chars  # noqa: SLF001
            self.screen.cursor_col = col

    def send_enter(self) -> None:
        self.write("\r")

    def sent_text(self) -> list[str]:
        return list(self._sent)

    def stop(self) -> None:
        self.close()

    def close(self) -> None:
        self._alive = False
        if self._process is not None:
            if self._process.stdin is not None:
                try:
                    self._process.stdin.close()
                except OSError:
                    pass
            try:
                self._process.terminate()
            except OSError:
                pass
            self._process = None

    def _start_reader(self) -> None:
        if self._process is None or self._process.stdout is None:
            return

        def _loop() -> None:
            stdout = self._process.stdout
            assert stdout is not None
            while self._alive:
                try:
                    chunk = stdout.read(4096)
                except (OSError, ValueError):
                    break
                if not chunk:
                    break
                self.screen.feed(chunk)

        self._reader = threading.Thread(target=_loop, name=f"terminal-{self.session_id}", daemon=True)
        self._reader.start()


class TerminalSessionRegistry:
    """In-memory registry of open terminal sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, TerminalSession] = {}

    def list_ids(self) -> list[str]:
        return sorted(self._sessions)

    def get(self, session_id: str) -> TerminalSession | None:
        return self._sessions.get(session_id)

    def require(self, session_id: str) -> TerminalSession:
        session = self.get(session_id)
        if session is None:
            raise KeyError(f"unknown terminal session: {session_id}")
        return session

    def open_mock(
        self,
        *,
        session_id: str | None = None,
        lines: list[str] | None = None,
        rows: int = 24,
        cols: int = 80,
        title: str | None = None,
        cursor_row: int = 0,
        cursor_col: int = 0,
    ) -> TerminalSession:
        sid = session_id or new_session_id()
        screen = ScreenBuffer(rows=rows, cols=cols, title=title or sid)
        if lines:
            screen.set_lines(lines, cursor_row=cursor_row, cursor_col=cursor_col)
        session = TerminalSession(session_id=sid, screen=screen, title=title or sid)
        self._sessions[sid] = session
        return session

    def open_process(
        self,
        command: str,
        *,
        session_id: str | None = None,
        rows: int = 24,
        cols: int = 80,
        title: str | None = None,
        env: dict[str, str] | None = None,
    ) -> TerminalSession:
        sid = session_id or new_session_id()
        screen = ScreenBuffer(rows=rows, cols=cols, title=title or command)
        session = TerminalSession(
            session_id=sid,
            screen=screen,
            command=command,
            title=title or command,
        )
        argv = shlex.split(command)
        session._process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )
        session._start_reader()
        self._sessions[sid] = session
        return session

    def open_pexpect(
        self,
        command: str,
        *,
        session_id: str | None = None,
        rows: int = 24,
        cols: int = 80,
        title: str | None = None,
    ) -> TerminalSession:
        try:
            import pexpect
        except ImportError:
            from ...utils import auto_install_package
            auto_install_package("pexpect")
            import pexpect

        sid = session_id or new_session_id()
        screen = ScreenBuffer(rows=rows, cols=cols, title=title or command)
        child = pexpect.spawn(command, encoding=None, dimensions=(rows, cols))
        session = TerminalSession(
            session_id=sid,
            screen=screen,
            command=command,
            title=title or command,
        )
        session._process = None  # pexpect owns the fd

        def _write(text: str) -> None:
            session._sent.append(text)
            child.send(text.encode("utf-8", errors="replace"))

        def _send_enter() -> None:
            _write("\r")

        session.write = _write  # type: ignore[method-assign]
        session.send_enter = _send_enter  # type: ignore[method-assign]

        def _loop() -> None:
            while session._alive:
                try:
                    chunk = child.read_nonblocking(size=4096, timeout=0.2)
                except (pexpect.TIMEOUT, pexpect.EOF):
                    if not child.isalive():
                        break
                    continue
                except OSError:
                    break
                if chunk:
                    screen.feed(chunk)

        session._reader = threading.Thread(target=_loop, name=f"terminal-{sid}", daemon=True)
        session._reader.start()
        self._sessions[sid] = session
        return session

    def close(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is not None:
            session.close()

    def close_all(self) -> None:
        for sid in list(self._sessions):
            self.close(sid)


_DEFAULT_REGISTRY = TerminalSessionRegistry()


def default_registry() -> TerminalSessionRegistry:
    return _DEFAULT_REGISTRY

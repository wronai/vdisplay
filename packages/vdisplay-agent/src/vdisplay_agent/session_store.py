"""Broker session registry (virtual, mirror, relay)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from vdisplay import WindowRelaySession
from vdisplay.exceptions import VDisplayError

from .services.browser_bridge import BrowserFrameStore


@dataclass
class SessionRecord:
    session_id: str
    kind: str
    handle: Any
    started: bool = True


@dataclass
class SessionStore:
    sessions: dict[str, SessionRecord] = field(default_factory=dict)
    relay: WindowRelaySession | None = None
    screencast: Any | None = None
    screencast_multiple: bool = False
    virtual: Any | None = None
    virtual_key: tuple[str, int, int] | None = None
    sampler: Any | None = None
    sampler_task_id: str | None = None
    screencast_task_id: str | None = None
    screencast_capture_failed: bool = False
    screencast_capture_error: str = ""
    browser_bridge: BrowserFrameStore = field(default_factory=BrowserFrameStore)

    def register(self, *, kind: str, handle: Any, prefix: str) -> SessionRecord:
        session_id = f"{prefix}-{uuid.uuid4().hex[:12]}"
        record = SessionRecord(session_id=session_id, kind=kind, handle=handle)
        self.sessions[session_id] = record
        return record

    def get(self, session_id: str) -> SessionRecord:
        record = self.sessions.get(session_id)
        if record is None:
            raise VDisplayError(f"unknown session_id: {session_id}")
        return record

    def pop(self, session_id: str) -> SessionRecord:
        record = self.sessions.pop(session_id, None)
        if record is None:
            raise VDisplayError(f"unknown session_id: {session_id}")
        return record

    def relay_session(self, session_id: str | None) -> WindowRelaySession:
        if session_id:
            record = self.sessions.get(str(session_id))
            if record is None or record.kind != "relay":
                raise VDisplayError(f"relay session not found: {session_id}")
            return record.handle
        if self.relay is None:
            self.relay = WindowRelaySession.create()
            self.relay.start()
        return self.relay

    def clear_relay(self) -> None:
        if self.relay is not None:
            self.relay.stop()
            self.relay = None

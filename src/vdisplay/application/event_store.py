"""Append-only event log for audit sessions."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .events import DomainEvent
from .session_recorder import session_recording_enabled


def event_store_enabled() -> bool:
    flag = os.environ.get("VDISPLAY_EVENT_STORE", "").strip().lower()
    if flag in {"0", "false", "no"}:
        return False
    if flag in {"1", "true", "yes"}:
        return True
    return session_recording_enabled()


def resolve_event_session_root(cmd) -> Path | None:
    if not event_store_enabled():
        return None
    explicit = os.environ.get("VDISPLAY_SESSION_DIR", "").strip()
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path
    if session_recording_enabled():
        from .session_recorder import resolve_session_root

        return resolve_session_root(cmd)
    return None


class EventStore:
    def __init__(self, session_root: Path) -> None:
        self.session_root = session_root
        self.index_path = session_root / "index.jsonl"

    def append(self, event: DomainEvent) -> None:
        self.session_root.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event.to_dict(), ensure_ascii=False)
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        self._maybe_append_protobuf(event)
        self._maybe_refresh_projections()

    def append_many(self, events: list[DomainEvent]) -> None:
        if not events:
            return
        self.session_root.mkdir(parents=True, exist_ok=True)
        with self.index_path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        if events:
            self._maybe_append_protobuf_many(events)
        self._maybe_refresh_projections()

    def _maybe_append_protobuf(self, event: DomainEvent) -> None:
        from .proto.codec import DomainEventEnvelope, encode_event_envelope, protobuf_events_enabled

        if not protobuf_events_enabled():
            return
        path = self.session_root / "index.pb"
        envelope = DomainEventEnvelope.from_domain_event(event)
        with path.open("ab") as handle:
            handle.write(encode_event_envelope(envelope))

    def _maybe_append_protobuf_many(self, events: list[DomainEvent]) -> None:
        from .proto.codec import DomainEventEnvelope, encode_event_envelope, protobuf_events_enabled

        if not protobuf_events_enabled():
            return
        path = self.session_root / "index.pb"
        with path.open("ab") as handle:
            for event in events:
                envelope = DomainEventEnvelope.from_domain_event(event)
                handle.write(encode_event_envelope(envelope))

    def read_all(self) -> list[DomainEvent]:
        if not self.index_path.is_file():
            return []
        events: list[DomainEvent] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            events.append(DomainEvent.from_dict(json.loads(stripped)))
        return events

    def _maybe_refresh_projections(self) -> None:
        from .env_defaults import env_flag

        if not env_flag("VDISPLAY_PROJECTIONS", default=True):
            return
        try:
            from .projections import refresh_projections

            refresh_projections(self.session_root)
        except Exception:
            return


def append_event(session_root: Path, event: DomainEvent) -> None:
    EventStore(session_root).append(event)


def append_events(session_root: Path, events: list[DomainEvent]) -> None:
    EventStore(session_root).append_many(events)


def read_events(session_root: Path) -> list[DomainEvent]:
    return EventStore(session_root).read_all()

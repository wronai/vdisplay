"""v1 envelope encode/decode — JSON transition payloads with optional binary index."""

from __future__ import annotations

import base64
import json
import os
import struct
from dataclasses import asdict, dataclass, field
from typing import Any

MAGIC = b"VDEV"
SCHEMA_VERSION = "2026-06"
EVENT_VERSION = 1


@dataclass
class TraceContext:
    session_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    request_source: str | None = None
    created_at_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.session_id:
            payload["session_id"] = self.session_id
        if self.request_id:
            payload["request_id"] = self.request_id
        if self.correlation_id:
            payload["correlation_id"] = self.correlation_id
        if self.request_source:
            payload["request_source"] = self.request_source
        if self.created_at_ms is not None:
            payload["created_at_ms"] = self.created_at_ms
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> TraceContext:
        data = payload or {}
        return cls(
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            correlation_id=data.get("correlation_id"),
            request_source=data.get("request_source"),
            created_at_ms=data.get("created_at_ms"),
        )


@dataclass
class Artifact:
    kind: str
    path: str
    label: str = ""
    role: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Artifact:
        return cls(
            kind=str(payload.get("kind") or ""),
            path=str(payload.get("path") or ""),
            label=str(payload.get("label") or ""),
            role=str(payload.get("role") or ""),
        )


@dataclass
class DomainEventEnvelope:
    event_id: str
    event_type: str
    occurred_at_ms: int
    trace: TraceContext = field(default_factory=TraceContext)
    aggregate_type: str | None = None
    aggregate_id: str | None = None
    event_version: int = EVENT_VERSION
    body: dict[str, Any] = field(default_factory=dict)
    artifacts: list[Artifact] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at_ms": self.occurred_at_ms,
            "session_id": self.trace.session_id,
            "request_id": self.trace.request_id,
            "aggregate": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_version": self.event_version,
            "trace": self.trace.to_dict(),
            "body": self.body,
            "artifacts": [item.to_dict() for item in self.artifacts],
        }

    @classmethod
    def from_domain_event(cls, event: Any) -> DomainEventEnvelope:
        return cls(
            event_id=str(event.event_id),
            event_type=str(event.event_type),
            occurred_at_ms=int(event.occurred_at_ms),
            trace=TraceContext(
                session_id=event.session_id,
                request_id=event.request_id,
            ),
            aggregate_type=event.aggregate,
            body=dict(event.body or {}),
        )

    def to_domain_event_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at_ms": self.occurred_at_ms,
            "session_id": self.trace.session_id,
            "request_id": self.trace.request_id,
            "aggregate": self.aggregate_type,
            "body": self.body,
        }


@dataclass
class CommandEnvelope:
    trace: TraceContext
    verb: str
    command_line: str = ""
    args: dict[str, str] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace": self.trace.to_dict(),
            "verb": self.verb,
            "command_line": self.command_line,
            "args": dict(self.args),
            "payload_json": self.payload,
            "schema_version": self.schema_version,
        }


@dataclass
class ResultEnvelope:
    trace: TraceContext
    ok: bool
    action: str
    handler: str = "local"
    payload: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    artifacts: list[Artifact] = field(default_factory=list)
    error: dict[str, Any] | None = None
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace": self.trace.to_dict(),
            "ok": self.ok,
            "action": self.action,
            "handler": self.handler,
            "payload_json": self.payload,
            "diagnostics_json": self.diagnostics,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


def event_format() -> str:
    return os.environ.get("VDISPLAY_EVENT_FORMAT", "json").strip().lower() or "json"


def protobuf_events_enabled() -> bool:
    return event_format() in {"protobuf", "proto", "binary"}


def encode_event_envelope(envelope: DomainEventEnvelope) -> bytes:
    payload = json.dumps(
        {
            "event_id": envelope.event_id,
            "event_type": envelope.event_type,
            "occurred_at_ms": envelope.occurred_at_ms,
            "trace": envelope.trace.to_dict(),
            "aggregate_type": envelope.aggregate_type,
            "aggregate_id": envelope.aggregate_id,
            "event_version": envelope.event_version,
            "body_json": envelope.body,
            "artifacts": [item.to_dict() for item in envelope.artifacts],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return struct.pack(">4sI", MAGIC, len(payload)) + payload


def decode_event_envelope(data: bytes) -> DomainEventEnvelope:
    if len(data) < 8 or data[:4] != MAGIC:
        raise ValueError("invalid event envelope magic")
    (length,) = struct.unpack(">I", data[4:8])
    body = data[8 : 8 + length]
    payload = json.loads(body.decode("utf-8"))
    trace = TraceContext.from_dict(payload.get("trace"))
    if payload.get("session_id"):
        trace.session_id = payload.get("session_id")
    if payload.get("request_id"):
        trace.request_id = payload.get("request_id")
    artifacts = [Artifact.from_dict(item) for item in payload.get("artifacts") or [] if isinstance(item, dict)]
    body_json = payload.get("body_json")
    if not isinstance(body_json, dict):
        body_json = {}
    return DomainEventEnvelope(
        event_id=str(payload.get("event_id") or ""),
        event_type=str(payload.get("event_type") or ""),
        occurred_at_ms=int(payload.get("occurred_at_ms") or 0),
        trace=trace,
        aggregate_type=payload.get("aggregate_type") or payload.get("aggregate"),
        aggregate_id=payload.get("aggregate_id"),
        event_version=int(payload.get("event_version") or EVENT_VERSION),
        body=body_json,
        artifacts=artifacts,
    )


def encode_event_line_base64(envelope: DomainEventEnvelope) -> str:
    return base64.b64encode(encode_event_envelope(envelope)).decode("ascii")


def decode_event_line_base64(line: str) -> DomainEventEnvelope:
    return decode_event_envelope(base64.b64decode(line.strip()))


def read_length_delimited_events(path: Any) -> list[DomainEventEnvelope]:
    from pathlib import Path

    data = Path(path).read_bytes()
    envelopes: list[DomainEventEnvelope] = []
    offset = 0
    while offset + 8 <= len(data):
        if data[offset : offset + 4] != MAGIC:
            break
        (length,) = struct.unpack(">I", data[offset + 4 : offset + 8])
        chunk = data[offset : offset + 8 + length]
        envelopes.append(decode_event_envelope(chunk))
        offset += 8 + length
    return envelopes

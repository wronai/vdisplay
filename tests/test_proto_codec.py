"""Protobuf envelope codec tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.event_store import EventStore
from vdisplay.application.events import DomainEvent
from vdisplay.application.proto.codec import (
    DomainEventEnvelope,
    decode_event_envelope,
    decode_event_line_base64,
    encode_event_envelope,
    encode_event_line_base64,
    read_length_delimited_events,
)


def test_domain_event_envelope_roundtrip() -> None:
    event = DomainEvent(
        event_id="evt-1",
        event_type="ControlActionPlanned",
        occurred_at_ms=123,
        session_id="sess",
        request_id="req",
        aggregate="control_action",
        body={"verb": "CONTROL_CLICK", "action": "invoke"},
    )
    envelope = DomainEventEnvelope.from_domain_event(event)
    encoded = encode_event_envelope(envelope)
    decoded = decode_event_envelope(encoded)
    assert decoded.event_id == "evt-1"
    assert decoded.event_type == "ControlActionPlanned"
    assert decoded.body["verb"] == "CONTROL_CLICK"
    assert decoded.trace.session_id == "sess"


def test_event_line_base64_roundtrip() -> None:
    envelope = DomainEventEnvelope(
        event_id="evt-2",
        event_type="SessionStarted",
        occurred_at_ms=1,
        trace=DomainEventEnvelope.from_domain_event(
            DomainEvent(
                event_id="evt-2",
                event_type="SessionStarted",
                occurred_at_ms=1,
                session_id="demo",
                body={"source": "cli"},
            )
        ).trace,
        body={"source": "cli"},
    )
    line = encode_event_line_base64(envelope)
    decoded = decode_event_line_base64(line)
    assert decoded.event_type == "SessionStarted"


def test_event_store_writes_index_pb(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("VDISPLAY_EVENT_FORMAT", "protobuf")
    store = EventStore(tmp_path)
    store.append(
        DomainEvent(
            event_id="evt-3",
            event_type="CommandReceived",
            occurred_at_ms=10,
            session_id="demo",
            request_id="req",
            aggregate="command",
            body={"verb": "MONITORS"},
        )
    )
    assert (tmp_path / "index.jsonl").is_file()
    assert (tmp_path / "index.pb").is_file()
    envelopes = read_length_delimited_events(tmp_path / "index.pb")
    assert len(envelopes) == 1
    assert envelopes[0].event_type == "CommandReceived"


def test_read_length_delimited_multiple_events(tmp_path: Path) -> None:
    path = tmp_path / "index.pb"
    events = [
        DomainEventEnvelope(
            event_id=f"evt-{idx}",
            event_type="StepRecorded",
            occurred_at_ms=idx,
            body={"step_id": f"{idx:04d}"},
        )
        for idx in range(1, 4)
    ]
    path.write_bytes(b"".join(encode_event_envelope(event) for event in events))
    decoded = read_length_delimited_events(path)
    assert [item.event_id for item in decoded] == ["evt-1", "evt-2", "evt-3"]


def test_json_index_still_human_readable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("VDISPLAY_EVENT_FORMAT", "protobuf")
    store = EventStore(tmp_path)
    store.append(
        DomainEvent(
            event_id="evt-4",
            event_type="CommandCompleted",
            occurred_at_ms=20,
            session_id="demo",
            body={"ok": True},
        )
    )
    payload = json.loads((tmp_path / "index.jsonl").read_text(encoding="utf-8").strip())
    assert payload["event_type"] == "CommandCompleted"

from __future__ import annotations

import json
import struct

import pytest
from jsonschema import validate

from vdisplay.capture import (
    SCREEN_OBSERVATION_V1,
    ScreenObservation,
    ScreenObservationV1,
    downscale_rgb_nearest,
    png_dimensions,
    resolve_capture_scale,
    rgb_mostly_black,
    screen_observation_v1_schema,
)


def _observation(**overrides: object) -> ScreenObservation:
    values: dict[str, object] = {
        "frame_id": "producer-1",
        "monitor_id": 1,
        "captured_at": "2026-07-19T10:00:00+00:00",
        "mime": "image/png",
        "width": 320,
        "height": 180,
        "payload": b"png-payload",
        "native_width": 1920,
        "native_height": 1080,
        "output": "DP-1",
        "provider": "portal_screencast",
        "capture_meta": {"stream": {"node": 8}, "rotation": "normal"},
    }
    values.update(overrides)
    return ScreenObservation(**values)  # type: ignore[arg-type]


def test_public_v1_alias_and_legacy_sha256() -> None:
    observation = _observation()

    assert ScreenObservationV1 is ScreenObservation
    assert observation.schema == SCREEN_OBSERVATION_V1
    assert observation.sha256 == observation.payload_sha256
    assert observation.frame_id == "producer-1"


def test_observation_hash_ignores_volatile_correlation_fields() -> None:
    first = _observation(frame_id="attempt-a", captured_at="2026-07-19T10:00:00+00:00")
    retry = _observation(frame_id="attempt-b", captured_at="2026-07-19T10:00:01+00:00")

    assert first.observation_hash == retry.observation_hash


def test_observation_hash_is_canonical_and_sensitive_to_provenance() -> None:
    first = _observation(capture_meta={"z": [2, 1], "a": {"enabled": True}})
    reordered = _observation(capture_meta={"a": {"enabled": True}, "z": [2, 1]})
    changed = _observation(capture_meta={"a": {"enabled": False}, "z": [2, 1]})

    assert first.canonical_json() == reordered.canonical_json()
    assert first.observation_hash == reordered.observation_hash
    assert first.observation_hash != changed.observation_hash
    with pytest.raises(TypeError, match="non-JSON"):
        _observation(capture_meta={"bad": {1, 2}})


def test_wire_record_validates_and_roundtrips_with_optional_payload() -> None:
    observation = _observation()
    metadata_only = observation.to_dict()
    encoded = observation.to_dict(include_payload=True)

    validate(metadata_only, screen_observation_v1_schema())
    validate(encoded, screen_observation_v1_schema())
    assert "payload_base64" not in metadata_only
    assert json.dumps(metadata_only, sort_keys=True)
    assert ScreenObservation.from_dict(encoded) == observation


def test_wire_record_rejects_payload_or_observation_hash_mismatch() -> None:
    observation = _observation()
    record = observation.to_dict(include_payload=True)
    record["payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="payload_sha256"):
        ScreenObservation.from_dict(record)

    record = observation.to_dict(include_payload=True)
    record["provider"] = "different"
    with pytest.raises(ValueError, match="observation_hash"):
        ScreenObservation.from_dict(record)


def test_png_factory_exposes_provider_descriptor() -> None:
    payload = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 8, 6)
    observation = ScreenObservation.from_png(
        payload,
        monitor_id=2,
        captured_at="now",
        width=4,
        height=3,
        output="DP-2",
        provider="test",
    )

    assert png_dimensions(payload) == (8, 6)
    assert observation.native_width == 8
    assert observation.native_height == 6
    assert observation.to_descriptor()["payload"] == payload
    assert observation.to_descriptor()["width"] == 4


def test_dependency_free_pixel_primitives(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_CAPTURE_SCALE", "invalid")
    assert resolve_capture_scale(None, env_var="TEST_CAPTURE_SCALE") == 0.2
    assert resolve_capture_scale(4.0) == 1.0
    assert rgb_mostly_black(b"\x00\x00\x00" * 10)
    assert not rgb_mostly_black(b"\x01\x00\x00" * 10)
    assert downscale_rgb_nearest(bytes(range(12)), 2, 2, 1, 1) == bytes(range(3))

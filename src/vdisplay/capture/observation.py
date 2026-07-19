"""Deterministic wire contract for one captured screen observation.

The model deliberately separates three identities:

* ``frame_id`` is the producer-provided correlation id;
* ``payload_sha256`` identifies the exact image bytes;
* ``observation_hash`` identifies image bytes plus stable capture provenance.

Volatile fields (``frame_id`` and ``captured_at``) are excluded from the
canonical observation hash, so retries and cross-process hand-offs converge
on the same identity.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib import resources
from types import MappingProxyType
from typing import Any, TypeAlias


SCREEN_OBSERVATION_V1 = "vdisplay.screen-observation.v1"
_SCHEMA_RESOURCE = "screen-observation-v1.schema.json"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

JSONScalar: TypeAlias = None | bool | int | float | str
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


def _freeze_json(value: Any, *, path: str = "capture_meta") -> Any:
    """Validate a JSON value and return an immutable canonical equivalent."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            frozen[key] = _freeze_json(value[key], path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_freeze_json(item, path=f"{path}[]") for item in value)
    raise TypeError(f"{path} contains non-JSON value {type(value).__name__}")


def _thaw_json(value: Any) -> JSONValue:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def png_dimensions(payload: bytes) -> tuple[int, int]:
    """Read PNG dimensions from IHDR without an image-library dependency."""
    if len(payload) >= 24 and payload.startswith(_PNG_SIGNATURE) and payload[12:16] == b"IHDR":
        width, height = struct.unpack(">II", payload[16:24])
        return int(width), int(height)
    return 0, 0


@dataclass(frozen=True)
class ScreenObservation:
    """Immutable ``vdisplay.screen-observation.v1`` capture record.

    The first eleven fields intentionally match Koru's historical
    ``VisionFrame`` constructor.  This lets consumers adopt the public model
    without a flag day or an intermediate translation object.
    """

    frame_id: str
    monitor_id: int
    captured_at: str
    mime: str
    width: int
    height: int
    payload: bytes = field(repr=False)
    native_width: int = 0
    native_height: int = 0
    output: str = ""
    provider: str = ""
    capture_meta: Mapping[str, JSONValue] = field(default_factory=dict, repr=False, hash=False)

    def __post_init__(self) -> None:
        if not isinstance(self.payload, bytes):
            raise TypeError("payload must be bytes")
        if not self.mime:
            raise ValueError("mime must not be empty")
        for name in ("width", "height", "native_width", "native_height"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if not isinstance(self.capture_meta, Mapping):
            raise TypeError("capture_meta must be a mapping")
        object.__setattr__(self, "capture_meta", _freeze_json(self.capture_meta))

    @property
    def schema(self) -> str:
        return SCREEN_OBSERVATION_V1

    @property
    def payload_sha256(self) -> str:
        """Hash of the exact image payload."""
        return hashlib.sha256(self.payload).hexdigest()

    @property
    def sha256(self) -> str:
        """Backward-compatible alias for ``payload_sha256``."""
        return self.payload_sha256

    def canonical_dict(self) -> dict[str, JSONValue]:
        """Stable semantic input for ``observation_hash``.

        Producer correlation and wall-clock time are intentionally omitted.
        """
        return {
            "schema": self.schema,
            "payload_sha256": self.payload_sha256,
            "monitor_id": self.monitor_id,
            "mime": self.mime,
            "width": self.width,
            "height": self.height,
            "native_width": self.native_width,
            "native_height": self.native_height,
            "output": self.output,
            "provider": self.provider,
            "capture_meta": _thaw_json(self.capture_meta),
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @property
    def observation_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def to_dict(self, *, include_payload: bool = False) -> dict[str, JSONValue]:
        """Return a JSON-safe wire representation validated by the v1 schema."""
        record: dict[str, JSONValue] = {
            "schema": self.schema,
            "frame_id": self.frame_id,
            "monitor_id": self.monitor_id,
            "captured_at": self.captured_at,
            "mime": self.mime,
            "width": self.width,
            "height": self.height,
            "native_width": self.native_width,
            "native_height": self.native_height,
            "output": self.output,
            "provider": self.provider,
            "capture_meta": _thaw_json(self.capture_meta),
            "payload_sha256": self.payload_sha256,
            "observation_hash": self.observation_hash,
        }
        if include_payload:
            record["payload_base64"] = base64.b64encode(self.payload).decode("ascii")
        return record

    def to_descriptor(self) -> dict[str, Any]:
        """Return the in-process descriptor used by capture provider adapters."""
        return {
            "frame_id": self.frame_id,
            "monitor_id": self.monitor_id,
            "captured_at": self.captured_at,
            "mime": self.mime,
            "width": self.width,
            "height": self.height,
            "payload": self.payload,
            "native_width": self.native_width,
            "native_height": self.native_height,
            "output": self.output,
            "provider": self.provider,
            "capture_meta": _thaw_json(self.capture_meta),
        }

    @classmethod
    def from_png(
        cls,
        payload: bytes,
        *,
        monitor_id: int,
        captured_at: str,
        width: int | None = None,
        height: int | None = None,
        native_width: int | None = None,
        native_height: int | None = None,
        output: str = "",
        provider: str = "",
        capture_meta: Mapping[str, JSONValue] | None = None,
        frame_id: str | None = None,
    ) -> ScreenObservation:
        """Build a typed observation from PNG bytes and explicit provenance."""
        png_width, png_height = png_dimensions(payload)
        if png_width <= 0 or png_height <= 0:
            raise ValueError("payload is not a PNG with valid IHDR dimensions")
        return cls(
            frame_id=frame_id or hashlib.sha256(payload).hexdigest()[:16],
            monitor_id=monitor_id,
            captured_at=captured_at,
            mime="image/png",
            width=png_width if width is None else width,
            height=png_height if height is None else height,
            payload=payload,
            native_width=png_width if native_width is None else native_width,
            native_height=png_height if native_height is None else native_height,
            output=output,
            provider=provider,
            capture_meta=capture_meta or {},
        )

    @classmethod
    def from_dict(cls, record: Mapping[str, Any], *, payload: bytes | None = None) -> ScreenObservation:
        """Restore a record from its wire form or from a raw provider descriptor."""
        if record.get("schema", SCREEN_OBSERVATION_V1) != SCREEN_OBSERVATION_V1:
            raise ValueError(f"unsupported screen observation schema: {record.get('schema')!r}")
        encoded = record.get("payload_base64")
        if payload is None and isinstance(encoded, str):
            payload = base64.b64decode(encoded, validate=True)
        if payload is None:
            raw_payload = record.get("payload")
            if isinstance(raw_payload, bytes):
                payload = raw_payload
        if payload is None:
            raise ValueError("payload or payload_base64 is required")
        observation = cls(
            frame_id=str(record.get("frame_id") or hashlib.sha256(payload).hexdigest()[:16]),
            monitor_id=int(record.get("monitor_id", -1)),
            captured_at=str(record.get("captured_at") or ""),
            mime=str(record.get("mime") or "application/octet-stream"),
            width=int(record.get("width", 0)),
            height=int(record.get("height", 0)),
            payload=payload,
            native_width=int(record.get("native_width", 0)),
            native_height=int(record.get("native_height", 0)),
            output=str(record.get("output") or ""),
            provider=str(record.get("provider") or ""),
            capture_meta=dict(record.get("capture_meta") or {}),
        )
        expected_payload_hash = record.get("payload_sha256")
        if expected_payload_hash and expected_payload_hash != observation.payload_sha256:
            raise ValueError("payload_sha256 does not match payload")
        expected_observation_hash = record.get("observation_hash")
        if expected_observation_hash and expected_observation_hash != observation.observation_hash:
            raise ValueError("observation_hash does not match observation")
        return observation


ScreenObservationV1 = ScreenObservation


def screen_observation_v1_schema() -> dict[str, Any]:
    """Load a fresh copy of the packaged JSON Schema for the wire contract."""
    resource = resources.files("vdisplay.data").joinpath(_SCHEMA_RESOURCE)
    return json.loads(resource.read_text(encoding="utf-8"))


__all__ = [
    "JSONValue",
    "SCREEN_OBSERVATION_V1",
    "ScreenObservation",
    "ScreenObservationV1",
    "png_dimensions",
    "screen_observation_v1_schema",
]

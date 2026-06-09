from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Capabilities:
    capture: bool = False
    input_control: bool = False
    launch: bool = False
    mirror_config: bool = False
    window_adopt: bool = False
    isolation: bool = False


@dataclass
class SessionInfo:
    kind: str
    backend: str
    active: bool = False
    width: int | None = None
    height: int | None = None
    source: str | None = None
    target: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

"""Session lifecycle kinds — orthogonal to control provider adapters."""

from __future__ import annotations

from enum import StrEnum


class SessionKind(StrEnum):
    VIRTUAL = "virtual"
    MIRROR = "mirror"
    RELAY = "relay"
    TERMINAL = "terminal"
    BROWSER = "browser"
    SCREENCAST = "screencast"
    CAPTURE_SAMPLER = "capture_sampler"

"""Structured diagnostics.control payloads from control actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from vdisplay.application.services.control import _build_control_diagnostics
from vdisplay.control.models import ControlBounds, ControlNode, ControlRole
from vdisplay.control.selector import ControlSelector


@dataclass
class _FakeRouting:
    selected_provider: str = "vision"
    verify_mode: str = "ocr_contains"
    why_selected: list[str] = field(default_factory=lambda: ["explicit backend=vision"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_provider": self.selected_provider,
            "verify_mode": self.verify_mode,
            "why_selected": list(self.why_selected),
        }


@dataclass
class _FakeVerification:
    verified: bool = True
    mode: str = "ocr_contains"
    confidence: float = 0.9
    reasons: list[str] = field(default_factory=lambda: ["text matched"])
    semantic: dict[str, Any] | None = None
    visual: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "mode": self.mode,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "semantic": self.semantic,
            "visual": self.visual,
            "ocr": None,
            "vision_llm": None,
        }


def test_build_control_diagnostics_includes_routing_and_map() -> None:
    selector = ControlSelector(
        backend="vision",
        extra={"map_path": "maps/chat.json", "map_target": "message"},
    )
    target = ControlNode(
        id="vision:msg",
        backend="vision",
        role=ControlRole.INPUT,
        name="message",
        bounds=ControlBounds(x=10, y=20, width=100, height=30),
    )
    diagnostics = _build_control_diagnostics(
        action="set_value",
        selector=selector,
        target=target,
        verify=True,
        screenshot_verify=False,
        result={
            "ok": True,
            "method": "ydotool-paste",
            "map_path": "maps/chat.json",
            "map_target": "message",
            "value": "hello",
        },
        routing=_FakeRouting(),
        verification=_FakeVerification(
            semantic={"verified": True, "text_value": {"after": "hello"}},
        ),
    )

    control = diagnostics["control"]
    assert control["action"] == "set_value"
    assert control["map"]["target"] == "message"
    assert control["routing"]["selected_provider"] == "vision"
    assert control["actuation"]["method"] == "ydotool-paste"
    assert control["verify"]["verified"] is True
    assert control["verify"]["phases"][0]["phase"] == "semantic"

"""set-value verify: ocr_contains mode and ok=false when text not applied."""

from __future__ import annotations

import pytest

from vdisplay.application.services.control import _build_action_payload, _resolve_verify_mode, control_set_value
from vdisplay.control.models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from vdisplay.control.selector import ControlSelector
from vdisplay.control.verifier import VerificationResult


def test_resolve_verify_mode_set_value_uses_ocr_contains_for_vision() -> None:
    assert (
        _resolve_verify_mode(
            action="set_value",
            verify=True,
            value="hello",
            routing_mode="anchor_visible",
            selected_provider="vision",
        )
        == "ocr_contains"
    )
    assert (
        _resolve_verify_mode(
            action="set_value",
            verify=True,
            value="hello",
            routing_mode="semantic",
            selected_provider="terminal",
        )
        == "semantic"
    )
    assert (
        _resolve_verify_mode(
            action="invoke",
            verify=True,
            value=None,
            routing_mode="anchor_visible",
        )
        == "anchor_visible"
    )


def test_build_action_payload_fails_ok_when_verify_false() -> None:
    target = ControlNode(
        id="vision:1",
        backend="vision",
        role=ControlRole.UNKNOWN,
        name="anything",
        bounds=ControlBounds(x=1, y=2, width=60, height=16),
    )
    verification = VerificationResult(
        verified=False,
        mode="ocr_contains",
        confidence=0.0,
        reasons=["ocr text missing"],
    )

    class FakeRouting:
        def to_dict(self):
            return {"verify_mode": "ocr_contains"}

    payload = _build_action_payload(
        action="set_value",
        selector=ControlSelector(text_contains="anything"),
        target=target,
        verify=True,
        screenshot_verify=False,
        result={"ok": True, "method": "ydotool-paste", "value": "hello"},
        routing=FakeRouting(),
        verification=verification,
    )
    assert payload["ok"] is False
    assert payload["reason"] == "text_not_applied"
    assert payload["verified"] is False


def test_control_set_value_verify_mode_ocr_contains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    class FakeRouting:
        verify_mode = "anchor_visible"
        verify_provider = "vision"
        selected_provider = "vision"

        def to_dict(self):
            return {}

    class FakeVision:
        name = "vision"

        def snapshot(self, **kwargs):
            return ControlSnapshot(
                backend="vision",
                window_id=None,
                app_label=None,
                nodes={},
                root_ids=[],
            )

        def find(self, selector):
            node = ControlNode(
                id="vision:ocr:0:anything",
                backend="vision",
                role=ControlRole.UNKNOWN,
                name="anything",
                bounds=ControlBounds(x=10, y=20, width=60, height=16),
            )
            return [node]

        def set_value(self, element_id: str, value: str):
            return {"ok": True, "method": "test-type", "value": value}

    monkeypatch.setattr(
        "vdisplay.application.services.control.resolve_provider_routing",
        lambda *args, **kwargs: (FakeVision(), FakeRouting()),
    )
    monkeypatch.setattr(
        "vdisplay.application.services.control._capture_before_state",
        lambda **_k: (None, None),
    )
    monkeypatch.setattr(
        "vdisplay.application.services.control._resolve_target",
        lambda provider, snapshot, selector: provider.find(selector)[0],
    )

    def _capture_verify(self, ctx, spec=None):
        captured["verify_mode"] = ctx.verify_mode
        return VerificationResult(
            verified=False,
            mode=ctx.verify_mode,
            confidence=0.0,
            reasons=["ocr text missing"],
        )

    monkeypatch.setattr(
        "vdisplay.control.verifier.VerifierPipeline.verify_after_action",
        _capture_verify,
    )

    payload = control_set_value(
        backend="vision",
        text_contains="anything",
        value="hello",
        verify=True,
    )
    assert captured["verify_mode"] == "ocr_contains"
    assert payload["ok"] is False
    assert payload["reason"] == "text_not_applied"

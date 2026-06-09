from __future__ import annotations

import io

import pytest

from vdisplay.application.services import control as control_svc
from vdisplay.control.models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from vdisplay.control.scoring import ProviderRoutingDecision, ProviderScore
from vdisplay.control.verifier import VerifierPipeline, VerifyContext, verify_spec_from_flags


def _png(color: tuple[int, int, int]) -> bytes:
    from PIL import Image

    image = Image.new("RGB", (32, 32), color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_verify_spec_from_dual_flags() -> None:
    spec = verify_spec_from_flags(verify_semantic=True, verify_screenshot=True, verify_mode="semantic")
    assert spec is not None
    assert spec.mode == "hybrid"


def test_hybrid_rescues_failed_semantic_with_visual(monkeypatch: pytest.MonkeyPatch) -> None:
    button = ControlNode(
        id="btn",
        backend="test",
        role=ControlRole.BUTTON,
        name="Go",
        bounds=ControlBounds(0, 0, 40, 20),
    )
    snapshot = ControlSnapshot(
        backend="test",
        window_id=None,
        app_label="demo",
        nodes={"btn": button},
        root_ids=["btn"],
    )

    class FakeProvider:
        name = "fake"

        def snapshot(self, **kwargs):
            return snapshot

        def invoke(self, element_id: str, *, action: str | None = None):
            return {"ok": True, "element_id": element_id}

    frames = {"n": 0}

    def fake_capture(**kwargs):
        frames["n"] += 1
        return _png((0, 0, 0) if frames["n"] == 1 else (255, 0, 0))

    routing = ProviderRoutingDecision(
        requested_backend="test",
        selected_provider="test",
        auto_mode=False,
        candidates=[ProviderScore(provider="test", score=100, eligible=True)],
        why_selected=["test mock"],
        verify_provider="test",
        verify_mode="hybrid",
    )
    monkeypatch.setattr(
        control_svc,
        "resolve_provider_routing",
        lambda backend, **kwargs: (FakeProvider(), routing),
    )

    result = control_svc._execute_action(
        action="invoke",
        display=":0",
        backend="test",
        verify=True,
        screenshot_verify=False,
        capture_fn=fake_capture,
        role="button",
        name="Go",
    )
    assert result["a11y_verified"] is False
    assert result["verified"] is True
    assert "visual verify rescued" in " ".join(result["verify_reasons"])
    assert result["verify_confidence"] == 0.75


def test_strict_dual_verify_still_requires_both(monkeypatch: pytest.MonkeyPatch) -> None:
    button = ControlNode(
        id="btn",
        backend="test",
        role=ControlRole.BUTTON,
        name="Go",
        bounds=ControlBounds(0, 0, 40, 20),
    )
    before = ControlSnapshot(
        backend="test",
        window_id=None,
        app_label="demo",
        nodes={"btn": button},
        root_ids=["btn"],
    )

    class FakeProvider:
        name = "fake"
        calls = 0

        def snapshot(self, **kwargs):
            self.calls += 1
            return before

        def invoke(self, element_id: str, *, action: str | None = None):
            return {"ok": True, "element_id": element_id}

    routing = ProviderRoutingDecision(
        requested_backend="test",
        selected_provider="test",
        auto_mode=False,
        candidates=[ProviderScore(provider="test", score=100, eligible=True)],
        why_selected=["test mock"],
        verify_mode="hybrid",
    )
    monkeypatch.setattr(
        control_svc,
        "resolve_provider_routing",
        lambda backend, **kwargs: (FakeProvider(), routing),
    )

    result = control_svc._execute_action(
        action="invoke",
        display=":0",
        backend="test",
        verify=True,
        screenshot_verify=True,
        capture_fn=lambda **kwargs: _png((0, 0, 0)),
        role="button",
        name="Go",
    )
    assert result["verified"] is False


def test_verifier_pipeline_semantic_only() -> None:
    from vdisplay.control.selector import ControlSelector

    before_button = ControlNode(
        id="btn",
        backend="test",
        role=ControlRole.BUTTON,
        name="Increment",
        text_value="Count: 0",
    )
    after_button = ControlNode(
        id="btn",
        backend="test",
        role=ControlRole.BUTTON,
        name="Increment",
        text_value="Count: 1",
    )
    before = ControlSnapshot(
        backend="test",
        window_id=None,
        app_label="demo",
        nodes={"btn": before_button},
        root_ids=["btn"],
    )
    after = ControlSnapshot(
        backend="test",
        window_id=None,
        app_label="demo",
        nodes={"btn": after_button},
        root_ids=["btn"],
    )

    class Provider:
        name = "test"

        def snapshot(self, **kwargs):
            return after

    result = VerifierPipeline().verify_after_action(
        VerifyContext(
            action_provider=Provider(),
            before_snapshot=before,
            target=before_button,
            action="invoke",
            selector=ControlSelector(role="button", name="Increment"),
            verify_semantic=True,
            verify_mode="semantic",
            spec=verify_spec_from_flags(
                verify_semantic=True,
                verify_screenshot=False,
                verify_mode="semantic",
            ),
        )
    )
    assert result.verified is True
    assert result.confidence == 0.9

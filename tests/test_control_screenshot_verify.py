from __future__ import annotations

import io

import pytest

from vdisplay.application.services import control as control_svc
from vdisplay.control.models import ControlBounds, ControlNode, ControlRole, ControlSnapshot
from vdisplay.control.policy import ProviderRoutingDecision, ProviderScore
from vdisplay.control.screenshot_verify import (
    _capture_via_agent,
    _maybe_crop_capture,
    capture_control_screenshot,
    diff_png_bytes,
    verify_screenshot_pair,
)


def _png(color: tuple[int, int, int], *, size: tuple[int, int] = (32, 32)) -> bytes:
    from PIL import Image

    image = Image.new("RGB", size, color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_diff_png_detects_change() -> None:
    before = _png((10, 10, 10))
    after = _png((200, 10, 10))
    result = diff_png_bytes(before, after)
    assert result["verified"] is True
    assert result["changed_ratio"] > 0


def test_diff_png_identical_is_not_verified() -> None:
    png = _png((10, 10, 10))
    result = diff_png_bytes(png, png)
    assert result["verified"] is False
    assert result["changed_ratio"] == 0.0


def test_diff_png_small_change_on_large_frame() -> None:
    before = _png((0, 0, 0), size=(200, 200))
    after = _png((0, 0, 0), size=(200, 200))
    from PIL import Image

    image = Image.open(io.BytesIO(after)).convert("RGB")
    image.putpixel((10, 10), (255, 0, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    after = buf.getvalue()
    result = diff_png_bytes(before, after, min_changed_ratio=0.00005)
    assert result["verified"] is True


def test_verify_screenshot_pair_payload() -> None:
    payload = verify_screenshot_pair(_png((0, 0, 0)), _png((255, 0, 0)))
    assert payload["verified"] is True
    assert "changed_ratio" in payload


def test_capture_via_agent_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    png = _png((5, 6, 7))

    class FakeClient:
        def capture_png_bytes(self, **kwargs):
            assert kwargs.get("output")
            return png, {"method": "portal-screencast", "display": kwargs.get("display")}

    monkeypatch.setattr("vdisplay.agent_config.resolve_agent_url", lambda **kwargs: "http://127.0.0.1:8765")
    monkeypatch.setattr("vdisplay.client.AgentClient", lambda url: FakeClient())

    captured = _capture_via_agent(display=":0", region=(1, 2, 3, 4))
    assert captured is not None
    data, meta = captured
    assert data == png
    assert meta["method"] == "portal-screencast"


def test_capture_via_agent_preserves_stream_region(monkeypatch: pytest.MonkeyPatch) -> None:
    from PIL import Image

    full = _png((20, 20, 20), size=(2560, 1600))
    image = Image.open(io.BytesIO(full)).convert("RGB")
    for x in range(2430, 2550):
        for y in range(540, 650):
            image.putpixel((x, y), (255, 0, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    png = buf.getvalue()

    class FakeClient:
        def capture_png_bytes(self, **kwargs):
            return png, {
                "method": "portal-screencast",
                "screencast_full_frame": True,
                "screencast_stream": True,
                "region": {"x": 0, "y": 1932, "width": 2048, "height": 1280},
                "width": 2560,
                "height": 1600,
            }

    monkeypatch.setattr("vdisplay.agent_config.resolve_agent_url", lambda **kwargs: "http://127.0.0.1:8765")
    monkeypatch.setattr("vdisplay.client.AgentClient", lambda url: FakeClient())

    captured, meta = _capture_via_agent(display=":0", region=(1951, 2373, 744, 72))
    assert captured == png
    assert meta.get("screencast_stream_region") == {"x": 0, "y": 1932, "width": 2048, "height": 1280}
    cropped, out_meta = _maybe_crop_capture((captured, meta), (1951, 2373, 744, 72))
    assert out_meta.get("region_cropped_client") is True
    assert out_meta.get("region_local", {}).get("width", 9999) < 2560


def test_maybe_crop_capture_screencast_global_region() -> None:
    from PIL import Image

    full = _png((0, 0, 0), size=(2560, 1600))
    image = Image.open(io.BytesIO(full)).convert("RGB")
    for x in range(2400, 2500):
        for y in range(540, 620):
            image.putpixel((x, y), (255, 0, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    full = buf.getvalue()

    meta = {
        "screencast_full_frame": True,
        "screencast_stream": True,
        "screencast_stream_region": {"x": 0, "y": 1932, "width": 2048, "height": 1280},
        "region": {"x": 0, "y": 1932, "width": 2048, "height": 1280},
        "width": 2560,
        "height": 1600,
    }
    cropped, out_meta = _maybe_crop_capture((full, meta), (1951, 2373, 744, 72))
    assert out_meta.get("region_crop_failed") is not True
    assert out_meta.get("region_cropped_client") is True
    crop = Image.open(io.BytesIO(cropped))
    assert crop.size[0] < 2560
    assert crop.size[1] < 1600


def test_capture_control_screenshot_uses_target_region() -> None:
    target = ControlNode(
        id="btn",
        backend="test",
        role=ControlRole.BUTTON,
        bounds=ControlBounds(100, 50, 80, 24),
    )
    captured: dict[str, object] = {}

    def fake_capture(*, display: str | None, region: tuple[int, int, int, int] | None) -> bytes:
        captured["display"] = display
        captured["region"] = region
        return _png((1, 2, 3))

    png, meta = capture_control_screenshot(display=":0", target=target, capture_fn=fake_capture)
    assert png
    assert captured["region"] == (88, 38, 104, 48)
    assert meta["method"] == "injected"


def test_execute_action_screenshot_verify_only(monkeypatch: pytest.MonkeyPatch) -> None:
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

        def focus(self, element_id: str):
            return {"ok": True, "element_id": element_id}

        def set_value(self, element_id: str, value: str):
            return {"ok": True, "element_id": element_id, "value": value}

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
        verify=False,
        screenshot_verify=True,
        capture_fn=fake_capture,
        role="button",
        name="Go",
    )
    assert result["screenshot_verify"] is True
    assert result["verified"] is True
    assert result["screenshot_diff"]["verified"] is True
    assert result.get("a11y_verified") is None


def test_execute_action_dual_verify_requires_both(monkeypatch: pytest.MonkeyPatch) -> None:
    before_button = ControlNode(
        id="btn",
        backend="test",
        role=ControlRole.BUTTON,
        name="Go",
        bounds=ControlBounds(0, 0, 40, 20),
    )
    after_button = ControlNode(
        id="btn",
        backend="test",
        role=ControlRole.BUTTON,
        name="Go",
        bounds=ControlBounds(0, 0, 40, 20),
    )
    before = ControlSnapshot(backend="test", window_id=None, app_label="demo", nodes={"btn": before_button}, root_ids=["btn"])
    after = ControlSnapshot(backend="test", window_id=None, app_label="demo", nodes={"btn": after_button}, root_ids=["btn"])

    class FakeProvider:
        name = "fake"
        calls = 0

        def snapshot(self, **kwargs):
            self.calls += 1
            return before if self.calls == 1 else after

        def invoke(self, element_id: str, *, action: str | None = None):
            return {"ok": True, "element_id": element_id}

    frames = {"n": 0}

    def fake_capture(**kwargs):
        frames["n"] += 1
        return _png((0, 0, 0))

    routing = ProviderRoutingDecision(
        requested_backend="test",
        selected_provider="test",
        auto_mode=False,
        candidates=[ProviderScore(provider="test", score=100, eligible=True)],
        why_selected=["test mock"],
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
        capture_fn=fake_capture,
        role="button",
        name="Go",
    )
    assert result["a11y_verified"] is False
    assert result["screenshot_diff"]["verified"] is False
    assert result["verified"] is False

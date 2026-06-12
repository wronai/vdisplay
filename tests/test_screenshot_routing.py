from __future__ import annotations

import pytest

from vdisplay.application.commands import CommandRequest, CommandVerb
from vdisplay.application.handlers import agent as agent_handlers
from vdisplay.application.handlers import local as local_handlers
from vdisplay.application.services import capture
from vdisplay.exceptions import VDisplayError


def test_resolve_screenshot_routing_host_with_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")

    mode, display, vd_display = capture.resolve_screenshot_routing(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output="/tmp/host.png",
            source="DP-1",
            mode="host",
        )
    )
    assert mode == "host"
    assert display == ":0"
    assert vd_display == ":99"


def test_resolve_screenshot_routing_explicit_virtual(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")

    mode, display, vd_display = capture.resolve_screenshot_routing(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output="/tmp/vd.png",
            mode="virtual",
            vd_display=":196",
        )
    )
    assert mode == "virtual"
    assert display is None
    assert vd_display == ":196"


def test_resolve_screenshot_routing_virtual_display_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")

    mode, display, vd_display = capture.resolve_screenshot_routing(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output="/tmp/vd.png",
            display=":99",
            mode="host",
        )
    )
    assert mode == "virtual"
    assert display is None
    assert vd_display == ":99"


def test_local_screenshot_handler_uses_host_for_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")
    calls: list[dict] = []

    def fake_local(**kwargs):
        calls.append(kwargs)
        return {"mode": kwargs["mode"], "saved": kwargs["output"]}

    monkeypatch.setattr(capture, "capture_screenshot_local", fake_local)

    local_handlers.execute_local(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output="/tmp/host.png",
            source="DP-1",
        )
    )
    assert calls[0]["mode"] == "host"
    assert calls[0]["source"] == "DP-1"
    assert calls[0]["display"] == ":0"


def test_agent_screenshot_handler_uses_host_for_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")
    calls: list[dict] = []

    class FakeClient:
        pass

    def fake_via_client(client, **kwargs):
        calls.append(kwargs)
        return {"mode": kwargs["mode"], "saved": kwargs["output"]}

    monkeypatch.setattr(capture, "capture_screenshot_via_client", fake_via_client)
    monkeypatch.setattr(agent_handlers, "agent_client_required", lambda: FakeClient())

    agent_handlers.execute_agent(
        CommandRequest(
            verb=CommandVerb.SCREENSHOT,
            output="/tmp/host.png",
            source="DP-1",
        )
    )
    assert calls[0]["mode"] == "host"
    assert calls[0]["source"] == "DP-1"
    assert calls[0]["display"] == ":0"


def test_agent_screenshot_handler_rejects_unknown_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(
        "vdisplay.application.services.capture.list_monitors",
        lambda _display: [
            {"name": "DP-1"},
            {"name": "HDMI-1"},
        ],
        raising=False,
    )
    monkeypatch.setattr(
        "vdisplay.discovery.list_monitors",
        lambda _display: [
            {"name": "DP-1"},
            {"name": "HDMI-1"},
        ],
    )
    monkeypatch.setattr("vdisplay.discovery.resolve_host_display", lambda _display: ":0")
    monkeypatch.setattr("vdisplay.application.services.capture.resolve_host_display", lambda _display: ":0", raising=False)
    monkeypatch.setattr(agent_handlers, "agent_client_required", lambda: object())

    with pytest.raises(VDisplayError, match="monitor not found: DP-2"):
        agent_handlers.execute_agent(
            CommandRequest(
                verb=CommandVerb.SCREENSHOT,
                output="/tmp/host.png",
                source="DP-2",
            )
        )

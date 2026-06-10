from __future__ import annotations

import pytest

from vdisplay.application.commands import CommandRequest, CommandVerb
from vdisplay.client_routes import route_command
from vdisplay.exceptions import VDisplayError


def test_route_command_virtual_start_body() -> None:
    cmd = CommandRequest(verb=CommandVerb.VIRTUAL_START, width=800, height=600, vd_display=":99")
    method, path, body = route_command(cmd)
    assert method == "POST"
    assert path == "/session/virtual/start"
    assert body == {"width": 800, "height": 600, "display": ":99"}


def test_route_command_diagnose_control_display_query() -> None:
    cmd = CommandRequest(verb=CommandVerb.DIAGNOSE_CONTROL, display=":0")
    method, path, body = route_command(cmd)
    assert method == "GET"
    assert path == "/diagnostics/control?display=:0"
    assert body is None


def test_route_command_browser_open_body() -> None:
    cmd = CommandRequest(
        verb=CommandVerb.BROWSER_OPEN,
        browser_url="https://example.com",
        browser_headless=False,
        browser_engine="firefox",
    )
    method, path, body = route_command(cmd)
    assert method == "POST"
    assert path == "/session/browser/open"
    assert body == {
        "url": "https://example.com",
        "headless": False,
        "engine": "firefox",
    }


def test_route_command_unknown_verb_raises() -> None:
    cmd = CommandRequest(verb=CommandVerb.SCREENSHOT)
    with pytest.raises(VDisplayError, match="no direct route"):
        route_command(cmd)

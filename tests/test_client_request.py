from __future__ import annotations

from vdisplay.application.commands import CommandRequest, CommandVerb
from vdisplay.client import AgentClient, _route_command


def test_route_command_health() -> None:
    method, path, body = _route_command(CommandRequest(verb=CommandVerb.HEALTH))
    assert method == "GET"
    assert path == "/health"
    assert body is None


def test_route_command_windows_query() -> None:
    cmd = CommandRequest(
        verb=CommandVerb.WINDOWS,
        display=":0",
        match_class="Firefox",
        match_pid=42,
    )
    method, path, body = _route_command(cmd)
    assert method == "GET"
    assert path.startswith("/windows?")
    assert "display=:0" in path
    assert "match_class=Firefox" in path
    assert "match_pid=42" in path
    assert body is None


def test_request_delegates_to_http(monkeypatch) -> None:
    calls: list[tuple[str, str, dict | None]] = []

    def fake_request(self, method, path, *, body=None):
        calls.append((method, path, body))
        return {"status": "ok"}

    monkeypatch.setattr(AgentClient, "_request", fake_request)
    client = AgentClient("http://127.0.0.1:8765")
    result = client.request(CommandRequest(verb=CommandVerb.HEALTH))
    assert result.ok is True
    assert result.data == {"status": "ok"}
    assert calls == [("GET", "/health", None)]

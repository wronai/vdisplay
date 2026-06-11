from __future__ import annotations

import pytest

from dsl2vdisplay.bus import dispatch
from dsl2vdisplay.grammar import parse_line, to_text
from dsl2vdisplay.schema_registry import validate_command_dict
from vdisplay.application.commands import CommandRequest, CommandResult, CommandVerb
from vdisplay.control.providers.browser_session import default_registry
from vdisplay.control.scoring import rank_providers
from vdisplay.control.selector import ControlSelector
from fixtures.fake_browser import FakePage


def test_parse_browser_open_session_alias() -> None:
    cmd = parse_line("browser open --url https://example.com --session web-1")
    assert cmd is not None
    assert cmd["session_id"] == "web-1"


def test_parse_browser_open_line() -> None:
    cmd = parse_line("browser open --url https://example.com --session-id web-1 --headed")
    assert cmd is not None
    assert cmd["verb"] == "BROWSER_OPEN"
    assert cmd["url"] == "https://example.com"
    assert cmd["session_id"] == "web-1"
    assert cmd["headless"] is False


def test_browser_open_schema_requires_url() -> None:
    errors = validate_command_dict({"verb": "BROWSER_OPEN"})
    assert any("url" in err.lower() for err in errors)


def test_command_request_from_dsl_browser_open() -> None:
    cmd = parse_line('browser open --url https://example.test --session-id web-1 --title "Demo App"')
    assert cmd is not None
    request = CommandRequest.from_dsl(cmd, line="browser open")
    assert request.verb == CommandVerb.BROWSER_OPEN
    assert request.browser_session_id == "web-1"
    assert request.browser_url == "https://example.test"
    assert request.browser_title == "Demo App"
    assert request.browser_headless is True
    assert request.control_session_id is None


def test_to_text_roundtrip_browser_open() -> None:
    cmd = parse_line("browser open --url https://example.com --session-id web-1 --headed")
    assert cmd is not None
    line = to_text(cmd)
    assert "browser open" in line
    assert "--url https://example.com" in line
    assert "--session web-1" in line
    assert "--headed" in line


def test_dispatch_browser_open_local(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: dict[str, object] = {}

    def fake_browser_open(**kwargs):
        opened.update(kwargs)
        return {
            "ok": True,
            "session_id": kwargs.get("session_id") or "auto",
            "mode": "browser",
            "url": kwargs.get("url"),
        }

    monkeypatch.setattr(
        "vdisplay.application.services.session.browser_open",
        fake_browser_open,
    )

    result = dispatch("browser open --url https://example.com --session-id dsl-web")
    assert result.ok is True
    assert result.action == "browser_open"
    assert opened["session_id"] == "dsl-web"
    assert opened["url"] == "https://example.com"


def test_browser_open_e2e_local(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.providers import browser_session as browser_mod

    registry = default_registry()
    registry.close_all()

    def fake_open(self, url, *, session_id=None, headless=True, title=None, engine=None, page=None):
        return self.open_mock(
            FakePage(),
            url=url,
            session_id=session_id or "e2e-browser",
            title=title,
            engine=engine,
        )

    monkeypatch.setattr(browser_mod.BrowserSessionRegistry, "open", fake_open)

    try:
        result = dispatch("browser open --url https://example.test --session-id e2e-browser")
        assert result.ok is True
        assert result.data["session_id"] == "e2e-browser"
        assert registry.get("e2e-browser") is not None
    finally:
        registry.close_all()


def test_browser_open_enables_dom_provider_eligibility(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.providers import browser_session as browser_mod

    registry = default_registry()
    registry.close_all()
    # Prevent detached/persisted browser sessions (from e2e runs etc.) from making
    # list_ids() report "open" sessions. The before-check must see a clean "no browser
    # sessions" state so that dom_css selectors do not enable browser provider eligibility
    # until an explicit open for a session.
    monkeypatch.setattr(
        "vdisplay.control.browser_session_store.process_alive", lambda pid: False
    )
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))

    def fake_open(self, url, *, session_id=None, headless=True, title=None, engine=None, page=None):
        return self.open_mock(
            FakePage(),
            url=url,
            session_id=session_id or "gate-web",
            title=title,
            engine=engine,
        )

    monkeypatch.setattr(browser_mod.BrowserSessionRegistry, "open", fake_open)

    try:
        ranked_before, _ = rank_providers(selector=ControlSelector(dom_css="#go"))
        browser_before = next(item for item in ranked_before if item.provider == "browser")
        assert browser_before.eligible is False

        result = dispatch("browser open --url https://example.test --session gate-web")
        assert result.ok is True

        ranked_after, _ = rank_providers(
            selector=ControlSelector(dom_css="#go", session_id="gate-web"),
        )
        browser_after = next(item for item in ranked_after if item.provider == "browser")
        assert browser_after.eligible is True
    finally:
        registry.close_all()


def test_agent_client_browser_open_route() -> None:
    from vdisplay.client import AgentClient

    client = AgentClient("http://127.0.0.1:0", token="")
    captured: dict[str, object] = {}

    def fake_request_json(method, path, body=None, **kwargs):
        captured.update({"method": method, "path": path, "body": body})
        return {"ok": True, "session_id": "web-1", "mode": "browser"}

    client.request_json = fake_request_json  # type: ignore[method-assign]
    payload = client.browser_open(url="https://example.com", session_id="web-1", headless=False)
    assert payload["session_id"] == "web-1"
    assert captured["method"] == "POST"
    assert captured["path"] == "/session/browser/open"
    assert captured["body"] == {
        "url": "https://example.com",
        "headless": False,
        "session_id": "web-1",
    }


def test_dispatch_browser_open_via_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_execute(request, **kwargs):
        assert request.verb == CommandVerb.BROWSER_OPEN
        assert request.browser_url == "https://example.com"
        return CommandResult.success(action="browser_open", data={"session_id": "x"})

    import vdisplay.application.executor as executor_mod

    monkeypatch.setattr(executor_mod, "execute", fake_execute)
    result = dispatch("browser open --url https://example.com --session-id x")
    assert result.ok is True
    assert result.action == "browser_open"

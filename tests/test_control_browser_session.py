"""Browser session registry and session-scoped provider (PR-13)."""

from __future__ import annotations

import pytest

from vdisplay.control.providers.browser_playwright import BrowserPlaywrightProvider
from vdisplay.control.providers.browser_session import BrowserSessionRegistry
from vdisplay.control.selector import ControlSelector
from vdisplay.exceptions import VDisplayError
from fixtures.fake_browser import FakePage


@pytest.fixture
def registry(monkeypatch: pytest.MonkeyPatch) -> BrowserSessionRegistry:
    monkeypatch.setenv("VDISPLAY_BROWSER_DETACHED", "0")
    reg = BrowserSessionRegistry()
    yield reg
    reg.close_all()


def test_browser_registry_open_mock_and_close(registry: BrowserSessionRegistry) -> None:
    page = FakePage()
    session = registry.open_mock(page, url="https://example.test/app", session_id="browser-test-1")
    assert session.session_id == "browser-test-1"
    assert registry.list_ids() == ["browser-test-1"]
    registry.close("browser-test-1")
    assert registry.list_ids() == []


def test_provider_requires_session_without_legacy_page(registry: BrowserSessionRegistry) -> None:
    provider = BrowserPlaywrightProvider(registry=registry)
    with pytest.raises(VDisplayError):
        provider.snapshot()


def test_provider_uses_registry_session(registry: BrowserSessionRegistry) -> None:
    page = FakePage()
    session = registry.open_mock(page, session_id="browser-test-2")
    provider = BrowserPlaywrightProvider(session_id=session.session_id, registry=registry)
    snapshot = provider.snapshot()
    assert len(snapshot.nodes) == 2

    matches = provider.find(ControlSelector(dom_css="#inc", session_id=session.session_id))
    assert len(matches) == 1


def test_browser_registry_reuses_existing_session(registry: BrowserSessionRegistry) -> None:
    page = FakePage()
    first = registry.open_mock(page, url="https://example.test/a", session_id="browser-reuse")
    second = registry.open("https://example.test/b", session_id="browser-reuse")
    assert second is first
    assert second.session_id == "browser-reuse"


def test_browser_session_scoring_ineligible_without_open_session(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.scoring import rank_providers

    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.browser_session_store.session_available", lambda _sid: False)
    monkeypatch.setattr(
        "vdisplay.control.providers.browser_session.default_registry",
        lambda: type("EmptyRegistry", (), {"list_ids": lambda self: [], "get": lambda self, _sid: None})(),
    )
    ranked, _ = rank_providers(selector=ControlSelector(dom_css="#go"))
    browser = next(item for item in ranked if item.provider == "browser")
    assert browser.eligible is False
    assert any("no browser session" in item for item in browser.missing_requirements)

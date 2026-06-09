"""Browser session registry and session-scoped provider (PR-13)."""

from __future__ import annotations

import pytest

from vdisplay.control.providers.browser_playwright import BrowserPlaywrightProvider
from vdisplay.control.providers.browser_session import BrowserSessionRegistry
from vdisplay.control.selector import ControlSelector
from vdisplay.exceptions import VDisplayError
from fixtures.fake_browser import FakePage


@pytest.fixture
def registry() -> BrowserSessionRegistry:
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


def test_browser_session_scoring_ineligible_without_open_session(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.scoring import rank_providers

    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    ranked, _ = rank_providers(selector=ControlSelector(dom_css="#go"))
    browser = next(item for item in ranked if item.provider == "browser")
    assert browser.eligible is False
    assert any("no browser session" in item for item in browser.missing_requirements)

from __future__ import annotations

import pytest

from dsl2vdisplay.bus import dispatch
from dsl2vdisplay.grammar import parse_line
from vdisplay.application.commands import CommandRequest
from vdisplay.control.browser_engine import (
    browser_engine_profile,
    engine_profile_id,
    normalize_browser_engine,
    resolve_session_browser_engine,
)
from vdisplay.control.policy import evaluate_provider_routing
from vdisplay.control.profile_inference import infer_application_profile
from vdisplay.control.providers.browser_session import BrowserSessionRegistry, default_registry
from vdisplay.control.selector import ControlSelector
from fixtures.fake_browser import FakePage


def test_normalize_browser_engine_aliases() -> None:
    assert normalize_browser_engine("firefox").value == "firefox"
    assert normalize_browser_engine("chrome").value == "chromium"
    assert normalize_browser_engine("browser_firefox").value == "firefox"
    assert normalize_browser_engine(None).value == "chromium"


def test_browser_engine_application_profiles_exist() -> None:
    chromium = browser_engine_profile("chromium")
    firefox = browser_engine_profile("firefox")
    assert chromium is not None
    assert firefox is not None
    assert chromium.vendor == "chromium"
    assert firefox.vendor == "firefox"
    assert chromium.preferred_providers == ["browser"]
    assert engine_profile_id("firefox") == "browser_firefox"


def test_browser_session_stores_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = default_registry()
    registry.close_all()

    def fake_open(self, url, *, session_id=None, headless=True, title=None, engine=None, page=None):
        return self.open_mock(
            FakePage(),
            url=url,
            session_id=session_id or "ff-1",
            engine=engine,
        )

    monkeypatch.setattr(BrowserSessionRegistry, "open", fake_open)

    session = registry.open("https://example.test", session_id="ff-1", engine="firefox")
    assert session.engine == "firefox"
    assert resolve_session_browser_engine("ff-1") is not None
    assert resolve_session_browser_engine("ff-1").value == "firefox"
    registry.close_all()


def test_infer_browser_firefox_profile_from_session(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = default_registry()
    registry.close_all()
    registry.open_mock(FakePage(), session_id="ff-route", engine="firefox")

    try:
        inference = infer_application_profile(
            ControlSelector(dom_css="#go", session_id="ff-route"),
            session_id="ff-route",
        )
        assert inference is not None
        assert inference.profile_id == "browser_firefox"
        assert inference.confidence >= 0.9
    finally:
        registry.close_all()


def test_routing_prefers_browser_with_firefox_session(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = default_registry()
    registry.close_all()
    registry.open_mock(FakePage(), session_id="ff-route", engine="firefox")

    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "atspi ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "browser ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "x11 ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "terminal ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda sid: (True, f"session {sid} open"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "terminal session ok"),
    )

    try:
        decision = evaluate_provider_routing(
            backend="auto",
            selector=ControlSelector(dom_css="#submit", session_id="ff-route"),
            session_id="ff-route",
        )
        assert decision.selected_provider == "browser"
        assert decision.routing_semantics is not None
        assert decision.application_profile in {"browser_firefox", "web_spa"}
        browser = next(item for item in decision.candidates if item.provider == "browser")
        assert browser.eligible is True
        assert any("engine=firefox" in reason for reason in browser.reasons)
    finally:
        registry.close_all()


def test_web_spa_fallback_without_engine_session() -> None:
    inference = infer_application_profile(ControlSelector(dom_css="#go"))
    assert inference is not None
    assert inference.profile_id == "web_spa"


def test_dsl_browser_open_vendor_flag() -> None:
    cmd = parse_line("browser open --url https://example.com --session web-ff --vendor firefox")
    assert cmd is not None
    request = CommandRequest.from_dsl(cmd)
    assert request.browser_engine == "firefox"


def test_dispatch_browser_open_passes_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: dict[str, object] = {}

    def fake_browser_open(**kwargs):
        opened.update(kwargs)
        return {
            "ok": True,
            "session_id": kwargs.get("session_id"),
            "mode": "browser",
            "engine": kwargs.get("engine"),
            "profile_id": f"browser_{kwargs.get('engine')}",
        }

    monkeypatch.setattr(
        "vdisplay.application.services.session.browser_open",
        fake_browser_open,
    )

    result = dispatch(
        "browser open --url https://example.com --session web-ff --vendor firefox"
    )
    assert result.ok is True
    assert opened["engine"] == "firefox"

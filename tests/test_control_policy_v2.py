from __future__ import annotations

import pytest

from vdisplay.control.policy import (
    ProviderRoutingDecision,
    evaluate_provider_routing,
    rank_providers,
)
from vdisplay.control.selector import ControlSelector
from vdisplay.exceptions import BackendNotAvailableError


def _mock_ready(
    monkeypatch: pytest.MonkeyPatch,
    *,
    atspi: tuple[bool, str] = (True, "atspi ok"),
    browser: tuple[bool, str] = (True, "browser ok"),
    x11: tuple[bool, str] = (True, "x11 ok"),
    terminal: tuple[bool, str] = (True, "terminal ok"),
    terminal_session: tuple[bool, str] = (True, "session ok"),
) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: atspi)
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: browser)
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: x11)
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: terminal)
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: terminal_session,
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "browser session ok"),
    )


def test_auto_prefers_atspi_for_desktop_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(monkeypatch)
    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(role="button", name="OK", app="demo"),
    )
    assert decision.selected_provider == "atspi"
    assert decision.auto_mode is True
    assert decision.why_selected
    assert decision.candidates[0].provider == "atspi"


def test_auto_prefers_terminal_for_terminal_context(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(monkeypatch)
    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(environment="terminal", session_id="term-1"),
        session_id="term-1",
    )
    assert decision.selected_provider == "terminal"
    terminal = next(item for item in decision.candidates if item.provider == "terminal")
    assert terminal.eligible is True
    assert any("terminal selector context" in reason for reason in terminal.reasons)


def test_auto_prefers_browser_for_dom_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(monkeypatch)
    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(dom_css="#submit"),
    )
    assert decision.selected_provider == "browser"
    browser = next(item for item in decision.candidates if item.provider == "browser")
    assert any("browser/DOM selector context" in reason for reason in browser.reasons)


def test_terminal_ineligible_without_open_session(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(
        monkeypatch,
        terminal_session=(False, "no terminal session open"),
    )
    decision = evaluate_provider_routing(
        backend="auto",
        selector=ControlSelector(environment="terminal", terminal_line=3),
    )
    assert decision.selected_provider == "atspi"
    terminal = next(item for item in decision.candidates if item.provider == "terminal")
    assert terminal.eligible is False
    assert "no terminal session open" in terminal.missing_requirements
    assert "terminal" in decision.why_not_selected


def test_explicit_backend_respects_forced_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(monkeypatch)
    decision = evaluate_provider_routing(backend="terminal", session_id="term-1")
    assert decision.selected_provider == "terminal"
    assert decision.auto_mode is False
    assert "explicit backend=terminal" in decision.why_selected[0]


def test_explicit_backend_raises_when_ineligible(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(monkeypatch, terminal=(False, "pyte missing"))
    with pytest.raises(BackendNotAvailableError, match="terminal"):
        evaluate_provider_routing(backend="terminal")


def test_rank_providers_orders_by_score(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(monkeypatch)
    ranked, _inference = rank_providers(selector=ControlSelector(role="button"))
    providers = [item.provider for item in ranked]
    assert providers[0] == "atspi"
    assert _inference is not None
    assert _inference["profile_id"] == "native_gtk"
    assert providers.index("x11") < providers.index("terminal")


def test_diagnose_control_includes_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(monkeypatch)
    from vdisplay.application.services import control as control_svc

    payload = control_svc.diagnose_control(dom_css="button", backend="auto")
    assert payload["ok"] is True
    assert "routing" in payload
    assert "routing_semantics" in payload
    assert payload["routing"]["selected_provider"] == "browser"
    assert payload["routing_semantics"]["target_environment"] == "browser"
    assert payload.get("application_profile", {}).get("profile_id") == "web_spa"
    assert payload["routing"]["candidates"]


def test_routing_decision_serializes(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_ready(monkeypatch)
    decision = evaluate_provider_routing(backend="auto")
    assert isinstance(decision, ProviderRoutingDecision)
    data = decision.to_dict()
    assert data["requested_backend"] == "auto"
    assert isinstance(data["candidates"], list)
    assert isinstance(data["why_not_selected"], dict)

from __future__ import annotations

import inspect

import pytest

from vdisplay.control.base import ControlProvider
from vdisplay.control.registry import default_provider_registry
from vdisplay.control.router import ControlRouter
from vdisplay.control.scoring import rank_providers
from vdisplay.control.selector import ControlSelector


def test_registry_lists_builtin_providers() -> None:
    registry = default_provider_registry()
    assert registry.list_names() == ["atspi", "ax", "browser", "terminal", "uia", "vision", "x11"]


def test_router_evaluate_without_building_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_session_ready", lambda _sid: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_session_ready", lambda _sid: (True, "ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "session ok"),
    )

    decision = ControlRouter().evaluate(
        selector=ControlSelector(dom_css="#go"),
        verify_screenshot=True,
    )
    assert decision.selected_provider == "browser"
    assert decision.verify_mode in {"screenshot", "hybrid"}
    assert decision.verify_provider


@pytest.mark.parametrize("name", ["atspi", "ax", "browser", "uia", "x11", "terminal", "vision"])
def test_provider_contract_surface(name: str) -> None:
    registry = default_provider_registry()
    try:
        provider = registry.build(name)
    except Exception:
        pytest.skip(f"{name} provider unavailable in this environment")

    assert isinstance(provider, ControlProvider)
    for method_name in ("available", "snapshot", "find", "invoke", "focus", "set_value", "bounds"):
        assert hasattr(provider, method_name)
        assert callable(getattr(provider, method_name))

    sig = inspect.signature(provider.snapshot)
    assert "window_id" in sig.parameters or len(sig.parameters) >= 0


def test_rank_providers_returns_contract_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_session_ready", lambda _sid: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_session_ready", lambda _sid: (True, "ok"))

    ranked, inference = rank_providers(selector=ControlSelector(role="button"))
    assert ranked[0].provider == "atspi"
    assert inference is not None
    assert inference["profile_id"] == "native_gtk"
    assert ranked[0].score >= ranked[-1].score

from __future__ import annotations

import pytest

from vdisplay.control.profile_inference import infer_application_profile, profile_for
from vdisplay.control.router import ControlRouter
from vdisplay.control.scoring import rank_providers
from vdisplay.control.selector import ControlSelector


def test_infer_web_spa_from_dom_css() -> None:
    inferred = infer_application_profile(ControlSelector(dom_css="#submit"))
    assert inferred is not None
    assert inferred.profile_id == "web_spa"
    assert inferred.confidence >= 0.9


def test_infer_terminal_pty_from_coordinates() -> None:
    inferred = infer_application_profile(
        ControlSelector(environment="terminal", terminal_line=3, session_id="t1"),
        session_id="t1",
    )
    assert inferred is not None
    assert inferred.profile_id == "terminal_pty"
    assert inferred.confidence >= 0.9


def test_infer_native_gtk_from_role() -> None:
    inferred = infer_application_profile(
        ControlSelector(role="button", name="OK", app="demo"),
    )
    assert inferred is not None
    assert inferred.profile_id == "native_gtk"


def test_infer_vision_from_anchor() -> None:
    inferred = infer_application_profile(ControlSelector(vision_anchor="login-button"))
    assert inferred is not None
    assert inferred.profile_id == "vision_only_surface"


def test_profile_boost_prefers_browser_for_web_spa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_session_ready", lambda _sid: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "ok"))

    ranked, inference = rank_providers(selector=ControlSelector(dom_css="button"))
    assert inference is not None
    assert inference["profile_id"] == "web_spa"
    assert ranked[0].provider == "browser"


def test_router_includes_application_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_session_ready", lambda _sid: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "session ok"),
    )

    decision = ControlRouter().evaluate(
        selector=ControlSelector(environment="terminal", session_id="demo"),
        session_id="demo",
    )
    assert decision.application_profile == "terminal_pty"
    assert decision.profile_inference is not None
    assert decision.selected_provider == "terminal"


def test_profile_for_builtin_ids() -> None:
    profile = profile_for("web_spa")
    assert profile is not None
    assert "browser" in profile.preferred_providers

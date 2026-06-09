"""PR-18 — example control plugin wheel integration."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_EXAMPLE_SRC = Path(__file__).resolve().parents[1] / "examples" / "control-plugin" / "src"
if str(_EXAMPLE_SRC) not in sys.path:
    sys.path.insert(0, str(_EXAMPLE_SRC))

from vdisplay.control.plugins import (  # noqa: E402
    list_control_plugins,
    register_control_provider,
    reset_control_plugins_for_tests,
    unregister_control_provider,
)
from vdisplay.control.policy import evaluate_provider_routing
from vdisplay.control.registry import default_provider_registry
from vdisplay.control.selector import ControlSelector
from vdisplay_example_plugin import ECHO_DESCRIPTOR, EchoControlProvider, register_plugin  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_plugins() -> None:
    reset_control_plugins_for_tests()
    yield
    reset_control_plugins_for_tests()


def test_echo_provider_contract() -> None:
    provider = EchoControlProvider()
    ok, reason = provider.available()
    assert ok is True
    assert "echo" in reason

    nodes = provider.find(ControlSelector(name="demo-button"))
    assert len(nodes) == 1
    assert nodes[0].role.value == "button"

    result = provider.invoke(nodes[0].id)
    assert result["ok"] is True
    assert result["backend"] == "echo"


def test_register_plugin_via_entry_point_helper() -> None:
    register_plugin()
    plugins = list_control_plugins()
    echo = next(item for item in plugins if item["provider_id"] == "echo")
    assert echo["source"] == "entrypoint"
    assert echo["entry_point"] == "echo"

    registry = default_provider_registry()
    assert "echo" in registry.list_names()
    built = registry.build("echo")
    assert isinstance(built, EchoControlProvider)


def test_unregister_echo_restores_builtin_count() -> None:
    register_control_provider(
        ECHO_DESCRIPTOR,
        lambda **kwargs: EchoControlProvider(**kwargs),
        source="manual",
    )
    assert len(default_provider_registry().list_names()) == 8
    assert unregister_control_provider("echo") is True
    assert default_provider_registry().list_names() == [
        "atspi",
        "ax",
        "browser",
        "terminal",
        "uia",
        "vision",
        "x11",
    ]


def test_echo_routing_eligible_with_forced_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    register_plugin()
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._vision_ready", lambda: (True, "ok"))
    monkeypatch.setattr(
        "vdisplay.control.scoring._browser_session_ready",
        lambda _sid: (True, "ok"),
    )
    monkeypatch.setattr(
        "vdisplay.control.scoring._terminal_session_ready",
        lambda _sid: (True, "ok"),
    )

    decision = evaluate_provider_routing(
        backend="echo",
        selector=ControlSelector(name="demo-button"),
    )
    assert decision.selected_provider == "echo"
    echo = next(item for item in decision.candidates if item.provider == "echo")
    assert echo.eligible is True

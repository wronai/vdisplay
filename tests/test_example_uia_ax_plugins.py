"""PR-23 — example UIA/AX control plugin wheels."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_UIA_SRC = Path(__file__).resolve().parents[1] / "examples" / "control-plugin-uia" / "src"
_AX_SRC = Path(__file__).resolve().parents[1] / "examples" / "control-plugin-ax" / "src"
for path in (_UIA_SRC, _AX_SRC):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from vdisplay.control.plugins import (  # noqa: E402
    list_control_plugins,
    reset_control_plugins_for_tests,
    unregister_control_provider,
)
from vdisplay.control.policy import evaluate_provider_routing
from vdisplay.control.registry import default_provider_registry
from vdisplay.control.selector import ControlSelector
from vdisplay_example_ax_plugin import register_plugin as register_ax_plugin  # noqa: E402
from vdisplay_example_uia_plugin import register_plugin as register_uia_plugin  # noqa: E402
from vdisplay_example_ax_plugin.provider import ExampleAxProvider  # noqa: E402
from vdisplay_example_uia_plugin.provider import ExampleUiaProvider  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_plugins() -> None:
    reset_control_plugins_for_tests()
    yield
    reset_control_plugins_for_tests()


def _mock_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.control.scoring._atspi_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._xdotool_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._vision_ready", lambda: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._browser_session_ready", lambda _sid: (True, "ok"))
    monkeypatch.setattr("vdisplay.control.scoring._terminal_session_ready", lambda _sid: (True, "ok"))


def test_example_uia_mock_contract() -> None:
    provider = ExampleUiaProvider()
    ok, reason = provider.available()
    assert ok is True
    assert "mock" in reason.lower()

    nodes = provider.find(ControlSelector(role="button", name="Save", app="Notepad"))
    assert len(nodes) == 1
    assert nodes[0].backend == "example-uia"

    result = provider.invoke(nodes[0].id)
    assert result["ok"] is True
    assert result["backend"] == "example-uia"


def test_example_ax_mock_contract() -> None:
    provider = ExampleAxProvider()
    ok, reason = provider.available()
    assert ok is True
    assert "mock" in reason.lower()

    nodes = provider.find(ControlSelector(role="button", name="OK", app="Calculator"))
    assert len(nodes) == 1
    assert nodes[0].backend == "example-ax"

    result = provider.invoke(nodes[0].id)
    assert result["ok"] is True
    assert result["backend"] == "example-ax"


def test_register_uia_plugin_via_entry_point() -> None:
    register_uia_plugin()
    plugins = list_control_plugins()
    uia = next(item for item in plugins if item["provider_id"] == "example-uia")
    assert uia["source"] == "entrypoint"
    assert uia["entry_point"] == "example-uia"

    registry = default_provider_registry()
    assert "example-uia" in registry.list_names()
    built = registry.build("example-uia")
    assert isinstance(built, ExampleUiaProvider)


def test_register_ax_plugin_via_entry_point() -> None:
    register_ax_plugin()
    plugins = list_control_plugins()
    ax = next(item for item in plugins if item["provider_id"] == "example-ax")
    assert ax["source"] == "entrypoint"
    assert ax["entry_point"] == "example-ax"

    registry = default_provider_registry()
    assert "example-ax" in registry.list_names()
    built = registry.build("example-ax")
    assert isinstance(built, ExampleAxProvider)


def test_unregister_example_plugins_restores_builtin_count() -> None:
    register_uia_plugin()
    register_ax_plugin()
    assert len(default_provider_registry().list_names()) == 9
    assert unregister_control_provider("example-uia") is True
    assert unregister_control_provider("example-ax") is True
    assert default_provider_registry().list_names() == [
        "atspi",
        "ax",
        "browser",
        "terminal",
        "uia",
        "vision",
        "x11",
    ]


def test_example_uia_forced_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    register_uia_plugin()
    _mock_readiness(monkeypatch)

    decision = evaluate_provider_routing(
        backend="example-uia",
        selector=ControlSelector(role="button", name="Save", app="Notepad"),
    )
    assert decision.selected_provider == "example-uia"
    candidate = next(item for item in decision.candidates if item.provider == "example-uia")
    assert candidate.eligible is True


def test_example_ax_forced_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    register_ax_plugin()
    _mock_readiness(monkeypatch)

    decision = evaluate_provider_routing(
        backend="example-ax",
        selector=ControlSelector(role="button", name="OK", app="Calculator"),
    )
    assert decision.selected_provider == "example-ax"
    candidate = next(item for item in decision.candidates if item.provider == "example-ax")
    assert candidate.eligible is True

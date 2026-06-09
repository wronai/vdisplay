"""PR-21 — Windows UIA invoke with mock backend."""

from __future__ import annotations

import sys

import pytest

from vdisplay.control.models import ControlBounds, ControlRole
from vdisplay.control.providers.uia import UiaControlProvider
from vdisplay.control.providers.uia_impl import MockUiaBackend, UiaElementRecord, uia_deps_available
from vdisplay.control.selector import ControlSelector


def _ok_button() -> UiaElementRecord:
    return UiaElementRecord(
        key="42-1",
        name="OK",
        role=ControlRole.BUTTON,
        bounds=ControlBounds(x=10, y=20, width=80, height=24),
        automation_id="ok-btn",
        app_label="Notepad",
        provider_ref="ok-btn",
    )


def _name_field() -> UiaElementRecord:
    return UiaElementRecord(
        key="42-2",
        name="Name",
        role=ControlRole.INPUT,
        bounds=ControlBounds(x=10, y=60, width=200, height=24),
        automation_id="name-input",
        app_label="Notepad",
        provider_ref="name-input",
    )


def test_uia_deps_unavailable_on_linux() -> None:
    if sys.platform == "win32":
        pytest.skip("linux-only assertion")
    ok, reason = uia_deps_available()
    assert ok is False
    assert "Windows" in reason


def test_uia_find_element_by_name() -> None:
    backend = MockUiaBackend([_ok_button(), _name_field()])
    provider = UiaControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(name="OK"))
    assert len(nodes) == 1
    assert nodes[0].name == "OK"
    assert nodes[0].bounds.width == 80


def test_uia_find_by_accessibility_id() -> None:
    backend = MockUiaBackend([_ok_button()])
    provider = UiaControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(accessibility_id="ok-btn"))
    assert len(nodes) == 1
    assert nodes[0].provider_ref == "ok-btn"


def test_uia_click_invoke_pattern() -> None:
    backend = MockUiaBackend([_ok_button()])
    provider = UiaControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(name="OK"))
    result = provider.invoke(nodes[0].id)
    assert result["ok"] is True
    assert backend.invoked == ["42-1"]


def test_uia_set_value() -> None:
    backend = MockUiaBackend([_name_field()])
    provider = UiaControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(accessibility_id="name-input"))
    result = provider.set_value(nodes[0].id, "Alice")
    assert result["ok"] is True
    assert backend.values["42-2"] == "Alice"


def test_uia_focus() -> None:
    backend = MockUiaBackend([_ok_button()])
    provider = UiaControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(name="OK"))
    result = provider.focus(nodes[0].id)
    assert result["ok"] is True
    assert backend.focused == ["42-1"]


def test_uia_fallback_when_unavailable_on_linux() -> None:
    if sys.platform == "win32":
        pytest.skip("linux-only assertion")
    provider = UiaControlProvider()
    ok, reason = provider.available()
    assert ok is False
    assert "Windows" in reason or "comtypes" in reason

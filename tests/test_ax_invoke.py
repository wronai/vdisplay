"""PR-21 — macOS AX invoke with mock backend."""

from __future__ import annotations

import sys

import pytest

from vdisplay.control.models import ControlBounds, ControlRole
from vdisplay.control.providers.ax import AxControlProvider
from vdisplay.control.providers.ax_impl import AxElementRecord, MockAxBackend, ax_deps_available
from vdisplay.control.selector import ControlSelector


def _submit_button() -> AxElementRecord:
    return AxElementRecord(
        key="99-1",
        name="Submit",
        role=ControlRole.BUTTON,
        bounds=ControlBounds(x=30, y=40, width=90, height=22),
        automation_id="submit-btn",
        app_label="Safari",
        provider_ref="submit-btn",
    )


def _search_field() -> AxElementRecord:
    return AxElementRecord(
        key="99-2",
        name="Search",
        role=ControlRole.INPUT,
        bounds=ControlBounds(x=30, y=80, width=240, height=22),
        automation_id="search-input",
        app_label="Safari",
        provider_ref="search-input",
    )


def test_ax_deps_unavailable_on_linux() -> None:
    if sys.platform == "darwin":
        pytest.skip("linux-only assertion")
    ok, reason = ax_deps_available()
    assert ok is False
    assert "macOS" in reason


def test_ax_find_element_by_title() -> None:
    backend = MockAxBackend([_submit_button()])
    provider = AxControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(name="Submit", app="Safari"))
    assert len(nodes) == 1
    assert nodes[0].app_label == "Safari"


def test_ax_click() -> None:
    backend = MockAxBackend([_submit_button()])
    provider = AxControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(name="Submit"))
    result = provider.invoke(nodes[0].id)
    assert result["ok"] is True
    assert backend.invoked == ["99-1"]


def test_ax_set_value() -> None:
    backend = MockAxBackend([_search_field()])
    provider = AxControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(accessibility_id="search-input"))
    result = provider.set_value(nodes[0].id, "vdisplay")
    assert result["ok"] is True
    assert backend.values["99-2"] == "vdisplay"


def test_ax_focus() -> None:
    backend = MockAxBackend([_submit_button()])
    provider = AxControlProvider(backend=backend)
    nodes = provider.find(ControlSelector(name_contains="Sub"))
    result = provider.focus(nodes[0].id)
    assert result["ok"] is True
    assert backend.focused == ["99-1"]


def test_ax_fallback_when_unavailable_on_linux() -> None:
    if sys.platform == "darwin":
        pytest.skip("linux-only assertion")
    provider = AxControlProvider()
    ok, reason = provider.available()
    assert ok is False
    assert "macOS" in reason or "ApplicationServices" in reason

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from vdisplay.application.services.control import control_click, control_set_value, controls_find, controls_list
from vdisplay.exceptions import VDisplayError
from vdisplay.control.providers.atspi import AtspiControlProvider

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
DEMO_SCRIPT = FIXTURE_DIR / "gtk_demo_app.py"
APP_LABEL = "gtk_demo_app.py"
WINDOW_TITLE = "vdisplay-gtk-demo"


def _atspi_available() -> bool:
    provider = AtspiControlProvider()
    ok, _ = provider.available()
    return ok


def _display_available() -> bool:
    return bool(os.environ.get("DISPLAY"))


@pytest.fixture(scope="module")
def gtk_demo_process():
    if not _atspi_available() or not _display_available():
        pytest.skip("AT-SPI or DISPLAY unavailable")
    env = {
        **os.environ,
        "GTK_A11Y": "1",
        "NO_AT_BRIDGE": "0",
        "GDK_BACKEND": "x11",
        "DISPLAY": os.environ.get("DISPLAY", ":0"),
    }
    proc = subprocess.Popen(
        ["/usr/bin/python3", str(DEMO_SCRIPT)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)
    visible = controls_list(backend="atspi", app=WINDOW_TITLE, max_depth=4)
    if visible.get("count", 0) == 0:
        proc.terminate()
        pytest.skip("GTK demo not visible in AT-SPI (needs DISPLAY + GDK_BACKEND=x11)")
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable")
@pytest.mark.skipif(not _display_available(), reason="DISPLAY unavailable")
def test_gtk_demo_find_increment_button(gtk_demo_process) -> None:
    payload = controls_find(
        backend="atspi",
        role="button",
        name="Increment",
        app=WINDOW_TITLE,
    )
    assert payload["ok"] is True
    assert payload["selected"] is not None
    assert payload["selected"]["name"] == "Increment"


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable")
@pytest.mark.skipif(not _display_available(), reason="DISPLAY unavailable")
def test_gtk_demo_list_by_window_title(gtk_demo_process) -> None:
    from vdisplay.application.services.control import controls_list

    payload = controls_list(
        backend="atspi",
        app=WINDOW_TITLE,
        max_depth=4,
    )
    assert payload["ok"] is True
    assert payload["count"] > 0
    names = {node.get("name") for node in payload["nodes"].values()}
    assert "Increment" in names


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable")
@pytest.mark.skipif(not _display_available(), reason="DISPLAY unavailable")
def test_gtk_demo_click_verify_label(gtk_demo_process) -> None:
    payload = control_click(
        backend="atspi",
        role="button",
        name="Increment",
        app=WINDOW_TITLE,
        verify=True,
        verify_label="Count:",
    )
    assert payload["ok"] is True
    assert payload["verified"] is True
    label_changes = payload["state_diff"].get("label_changes") or payload["state_diff"].get("text_value_changes")
    assert label_changes
    assert "Count:" in str(label_changes[0].get("after", ""))


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable")
@pytest.mark.skipif(not _display_available(), reason="DISPLAY unavailable")
def test_gtk_demo_set_value_verify(gtk_demo_process) -> None:
    try:
        controls_find(backend="atspi", role="input", app=WINDOW_TITLE)
    except VDisplayError:
        pytest.skip("GTK demo entry not exposed in AT-SPI tree")

    payload = control_set_value(
        backend="atspi",
        role="input",
        app=WINDOW_TITLE,
        index=0,
        value="hello",
        verify=True,
    )
    assert payload["ok"] is True
    assert payload["verified"] is True
    assert payload["state_diff"]["text_value"]["after"] == "hello"

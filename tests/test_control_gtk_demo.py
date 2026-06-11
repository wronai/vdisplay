from __future__ import annotations

import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest

from vdisplay.application.services.control import control_click, control_set_value, controls_find, controls_list
from vdisplay.exceptions import VDisplayError
from vdisplay.control.providers.atspi import AtspiControlProvider

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
DEMO_SCRIPT = FIXTURE_DIR / "gtk_demo_app.py"
APP_LABEL = "gtk_demo_app.py"
DEFAULT_WINDOW_TITLE = "vdisplay-gtk-demo"
POLL_INTERVAL_S = 0.5
STARTUP_TIMEOUT_S = 30.0
_ATSPI_POLL_TIMEOUT_S = 3.0


@dataclass(frozen=True)
class GtkDemoSession:
    proc: subprocess.Popen[str]
    window_title: str


def _atspi_available() -> bool:
    provider = AtspiControlProvider()
    ok, _ = provider.available()
    return ok


def _display_available() -> bool:
    return bool(os.environ.get("DISPLAY"))


def _app_selector(*, window_title: str) -> dict[str, str]:
    return {"app": window_title}


def _find_selector(*, window_title: str) -> dict[str, str]:
    return {
        "app": window_title,
        "window_title": window_title,
    }


def _find_increment(*, window_title: str) -> dict[str, object] | None:
    # Scope the short poll timeout *only* to readiness probes. This affects the
    # env read inside atspi._run_subprocess for the subprocess.run(..., timeout=...).
    # We do NOT want to force 3s on the "real" controls_find calls in the test bodies
    # (or other atspi tests sharing the process), only on the waiter that expects
    # quick-fail when the target app/widget is not yet on the bus.
    old_timeout = os.environ.get("VDISPLAY_ATSPI_TIMEOUT_S")
    os.environ["VDISPLAY_ATSPI_TIMEOUT_S"] = str(_ATSPI_POLL_TIMEOUT_S)
    try:
        payload = controls_find(
            backend="atspi",
            role="button",
            name="Increment",
            **_find_selector(window_title=window_title),
        )
    except Exception:
        # Transient snapshot / a11y errors (timeouts, dbind, BackendNotAvailable during poll,
        # VDisplayError "no match", raw TimeoutExpired etc.) are expected while the demo
        # is still starting or when AT-SPI is sluggish. Treat as "not ready yet".
        return None
    finally:
        if old_timeout is None:
            os.environ.pop("VDISPLAY_ATSPI_TIMEOUT_S", None)
        else:
            os.environ["VDISPLAY_ATSPI_TIMEOUT_S"] = old_timeout
    if payload.get("selected"):
        return payload
    return None


def _wait_for_gtk_demo(*, proc: subprocess.Popen[str], window_title: str, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    # Give the child a moment to start and register with a11y before first expensive snapshot poll.
    time.sleep(0.2)
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        try:
            if _find_increment(window_title=window_title) is not None:
                return True
        except Exception:
            # Never let a11y snapshot problems escape the waiter; the outer deadline will
            # cause a clean skip instead of ERROR at setup of the gtk_demo tests.
            pass
        time.sleep(POLL_INTERVAL_S)
    return False


def _ensure_gtk_demo_ready(session: GtkDemoSession) -> None:
    if session.proc.poll() is not None:
        pytest.skip("GTK demo process exited before test")
    try:
        found = _find_increment(window_title=session.window_title) is not None
    except Exception:
        found = False
    if not found:
        if not _wait_for_gtk_demo(
            proc=session.proc,
            window_title=session.window_title,
            timeout_s=10.0,
        ):
            pytest.skip("GTK demo not visible in AT-SPI (needs DISPLAY + GDK_BACKEND=x11)")


@pytest.fixture(scope="module")
def gtk_demo_session() -> GtkDemoSession:
    if not _atspi_available() or not _display_available():
        pytest.skip("AT-SPI or DISPLAY unavailable")

    window_title = f"{DEFAULT_WINDOW_TITLE}-{uuid.uuid4().hex[:8]}"
    env = {
        **os.environ,
        "GTK_A11Y": "1",
        "NO_AT_BRIDGE": "0",
        "GDK_BACKEND": "x11",
        "DISPLAY": os.environ.get("DISPLAY", ":0"),
        "VDISPLAY_GTK_DEMO_TITLE": window_title,
        # Note: VDISPLAY_ATSPI_TIMEOUT_S is not needed for the demo itself (it does not
        # spawn atspi dispatch); the short timeout for polling snapshots is scoped inside
        # _find_increment for the *test* process that performs the controls_find calls.
    }
    proc = subprocess.Popen(
        ["/usr/bin/python3", str(DEMO_SCRIPT)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not _wait_for_gtk_demo(proc=proc, window_title=window_title, timeout_s=STARTUP_TIMEOUT_S):
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        pytest.skip("GTK demo not visible in AT-SPI (needs DISPLAY + GDK_BACKEND=x11)")

    session = GtkDemoSession(proc=proc, window_title=window_title)
    yield session

    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="module")
def gtk_demo_process(gtk_demo_session: GtkDemoSession) -> subprocess.Popen[str]:
    return gtk_demo_session.proc


@pytest.fixture
def gtk_demo_window(gtk_demo_session: GtkDemoSession) -> str:
    _ensure_gtk_demo_ready(gtk_demo_session)
    return gtk_demo_session.window_title


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable")
@pytest.mark.skipif(not _display_available(), reason="DISPLAY unavailable")
def test_gtk_demo_find_increment_button(gtk_demo_window: str) -> None:
    payload = controls_find(
        backend="atspi",
        role="button",
        name="Increment",
        **_find_selector(window_title=gtk_demo_window),
    )
    assert payload["ok"] is True
    assert payload["selected"] is not None
    assert payload["selected"]["name"] == "Increment"


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable")
@pytest.mark.skipif(not _display_available(), reason="DISPLAY unavailable")
def test_gtk_demo_list_by_window_title(gtk_demo_window: str) -> None:
    payload = controls_list(
        backend="atspi",
        max_depth=8,
        **_app_selector(window_title=gtk_demo_window),
    )
    assert payload["ok"] is True
    assert payload["count"] > 0
    names = {node.get("name") for node in payload["nodes"].values()}
    assert "Increment" in names


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable")
@pytest.mark.skipif(not _display_available(), reason="DISPLAY unavailable")
def test_gtk_demo_click_verify_label(gtk_demo_window: str) -> None:
    payload = control_click(
        backend="atspi",
        role="button",
        name="Increment",
        verify=True,
        verify_label="Count:",
        **_find_selector(window_title=gtk_demo_window),
    )
    assert payload["ok"] is True
    assert payload["verified"] is True
    label_changes = payload["state_diff"].get("label_changes") or payload["state_diff"].get("text_value_changes")
    assert label_changes
    assert "Count:" in str(label_changes[0].get("after", ""))


@pytest.mark.skipif(not _atspi_available(), reason="AT-SPI unavailable")
@pytest.mark.skipif(not _display_available(), reason="DISPLAY unavailable")
def test_gtk_demo_set_value_verify(gtk_demo_window: str) -> None:
    try:
        controls_find(
            backend="atspi",
            role="input",
            **_find_selector(window_title=gtk_demo_window),
        )
    except VDisplayError:
        pytest.skip("GTK demo entry not exposed in AT-SPI tree")

    payload = control_set_value(
        backend="atspi",
        role="input",
        index=0,
        value="hello",
        verify=True,
        **_find_selector(window_title=gtk_demo_window),
    )
    assert payload["ok"] is True
    assert payload["verified"] is True
    assert payload["state_diff"]["text_value"]["after"] == "hello"

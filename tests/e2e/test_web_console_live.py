"""Playwright GUI tests against vdisplay-agent (live broker).

By default starts an embedded agent (``live_agent_url`` fixture) so CI does not
require ``vdisplay-agent serve`` on port 8765.

For manual testing against a long-running broker + real screencast:
  export VDISPLAY_LIVE_EXTERNAL=1
  export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
  vdisplay-agent serve
  pytest tests/e2e/test_web_console_live.py -m live -v
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import pytest

pytestmark = pytest.mark.live


def _agent_base() -> str:
    return os.environ.get("VDISPLAY_AGENT_URL", "http://127.0.0.1:8765").rstrip("/")


def _external_live_requested() -> bool:
    return os.environ.get("VDISPLAY_LIVE_EXTERNAL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _fetch_json(path: str, *, base: str | None = None) -> dict:
    root = (base or _agent_base()).rstrip("/")
    req = urllib.request.Request(f"{root}{path}")
    token = os.environ.get("VDISPLAY_AGENT_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


@pytest.fixture(scope="module")
def broker_url(live_agent_url: str) -> str:
    if not _external_live_requested():
        return live_agent_url
    base = _agent_base()
    try:
        _fetch_json("/health", base=base)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        pytest.skip(f"live agent not reachable at {base}: {exc}")
    return base


@pytest.fixture(scope="module")
def live_overview(broker_url: str) -> dict:
    payload = _fetch_json("/api/web/overview", base=broker_url)
    assert payload.get("ok") is True, payload
    return payload["data"]


@pytest.fixture(scope="module")
def playwright_browser_live():
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def live_console_page(playwright_browser_live, broker_url: str):
    page = playwright_browser_live.new_page()
    page.goto(f"{broker_url}/web")
    page.wait_for_selector("[data-testid=console-header]")
    yield page
    page.close()


def test_live_overview_api(live_overview: dict) -> None:
    monitors = live_overview.get("monitors", {})
    assert int(monitors.get("monitor_count") or 0) >= 1
    names = [m.get("name") for m in monitors.get("monitors") or []]
    assert any(names), "expected at least one monitor name"


def test_live_replay_sessions_route(broker_url: str) -> None:
    payload = _fetch_json("/api/web/replay/sessions", base=broker_url)
    assert payload.get("ok") is True
    assert "sessions" in payload.get("data", {})


def test_live_console_loads(live_console_page) -> None:
    from playwright.sync_api import expect

    expect(live_console_page.get_by_test_id("console-title")).to_have_text("vdisplay console")
    expect(live_console_page.get_by_test_id("control-panel")).to_be_visible()
    expect(live_console_page.get_by_test_id("statusline")).not_to_have_text("loading")


def test_live_monitor_tiles(live_console_page, live_overview: dict) -> None:
    from playwright.sync_api import expect

    monitors = list((live_overview.get("monitors") or {}).get("monitors") or [])
    assert monitors, "no monitors in overview"
    first = str(monitors[0].get("name") or monitors[0].get("label") or "")
    assert first
    tile = live_console_page.get_by_test_id(f"monitor-tile-{first}")
    expect(tile).to_be_visible(timeout=15_000)
    expect(live_console_page.get_by_test_id(f"monitor-meta-{first}")).to_be_visible()


def test_live_monitor_frame_http(live_overview: dict, broker_url: str) -> None:
    sc = live_overview.get("screencast") or {}
    if not (sc.get("active") and sc.get("ready")):
        pytest.skip("screencast not active — run: vdisplay agent screencast start")

    monitors = list((live_overview.get("monitors") or {}).get("monitors") or [])
    name = str(monitors[0].get("name") or monitors[0].get("label") or "")
    req = urllib.request.Request(f"{broker_url}/api/web/frame/{name}")
    token = os.environ.get("VDISPLAY_AGENT_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            assert resp.status == 200
            assert resp.headers.get("content-type", "").startswith("image/png")
            assert len(resp.read()) > 100
    except urllib.error.HTTPError as exc:
        if exc.code == 503:
            pytest.skip(f"frame capture unavailable for {name}: {exc.reason}")
        raise


def test_live_screencast_pill_reflects_overview(live_console_page, live_overview: dict) -> None:
    from playwright.sync_api import expect

    sc = live_overview.get("screencast") or {}
    pill = live_console_page.get_by_test_id("screencast-pill")
    if sc.get("active") and sc.get("ready"):
        expect(pill).to_have_text("screencast ready")
    else:
        expect(pill).to_have_text("screencast off")


def test_live_replay_panel_loads(live_console_page) -> None:
    from playwright.sync_api import expect

    expect(live_console_page.get_by_test_id("replay-panel")).to_be_visible()
    expect(live_console_page.get_by_test_id("btn-replay-refresh")).to_be_visible()
    with live_console_page.expect_response(
        lambda resp: "/api/web/replay/sessions" in resp.url and resp.status == 200
    ):
        live_console_page.get_by_test_id("btn-replay-refresh").click()


def test_live_settings_interval_sync(live_console_page) -> None:
    from playwright.sync_api import expect

    live_console_page.get_by_test_id("auto-refresh").uncheck()
    interval = live_console_page.get_by_test_id("refresh-interval")
    interval.fill("3.0")
    interval.blur()
    expect(live_console_page.get_by_test_id("settings-interval-display")).to_have_text("3.0")

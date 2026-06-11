"""Playwright GUI tests for vdisplay web console (multi-monitor control desk)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture
def console_page(playwright_browser, web_app_url: str):
    page = playwright_browser.new_page()
    page.goto(f"{web_app_url}/web")
    page.wait_for_selector("[data-testid=console-header]")
    yield page
    page.close()


def test_console_header_and_status_pills(console_page) -> None:
    from playwright.sync_api import expect

    expect(console_page.get_by_test_id("console-title")).to_have_text("vdisplay console")
    expect(console_page.get_by_test_id("screencast-pill")).to_have_text("screencast ready")
    expect(console_page.get_by_test_id("sampler-pill")).to_have_text("sampler off")
    expect(console_page.get_by_test_id("statusline")).not_to_have_text("loading")


def test_monitor_tiles_render(console_page) -> None:
    from playwright.sync_api import expect

    expect(console_page.get_by_test_id("monitor-tile-DP-1")).to_be_visible()
    expect(console_page.get_by_test_id("monitor-tile-DP-2")).to_be_visible()
    expect(console_page.get_by_test_id("monitor-meta-DP-1")).to_contain_text("4096")
    expect(console_page.get_by_test_id("monitor-image-DP-1")).to_be_visible()
    expect(console_page.get_by_test_id("monitor-image-DP-1")).to_have_css("cursor", "crosshair")


def test_windows_and_tasks_tables(console_page) -> None:
    from playwright.sync_api import expect

    expect(console_page.get_by_test_id("tasks-table")).to_contain_text("task-sampler-1")
    expect(console_page.get_by_test_id("windows-table")).to_contain_text("firefox")
    expect(console_page.get_by_test_id("windows-table")).to_contain_text("Example Browser")


def test_control_buttons_present(console_page) -> None:
    from playwright.sync_api import expect

    expect(console_page.get_by_test_id("btn-screencast-start")).to_be_visible()
    expect(console_page.get_by_test_id("btn-screencast-stop")).to_be_visible()
    expect(console_page.get_by_test_id("btn-sampler-start")).to_be_visible()
    expect(console_page.get_by_test_id("btn-sampler-stop")).to_be_visible()


def test_settings_panel_shows_refresh_interval(console_page) -> None:
    from playwright.sync_api import expect

    expect(console_page.get_by_test_id("settings-panel")).to_be_visible()
    expect(console_page.get_by_test_id("settings-interval-display")).to_have_text("5")
    console_page.get_by_test_id("auto-refresh").uncheck()
    interval = console_page.get_by_test_id("refresh-interval")
    interval.fill("3")
    interval.blur()
    expect(console_page.get_by_test_id("settings-interval-display")).to_have_text("3")


def test_auto_refresh_toggle(console_page) -> None:
    from playwright.sync_api import expect

    checkbox = console_page.get_by_test_id("auto-refresh")
    expect(checkbox).not_to_be_checked()
    checkbox.check()
    expect(checkbox).to_be_checked()
    checkbox.uncheck()
    expect(checkbox).not_to_be_checked()


def test_replay_sessions_list_and_queue(console_page, web_app_url: str) -> None:
    from playwright.sync_api import expect

    expect(console_page.get_by_test_id("replay-panel")).to_be_visible()
    expect(console_page.get_by_test_id("replay-sessions")).to_contain_text("demo-session")
    replay_btn = console_page.get_by_test_id("btn-replay-demo-session")
    expect(replay_btn).to_be_visible()

    with console_page.expect_response(
        lambda resp: "/api/web/replay/start" in resp.url and resp.status == 200
    ) as resp_info:
        replay_btn.click()
    body = resp_info.value.json()
    assert body.get("ok") is True
    assert body.get("data", {}).get("queued") is True


def test_screencast_start_button_posts_api(console_page, web_app_url: str) -> None:
    from playwright.sync_api import expect

    with console_page.expect_response(
        lambda resp: "/api/web/screencast/start" in resp.url
    ) as resp_info:
        console_page.get_by_test_id("btn-screencast-start").click()
    response = resp_info.value
    assert response.status in {200, 400, 500}


def test_sampler_start_button_posts_api(console_page) -> None:
    with console_page.expect_response(
        lambda resp: "/api/web/sampler/start" in resp.url
    ) as resp_info:
        console_page.get_by_test_id("btn-sampler-start").click()
    assert resp_info.value.status in {200, 400, 500}


def test_replay_refresh_button(console_page) -> None:
    from playwright.sync_api import expect

    with console_page.expect_response(
        lambda resp: "/api/web/replay/sessions" in resp.url and resp.status == 200
    ):
        console_page.get_by_test_id("btn-replay-refresh").click()
    expect(console_page.get_by_test_id("replay-sessions")).to_contain_text("demo-session")


def test_monitor_click_posts_pointer_api(console_page) -> None:
    with console_page.expect_response(
        lambda resp: "/api/web/pointer/click" in resp.url and resp.status == 200
    ) as resp_info:
        console_page.get_by_test_id("monitor-image-DP-1").click(position={"x": 8, "y": 8})
    body = resp_info.value.json()
    assert body.get("ok") is True
    assert body.get("data", {}).get("monitor") == "DP-1"

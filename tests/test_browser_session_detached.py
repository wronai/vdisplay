from __future__ import annotations

import pytest

from vdisplay.control.browser_session_store import (
    load_meta,
    remove_meta,
    session_available,
    stop_detached,
)
from vdisplay.control.providers.browser_session import default_registry


@pytest.fixture
def clean_web1() -> None:
    stop_detached("web-1")
    default_registry().close_all()
    yield
    stop_detached("web-1")
    default_registry().close_all()


def test_detached_session_survives_registry_reset(monkeypatch: pytest.MonkeyPatch, clean_web1: None) -> None:
    monkeypatch.setenv("VDISPLAY_BROWSER_DETACHED", "1")
    launched: dict[str, object] = {}

    def fake_launch(**kwargs):
        launched.update(kwargs)
        from vdisplay.control.browser_session_store import DetachedBrowserMeta, save_meta

        meta = DetachedBrowserMeta(
            session_id=kwargs["session_id"],
            cdp_url="http://127.0.0.1:9222",
            pid=424242,
            url=kwargs["url"],
            engine="chromium",
            headless=kwargs["headless"],
        )
        save_meta(meta)
        return meta

    attached = {"count": 0}

    def fake_attach(self, session_id, *, meta=None, title=None):
        attached["count"] += 1
        from fixtures.fake_browser import FakePage

        return self.open_mock(FakePage(), session_id=session_id, url="https://example.com")

    monkeypatch.setattr(
        "vdisplay.control.browser_session_store.launch_detached_chromium",
        fake_launch,
    )
    monkeypatch.setattr(
        "vdisplay.control.browser_session_store.process_alive",
        lambda _pid: True,
    )
    monkeypatch.setattr(
        "vdisplay.control.providers.browser_session.BrowserSessionRegistry._attach",
        fake_attach,
    )

    registry = default_registry()
    registry.open("https://example.com", session_id="web-1", headless=True)
    assert session_available("web-1")

    registry._sessions.clear()
    assert "web-1" not in registry._sessions

    session = registry.get("web-1")
    assert session is not None
    assert attached["count"] >= 1
    assert load_meta("web-1") is not None
    remove_meta("web-1")

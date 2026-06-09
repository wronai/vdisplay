"""Playwright browser session registry for multi-tab control."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from ...exceptions import VDisplayError


def new_session_id() -> str:
    return f"browser-{uuid.uuid4().hex[:12]}"


@dataclass
class BrowserSession:
    session_id: str
    url: str | None = None
    title: str | None = None
    headless: bool = True
    engine: str = "chromium"
    page: Any | None = field(default=None, repr=False)
    _playwright: Any = field(default=None, repr=False)
    _browser: Any = field(default=None, repr=False)
    _alive: bool = True

    def close(self) -> None:
        self._alive = False
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self.page = None


class BrowserSessionRegistry:
    """Browser sessions — in-process registry with optional CDP reattach across CLI calls."""

    def __init__(self) -> None:
        self._sessions: dict[str, BrowserSession] = {}

    def list_ids(self) -> list[str]:
        from ..browser_session_store import _SESSION_ROOT, load_meta, process_alive

        ids = set(self._sessions)
        if _SESSION_ROOT.is_dir():
            for path in _SESSION_ROOT.glob("*.json"):
                meta = load_meta(path.stem)
                if meta is not None and process_alive(meta.pid):
                    ids.add(meta.session_id)
        return sorted(ids)

    def get(self, session_id: str) -> BrowserSession | None:
        if session_id in self._sessions:
            return self._sessions[session_id]
        return self._attach(session_id)

    def require(self, session_id: str) -> BrowserSession:
        session = self.get(session_id)
        if session is None:
            raise KeyError(f"browser session not found: {session_id}")
        return session

    def open(
        self,
        url: str,
        *,
        session_id: str | None = None,
        headless: bool = True,
        title: str | None = None,
        engine: str | None = None,
        page: Any | None = None,
    ) -> BrowserSession:
        from ..browser_engine import normalize_browser_engine

        resolved_engine = normalize_browser_engine(engine).value
        sid = session_id or new_session_id()
        if sid in self._sessions:
            raise VDisplayError(f"browser session already exists: {sid}")

        from ..browser_session_store import (
            detached_sessions_enabled,
            launch_detached_chromium,
            session_available,
        )

        if page is None and session_available(sid):
            return self._attach(sid)

        if page is not None:
            session = BrowserSession(
                session_id=sid,
                url=url,
                title=title or getattr(page, "title", lambda: None)(),
                headless=headless,
                engine=resolved_engine,
                page=page,
            )
            self._sessions[sid] = session
            return session

        from .browser_playwright import _playwright_available

        ready, reason = _playwright_available()
        if not ready:
            raise VDisplayError(reason)

        if detached_sessions_enabled() and resolved_engine != "firefox":
            meta = launch_detached_chromium(session_id=sid, url=url, headless=headless)
            return self._attach(sid, meta=meta, title=title)

        from playwright.sync_api import sync_playwright

        playwright = sync_playwright().start()
        if resolved_engine == "firefox":
            browser = playwright.firefox.launch(headless=headless)
        else:
            browser = playwright.chromium.launch(headless=headless)
        browser_page = browser.new_page()
        if url:
            browser_page.goto(url)
        session = BrowserSession(
            session_id=sid,
            url=url,
            title=title or browser_page.title(),
            headless=headless,
            engine=resolved_engine,
            page=browser_page,
            _playwright=playwright,
            _browser=browser,
        )
        self._sessions[sid] = session
        return session

    def _attach(self, session_id: str, *, meta: Any = None, title: str | None = None) -> BrowserSession | None:
        from ..browser_session_store import load_meta, process_alive, remove_meta

        record = meta or load_meta(session_id)
        if record is None:
            return None
        if not process_alive(record.pid):
            remove_meta(session_id)
            return None

        from .browser_playwright import _playwright_available

        ready, reason = _playwright_available()
        if not ready:
            raise VDisplayError(reason)

        from playwright.sync_api import sync_playwright

        playwright = sync_playwright().start()
        try:
            browser = playwright.chromium.connect_over_cdp(record.cdp_url)
        except Exception as exc:
            playwright.stop()
            remove_meta(session_id)
            raise VDisplayError(f"failed to attach browser session {session_id!r}: {exc}") from exc

        page = None
        for context in browser.contexts:
            if context.pages:
                page = context.pages[0]
                break
        if page is None:
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            if record.url:
                page.goto(record.url)

        session = BrowserSession(
            session_id=session_id,
            url=record.url,
            title=title or page.title(),
            headless=record.headless,
            engine=record.engine,
            page=page,
            _playwright=playwright,
            _browser=browser,
        )
        self._sessions[session_id] = session
        return session

    def open_mock(
        self,
        page: Any,
        *,
        url: str = "https://example.test/app",
        session_id: str | None = None,
        title: str | None = None,
        engine: str | None = None,
    ) -> BrowserSession:
        from ..browser_engine import normalize_browser_engine

        sid = session_id or new_session_id()
        if sid in self._sessions:
            raise VDisplayError(f"browser session already exists: {sid}")
        title_fn = getattr(page, "title", None)
        resolved_title = title or (title_fn() if callable(title_fn) else None)
        session = BrowserSession(
            session_id=sid,
            url=url,
            title=resolved_title,
            engine=normalize_browser_engine(engine).value,
            page=page,
        )
        self._sessions[sid] = session
        return session

    def close(self, session_id: str) -> None:
        from ..browser_session_store import stop_detached

        session = self._sessions.pop(session_id, None)
        if session is not None:
            session.close()
        stop_detached(session_id)

    def close_all(self) -> None:
        for sid in list(self._sessions):
            self.close(sid)


_DEFAULT_REGISTRY = BrowserSessionRegistry()


def default_registry() -> BrowserSessionRegistry:
    return _DEFAULT_REGISTRY

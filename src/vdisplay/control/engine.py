"""Resolve control providers (auto / explicit backend)."""

from __future__ import annotations

from ..exceptions import BackendNotAvailableError
from .base import ControlProvider
from .providers.atspi import AtspiControlProvider
from .providers.browser_playwright import BrowserPlaywrightProvider
from .providers.terminal import TerminalControlProvider
from .providers.x11 import X11ControlProvider
from .selector import ControlSelector


def _infer_backend(
    backend: str,
    *,
    selector: ControlSelector | None = None,
    session_id: str | None = None,
) -> str:
    normalized = (backend or "auto").strip().lower()
    if normalized != "auto":
        return normalized
    if selector is not None:
        if selector.backend and selector.backend.strip().lower() not in {"", "auto"}:
            return selector.backend.strip().lower()
        if (
            selector.environment == "terminal"
            or selector.terminal_line is not None
            or selector.terminal_col is not None
            or selector.session_id
        ):
            return "terminal"
        if selector.environment == "browser" or selector.dom_css or selector.dom_xpath:
            return "browser"
    if session_id:
        return "terminal"
    return "auto"


def resolve_provider(
    backend: str = "auto",
    *,
    display: str | None = None,
    session_id: str | None = None,
    selector: ControlSelector | None = None,
) -> ControlProvider:
    normalized = _infer_backend(backend, selector=selector, session_id=session_id)
    if normalized in {"atspi", "a11y", "accessibility"}:
        provider = AtspiControlProvider()
        ok, reason = provider.available()
        if not ok:
            raise BackendNotAvailableError(reason)
        return provider
    if normalized in {"browser", "playwright", "chromium"}:
        provider = BrowserPlaywrightProvider()
        ok, reason = provider.available()
        if not ok:
            raise BackendNotAvailableError(reason)
        return provider
    if normalized in {"x11", "x11-fallback", "pointer"}:
        provider = X11ControlProvider(display=display)
        ok, reason = provider.available()
        if not ok:
            raise BackendNotAvailableError(reason)
        return provider
    if normalized in {"terminal", "pty", "tui", "screen"}:
        sid = session_id or (selector.session_id if selector else None)
        provider = TerminalControlProvider(session_id=sid)
        ok, reason = provider.available()
        if not ok:
            raise BackendNotAvailableError(reason)
        return provider
    if normalized != "auto":
        raise BackendNotAvailableError(f"unknown control backend: {backend}")

    atspi = AtspiControlProvider()
    ok, _ = atspi.available()
    if ok:
        return atspi
    x11 = X11ControlProvider(display=display)
    ok, reason = x11.available()
    if ok:
        return x11
    raise BackendNotAvailableError(f"no control backend available ({reason})")

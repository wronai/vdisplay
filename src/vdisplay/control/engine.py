"""Resolve control providers (auto / explicit backend)."""

from __future__ import annotations

from ..exceptions import BackendNotAvailableError
from .base import ControlProvider
from .providers.atspi import AtspiControlProvider
from .providers.x11 import X11ControlProvider


def resolve_provider(backend: str = "auto", *, display: str | None = None) -> ControlProvider:
    normalized = (backend or "auto").strip().lower()
    if normalized in {"atspi", "a11y", "accessibility"}:
        provider = AtspiControlProvider()
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

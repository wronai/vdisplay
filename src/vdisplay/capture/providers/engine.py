"""Driver-level capture provider chain (DRM → fbdev → XCB → X11)."""

from __future__ import annotations

import os

from ...discovery import _looks_like_xvfb_only
from ...exceptions import VDisplayError
from ..linux_xwd import PNG_SIGNATURE, _is_wayland_session, is_blank_png
from .base import CaptureProvider, ProviderResult
from .drm import DrmProvider
from .fbdev import FbdevProvider
from .mss import MssProvider
from .x11 import X11Provider


def _allow_portal() -> bool:
    return os.environ.get("VDISPLAY_CAPTURE_ALLOW_PORTAL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _providers(display: str) -> list[CaptureProvider]:
    owned = _looks_like_xvfb_only(display)
    if owned or not _is_wayland_session():
        ordered: list[CaptureProvider] = [
            X11Provider(display),
            MssProvider(display),
            DrmProvider(),
            FbdevProvider(),
        ]
    else:
        ordered = [
            DrmProvider(),
            FbdevProvider(),
            MssProvider(display),
            X11Provider(display),
        ]
    if _allow_portal():
        from ..portal import PortalProvider

        ordered.append(PortalProvider())
    return ordered


def capture_full_png(display: str) -> ProviderResult:
    return _try_providers(_providers(display), display=display, region=None)


def capture_region_png(display: str, region: tuple[int, int, int, int]) -> ProviderResult:
    return _try_providers(_providers(display), display=display, region=region)


def list_capture_providers(display: str | None = None) -> list[dict[str, str]]:
    resolved = display or os.environ.get("DISPLAY") or ":0"
    rows: list[dict[str, str]] = []
    for provider in _providers(resolved):
        ok, reason = provider.available()
        rows.append({"name": provider.name, "available": str(ok).lower(), "reason": reason})
    return rows


def _try_providers(
    providers: list[CaptureProvider],
    *,
    display: str,
    region: tuple[int, int, int, int] | None,
) -> ProviderResult:
    errors: list[str] = []
    allow_blank = _looks_like_xvfb_only(display)
    for provider in providers:
        ok, reason = provider.available()
        if not ok:
            errors.append(f"{provider.name}: unavailable ({reason})")
            continue
        try:
            png = provider.capture_region(region) if region is not None else provider.capture_full()
        except Exception as exc:
            errors.append(f"{provider.name}: {exc}")
            continue
        if not png or png[: len(PNG_SIGNATURE)] != PNG_SIGNATURE:
            errors.append(f"{provider.name}: invalid PNG")
            continue
        if is_blank_png(png) and not allow_blank:
            errors.append(f"{provider.name}: blank/black frame")
            continue
        return ProviderResult(png=png, provider=provider.name, detail=reason)

    hint = (
        "Driver-level capture failed. On Wayland host sessions use DRM/fbdev (video group), "
        "or capture from vdisplay virtual/mirror framebuffer (Xvfb). "
        "Portal is disabled by default; set VDISPLAY_CAPTURE_ALLOW_PORTAL=1 to opt in."
    )
    if _is_wayland_session():
        hint += f" Session is Wayland (DISPLAY={os.environ.get('DISPLAY', ':0')} is XWayland)."
    raise VDisplayError(f"{hint}\nTried: {'; '.join(errors) or 'no providers'}")


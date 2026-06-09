"""X11 root capture via scrot/xwd (works on owned virtual displays and pure X11)."""

from __future__ import annotations

from ...capture.linux_xwd import _capture_scrot_png, _capture_xwd_png, _crop_png
from ...exceptions import VDisplayError


class X11Provider:
    name = "x11"

    def __init__(self, display: str) -> None:
        self.display = display

    def available(self) -> tuple[bool, str]:
        return True, f"X11 capture on DISPLAY={self.display}"

    def capture_full(self) -> bytes:
        errors: list[str] = []
        try:
            return _capture_scrot_png(self.display, None)
        except Exception as exc:
            errors.append(f"scrot: {exc}")
        try:
            return _capture_xwd_png(self.display)
        except Exception as exc:
            errors.append(f"xwd: {exc}")
        raise VDisplayError("; ".join(errors) or "x11 capture failed")

    def capture_region(self, region: tuple[int, int, int, int]) -> bytes:
        data = _capture_scrot_png(self.display, region)
        if data:
            return data
        full = self.capture_full()
        return _crop_png(full, region)

"""XCB/XGetImage capture via mss (low-level X11, no compositor portal)."""

from __future__ import annotations

import io
import os

from ...exceptions import VDisplayError


class MssProvider:
    name = "mss"

    def __init__(self, display: str) -> None:
        self.display = display

    def available(self) -> tuple[bool, str]:
        try:
            import mss  # noqa: F401
        except ImportError:
            from ...utils import auto_install_package
            try:
                auto_install_package("mss")
                import mss  # noqa: F401
            except Exception as exc:
                return False, f"mss auto-install failed: {exc}"
        return True, f"XCB screen grab via mss on DISPLAY={self.display}"

    def capture_full(self) -> bytes:
        return self._grab(None)

    def capture_region(self, region: tuple[int, int, int, int]) -> bytes:
        return self._grab(region)

    def _grab(self, region: tuple[int, int, int, int] | None) -> bytes:
        try:
            import mss
            from PIL import Image
        except ImportError:
            from ...utils import auto_install_package
            auto_install_package("mss")
            import mss
            from PIL import Image

        env = os.environ.copy()
        env["DISPLAY"] = self.display
        monitor = {
            "left": region[0] if region else 0,
            "top": region[1] if region else 0,
            "width": region[2] if region else 0,
            "height": region[3] if region else 0,
        }
        with mss.mss() as grabber:
            old_display = os.environ.get("DISPLAY")
            os.environ["DISPLAY"] = self.display
            try:
                if region is None:
                    monitor = grabber.monitors[0]
                shot = grabber.grab(monitor)
            finally:
                if old_display is None:
                    os.environ.pop("DISPLAY", None)
                else:
                    os.environ["DISPLAY"] = old_display
        image = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

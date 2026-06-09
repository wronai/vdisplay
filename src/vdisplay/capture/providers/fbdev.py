"""Legacy framebuffer capture from /dev/fb0 (kernel fbdev driver)."""

from __future__ import annotations

import io
import mmap
from pathlib import Path

from ...exceptions import VDisplayError


def _fb_info() -> tuple[int, int, int]:
    base = Path("/sys/class/graphics/fb0")
    if not base.is_dir():
        raise VDisplayError("fb0 sysfs missing")
    virtual = (base / "virtual_size").read_text().strip().split(",")
    width, height = int(virtual[0]), int(virtual[1])
    bpp = int((base / "bits_per_pixel").read_text().strip())
    return width, height, bpp


class FbdevProvider:
    name = "fbdev"

    def available(self) -> tuple[bool, str]:
        if not Path("/dev/fb0").exists():
            return False, "/dev/fb0 missing"
        try:
            _fb_info()
        except (OSError, ValueError, VDisplayError) as exc:
            return False, str(exc)
        return True, "kernel framebuffer /dev/fb0"

    def capture_full(self) -> bytes:
        return self._capture(None)

    def capture_region(self, region: tuple[int, int, int, int]) -> bytes:
        return self._capture(region)

    def _capture(self, region: tuple[int, int, int, int] | None) -> bytes:
        width, height, bpp = _fb_info()
        if bpp not in {16, 24, 32}:
            raise VDisplayError(f"unsupported fb0 bpp={bpp}")

        stride = width * (bpp // 8)
        try:
            with open("/dev/fb0", "rb") as handle:
                raw = mmap.mmap(handle.fileno(), stride * height, access=mmap.ACCESS_READ)
        except OSError as exc:
            raise VDisplayError(
                "cannot read /dev/fb0 (add user to `video` group for driver-level capture)"
            ) from exc

        try:
            from PIL import Image
        except ImportError as exc:
            raise VDisplayError("fbdev capture requires Pillow") from exc

        if bpp == 32:
            mode = "BGRX"
            image = Image.frombuffer("RGB", (width, height), raw, "raw", mode, stride, 1)
        elif bpp == 24:
            image = Image.frombuffer("RGB", (width, height), raw, "raw", "BGR", stride, 1)
        else:
            image = Image.frombytes("RGB", (width, height), raw[: stride * height])

        if region is not None:
            x, y, rw, rh = region
            left = max(0, min(x, width))
            top = max(0, min(y, height))
            right = max(left + 1, min(x + rw, width))
            bottom = max(top + 1, min(y + rh, height))
            image = image.crop((left, top, right, bottom))

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

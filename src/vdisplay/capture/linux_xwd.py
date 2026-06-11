from __future__ import annotations

import io
import os
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import BinaryIO, Callable

from ..exceptions import VDisplayError
from ..utils import require_command, run_command, run_command_bytes

XWD_VERSION = 7
ZPIXMAP = 2
LSB_FIRST = 0
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _is_valid_png(data: bytes) -> bool:
    return len(data) >= len(PNG_SIGNATURE) and data[: len(PNG_SIGNATURE)] == PNG_SIGNATURE


def is_blank_png(data: bytes) -> bool:
    """True when PNG is empty, invalid, or nearly all black (common on GNOME Wayland + X11 capture)."""
    if not _is_valid_png(data):
        return True
    try:
        from PIL import Image
    except ImportError:
        # Minimal PNG encoder (no Pillow) produces small but valid captures.
        return not _is_valid_png(data)

    image = Image.open(io.BytesIO(data)).convert("RGB")
    sample = image.resize((min(64, image.width), min(64, image.height)))
    pixels = list(sample.get_flattened_data())
    if not pixels:
        return True
    brightness = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels]
    if max(brightness) < 8:
        return True
    if len(set(pixels)) <= 1 and max(brightness) < 32:
        return True
    return False


def _is_wayland_session() -> bool:
    session = (os.environ.get("XDG_SESSION_TYPE") or "").lower()
    return session == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def _capture_hint(display: str) -> str:
    if _is_wayland_session():
        return (
            f"Session is Wayland (DISPLAY={display} is XWayland). "
            "Use driver-level capture (DRM/fbdev via `video` group) or vdisplay virtual framebuffer. "
            "Portal is opt-in: VDISPLAY_CAPTURE_ALLOW_PORTAL=1."
        )
    return f"Verify DISPLAY={display}; driver chain tries DRM, fbdev, mss, scrot, xwd."


def _crop_png(full_png: bytes, region: tuple[int, int, int, int]) -> bytes:
    try:
        from PIL import Image
    except ImportError as exc:
        raise VDisplayError("monitor crop requires Pillow") from exc

    x, y, width, height = region
    image = Image.open(io.BytesIO(full_png))
    left = max(0, min(x, image.width))
    top = max(0, min(y, image.height))
    right = max(left + 1, min(x + width, image.width))
    bottom = max(top + 1, min(y + height, image.height))
    cropped = image.crop((left, top, right, bottom))
    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    return buf.getvalue()


def _capture_full_display_png(display: str) -> bytes:
    from .providers.engine import capture_full_png

    return capture_full_png(display).png


def capture_display_png(
    display: str,
    *,
    region: tuple[int, int, int, int] | None = None,
) -> bytes:
    """Capture display as PNG via driver-level provider chain."""
    from .providers.engine import capture_full_png, capture_region_png

    if region is not None:
        return capture_region_png(display, region).png
    return capture_full_png(display).png


def _capture_xwd_png(display: str) -> bytes:
    require_command("xwd")
    xwd_data = run_command_bytes(
        ["xwd", "-root", "-display", display],
        env={"DISPLAY": display},
        timeout=60,
    )
    return xwd_bytes_to_png(xwd_data)


def _capture_scrot_png(
    display: str,
    region: tuple[int, int, int, int] | None,
) -> bytes:
    require_command("scrot")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        args = ["scrot", "-o"]
        if region is not None:
            x, y, width, height = region
            args.extend(["-a", f"{x},{y},{width},{height}"])
        args.append(str(tmp_path))
        result = run_command(
            args,
            env={"DISPLAY": display},
            text=False,
            check=False,
            timeout=60,
        )
        data = tmp_path.read_bytes() if tmp_path.exists() else b""
        if result.returncode != 0 or not _is_valid_png(data):
            return b""
        return data
    finally:
        tmp_path.unlink(missing_ok=True)


def _capture_gnome_screenshot_png() -> bytes:
    require_command("gnome-screenshot")
    from .portal_screencast import ensure_portal_session_env

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    env = os.environ.copy()
    env.update(ensure_portal_session_env())
    try:
        result = run_command(
            ["gnome-screenshot", "-f", str(tmp_path)],
            env=env,
            timeout=12,
            text=False,
            check=False,
        )
        data = tmp_path.read_bytes() if tmp_path.is_file() else b""
        if result.returncode != 0 or not _is_valid_png(data):
            err = ""
            if hasattr(result, "stderr") and result.stderr:
                err = result.stderr.decode("utf-8", errors="replace").strip()[:200]
            raise VDisplayError(f"gnome-screenshot failed{': ' + err if err else ''}")
        return data
    finally:
        tmp_path.unlink(missing_ok=True)


def _capture_portal_png(*, interactive: bool) -> bytes:
    return capture_portal_png(interactive=interactive, timeout_s=20.0)


def _capture_grim_png() -> bytes:
    require_command("grim")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        result = run_command(
            ["grim", str(tmp_path)],
            env=os.environ.copy(),
            timeout=30,
            text=False,
            check=False,
        )
        data = tmp_path.read_bytes() if tmp_path.is_file() else b""
        if result.returncode != 0 or not _is_valid_png(data):
            raise VDisplayError("grim failed (GNOME needs portal/gnome-screenshot, not grim)")
        return data
    finally:
        tmp_path.unlink(missing_ok=True)


def xwd_bytes_to_png(data: bytes) -> bytes:
    rgb = _xwd_to_rgb_bytes(data)
    width, height = _xwd_dimensions(data)
    return _rgb_to_png(rgb, width, height)


def _xwd_dimensions(data: bytes) -> tuple[int, int]:
    header = _parse_xwd_header(data)
    return header["pixmap_width"], header["pixmap_height"]


def _xwd_to_rgb_bytes(data: bytes) -> bytes:
    stream = io.BytesIO(data)
    header = _read_xwd_header(stream)
    if header["pixmap_format"] != ZPIXMAP:
        raise VDisplayError("Only ZPixmap XWD captures are supported")

    extra = header["header_size"] - 100
    if extra > 0:
        stream.read(extra)

    if header["ncolors"] > 0 and header["pixmap_depth"] <= 8:
        stream.read(header["ncolors"] * 12)

    pixels = stream.read()
    expected = header["bytes_per_line"] * header["pixmap_height"]
    if len(pixels) < expected:
        raise VDisplayError("XWD pixel data is truncated")

    return _decode_pixels(header, pixels[:expected])


def _parse_xwd_header(data: bytes) -> dict[str, int]:
    if len(data) < 100:
        raise VDisplayError("XWD data too short")
    fields = struct.unpack(">25I", data[:100])
    if fields[1] != XWD_VERSION:
        raise VDisplayError(f"Unsupported XWD version: {fields[1]}")
    return _header_fields(fields)


def _read_xwd_header(stream: BinaryIO) -> dict[str, int]:
    raw = stream.read(100)
    if len(raw) != 100:
        raise VDisplayError("Invalid XWD header")
    return _header_fields(struct.unpack(">25I", raw))


def _header_fields(fields: tuple[int, ...]) -> dict[str, int]:
    return {
        "header_size": fields[0],
        "version": fields[1],
        "pixmap_format": fields[2],
        "pixmap_depth": fields[3],
        "pixmap_width": fields[4],
        "pixmap_height": fields[5],
        "byte_order": fields[7],
        "bits_per_pixel": fields[11],
        "bytes_per_line": fields[12],
        "ncolors": fields[18],
    }


def _decode_pixels(header: dict[str, int], pixels: bytes) -> bytes:
    width = header["pixmap_width"]
    height = header["pixmap_height"]
    bpp = header["bits_per_pixel"]
    depth = header["pixmap_depth"]
    stride = header["bytes_per_line"]
    little_endian = header["byte_order"] == LSB_FIRST

    rgb = bytearray(width * height * 3)
    out = 0

    for y in range(height):
        row_start = y * stride
        row = pixels[row_start : row_start + stride]
        x_offset = 0
        for _x in range(width):
            if bpp == 32:
                if little_endian:
                    b, g, r, _a = row[x_offset : x_offset + 4]
                else:
                    _a, r, g, b = row[x_offset : x_offset + 4]
                x_offset += 4
            elif bpp == 24:
                if little_endian:
                    b, g, r = row[x_offset : x_offset + 3]
                else:
                    r, g, b = row[x_offset : x_offset + 3]
                x_offset += 3
            elif bpp == 16 and depth == 16:
                value = struct.unpack_from("<H" if little_endian else ">H", row, x_offset)[0]
                r = ((value >> 10) & 0x1F) * 255 // 31
                g = ((value >> 5) & 0x1F) * 255 // 31
                b = (value & 0x1F) * 255 // 31
                x_offset += 2
            elif bpp == 8 and depth == 8:
                index = row[x_offset]
                r = g = b = index
                x_offset += 1
            else:
                raise VDisplayError(
                    f"Unsupported XWD pixel format: depth={depth}, bpp={bpp}"
                )

            rgb[out : out + 3] = bytes((r, g, b))
            out += 3

    return bytes(rgb)


def _rgb_to_png(rgb: bytes, width: int, height: int) -> bytes:
    try:
        from PIL import Image
    except ImportError:
        return _rgb_to_png_minimal(rgb, width, height)

    image = Image.frombytes("RGB", (width, height), rgb)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _rgb_to_png_minimal(rgb: bytes, width: int, height: int) -> bytes:
    raw_rows = b"".join(b"\x00" + rgb[y * width * 3 : (y + 1) * width * 3] for y in range(height))
    compressed = zlib.compress(raw_rows, level=6)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )

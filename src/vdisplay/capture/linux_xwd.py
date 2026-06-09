from __future__ import annotations

import io
import struct
import zlib
from typing import BinaryIO

from ..exceptions import VDisplayError
from ..utils import require_command, run_command_bytes

XWD_VERSION = 7
ZPIXMAP = 2
LSB_FIRST = 0


def capture_display_png(display: str) -> bytes:
    require_command("xwd")
    xwd_data = run_command_bytes(
        ["xwd", "-root", "-display", display],
        env={"DISPLAY": display},
        timeout=60,
    )
    return xwd_bytes_to_png(xwd_data)


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

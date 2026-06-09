import struct

import pytest

from vdisplay.capture.linux_xwd import xwd_bytes_to_png


def _make_xwd(width: int, height: int, pixels: bytes) -> bytes:
    header = [0] * 25
    header[0] = 100
    header[1] = 7
    header[2] = 2
    header[3] = 24
    header[4] = width
    header[5] = height
    header[7] = 0
    header[11] = 32
    header[12] = width * 4
    header[18] = 0
    return struct.pack(">25I", *header) + pixels


def test_xwd_to_png_red_pixel():
    pixels = bytes([0, 0, 255, 0])  # BGRx
    data = _make_xwd(1, 1, pixels)
    png = xwd_bytes_to_png(data)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_xwd_to_png_2x1():
    pixels = bytes(
        [
            0,
            0,
            255,
            0,
            0,
            255,
            0,
            0,
        ]
    )
    data = _make_xwd(2, 1, pixels)
    png = xwd_bytes_to_png(data)
    assert len(png) > 32

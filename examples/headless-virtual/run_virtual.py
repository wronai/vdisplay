#!/usr/bin/env python3
"""Headless virtual display example — no host X11 required."""

from __future__ import annotations

import os
from pathlib import Path

from vdisplay import VirtualDisplaySession


def main() -> None:
    output_dir = Path(os.environ.get("VD_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "screen.png"

    width = int(os.environ.get("VD_WIDTH", "1280"))
    height = int(os.environ.get("VD_HEIGHT", "720"))
    display = os.environ.get("VD_DISPLAY", ":99")

    session = VirtualDisplaySession.create(width=width, height=height, display=display)
    session.start()
    try:
        path = session.save_screenshot(str(out_file))
        info = session.info()
        print(f"saved: {path}")
        print(f"display: {info['metadata']['display']}")
        print(f"size: {info['width']}x{info['height']}")
    finally:
        session.stop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""CI-style agent: virtual display + optional app launch + frame capture."""

from __future__ import annotations

import os
import shlex
import time
from pathlib import Path

from vdisplay import VirtualDisplaySession


def main() -> None:
    output_dir = Path(os.environ.get("VD_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = int(os.environ.get("VD_FRAMES", "3"))
    width = int(os.environ.get("VD_WIDTH", "1920"))
    height = int(os.environ.get("VD_HEIGHT", "1080"))
    display = os.environ.get("VD_DISPLAY", ":99")
    launch_cmd = os.environ.get("VD_LAUNCH", "").strip()

    session = VirtualDisplaySession.create(width=width, height=height, display=display)
    session.start()
    try:
        if launch_cmd:
            cmd = shlex.split(launch_cmd)
            pid = session.launch(cmd)
            print(f"launched: {cmd} (pid={pid})")
            time.sleep(1.0)

        for i in range(frames):
            path = output_dir / f"frame-{i:03d}.png"
            session.save_screenshot(str(path))
            print(f"frame {i}: {path}")
            time.sleep(0.5)
    finally:
        session.stop()


if __name__ == "__main__":
    main()

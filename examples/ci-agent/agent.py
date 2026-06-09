#!/usr/bin/env python3
"""CI-style agent: virtual display + optional app launch + frame capture."""

from __future__ import annotations

import json
import os
import shlex
import time
from pathlib import Path

from vdisplay import VirtualDisplaySession


def _load_common() -> None:
    import sys
    from pathlib import Path

    here = Path(__file__).resolve()
    for base in (here.parent, here.parent.parent, Path("/app")):
        for common in (base / "common", base / "examples" / "common"):
            if (common / "screenshot_meta.py").exists():
                sys.path.insert(0, str(common))
                return
    raise ImportError("examples/common not found")


_load_common()
from screenshot_meta import print_artifact, write_screenshot_meta  # noqa: E402


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
        launched = None
        if launch_cmd:
            cmd = shlex.split(launch_cmd)
            pid = session.launch(cmd)
            launched = {"command": cmd, "pid": pid}
            print(json.dumps({"launched": launched}, indent=2))
            time.sleep(1.0)

        info = session.info()
        for i in range(frames):
            path = output_dir / f"frame-{i:03d}.png"
            saved = session.save_screenshot(str(path))
            meta = write_screenshot_meta(
                saved,
                label=f"CI agent frame {i}",
                session_kind="virtual",
                display=info["metadata"]["display"],
                phase=f"frame_{i:03d}",
                session_info=info,
                extra={"frame_index": i, "launch": launched},
            )
            print_artifact(meta)
            time.sleep(0.5)
    finally:
        session.stop()


if __name__ == "__main__":
    main()

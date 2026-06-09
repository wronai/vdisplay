#!/usr/bin/env python3
"""Headless virtual display example — no host X11 required."""

from __future__ import annotations

import json
import os
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
    out_file = output_dir / "screen.png"

    width = int(os.environ.get("VD_WIDTH", "1280"))
    height = int(os.environ.get("VD_HEIGHT", "720"))
    display = os.environ.get("VD_DISPLAY", ":99")

    session = VirtualDisplaySession.create(width=width, height=height, display=display)
    session.start()
    try:
        path = session.save_screenshot(str(out_file))
        info = session.info()
        meta = write_screenshot_meta(
            path,
            label="Headless virtual display baseline capture",
            session_kind="virtual",
            display=info["metadata"]["display"],
            phase="baseline",
            session_info=info,
            extra={
                "expected_width": width,
                "expected_height": height,
            },
        )
        print_artifact(meta)
        print(json.dumps({"saved": path, "info": info}, indent=2))
    finally:
        session.stop()


if __name__ == "__main__":
    main()

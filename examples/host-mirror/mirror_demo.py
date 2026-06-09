#!/usr/bin/env python3
"""Mirror host display inside Docker (requires host X11 socket)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from vdisplay import MirrorSession
from vdisplay.discovery import diagnose_display, list_monitors
from vdisplay.exceptions import VDisplayError
from vdisplay.payloads import all_payload


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
    out_file = output_dir / "mirror.png"

    source = os.environ.get("VD_SOURCE", "primary")
    target = os.environ.get("VD_TARGET") or None
    display = os.environ.get("DISPLAY")

    diag = diagnose_display(display)
    print(json.dumps({"display": display, "source": source, "target": target, "diagnostic": diag}))

    resolved = diag["resolved_display"]
    monitors = list_monitors(resolved)
    if len(monitors) < 2:
        raise VDisplayError(
            f"Mirror needs at least two monitors on {resolved}, found {len(monitors)}: "
            f"{[o['name'] for o in monitors]}. "
            f"Hint: {diag.get('hint') or 'run vdisplay monitors and set VD_TARGET to a connected monitor'}"
        )

    state = all_payload(resolved)
    session = MirrorSession.create(source=source, target=target, display=resolved)
    session.start()
    try:
        path = session.save_screenshot(str(out_file))
        info = session.info()
        meta = write_screenshot_meta(
            path,
            label="Host mirror capture after xrandr same-as",
            session_kind="mirror",
            display=resolved,
            phase="after_mirror",
            session_info=info,
            monitors=state.get("monitors"),
            windows=state.get("windows"),
            state=state,
            extra={"source": source, "target": target},
        )
        print_artifact(meta)
        payload = {
            "saved": path,
            "info": info,
            "capabilities": session.capabilities(),
        }
        print(json.dumps(payload, indent=2))
    finally:
        session.stop()


if __name__ == "__main__":
    try:
        main()
    except VDisplayError as exc:
        print(f"error: {exc}")
        raise SystemExit(1) from exc

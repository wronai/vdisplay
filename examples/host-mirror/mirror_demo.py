#!/usr/bin/env python3
"""Mirror host display inside Docker (requires host X11 socket)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from vdisplay import MirrorSession
from vdisplay.discovery import diagnose_display, list_outputs
from vdisplay.exceptions import VDisplayError


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
    outputs = list_outputs(resolved)
    if len(outputs) < 2:
        raise VDisplayError(
            f"Mirror needs at least two outputs on {resolved}, found {len(outputs)}: "
            f"{[o['name'] for o in outputs]}. "
            f"Hint: {diag.get('hint') or 'use ./run.sh and set VD_TARGET to a connected output'}"
        )

    session = MirrorSession.create(source=source, target=target, display=resolved)
    session.start()
    try:
        path = session.save_screenshot(str(out_file))
        payload = {
            "saved": path,
            "info": session.info(),
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

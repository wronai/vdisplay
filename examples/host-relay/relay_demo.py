#!/usr/bin/env python3
"""Relay window off-screen and back (requires host X11 socket)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from vdisplay import WindowRelaySession
from vdisplay.capture.linux_xwd import capture_display_png
from vdisplay.discovery import resolve_host_display
from vdisplay.exceptions import VDisplayError
from vdisplay.payloads import all_payload, windows_payload


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
from screenshot_meta import print_artifact, save_png_with_meta  # noqa: E402


def _capture_phase(
    output_dir: Path,
    *,
    display: str,
    phase: str,
    label: str,
) -> dict:
    state = all_payload(display)
    png = capture_display_png(display)
    path = output_dir / f"{phase}.png"
    meta = save_png_with_meta(
        path,
        png,
        label=label,
        session_kind="relay",
        display=display,
        phase=phase,
        monitors=state.get("monitors"),
        windows=state.get("windows"),
        state=state,
    )
    print_artifact(meta)
    return meta


def main() -> None:
    title = os.environ.get("WINDOW_TITLE") or None
    app = os.environ.get("WINDOW_APP") or None
    target = os.environ.get("VD_TARGET", "offscreen")
    display = resolve_host_display(os.environ.get("DISPLAY"))
    output_dir = Path(os.environ.get("VD_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    if not title and not app:
        windows = windows_payload(display, include_all=True).get("windows", [])
        apps = [
            w
            for w in windows
            if w.get("type") == "application" and not w.get("is_internal")
        ]
        if apps:
            app = str(apps[0].get("app_label") or apps[0].get("process_name") or "")
        else:
            raise VDisplayError(
                "No WINDOW_TITLE/WINDOW_APP set and no XWayland application windows found. "
                "Set WINDOW_APP=JetBrains or launch an X11/XWayland app first."
            )

    print(
        json.dumps(
            {
                "display": display,
                "window_title": title,
                "window_app": app,
                "target": target,
            },
            indent=2,
        )
    )

    _capture_phase(
        output_dir,
        display=display,
        phase="before_automation",
        label="Host desktop before relay automation",
    )

    session = WindowRelaySession.create(display=display)
    session.start()
    try:
        wid = session.adopt_window(
            match_title=title,
            match_app=app,
            target=target,
        )
        print(json.dumps({"adopted": wid, "windows": session.list_adopted()}, indent=2))

        _capture_phase(
            output_dir,
            display=display,
            phase="after_adopt",
            label="Host desktop after adopt-window",
        )

        time.sleep(1.0)
        session.release_window(window_id=wid)
        print(json.dumps({"released": wid, "windows": session.list_adopted()}, indent=2))

        _capture_phase(
            output_dir,
            display=display,
            phase="after_release",
            label="Host desktop after release-window",
        )
    finally:
        session.stop()


if __name__ == "__main__":
    try:
        main()
    except VDisplayError as exc:
        print(f"error: {exc}")
        raise SystemExit(1) from exc

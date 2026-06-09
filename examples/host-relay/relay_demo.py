#!/usr/bin/env python3
"""Relay window off-screen and back (requires host X11 socket)."""

from __future__ import annotations

import json
import os
import time

from vdisplay import WindowRelaySession
from vdisplay.exceptions import VDisplayError


def main() -> None:
    title = os.environ.get("WINDOW_TITLE", "xterm")
    target = os.environ.get("VD_TARGET", "offscreen")
    display = os.environ.get("DISPLAY")

    print(json.dumps({"display": display, "window_title": title, "target": target}))

    session = WindowRelaySession.create(display=display)
    session.start()
    try:
        wid = session.adopt_window(match_title=title, target=target)
        print(json.dumps({"adopted": wid, "windows": session.list_adopted()}, indent=2))
        time.sleep(2.0)
        session.release_window(window_id=wid)
        print(json.dumps({"released": wid, "windows": session.list_adopted()}, indent=2))
    finally:
        session.stop()


if __name__ == "__main__":
    try:
        main()
    except VDisplayError as exc:
        print(f"error: {exc}")
        raise SystemExit(1) from exc

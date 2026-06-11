"""Start portal ScreenCast through the long-lived vdisplay-agent broker."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from ...capture.portal_screencast import portal_session_env_status
from ...exceptions import VDisplayError

_COOLDOWN_FILE = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}") / "vdisplay-screencast-last-start"
_LOCAL_START_COOLDOWN_S = max(
    30.0,
    float(os.environ.get("VDISPLAY_SCREENCAST_LOCAL_START_COOLDOWN_S", "300")),
)


def _local_start_cooldown_remaining() -> float:
    try:
        last = float(_COOLDOWN_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0.0
    elapsed = time.time() - last
    return max(0.0, _LOCAL_START_COOLDOWN_S - elapsed)


def _mark_local_start_attempt() -> None:
    try:
        _COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
        _COOLDOWN_FILE.write_text(str(time.time()), encoding="utf-8")
    except OSError:
        pass


def start_screencast_via_agent(
    client,
    *,
    interactive: bool = True,
    timeout_s: float = 120.0,
    multiple: bool | None = None,
) -> dict[str, Any]:
    """Run ScreenCast inside vdisplay-agent (portal session must live in the broker)."""
    status = client.screencast_status()
    if status.get("active") and status.get("ready"):
        return {**status, "ok": True, "reused": True}

    remaining = _local_start_cooldown_remaining()
    if remaining > 0 and interactive:
        raise VDisplayError(
            "screencast not ready — restart vdisplay-agent serve from a local GUI terminal, "
            f"then run: vdisplay agent screencast start "
            f"(portal retry blocked for {int(remaining)}s to avoid repeated permission prompts)"
        )

    ok, hint = portal_session_env_status()
    if not ok:
        raise VDisplayError(
            f"{hint} Restart vdisplay-agent serve from the same desktop terminal, then retry."
        )

    _mark_local_start_attempt()
    return client.start_screencast(
        interactive=interactive,
        timeout_s=timeout_s,
        multiple=multiple,
    )

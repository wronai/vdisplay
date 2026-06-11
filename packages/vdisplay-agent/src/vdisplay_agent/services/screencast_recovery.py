"""Auto-start portal ScreenCast when host capture finds no active session."""

from __future__ import annotations

import os
import time

from vdisplay.exceptions import VDisplayError

from ..session_store import SessionStore

_LAST_RECOVERY_ATTEMPT_MONO: float = 0.0
_RECOVERY_COOLDOWN_S = max(
    30.0,
    float(os.environ.get("VDISPLAY_SCREENCAST_RECOVERY_COOLDOWN_S", "300")),
)


def is_recoverable_screencast_error(exc: VDisplayError) -> bool:
    lowered = str(exc).lower()
    return any(
        token in lowered
        for token in (
            "blank frame",
            "stale screencast",
            "no active session",
            "screencast capture blank",
            "target not found",
        )
    )


def screencast_recovery_cooldown_remaining() -> float:
    """Seconds until another automatic screencast recovery is allowed."""
    elapsed = time.monotonic() - _LAST_RECOVERY_ATTEMPT_MONO
    return max(0.0, _RECOVERY_COOLDOWN_S - elapsed)


def _mark_recovery_attempt() -> None:
    global _LAST_RECOVERY_ATTEMPT_MONO
    _LAST_RECOVERY_ATTEMPT_MONO = time.monotonic()


def try_recover_screencast(
    store: SessionStore,
    *,
    interactive_preferred: bool = False,
    allow_recovery: bool = True,
) -> bool:
    """Try to restore host capture without spamming portal consent dialogs."""
    if not allow_recovery:
        return False

    remaining = screencast_recovery_cooldown_remaining()
    if remaining > 0:
        return False

    from . import sessions as session_svc

    _mark_recovery_attempt()
    # Agent-side recovery must never open interactive portal dialogs — that belongs
    # in the user's GUI terminal: `vdisplay agent screencast start`.
    order = (False,) if not interactive_preferred else (False, True)
    for interactive in order:
        try:
            payload = session_svc.start_screencast(
                store,
                interactive=interactive,
                timeout_s=30.0,
            )
        except VDisplayError:
            continue
        if payload.get("ready") or payload.get("active"):
            return True
    return False

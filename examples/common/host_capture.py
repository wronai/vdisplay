"""Host screenshot helper for example scripts (agent-aware on Wayland)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def capture_host_screenshot(
    path: str | Path,
    *,
    display: str | None = None,
    source: str | None = None,
    target: str | None = None,
    monitor: int = 1,
    mode: str = "host",
) -> dict[str, Any]:
    """Capture host desktop PNG; routes via vdisplay-agent when available."""
    from vdisplay.application.services.capture import capture_screenshot

    return capture_screenshot(
        output=str(path),
        display=display,
        source=source,
        target=target,
        monitor=monitor,
        mode=mode,
        skip_img2nl=True,
    )

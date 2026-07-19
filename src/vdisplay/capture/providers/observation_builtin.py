"""Stable public imports for VDisplay's built-in observation providers."""

from .observation_cli import (
    CliToolsObservationProvider,
    GrimObservationProvider,
    command_candidates,
    run_png_command,
)
from .observation_mss import BlackFrameError, MssObservationProvider
from .observation_portal import (
    PortalScreenCastObservationProvider,
    PortalScreenshotObservationProvider,
)

__all__ = [
    "BlackFrameError",
    "CliToolsObservationProvider",
    "GrimObservationProvider",
    "MssObservationProvider",
    "PortalScreenCastObservationProvider",
    "PortalScreenshotObservationProvider",
    "command_candidates",
    "run_png_command",
]

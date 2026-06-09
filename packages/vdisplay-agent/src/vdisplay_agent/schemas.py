"""Frozen agent HTTP route → action mapping."""

from __future__ import annotations

from typing import Final

# Query routes
ACTION_HEALTH: Final = "health"
ACTION_CAPABILITIES: Final = "capabilities"
ACTION_DIAGNOSTICS: Final = "diagnostics"
ACTION_OUTPUTS: Final = "outputs"
ACTION_WINDOWS: Final = "windows"

# Session routes
ACTION_VIRTUAL_START: Final = "virtual_start"
ACTION_MIRROR_START: Final = "mirror_start"
ACTION_RELAY_START: Final = "relay_start"
ACTION_SCREENCAST_START: Final = "screencast_start"
ACTION_SCREENCAST_STOP: Final = "screencast_stop"
ACTION_SCREENCAST_STATUS: Final = "screencast_status"
ACTION_SESSION_STOP: Final = "session_stop"

# Mutation routes
ACTION_CAPTURE_FRAME: Final = "capture_frame"
ACTION_WINDOW_ADOPT: Final = "window_adopt"
ACTION_WINDOW_RELEASE: Final = "window_release"

AGENT_ROUTES: Final = {
    "GET /health": ACTION_HEALTH,
    "GET /capabilities": ACTION_CAPABILITIES,
    "GET /diagnostics": ACTION_DIAGNOSTICS,
    "GET /outputs": ACTION_OUTPUTS,
    "GET /windows": ACTION_WINDOWS,
    "POST /session/virtual/start": ACTION_VIRTUAL_START,
    "POST /session/mirror/start": ACTION_MIRROR_START,
    "POST /session/relay/start": ACTION_RELAY_START,
    "POST /session/screencast/start": ACTION_SCREENCAST_START,
    "POST /session/screencast/stop": ACTION_SCREENCAST_STOP,
    "GET /session/screencast/status": ACTION_SCREENCAST_STATUS,
    "POST /session/{session_id}/stop": ACTION_SESSION_STOP,
    "POST /capture/frame": ACTION_CAPTURE_FRAME,
    "POST /window/adopt": ACTION_WINDOW_ADOPT,
    "POST /window/release": ACTION_WINDOW_RELEASE,
}

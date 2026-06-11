"""Frozen agent HTTP route → action mapping."""

from __future__ import annotations

from typing import Final

# Query routes
ACTION_HEALTH: Final = "health"
ACTION_VERSION: Final = "version"
ACTION_CAPABILITIES: Final = "capabilities"
ACTION_DIAGNOSTICS: Final = "diagnostics"
ACTION_OUTPUTS: Final = "outputs"
ACTION_WINDOWS: Final = "windows"

# Session routes
ACTION_VIRTUAL_START: Final = "virtual_start"
ACTION_MIRROR_START: Final = "mirror_start"
ACTION_RELAY_START: Final = "relay_start"
ACTION_TERMINAL_START: Final = "terminal_start"
ACTION_BROWSER_START: Final = "browser_start"
ACTION_SCREENCAST_START: Final = "screencast_start"
ACTION_SCREENCAST_ADOPT: Final = "screencast_adopt"
ACTION_SCREENCAST_STOP: Final = "screencast_stop"
ACTION_SCREENCAST_STATUS: Final = "screencast_status"
ACTION_SESSION_STOP: Final = "session_stop"
ACTION_SESSIONS_LIST: Final = "sessions_list"

# Task routes (PR-11)
ACTION_TASKS_LIST: Final = "tasks_list"
ACTION_TASK_GET: Final = "task_get"
ACTION_TASK_HEARTBEAT: Final = "task_heartbeat"
ACTION_TASK_STOP: Final = "task_stop"

# Mutation routes
ACTION_SAMPLER_START: Final = "sampler_start"
ACTION_SAMPLER_STOP: Final = "sampler_stop"
ACTION_SAMPLER_STATUS: Final = "sampler_status"
ACTION_CAPTURE_FRAME: Final = "capture_frame"
ACTION_WINDOW_ADOPT: Final = "window_adopt"
ACTION_WINDOW_RELEASE: Final = "window_release"

# Control routes
ACTION_CONTROL_PLUGINS: Final = "control_plugins"
ACTION_CONTROL_DIAGNOSTICS: Final = "control_diagnostics"
ACTION_CONTROLS_LIST: Final = "controls_list"
ACTION_CONTROLS_FIND: Final = "controls_find"
ACTION_CONTROL_INVOKE: Final = "control_invoke"
ACTION_CONTROL_FOCUS: Final = "control_focus"
ACTION_CONTROL_SET_VALUE: Final = "control_set_value"

ACTION_WEB_OVERVIEW: Final = "web_overview"
ACTION_WEB_FRAMES: Final = "web_frames"
ACTION_WEB_REPLAY_SESSIONS: Final = "web_replay_sessions"
ACTION_WEB_REPLAY_START: Final = "web_replay_start"
ACTION_WEB_REPLAY_STATUS: Final = "web_replay_status"
ACTION_WEB_POINTER_CLICK: Final = "web_pointer_click"

AGENT_ROUTES: Final = {
    "GET /health": ACTION_HEALTH,
    "GET /version": ACTION_VERSION,
    "GET /capabilities": ACTION_CAPABILITIES,
    "GET /diagnostics": ACTION_DIAGNOSTICS,
    "GET /outputs": ACTION_OUTPUTS,
    "GET /windows": ACTION_WINDOWS,
    "POST /session/virtual/start": ACTION_VIRTUAL_START,
    "POST /session/mirror/start": ACTION_MIRROR_START,
    "POST /session/relay/start": ACTION_RELAY_START,
    "POST /session/terminal/open": ACTION_TERMINAL_START,
    "POST /session/browser/open": ACTION_BROWSER_START,
    "POST /session/screencast/start": ACTION_SCREENCAST_START,
    "POST /session/screencast/adopt": ACTION_SCREENCAST_ADOPT,
    "POST /session/screencast/stop": ACTION_SCREENCAST_STOP,
    "GET /session/screencast/status": ACTION_SCREENCAST_STATUS,
    "POST /session/{session_id}/stop": ACTION_SESSION_STOP,
    "GET /sessions": ACTION_SESSIONS_LIST,
    "GET /tasks": ACTION_TASKS_LIST,
    "GET /tasks/{task_id}": ACTION_TASK_GET,
    "POST /tasks/{task_id}/heartbeat": ACTION_TASK_HEARTBEAT,
    "POST /tasks/{task_id}/stop": ACTION_TASK_STOP,
    "POST /sampler/start": ACTION_SAMPLER_START,
    "POST /sampler/stop": ACTION_SAMPLER_STOP,
    "GET /sampler/status": ACTION_SAMPLER_STATUS,
    "POST /capture/frame": ACTION_CAPTURE_FRAME,
    "POST /window/adopt": ACTION_WINDOW_ADOPT,
    "POST /window/release": ACTION_WINDOW_RELEASE,
    "GET /control/plugins": ACTION_CONTROL_PLUGINS,
    "GET /diagnostics/control": ACTION_CONTROL_DIAGNOSTICS,
    "POST /controls/list": ACTION_CONTROLS_LIST,
    "POST /controls/find": ACTION_CONTROLS_FIND,
    "POST /control/invoke": ACTION_CONTROL_INVOKE,
    "POST /control/focus": ACTION_CONTROL_FOCUS,
    "POST /control/set-value": ACTION_CONTROL_SET_VALUE,
}

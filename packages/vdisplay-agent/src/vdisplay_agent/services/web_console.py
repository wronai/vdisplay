"""Aggregate broker state and on-demand monitor frames for the web console."""

from __future__ import annotations

from typing import Any

from ..runtime import AgentRuntime
from . import web_frame_cache, web_replay

capture_monitor_frame = web_frame_cache.capture_monitor_frame
capture_monitor_frame_with_meta = web_frame_cache.capture_monitor_frame_with_meta
capture_all_monitor_frames = web_frame_cache.capture_all_monitor_frames
list_replay_sessions = web_replay.list_replay_sessions
queue_replay = web_replay.queue_replay


def build_overview(runtime: AgentRuntime, *, display: str | None = None) -> dict[str, Any]:
    """Single payload for the web dashboard."""
    sampler = runtime.sampler_status()
    if not sampler.get("running"):
        sampler.setdefault("running", False)
    windows = runtime.list_windows(apps_only=True, min_width=80, min_height=80, display=display)
    return {
        "monitors": runtime.outputs(display=display, include_all=True),
        "screencast": runtime.screencast_status(),
        "sampler": sampler,
        "tasks": runtime.list_tasks(),
        "sessions": runtime.list_sessions(),
        "windows": windows,
        "capabilities": runtime.platform_capabilities(),
    }


def click_monitor_pointer(
    runtime: AgentRuntime,
    *,
    monitor_name: str,
    x: float,
    y: float,
    coord_space: str = "png",
    button: int = 1,
    display: str | None = None,
) -> dict[str, Any]:
    """Click on monitor image coordinates from the web console."""
    from vdisplay.application.services.web_pointer import pointer_click_at_monitor

    png_path, capture_meta = capture_monitor_frame_with_meta(
        runtime,
        monitor_name,
        display=display,
        use_cache=True,
    )
    return pointer_click_at_monitor(
        monitor_name=monitor_name,
        x=x,
        y=y,
        capture_meta=capture_meta,
        png_path=png_path,
        coord_space=coord_space,
        button=button,
        display=display,
    )

"""Typed observations from xdg-desktop-portal Screenshot and ScreenCast."""

from __future__ import annotations

import os
import shutil
from typing import Any

from ..observation import ScreenObservation
from ..portal import capture_portal_png
from ..portal_screencast import (
    get_active_screencast,
    portal_session_env_status,
    start_screencast_session,
)
from .observation import MonitorSpec, ProviderAvailability, screen_observation_from_png
from .observation_discovery import monitor_specs_from_discovery


class PortalScreenshotObservationProvider:
    name = "portal_screenshot"
    streams = False

    def availability(self) -> ProviderAvailability:
        if not os.environ.get("DBUS_SESSION_BUS_ADDRESS", "").strip():
            return ProviderAvailability(
                available=False,
                reason="no D-Bus session (portal unavailable)",
            )
        return ProviderAvailability(
            available=True,
            reason="xdg-desktop-portal Screenshot API",
            needs_consent=True,
            install_hint="Grant Screenshot in Settings → Privacy",
        )

    def list_monitors(self) -> list[MonitorSpec]:
        return monitor_specs_from_discovery()

    def capture_one(self, monitor_id: int | None, scale: float) -> ScreenObservation:
        del monitor_id, scale  # Screenshot returns one full-size desktop.
        return screen_observation_from_png(
            capture_portal_png(interactive=False),
            monitor_id=-1,
            scale=1.0,
            output="portal",
            provider=self.name,
        )

    def capture_all(self, scale: float) -> list[ScreenObservation]:
        return [self.capture_one(None, scale)]


def _stream_properties(session: Any, index: int) -> dict[str, Any]:
    streams = list(getattr(session, "streams", []) or [])
    if index >= len(streams) or not isinstance(streams[index], dict):
        return {}
    properties = streams[index].get("properties") or {}
    return dict(properties) if isinstance(properties, dict) else {}


def _stream_output(session: Any, index: int) -> str:
    targets = list(getattr(session, "stream_targets", []) or [])
    if index < len(targets) and str(targets[index]).strip():
        return str(targets[index]).strip()
    properties = _stream_properties(session, index)
    return str(properties.get("id") or f"monitor-{index}")


def _active_or_new_screencast() -> Any:
    session = get_active_screencast()
    if session is not None and bool(getattr(session, "is_ready", False)):
        return session
    return start_screencast_session(interactive=True, multiple=True)


class PortalScreenCastObservationProvider:
    name = "portal_screencast"
    streams = True

    def availability(self) -> ProviderAvailability:
        available, reason = portal_session_env_status()
        if not available:
            return ProviderAvailability(available=False, reason=reason)
        if shutil.which("gst-launch-1.0") is None:
            return ProviderAvailability(
                available=False,
                reason="gst-launch-1.0 not found",
                install_hint="apt install gstreamer1.0-tools gstreamer1.0-pipewire",
            )
        session = get_active_screencast()
        ready = session is not None and bool(getattr(session, "is_ready", False))
        return ProviderAvailability(
            available=True,
            reason="active VDisplay ScreenCast session" if ready else "VDisplay portal ScreenCast",
            needs_consent=not ready,
            install_hint=(
                "persistent VDisplay session ready"
                if ready
                else "Accept screen sharing when capture starts VDisplay ScreenCast"
            ),
        )

    def list_monitors(self) -> list[MonitorSpec]:
        return monitor_specs_from_discovery()

    def capture_all(self, scale: float) -> list[ScreenObservation]:
        session = _active_or_new_screencast()
        node_ids = list(getattr(session, "node_ids", []) or [])
        if not node_ids:
            raise RuntimeError("portal_screencast: VDisplay session has no PipeWire streams")
        observations: list[ScreenObservation] = []
        errors: list[str] = []
        for index, node_id in enumerate(node_ids):
            try:
                observations.append(
                    screen_observation_from_png(
                        session.capture_png(node_index=index),
                        monitor_id=index,
                        scale=scale,
                        output=_stream_output(session, index),
                        provider=self.name,
                        capture_meta={
                            "session": "vdisplay",
                            "stream_index": index,
                            "node_id": int(node_id),
                        },
                    )
                )
            except Exception as exc:  # noqa: BLE001 - one stream must not hide the others.
                errors.append(f"stream {index}: {exc}")
        if not observations:
            raise RuntimeError(
                f"portal_screencast: {'; '.join(errors) if errors else 'no frames'}"
            )
        return observations

    def capture_one(self, monitor_id: int | None, scale: float) -> ScreenObservation:
        observations = self.capture_all(scale)
        if monitor_id is None:
            return observations[0]
        for observation in observations:
            if observation.monitor_id == monitor_id:
                return observation
        return observations[min(max(0, monitor_id), len(observations) - 1)]


__all__ = [
    "PortalScreenCastObservationProvider",
    "PortalScreenshotObservationProvider",
]

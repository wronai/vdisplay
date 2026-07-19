"""Typed multi-monitor observations captured through MSS."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..observation import ScreenObservation
from ..pixels import downscale_rgb_nearest, resolve_capture_scale, rgb_mostly_black
from .observation import MonitorSpec, ProviderAvailability


class BlackFrameError(RuntimeError):
    """Captured buffer is empty/black (common with XWayland + ``mss``)."""


def _ordered_monitor_indices(targets: list[dict[str, Any]]) -> list[int]:
    primary = [index for index, monitor in enumerate(targets) if monitor.get("is_primary")]
    rest = [index for index in range(len(targets)) if index not in primary]
    return primary + rest


def _observation_from_mss_shot(
    shot: Any,
    *,
    monitor_id: int,
    scale: float,
    output: str,
) -> ScreenObservation:
    import mss.tools

    if rgb_mostly_black(shot.rgb):
        raise BlackFrameError("monitor image is mostly black")
    src_width, src_height = shot.size
    scale_value = resolve_capture_scale(scale)
    dst_width = max(1, int(src_width * scale_value))
    dst_height = max(1, int(src_height * scale_value))
    rgb = downscale_rgb_nearest(
        shot.rgb,
        src_width,
        src_height,
        dst_width,
        dst_height,
    )
    payload = mss.tools.to_png(rgb, (dst_width, dst_height))
    return ScreenObservation.from_png(
        payload,
        monitor_id=monitor_id,
        captured_at=datetime.now(UTC).isoformat(),
        native_width=src_width,
        native_height=src_height,
        output=output,
        provider="mss",
    )


class MssObservationProvider:
    name = "mss"
    streams = False

    def availability(self) -> ProviderAvailability:
        try:
            import mss  # noqa: F401
        except ImportError:
            return ProviderAvailability(
                available=False,
                reason="mss not installed",
                install_hint="pip install mss",
            )
        return ProviderAvailability(available=True, reason="mss screen grabber")

    def list_monitors(self) -> list[MonitorSpec]:
        import mss

        with mss.mss() as grabber:
            return [
                MonitorSpec(
                    id=index,
                    output=str(
                        target.get("name")
                        or target.get("output")
                        or f"monitor-{index}"
                    ),
                    width=int(target.get("width", 0) or 0),
                    height=int(target.get("height", 0) or 0),
                    left=int(target.get("left", 0) or 0),
                    top=int(target.get("top", 0) or 0),
                    is_primary=bool(target.get("is_primary")),
                )
                for index, target in enumerate(grabber.monitors[1:])
            ]

    @staticmethod
    def _grab(grabber: Any, target: dict[str, Any], index: int, scale: float) -> ScreenObservation:
        return _observation_from_mss_shot(
            grabber.grab(target),
            monitor_id=index,
            scale=scale,
            output=str(target.get("output") or ""),
        )

    def capture_one(self, monitor_id: int | None, scale: float) -> ScreenObservation:
        import mss

        with mss.mss() as grabber:
            targets = [dict(monitor) for monitor in grabber.monitors[1:]]
            if not targets:
                raise RuntimeError("no monitors detected")
            if monitor_id is not None:
                index = max(0, min(monitor_id, len(targets) - 1))
                return self._grab(grabber, targets[index], index, scale)
            last_error: Exception | None = None
            for index in _ordered_monitor_indices(targets):
                try:
                    return self._grab(grabber, targets[index], index, scale)
                except BlackFrameError as exc:
                    last_error = exc
            raise RuntimeError(f"mss capture produced only black frames ({last_error})") from last_error

    def capture_all(self, scale: float) -> list[ScreenObservation]:
        import mss

        observations: list[ScreenObservation] = []
        with mss.mss() as grabber:
            targets = [dict(monitor) for monitor in grabber.monitors[1:]]
            for index, target in enumerate(targets):
                try:
                    observations.append(self._grab(grabber, target, index, scale))
                except Exception:  # noqa: BLE001 - one monitor must not hide the others.
                    continue
        if not observations:
            raise RuntimeError("all monitors returned black frames")
        return observations


__all__ = ["BlackFrameError", "MssObservationProvider"]

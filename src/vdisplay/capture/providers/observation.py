"""Typed observation-provider contract and deterministic fallback runner.

This layer owns capture *mechanics*.  Callers remain responsible for policy:
they pass providers in the exact order in which they should be attempted.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from ..observation import ScreenObservation, png_dimensions
from ..pixels import resolve_capture_scale


@dataclass(frozen=True)
class ProviderAvailability:
    available: bool
    reason: str = ""
    install_hint: str = ""
    needs_consent: bool = False


@dataclass(frozen=True)
class MonitorSpec:
    id: int
    output: str
    width: int
    height: int
    left: int = 0
    top: int = 0
    is_primary: bool = False


@runtime_checkable
class ObservationProvider(Protocol):
    """Provider returning the public :class:`ScreenObservation` contract."""

    name: str
    streams: bool

    def availability(self) -> ProviderAvailability: ...

    def list_monitors(self) -> list[MonitorSpec]: ...

    def capture_all(
        self, scale: float
    ) -> Sequence[ScreenObservation | Mapping[str, Any]]: ...

    def capture_one(
        self, monitor_id: int | None, scale: float
    ) -> ScreenObservation | Mapping[str, Any]: ...


@dataclass(frozen=True)
class ObservationProviderFailure:
    provider: str
    error: str


@dataclass(frozen=True)
class ObservationBatch:
    """Successful result plus the ordered failures that preceded it."""

    provider: str
    observations: tuple[ScreenObservation, ...]
    failures: tuple[ObservationProviderFailure, ...] = ()


class ObservationProviderChainError(RuntimeError):
    """Raised after every provider in an ordered chain failed."""

    def __init__(self, failures: Sequence[ObservationProviderFailure]) -> None:
        self.failures = tuple(failures)
        detail = "; ".join(
            f"{failure.provider}: {failure.error}" for failure in self.failures
        )
        super().__init__(f"no observation provider succeeded{'; ' + detail if detail else ''}")


def coerce_screen_observation(
    value: ScreenObservation | Mapping[str, Any],
) -> ScreenObservation:
    """Accept the public model or a one-release legacy descriptor mapping."""
    if isinstance(value, ScreenObservation):
        return value
    if isinstance(value, Mapping):
        return ScreenObservation.from_dict(value)
    raise TypeError(
        "observation provider returned "
        f"{type(value).__name__}, expected ScreenObservation or mapping"
    )


def screen_observation_from_png(
    payload: bytes,
    *,
    monitor_id: int,
    scale: float,
    output: str,
    provider: str,
    capture_meta: Mapping[str, Any] | None = None,
) -> ScreenObservation:
    """Build a scaled logical observation from PNG bytes.

    Command and portal backends commonly return only a full-size PNG.  The
    requested scale therefore describes the logical dimensions supplied to a
    downstream vision model; raw payload dimensions remain available through
    ``native_width`` and ``native_height``.
    """
    if not payload:
        raise RuntimeError(f"{provider}: empty image")
    native_width, native_height = png_dimensions(payload)
    if native_width <= 0 or native_height <= 0:
        raise RuntimeError(f"{provider}: invalid PNG dimensions")
    scale_value = resolve_capture_scale(scale)
    return ScreenObservation.from_png(
        payload,
        monitor_id=monitor_id,
        captured_at=datetime.now(UTC).isoformat(),
        width=max(1, int(native_width * scale_value)),
        height=max(1, int(native_height * scale_value)),
        output=output or provider,
        provider=provider,
        capture_meta=capture_meta or {},
    )


def capture_observations_with_fallback(
    providers: Sequence[ObservationProvider],
    *,
    scale: float,
    monitor_id: int | None = None,
    all_monitors: bool = False,
) -> ObservationBatch:
    """Try providers in caller-supplied order and return the first non-empty batch.

    The actual winning provider is stamped on every observation.  Failures are
    retained in stable attempt order so an orchestration layer can render its
    own operator-facing message without parsing exception text.
    """
    failures: list[ObservationProviderFailure] = []
    for provider in providers:
        try:
            raw = (
                provider.capture_all(scale)
                if all_monitors
                else [provider.capture_one(monitor_id, scale)]
            )
            observations = tuple(coerce_screen_observation(item) for item in raw)
            if not observations:
                raise RuntimeError("no observations")
        except Exception as exc:  # noqa: BLE001 - fallback is the contract.
            failures.append(
                ObservationProviderFailure(
                    provider=str(provider.name),
                    error=str(exc) or type(exc).__name__,
                )
            )
            continue
        stamped = tuple(
            replace(observation, provider=str(provider.name))
            for observation in observations
        )
        return ObservationBatch(
            provider=str(provider.name),
            observations=stamped,
            failures=tuple(failures),
        )
    raise ObservationProviderChainError(failures)


__all__ = [
    "MonitorSpec",
    "ObservationBatch",
    "ObservationProvider",
    "ObservationProviderChainError",
    "ObservationProviderFailure",
    "ProviderAvailability",
    "capture_observations_with_fallback",
    "coerce_screen_observation",
    "screen_observation_from_png",
]

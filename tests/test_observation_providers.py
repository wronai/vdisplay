from __future__ import annotations

import struct
from types import SimpleNamespace
from unittest import mock

import pytest

from vdisplay.capture import (
    CliToolsObservationProvider,
    MssObservationProvider,
    ObservationProviderChainError,
    PortalScreenCastObservationProvider,
    ScreenObservation,
    capture_observations_with_fallback,
)


def _png(width: int = 4, height: int = 3) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", width, height)


def _observation(provider: str = "producer") -> ScreenObservation:
    return ScreenObservation.from_png(
        _png(),
        monitor_id=0,
        captured_at="2026-07-19T00:00:00+00:00",
        output="DP-1",
        provider=provider,
    )


class _Provider:
    streams = False

    def __init__(self, name: str, result=None, error: Exception | None = None) -> None:
        self.name = name
        self.result = result
        self.error = error

    def capture_one(self, monitor_id, scale):
        del monitor_id, scale
        if self.error:
            raise self.error
        return self.result

    def capture_all(self, scale):
        del scale
        if self.error:
            raise self.error
        return self.result


def test_fallback_records_order_and_stamps_actual_provider() -> None:
    legacy = _observation("legacy").to_descriptor()
    result = capture_observations_with_fallback(
        [
            _Provider("first", error=RuntimeError("black frame")),
            _Provider("second", result=legacy),
        ],
        scale=0.2,
    )

    assert result.provider == "second"
    assert result.observations[0].provider == "second"
    assert [(item.provider, item.error) for item in result.failures] == [
        ("first", "black frame")
    ]


def test_all_monitor_fallback_rejects_empty_batches() -> None:
    with pytest.raises(ObservationProviderChainError) as caught:
        capture_observations_with_fallback(
            [_Provider("empty", result=[]), _Provider("broken", error=ValueError("nope"))],
            scale=1.0,
            all_monitors=True,
        )

    assert [failure.provider for failure in caught.value.failures] == ["empty", "broken"]
    assert "empty: no observations" in str(caught.value)


def test_mss_provider_returns_typed_scaled_observation(monkeypatch) -> None:
    pytest.importorskip("mss")
    shot = SimpleNamespace(
        rgb=bytes([10, 20, 30] * 100),
        size=(10, 10),
    )
    grabber = mock.MagicMock()
    grabber.monitors = [
        {"left": 0, "top": 0, "width": 10, "height": 10},
        {
            "left": 0,
            "top": 0,
            "width": 10,
            "height": 10,
            "is_primary": True,
            "output": "DP-1",
        },
    ]
    grabber.grab.return_value = shot
    grabber.__enter__.return_value = grabber
    monkeypatch.setattr("mss.mss", lambda: grabber)

    observation = MssObservationProvider().capture_one(None, 0.2)

    assert isinstance(observation, ScreenObservation)
    assert (observation.width, observation.height) == (2, 2)
    assert (observation.native_width, observation.native_height) == (10, 10)
    assert observation.provider == "mss"


def test_cli_provider_preserves_command_identity(monkeypatch) -> None:
    monkeypatch.setattr(
        "vdisplay.capture.providers.observation_cli.command_candidates",
        lambda: [("grim", ["grim", "-"], True)],
    )
    monkeypatch.setattr(
        "vdisplay.capture.providers.observation_cli.run_png_command",
        lambda *args: _png(11, 6),
    )

    observation = CliToolsObservationProvider().capture_one(None, 0.2)

    assert observation.output == "grim"
    assert observation.provider == "cli_tools"
    assert (observation.width, observation.height) == (11, 6)


def test_screencast_provider_captures_each_stream(monkeypatch) -> None:
    class _Session:
        node_ids = [41, 42]
        stream_targets = ["DP-1", "DP-2"]
        streams = []

        def capture_png(self, *, node_index: int = 0) -> bytes:
            return _png(8 + node_index, 6)

    monkeypatch.setattr(
        "vdisplay.capture.providers.observation_portal._active_or_new_screencast",
        lambda: _Session(),
    )

    observations = PortalScreenCastObservationProvider().capture_all(0.5)

    assert [item.output for item in observations] == ["DP-1", "DP-2"]
    assert [item.width for item in observations] == [4, 4]
    assert observations[1].capture_meta["node_id"] == 42

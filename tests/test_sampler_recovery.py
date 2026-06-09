from __future__ import annotations

import time
from pathlib import Path

import pytest

from vdisplay.application.services.sampler_loop import (
    SamplerLoop,
    SamplerLoopConfig,
    is_screencast_recoverable_error,
)
from vdisplay.exceptions import VDisplayError


def _stub_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.application.services.sampler_loop.assess_unattended_capture",
        lambda **kwargs: type(
            "C",
            (),
            {
                "supports_unattended_capture": True,
                "requires_user_consent": False,
                "to_dict": lambda self: {"supports_unattended_capture": True},
            },
        )(),
    )


def test_is_screencast_recoverable_error() -> None:
    assert is_screencast_recoverable_error("portal-screencast: blank frame")
    assert is_screencast_recoverable_error("no active session")
    assert not is_screencast_recoverable_error("permission denied")


def test_sampler_recovers_from_blank_screencast(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_contract(monkeypatch)
    calls = {"n": 0, "recover": 0}

    def capture_fn(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise VDisplayError("portal-screencast: blank frame (stale ScreenCast)")
        path = Path(kwargs["output"])
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
        return {"path": str(path), "bytes": path.stat().st_size, "method": "portal-screencast"}

    def recover_fn() -> bool:
        calls["recover"] += 1
        return True

    loop = SamplerLoop(
        SamplerLoopConfig(
            interval_s=0.05,
            output_dir=str(tmp_path),
            max_frames=1,
            dedupe=False,
        ),
        capture_fn,
        recover_fn=recover_fn,
    )
    loop.start()
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if loop.state.frames_saved >= 1 or not loop.state.running:
            break
        time.sleep(0.02)

    status = loop.stop()
    assert calls["recover"] == 1
    assert status["frames_saved"] >= 1
    assert status["requires_reconsent"] is False


def test_sampler_marks_reconsent_when_recovery_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_contract(monkeypatch)
    def capture_fn(**kwargs):
        raise VDisplayError("portal-screencast: no active session")

    loop = SamplerLoop(
        SamplerLoopConfig(interval_s=0.05, output_dir=str(tmp_path), dedupe=False),
        capture_fn,
        recover_fn=lambda: False,
    )
    loop.start()
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and loop.state.running:
        time.sleep(0.02)

    status = loop.stop()
    assert status["requires_reconsent"] is True
    assert status["recovery_attempts"] >= 1

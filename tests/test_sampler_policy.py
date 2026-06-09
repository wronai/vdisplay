from __future__ import annotations

from pathlib import Path

import pytest

from vdisplay.application.services.discovery import diagnose_unattended
from vdisplay.application.services.sampler import SamplerConfig, run_sampler
from vdisplay.capture.policy import assess_unattended_capture


def test_assess_unattended_virtual_display() -> None:
    contract = assess_unattended_capture(display=":99")
    assert contract.supports_unattended_capture is True
    assert contract.requires_user_consent is False
    assert contract.recommended_profile == "virtual"
    assert contract.recommended_mode == "strict"


def test_assess_unattended_wayland_without_screencast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.capture.policy._is_wayland_session", lambda: True)
    contract = assess_unattended_capture(display=":0", agent_url=None, screencast_ready=False)
    assert contract.requires_user_consent is True
    assert contract.supports_unattended_capture is False
    assert contract.recommended_profile == "screencast"


def test_assess_unattended_wayland_with_screencast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.capture.policy._is_wayland_session", lambda: True)
    contract = assess_unattended_capture(display=":0", screencast_ready=True)
    assert contract.supports_unattended_capture is True
    assert contract.recommended_mode == "desktop"


def test_assess_unattended_uses_in_process_screencast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vdisplay.capture.policy._is_wayland_session", lambda: True)

    class FakeSession:
        is_ready = True

        def stop(self) -> dict:
            return {"ok": True, "stopped": False}

    monkeypatch.setattr(
        "vdisplay.capture.portal_screencast.get_active_screencast",
        lambda: FakeSession(),
    )
    contract = assess_unattended_capture(display=":0")
    assert contract.supports_unattended_capture is True


def test_diagnose_unattended_includes_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vdisplay.discovery.list_outputs",
        lambda *a, **k: [{"name": "DP-2", "primary": True}],
    )
    monkeypatch.setattr("vdisplay.capture.policy._is_wayland_session", lambda: True)
    monkeypatch.setattr("vdisplay.agent_config.resolve_agent_url", lambda **k: None)

    payload = diagnose_unattended(":0")
    assert "unattended" in payload
    assert payload["unattended"]["requires_user_consent"] is True
    assert "sampler_hint" in payload


def test_sampler_strict_virtual(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fake_capture(**kwargs: object) -> dict:
        calls["n"] += 1
        path = kwargs["output"]
        Path(str(path)).write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([calls["n"] % 256]) * 128)
        return {"path": path, "bytes": 128, "method": "virtual", "mode": "virtual"}

    monkeypatch.setattr(
        "vdisplay.application.services.capture.capture_screenshot",
        fake_capture,
    )

    config = SamplerConfig(
        mode="strict",
        interval_s=0.01,
        output_dir=str(tmp_path),
        max_frames=2,
        vd_display=":99",
    )
    result = run_sampler(config)
    assert result["frames_saved"] == 2
    assert result["capture_mode"] == "virtual"
    assert calls["n"] >= 2

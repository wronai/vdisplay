"""Control action lifecycle tests."""

from __future__ import annotations

from vdisplay.control.action_state import ControlActionPhase, ControlActionState, phase_from_payload


def test_control_action_state_roundtrip() -> None:
    state = ControlActionState.new("set_value")
    advanced = state.advance(ControlActionPhase.EXECUTED, attempt=2)
    payload = advanced.to_dict()
    assert payload["action"] == "set_value"
    assert payload["phase"] == "executed"
    assert payload["attempt"] == 2


def test_phase_from_payload_verified() -> None:
    assert phase_from_payload({"ok": True}) == ControlActionPhase.VERIFIED


def test_phase_from_payload_failed() -> None:
    phase = phase_from_payload(
        {
            "ok": False,
            "diagnostics": {"control": {"verify": {"verified": False}}},
        }
    )
    assert phase == ControlActionPhase.FAILED

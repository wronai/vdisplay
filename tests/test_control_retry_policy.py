"""Control retry policy tests."""

from __future__ import annotations

from vdisplay.control.action_state import ControlActionPhase, ControlActionState
from vdisplay.control.retry_policy import RetryPolicy, next_action


def test_next_action_fallback_backend() -> None:
    state = ControlActionState.new("invoke", action_id="a1")
    payload = {
        "ok": False,
        "routing": {
            "selected_provider": "atspi",
            "candidates": [
                {"provider": "atspi", "eligible": True, "score": 80},
                {"provider": "vision", "eligible": True, "score": 70},
            ],
        },
        "diagnostics": {
            "control": {
                "routing": {
                    "selected_provider": "atspi",
                    "candidates": [
                        {"provider": "atspi", "eligible": True, "score": 80},
                        {"provider": "vision", "eligible": True, "score": 70},
                    ],
                }
            }
        },
    }
    decision = next_action(state, payload, policy=RetryPolicy(max_attempts=3))
    assert decision.should_retry is True
    assert decision.strategy == "retry_scope"
    assert decision.next_backend is None


def test_next_action_rotates_on_second_failure() -> None:
    state = ControlActionState.new("invoke").advance(ControlActionPhase.PLANNED, attempt=2)
    payload = {
        "ok": False,
        "diagnostics": {
            "control": {
                "routing": {
                    "selected_provider": "atspi",
                    "candidates": [
                        {"provider": "atspi", "eligible": True, "score": 80},
                        {"provider": "vision", "eligible": True, "score": 70},
                    ],
                }
            }
        },
    }
    decision = next_action(state, payload, policy=RetryPolicy(max_attempts=3))
    assert decision.should_retry is True
    assert decision.strategy == "fallback_backend"
    assert decision.next_backend == "vision"


def test_next_action_exhausted() -> None:
    state = ControlActionState.new("invoke").advance(ControlActionPhase.PLANNED, attempt=3)
    decision = next_action(state, {"ok": False}, policy=RetryPolicy(max_attempts=3))
    assert decision.should_retry is False
    assert decision.reason == "max_attempts_exhausted"

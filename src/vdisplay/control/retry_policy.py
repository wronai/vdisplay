"""Policy-driven control retry after verify failure (PR-D)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..application.env_defaults import env_int_value, env_str_lower, env_value
from .action_state import ControlActionPhase, ControlActionState


@dataclass(frozen=True)
class RetryDecision:
    should_retry: bool
    strategy: str | None = None
    next_backend: str | None = None
    reason: str = ""
    delay_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "should_retry": self.should_retry,
            "strategy": self.strategy,
            "next_backend": self.next_backend,
            "reason": self.reason,
            "delay_ms": self.delay_ms,
        }


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    strategies: tuple[str, ...] = ("retry_scope", "fallback_backend", "refresh_map")
    delay_ms: int = 150

    @classmethod
    def from_env(cls) -> RetryPolicy:
        max_attempts = max(1, env_int_value("VDISPLAY_CONTROL_MAX_ATTEMPTS", default=3))
        delay_ms = max(0, env_int_value("VDISPLAY_CONTROL_RETRY_DELAY_MS", default=150))
        raw = env_value("VDISPLAY_CONTROL_RETRY_STRATEGIES").strip()
        if raw:
            strategies = tuple(item.strip() for item in raw.split(",") if item.strip())
        else:
            strategies = tuple(get_runtime_options().control_retry_strategies)
        if not strategies:
            strategies = cls.strategies
        return cls(max_attempts=max_attempts, strategies=strategies, delay_ms=delay_ms)


def retry_enabled(*, verify: bool, screenshot_verify: bool = False) -> bool:
    flag = env_str_lower("VDISPLAY_CONTROL_RETRY", "auto")
    if flag in {"0", "false", "no", "off"}:
        return False
    if flag in {"1", "true", "yes", "on"}:
        return True
    return verify or screenshot_verify


def next_action(
    state: ControlActionState,
    payload: dict[str, Any],
    *,
    policy: RetryPolicy | None = None,
) -> RetryDecision:
    policy = policy or RetryPolicy.from_env()
    if state.attempt >= policy.max_attempts:
        return RetryDecision(should_retry=False, reason="max_attempts_exhausted")

    strategy_index = state.attempt - 1
    if strategy_index >= len(policy.strategies):
        return RetryDecision(should_retry=False, reason="no_more_strategies")

    strategy = policy.strategies[strategy_index]
    routing = _routing_dict(payload)
    current = str(routing.get("selected_provider") or "")

    if strategy == "fallback_backend":
        nxt = _next_fallback_provider(routing, current)
        if nxt is None:
            return RetryDecision(should_retry=False, reason="no_fallback_provider")
        return RetryDecision(
            should_retry=True,
            strategy=strategy,
            next_backend=nxt,
            reason=f"rotate provider {current} -> {nxt}",
            delay_ms=policy.delay_ms,
        )

    if strategy == "retry_scope":
        return RetryDecision(
            should_retry=True,
            strategy=strategy,
            reason="tighten verify scope",
            delay_ms=policy.delay_ms,
        )

    if strategy == "refresh_map":
        map_block = _map_dict(payload)
        if not map_block.get("path"):
            return RetryDecision(should_retry=False, reason="no_map_for_refresh")
        return RetryDecision(
            should_retry=True,
            strategy=strategy,
            next_backend="vision",
            reason="refresh map + vision retry",
            delay_ms=policy.delay_ms,
        )

    return RetryDecision(should_retry=False, reason=f"unknown_strategy:{strategy}")


def apply_retry_decision(
    decision: RetryDecision,
    *,
    backend: str,
    selector_kwargs: dict[str, Any],
    screenshot_verify: bool,
) -> tuple[str, dict[str, Any], bool]:
    kwargs = dict(selector_kwargs)
    new_backend = backend
    new_screenshot_verify = screenshot_verify

    if decision.next_backend:
        new_backend = decision.next_backend

    if decision.strategy == "retry_scope":
        new_screenshot_verify = True
    elif decision.strategy == "refresh_map":
        kwargs["refresh_map"] = True
        new_backend = decision.next_backend or "vision"

    return new_backend, kwargs, new_screenshot_verify


def attach_retry_metadata(
    state: ControlActionState,
    decision: RetryDecision,
) -> ControlActionState:
    retry_block = {
        "attempt": state.attempt,
        "strategy": decision.strategy,
        "next_backend": decision.next_backend,
        "reason": decision.reason,
        "phase": ControlActionPhase.RETRY_SCHEDULED.value,
    }
    return state.advance(ControlActionPhase.RETRY_SCHEDULED, retry=retry_block)


def _routing_dict(payload: dict[str, Any]) -> dict[str, Any]:
    diagnostics = payload.get("diagnostics") or {}
    control = diagnostics.get("control") if isinstance(diagnostics.get("control"), dict) else {}
    routing = control.get("routing") if isinstance(control.get("routing"), dict) else payload.get("routing")
    return dict(routing) if isinstance(routing, dict) else {}


def _map_dict(payload: dict[str, Any]) -> dict[str, Any]:
    diagnostics = payload.get("diagnostics") or {}
    control = diagnostics.get("control") if isinstance(diagnostics.get("control"), dict) else {}
    map_block = control.get("map") if isinstance(control.get("map"), dict) else {}
    if map_block:
        return map_block
    return {
        "path": payload.get("map_path"),
        "target": payload.get("map_target"),
    }


def _next_fallback_provider(routing: dict[str, Any], current: str) -> str | None:
    candidates = routing.get("candidates") or []
    eligible = [
        item
        for item in candidates
        if isinstance(item, dict)
        and item.get("eligible")
        and str(item.get("provider") or "") != current
    ]
    if not eligible:
        return None
    eligible.sort(key=lambda item: int(item.get("score") or 0), reverse=True)
    return str(eligible[0].get("provider"))

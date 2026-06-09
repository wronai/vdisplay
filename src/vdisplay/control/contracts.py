"""Formal control-plane contracts (Pydantic v2 when available)."""

from __future__ import annotations

from typing import Any, Literal

from .selector import ControlSelector

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - pydantic optional at runtime
    BaseModel = object  # type: ignore[misc, assignment]
    Field = lambda *args, **kwargs: None  # type: ignore[misc, assignment]

    class _FallbackModel:
        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> dict[str, Any]:
            return {key: value for key, value in self.__dict__.items() if not key.startswith("_")}

    BaseModel = _FallbackModel  # type: ignore[misc, assignment]


class ProviderScoreContract(BaseModel):
    provider: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    cost: float = Field(default=0.2, ge=0.0)
    risk: float = Field(default=0.2, ge=0.0, le=1.0)
    eligible: bool = True
    reason: str = ""
    reasons: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    supports_find: bool = True
    supports_act: bool = True
    supports_verify_semantic: bool = False
    supports_verify_visual: bool = False

    def to_dict(self) -> dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.__dict__


class ExecutionContext(BaseModel):
    session_id: str | None = None
    display: str | None = None
    environment: str | None = None
    safe_retry: bool = False
    explain_route: bool = False
    verify_semantic: bool = False
    verify_screenshot: bool = False

    def to_dict(self) -> dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.__dict__


class VerifySpec(BaseModel):
    mode: Literal["semantic", "screenshot_diff", "ocr_contains", "anchor_visible", "hybrid", "dom"] = "hybrid"
    expected_text: str | None = None
    region: tuple[int, int, int, int] | None = None
    min_change_ratio: float = 0.02
    min_confidence: float = 0.80
    stable_for_ms: int = 0
    timeout_ms: int = 5000

    def to_dict(self) -> dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.__dict__


class ProviderResult(BaseModel):
    ok: bool
    provider: str
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.__dict__


class ControlRouteRequest(BaseModel):
    backend: str = "auto"
    selector: ControlSelector = Field(default_factory=ControlSelector)
    session_id: str | None = None
    display: str | None = None
    verify_semantic: bool = False
    verify_screenshot: bool = False

    def to_dict(self) -> dict[str, Any]:
        if hasattr(self, "model_dump"):
            payload = self.model_dump()
            payload["selector"] = self.selector.__dict__
            return payload
        return {
            "backend": self.backend,
            "selector": self.selector.__dict__,
            "session_id": self.session_id,
            "display": self.display,
            "verify_semantic": self.verify_semantic,
            "verify_screenshot": self.verify_screenshot,
        }


def provider_score_from_dataclass(score: Any) -> ProviderScoreContract:
    from .scoring import score_to_confidence

    confidence = score_to_confidence(score.score, eligible=score.eligible)
    cost = 0.1 if score.supports_native_invoke else 0.4
    risk = 0.1 if score.eligible else 0.9
    reason = score.reasons[0] if score.reasons else ""
    return ProviderScoreContract(
        provider=score.provider,
        confidence=confidence,
        cost=cost,
        risk=risk,
        eligible=score.eligible,
        reason=reason,
        reasons=list(score.reasons),
        missing_requirements=list(score.missing_requirements),
        supports_find=score.supports_semantic_find,
        supports_act=score.supports_native_invoke,
        supports_verify_semantic=score.supports_semantic_find,
        supports_verify_visual=score.supports_visual_verify,
    )


def control_route_request_from_command(cmd: Any) -> ControlRouteRequest:
    selector = ControlSelector(
        role=getattr(cmd, "control_role", None),
        name=getattr(cmd, "control_name", None),
        app=getattr(cmd, "control_app", None),
        window_id=getattr(cmd, "control_window_id", None),
        window_title=getattr(cmd, "control_window_title", None),
        index=int(getattr(cmd, "control_index", 0) or 0),
        backend=getattr(cmd, "control_backend", None),
        environment=getattr(cmd, "control_environment", None),
        text=getattr(cmd, "control_text", None),
        text_contains=getattr(cmd, "control_text_contains", None),
        terminal_line=getattr(cmd, "control_terminal_line", None),
        terminal_col=getattr(cmd, "control_terminal_col", None),
        session_id=getattr(cmd, "control_session_id", None),
        accessibility_id=getattr(cmd, "control_provider_ref", None),
    )
    if getattr(cmd, "control_selector", None):
        from .selector import parse_selector

        selector = parse_selector(cmd.control_selector)
    return ControlRouteRequest(
        backend=str(getattr(cmd, "control_backend", None) or "auto"),
        selector=selector,
        session_id=getattr(cmd, "control_session_id", None),
        display=getattr(cmd, "display", None),
        verify_semantic=bool(getattr(cmd, "control_verify", False)),
        verify_screenshot=bool(getattr(cmd, "control_screenshot_verify", False)),
    )

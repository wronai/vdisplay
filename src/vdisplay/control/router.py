"""Control router: score candidates, pick action and verify providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..exceptions import BackendNotAvailableError
from .base import ControlProvider
from .contracts import (
    ControlRouteRequest,
    ExecutionContext,
    ProviderScoreContract,
    control_route_request_from_command,
    provider_score_from_dataclass,
)
from .scoring import ProviderRoutingDecision, ProviderScore
from .registry import ProviderRegistry, default_provider_registry
from .scoring import (
    normalize_backend,
    rank_providers,
    select_verify_provider,
)
from .selector import ControlSelector


@dataclass(frozen=True)
class RouteResult:
    action_provider: ControlProvider
    decision: ProviderRoutingDecision
    verify_provider: str
    verify_mode: str
    contract_candidates: list[ProviderScoreContract] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = self.decision.to_dict()
        payload["verify_provider"] = self.verify_provider
        payload["verify_mode"] = self.verify_mode
        payload["contract_candidates"] = [item.to_dict() for item in self.contract_candidates]
        return payload


def _select_winner(
    backend: str,
    candidates: list[ProviderScore],
) -> tuple[str, list[str]]:
    requested = (backend or "auto").strip().lower()
    normalized = normalize_backend(requested)
    auto_mode = normalized == "auto"
    eligible = [item for item in candidates if item.eligible]

    if auto_mode:
        if not eligible:
            raise BackendNotAvailableError("no eligible control provider for auto routing")
        winner = eligible[0]
        selected = winner.provider
        why_selected = [f"highest eligible score ({winner.score})", *winner.reasons[:3]]
    else:
        match = next((item for item in candidates if item.provider == normalized), None)
        if match is None:
            raise BackendNotAvailableError(f"unknown control backend: {backend}")
        if not match.eligible:
            detail = ", ".join(match.missing_requirements) or "provider not eligible"
            raise BackendNotAvailableError(f"control backend {normalized} not available ({detail})")
        selected = normalized
        why_selected = [f"explicit backend={normalized}", *match.reasons[:3]]
    return selected, why_selected


class ControlRouter:
    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self._registry = registry or default_provider_registry()

    def _normalize_request(
        self,
        request: ControlRouteRequest | None,
        *,
        backend: str,
        selector: ControlSelector | None,
        session_id: str | None,
        display: str | None,
        verify_semantic: bool,
        verify_screenshot: bool,
        ctx: ExecutionContext | None,
    ) -> ControlRouteRequest:
        if request is None:
            request = ControlRouteRequest(
                backend=backend,
                selector=selector or ControlSelector(),
                session_id=session_id,
                display=display,
                verify_semantic=verify_semantic,
                verify_screenshot=verify_screenshot,
            )
        if ctx is not None:
            request = ControlRouteRequest(
                backend=request.backend,
                selector=request.selector,
                session_id=request.session_id or ctx.session_id,
                display=request.display or ctx.display,
                verify_semantic=request.verify_semantic or ctx.verify_semantic,
                verify_screenshot=request.verify_screenshot or ctx.verify_screenshot,
            )
        return request

    def evaluate(
        self,
        request: ControlRouteRequest | None = None,
        *,
        backend: str = "auto",
        selector: ControlSelector | None = None,
        session_id: str | None = None,
        display: str | None = None,
        verify_semantic: bool = False,
        verify_screenshot: bool = False,
        ctx: ExecutionContext | None = None,
    ) -> ProviderRoutingDecision:
        request = self._normalize_request(
            request,
            backend=backend,
            selector=selector,
            session_id=session_id,
            display=display,
            verify_semantic=verify_semantic,
            verify_screenshot=verify_screenshot,
            ctx=ctx,
        )
        sid = request.session_id or request.selector.session_id
        candidates, inference_payload = rank_providers(
            selector=request.selector,
            session_id=sid,
            display=request.display,
        )
        from .routing_semantics import build_routing_semantics

        semantics = build_routing_semantics(
            selector=request.selector,
            session_id=sid,
            display=request.display,
        )
        return self._build_decision(
            backend=request.backend,
            candidates=candidates,
            verify_semantic=request.verify_semantic,
            verify_screenshot=request.verify_screenshot,
            profile_inference=inference_payload,
            routing_semantics=semantics.to_dict(),
        )

    def route(
        self,
        request: ControlRouteRequest | None = None,
        *,
        backend: str = "auto",
        selector: ControlSelector | None = None,
        session_id: str | None = None,
        display: str | None = None,
        verify_semantic: bool = False,
        verify_screenshot: bool = False,
        ctx: ExecutionContext | None = None,
    ) -> RouteResult:
        request = self._normalize_request(
            request,
            backend=backend,
            selector=selector,
            session_id=session_id,
            display=display,
            verify_semantic=verify_semantic,
            verify_screenshot=verify_screenshot,
            ctx=ctx,
        )
        sid = request.session_id or request.selector.session_id
        decision = self.evaluate(request=request)
        action_provider = self._registry.build(
            decision.selected_provider,
            display=request.display,
            session_id=sid,
        )
        contract_candidates = [provider_score_from_dataclass(item) for item in decision.candidates]
        return RouteResult(
            action_provider=action_provider,
            decision=decision,
            verify_provider=decision.verify_provider or decision.selected_provider,
            verify_mode=decision.verify_mode,
            contract_candidates=contract_candidates,
        )

    def route_command(self, cmd: Any, *, ctx: ExecutionContext | None = None) -> RouteResult:
        request = control_route_request_from_command(cmd)
        return self.route(request=request, ctx=ctx)

    def _build_decision(
        self,
        *,
        backend: str,
        candidates: list[ProviderScore],
        verify_semantic: bool,
        verify_screenshot: bool,
        profile_inference: dict[str, Any] | None = None,
        routing_semantics: dict[str, Any] | None = None,
    ) -> ProviderRoutingDecision:
        requested = (backend or "auto").strip().lower()
        normalized = normalize_backend(requested)
        auto_mode = normalized == "auto"
        why_not_selected = {
            item.provider: list(item.missing_requirements or item.reasons[:1])
            for item in candidates
            if not item.eligible
        }

        selected, why_selected = _select_winner(backend, candidates)

        verify_provider, verify_mode = select_verify_provider(
            candidates,
            action_provider=selected,
            verify_semantic=verify_semantic,
            verify_screenshot=verify_screenshot,
        )
        application_profile = None
        if profile_inference:
            application_profile = profile_inference.get("profile_id")
            if application_profile:
                why_selected.append(f"application profile={application_profile}")

        return ProviderRoutingDecision(
            requested_backend=requested,
            selected_provider=selected,
            auto_mode=auto_mode,
            candidates=candidates,
            why_selected=why_selected,
            why_not_selected=why_not_selected,
            verify_provider=verify_provider,
            verify_mode=verify_mode,
            application_profile=application_profile,
            profile_inference=profile_inference,
            routing_semantics=routing_semantics,
        )


_default_router: ControlRouter | None = None


def default_router() -> ControlRouter:
    global _default_router
    if _default_router is None:
        _default_router = ControlRouter()
    return _default_router

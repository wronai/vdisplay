"""Resolve control providers (auto / explicit backend)."""

from __future__ import annotations

from .base import ControlProvider
from .router import ControlRouter, RouteResult, default_router
from .scoring import ProviderRoutingDecision
from .selector import ControlSelector


def resolve_provider_routing(
    backend: str = "auto",
    *,
    display: str | None = None,
    session_id: str | None = None,
    selector: ControlSelector | None = None,
    verify_semantic: bool = False,
    verify_screenshot: bool = False,
    router: ControlRouter | None = None,
) -> tuple[ControlProvider, ProviderRoutingDecision]:
    route = (router or default_router()).route(
        backend=backend,
        selector=selector,
        session_id=session_id,
        display=display,
        verify_semantic=verify_semantic,
        verify_screenshot=verify_screenshot,
    )
    return route.action_provider, route.decision


def resolve_route(
    backend: str = "auto",
    *,
    display: str | None = None,
    session_id: str | None = None,
    selector: ControlSelector | None = None,
    verify_semantic: bool = False,
    verify_screenshot: bool = False,
    router: ControlRouter | None = None,
) -> RouteResult:
    return (router or default_router()).route(
        backend=backend,
        selector=selector,
        session_id=session_id,
        display=display,
        verify_semantic=verify_semantic,
        verify_screenshot=verify_screenshot,
    )


def resolve_provider(
    backend: str = "auto",
    *,
    display: str | None = None,
    session_id: str | None = None,
    selector: ControlSelector | None = None,
    router: ControlRouter | None = None,
) -> ControlProvider:
    provider, _decision = resolve_provider_routing(
        backend,
        display=display,
        session_id=session_id,
        selector=selector,
        router=router,
    )
    return provider

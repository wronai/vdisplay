"""Accessibility-first desktop control plane."""

from .engine import resolve_provider, resolve_route
from .models import ControlNode, ControlRole, ControlSnapshot, ElementCapabilities, EnvironmentKind
from .descriptors import (
    ApplicationProfile,
    HostEnvironmentKind,
    PlatformProfile,
    ProviderDescriptor,
    extension_catalog,
    resolve_host_environment,
)
from .browser_engine import BrowserEngineKind, browser_engine_profile, normalize_browser_engine
from .routing_semantics import RoutingSemantics, build_routing_semantics, infer_target_environment
from .profile_inference import ProfileInference, infer_application_profile
from .policy import ControlCapabilityContract, ProviderRoutingDecision, assess_control_capability
from .session_kind import SessionKind
from .verify_strategy import VerifyStrategy
from .router import ControlRouter, RouteResult, default_router
from .verifier import VerificationResult, VerifierPipeline, default_verifier
from .selector import ControlSelector, parse_selector, pick_match
from .plugins import (
    RegisteredPlugin,
    list_control_plugins,
    register_control_provider,
    unregister_control_provider,
)

__all__ = [
    "ApplicationProfile",
    "BrowserEngineKind",
    "browser_engine_profile",
    "normalize_browser_engine",
    "ControlCapabilityContract",
    "HostEnvironmentKind",
    "PlatformProfile",
    "RoutingSemantics",
    "build_routing_semantics",
    "infer_target_environment",
    "resolve_host_environment",
    "ProviderDescriptor",
    "SessionKind",
    "VerifyStrategy",
    "ProfileInference",
    "extension_catalog",
    "infer_application_profile",
    "ControlNode",
    "ControlRole",
    "ElementCapabilities",
    "ControlSelector",
    "ControlSnapshot",
    "EnvironmentKind",
    "ControlRouter",
    "ProviderRoutingDecision",
    "RouteResult",
    "assess_control_capability",
    "VerificationResult",
    "VerifierPipeline",
    "default_router",
    "default_verifier",
    "parse_selector",
    "pick_match",
    "resolve_provider",
    "resolve_route",
    "RegisteredPlugin",
    "list_control_plugins",
    "register_control_provider",
    "unregister_control_provider",
]

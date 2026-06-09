"""Provider readiness probes and routing score calculation."""

from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass, field
from typing import Any

from .selector import ControlSelector


@dataclass(frozen=True)
class ProviderScore:
    provider: str
    score: int
    eligible: bool
    reasons: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    supports_semantic_find: bool = False
    supports_native_invoke: bool = False
    supports_visual_verify: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderRoutingDecision:
    requested_backend: str
    selected_provider: str
    auto_mode: bool
    candidates: list[ProviderScore]
    why_selected: list[str] = field(default_factory=list)
    why_not_selected: dict[str, list[str]] = field(default_factory=dict)
    verify_provider: str | None = None
    verify_mode: str = "semantic"
    application_profile: str | None = None
    profile_inference: dict[str, Any] | None = None
    routing_semantics: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "requested_backend": self.requested_backend,
            "selected_provider": self.selected_provider,
            "auto_mode": self.auto_mode,
            "candidates": [item.to_dict() for item in self.candidates],
            "why_selected": list(self.why_selected),
            "why_not_selected": dict(self.why_not_selected),
            "verify_provider": self.verify_provider,
            "verify_mode": self.verify_mode,
        }
        if self.application_profile:
            payload["application_profile"] = self.application_profile
        if self.profile_inference:
            payload["profile_inference"] = self.profile_inference
        if self.routing_semantics:
            payload["routing_semantics"] = self.routing_semantics
        return payload

_PROVIDER_ALIASES: dict[str, set[str]] = {
    "atspi": {"atspi", "a11y", "accessibility"},
    "uia": {"uia", "windows-a11y", "uia-automation"},
    "ax": {"ax", "macos-a11y", "macos-ax"},
    "browser": {"browser", "playwright", "chromium"},
    "x11": {"x11", "x11-fallback", "pointer"},
    "terminal": {"terminal", "pty", "tui", "screen"},
    "vision": {"vision", "vision-only", "ocr"},
}

_BUILTIN_PROVIDERS = ("atspi", "uia", "ax", "terminal", "browser", "x11", "vision")


def _all_provider_names() -> tuple[str, ...]:
    from .plugins import iter_provider_names

    names = list(_BUILTIN_PROVIDERS)
    for name in iter_provider_names():
        if name not in names:
            names.append(name)
    return tuple(names)


def _base_score(provider: str) -> int:
    from .descriptors import descriptor_for

    descriptor = descriptor_for(provider)
    return descriptor.base_score if descriptor is not None else 0

_MAX_SCORE = 800.0


def normalize_backend(backend: str | None) -> str:
    normalized = (backend or "auto").strip().lower()
    for canonical, aliases in _PROVIDER_ALIASES.items():
        if normalized in aliases:
            return canonical
    return normalized


def score_to_confidence(score: int, *, eligible: bool) -> float:
    if not eligible:
        return 0.0
    return round(min(1.0, max(0.0, score / _MAX_SCORE)), 3)


def _atspi_ready() -> tuple[bool, str]:
    try:
        from .providers.atspi import AtspiControlProvider

        return AtspiControlProvider().available()
    except Exception as exc:
        return False, str(exc)


def _uia_ready() -> tuple[bool, str]:
    try:
        from .providers.uia_impl import uia_deps_available

        return uia_deps_available()
    except Exception as exc:
        return False, str(exc)


def _ax_ready() -> tuple[bool, str]:
    try:
        from .providers.ax_impl import ax_deps_available

        return ax_deps_available()
    except Exception as exc:
        return False, str(exc)


def _browser_ready() -> tuple[bool, str]:
    try:
        from .providers.browser_playwright import _playwright_available

        return _playwright_available()
    except Exception as exc:
        return False, str(exc)


def _xdotool_ready() -> tuple[bool, str]:
    if shutil.which("xdotool"):
        return True, "xdotool available"
    return False, "xdotool not installed"


def _xwayland_reachable(display: str | None = None) -> tuple[bool, str]:
    """Probe whether an X server (XWayland) accepts connections on the display.

    On Wayland hosts the X11 provider can still drive XWayland clients
    (e.g. JetBrains Toolbox, X11-forced Electron apps) even though native
    Wayland windows stay invisible to xdotool.
    """
    disp = (display or os.environ.get("DISPLAY") or "").strip()
    if not disp:
        return False, "DISPLAY is not set"
    if not shutil.which("xdotool"):
        return False, "xdotool not installed"
    import subprocess

    try:
        proc = subprocess.run(
            ["xdotool", "getdisplaygeometry"],
            env={**os.environ, "DISPLAY": disp},
            capture_output=True,
            timeout=3,
        )
    except Exception as exc:
        return False, f"X display probe failed: {exc}"
    if proc.returncode == 0:
        return True, f"XWayland reachable on {disp}"
    return False, f"X display {disp} not reachable"


def _terminal_ready() -> tuple[bool, str]:
    try:
        from .providers.terminal import TerminalControlProvider

        return TerminalControlProvider().available()
    except Exception as exc:
        return False, str(exc)


def _browser_session_ready(session_id: str | None) -> tuple[bool, str]:
    from .browser_session_store import session_available
    from .providers.browser_session import default_registry

    registry = default_registry()
    if session_id:
        if registry.get(session_id) is not None or session_available(session_id):
            return True, f"browser session {session_id!r} is open"
        return False, f"browser session {session_id!r} is not open"
    open_ids = registry.list_ids()
    if open_ids:
        return True, f"{len(open_ids)} browser session(s) open"
    return False, "no browser session open"


def _vision_ready() -> tuple[bool, str]:
    try:
        from .providers.vision import VisionStubProvider
        from .vision_ocr import ocr_available

        provider_ok, provider_reason = VisionStubProvider().available()
        ocr_ok, ocr_reason = ocr_available()
        if ocr_ok:
            return True, f"vision OCR invoke ({ocr_reason})"
        return provider_ok, provider_reason
    except Exception as exc:
        return False, str(exc)


def _terminal_session_ready(session_id: str | None) -> tuple[bool, str]:
    from .providers.terminal_session import default_registry

    registry = default_registry()
    if session_id:
        if registry.get(session_id) is not None:
            return True, f"terminal session {session_id!r} is open"
        return False, f"terminal session {session_id!r} is not open"
    open_ids = registry.list_ids()
    if open_ids:
        return True, f"{len(open_ids)} terminal session(s) open"
    return False, "no terminal session open"


def _is_terminal_context(selector: ControlSelector, sid: str | None) -> bool:
    if selector.environment == "terminal":
        return True
    if selector.terminal_line is not None:
        return True
    if selector.terminal_col is not None:
        return True
    return bool(sid)


def _is_browser_context(selector: ControlSelector) -> bool:
    if selector.environment == "browser":
        return True
    if selector.dom_css:
        return True
    return bool(selector.dom_xpath)


def _is_desktop_context(selector: ControlSelector) -> bool:
    if selector.role or selector.name or selector.name_contains:
        return True
    if selector.app or selector.window_id or selector.window_title:
        return True
    return bool(selector.accessibility_id or selector.path)


def selector_context(selector: ControlSelector | None, session_id: str | None) -> dict[str, Any]:
    if selector is None:
        selector = ControlSelector()
    sid = session_id or selector.session_id
    return {
        "terminal": _is_terminal_context(selector, sid),
        "browser": _is_browser_context(selector),
        "desktop": _is_desktop_context(selector),
        "vision": bool(selector.environment == "vision" or selector.vision_anchor),
        "session_id": bool(sid),
    }


def _linux_desktop_hosts() -> tuple:
    from .descriptors import HostEnvironmentKind

    return (HostEnvironmentKind.LINUX_X11, HostEnvironmentKind.LINUX_WAYLAND)


def _score_atspi_provider(
    context: dict[str, Any],
) -> tuple[float, list[str], list[str], bool, bool, bool, bool]:
    from .descriptors import HostEnvironmentKind

    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    eligible = True
    supports_semantic_find = False
    supports_native_invoke = False

    host = context.get("host_environment")
    if host not in _linux_desktop_hosts():
        eligible = False
        missing.append(f"atspi requires Linux desktop host (host={host})")
        reasons.append("atspi limited to linux_x11/linux_wayland")

    ready, ready_reason = _atspi_ready()
    if eligible and ready:
        reasons.append(ready_reason)
        supports_semantic_find = True
        supports_native_invoke = True
    elif eligible:
        eligible = False
        missing.append(ready_reason)

    if context["desktop"] and not context["terminal"] and not context["browser"]:
        score += 30
        reasons.append("desktop selector context")
    if context["terminal"] or context["browser"]:
        score -= 40
        reasons.append("non-desktop selector context")

    return score, reasons, missing, eligible, supports_semantic_find, supports_native_invoke, False


def _score_uia_provider(
    context: dict[str, Any],
) -> tuple[float, list[str], list[str], bool, bool, bool, bool]:
    from .descriptors import HostEnvironmentKind

    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    eligible = True
    supports_semantic_find = False
    supports_native_invoke = False

    host = context.get("host_environment")
    if host != HostEnvironmentKind.WINDOWS:
        eligible = False
        missing.append(f"uia requires windows host (host={host})")
        reasons.append("uia limited to windows host")

    ready, ready_reason = _uia_ready()
    if eligible and ready:
        reasons.append(ready_reason)
        supports_semantic_find = True
        supports_native_invoke = True
    elif eligible:
        eligible = False
        missing.append(ready_reason)

    if context["desktop"] and not context["terminal"] and not context["browser"]:
        score += 30
        reasons.append("desktop selector context")
    if context["terminal"] or context["browser"]:
        score -= 40
        reasons.append("non-desktop selector context")

    return score, reasons, missing, eligible, supports_semantic_find, supports_native_invoke, False


def _score_ax_provider(
    context: dict[str, Any],
) -> tuple[float, list[str], list[str], bool, bool, bool, bool]:
    from .descriptors import HostEnvironmentKind

    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    eligible = True
    supports_semantic_find = False
    supports_native_invoke = False

    host = context.get("host_environment")
    if host != HostEnvironmentKind.DARWIN:
        eligible = False
        missing.append(f"ax requires darwin host (host={host})")
        reasons.append("ax limited to darwin host")

    ready, ready_reason = _ax_ready()
    if eligible and ready:
        reasons.append(ready_reason)
        supports_semantic_find = True
        supports_native_invoke = True
    elif eligible:
        eligible = False
        missing.append(ready_reason)

    if context["desktop"] and not context["terminal"] and not context["browser"]:
        score += 30
        reasons.append("desktop selector context")
    if context["terminal"] or context["browser"]:
        score -= 40
        reasons.append("non-desktop selector context")

    return score, reasons, missing, eligible, supports_semantic_find, supports_native_invoke, False


def _score_terminal_provider(
    context: dict[str, Any],
    session_id: str | None,
) -> tuple[float, list[str], list[str], bool, bool, bool, bool]:
    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    eligible = True
    supports_semantic_find = False
    supports_native_invoke = False

    ready, ready_reason = _terminal_ready()
    if ready:
        reasons.append(ready_reason)
        supports_semantic_find = True
        supports_native_invoke = True
    else:
        eligible = False
        missing.append(ready_reason)

    if context["terminal"]:
        score += 200
        reasons.append("terminal selector context")

    if context["session_id"]:
        session_ok, session_reason = _terminal_session_ready(session_id)
        if session_ok:
            reasons.append(session_reason)
            score += 40
        else:
            eligible = False
            missing.append(session_reason)
    elif context["terminal"]:
        session_ok, session_reason = _terminal_session_ready(None)
        if not session_ok:
            eligible = False
            missing.append(session_reason)

    return score, reasons, missing, eligible, supports_semantic_find, supports_native_invoke, False


def _score_browser_provider(
    context: dict[str, Any],
    session_id: str | None,
) -> tuple[float, list[str], list[str], bool, bool, bool, bool]:
    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    eligible = True
    supports_semantic_find = False
    supports_native_invoke = False
    supports_visual_verify = False

    ready, ready_reason = _browser_ready()
    if ready:
        reasons.append(ready_reason)
        supports_semantic_find = True
        supports_native_invoke = True
        supports_visual_verify = True
    else:
        eligible = False
        missing.append(ready_reason)

    if context["browser"]:
        score += 200
        reasons.append("browser/DOM selector context")
    browser_engine = context.get("browser_engine")
    if browser_engine:
        reasons.append(f"browser session engine={browser_engine}")
        score += 15
    if context["terminal"]:
        score -= 60
        reasons.append("terminal context deprioritizes browser")

    if context["session_id"] or context["browser"]:
        session_ok, session_reason = _browser_session_ready(session_id if context["session_id"] else None)
        if session_ok:
            reasons.append(session_reason)
            if context["session_id"]:
                score += 40
        elif context["session_id"] or context["browser"]:
            eligible = False
            missing.append(session_reason)

    return score, reasons, missing, eligible, supports_semantic_find, supports_native_invoke, supports_visual_verify


def _score_x11_provider(
    context: dict[str, Any],
    display: str | None,
) -> tuple[float, list[str], list[str], bool, bool, bool, bool]:
    from .descriptors import HostEnvironmentKind

    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    eligible = True
    supports_native_invoke = False
    supports_visual_verify = False

    host = context.get("host_environment")
    if host not in (HostEnvironmentKind.LINUX_X11, HostEnvironmentKind.LINUX_WAYLAND):
        eligible = False
        missing.append(f"x11 pointer fallback requires Linux host (host={host})")
        reasons.append("x11 limited to linux desktop hosts")
    elif host == HostEnvironmentKind.LINUX_WAYLAND:
        xwayland_ok, xwayland_reason = _xwayland_reachable(display)
        if xwayland_ok:
            reasons.append(f"Wayland host: {xwayland_reason} (XWayland clients only)")
        else:
            eligible = False
            missing.append(f"xdotool ineffective on Wayland host ({xwayland_reason})")
            reasons.append("host=linux_wayland blocks pointer fallback")

    ready, ready_reason = _xdotool_ready()
    display_ok = bool((display or os.environ.get("DISPLAY") or "").strip())
    if eligible and ready and display_ok:
        reasons.append(ready_reason)
        supports_native_invoke = True
        supports_visual_verify = True
    elif eligible:
        eligible = False
        if not ready:
            missing.append(ready_reason)
        if not display_ok:
            missing.append("DISPLAY is not set")

    if context["desktop"] and not context["terminal"] and not context["browser"]:
        score += 10
        reasons.append("desktop fallback context")
    if context["vision"]:
        score += 40
        reasons.append("vision_only_surface pointer fallback")
    if context["browser"] or context["terminal"]:
        score -= 30
        reasons.append("semantic context prefers non-x11 providers")

    return score, reasons, missing, eligible, False, supports_native_invoke, supports_visual_verify


def _score_vision_provider(
    context: dict[str, Any],
) -> tuple[float, list[str], list[str], bool, bool, bool, bool]:
    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    eligible = True
    supports_semantic_find = False
    supports_native_invoke = False
    supports_visual_verify = False

    ready, ready_reason = _vision_ready()
    if ready:
        reasons.append(ready_reason)
        supports_visual_verify = True
        from .vision_ocr import ocr_available

        if ocr_available()[0]:
            supports_native_invoke = True
    else:
        eligible = False
        missing.append(ready_reason)

    if context["vision"]:
        score -= 500
        reasons.append("vision OCR defers auto routing to x11/atspi/uia/ax fallback")
        supports_semantic_find = True
    if context["browser"] or context["terminal"]:
        score -= 50
        reasons.append("non-vision selector context")

    return score, reasons, missing, eligible, supports_semantic_find, supports_native_invoke, supports_visual_verify


def _score_plugin_provider(
    provider: str,
    context: dict[str, Any],
) -> tuple[float, list[str], list[str], bool, bool, bool, bool]:
    from .descriptors import descriptor_for

    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    eligible = True
    supports_semantic_find = False
    supports_native_invoke = False
    supports_visual_verify = False

    descriptor = descriptor_for(provider)
    if descriptor is not None:
        caps = descriptor.capabilities
        supports_semantic_find = caps.can_find and (
            caps.has_accessibility_tree or caps.has_dom or caps.has_terminal_grid
        )
        supports_native_invoke = caps.can_invoke
        supports_visual_verify = caps.supports_visual_verify
        score = descriptor.base_score
        reasons = [f"plugin descriptor base score {descriptor.base_score}"]
        if context["browser"] and "browser" in descriptor.environments:
            score += 80
            reasons.append("browser environment match")
        if context["terminal"] and "terminal" in descriptor.environments:
            score += 80
            reasons.append("terminal environment match")
        if context["desktop"] and "desktop" in descriptor.environments:
            score += 40
            reasons.append("desktop environment match")
    else:
        eligible = False
        missing.append(f"unknown provider: {provider}")

    return score, reasons, missing, eligible, supports_semantic_find, supports_native_invoke, supports_visual_verify


def score_provider(
    provider: str,
    *,
    context: dict[str, Any],
    display: str | None,
    session_id: str | None,
) -> ProviderScore:
    base = _base_score(provider)
    
    if provider == "atspi":
        p_score, p_reasons, missing, eligible, semantic, native, visual = _score_atspi_provider(context)
    elif provider == "uia":
        p_score, p_reasons, missing, eligible, semantic, native, visual = _score_uia_provider(context)
    elif provider == "ax":
        p_score, p_reasons, missing, eligible, semantic, native, visual = _score_ax_provider(context)
    elif provider == "terminal":
        p_score, p_reasons, missing, eligible, semantic, native, visual = _score_terminal_provider(context, session_id)
    elif provider == "browser":
        p_score, p_reasons, missing, eligible, semantic, native, visual = _score_browser_provider(context, session_id)
    elif provider == "x11":
        p_score, p_reasons, missing, eligible, semantic, native, visual = _score_x11_provider(context, display)
    elif provider == "vision":
        p_score, p_reasons, missing, eligible, semantic, native, visual = _score_vision_provider(context)
    else:
        p_score, p_reasons, missing, eligible, semantic, native, visual = _score_plugin_provider(provider, context)

    _builtin = ("atspi", "uia", "ax", "terminal", "browser", "x11", "vision")
    score = (base if provider in _builtin else 0.0) + p_score
    reasons = [f"base score {base}"] + p_reasons if provider in _builtin else p_reasons

    if context["vision"] and provider != "vision":
        score += 20
        reasons.append("vision selector prefers actionable fallback providers")

    if forced := context.get("forced_provider"):
        if provider == forced:
            score += 500
            reasons.append("selector.backend forces provider")

    profile = context.get("application_profile")
    if profile is not None:
        from .profile_inference import profile_provider_boost

        boost, boost_reasons = profile_provider_boost(provider, profile)
        if boost:
            score += boost
            reasons.extend(boost_reasons)

    return ProviderScore(
        provider=provider,
        score=int(score),
        eligible=eligible,
        reasons=reasons,
        missing_requirements=missing,
        supports_semantic_find=semantic,
        supports_native_invoke=native,
        supports_visual_verify=visual,
    )


def rank_providers(
    *,
    selector: ControlSelector | None = None,
    session_id: str | None = None,
    display: str | None = None,
) -> tuple[list[ProviderScore], dict[str, Any] | None]:
    from .descriptors import detect_platform_profile
    from .profile_inference import infer_application_profile, profile_for
    from .routing_semantics import build_routing_semantics

    from .browser_engine import resolve_session_browser_engine

    platform = detect_platform_profile(display=display)
    semantics = build_routing_semantics(selector=selector, session_id=session_id, display=display)
    context = selector_context(selector, session_id)
    browser_engine = resolve_session_browser_engine(session_id)
    context = {
        **context,
        "host_environment": platform.host_environment,
        "routing_semantics": semantics.to_dict(),
    }
    if browser_engine is not None:
        context["browser_engine"] = browser_engine.value
    inference = infer_application_profile(selector, session_id=session_id)
    inference_payload: dict[str, Any] | None = None
    if inference is not None:
        inference_payload = inference.to_dict()
        profile = profile_for(inference.profile_id)
        if profile is not None:
            context = {**context, "application_profile": profile}
    if selector is not None and selector.backend:
        forced = normalize_backend(selector.backend)
        if forced != "auto":
            context = {**context, "forced_provider": forced}
    candidates = [
        score_provider(name, context=context, display=display, session_id=session_id)
        for name in _all_provider_names()
    ]
    return sorted(candidates, key=lambda item: item.score, reverse=True), inference_payload


def _verify_screenshot_only(candidates: list[ProviderScore], action_provider: str) -> tuple[str, str]:
    for item in candidates:
        if item.eligible and item.supports_visual_verify:
            return item.provider, "screenshot"
    return action_provider, "screenshot"


def _verify_hybrid(candidates: list[ProviderScore], action_provider: str) -> tuple[str, str]:
    for item in candidates:
        if item.eligible and item.supports_visual_verify and item.provider != action_provider:
            return item.provider, "hybrid"
    action = next((item for item in candidates if item.provider == action_provider), None)
    if action and action.supports_visual_verify:
        return action_provider, "hybrid"
    for item in candidates:
        if item.eligible and item.supports_visual_verify:
            return item.provider, "hybrid"
    return action_provider, "hybrid"


def select_verify_provider(
    candidates: list[ProviderScore],
    *,
    action_provider: str,
    verify_semantic: bool,
    verify_screenshot: bool,
) -> tuple[str, str]:
    if verify_screenshot and not verify_semantic:
        return _verify_screenshot_only(candidates, action_provider)

    if verify_semantic and verify_screenshot:
        return _verify_hybrid(candidates, action_provider)

    if verify_semantic and action_provider == "browser":
        return action_provider, "dom"

    return action_provider, "semantic"

"""Infer application profile from selector context — not from vendor-specific apps."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .descriptors import (
    BUILTIN_APPLICATION_PROFILES,
    ApplicationProfile,
)
from .selector import ControlSelector

_ELECTRON_APP_HINTS = (
    "electron",
    "slack",
    "discord",
    "vscode",
    "code",
    "cursor",
    "spotify",
    "teams",
)


@dataclass(frozen=True)
class ProfileInference:
    profile_id: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        profile = profile_for(self.profile_id)
        if profile is not None:
            payload["profile"] = profile.to_dict()
        return payload


def profile_for(profile_id: str) -> ApplicationProfile | None:
    normalized = profile_id.strip().lower()
    for item in BUILTIN_APPLICATION_PROFILES:
        if item.profile_id == normalized:
            return item
    return None


def _score_vision_only_surface(selector: ControlSelector) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if selector.environment == "vision" or selector.vision_anchor:
        score += 0.95
        reasons.append("vision environment or anchor")
    if selector.dom_css or selector.dom_xpath or selector.terminal_line is not None:
        score -= 0.4
    return score, reasons


def _score_browser_engine(
    profile: ApplicationProfile,
    *,
    selector: ControlSelector,
    session_id: str | None,
) -> tuple[float, list[str]]:
    from .browser_engine import normalize_browser_engine, resolve_session_browser_engine

    score = 0.0
    reasons: list[str] = []
    session_engine = resolve_session_browser_engine(session_id or selector.session_id)
    if session_engine is None:
        return score, reasons

    expected_vendor = profile.vendor or profile.profile_id.removeprefix("browser_")
    if session_engine.value == normalize_browser_engine(expected_vendor).value:
        score += 0.98
        reasons.append(f"browser session engine={session_engine.value}")
    if selector.dom_css or selector.dom_xpath or selector.environment == "browser":
        score += 0.5
        reasons.append("DOM/browser selector context")
    return score, reasons


def _score_web_spa(selector: ControlSelector) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if selector.dom_css or selector.dom_xpath:
        score += 0.95
        reasons.append("DOM selector present")
    if selector.environment == "browser":
        score += 0.85
        reasons.append("environment=browser")
    if selector.role or selector.accessibility_id:
        score += 0.15
        reasons.append("a11y fields on web surface")
    return score, reasons


def _score_terminal_pty(selector: ControlSelector, sid: str | None) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if selector.terminal_line is not None or selector.terminal_col is not None:
        score += 0.95
        reasons.append("terminal coordinates")
    if selector.environment == "terminal":
        score += 0.9
        reasons.append("environment=terminal")
    if sid:
        score += 0.5
        reasons.append("session_id present")
    if selector.text or selector.text_contains:
        score += 0.2
        reasons.append("terminal text match")
    return score, reasons


def _score_electron_desktop(selector: ControlSelector) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    app_blob = " ".join(
        filter(
            None,
            [
                selector.app,
                selector.window_title,
                str(selector.extra.get("app_kind", "")),
            ],
        )
    ).lower()
    if any(hint in app_blob for hint in _ELECTRON_APP_HINTS):
        score += 0.75
        reasons.append("electron-like app hint")
    if selector.dom_css or selector.dom_xpath:
        score += 0.35
        reasons.append("DOM fields suggest embedded webview")
    return score, reasons


def _score_native_gtk(selector: ControlSelector) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if selector.role or selector.name or selector.name_contains:
        score += 0.55
        reasons.append("desktop a11y selector")
    if selector.app or selector.window_title or selector.window_id:
        score += 0.45
        reasons.append("window/app targeting")
    if selector.accessibility_id or selector.path:
        score += 0.35
        reasons.append("accessibility id or path")
    if selector.environment == "desktop":
        score += 0.4
        reasons.append("environment=desktop")
    if selector.dom_css or selector.dom_xpath:
        score -= 0.5
    if selector.terminal_line is not None or selector.environment == "terminal":
        score -= 0.6
    return score, reasons


def _score_candidate(
    profile: ApplicationProfile,
    *,
    selector: ControlSelector,
    session_id: str | None,
) -> tuple[float, list[str]]:
    sid = session_id or selector.session_id

    if profile.profile_id == "vision_only_surface":
        score, reasons = _score_vision_only_surface(selector)
    elif profile.profile_id in {"browser_chromium", "browser_firefox"}:
        score, reasons = _score_browser_engine(profile, selector=selector, session_id=sid)
    elif profile.profile_id == "web_spa":
        score, reasons = _score_web_spa(selector)
        session_engine = None
        try:
            from .browser_engine import resolve_session_browser_engine

            session_engine = resolve_session_browser_engine(sid)
        except Exception:
            pass
        if session_engine is not None:
            score = max(0.0, score - 0.2)
            reasons.append("generic web_spa — prefer browser_* engine profile when session engine known")
    elif profile.profile_id == "terminal_pty":
        score, reasons = _score_terminal_pty(selector, sid)
    elif profile.profile_id == "electron_desktop":
        score, reasons = _score_electron_desktop(selector)
    elif profile.profile_id == "native_gtk":
        score, reasons = _score_native_gtk(selector)
    else:
        score, reasons = 0.0, []

    if score > 0:
        reasons.insert(0, f"profile={profile.profile_id}")
    return score, reasons


def infer_application_profile(
    selector: ControlSelector | None = None,
    *,
    session_id: str | None = None,
) -> ProfileInference | None:
    if selector is None:
        selector = ControlSelector()

    ranked: list[tuple[float, ApplicationProfile, list[str]]] = []
    for profile in BUILTIN_APPLICATION_PROFILES:
        score, reasons = _score_candidate(profile, selector=selector, session_id=session_id)
        if score > 0:
            ranked.append((score, profile, reasons))

    if not ranked:
        return None

    ranked.sort(key=lambda item: item[0], reverse=True)
    best_score, best_profile, best_reasons = ranked[0]
    confidence = round(min(1.0, max(0.0, best_score)), 3)
    candidates = [
        {
            "profile_id": profile.profile_id,
            "confidence": round(min(1.0, score), 3),
            "reasons": reasons[:3],
        }
        for score, profile, reasons in ranked[:4]
    ]
    return ProfileInference(
        profile_id=best_profile.profile_id,
        confidence=confidence,
        reasons=best_reasons[:5],
        candidates=candidates,
    )


def profile_provider_boost(
    provider: str,
    profile: ApplicationProfile | None,
) -> tuple[int, list[str]]:
    if profile is None:
        return 0, []
    reasons: list[str] = []
    boost = 0
    if profile.preferred_providers:
        if provider == profile.preferred_providers[0]:
            boost = 80
            reasons.append(f"primary provider for profile {profile.profile_id}")
        elif provider in profile.preferred_providers[1:]:
            boost = 40
            reasons.append(f"secondary provider for profile {profile.profile_id}")
        elif provider in profile.fallback_providers:
            boost = 10
            reasons.append(f"fallback provider for profile {profile.profile_id}")
        else:
            boost = -20
            reasons.append(f"not in profile {profile.profile_id} provider stack")
    return boost, reasons

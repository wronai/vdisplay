"""Browser engine profiles — vendor/engine as application profile, not provider."""

from __future__ import annotations

from enum import StrEnum

from .descriptors import ApplicationProfile, BUILTIN_APPLICATION_PROFILES


class BrowserEngineKind(StrEnum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"


DEFAULT_BROWSER_ENGINE = BrowserEngineKind.CHROMIUM

_ENGINE_ALIASES: dict[str, BrowserEngineKind] = {
    "chromium": BrowserEngineKind.CHROMIUM,
    "chrome": BrowserEngineKind.CHROMIUM,
    "firefox": BrowserEngineKind.FIREFOX,
    "ff": BrowserEngineKind.FIREFOX,
}


def normalize_browser_engine(value: str | None) -> BrowserEngineKind:
    if not value:
        return DEFAULT_BROWSER_ENGINE
    normalized = str(value).strip().lower()
    if normalized.startswith("browser_"):
        normalized = normalized.removeprefix("browser_")
    return _ENGINE_ALIASES.get(normalized, DEFAULT_BROWSER_ENGINE)


def engine_profile_id(engine: BrowserEngineKind | str) -> str:
    kind = engine if isinstance(engine, BrowserEngineKind) else normalize_browser_engine(str(engine))
    return f"browser_{kind.value}"


def browser_engine_profile(engine: BrowserEngineKind | str) -> ApplicationProfile | None:
    profile_id = engine_profile_id(engine)
    for item in BUILTIN_APPLICATION_PROFILES:
        if item.profile_id == profile_id:
            return item
    return None


def resolve_session_browser_engine(session_id: str | None) -> BrowserEngineKind | None:
    if not session_id:
        return None
    from .providers.browser_session import default_registry

    session = default_registry().get(session_id)
    if session is None:
        return None
    return normalize_browser_engine(getattr(session, "engine", None))

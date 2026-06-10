"""Extension model: platform, application, and provider descriptors."""

from __future__ import annotations

import os
import platform
import shutil
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from .capabilities import (
    BROWSER_DOM,
    DESKTOP_A11Y,
    POINTER_FALLBACK,
    TERMINAL_GRID,
    VISION_SURFACE,
    ProviderCapabilities,
)
from .session_kind import SessionKind
from .verify_strategy import VerifyStrategy

SELECTOR_CORE_FIELDS = frozenset(
    {
        "role",
        "name",
        "name_contains",
        "app",
        "window_id",
        "window_title",
        "index",
        "backend",
        "environment",
        "text",
        "text_contains",
        "value",
        "accessibility_id",
        "path",
        "session_id",
    }
)


@dataclass(frozen=True)
class SelectorExtension:
    """Backend- or profile-specific selector fields beyond the core set."""

    name: str
    fields: frozenset[str]
    environments: frozenset[str] = field(default_factory=frozenset)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "fields": sorted(self.fields),
            "environments": sorted(self.environments),
            "description": self.description,
        }


TERMINAL_SELECTOR = SelectorExtension(
    name="terminal",
    fields=frozenset({"terminal_line", "terminal_col"}),
    environments=frozenset({"terminal"}),
    description="TUI grid coordinates and line text matching",
)

BROWSER_SELECTOR = SelectorExtension(
    name="browser",
    fields=frozenset({"dom_css", "dom_xpath"}),
    environments=frozenset({"browser"}),
    description="DOM locators for web surfaces",
)

VISION_SELECTOR = SelectorExtension(
    name="vision",
    fields=frozenset(
        {
            "vision_anchor",
            "vision_template",
            "vision_anchor_rel",
            "vision_target",
            "vision_min_confidence",
        }
    ),
    environments=frozenset({"vision"}),
    description="Visual anchor/template hints when semantic trees are unavailable",
)


class HostEnvironmentKind(StrEnum):
    """Host / execution environment — capability probes, deps, policy."""

    LINUX_X11 = "linux_x11"
    LINUX_WAYLAND = "linux_wayland"
    LINUX_HEADLESS = "linux_headless"
    WINDOWS = "windows"
    DARWIN = "darwin"
    UNKNOWN = "unknown"


_DISPLAY_STACK_TO_LINUX_HOST: dict[str, HostEnvironmentKind] = {
    "x11": HostEnvironmentKind.LINUX_X11,
    "wayland": HostEnvironmentKind.LINUX_WAYLAND,
    "headless": HostEnvironmentKind.LINUX_HEADLESS,
}


def resolve_host_environment(*, os_family: str, display_stack: str) -> HostEnvironmentKind:
    family = os_family.lower()
    if family == "linux":
        return _DISPLAY_STACK_TO_LINUX_HOST.get(display_stack, HostEnvironmentKind.UNKNOWN)
    if family == "windows":
        return HostEnvironmentKind.WINDOWS
    if family == "darwin":
        return HostEnvironmentKind.DARWIN
    return HostEnvironmentKind.UNKNOWN


@dataclass(frozen=True)
class PlatformProfile:
    os_family: str
    display_stack: str
    host_environment: HostEnvironmentKind
    desktop_env: str | None = None
    available_integrations: list[str] = field(default_factory=list)
    security_constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["host_environment"] = self.host_environment.value
        return payload


@dataclass(frozen=True)
class ApplicationProfile:
    """Class-of-app hints — not a first-class backend."""

    profile_id: str
    kind: str
    vendor: str | None = None
    preferred_providers: list[str] = field(default_factory=list)
    fallback_providers: list[str] = field(default_factory=list)
    selector_extensions: list[str] = field(default_factory=list)
    verify_strategies: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    adapter_kind: str
    environments: frozenset[str]
    session_kind: SessionKind | None
    capabilities: ProviderCapabilities
    selector_extensions: tuple[SelectorExtension, ...] = ()
    actions: frozenset[str] = frozenset({"snapshot", "find"})
    verify_strategies: frozenset[VerifyStrategy] = frozenset()
    required_deps: tuple[str, ...] = ()
    aliases: frozenset[str] = frozenset()
    base_score: int = 50
    cost: float = 0.3
    risk: float = 0.2

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "adapter_kind": self.adapter_kind,
            "environments": sorted(self.environments),
            "session_kind": self.session_kind.value if self.session_kind else None,
            "capabilities": self.capabilities.to_dict(),
            "selector_extensions": [item.to_dict() for item in self.selector_extensions],
            "actions": sorted(self.actions),
            "verify_strategies": [item.value for item in self.verify_strategies],
            "required_deps": list(self.required_deps),
            "aliases": sorted(self.aliases),
            "base_score": self.base_score,
            "cost": self.cost,
            "risk": self.risk,
        }


BUILTIN_PROVIDER_DESCRIPTORS: tuple[ProviderDescriptor, ...] = (
    ProviderDescriptor(
        provider_id="atspi",
        adapter_kind="linux_desktop_a11y",
        environments=frozenset({"desktop"}),
        session_kind=None,
        capabilities=DESKTOP_A11Y,
        selector_extensions=(),
        actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
        verify_strategies=frozenset({VerifyStrategy.STRUCTURE, VerifyStrategy.TEXT, VerifyStrategy.HYBRID}),
        required_deps=("pyatspi / AT-SPI bus",),
        aliases=frozenset({"a11y", "accessibility"}),
        base_score=100,
        cost=0.15,
        risk=0.1,
    ),
    ProviderDescriptor(
        provider_id="uia",
        adapter_kind="windows_uia",
        environments=frozenset({"desktop"}),
        session_kind=None,
        capabilities=DESKTOP_A11Y,
        selector_extensions=(),
        actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
        verify_strategies=frozenset({VerifyStrategy.STRUCTURE, VerifyStrategy.TEXT, VerifyStrategy.HYBRID}),
        required_deps=("Windows UIA / COM", "comtypes"),
        aliases=frozenset({"windows-a11y", "uia-automation"}),
        base_score=98,
        cost=0.18,
        risk=0.12,
    ),
    ProviderDescriptor(
        provider_id="ax",
        adapter_kind="darwin_ax",
        environments=frozenset({"desktop"}),
        session_kind=None,
        capabilities=DESKTOP_A11Y,
        selector_extensions=(),
        actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
        verify_strategies=frozenset({VerifyStrategy.STRUCTURE, VerifyStrategy.TEXT, VerifyStrategy.HYBRID}),
        required_deps=("macOS Accessibility API", "pyobjc-framework-ApplicationServices"),
        aliases=frozenset({"macos-a11y", "macos-ax"}),
        base_score=98,
        cost=0.18,
        risk=0.12,
    ),
    ProviderDescriptor(
        provider_id="terminal",
        adapter_kind="terminal_pty",
        environments=frozenset({"terminal"}),
        session_kind=SessionKind.TERMINAL,
        capabilities=TERMINAL_GRID,
        selector_extensions=(TERMINAL_SELECTOR,),
        actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value"}),
        verify_strategies=frozenset({VerifyStrategy.TEXT, VerifyStrategy.STRUCTURE}),
        required_deps=("pyte (optional)", "pexpect (optional)"),
        aliases=frozenset({"pty", "tui", "screen"}),
        base_score=80,
        cost=0.2,
        risk=0.2,
    ),
    ProviderDescriptor(
        provider_id="browser",
        adapter_kind="browser_playwright",
        environments=frozenset({"browser"}),
        session_kind=SessionKind.BROWSER,
        capabilities=BROWSER_DOM,
        selector_extensions=(BROWSER_SELECTOR,),
        actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
        verify_strategies=frozenset({VerifyStrategy.DOM, VerifyStrategy.SCREENSHOT, VerifyStrategy.HYBRID}),
        required_deps=("playwright",),
        aliases=frozenset({"playwright", "chromium"}),
        base_score=70,
        cost=0.25,
        risk=0.15,
    ),
    ProviderDescriptor(
        provider_id="x11",
        adapter_kind="pointer_fallback",
        environments=frozenset({"desktop"}),
        session_kind=None,
        capabilities=POINTER_FALLBACK,
        selector_extensions=(),
        actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
        verify_strategies=frozenset({VerifyStrategy.SCREENSHOT}),
        required_deps=("xdotool", "DISPLAY"),
        aliases=frozenset({"x11-fallback", "pointer"}),
        base_score=50,
        cost=0.35,
        risk=0.4,
    ),
    ProviderDescriptor(
        provider_id="vision",
        adapter_kind="vision_ocr",
        environments=frozenset({"vision"}),
        session_kind=None,
        capabilities=VISION_SURFACE,
        selector_extensions=(VISION_SELECTOR,),
        actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
        verify_strategies=frozenset({VerifyStrategy.SCREENSHOT, VerifyStrategy.OCR, VerifyStrategy.ANCHOR_VISIBLE}),
        required_deps=("screenshot capture", "tesseract", "pytesseract"),
        aliases=frozenset({"vision-only", "ocr"}),
        base_score=45,
        cost=0.4,
        risk=0.25,
    ),
)

BUILTIN_APPLICATION_PROFILES: tuple[ApplicationProfile, ...] = (
    ApplicationProfile(
        profile_id="native_gtk",
        kind="desktop_native",
        vendor="gtk",
        preferred_providers=["atspi"],
        fallback_providers=["x11"],
        verify_strategies=["structure", "text", "hybrid"],
        notes="GTK/Qt apps with AT-SPI enabled (Linux)",
    ),
    ApplicationProfile(
        profile_id="native_windows",
        kind="desktop_native",
        vendor="windows",
        preferred_providers=["uia"],
        fallback_providers=["browser"],
        verify_strategies=["structure", "text", "hybrid"],
        notes="Win32/UWP/Electron on Windows — UIA primary",
    ),
    ApplicationProfile(
        profile_id="native_macos",
        kind="desktop_native",
        vendor="apple",
        preferred_providers=["ax"],
        fallback_providers=["browser"],
        verify_strategies=["structure", "text", "hybrid"],
        notes="Cocoa/Swift/Electron on macOS — AX primary",
    ),
    ApplicationProfile(
        profile_id="electron_desktop",
        kind="electron",
        preferred_providers=["atspi", "browser"],
        fallback_providers=["x11"],
        verify_strategies=["structure", "screenshot", "hybrid"],
        notes="Electron shell — prefer a11y; DOM only when debug port exposed",
    ),
    ApplicationProfile(
        profile_id="web_spa",
        kind="browser",
        preferred_providers=["browser"],
        fallback_providers=["x11"],
        selector_extensions=["browser"],
        verify_strategies=["dom", "screenshot", "hybrid"],
        notes="Generic web/DOM surface — engine resolved via browser session",
    ),
    ApplicationProfile(
        profile_id="browser_chromium",
        kind="browser",
        vendor="chromium",
        preferred_providers=["browser"],
        fallback_providers=[],
        selector_extensions=["browser"],
        verify_strategies=["dom", "screenshot", "hybrid"],
        notes="Playwright chromium engine profile",
    ),
    ApplicationProfile(
        profile_id="browser_firefox",
        kind="browser",
        vendor="firefox",
        preferred_providers=["browser"],
        fallback_providers=[],
        selector_extensions=["browser"],
        verify_strategies=["dom", "screenshot", "hybrid"],
        notes="Playwright firefox engine profile",
    ),
    ApplicationProfile(
        profile_id="terminal_pty",
        kind="terminal",
        preferred_providers=["terminal"],
        selector_extensions=["terminal"],
        verify_strategies=["text", "structure"],
    ),
    ApplicationProfile(
        profile_id="vision_only_surface",
        kind="vision_only",
        preferred_providers=["x11"],
        fallback_providers=["vision"],
        selector_extensions=["vision"],
        verify_strategies=["screenshot", "ocr"],
        notes="Canvas, games, remote streams — x11 pointer fallback; vision stub for verify",
    ),
)


def descriptor_for(provider_id: str) -> ProviderDescriptor | None:
    from .plugins import get_registered_descriptor

    return get_registered_descriptor(provider_id)


def all_provider_descriptors() -> list[ProviderDescriptor]:
    from .plugins import get_provider_registry

    return get_provider_registry().list_descriptors()


def all_application_profiles() -> list[ApplicationProfile]:
    return list(BUILTIN_APPLICATION_PROFILES)


def all_selector_extensions() -> list[SelectorExtension]:
    return [TERMINAL_SELECTOR, BROWSER_SELECTOR, VISION_SELECTOR]


def detect_platform_profile(*, display: str | None = None) -> PlatformProfile:
    os_family = platform.system().lower()
    session_type = (os.environ.get("XDG_SESSION_TYPE") or "").lower()
    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION")
    integrations: list[str] = []
    constraints: list[str] = []

    if shutil.which("xdotool"):
        integrations.append("xdotool")
    if os.environ.get("DISPLAY") or display:
        integrations.append("x11")
    if session_type == "wayland":
        integrations.append("portal")
        constraints.append("xdotool ineffective on Wayland")
    try:
        from .scoring import _atspi_ready, _browser_ready, _terminal_ready

        if _atspi_ready()[0]:
            integrations.append("atspi")
        if _browser_ready()[0]:
            integrations.append("playwright")
        if _terminal_ready()[0]:
            integrations.append("terminal")
    except Exception:
        pass

    if session_type == "wayland":
        display_stack = "wayland"
    elif os.environ.get("DISPLAY") or display:
        display_stack = "x11"
    else:
        display_stack = "headless"

    return PlatformProfile(
        os_family=os_family,
        display_stack=display_stack,
        host_environment=resolve_host_environment(os_family=os_family, display_stack=display_stack),
        desktop_env=desktop_env,
        available_integrations=sorted(set(integrations)),
        security_constraints=constraints,
    )


def extension_catalog() -> dict[str, Any]:
    from .plugins import list_control_plugins

    return {
        "platform": detect_platform_profile().to_dict(),
        "terminology": {
            "host_environment": "HostEnvironmentKind — execution/capability probes",
            "target_environment": "EnvironmentKind — selector-driven automation target",
            "session_kind": "SessionKind — broker session lifecycle",
            "verify_strategy": "VerifyStrategy — legal verify modes per target",
        },
        "providers": [item.to_dict() for item in all_provider_descriptors()],
        "plugins": list_control_plugins(),
        "application_profiles": [item.to_dict() for item in BUILTIN_APPLICATION_PROFILES],
        "browser_engine_profiles": [
            item.to_dict()
            for item in BUILTIN_APPLICATION_PROFILES
            if item.profile_id.startswith("browser_")
        ],
        "selector_extensions": [item.to_dict() for item in all_selector_extensions()],
        "session_kinds": [item.value for item in SessionKind],
        "verify_strategies": [item.value for item in VerifyStrategy],
    }

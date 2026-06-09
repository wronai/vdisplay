"""In-process provider registry with data-driven descriptors."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..exceptions import BackendNotAvailableError
from .base import ControlProvider
from .descriptors import BUILTIN_PROVIDER_DESCRIPTORS, ProviderDescriptor, descriptor_for
from .scoring import normalize_backend

ProviderFactory = Callable[..., ControlProvider]


class ProviderRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}
        self._descriptors: dict[str, ProviderDescriptor] = {}

    def register(
        self,
        descriptor: ProviderDescriptor,
        factory: ProviderFactory,
    ) -> None:
        self._descriptors[descriptor.provider_id] = descriptor
        self._factories[descriptor.provider_id] = factory
        for alias in descriptor.aliases:
            self._factories[normalize_backend(alias)] = factory

    def list_names(self) -> list[str]:
        return sorted(self._descriptors)

    def list_descriptors(self) -> list[ProviderDescriptor]:
        return [self._descriptors[name] for name in self.list_names()]

    def get_descriptor(self, name: str) -> ProviderDescriptor | None:
        normalized = normalize_backend(name)
        if normalized in self._descriptors:
            return self._descriptors[normalized]
        return descriptor_for(normalized)

    def build(
        self,
        name: str,
        *,
        display: str | None = None,
        session_id: str | None = None,
    ) -> ControlProvider:
        normalized = normalize_backend(name)
        factory = self._factories.get(normalized)
        if factory is None:
            raise BackendNotAvailableError(f"unknown control backend: {name}")
        provider = factory(display=display, session_id=session_id)
        ok, reason = provider.available()
        if not ok:
            raise BackendNotAvailableError(reason)
        return provider


def _build_atspi(*, display: str | None = None, session_id: str | None = None) -> ControlProvider:
    from .providers.atspi import AtspiControlProvider

    return AtspiControlProvider()


def _build_uia(*, display: str | None = None, session_id: str | None = None) -> ControlProvider:
    from .providers.uia import UiaStubProvider

    return UiaStubProvider(display=display, session_id=session_id)


def _build_ax(*, display: str | None = None, session_id: str | None = None) -> ControlProvider:
    from .providers.ax import AxStubProvider

    return AxStubProvider(display=display, session_id=session_id)


def _build_browser(*, display: str | None = None, session_id: str | None = None) -> ControlProvider:
    from .providers.browser_playwright import BrowserPlaywrightProvider

    return BrowserPlaywrightProvider(session_id=session_id)


def _build_x11(*, display: str | None = None, session_id: str | None = None) -> ControlProvider:
    from .providers.x11 import X11ControlProvider

    return X11ControlProvider(display=display)


def _build_terminal(*, display: str | None = None, session_id: str | None = None) -> ControlProvider:
    from .providers.terminal import TerminalControlProvider

    return TerminalControlProvider(session_id=session_id)


def _build_vision(*, display: str | None = None, session_id: str | None = None) -> ControlProvider:
    from .providers.vision import VisionStubProvider

    return VisionStubProvider(display=display, session_id=session_id)


_BUILTIN_FACTORIES: dict[str, ProviderFactory] = {
    "atspi": _build_atspi,
    "uia": _build_uia,
    "ax": _build_ax,
    "browser": _build_browser,
    "x11": _build_x11,
    "terminal": _build_terminal,
    "vision": _build_vision,
}


def default_provider_registry() -> ProviderRegistry:
    from .plugins import get_provider_registry

    return get_provider_registry()

"""Control provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .capabilities import ProviderCapabilities
from .models import ControlBounds, ControlNode, ControlSnapshot
from .selector import ControlSelector
from .session_kind import SessionKind
from .verify_strategy import VerifyStrategy


class ControlProvider(ABC):
    name: str

    @abstractmethod
    def available(self) -> tuple[bool, str]:
        """Return (ready, reason)."""

    @abstractmethod
    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot: ...

    @abstractmethod
    def find(self, selector: ControlSelector) -> list[ControlNode]: ...

    @abstractmethod
    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def focus(self, element_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def set_value(self, element_id: str, value: str) -> dict[str, Any]: ...

    @abstractmethod
    def bounds(self, element_id: str) -> ControlBounds | None: ...

    def capabilities(self) -> ProviderCapabilities:
        """Plugin contract — defaults from builtin descriptor catalog."""
        from .descriptors import descriptor_for

        descriptor = descriptor_for(self.name)
        if descriptor is None:
            return ProviderCapabilities()
        return descriptor.capabilities

    def verify_modes(self) -> frozenset[VerifyStrategy]:
        from .descriptors import descriptor_for

        descriptor = descriptor_for(self.name)
        if descriptor is None:
            return frozenset()
        return descriptor.verify_strategies

    def session_kind(self) -> SessionKind | None:
        from .descriptors import descriptor_for

        descriptor = descriptor_for(self.name)
        if descriptor is None:
            return None
        return descriptor.session_kind

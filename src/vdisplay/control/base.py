"""Control provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import ControlBounds, ControlNode, ControlSnapshot
from .selector import ControlSelector


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

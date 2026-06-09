from __future__ import annotations

from abc import ABC, abstractmethod


class CaptureBackend(ABC):
    @abstractmethod
    def screenshot_png(self, *, display: str | None = None) -> bytes:
        raise NotImplementedError

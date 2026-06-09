from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ProviderResult:
    png: bytes
    provider: str
    detail: str = ""


@runtime_checkable
class CaptureProvider(Protocol):
    name: str

    def available(self) -> tuple[bool, str]: ...

    def capture_full(self) -> bytes: ...

    def capture_region(self, region: tuple[int, int, int, int]) -> bytes: ...

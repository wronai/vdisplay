"""Pointer sample datatypes for HMI watch."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PointerSample:
    x: int | None
    y: int | None
    window_id: str | None = None
    sources: dict[str, tuple[int, int]] = field(default_factory=dict)
    monitor: dict[str, Any] | None = None
    window_title: str | None = None
    app_label: str | None = None
    process_name: str | None = None
    context_x: int | None = None
    context_y: int | None = None
    context_source: str | None = None
    error: str | None = None
    primary: str | None = None
    stale_sources: tuple[str, ...] = ()

    def _format_stale_sources(self) -> str:
        return " ".join(
            f"{name}*=({xy[0]},{xy[1]})" for name, xy in sorted(self.sources.items()) if name in self.stale_sources
        )

    def _format_live_sources(self) -> str:
        return " ".join(
            f"{name}=({xy[0]},{xy[1]})" for name, xy in sorted(self.sources.items()) if name not in self.stale_sources
        )

    def primary_label(self) -> str:
        if self.x is None or self.y is None:
            stale = self._format_stale_sources()
            live = self._format_live_sources()
            extra = " ".join(part for part in (live, stale) if part)
            return f"? [{extra}]" if extra else "?"

        label = self.primary or next(iter(self.sources), "ptr")
        parts = [f"{label}=({self.x},{self.y})"]
        others = [
            f"{name}=({xy[0]},{xy[1]})" + ("*" if name in self.stale_sources else "")
            for name, xy in sorted(self.sources.items())
            if name != label
        ]
        if others:
            parts.append("[" + " ".join(others) + "]")
        return " ".join(parts)

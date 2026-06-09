"""Provider capability flags — what an adapter can do, not which app it targets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderCapabilities:
    can_snapshot: bool = True
    can_find: bool = True
    can_invoke: bool = False
    can_focus: bool = False
    can_set_value: bool = False
    can_type: bool = False
    has_accessibility_tree: bool = False
    has_dom: bool = False
    has_terminal_grid: bool = False
    has_pixel_bounds: bool = False
    supports_semantic_verify: bool = False
    supports_visual_verify: bool = False
    supports_ocr_verify: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DESKTOP_A11Y = ProviderCapabilities(
    can_invoke=True,
    can_focus=True,
    can_set_value=True,
    has_accessibility_tree=True,
    has_pixel_bounds=True,
    supports_semantic_verify=True,
    supports_visual_verify=True,
)

BROWSER_DOM = ProviderCapabilities(
    can_invoke=True,
    can_focus=True,
    can_set_value=True,
    can_type=True,
    has_dom=True,
    has_pixel_bounds=True,
    supports_semantic_verify=True,
    supports_visual_verify=True,
    supports_ocr_verify=True,
)

TERMINAL_GRID = ProviderCapabilities(
    can_invoke=True,
    can_focus=True,
    can_set_value=True,
    can_type=True,
    has_terminal_grid=True,
    supports_semantic_verify=True,
)

POINTER_FALLBACK = ProviderCapabilities(
    can_invoke=True,
    can_focus=True,
    can_set_value=True,
    has_pixel_bounds=True,
    supports_visual_verify=True,
)

VISION_SURFACE = ProviderCapabilities(
    can_find=True,
    can_invoke=True,
    can_focus=True,
    can_set_value=True,
    has_pixel_bounds=True,
    supports_visual_verify=True,
    supports_ocr_verify=True,
)

"""Cross-repo integrations: ScreenContext, IMGL analysis, VQL metadata export."""

from .pipeline import enrich_capture_payload, observe_screen
from .screen_context import ScreenContext, screen_context_from_capture
from .vql_bridge import build_imgl_layers
from .vql_normalize import normalize_vql_ui_elements

__all__ = [
    "ScreenContext",
    "build_imgl_layers",
    "enrich_capture_payload",
    "observe_screen",
    "normalize_vql_ui_elements",
    "screen_context_from_capture",
]

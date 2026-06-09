"""Window discovery — scan, normalize, filter, rank, query."""

from .filter import (
    is_internal_window,
    matches_app,
    matches_class,
    matches_title,
)
from .normalize import derive_app_label, parse_wm_class
from .query import (
    find_companion_frames,
    find_windows,
    inspect_window,
    list_windows_enriched,
    pick_best_window,
)
from .rank import dedupe_app_windows

# Backward-compatible private aliases used in tests
_dedupe_app_windows = dedupe_app_windows
_derive_app_label = derive_app_label
_is_internal_window = is_internal_window
_matches_app = matches_app
_matches_title = matches_title
_parse_wm_class = parse_wm_class

__all__ = [
    "dedupe_app_windows",
    "derive_app_label",
    "find_companion_frames",
    "find_windows",
    "inspect_window",
    "is_internal_window",
    "list_windows_enriched",
    "matches_app",
    "matches_class",
    "matches_title",
    "parse_wm_class",
    "pick_best_window",
    "_dedupe_app_windows",
    "_derive_app_label",
    "_is_internal_window",
    "_matches_app",
    "_matches_title",
    "_parse_wm_class",
]

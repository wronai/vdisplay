"""Analyze event history stored under ``.vdisplay/**``."""

from .analyze import analyze_history, collect_events
from .loader import (
    discover_run_dirs,
    discover_session_dirs,
    load_history_index,
    load_run_detail,
    load_session_ref,
    resolve_metadata_root,
)
from .models import AnalyzeReport, HistoryIndex, RunRecord, SessionRef, TaskRecord

__all__ = [
    "AnalyzeReport",
    "HistoryIndex",
    "RunRecord",
    "SessionRef",
    "TaskRecord",
    "analyze_history",
    "collect_events",
    "discover_run_dirs",
    "discover_session_dirs",
    "load_history_index",
    "load_run_detail",
    "load_session_ref",
    "resolve_metadata_root",
]

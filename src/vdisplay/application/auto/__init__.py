"""Planfile-driven desktop automation runner."""

from .runner import AutoRunResult, run_auto_loop, run_auto_once
from .tasks import AutoTask, load_auto_tasks

__all__ = [
    "AutoRunResult",
    "AutoTask",
    "load_auto_tasks",
    "run_auto_loop",
    "run_auto_once",
]

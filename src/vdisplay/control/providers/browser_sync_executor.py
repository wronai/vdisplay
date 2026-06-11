"""Run Playwright sync API on a single dedicated thread (safe under asyncio agents)."""

from __future__ import annotations

import atexit
import concurrent.futures
import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_executor: concurrent.futures.ThreadPoolExecutor | None = None
_tls = threading.local()


def _get_executor() -> concurrent.futures.ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="vdisplay-playwright",
        )
        atexit.register(shutdown_browser_sync)
    return _executor


def in_browser_thread() -> bool:
    return bool(getattr(_tls, "active", False))


def run_browser_sync(func: Callable[..., T], /, *args, **kwargs) -> T:
    """Execute Playwright sync work on the dedicated browser thread."""
    if in_browser_thread():
        return func(*args, **kwargs)

    def _run() -> T:
        _tls.active = True
        try:
            return func(*args, **kwargs)
        finally:
            _tls.active = False

    return _get_executor().submit(_run).result()


def shutdown_browser_sync() -> None:
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=True)
        _executor = None

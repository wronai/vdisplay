"""Application use-cases — single execution layer for all interfaces."""

from . import commands, errors

__all__ = ["capture", "commands", "discovery", "errors", "executor", "info", "session"]


def __getattr__(name: str):
    if name == "executor":
        from . import executor as executor_mod

        return executor_mod
    if name in {"capture", "discovery", "info", "session"}:
        from . import services

        return getattr(services, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

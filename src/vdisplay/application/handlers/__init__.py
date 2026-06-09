"""Per-verb command handlers for local and agent execution."""

from .agent import execute_agent
from .local import execute_local

__all__ = ["execute_agent", "execute_local"]

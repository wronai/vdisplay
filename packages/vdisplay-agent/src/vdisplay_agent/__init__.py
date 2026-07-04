"""vdisplay-agent — local display automation broker."""

from importlib.metadata import PackageNotFoundError, version as _dist_version

from .runtime import AgentRuntime

try:
    __version__ = _dist_version("vdisplay-agent")
except PackageNotFoundError:  # source checkout without an installed dist
    __version__ = "0.0.0"

__all__ = ["AgentRuntime", "__version__"]

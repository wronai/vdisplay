"""Control backends."""

from .atspi import AtspiControlProvider
from .x11 import X11ControlProvider

__all__ = ["AtspiControlProvider", "X11ControlProvider"]

"""Control backends."""

from .atspi import AtspiControlProvider
from .ax import AxControlProvider, AxStubProvider
from .uia import UiaControlProvider, UiaStubProvider
from .vision import VisionProviderStub, VisionStubProvider
from .x11 import X11ControlProvider

__all__ = [
    "AtspiControlProvider",
    "AxControlProvider",
    "AxStubProvider",
    "UiaControlProvider",
    "UiaStubProvider",
    "VisionProviderStub",
    "VisionStubProvider",
    "X11ControlProvider",
]

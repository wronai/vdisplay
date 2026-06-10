"""Example Windows UIA plugin — wraps core UiaControlProvider (PR-23)."""

from __future__ import annotations

import os
import sys

from vdisplay.control.descriptors import ProviderDescriptor
from vdisplay.control.models import ControlBounds, ControlRole
from vdisplay.control.providers.uia import UiaControlProvider
from vdisplay.control.providers.uia_impl import MockUiaBackend, UiaElementRecord, UiaBackend
from vdisplay.control.verify_strategy import VerifyStrategy

from vdisplay.control.capabilities import DESKTOP_A11Y

EXAMPLE_UIA_DESCRIPTOR = ProviderDescriptor(
    provider_id="example-uia",
    adapter_kind="example_windows_uia",
    environments=frozenset({"desktop"}),
    session_kind=None,
    capabilities=DESKTOP_A11Y,
    actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
    verify_strategies=frozenset({VerifyStrategy.STRUCTURE, VerifyStrategy.TEXT, VerifyStrategy.HYBRID}),
    required_deps=("Windows UIA / COM", "comtypes"),
    aliases=frozenset({"example-uia-automation", "demo-uia"}),
    base_score=40,
    cost=0.2,
    risk=0.15,
)

_DEMO_RECORDS = [
    UiaElementRecord(
        key="demo-save",
        name="Save",
        role=ControlRole.BUTTON,
        bounds=ControlBounds(x=120, y=240, width=72, height=28),
        automation_id="SaveButton",
        app_label="Notepad",
        window_title="Untitled - Notepad",
    ),
    UiaElementRecord(
        key="demo-edit",
        name="Document",
        role=ControlRole.INPUT,
        bounds=ControlBounds(x=8, y=60, width=640, height=400),
        automation_id="TextEditor",
        app_label="Notepad",
        window_title="Untitled - Notepad",
    ),
]


def _use_mock_backend() -> bool:
    flag = os.environ.get("VDISPLAY_UIA_MOCK", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return True
    return sys.platform != "win32"


def _demo_backend() -> UiaBackend:
    return MockUiaBackend(_DEMO_RECORDS)


class ExampleUiaProvider(UiaControlProvider):
    """UIA adapter — native on Windows, mock tree elsewhere for CI/docs."""

    name = "example-uia"

    def __init__(
        self,
        *,
        display: str | None = None,
        session_id: str | None = None,
        backend: UiaBackend | None = None,
    ) -> None:
        if backend is None and _use_mock_backend():
            backend = _demo_backend()
        super().__init__(display=display, session_id=session_id, backend=backend)

    def available(self) -> tuple[bool, str]:
        if isinstance(self._backend, MockUiaBackend):
            return True, "example-uia mock backend (set VDISPLAY_UIA_MOCK=0 on Windows for native UIA)"
        return super().available()


def build_example_uia(
    *,
    display: str | None = None,
    session_id: str | None = None,
    backend: UiaBackend | None = None,
) -> ExampleUiaProvider:
    if backend is None and _use_mock_backend():
        backend = _demo_backend()
    return ExampleUiaProvider(display=display, session_id=session_id, backend=backend)

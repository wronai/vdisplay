"""Example macOS AX plugin — wraps core AxControlProvider (PR-23)."""

from __future__ import annotations

import os
import sys

from vdisplay.control.capabilities import DESKTOP_A11Y
from vdisplay.control.descriptors import ProviderDescriptor
from vdisplay.control.models import ControlBounds, ControlRole
from vdisplay.control.providers.ax import AxControlProvider
from vdisplay.control.providers.ax_impl import AxBackend, AxElementRecord, MockAxBackend
from vdisplay.control.verify_strategy import VerifyStrategy

EXAMPLE_AX_DESCRIPTOR = ProviderDescriptor(
    provider_id="example-ax",
    adapter_kind="example_darwin_ax",
    environments=frozenset({"desktop"}),
    session_kind=None,
    capabilities=DESKTOP_A11Y,
    actions=frozenset({"snapshot", "find", "invoke", "focus", "set_value", "bounds"}),
    verify_strategies=frozenset({VerifyStrategy.STRUCTURE, VerifyStrategy.TEXT, VerifyStrategy.HYBRID}),
    required_deps=("macOS Accessibility API", "pyobjc-framework-ApplicationServices"),
    aliases=frozenset({"example-macos-ax", "demo-ax"}),
    base_score=40,
    cost=0.2,
    risk=0.15,
)

_DEMO_RECORDS = [
    AxElementRecord(
        key="demo-ok",
        name="OK",
        role=ControlRole.BUTTON,
        bounds=ControlBounds(x=420, y=320, width=64, height=32),
        automation_id="OKButton",
        app_label="Calculator",
        window_title="Calculator",
    ),
    AxElementRecord(
        key="demo-display",
        name="Display",
        role=ControlRole.LABEL,
        bounds=ControlBounds(x=40, y=40, width=200, height=48),
        automation_id="DisplayLabel",
        app_label="Calculator",
        window_title="Calculator",
    ),
]


def _use_mock_backend() -> bool:
    flag = os.environ.get("VDISPLAY_AX_MOCK", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return True
    return sys.platform != "darwin"


def _demo_backend() -> AxBackend:
    return MockAxBackend(_DEMO_RECORDS)


class ExampleAxProvider(AxControlProvider):
    """AX adapter — native on macOS, mock tree elsewhere for CI/docs."""

    name = "example-ax"

    def __init__(
        self,
        *,
        display: str | None = None,
        session_id: str | None = None,
        backend: AxBackend | None = None,
    ) -> None:
        if backend is None and _use_mock_backend():
            backend = _demo_backend()
        super().__init__(display=display, session_id=session_id, backend=backend)

    def available(self) -> tuple[bool, str]:
        if isinstance(self._backend, MockAxBackend):
            return True, "example-ax mock backend (set VDISPLAY_AX_MOCK=0 on macOS for native AX)"
        return super().available()


def build_example_ax(
    *,
    display: str | None = None,
    session_id: str | None = None,
    backend: AxBackend | None = None,
) -> ExampleAxProvider:
    if backend is None and _use_mock_backend():
        backend = _demo_backend()
    return ExampleAxProvider(display=display, session_id=session_id, backend=backend)

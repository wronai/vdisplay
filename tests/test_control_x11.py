"""X11 fallback provider click/type sequencing."""

from __future__ import annotations

import pytest

from vdisplay.control.models import ControlBounds, ControlNode, ControlRole
from vdisplay.control.providers.x11 import X11ControlProvider


class _FakeInput:
    def __init__(self) -> None:
        self.moves: list[tuple[int, int]] = []
        self.clicks: list[int] = []
        self.typed: list[str] = []

    def move(self, x: int, y: int) -> None:
        self.moves.append((x, y))

    def click(self, button: int) -> None:
        self.clicks.append(button)

    def type_text(self, value: str) -> None:
        self.typed.append(value)


def test_x11_set_value_clicks_before_typing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeInput()
    provider = X11ControlProvider(display=":99")
    provider._input = fake  # type: ignore[assignment]
    node = ControlNode(
        id="x11:42",
        backend="x11-fallback",
        role=ControlRole.WINDOW,
        name="Demo",
        bounds=ControlBounds(x=10, y=20, width=200, height=100),
        window_id="42",
    )
    provider._cache = type(
        "Snap",
        (),
        {"nodes": {"x11:42": node}},
    )()
    monkeypatch.setenv("VDISPLAY_CONTROL_FOCUS_MS", "0")
    monkeypatch.setenv("VDISPLAY_CONTROL_POINTER_SETTLE_MS", "0")

    result = provider.set_value("x11:42", "hello")

    assert result["ok"] is True
    assert fake.moves == [(110, 70)]
    assert fake.clicks == [1]
    assert fake.typed == ["hello"]


def test_x11_invoke_clicks_center(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeInput()
    provider = X11ControlProvider(display=":99")
    provider._input = fake  # type: ignore[assignment]
    node = ControlNode(
        id="x11:7",
        backend="x11-fallback",
        role=ControlRole.WINDOW,
        name="Win",
        bounds=ControlBounds(x=0, y=0, width=100, height=50),
        window_id="7",
    )
    provider._cache = type(
        "Snap",
        (),
        {"nodes": {"x11:7": node}},
    )()
    monkeypatch.setenv("VDISPLAY_CONTROL_POINTER_SETTLE_MS", "0")

    result = provider.invoke("x11:7")

    assert result["ok"] is True
    assert fake.moves == [(50, 25)]
    assert fake.clicks == [1]

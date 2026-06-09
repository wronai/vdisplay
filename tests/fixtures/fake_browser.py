"""Playwright page mocks for browser provider unit tests."""

from __future__ import annotations

from typing import Any


class FakeElement:
    def __init__(self, spec: dict) -> None:
        self._spec = spec
        self.filled: str | None = None
        self.clicked = False
        self.focused = False

    def evaluate(self, script: str, *args) -> Any:
        del args
        if "focused" in script:
            return {
                "tag": self._spec.get("tag", "button"),
                "focused": self.focused,
                "checked": bool(self._spec.get("attrs", {}).get("checked")),
                "disabled": bool(self._spec.get("attrs", {}).get("disabled")),
                "visible": True,
                "value": self.filled or self._spec.get("attrs", {}).get("value"),
            }
        return self._spec.get("tag", "button")

    def bounding_box(self) -> dict[str, float]:
        return self._spec.get("box", {"x": 1, "y": 2, "width": 80, "height": 24})

    def inner_text(self) -> str:
        return self._spec.get("text", "")

    def get_attribute(self, name: str) -> str | None:
        return self._spec.get("attrs", {}).get(name)

    def click(self, *, timeout: int | None = None) -> None:
        del timeout
        self.clicked = True

    def fill(self, value: str) -> None:
        self.filled = value
        attrs = self._spec.setdefault("attrs", {})
        attrs["value"] = value

    def focus(self) -> None:
        self.focused = True


class FakeLocator:
    def __init__(self, elements: list[FakeElement]) -> None:
        self._elements = elements

    def count(self) -> int:
        return len(self._elements)

    def nth(self, index: int) -> FakeElement:
        return self._elements[index]

    @property
    def first(self) -> FakeElement:
        return self._elements[0]


class FakePage:
    url = "https://example.test/app"

    def __init__(self) -> None:
        self._elements = [
            FakeElement({"tag": "button", "text": "Increment", "attrs": {"id": "inc", "aria-label": "Increment"}}),
            FakeElement({"tag": "input", "text": "", "attrs": {"name": "query", "value": "hi"}}),
        ]
        self.navigated: str | None = None

    def goto(self, url: str, *, wait_until: str = "domcontentloaded") -> None:
        del wait_until
        self.navigated = url
        self.url = url

    def title(self) -> str:
        return "Example App"

    def query_selector_all(self, selector: str) -> list[FakeElement]:
        del selector
        return list(self._elements)

    def locator(self, selector: str) -> FakeLocator:
        if selector == "#inc":
            return FakeLocator([self._elements[0]])
        if selector == 'input[name="query"]':
            return FakeLocator([self._elements[1]])
        return FakeLocator([])

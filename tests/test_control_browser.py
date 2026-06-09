from __future__ import annotations

from vdisplay.control.engine import resolve_provider
from vdisplay.control.providers.browser_playwright import BrowserPlaywrightProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.exceptions import BackendNotAvailableError


class FakeElement:
    def __init__(self, spec: dict) -> None:
        self._spec = spec
        self.filled: str | None = None
        self.clicked = False
        self.focused = False

    def evaluate(self, script: str) -> str:
        del script
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


def test_browser_provider_snapshot_and_find() -> None:
    provider = BrowserPlaywrightProvider(page=FakePage())
    snapshot = provider.snapshot(app="https://example.test/app")
    assert len(snapshot.nodes) == 2

    matches = provider.find(ControlSelector(role="button", name="Increment"))
    assert len(matches) == 1
    assert matches[0].role.value == "button"

    css_matches = provider.find(ControlSelector(dom_css="#inc"))
    assert len(css_matches) == 1
    assert css_matches[0].provider_ref == "browser:loc:#inc:0"


def test_browser_provider_actions() -> None:
    page = FakePage()
    provider = BrowserPlaywrightProvider(page=page)
    snapshot = provider.snapshot()
    button_id = next(node.id for node in snapshot.nodes.values() if node.name == "Increment")
    provider.invoke(button_id)
    assert page._elements[0].clicked is True

    input_id = next(node.id for node in snapshot.nodes.values() if node.role.value == "input")
    provider.set_value(input_id, "hello")
    assert page._elements[1].filled == "hello"


def test_resolve_browser_backend_with_injected_page() -> None:
    provider = BrowserPlaywrightProvider(page=FakePage())
    assert provider.available()[0] is True


def test_resolve_browser_backend_without_playwright(monkeypatch) -> None:
    import vdisplay.control.providers.browser_playwright as mod

    monkeypatch.setattr(mod, "_playwright_available", lambda: (False, "missing"))
    try:
        resolve_provider("browser")
        raised = False
    except BackendNotAvailableError:
        raised = True
    assert raised

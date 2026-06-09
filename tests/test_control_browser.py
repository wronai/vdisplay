from __future__ import annotations

from fixtures.fake_browser import FakePage
from vdisplay.control.engine import resolve_provider
from vdisplay.control.providers.browser_playwright import BrowserPlaywrightProvider
from vdisplay.control.selector import ControlSelector
from vdisplay.exceptions import BackendNotAvailableError


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

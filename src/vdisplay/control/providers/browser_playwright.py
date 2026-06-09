"""Browser control provider via Playwright (optional dependency)."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from ..base import ControlProvider
from ..models import (
    ControlAction,
    ControlActionKind,
    ControlBounds,
    ControlNode,
    ControlRole,
    ControlSnapshot,
    ElementCapabilities,
)
from ..selector import ControlSelector, find_matches

_INTERACTIVE_SELECTORS = "button, input, textarea, select, a, [role='button'], [role='textbox']"

_TAG_ROLE = {
    "button": ControlRole.BUTTON,
    "input": ControlRole.INPUT,
    "textarea": ControlRole.INPUT,
    "select": ControlRole.COMBOBOX,
    "a": ControlRole.UNKNOWN,
}


class _PageLike(Protocol):
    url: str

    def goto(self, url: str, *, wait_until: str = "domcontentloaded") -> None: ...

    def title(self) -> str: ...

    def query_selector_all(self, selector: str) -> list[Any]: ...

    def locator(self, selector: str) -> Any: ...


class _ElementLike(Protocol):
    def evaluate(self, script: str) -> Any: ...

    def bounding_box(self) -> dict[str, float] | None: ...

    def inner_text(self) -> str: ...

    def get_attribute(self, name: str) -> str | None: ...

    def click(self, *, timeout: int | None = None) -> None: ...

    def fill(self, value: str) -> None: ...

    def focus(self) -> None: ...


def _playwright_available() -> tuple[bool, str]:
    try:
        import playwright  # noqa: F401

        return True, "playwright available"
    except ImportError:
        return False, "playwright not installed (pip install playwright && playwright install)"


def _role_for_element(element: _ElementLike) -> ControlRole:
    tag = (element.evaluate("el => el.tagName.toLowerCase()") or "").lower()
    explicit = element.get_attribute("role")
    if explicit == "button":
        return ControlRole.BUTTON
    if explicit == "textbox":
        return ControlRole.INPUT
    input_type = (element.get_attribute("type") or "").lower()
    if tag == "input" and input_type == "checkbox":
        return ControlRole.CHECKBOX
    return _TAG_ROLE.get(tag, ControlRole.UNKNOWN)


def _capabilities_for(role: ControlRole) -> ElementCapabilities:
    if role == ControlRole.BUTTON:
        return ElementCapabilities(activate=True, focus=True)
    if role == ControlRole.INPUT:
        return ElementCapabilities(focus=True, set_value=True, text_read=True, text_write=True)
    if role == ControlRole.CHECKBOX:
        return ElementCapabilities(toggle=True, focus=True)
    if role == ControlRole.COMBOBOX:
        return ElementCapabilities(select=True, focus=True, set_value=True)
    return ElementCapabilities(focus=True)


def _actions_for(role: ControlRole) -> list[ControlAction]:
    if role == ControlRole.BUTTON:
        return [ControlAction(kind=ControlActionKind.INVOKE, name="click")]
    if role in {ControlRole.INPUT, ControlRole.COMBOBOX}:
        return [
            ControlAction(kind=ControlActionKind.FOCUS, name="focus"),
            ControlAction(kind=ControlActionKind.SET_VALUE, name="fill"),
        ]
    return [ControlAction(kind=ControlActionKind.FOCUS, name="focus")]


def _bounds_from_box(box: dict[str, float] | None) -> ControlBounds | None:
    if not box:
        return None
    return ControlBounds(
        int(box.get("x", 0)),
        int(box.get("y", 0)),
        int(box.get("width", 0)),
        int(box.get("height", 0)),
    )


def _node_from_element(
    element: _ElementLike,
    *,
    backend: str,
    window_id: str | None,
    app_label: str | None,
    window_title: str | None,
    provider_ref: str | None = None,
) -> ControlNode:
    role = _role_for_element(element)
    name = (
        element.get_attribute("aria-label")
        or element.get_attribute("name")
        or element.get_attribute("id")
        or (element.inner_text() or "").strip()
        or None
    )
    text_value = element.get_attribute("value") or ((element.inner_text() or "").strip() or None)
    node_id = provider_ref or f"browser:{uuid.uuid4().hex[:12]}"
    return ControlNode(
        id=node_id,
        backend=backend,
        role=role,
        name=name,
        bounds=_bounds_from_box(element.bounding_box()),
        window_id=window_id,
        app_label=app_label,
        window_title=window_title,
        provider_ref=provider_ref or node_id,
        actions=_actions_for(role),
        capabilities=_capabilities_for(role),
        text_value=text_value,
        state={"tag": element.evaluate("el => el.tagName.toLowerCase()")},
    )


class BrowserPlaywrightProvider(ControlProvider):
    name = "browser-playwright"

    def __init__(self, *, page: _PageLike | None = None, default_url: str | None = None) -> None:
        self._page = page
        self._default_url = default_url
        self._playwright = None
        self._browser = None

    def available(self) -> tuple[bool, str]:
        if self._page is not None:
            return True, "injected browser page"
        return _playwright_available()

    def _ensure_page(self, *, app: str | None = None) -> _PageLike:
        if self._page is not None:
            page = self._page
        else:
            from playwright.sync_api import sync_playwright

            if self._playwright is None:
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(headless=True)
                self._page = self._browser.new_page()
            page = self._page
        target_url = app or self._default_url
        if target_url and target_url.startswith(("http://", "https://", "file://")):
            if getattr(page, "url", "") != target_url:
                page.goto(target_url)
        return page

    def snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        del max_depth  # DOM snapshot is flat for MVP
        page = self._ensure_page(app=app)
        window_title = page.title()
        app_label = app or page.url
        nodes: dict[str, ControlNode] = {}
        root_ids: list[str] = []
        for index, element in enumerate(page.query_selector_all(_INTERACTIVE_SELECTORS)):
            provider_ref = f"browser:dom:{index}"
            node = _node_from_element(
                element,
                backend=self.name,
                window_id=window_id or page.url,
                app_label=app_label,
                window_title=window_title,
                provider_ref=provider_ref,
            )
            nodes[node.id] = node
            root_ids.append(node.id)
        return ControlSnapshot(
            backend=self.name,
            window_id=window_id or page.url,
            app_label=app_label,
            nodes=nodes,
            root_ids=root_ids,
        )

    def find(self, selector: ControlSelector) -> list[ControlNode]:
        if selector.dom_css or selector.dom_xpath:
            page = self._ensure_page(app=selector.app)
            query = selector.dom_css or selector.dom_xpath
            locator = page.locator(query)
            matches: list[ControlNode] = []
            count = locator.count()
            for index in range(count):
                element = locator.nth(index)
                node = _node_from_element(
                    element,
                    backend=self.name,
                    window_id=page.url,
                    app_label=selector.app or page.url,
                    window_title=page.title(),
                    provider_ref=f"browser:loc:{query}:{index}",
                )
                matches.append(node)
            if selector.index:
                if selector.index < len(matches):
                    return [matches[selector.index]]
                return []
            return matches
        snapshot = self.snapshot(app=selector.app)
        return find_matches(snapshot.nodes, selector)

    def _resolve_element(self, element_id: str) -> tuple[_PageLike, _ElementLike]:
        page = self._ensure_page()
        if element_id.startswith("browser:loc:"):
            _, _, query, index_raw = element_id.split(":", 3)
            return page, page.locator(query).nth(int(index_raw))
        if element_id.startswith("browser:dom:"):
            index = int(element_id.rsplit(":", 1)[-1])
            return page, page.query_selector_all(_INTERACTIVE_SELECTORS)[index]
        if element_id.startswith("browser:"):
            locator = page.locator(f"[data-vdisplay-ref='{element_id}']")
            if locator.count():
                return page, locator.first
        raise KeyError(f"unknown browser element: {element_id}")

    def invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        del action
        _, element = self._resolve_element(element_id)
        element.click()
        return {"ok": True, "action": "invoke", "element_id": element_id, "backend": self.name}

    def focus(self, element_id: str) -> dict[str, Any]:
        _, element = self._resolve_element(element_id)
        element.focus()
        return {"ok": True, "action": "focus", "element_id": element_id, "backend": self.name}

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        _, element = self._resolve_element(element_id)
        element.fill(value)
        return {"ok": True, "action": "set_value", "element_id": element_id, "backend": self.name, "value": value}

    def bounds(self, element_id: str) -> ControlBounds | None:
        _, element = self._resolve_element(element_id)
        return _bounds_from_box(element.bounding_box())

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
        self._page = None

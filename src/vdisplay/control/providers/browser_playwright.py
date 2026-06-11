"""Browser control provider via Playwright (optional dependency)."""

from __future__ import annotations

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
from .browser_session import BrowserSessionRegistry, default_registry

_INTERACTIVE_SELECTORS = "button, input, textarea, select, a, [role='button'], [role='textbox']"

_TAG_ROLE = {
    "button": ControlRole.BUTTON,
    "input": ControlRole.INPUT,
    "textarea": ControlRole.INPUT,
    "select": ControlRole.COMBOBOX,
    "a": ControlRole.UNKNOWN,
}

_DOM_STATE_SCRIPT = """el => ({
  tag: el.tagName.toLowerCase(),
  focused: document.activeElement === el,
  checked: !!el.checked,
  disabled: !!el.disabled,
  visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
  value: el.value ?? null,
})"""


class _PageLike(Protocol):
    url: str

    def goto(self, url: str, *, wait_until: str = "domcontentloaded") -> None: ...

    def title(self) -> str: ...

    def query_selector_all(self, selector: str) -> list[Any]: ...

    def locator(self, selector: str) -> Any: ...


class _ElementLike(Protocol):
    def evaluate(self, script: str, *args: Any) -> Any: ...

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
        from ...utils import auto_install_package
        try:
            auto_install_package("playwright", post_install=[["playwright", "install", "chromium"]])
            import playwright  # noqa: F401
            return True, "playwright available (auto-installed)"
        except Exception as exc:
            return False, f"playwright auto-install failed: {exc}"


def _role_for_element(element: _ElementLike) -> ControlRole:
    raw = element.evaluate("el => el.tagName.toLowerCase()")
    if isinstance(raw, dict):
        tag = str(raw.get("tag", "")).lower()
    else:
        tag = (raw or "").lower()
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


def _dom_state(element: _ElementLike) -> dict[str, Any]:
    try:
        payload = element.evaluate(_DOM_STATE_SCRIPT)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {"tag": element.evaluate("el => el.tagName.toLowerCase()")}


def _node_from_element(
    element: _ElementLike,
    *,
    backend: str,
    window_id: str | None,
    app_label: str | None,
    window_title: str | None,
    provider_ref: str,
) -> ControlNode:
    role = _role_for_element(element)
    dom_state = _dom_state(element)
    name = (
        element.get_attribute("aria-label")
        or element.get_attribute("name")
        or element.get_attribute("id")
        or (element.inner_text() or "").strip()
        or None
    )
    text_value = element.get_attribute("value") or dom_state.get("value") or ((element.inner_text() or "").strip() or None)
    return ControlNode(
        id=provider_ref,
        backend=backend,
        role=role,
        name=name,
        bounds=_bounds_from_box(element.bounding_box()),
        window_id=window_id,
        app_label=app_label,
        window_title=window_title,
        provider_ref=provider_ref,
        actions=_actions_for(role),
        capabilities=_capabilities_for(role),
        text_value=text_value if isinstance(text_value, str) else None,
        state=dom_state,
    )


class BrowserPlaywrightProvider(ControlProvider):
    name = "browser-playwright"

    def __init__(
        self,
        *,
        session_id: str | None = None,
        registry: BrowserSessionRegistry | None = None,
        page: _PageLike | None = None,
        default_url: str | None = None,
    ) -> None:
        self._session_id = session_id
        self._registry = registry or default_registry()
        self._legacy_page = page
        self._default_url = default_url

    def available(self) -> tuple[bool, str]:
        if self._legacy_page is not None:
            return True, "injected browser page"
        return _playwright_available()

    def _resolve_session_id(self, *, app: str | None = None, window_id: str | None = None) -> str | None:
        if self._session_id:
            return self._session_id
        if window_id and self._registry.get(window_id) is not None:
            return window_id
        if app and self._registry.get(app) is not None:
            return app
        if self._legacy_page is not None:
            return None
        sessions = self._registry.list_ids()
        if not sessions:
            from ...exceptions import VDisplayError
            raise VDisplayError(
                "no browser session open; use browser_open or POST /session/browser/open first"
            )
        return sessions[-1]

    def _page_for(self, *, app: str | None = None, window_id: str | None = None) -> _PageLike:
        if self._legacy_page is not None:
            page = self._legacy_page
            target_url = app or self._default_url
            if target_url and target_url.startswith(("http://", "https://", "file://")):
                if getattr(page, "url", "") != target_url:
                    page.goto(target_url)
            return page

        session_id = self._resolve_session_id(app=app, window_id=window_id)
        assert session_id is not None
        try:
            session = self._registry.require(session_id)
        except KeyError as exc:
            from ...exceptions import VDisplayError
            raise VDisplayError(str(exc)) from exc
        page = session.page
        if page is None:
            from ...exceptions import VDisplayError
            raise VDisplayError(f"browser session {session_id!r} has no active page")
        target_url = app or session.url or self._default_url
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
        from .browser_sync_executor import run_browser_sync

        return run_browser_sync(
            self._snapshot,
            window_id=window_id,
            app=app,
            max_depth=max_depth,
        )

    def _snapshot(
        self,
        *,
        window_id: str | None = None,
        app: str | None = None,
        max_depth: int = 8,
    ) -> ControlSnapshot:
        del max_depth
        page = self._page_for(app=app, window_id=window_id)
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
        from .browser_sync_executor import run_browser_sync

        return run_browser_sync(self._find, selector)

    def _find(self, selector: ControlSelector) -> list[ControlNode]:
        if selector.dom_css or selector.dom_xpath:
            page = self._page_for(app=selector.app, window_id=selector.window_id or selector.session_id)
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
        snapshot = self.snapshot(app=selector.app, window_id=selector.window_id or selector.session_id)
        return find_matches(snapshot.nodes, selector)

    def _resolve_element(self, element_id: str, *, app: str | None = None, window_id: str | None = None) -> tuple[_PageLike, _ElementLike]:
        page = self._page_for(app=app, window_id=window_id)
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
        from .browser_sync_executor import run_browser_sync

        return run_browser_sync(self._invoke, element_id, action=action)

    def _invoke(self, element_id: str, *, action: str | None = None) -> dict[str, Any]:
        del action
        _, element = self._resolve_element(element_id)
        element.click()
        return {"ok": True, "action": "invoke", "element_id": element_id, "backend": self.name}

    def focus(self, element_id: str) -> dict[str, Any]:
        from .browser_sync_executor import run_browser_sync

        return run_browser_sync(self._focus, element_id)

    def _focus(self, element_id: str) -> dict[str, Any]:
        _, element = self._resolve_element(element_id)
        element.focus()
        return {"ok": True, "action": "focus", "element_id": element_id, "backend": self.name}

    def set_value(self, element_id: str, value: str) -> dict[str, Any]:
        from .browser_sync_executor import run_browser_sync

        return run_browser_sync(self._set_value, element_id, value)

    def _set_value(self, element_id: str, value: str) -> dict[str, Any]:
        _, element = self._resolve_element(element_id)
        element.fill(value)
        return {"ok": True, "action": "set_value", "element_id": element_id, "backend": self.name, "value": value}

    def bounds(self, element_id: str) -> ControlBounds | None:
        from .browser_sync_executor import run_browser_sync

        return run_browser_sync(self._bounds, element_id)

    def _bounds(self, element_id: str) -> ControlBounds | None:
        _, element = self._resolve_element(element_id)
        return _bounds_from_box(element.bounding_box())

    def close(self) -> None:
        if self._session_id:
            self._registry.close(self._session_id)

"""macOS Accessibility (AX) backend — pyobjc ApplicationServices (PR-21)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Protocol

from ..models import ControlBounds, ControlRole
from ..selector import ControlSelector


@dataclass(frozen=True)
class AxElementRecord:
    key: str
    name: str
    role: ControlRole
    bounds: ControlBounds
    automation_id: str | None = None
    app_label: str | None = None
    window_id: str | None = None
    window_title: str | None = None
    provider_ref: str | None = None
    raw: Any | None = None


class AxBackend(Protocol):
    def connect(self) -> None: ...

    def collect_elements(
        self,
        *,
        app: str | None = None,
        window_id: str | None = None,
        max_depth: int = 8,
    ) -> list[AxElementRecord]: ...

    def invoke(self, record: AxElementRecord) -> None: ...

    def focus(self, record: AxElementRecord) -> None: ...

    def set_value(self, record: AxElementRecord, value: str) -> None: ...


_AX_ROLE_MAP: dict[str, ControlRole] = {
    "button": ControlRole.BUTTON,
    "textfield": ControlRole.INPUT,
    "checkbox": ControlRole.CHECKBOX,
    "pop up button": ControlRole.COMBOBOX,
    "menuitem": ControlRole.MENUITEM,
    "statictext": ControlRole.LABEL,
    "window": ControlRole.WINDOW,
    "group": ControlRole.PANEL,
}


def ax_deps_available() -> tuple[bool, str]:
    if sys.platform != "darwin":
        return False, "ax requires macOS host"
    try:
        import ApplicationServices  # noqa: F401
    except ImportError:
        return False, "pyobjc ApplicationServices not installed (optional: pip install -e '.[macos]')"
    return True, "macOS AX via ApplicationServices"


def _role_from_ax(role_value: str) -> ControlRole:
    lowered = (role_value or "").lower()
    for key, role in _AX_ROLE_MAP.items():
        if key in lowered:
            return role
    return ControlRole.UNKNOWN


def _ax_bounds(element: Any) -> ControlBounds:
    from ApplicationServices import (
        AXUIElementCopyAttributeValue,
        kAXPositionAttribute,
        kAXSizeAttribute,
    )

    pos = AXUIElementCopyAttributeValue(element, kAXPositionAttribute, None)[1]
    size = AXUIElementCopyAttributeValue(element, kAXSizeAttribute, None)[1]
    x = int(pos.x) if pos is not None else 0
    y = int(pos.y) if pos is not None else 0
    width = int(size.width) if size is not None else 0
    height = int(size.height) if size is not None else 0
    return ControlBounds(x=x, y=y, width=width, height=height)


def _matches_selector(record: AxElementRecord, selector: ControlSelector) -> bool:
    if selector.role and record.role.value != selector.role.strip().lower():
        return False
    if selector.name and record.name.lower() != selector.name.strip().lower():
        return False
    if selector.name_contains and selector.name_contains.lower() not in (record.name or "").lower():
        return False
    if selector.accessibility_id and selector.accessibility_id != (record.automation_id or record.provider_ref):
        return False
    if selector.app and selector.app.lower() not in (record.app_label or "").lower():
        return False
    if selector.window_title and selector.window_title.lower() not in (record.window_title or "").lower():
        return False
    return True


def filter_records(records: list[AxElementRecord], selector: ControlSelector) -> list[AxElementRecord]:
    return [item for item in records if _matches_selector(item, selector)]


class PyobjcAxBackend:
    """Native macOS AX via ApplicationServices."""

    def __init__(self) -> None:
        self._element_by_key: dict[str, AxElementRecord] = {}

    def connect(self) -> None:
        ready, reason = ax_deps_available()
        if not ready:
            raise RuntimeError(reason)

    def collect_elements(
        self,
        *,
        app: str | None = None,
        window_id: str | None = None,
        max_depth: int = 8,
    ) -> list[AxElementRecord]:
        del window_id
        self.connect()
        from AppKit import NSWorkspace
        from ApplicationServices import (
            AXUIElementCopyAttributeValue,
            AXUIElementCreateApplication,
            kAXChildrenAttribute,
            kAXIdentifierAttribute,
            kAXRoleAttribute,
            kAXTitleAttribute,
        )

        records: list[AxElementRecord] = []
        self._element_by_key.clear()
        workspace = NSWorkspace.sharedWorkspace()
        apps = workspace.runningApplications()
        for running_app in apps:
            app_name = str(running_app.localizedName() or "")
            if app and app.lower() not in app_name.lower():
                continue
            pid = int(running_app.processIdentifier())
            root = AXUIElementCreateApplication(pid)

            def walk(element: Any, depth: int, app_label: str) -> None:
                if depth > max_depth or len(records) >= 500:
                    return
                try:
                    title = str(AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)[1] or "")
                    role_raw = str(AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)[1] or "")
                    identifier = AXUIElementCopyAttributeValue(element, kAXIdentifierAttribute, None)[1]
                    automation_id = str(identifier) if identifier is not None else None
                    bounds = _ax_bounds(element)
                    key = f"{pid}:{automation_id or title or role_raw}:{len(records)}"
                    record = AxElementRecord(
                        key=key,
                        name=title,
                        role=_role_from_ax(role_raw),
                        bounds=bounds,
                        automation_id=automation_id,
                        app_label=app_label,
                        window_title=title if "window" in role_raw.lower() else None,
                        provider_ref=automation_id,
                        raw=element,
                    )
                    records.append(record)
                    self._element_by_key[key] = record
                    children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)[1] or []
                    for child in children:
                        walk(child, depth + 1, app_label)
                except Exception:
                    return

            walk(root, 0, app_name)
        return records

    def _require_record(self, record: AxElementRecord) -> AxElementRecord:
        cached = self._element_by_key.get(record.key)
        if cached is not None and cached.raw is not None:
            return cached
        if record.raw is not None:
            return record
        raise RuntimeError(f"ax element not connected: {record.key}")

    def invoke(self, record: AxElementRecord) -> None:
        from ApplicationServices import AXUIElementPerformAction, kAXPressAction

        element = self._require_record(record).raw
        err = AXUIElementPerformAction(element, kAXPressAction)
        if err != 0:
            raise RuntimeError(f"AX press failed: {err}")

    def focus(self, record: AxElementRecord) -> None:
        from ApplicationServices import AXUIElementPerformAction, kAXRaiseAction

        element = self._require_record(record).raw
        err = AXUIElementPerformAction(element, kAXRaiseAction)
        if err != 0:
            raise RuntimeError(f"AX focus failed: {err}")

    def set_value(self, record: AxElementRecord, value: str) -> None:
        from ApplicationServices import AXUIElementSetAttributeValue, kAXValueAttribute

        element = self._require_record(record).raw
        err = AXUIElementSetAttributeValue(element, kAXValueAttribute, value)
        if err != 0:
            raise RuntimeError(f"AX set value failed: {err}")


class MockAxBackend:
    """In-memory AX backend for tests."""

    def __init__(self, records: list[AxElementRecord] | None = None) -> None:
        self._records = list(records or [])
        self.invoked: list[str] = []
        self.focused: list[str] = []
        self.values: dict[str, str] = {}

    def connect(self) -> None:
        return None

    def collect_elements(
        self,
        *,
        app: str | None = None,
        window_id: str | None = None,
        max_depth: int = 8,
    ) -> list[AxElementRecord]:
        del max_depth, window_id
        records = self._records
        if app:
            records = [item for item in records if app.lower() in (item.app_label or "").lower()]
        return records

    def invoke(self, record: AxElementRecord) -> None:
        self.invoked.append(record.key)

    def focus(self, record: AxElementRecord) -> None:
        self.focused.append(record.key)

    def set_value(self, record: AxElementRecord, value: str) -> None:
        self.values[record.key] = value


def create_ax_backend(backend: AxBackend | None = None) -> AxBackend:
    if backend is not None:
        return backend
    return PyobjcAxBackend()

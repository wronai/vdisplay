"""Windows UI Automation backend — comtypes + UIAutomationCore (PR-21)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Protocol

from ..models import ControlBounds, ControlRole
from ..selector import ControlSelector


@dataclass(frozen=True)
class UiaElementRecord:
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


class UiaBackend(Protocol):
    def connect(self) -> None: ...

    def collect_elements(
        self,
        *,
        app: str | None = None,
        window_id: str | None = None,
        max_depth: int = 8,
    ) -> list[UiaElementRecord]: ...

    def invoke(self, record: UiaElementRecord) -> None: ...

    def focus(self, record: UiaElementRecord) -> None: ...

    def set_value(self, record: UiaElementRecord, value: str) -> None: ...


_UIA_ROLE_MAP: dict[str, ControlRole] = {
    "button": ControlRole.BUTTON,
    "edit": ControlRole.INPUT,
    "checkbox": ControlRole.CHECKBOX,
    "combobox": ControlRole.COMBOBOX,
    "menuitem": ControlRole.MENUITEM,
    "text": ControlRole.LABEL,
    "window": ControlRole.WINDOW,
    "pane": ControlRole.PANEL,
}


def uia_deps_available() -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "uia requires Windows host"
    try:
        import comtypes  # noqa: F401
    except ImportError:
        return False, "comtypes not installed (optional: pip install -e '.[windows]')"
    return True, "Windows UIA via comtypes"


def _role_from_uia(control_type_name: str) -> ControlRole:
    lowered = control_type_name.lower().replace("controltype", "").replace("control", "")
    for key, role in _UIA_ROLE_MAP.items():
        if key in lowered:
            return role
    return ControlRole.UNKNOWN


def _rect_to_bounds(rect: Any) -> ControlBounds:
    return ControlBounds(
        x=int(rect.left),
        y=int(rect.top),
        width=max(0, int(rect.right) - int(rect.left)),
        height=max(0, int(rect.bottom) - int(rect.top)),
    )


def _matches_selector(record: UiaElementRecord, selector: ControlSelector) -> bool:
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
    if selector.window_id and str(selector.window_id) != str(record.window_id or ""):
        return False
    if selector.window_title and selector.window_title.lower() not in (record.window_title or "").lower():
        return False
    return True


def filter_records(records: list[UiaElementRecord], selector: ControlSelector) -> list[UiaElementRecord]:
    return [item for item in records if _matches_selector(item, selector)]


class ComtypesUiaBackend:
    """Native Windows UIA via UIAutomationCore.dll."""

    def __init__(self) -> None:
        self._automation: Any = None
        self._element_by_key: dict[str, UiaElementRecord] = {}

    def connect(self) -> None:
        ready, reason = uia_deps_available()
        if not ready:
            raise RuntimeError(reason)
        import comtypes.client

        comtypes.client.GetModule("UIAutomationCore.dll")
        from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation

        self._automation = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)

    def collect_elements(
        self,
        *,
        app: str | None = None,
        window_id: str | None = None,
        max_depth: int = 8,
    ) -> list[UiaElementRecord]:
        if self._automation is None:
            self.connect()
        from comtypes.gen.UIAutomationClient import TreeScope_Descendants

        root = self._automation.GetRootElement()
        condition = self._automation.CreateTrueCondition()
        elements = root.FindAll(TreeScope_Descendants, condition)
        records: list[UiaElementRecord] = []
        self._element_by_key.clear()
        count = int(elements.Length)
        for index in range(count):
            element = elements.GetElement(index)
            try:
                name = str(element.CurrentName or "")
                automation_id = str(element.CurrentAutomationId or "") or None
                class_name = str(element.CurrentClassName or "")
                control_type = str(element.CurrentControlType)
                runtime = tuple(int(x) for x in element.GetRuntimeId())
                key = f"{'-'.join(str(x) for x in runtime)}"
                bounds = _rect_to_bounds(element.CurrentBoundingRectangle)
                app_label = str(element.CurrentProcessName or class_name or "")
                window_title = name if "window" in control_type.lower() else None
                record = UiaElementRecord(
                    key=key,
                    name=name,
                    role=_role_from_uia(control_type),
                    bounds=bounds,
                    automation_id=automation_id,
                    app_label=app_label,
                    window_id=str(element.CurrentNativeWindowHandle or "") or None,
                    window_title=window_title,
                    provider_ref=automation_id,
                    raw=element,
                )
            except Exception:
                continue
            if app and app.lower() not in (record.app_label or "").lower():
                continue
            if window_id and str(window_id) != str(record.window_id or ""):
                continue
            records.append(record)
            self._element_by_key[key] = record
            if len(records) >= 500:
                break
        return records

    def _require_record(self, record: UiaElementRecord) -> UiaElementRecord:
        cached = self._element_by_key.get(record.key)
        if cached is not None and cached.raw is not None:
            return cached
        if record.raw is not None:
            return record
        raise RuntimeError(f"uia element not connected: {record.key}")

    def invoke(self, record: UiaElementRecord) -> None:
        element = self._require_record(record).raw
        from comtypes.gen.UIAutomationClient import IUIAutomationInvokePattern, UIA_InvokePatternId

        pattern = element.GetCurrentPattern(UIA_InvokePatternId)
        if pattern is None:
            raise RuntimeError("InvokePattern not supported")
        invoke = pattern.QueryInterface(IUIAutomationInvokePattern)
        invoke.Invoke()

    def focus(self, record: UiaElementRecord) -> None:
        element = self._require_record(record).raw
        from comtypes.gen.UIAutomationClient import (
            IUIAutomationSelectionItemPattern,
            TreeScope_Parent,
            UIA_SelectionItemPatternId,
        )

        try:
            element.SetFocus()
            return
        except Exception:
            pass
        pattern = element.GetCurrentPattern(UIA_SelectionItemPatternId)
        if pattern is not None:
            selection = pattern.QueryInterface(IUIAutomationSelectionItemPattern)
            selection.Select()
            return
        parent = element.FindFirst(TreeScope_Parent, self._automation.CreateTrueCondition())
        if parent is not None:
            parent.SetFocus()

    def set_value(self, record: UiaElementRecord, value: str) -> None:
        element = self._require_record(record).raw
        from comtypes.gen.UIAutomationClient import IUIAutomationValuePattern, UIA_ValuePatternId

        pattern = element.GetCurrentPattern(UIA_ValuePatternId)
        if pattern is None:
            raise RuntimeError("ValuePattern not supported")
        value_pattern = pattern.QueryInterface(IUIAutomationValuePattern)
        value_pattern.SetValue(value)


class MockUiaBackend:
    """In-memory UIA backend for tests."""

    def __init__(self, records: list[UiaElementRecord] | None = None) -> None:
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
    ) -> list[UiaElementRecord]:
        del max_depth
        records = self._records
        if app:
            records = [item for item in records if app.lower() in (item.app_label or "").lower()]
        if window_id:
            records = [item for item in records if str(window_id) == str(item.window_id or "")]
        return records

    def invoke(self, record: UiaElementRecord) -> None:
        self.invoked.append(record.key)

    def focus(self, record: UiaElementRecord) -> None:
        self.focused.append(record.key)

    def set_value(self, record: UiaElementRecord, value: str) -> None:
        self.values[record.key] = value


def create_uia_backend(backend: UiaBackend | None = None) -> UiaBackend:
    if backend is not None:
        return backend
    return ComtypesUiaBackend()

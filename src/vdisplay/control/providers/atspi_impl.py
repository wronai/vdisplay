"""AT-SPI implementation (requires system python3-gi)."""

from __future__ import annotations

from typing import Any

from ..models import (
    ControlAction,
    ControlActionKind,
    ControlBounds,
    ControlNode,
    ControlRole,
    ControlSnapshot,
    ElementCapabilities,
)

_ROLE_MAP: dict[str, ControlRole] = {
    "push button": ControlRole.BUTTON,
    "button": ControlRole.BUTTON,
    "toggle button": ControlRole.BUTTON,
    "entry": ControlRole.INPUT,
    "password text": ControlRole.INPUT,
    "text": ControlRole.INPUT,
    "check box": ControlRole.CHECKBOX,
    "combo box": ControlRole.COMBOBOX,
    "menu item": ControlRole.MENUITEM,
    "label": ControlRole.LABEL,
    "panel": ControlRole.PANEL,
    "frame": ControlRole.PANEL,
    "window": ControlRole.WINDOW,
    "application": ControlRole.WINDOW,
}


def _atspi():
    import gi

    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi

    return Atspi


def _map_role(role_name: str | None) -> ControlRole:
    if not role_name:
        return ControlRole.UNKNOWN
    return _ROLE_MAP.get(role_name.strip().lower(), ControlRole.UNKNOWN)


def _atspi_module():
    return _atspi()


def _iface(accessible, name: str):
    getter = getattr(accessible, f"get_{name}", None)
    if getter is None:
        return None
    try:
        return getter()
    except TypeError:
        try:
            return getter(0)
        except Exception:
            return None
    except Exception:
        return None


def _node_actions(accessible) -> list[ControlAction]:
    actions: list[ControlAction] = []
    action_iface = _iface(accessible, "action")
    if action_iface is None:
        return actions
    if action_iface is None:
        return actions
    Atspi = _atspi_module()
    try:
        count = int(Atspi.Action.get_n_actions(action_iface))
    except Exception:
        return actions
    for index in range(count):
        try:
            name = Atspi.Action.get_action_name(action_iface, index)
            desc = Atspi.Action.get_action_description(action_iface, index)
        except Exception:
            name, desc = None, None
        actions.append(
            ControlAction(
                kind=ControlActionKind.INVOKE,
                name=str(name) if name else None,
                description=str(desc) if desc else None,
            )
        )
    return actions


def _text_iface(accessible):
    getter = getattr(accessible, "get_text_iface", None)
    if getter is None:
        return None
    try:
        return getter()
    except Exception:
        return None


def _node_text_value(accessible) -> str | None:
    text_iface = _text_iface(accessible)
    if text_iface is None:
        return None
    Atspi = _atspi_module()
    try:
        count = int(Atspi.Text.get_character_count(text_iface))
        if count <= 0:
            return ""
        return str(Atspi.Text.get_text(text_iface, 0, count))
    except Exception:
        return None


def _provider_ref(accessible, node_id: str) -> str:
    """Native backend handle (D-Bus path), distinct from snapshot-local ``id``."""
    try:
        return str(accessible.get_object().get_path())
    except Exception:
        pass
    try:
        return str(accessible.path)
    except Exception:
        return node_id


def _node_state(accessible, role_name: str) -> dict[str, Any]:
    state: dict[str, Any] = {"role_name": role_name}
    try:
        Atspi = _atspi_module()
        state_set = accessible.get_state_set()
        if state_set is not None:
            for key, state_type in (
                ("focused", Atspi.StateType.FOCUSED),
                ("enabled", Atspi.StateType.ENABLED),
                ("visible", Atspi.StateType.VISIBLE),
                ("expanded", Atspi.StateType.EXPANDED),
                ("checked", Atspi.StateType.CHECKED),
            ):
                try:
                    state[key] = bool(state_set.contains(state_type))
                except Exception:
                    continue
    except Exception:
        pass
    return state


def _node_capabilities(
    accessible,
    actions: list[ControlAction],
    role: ControlRole,
) -> ElementCapabilities:
    text_iface = _text_iface(accessible)
    value_iface = _iface(accessible, "value")
    component = _iface(accessible, "component")
    selection = _iface(accessible, "selection")
    expand_iface = _iface(accessible, "expand_collapse")
    editable = False
    if text_iface is not None:
        try:
            Atspi = _atspi_module()
            editable = bool(Atspi.EditableText.get_editable_text(text_iface))
        except Exception:
            editable = True
    return ElementCapabilities(
        activate=bool(actions),
        focus=component is not None,
        set_value=editable or value_iface is not None,
        text_read=text_iface is not None,
        text_write=editable,
        select=selection is not None,
        toggle=role in {ControlRole.CHECKBOX, ControlRole.BUTTON} and bool(actions),
        expand=expand_iface is not None,
    )


def _node_bounds(accessible) -> ControlBounds | None:
    try:
        Atspi = _atspi()
        extents = accessible.get_extents(Atspi.CoordType.SCREEN)
    except Exception:
        return None
    if extents is None:
        return None
    try:
        x, y, w, h = int(extents.x), int(extents.y), int(extents.width), int(extents.height)
    except Exception:
        return None
    if w <= 0 or h <= 0:
        return None
    return ControlBounds(x=x, y=y, width=w, height=h)


def _application_matches(application, app_filter: str | None, *, max_depth: int = 4) -> bool:
    if not app_filter:
        return True
    needle = app_filter.lower()
    app_name = (application.name or "").lower()
    if needle in app_name:
        return True

    def scan(accessible, depth: int) -> bool:
        if depth > max_depth:
            return False
        name = (accessible.name or "").lower()
        if needle in name:
            return True
        try:
            child_count = accessible.get_child_count()
        except Exception:
            child_count = 0
        for index in range(child_count):
            try:
                child = accessible.get_child_at_index(index)
            except Exception:
                continue
            if child is not None and scan(child, depth + 1):
                return True
        return False

    return scan(application, 0)


def snapshot_dict(
    *,
    window_id: str | None = None,
    app: str | None = None,
    max_depth: int = 8,
) -> dict[str, Any]:
    Atspi = _atspi()
    Atspi.init()
    desktop = Atspi.get_desktop(0)
    nodes: dict[str, ControlNode] = {}
    root_ids: list[str] = []
    app_label: str | None = None

    def walk(
        accessible,
        path: str,
        parent_id: str | None,
        depth: int,
        app_name: str | None,
        window_title: str | None,
    ) -> str:
        node_id = f"atspi:{path}"
        role_name = accessible.get_role_name() or ""
        role = _map_role(role_name)
        name = accessible.name or None
        current_window_title = window_title
        if role in {ControlRole.WINDOW, ControlRole.PANEL} and name:
            current_window_title = name

        actions = _node_actions(accessible)
        node = ControlNode(
            id=node_id,
            backend="atspi",
            role=role,
            name=name,
            description=accessible.description or None,
            bounds=_node_bounds(accessible),
            window_id=window_id,
            app_label=app_name,
            window_title=current_window_title,
            provider_ref=_provider_ref(accessible, node_id),
            state=_node_state(accessible, role_name),
            actions=actions,
            capabilities=_node_capabilities(accessible, actions, role),
            text_value=_node_text_value(accessible),
            parent_id=parent_id,
        )
        nodes[node_id] = node
        if parent_id and parent_id in nodes:
            nodes[parent_id].children_ids.append(node_id)
        if parent_id is None:
            root_ids.append(node_id)
        if depth >= max_depth:
            return node_id
        try:
            child_count = accessible.get_child_count()
        except Exception:
            child_count = 0
        for index in range(child_count):
            try:
                child = accessible.get_child_at_index(index)
            except Exception:
                continue
            if child is None:
                continue
            walk(child, f"{path}/{index}", node_id, depth + 1, app_name, current_window_title)
        return node_id

    for app_index in range(desktop.get_child_count()):
        application = desktop.get_child_at_index(app_index)
        if application is None:
            continue
        app_name = application.name or None
        if not _application_matches(application, app):
            continue
        app_label = app_name
        walk(application, str(app_index), None, 0, app_name, None)

    return ControlSnapshot(
        backend="atspi",
        window_id=window_id,
        app_label=app_label,
        nodes=nodes,
        root_ids=root_ids,
    ).to_dict()


def _resolve_accessible(element_id: str):
    Atspi = _atspi()
    Atspi.init()
    path = element_id.removeprefix("atspi:")
    desktop = Atspi.get_desktop(0)
    current = desktop
    for part in [int(item) for item in path.split("/") if item.isdigit()]:
        current = current.get_child_at_index(part)
        if current is None:
            raise RuntimeError(f"AT-SPI element not found: {element_id}")
    return current


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    op = payload.get("op")
    if op == "available":
        return _handle_available()
    if op == "snapshot":
        return {"ok": True, "snapshot": snapshot_dict(**payload.get("params", {}))}
    if op == "invoke":
        return _handle_invoke(payload)
    if op == "focus":
        return _handle_focus(payload)
    if op == "set_value":
        return _handle_set_value(payload)
    raise RuntimeError(f"unknown atspi op: {op}")


def _handle_available() -> dict[str, Any]:
    Atspi = _atspi()
    Atspi.init()
    desktop = Atspi.get_desktop(0)
    if desktop is None:
        return {"ok": False, "reason": "AT-SPI desktop unavailable"}
    return {"ok": True, "reason": "AT-SPI2 bus active (system python)"}


def _handle_invoke(payload: dict[str, Any]) -> dict[str, Any]:
    accessible = _resolve_accessible(str(payload["element_id"]))
    action_iface = _iface(accessible, "action")
    if action_iface is None:
        raise RuntimeError("element has no Action interface")
    Atspi = _atspi_module()
    index = 0
    action = payload.get("action")
    if action:
        for i in range(int(Atspi.Action.get_n_actions(action_iface))):
            if Atspi.Action.get_action_name(action_iface, i) == action:
                index = i
                break
    if not Atspi.Action.do_action(action_iface, index):
        raise RuntimeError("invoke failed")
    return {"ok": True, "element_id": payload["element_id"], "backend": "atspi"}


def _handle_focus(payload: dict[str, Any]) -> dict[str, Any]:
    accessible = _resolve_accessible(str(payload["element_id"]))
    component = _iface(accessible, "component")
    if component is None or not component.grab_focus():
        raise RuntimeError("focus failed")
    return {"ok": True, "element_id": payload["element_id"], "backend": "atspi"}


def _handle_set_value(payload: dict[str, Any]) -> dict[str, Any]:
    accessible = _resolve_accessible(str(payload["element_id"]))
    value = str(payload.get("value") or "")
    text_iface = _text_iface(accessible)
    if text_iface is not None:
        Atspi = _atspi_module()
        Atspi.EditableText.set_text_contents(text_iface, value)
        return {"ok": True, "element_id": payload["element_id"], "backend": "atspi", "method": "text"}
    value_iface = _iface(accessible, "value")
    if value_iface is not None and value_iface.set_current_value(value):
        return {"ok": True, "element_id": payload["element_id"], "backend": "atspi", "method": "value"}
    raise RuntimeError("element supports neither Text nor Value")

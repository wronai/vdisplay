"""AT-SPI implementation (requires system python3-gi)."""

from __future__ import annotations

from typing import Any

from ..models import ControlAction, ControlActionKind, ControlBounds, ControlNode, ControlRole, ControlSnapshot

_ROLE_MAP: dict[str, ControlRole] = {
    "push button": ControlRole.BUTTON,
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


def _node_actions(accessible) -> list[ControlAction]:
    actions: list[ControlAction] = []
    try:
        action_iface = accessible.get_action(0)
    except Exception:
        return actions
    if action_iface is None:
        return actions
    try:
        count = action_iface.n_actions
    except Exception:
        return actions
    for index in range(count):
        try:
            name = action_iface.get_action_name(index)
            desc = action_iface.get_action_description(index)
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


def _node_text_value(accessible) -> str | None:
    try:
        text_iface = accessible.get_text(0)
    except Exception:
        return None
    if text_iface is None:
        return None
    try:
        return str(text_iface.get_text(0, text_iface.character_count))
    except Exception:
        return None


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

    def walk(accessible, path: str, parent_id: str | None, depth: int, app_name: str | None) -> str:
        node_id = f"atspi:{path}"
        role_name = accessible.get_role_name() or ""
        role = _map_role(role_name)
        name = accessible.name or None
        current_app = app_name
        if role == ControlRole.WINDOW and name:
            current_app = name
        if app and current_app and app.lower() not in (current_app or "").lower():
            return node_id

        node = ControlNode(
            id=node_id,
            backend="atspi",
            role=role,
            name=name,
            description=accessible.description or None,
            bounds=_node_bounds(accessible),
            window_id=window_id,
            app_label=current_app,
            state={"role_name": role_name},
            actions=_node_actions(accessible),
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
            walk(child, f"{path}/{index}", node_id, depth + 1, current_app)
        return node_id

    for app_index in range(desktop.get_child_count()):
        application = desktop.get_child_at_index(app_index)
        if application is None:
            continue
        app_name = application.name or None
        if app and app_name and app.lower() not in app_name.lower():
            continue
        app_label = app_name
        walk(application, str(app_index), None, 0, app_name)

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
        Atspi = _atspi()
        Atspi.init()
        desktop = Atspi.get_desktop(0)
        if desktop is None:
            return {"ok": False, "reason": "AT-SPI desktop unavailable"}
        return {"ok": True, "reason": "AT-SPI2 bus active (system python)"}
    if op == "snapshot":
        return {"ok": True, "snapshot": snapshot_dict(**payload.get("params", {}))}
    if op == "invoke":
        accessible = _resolve_accessible(str(payload["element_id"]))
        action_iface = accessible.get_action(0)
        if action_iface is None:
            raise RuntimeError("element has no Action interface")
        index = 0
        action = payload.get("action")
        if action:
            for i in range(action_iface.n_actions):
                if action_iface.get_action_name(i) == action:
                    index = i
                    break
        if not action_iface.doAction(index):
            raise RuntimeError("invoke failed")
        return {"ok": True, "element_id": payload["element_id"], "backend": "atspi"}
    if op == "focus":
        accessible = _resolve_accessible(str(payload["element_id"]))
        component = accessible.get_component(0)
        if component is None or not component.grab_focus():
            raise RuntimeError("focus failed")
        return {"ok": True, "element_id": payload["element_id"], "backend": "atspi"}
    if op == "set_value":
        accessible = _resolve_accessible(str(payload["element_id"]))
        value = str(payload.get("value") or "")
        try:
            text_iface = accessible.get_text(0)
        except Exception:
            text_iface = None
        if text_iface is not None:
            text_iface.set_text(value)
            return {"ok": True, "element_id": payload["element_id"], "backend": "atspi", "method": "text"}
        try:
            value_iface = accessible.get_value(0)
        except Exception:
            value_iface = None
        if value_iface is not None and value_iface.set_current_value(value):
            return {"ok": True, "element_id": payload["element_id"], "backend": "atspi", "method": "value"}
        raise RuntimeError("element supports neither Text nor Value")
    raise RuntimeError(f"unknown atspi op: {op}")

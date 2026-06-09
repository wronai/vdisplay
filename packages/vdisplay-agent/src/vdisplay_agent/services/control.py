"""Control-plane broker services."""

from __future__ import annotations

from typing import Any

from vdisplay.application.services import control as control_svc


def diagnose_control(*, display: str | None = None) -> dict[str, Any]:
    return control_svc.diagnose_control(display=display)


def list_controls(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.controls_list(
        display=body.get("display"),
        window_id=body.get("window_id"),
        app=body.get("app"),
        backend=str(body.get("backend") or "auto"),
        max_depth=int(body.get("max_depth") or 8),
        format=str(body.get("format") or "flat"),
    )


def find_controls(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.controls_find(
        display=body.get("display"),
        backend=str(body.get("backend") or "auto"),
        selector=body.get("selector"),
        name=body.get("name"),
        role=body.get("role"),
        app=body.get("app"),
        window_id=body.get("window_id"),
        index=body.get("index"),
    )


def invoke_control(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.control_click(
        display=body.get("display"),
        backend=str(body.get("backend") or "auto"),
        verify=bool(body.get("verify", False)),
        selector=body.get("selector"),
        name=body.get("name"),
        role=body.get("role"),
        app=body.get("app"),
        window_id=body.get("window_id"),
        index=body.get("index"),
    )


def focus_control(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.control_focus(
        display=body.get("display"),
        backend=str(body.get("backend") or "auto"),
        selector=body.get("selector"),
        name=body.get("name"),
        role=body.get("role"),
        app=body.get("app"),
        window_id=body.get("window_id"),
        index=body.get("index"),
    )


def set_control_value(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.control_set_value(
        display=body.get("display"),
        backend=str(body.get("backend") or "auto"),
        verify=bool(body.get("verify", False)),
        value=str(body.get("value") or ""),
        selector=body.get("selector"),
        name=body.get("name"),
        role=body.get("role"),
        app=body.get("app"),
        window_id=body.get("window_id"),
        index=body.get("index"),
    )

"""Control-plane broker services."""

from __future__ import annotations

from typing import Any

from vdisplay.application.services import control as control_svc


def _selector_kwargs(body: dict[str, Any]) -> dict[str, Any]:
    return {
        "selector": body.get("selector"),
        "name": body.get("name"),
        "role": body.get("role"),
        "app": body.get("app"),
        "window_id": body.get("window_id"),
        "window_title": body.get("window_title"),
        "index": body.get("index"),
        "environment": body.get("environment"),
        "text": body.get("text"),
        "text_contains": body.get("text_contains"),
        "terminal_line": body.get("terminal_line"),
        "terminal_col": body.get("terminal_col"),
        "session_id": body.get("session_id"),
    }


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
        session_id=body.get("session_id"),
    )


def find_controls(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.controls_find(
        display=body.get("display"),
        backend=str(body.get("backend") or "auto"),
        **_selector_kwargs(body),
    )


def invoke_control(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.control_click(
        display=body.get("display"),
        backend=str(body.get("backend") or "auto"),
        verify=bool(body.get("verify", False)),
        screenshot_verify=bool(body.get("screenshot_verify", False)),
        verify_label=body.get("verify_label"),
        verify_selector=body.get("verify_selector"),
        **_selector_kwargs(body),
    )


def focus_control(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.control_focus(
        display=body.get("display"),
        backend=str(body.get("backend") or "auto"),
        verify=bool(body.get("verify", False)),
        screenshot_verify=bool(body.get("screenshot_verify", False)),
        **_selector_kwargs(body),
    )


def set_control_value(body: dict[str, Any]) -> dict[str, Any]:
    return control_svc.control_set_value(
        display=body.get("display"),
        backend=str(body.get("backend") or "auto"),
        verify=bool(body.get("verify", False)),
        screenshot_verify=bool(body.get("screenshot_verify", False)),
        verify_label=body.get("verify_label"),
        verify_selector=body.get("verify_selector"),
        value=str(body.get("value") or ""),
        **_selector_kwargs(body),
    )

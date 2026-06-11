"""End-to-end IDE prompt helper: launch, focus, find chat, set-value."""

from __future__ import annotations

import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any

from .desktop_apps import (
    chat_selectors_for,
    get_desktop_app,
    ide_hints_for,
    launch_env_for,
    map_input_target_candidates,
    map_manifest_path,
    map_submit_target_candidates,
    prompt_chat_selectors_for,
    resolve_map_path,
    submit_selectors_for,
)
from .exceptions import VDisplayError


def _is_wayland_session() -> bool:
    from .hmi.pointer import is_wayland_session

    return is_wayland_session()


def _ide_find_timeout_seconds() -> float:
    raw = os.environ.get("VDISPLAY_IDE_FIND_TIMEOUT_S", "20")
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 20.0


def _should_skip_window_wait(app_id: str, *, backend: str, map_path: str | None) -> str | None:
    """Skip AT-SPI/xdotool window polling for native Wayland vision-only IDEs."""
    if map_path or not _is_wayland_session():
        return None
    app = get_desktop_app(app_id)
    if backend not in {"auto", "vision"} and app.preferred_backend != "vision":
        return None
    if app.preferred_backend != "vision":
        return None
    return (
        f"{app.label} on native Wayland is not visible to AT-SPI/xdotool; "
        "skipped window focus wait (use --map, koru plugin, or --variant xwayland)"
    )


def open_desktop_app(
    app_id: str,
    *,
    variant: str | None = None,
    wait_seconds: float = 0.0,
) -> dict[str, Any]:
    app = get_desktop_app(app_id)
    launch = app.variant(variant)
    env = launch_env_for(launch)
    try:
        process = subprocess.Popen(
            list(launch.argv),
            env=env,
            cwd=launch.cwd,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise VDisplayError(f"failed to launch {app.app_id}: {exc}") from exc
    if wait_seconds > 0:
        time.sleep(wait_seconds)
    return {
        "ok": True,
        "app_id": app.app_id,
        "variant": launch.variant_id,
        "argv": list(launch.argv),
        "pid": process.pid,
        "wait_seconds": wait_seconds,
    }


def wait_for_app_window(
    app_id: str,
    *,
    display: str | None = None,
    timeout_seconds: float = 20.0,
    poll_interval: float = 0.5,
    backend: str | None = None,
    map_path: str | None = None,
) -> dict[str, Any]:
    app = get_desktop_app(app_id)
    effective_backend = backend or app.preferred_backend or "auto"
    skip_reason = _should_skip_window_wait(app_id, backend=effective_backend, map_path=map_path)
    if skip_reason:
        return {
            "ok": True,
            "app_id": app_id,
            "focused": None,
            "skipped": True,
            "note": skip_reason,
        }

    from .application.services import control as control_svc

    hints = ide_hints_for(app_id)
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            control_svc.control_focus(
                display=display,
                backend=effective_backend if effective_backend != "auto" else "auto",
                app=hints["app"],
                window_title=hints["window_title_contains"],
                role="window",
            )
            return {
                "ok": True,
                "app_id": app_id,
                "focused": True,
                "app": hints["app"],
            }
        except Exception as exc:
            last_error = str(exc)
        time.sleep(poll_interval)
    return {
        "ok": False,
        "app_id": app_id,
        "focused": False,
        "error": last_error or "timeout waiting for window",
        "timeout_seconds": timeout_seconds,
    }


def _find_map_target(
    map_path: str,
    targets: tuple[str, ...],
) -> tuple[str | None, dict[str, Any] | None]:
    from .control.gui_map import load_gui_map, map_element_to_node

    try:
        pack = load_gui_map(map_path)
    except Exception as exc:
        return None, {"ok": False, "error": str(exc), "map_path": map_path}
    available = set(pack.elements.keys())
    for target in targets:
        if target in available:
            node = map_element_to_node(pack.elements[target])
            return target, {
                "ok": True,
                "count": 1,
                "map": map_path,
                "map_target": target,
                "selected": node.to_dict(),
            }
    return None, {
        "ok": False,
        "map_path": map_path,
        "map_targets_tried": list(targets),
        "available_targets": sorted(available)[:30],
    }


def _find_first_selector(
    *,
    app_id: str,
    selectors: tuple[dict[str, str], ...],
    display: str | None,
    backend: str,
    map_path: str | None = None,
    map_scope: str | None = None,
    map_target: str | None = None,
    map_targets: tuple[str, ...] | None = None,
) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    from .application.services import control as control_svc

    hints = ide_hints_for(app_id)
    base = {
        "display": display,
        "backend": backend,
        "app": hints["app"],
        "window_title": hints["window_title_contains"],
    }
    if map_path:
        target, found = _find_map_target(map_path, map_targets or ((map_target,) if map_target else ()))
        if target is not None:
            payload = {
                **base,
                "map_path": map_path,
                "map_scope": map_scope,
                "map_target": target,
            }
            return payload, found
        return None, found

    last_error: dict[str, Any] | None = None
    find_timeout = _ide_find_timeout_seconds()
    for spec in selectors:
        payload = {**base, **spec}
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(control_svc.controls_find, **payload)
                found = future.result(timeout=find_timeout)
        except FuturesTimeoutError:
            last_error = {
                "ok": False,
                "error": f"controls_find timed out after {find_timeout:.0f}s",
                "selector": spec,
            }
            continue
        except Exception as exc:
            last_error = {"ok": False, "error": str(exc), "selector": spec}
            continue
        if found.get("ok") and int(found.get("count") or 0) > 0:
            return spec, found
        last_error = found
    return None, last_error


def _submit_via_keyboard(*, app_id: str) -> dict[str, Any]:
    key = "ctrl+Return" if app_id in {"pycharm", "jetbrains"} else "Return"
    injector_error = ""
    try:
        from gillm.injection.injector import Injector

        Injector().press_key(key)
        return {"ok": True, "method": "injector-key", "key": key}
    except Exception as exc:
        injector_error = str(exc)
    try:
        from vdisplay.input.linux_ydotool import LinuxYdotoolInput

        yinput = LinuxYdotoolInput()
        if key == "ctrl+Return":
            yinput.hotkey("29:1", "28:1", "28:0", "29:0")
        else:
            yinput.hotkey("28:1", "28:0")
        return {"ok": True, "method": "ydotool-key", "key": key}
    except Exception as exc:
        return {
            "ok": False,
            "method": "ydotool-key",
            "key": key,
            "error": f"{injector_error}; ydotool: {exc}",
        }


def _handle_wait_window(
    app: Any,
    resolved_map: str | None,
    display: str | None,
    wait_timeout: float,
    result: dict[str, Any],
    *,
    open_app: bool = False,
) -> str | None:
    focus_error: str | None = None
    effective_timeout = wait_timeout if (not resolved_map or open_app) else min(wait_timeout, 3.0)
    wait_result = wait_for_app_window(
        app.app_id,
        display=display,
        timeout_seconds=effective_timeout,
        backend=app.preferred_backend,
        map_path=resolved_map,
    )
    result["wait_window"] = wait_result
    if wait_result.get("skipped"):
        return None
    if not resolved_map:
        if not wait_result.get("ok"):
            focus_error = str(wait_result.get("error") or "window not ready")
            result["next"] = _wayland_ide_next_steps(app)
        return focus_error
    if not wait_result.get("ok"):
        focus_error = str(wait_result.get("error") or "window not ready")
        result["wait_window"]["note"] = "continuing with GUI map (AT-SPI window focus not required)"
    return focus_error


def _wayland_ide_next_steps(app: Any) -> list[str]:
    steps = [
        f"Try XWayland: vdisplay app open {app.app_id} --variant xwayland",
        f"Build GUI map: vdisplay map build -o maps/{app.app_id}-chat.json",
        "For vision backend: vdisplay-agent serve && vdisplay agent screencast start",
        "Prefer koru plugin for native Wayland Electron chat",
    ]
    return steps


def _handle_focus_window(
    app: Any,
    display: str | None,
) -> str | None:
    from .application.services import control as control_svc

    try:
        hints = ide_hints_for(app.app_id)
        control_svc.control_focus(
            display=display,
            backend="auto",
            app=hints["app"],
            window_title=hints["window_title_contains"],
            role="window",
        )
        return None
    except Exception as exc:
        return str(exc)


def _handle_submit(
    app: Any,
    display: str | None,
    effective_backend: str,
    resolved_map: str | None,
    map_scope: str | None,
) -> tuple[bool, dict[str, Any] | None]:
    from .application.services import control as control_svc

    submit_map_targets = map_submit_target_candidates(app.app_id, app.map_targets.get("send"))
    submit_selector, submit_found = _find_first_selector(
        app_id=app.app_id,
        selectors=submit_selectors_for(app.app_id),
        display=display,
        backend=effective_backend,
        map_path=resolved_map,
        map_scope=map_scope,
        map_target=submit_map_targets[0] if submit_map_targets else None,
        map_targets=submit_map_targets if resolved_map else None,
    )

    submit_result: dict[str, Any] | None = None
    submitted = False

    if submit_selector is not None:
        click_kwargs: dict[str, Any] = {
            "display": display,
            "backend": effective_backend,
        }
        if resolved_map and submit_selector.get("map_path"):
            click_kwargs.update(
                {
                    "map_path": submit_selector["map_path"],
                    "map_scope": submit_selector.get("map_scope"),
                    "map_target": submit_selector.get("map_target"),
                }
            )
        else:
            click_kwargs.update(
                {
                    "app": app.app_hint,
                    "window_title": app.window_title_contains,
                    **submit_selector,
                }
            )
        selected_submit = (submit_found or {}).get("selected")
        if isinstance(selected_submit, dict) and selected_submit.get("id"):
            click_kwargs["provider_ref"] = selected_submit["id"]
        try:
            submit_result = control_svc.control_click(**click_kwargs)
            submitted = bool(submit_result.get("ok", True))
        except Exception as exc:
            submit_result = {"ok": False, "error": str(exc)}

    if not submitted:
        submit_result = _submit_via_keyboard(app_id=app.app_id)
        submitted = bool(submit_result.get("ok"))

    return submitted, submit_result


def _build_map_missing_result(
    app: Any,
    text: str,
    effective_backend: str,
    map_path: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "app_id": app.app_id,
        "backend": effective_backend,
        "chars": len(text),
        "submit": False,
        "map_path": None,
        "map_path_requested": map_path,
        "message": f"map file not found or invalid: {map_path}",
        "hint": "Build the map first: vdisplay map build --monitor DP-1 --crop-bounds X,Y,W,H -o maps/cursor-chat.json",
        "next": [
            "Install OCR deps: pip install pytesseract Pillow && sudo apt install tesseract-ocr",
            "Ensure screencast is active: vdisplay agent screencast status",
            f"See template: {map_manifest_path(app.app_id) or 'maps/templates/cursor-chat.manifest.json'}",
        ],
    }


def _build_no_selector_result(
    app: Any,
    focus_error: str | None,
    resolved_map: str | None,
    map_manifest: str | None,
    open_app: bool,
    found: dict[str, Any] | None,
    target_candidates: tuple[str, ...],
) -> dict[str, Any]:
    next_steps: list[str] = []
    if not resolved_map and map_manifest:
        next_steps.append(
            f"Build GUI map: vdisplay map build -o maps/{app.app_id}-chat.json (template: {map_manifest})"
        )
    if _is_wayland_session() and app.preferred_backend == "vision" and not resolved_map:
        next_steps.extend(_wayland_ide_next_steps(app))
    if not open_app:
        next_steps.append(f"Launch IDE first: vdisplay app open {app.app_id}")
    if resolved_map:
        next_steps.append(
            f"Retarget map element: vdisplay map show {resolved_map} | jq '.elements | keys'"
        )
    return {
        "ok": False,
        "message": (
            f"no chat input matched for app={app.app_id} (app={app.app_hint!r}); "
            f"focus_error={focus_error or '-'}"
        ),
        "focus_error": focus_error,
        "diagnostics": found,
        "map_targets_tried": list(target_candidates),
        "hint": app.notes or "build a GUI map or use koru plugin for Electron chat",
        "next": next_steps,
    }


def _build_write_kwargs(
    selector: dict[str, str],
    found: dict[str, Any] | None,
    *,
    display: str | None,
    backend: str,
    value: str,
    verify: bool,
    resolved_map: str | None,
    app: Any,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "display": display,
        "backend": backend,
        "value": value,
        "verify": verify,
    }
    if resolved_map and selector.get("map_path"):
        kwargs.update(
            {
                "map_path": selector["map_path"],
                "map_scope": selector.get("map_scope"),
                "map_target": selector.get("map_target"),
            }
        )
    else:
        selector_payload = {key: value for key, value in selector.items() if key != "backend"}
        kwargs.update(
            {
                "app": app.app_hint,
                "window_title": app.window_title_contains,
                **selector_payload,
            }
        )
    selected = (found or {}).get("selected") if isinstance(found, dict) else None
    if isinstance(selected, dict) and selected.get("id"):
        kwargs["provider_ref"] = selected["id"]
    return kwargs


def _build_set_value_failure_result(
    result: dict[str, Any],
    message: str,
    selector: dict[str, str],
    focus_error: str | None,
) -> dict[str, Any]:
    result.update({"message": message, "selector": selector, "focus_error": focus_error})
    return result


def _try_control_set_value(
    write_kwargs: dict[str, Any],
    result: dict[str, Any],
    selector: dict[str, str],
    focus_error: str | None,
) -> dict[str, Any] | None:
    from .application.services import control as control_svc

    try:
        typed = control_svc.control_set_value(**write_kwargs)
    except Exception as exc:
        return _build_set_value_failure_result(result, str(exc), selector, focus_error)
    if not typed.get("ok", True):
        return _build_set_value_failure_result(
            result,
            str(typed.get("error") or typed.get("message") or "set_value failed"),
            selector,
            focus_error,
        )
    return typed


def _build_ide_success_result(
    result: dict[str, Any],
    selector: dict[str, str],
    focus_error: str | None,
    typed: dict[str, Any],
    submit: bool,
    app: Any,
    display: str | None,
    effective_backend: str,
    resolved_map: str | None,
    map_scope: str | None,
) -> dict[str, Any]:
    submitted = False
    submit_result: dict[str, Any] | None = None
    if submit:
        submitted, submit_result = _handle_submit(
            app, display, effective_backend, resolved_map, map_scope
        )
    result.update(
        {
            "ok": True,
            "message": "typed via vdisplay ide prompt",
            "selector": selector,
            "focus_error": focus_error,
            "typed": typed,
            "submitted": submitted,
            "submit_result": submit_result,
            "map_path": resolved_map,
        }
    )
    return result


def send_ide_prompt(
    *,
    app_id: str,
    text: str,
    display: str | None = None,
    backend: str | None = None,
    open_app: bool = False,
    launch_variant: str | None = None,
    wait_window: bool = True,
    wait_timeout: float = 20.0,
    submit: bool = False,
    map_path: str | None = None,
    map_scope: str | None = None,
    map_target: str | None = None,
    verify: bool = False,
) -> dict[str, Any]:
    app = get_desktop_app(app_id)
    effective_backend = backend or app.preferred_backend or "auto"
    resolved_map = resolve_map_path(app_id, map_path)
    if map_path and resolved_map is None:
        return _build_map_missing_result(app, text, effective_backend, map_path)

    map_manifest = map_manifest_path(app_id)
    target_candidates = map_input_target_candidates(app_id, map_target)
    result: dict[str, Any] = {
        "ok": False,
        "app_id": app.app_id,
        "backend": effective_backend,
        "chars": len(text),
        "submit": submit,
        "map_path": resolved_map,
        "map_manifest": map_manifest,
    }

    if open_app:
        result["launch"] = open_desktop_app(app.app_id, variant=launch_variant, wait_seconds=1.0)

    if wait_window:
        focus_error = _handle_wait_window(
            app, resolved_map, display, wait_timeout, result, open_app=open_app
        )
    else:
        focus_error = _handle_focus_window(app, display)

    selector, found = _find_first_selector(
        app_id=app.app_id,
        selectors=prompt_chat_selectors_for(app.app_id, backend=effective_backend, map_path=resolved_map),
        display=display,
        backend=effective_backend,
        map_path=resolved_map,
        map_scope=map_scope,
        map_target=target_candidates[0] if target_candidates else None,
        map_targets=target_candidates if resolved_map else None,
    )

    if selector is None:
        result.update(
            _build_no_selector_result(
                app, focus_error, resolved_map, map_manifest, open_app, found, target_candidates
            )
        )
        return result

    write_kwargs = _build_write_kwargs(
        selector,
        found,
        display=display,
        backend=effective_backend,
        value=text,
        verify=verify,
        resolved_map=resolved_map,
        app=app,
    )

    typed = _try_control_set_value(write_kwargs, result, selector, focus_error)
    if isinstance(typed, dict) and not typed.get("ok", True):
        return typed
    if typed is None:
        return result

    return _build_ide_success_result(
        result, selector, focus_error, typed, submit, app, display, effective_backend, resolved_map, map_scope
    )


__all__ = [
    "open_desktop_app",
    "send_ide_prompt",
    "wait_for_app_window",
]
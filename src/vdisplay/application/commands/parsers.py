"""Parsers for converting various formats into CommandRequest."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .models import CommandRequest
from .verbs import CommandVerb


def _resolve_browser_engine_from_dsl(cmd: dict[str, Any]) -> str | None:
    if engine := cmd.get("engine") or cmd.get("vendor"):
        return str(engine)
    if profile := cmd.get("profile"):
        profile_id = str(profile).strip().lower()
        if profile_id.startswith("browser_"):
            return profile_id.removeprefix("browser_")
    return None


def _control_session_id_from_dsl(cmd: dict[str, Any], verb: CommandVerb) -> str | None:
    if verb in {CommandVerb.TERMINAL_OPEN, CommandVerb.BROWSER_OPEN}:
        return None
    return cmd.get("session_id")


def _control_fields_from_dsl(cmd: dict[str, Any]) -> dict[str, Any]:
    return {
        "control_selector": cmd.get("selector"),
        "control_provider_ref": cmd.get("provider_ref") or cmd.get("id"),
        "control_name": cmd.get("name"),
        "control_role": cmd.get("role"),
        "control_app": cmd.get("app"),
        "control_window_id": cmd.get("window_id"),
        "control_window_title": cmd.get("window_title"),
        "control_value": cmd.get("value"),
        "control_verify": bool(cmd.get("verify", False)),
        "control_screenshot_verify": bool(cmd.get("screenshot_verify", False)),
        "control_verify_label": cmd.get("verify_label"),
        "control_verify_selector": cmd.get("verify_selector"),
        "control_backend": str(cmd.get("control_backend") or cmd.get("backend") or "auto"),
        "control_index": int(cmd.get("index") or 0),
        "control_max_depth": int(cmd.get("max_depth") or 8),
        "control_format": str(cmd.get("format") or "flat"),
        "control_environment": cmd.get("environment"),
        "control_text": cmd.get("text"),
        "control_text_contains": cmd.get("text_contains"),
        "control_terminal_line": int(cmd["terminal_line"]) if cmd.get("terminal_line") is not None else None,
        "control_terminal_col": int(cmd["terminal_col"]) if cmd.get("terminal_col") is not None else None,
    }


def _terminal_fields_from_dsl(cmd: dict[str, Any], verb: CommandVerb) -> dict[str, Any]:
    if verb != CommandVerb.TERMINAL_OPEN:
        return {
            "terminal_session_id": None,
            "terminal_command": None,
            "terminal_title": None,
        }
    return {
        "terminal_session_id": cmd.get("session_id"),
        "terminal_command": cmd.get("command"),
        "terminal_title": cmd.get("title"),
    }


def _browser_fields_from_dsl(cmd: dict[str, Any], verb: CommandVerb) -> dict[str, Any]:
    if verb != CommandVerb.BROWSER_OPEN:
        return {
            "browser_session_id": None,
            "browser_url": None,
            "browser_headless": True,
            "browser_title": None,
            "browser_engine": None,
        }
    return {
        "browser_session_id": cmd.get("session_id"),
        "browser_url": cmd.get("url"),
        "browser_headless": bool(cmd.get("headless", True)),
        "browser_title": cmd.get("title"),
        "browser_engine": _resolve_browser_engine_from_dsl(cmd),
    }


def parse_dsl(cmd: dict[str, Any], *, line: str = "") -> CommandRequest:
    verb_raw = str(cmd.get("verb", "HEALTH")).upper()
    try:
        verb = CommandVerb(verb_raw)
    except ValueError:
        verb = CommandVerb.HEALTH
    apps_only = bool(cmd.get("apps_only", False))
    terminal_fields = _terminal_fields_from_dsl(cmd, verb)
    browser_fields = _browser_fields_from_dsl(cmd, verb)
    return CommandRequest(
        verb=verb,
        line=line,
        request_source=str(cmd.get("request_source") or "dsl"),
        display=cmd.get("display"),
        apps_only=apps_only,
        include_all=not apps_only,
        match_class=cmd.get("class"),
        match_pid=cmd.get("pid"),
        match_app=cmd.get("app"),
        match_title=cmd.get("title"),
        window_id=cmd.get("window_id"),
        output=cmd.get("out"),
        width=int(cmd.get("width", 1920)),
        height=int(cmd.get("height", 1080)),
        source=cmd.get("source"),
        target=cmd.get("target"),
        vd_display=str(cmd.get("display", ":99")),
        backend=str(cmd.get("backend", "xvfb")),
        control_session_id=_control_session_id_from_dsl(cmd, verb),
        session_id=cmd.get("audit_session_id"),
        request_id=cmd.get("request_id"),
        terminal_rows=int(cmd.get("rows") or 24),
        terminal_cols=int(cmd.get("cols") or 80),
        extra={k: v for k, v in cmd.items() if k not in {"verb"}},
        **_control_fields_from_dsl(cmd),
        **terminal_fields,
        **browser_fields,
    )


def parse_agent_control_body(
    verb: CommandVerb,
    body: dict[str, Any],
    *,
    audit: Any,
) -> CommandRequest:
    reserved = {
        "display",
        "backend",
        "verify",
        "screenshot_verify",
        "verify_label",
        "verify_selector",
        "value",
        "max_depth",
        "format",
        "preview",
        "preview_output",
        "preview_debug",
        "provider_ref",
        "selector",
        "name",
        "role",
        "app",
        "window_id",
        "window_title",
        "index",
        "environment",
        "text",
        "text_contains",
        "terminal_line",
        "terminal_col",
        "session_id",
        "dom_css",
        "dom_xpath",
        "vision_anchor",
        "vision_template",
        "vision_anchor_rel",
        "vision_target",
        "vision_min_confidence",
        "map_path",
        "map_scope",
        "map_target",
    }
    extra = {key: value for key, value in body.items() if key not in reserved and value is not None}
    passthrough = {
        key: body[key]
        for key in (
            "dom_css",
            "dom_xpath",
            "vision_anchor",
            "vision_template",
            "vision_anchor_rel",
            "vision_target",
            "vision_min_confidence",
            "map_path",
            "map_scope",
            "map_target",
            "preview",
            "preview_output",
            "preview_debug",
        )
        if body.get(key) is not None
    }
    return CommandRequest(
        verb=verb,
        request_source=audit.request_source or "agent",
        session_id=audit.session_id,
        request_id=audit.request_id,
        display=body.get("display"),
        control_selector=body.get("selector"),
        control_provider_ref=body.get("provider_ref"),
        control_name=body.get("name"),
        control_role=body.get("role"),
        control_app=body.get("app"),
        control_window_id=body.get("window_id"),
        control_window_title=body.get("window_title"),
        control_index=int(body.get("index") or 0),
        control_environment=body.get("environment"),
        control_text=body.get("text"),
        control_text_contains=body.get("text_contains"),
        control_terminal_line=body.get("terminal_line"),
        control_terminal_col=body.get("terminal_col"),
        control_session_id=body.get("session_id"),
        control_backend=str(body.get("backend") or "auto"),
        control_verify=bool(body.get("verify", False)),
        control_screenshot_verify=bool(body.get("screenshot_verify", False)),
        control_verify_label=body.get("verify_label"),
        control_verify_selector=body.get("verify_selector"),
        control_value=body.get("value"),
        control_max_depth=int(body.get("max_depth") or 8),
        control_format=str(body.get("format") or "flat"),
        extra={**extra, **passthrough},
    )


def _parse_terminal_open_from_agent(request: CommandRequest, body: dict[str, Any]) -> CommandRequest:
    return replace(request, **_terminal_fields_from_dsl(body, CommandVerb.TERMINAL_OPEN))


def _parse_browser_open_from_agent(request: CommandRequest, body: dict[str, Any]) -> CommandRequest:
    mapped = dict(body)
    if mapped.get("app") and not mapped.get("url"):
        mapped["url"] = mapped["app"]
    return replace(request, **_browser_fields_from_dsl(mapped, CommandVerb.BROWSER_OPEN))


def _parse_virtual_start_from_agent(request: CommandRequest, body: dict[str, Any]) -> CommandRequest:
    return replace(
        request,
        vd_display=str(body.get("display") or ":99"),
        backend=str(body.get("backend") or "xvfb"),
    )


def _parse_adopt_release_from_agent(request: CommandRequest, body: dict[str, Any]) -> CommandRequest:
    pid = body.get("match_pid", body.get("pid"))
    return replace(
        request,
        match_title=body.get("match_title") or body.get("title"),
        match_class=body.get("match_class") or body.get("wm_class") or body.get("class"),
        match_pid=int(pid) if pid is not None else None,
        match_app=body.get("match_app") or body.get("app"),
        target=body.get("target") or request.target,
    )


_AGENT_VERB_PARSERS = {
    CommandVerb.TERMINAL_OPEN: _parse_terminal_open_from_agent,
    CommandVerb.BROWSER_OPEN: _parse_browser_open_from_agent,
    CommandVerb.VIRTUAL_START: _parse_virtual_start_from_agent,
    CommandVerb.ADOPT: _parse_adopt_release_from_agent,
    CommandVerb.RELEASE: _parse_adopt_release_from_agent,
}


def parse_agent_body(
    verb: CommandVerb,
    body: dict[str, Any],
    *,
    audit: Any,
) -> CommandRequest:
    control_verbs = {
        CommandVerb.CONTROLS_LIST,
        CommandVerb.CONTROLS_FIND,
        CommandVerb.CONTROL_CLICK,
        CommandVerb.CONTROL_FOCUS,
        CommandVerb.CONTROL_SET_VALUE,
        CommandVerb.DIAGNOSE_CONTROL,
    }
    if verb in control_verbs:
        return parse_agent_control_body(verb, body, audit=audit)

    passthrough = {
        key: body[key]
        for key in (
            "region",
            "prefer_mirror",
            "all_monitors",
            "out_dir",
            "lines",
            "engine",
            "vendor",
            "profile",
            "headless",
            "interactive",
            "timeout_s",
            "multiple",
        )
        if body.get(key) is not None
    }
    request = CommandRequest(
        verb=verb,
        request_source=getattr(audit, "request_source", None) or "agent",
        session_id=getattr(audit, "session_id", None),
        request_id=getattr(audit, "request_id", None),
        display=body.get("display"),
        output=body.get("output") or body.get("path"),
        source=body.get("source"),
        target=body.get("target"),
        monitor=int(body["monitor"]) if body.get("monitor") is not None else None,
        width=int(body.get("width") or 1920),
        height=int(body.get("height") or 720),
        window_id=body.get("window_id"),
        all_monitors=bool(body.get("all_monitors", False)),
        out_dir=body.get("out_dir"),
        terminal_rows=int(body.get("rows") or 24),
        terminal_cols=int(body.get("cols") or 80),
        extra={**passthrough, "agent_body": dict(body)},
    )

    if verb in _AGENT_VERB_PARSERS:
        return _AGENT_VERB_PARSERS[verb](request, body)

    return request
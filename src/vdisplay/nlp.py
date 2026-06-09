from __future__ import annotations

import re
from collections.abc import Callable


def parse_display(text: str) -> str | None:
    lowered = text.lower()
    if "display zero" in lowered or "display 0" in lowered or "on :0" in lowered:
        return ":0"
    if "display one" in lowered or "display 1" in lowered or "on :1" in lowered:
        return ":1"
    match = re.search(r"display\s+(:?\d+)", lowered)
    if match:
        value = match.group(1)
        return value if value.startswith(":") else f":{value}"
    match = re.search(r"(\:\d+)", text)
    if match:
        return match.group(1)
    return None


def _display_suffix(display: str | None) -> str:
    return f" DISPLAY {display}" if display else ""


def _default_display_suffix(display: str | None) -> str:
    return _display_suffix(display) or " DISPLAY :0"


def _default_all(_text: str, display: str | None) -> str:
    return f"ALL{_default_display_suffix(display)}"


def _default_monitors(_text: str, display: str | None) -> str:
    return f"MONITORS{_default_display_suffix(display)}"


def _default_windows(_text: str, display: str | None) -> str:
    return f"WINDOWS{_default_display_suffix(display)}"


def _screenshot_dsl(prompt: str, _display: str | None) -> str:
    out_match = re.search(r"(\S+\.png)", prompt)
    out = out_match.group(1) if out_match else "screen.png"
    return f"SCREENSHOT OUT {out} DISPLAY :99"


def _mirror_dsl(_prompt: str, _display: str | None) -> str:
    return "MIRROR SOURCE primary"


def _release_dsl(text: str, _display: str | None) -> str:
    if "firefox" in text:
        return "RELEASE TITLE Firefox"
    if "jetbrains" in text or "toolbox" in text:
        return "RELEASE APP JetBrains"
    return "RELEASE TITLE Firefox"


def _adopt_dsl(text: str, _display: str | None) -> str:
    if "jetbrains" in text or "toolbox" in text:
        return "ADOPT APP JetBrains"
    return "ADOPT TITLE Firefox"


def _validate_dsl(_text: str, display: str | None) -> str:
    return f"VALIDATE{_display_suffix(display)}".strip()


_NL_RULES: list[tuple[Callable[[str], bool], Callable[[str, str | None], str]]] = [
    (
        lambda t: any(w in t for w in ("everything", "all monitors", "full state", "całość", "wszystko")),
        _default_all,
    ),
    (
        lambda t: "window" in t or "okno" in t or "aplikac" in t,
        _default_windows,
    ),
    (
        lambda t: "output" in t or "monitor" in t or "ekran" in t,
        _default_monitors,
    ),
    (
        lambda t: "screenshot" in t or "zrzut" in t,
        _screenshot_dsl,
    ),
    (
        lambda t: "mirror" in t or "lustrz" in t,
        _mirror_dsl,
    ),
    (
        lambda t: "release" in t or "przywróć" in t or "restore" in t,
        _release_dsl,
    ),
    (
        lambda t: "adopt" in t or "hide" in t or "ukryj" in t or "firefox" in t,
        _adopt_dsl,
    ),
    (
        lambda t: "validate" in t or "sprawdź" in t,
        _validate_dsl,
    ),
    (
        lambda t: "info" in t or "capabilities" in t,
        lambda _t, _d: "INFO",
    ),
]


def nl_to_dsl(prompt: str) -> str:
    text = prompt.strip().lower()
    if not text:
        return "ALL"
    display = parse_display(prompt)
    for matches, build in _NL_RULES:
        if matches(text):
            return build(text, display)
    return _default_all(display)


def run_nl_prompt(prompt: str, *, dsl_only: bool = False) -> tuple[str, str | None, int]:
    """Return (dsl_line, json_output_or_dsl, exit_code)."""
    line = nl_to_dsl(prompt)
    if dsl_only:
        return line, line, 0

    try:
        from dsl2vdisplay import dispatch
    except ImportError:
        payload, code = _run_local_dsl(line)
        import json

        return line, json.dumps(payload, indent=2), code

    result = dispatch(line)
    output = result.output or __import__("json").dumps(result.to_dict(), indent=2)
    return line, output, 0 if result.ok else 1


def _run_local_dsl(line: str) -> tuple[dict | list, int]:
    from .application.services import discovery

    tokens = line.split()
    verb = tokens[0].upper() if tokens else "ALL"
    display = None
    if "DISPLAY" in tokens:
        idx = tokens.index("DISPLAY")
        if idx + 1 < len(tokens):
            display = tokens[idx + 1]

    if verb in {"MONITORS", "OUTPUTS"}:
        return discovery.list_monitors(display), 0
    if verb == "WINDOWS":
        return discovery.list_windows_payload(display, include_all=True), 0
    if verb == "ALL":
        return discovery.list_all(display, include_all=True), 0
    return {"error": f"dsl2vdisplay not installed; unsupported local verb: {verb}", "dsl": line}, 1

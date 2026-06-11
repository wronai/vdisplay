"""Single registry of ``VDISPLAY_*`` defaults (documented in ``.env.example``)."""

from __future__ import annotations

import os

ENV_DEFAULTS: dict[str, str] = {
    # Agent
    "VDISPLAY_AGENT_URL": "",
    "VDISPLAY_AGENT_HOST": "127.0.0.1",
    "VDISPLAY_AGENT_PORT": "8765",
    "VDISPLAY_AGENT_AUTO": "1",
    "VDISPLAY_AGENT_AUDIT_DELEGATE": "1",
    # Observe / IMGL / VQL
    "VDISPLAY_OBSERVE": "1",
    "VDISPLAY_OBSERVE_CACHE": "1",
    "VDISPLAY_VQL": "1",
    "VDISPLAY_IMGL": "1",
    "VDISPLAY_IMGL_LANG": "eng+pol",
    "VDISPLAY_IMGL_SKIP_BLANK": "0",
    "VDISPLAY_SESSION_BASE": ".vdisplay",
    # Control / vision
    "VDISPLAY_CONTROL_RETRY": "auto",
    "VDISPLAY_CONTROL_MAX_ATTEMPTS": "3",
    "VDISPLAY_CONTROL_RETRY_DELAY_MS": "150",
    "VDISPLAY_CONTROL_RETRY_STRATEGIES": "retry_scope,fallback_backend,refresh_map",
    "VDISPLAY_CONTROL_FOCUS_MS": "350",
    "VDISPLAY_CONTROL_POINTER_SETTLE_MS": "50",
    "VDISPLAY_CONTROL_SETTLE_MS": "150",
    "VDISPLAY_VISION_BACKEND": "auto",
    "VDISPLAY_OCR_CACHE": "1",
    "VDISPLAY_ATSPI_TIMEOUT_S": "30",
    "VDISPLAY_IDE_FIND_TIMEOUT_S": "20",
    "VDISPLAY_BROWSER_DETACHED": "1",
    "VDISPLAY_VISION_PREVIEW": "auto",
    "VDISPLAY_DESCRIBE_BACKEND": "auto",
    "VDISPLAY_IMG2NL": "1",
    "VDISPLAY_IMG2NL_LOCALE": "pl",
    "VDISPLAY_VISION_LLM_MODE": "off",
    "VDISPLAY_VISION_LLM_MODALITIES": "image,text",
    "VDISPLAY_VISION_LLM_TIMEOUT_S": "30",
    # Screencast / capture
    "VDISPLAY_PIPEWIRE_CAPTURE_TIMEOUT_S": "8",
    "VDISPLAY_PIPEWIRE_FORCE_CAPS": "0",
    "VDISPLAY_SCREENCAST_GNOME_FALLBACK": "1",
    "VDISPLAY_PIPEWIRE_FRESH_FD": "0",
    "VDISPLAY_SCREENCAST_CURSOR": "2",
    "VDISPLAY_SCREENCAST_LOCAL_START_COOLDOWN_S": "60",
    "VDISPLAY_SCREENCAST_RECOVERY_COOLDOWN_S": "300",
    "VDISPLAY_KEEPER_CAPTURE_TIMEOUT_S": "",
    "VDISPLAY_WEB_FRAME_CACHE_TTL_S": "5.0",
    # Replay / events
    "VDISPLAY_REPLAY_DELAY_S": "0.25",
    "VDISPLAY_EVENT_FORMAT": "json",
    "VDISPLAY_PROJECTIONS": "1",
}


def env_value(name: str, default: str | None = None) -> str:
    if name in os.environ:
        return os.environ[name]
    if default is not None:
        return default
    return ENV_DEFAULTS.get(name, "")


def env_flag(name: str, *, default: bool | None = None) -> bool:
    if name in os.environ:
        raw = os.environ[name].strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return True
        if raw in {"0", "false", "no", "off"}:
            return False
    if default is not None:
        return default
    raw = ENV_DEFAULTS.get(name, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def env_int_value(name: str, default: int | None = None) -> int:
    raw = env_value(name, None if default is None else str(default)).strip()
    if not raw:
        return default if default is not None else 0
    try:
        return int(raw)
    except ValueError:
        return default if default is not None else 0


def env_float_value(name: str, default: float | None = None) -> float:
    raw = env_value(name, None if default is None else str(default)).strip()
    if not raw:
        return default if default is not None else 0.0
    try:
        return float(raw)
    except ValueError:
        return default if default is not None else 0.0


def env_str_lower(name: str, default: str = "") -> str:
    raw = env_value(name, default).strip().lower()
    return raw or default


def env_optional(name: str) -> str:
    return os.environ.get(name, "").strip()


def vision_backend_name() -> str:
    return env_str_lower("VDISPLAY_VISION_BACKEND", "auto") or "auto"

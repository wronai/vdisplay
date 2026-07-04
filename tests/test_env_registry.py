"""Keep VDISPLAY_* env registry in sync across code, defaults, and .env.example."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vdisplay.application.config_options import (
    VDISPLAY_ACTION_MAP_TEMPLATES,
    VDISPLAY_AUTO_SOURCES,
    VDISPLAY_BROWSER_VENDORS,
    VDISPLAY_CONTROL_ACTUATION_MARKERS,
    VDISPLAY_CONTROL_BACKENDS,
    VDISPLAY_CONTROL_ENVIRONMENTS,
    VDISPLAY_CONTROL_LIST_FORMATS,
    VDISPLAY_CONTROL_RETRY_STRATEGIES,
    VDISPLAY_DIAGNOSE_MODES,
    VDISPLAY_IDE_APPS,
    VDISPLAY_METADATA_SUBDIRS,
    VDISPLAY_OBSERVE_OUTPUT_FORMATS,
    VDISPLAY_OBSERVE_SIDECAR_SUFFIXES,
    VDISPLAY_PLANFILE_TASK_KEYS,
    VDISPLAY_RUNNABLE_TASK_STATUSES,
    VDISPLAY_SAMPLER_CAPTURE_MODES,
    VDISPLAY_SAMPLER_FRAME_FORMATS,
    VDISPLAY_SCREENSHOT_SOURCES,
    VDISPLAY_SESSION_EXPORT_FORMATS,
    VDISPLAY_TASK_PRIORITIES,
    VDISPLAY_VISION_ANCHOR_RELATIONS,
    VDISPLAY_VISION_INJECTION_COMMANDS,
    VDISPLAY_VQL_KIND_PRIORITY,
    VDISPLAY_VQL_LAYER_EXPORT_LIMIT,
    VDISPLAY_VQL_MAP_TARGET_LIMIT,
    VDISPLAY_VQL_OCR_TEXT_MAX_LEN,
    VDISPLAY_VQL_TARGET_LIMIT,
)
from vdisplay.application.env_defaults import ENV_DEFAULTS

ROOT = Path(__file__).resolve().parents[1]

CONFIG_OPTION_KEYS = {
    VDISPLAY_ACTION_MAP_TEMPLATES,
    VDISPLAY_AUTO_SOURCES,
    VDISPLAY_BROWSER_VENDORS,
    VDISPLAY_CONTROL_ACTUATION_MARKERS,
    VDISPLAY_CONTROL_BACKENDS,
    VDISPLAY_CONTROL_ENVIRONMENTS,
    VDISPLAY_CONTROL_LIST_FORMATS,
    VDISPLAY_CONTROL_RETRY_STRATEGIES,
    VDISPLAY_DIAGNOSE_MODES,
    VDISPLAY_IDE_APPS,
    VDISPLAY_METADATA_SUBDIRS,
    VDISPLAY_OBSERVE_OUTPUT_FORMATS,
    VDISPLAY_OBSERVE_SIDECAR_SUFFIXES,
    VDISPLAY_PLANFILE_TASK_KEYS,
    VDISPLAY_RUNNABLE_TASK_STATUSES,
    VDISPLAY_SAMPLER_CAPTURE_MODES,
    VDISPLAY_SAMPLER_FRAME_FORMATS,
    VDISPLAY_SCREENSHOT_SOURCES,
    VDISPLAY_SESSION_EXPORT_FORMATS,
    VDISPLAY_TASK_PRIORITIES,
    VDISPLAY_VISION_ANCHOR_RELATIONS,
    VDISPLAY_VISION_INJECTION_COMMANDS,
    VDISPLAY_VQL_KIND_PRIORITY,
    VDISPLAY_VQL_LAYER_EXPORT_LIMIT,
    VDISPLAY_VQL_MAP_TARGET_LIMIT,
    VDISPLAY_VQL_OCR_TEXT_MAX_LEN,
    VDISPLAY_VQL_TARGET_LIMIT,
}

# Runtime-only vars (set by CLI/session, no built-in default required).
RUNTIME_ONLY_KEYS = frozenset(
    {
        "VDISPLAY_AGENT_BROKER",
        "VDISPLAY_AGENT_DB",
        "VDISPLAY_AGENT_FORCE_REMOTE",
        "VDISPLAY_AGENT_TOKEN",
        "VDISPLAY_ALLOW_YDOTOOL_TYPING",
        "VDISPLAY_CAPTURE_ALLOW_PORTAL",
        "VDISPLAY_CAPTURE_SOURCE",
        "VDISPLAY_CONFIG",
        "VDISPLAY_EVENT_STORE",
        "VDISPLAY_OBSERVE_SIDECAR",
        "VDISPLAY_OBSERVE_VQL",
        "VDISPLAY_SCREEN_CONTEXT_JSON",
        "VDISPLAY_SCREEN_CONTEXT_PATH",
        "VDISPLAY_SCREENCAST_MULTIPLE",
        "VDISPLAY_SESSION",
        "VDISPLAY_SESSION_DIR",
        "VDISPLAY_SESSION_ID",
        "VDISPLAY_VISION_LLM",
        "VDISPLAY_VISION_LLM_ENABLED",
    }
)

# Automation / project keys documented in .env.example but resolved via env_loader (not ENV_DEFAULTS).
AUTOMATION_ENV_KEYS = frozenset(
    {
        "VDISPLAY_AUTOMATION_OBSERVE",
        "VDISPLAY_AUTOMATION_OBSERVE_ON_SCREENSHOT",
        "VDISPLAY_AUTOMATION_VERIFY_STRICT",
        "VDISPLAY_AUTOMATION_REJECT_VISION_STUBS",
        "VDISPLAY_AUTOMATION_SESSION",
        "VDISPLAY_AUTOMATION_POST_ACT_VERIFY",
        "VDISPLAY_METADATA_DIR",
        "VDISPLAY_DEFAULT_MONITOR",
        "VDISPLAY_DEFAULT_MAP",
        "VDISPLAY_PLANFILE",
    }
)


def _parse_env_example_keys() -> set[str]:
    keys: set[str] = set()
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key.startswith("VDISPLAY_"):
            keys.add(key)
    return keys


def test_env_defaults_documented_in_env_example() -> None:
    example = _parse_env_example_keys()
    missing = sorted(set(ENV_DEFAULTS) - example)
    assert not missing, f"ENV_DEFAULTS keys missing from .env.example: {missing}"


def test_config_option_keys_documented_in_env_example() -> None:
    example = _parse_env_example_keys()
    missing = sorted(CONFIG_OPTION_KEYS - example)
    assert not missing, f"config_options env keys missing from .env.example: {missing}"


def test_automation_env_keys_documented_in_env_example() -> None:
    example = _parse_env_example_keys()
    missing = sorted(AUTOMATION_ENV_KEYS - example)
    assert not missing, f"automation env keys missing from .env.example: {missing}"


def test_metadata_subdirs_match_vdisplay_layout() -> None:
    from vdisplay.application.project_config import load_project_config

    cfg = load_project_config(ROOT)
    expected = set(cfg.options.metadata_subdirs)
    base = ROOT / cfg.automation.metadata_dir
    if not base.is_dir():
        pytest.skip(".vdisplay not present in checkout")
    actual = {p.name for p in base.iterdir() if p.is_dir() and not re.match(r"^\d{4}-\d{2}-\d{2}T", p.name)}
    if not actual:
        pytest.skip(".vdisplay has no metadata subdirs in this checkout (fresh CI workspace)")
    assert expected <= actual, f"missing metadata dirs: {sorted(expected - actual)}"


from __future__ import annotations

from pathlib import Path

import pytest

from vdisplay.application.config_options import ConfigOptions, get_runtime_options
from vdisplay.application.env_loader import _LOADED_PATHS, load_project_env
from vdisplay.application.project_config import load_project_config


@pytest.fixture(autouse=True)
def _reset_env_loader_cache() -> None:
    _LOADED_PATHS.clear()
    get_runtime_options.cache_clear()
    yield
    _LOADED_PATHS.clear()
    get_runtime_options.cache_clear()


def test_load_project_env_sets_variables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_DEFAULT_MONITOR", raising=False)
    monkeypatch.delenv("VDISPLAY_CONTROL_BACKENDS", raising=False)
    (tmp_path / ".env").write_text(
        "VDISPLAY_DEFAULT_MONITOR=HDMI-1\nVDISPLAY_CONTROL_BACKENDS=auto,vision\n",
        encoding="utf-8",
    )
    load_project_env(tmp_path)
    assert __import__("os").environ["VDISPLAY_DEFAULT_MONITOR"] == "HDMI-1"
    assert __import__("os").environ["VDISPLAY_CONTROL_BACKENDS"] == "auto,vision"


def test_config_options_from_env_without_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_CONTROL_BACKENDS", "auto,custom")
    monkeypatch.setenv("VDISPLAY_VQL_TARGET_LIMIT", "64")
    monkeypatch.setenv("VDISPLAY_TASK_PRIORITIES", "urgent=-1,normal=2")
    options = ConfigOptions.from_mapping(None)
    assert options.control_backends == ["auto", "custom"]
    assert options.vql.target_limit == 64
    assert options.priority_rank("urgent") == -1


def test_yaml_overrides_env_for_options(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_CONTROL_BACKENDS", "auto,env-only")
    (tmp_path / "vdisplay.yaml").write_text(
        """
options:
  control_backends: [auto, yaml-only]
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    assert config.options.control_backends == ["auto", "yaml-only"]


def test_env_cli_format_catalogs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VDISPLAY_CONTROL_LIST_FORMATS", "flat,custom")
    monkeypatch.setenv("VDISPLAY_OBSERVE_OUTPUT_FORMATS", "json,custom")
    options = ConfigOptions.from_mapping(None)
    assert options.control_list_formats == ["flat", "custom"]
    assert "custom" in options.observe_output_formats


def test_retry_policy_uses_env_strategies(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.control.retry_policy import RetryPolicy

    monkeypatch.setenv("VDISPLAY_CONTROL_RETRY_STRATEGIES", "retry_scope,refresh_map")
    policy = RetryPolicy.from_env()
    assert policy.strategies == ("retry_scope", "refresh_map")


def test_env_defaults_registry_values(monkeypatch: pytest.MonkeyPatch) -> None:
    from vdisplay.application.env_defaults import ENV_DEFAULTS, env_float_value, vision_backend_name

    monkeypatch.delenv("VDISPLAY_VISION_BACKEND", raising=False)
    assert vision_backend_name() == "auto"
    monkeypatch.setenv("VDISPLAY_REPLAY_DELAY_S", "0.5")
    assert env_float_value("VDISPLAY_REPLAY_DELAY_S") == 0.5
    assert "VDISPLAY_PIPEWIRE_CAPTURE_TIMEOUT_S" in ENV_DEFAULTS


def test_env_overrides_automation_when_yaml_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VDISPLAY_DEFAULT_MONITOR", raising=False)
    (tmp_path / ".env").write_text("VDISPLAY_DEFAULT_MONITOR=DP-2\n", encoding="utf-8")
    config = load_project_config(tmp_path)
    assert config.automation.default_monitor == "DP-2"

from __future__ import annotations

import pytest
from pathlib import Path

from vdisplay.desktop_apps import (
    DESKTOP_APPS,
    get_desktop_app,
    ide_hints_for,
    launch_env_for,
    list_desktop_apps,
)


def test_list_desktop_apps_returns_profiles() -> None:
    apps = list_desktop_apps()
    assert isinstance(apps, list)
    if apps:
        assert "app_id" in apps[0]
        assert "variants" in apps[0]


def test_get_desktop_app_aliases() -> None:
    if "pycharm" not in DESKTOP_APPS:
        pytest.skip("pycharm not installed on host")
    app = get_desktop_app("jetbrains")
    assert app.app_id == "pycharm"


def test_ide_hints_for_known_app() -> None:
    if "cursor" not in DESKTOP_APPS:
        pytest.skip("cursor not installed on host")
    hints = ide_hints_for("cursor")
    assert hints["app"] == "Cursor"
    assert "window_title_contains" in hints


def test_launch_env_for_xwayland_unsets_wayland() -> None:
    if "pycharm" not in DESKTOP_APPS:
        pytest.skip("pycharm not installed on host")
    app = get_desktop_app("pycharm")
    xwayland = next(v for v in app.variants if v.variant_id.endswith("xwayland"))
    env = launch_env_for(xwayland)
    assert "WAYLAND_DISPLAY" not in env
    assert env.get("DISPLAY") == ":0"


def test_unknown_app_raises() -> None:
    with pytest.raises(KeyError, match="unknown app"):
        get_desktop_app("not-a-real-app-id")


def test_resolve_map_path_ignores_manifest(tmp_path: Path) -> None:
    from vdisplay.desktop_apps import resolve_map_path

    manifest = tmp_path / "pycharm-chat.manifest.json"
    manifest.write_text('{"version": 1, "app_id": "pycharm"}', encoding="utf-8")
    real_map = tmp_path / "pycharm-chat.json"
    real_map.write_text('{"elements": {"ask": {}}}', encoding="utf-8")

    if "pycharm" not in DESKTOP_APPS:
        pytest.skip("pycharm not installed on host")

    resolved = resolve_map_path("pycharm", str(manifest))
    assert resolved is None
    resolved_real = resolve_map_path("pycharm", str(real_map))
    assert resolved_real == str(real_map.resolve())


def test_resolve_map_path_finds_project_map() -> None:
    from vdisplay.desktop_apps import resolve_map_path

    if "pycharm" not in DESKTOP_APPS:
        pytest.skip("pycharm not installed on host")
    resolved = resolve_map_path("pycharm")
    if Path("/home/tom/github/wronai/vdisplay/maps/pycharm-chat.json").is_file():
        assert resolved is not None
        assert resolved.endswith("maps/pycharm-chat.json")
        assert "manifest" not in resolved

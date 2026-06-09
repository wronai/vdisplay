from __future__ import annotations

from vdisplay.control.descriptors import (
    BUILTIN_PROVIDER_DESCRIPTORS,
    HostEnvironmentKind,
    descriptor_for,
    detect_platform_profile,
    extension_catalog,
    resolve_host_environment,
)
from vdisplay.control.registry import default_provider_registry
from vdisplay.control.session_kind import SessionKind
from vdisplay.control.verify_strategy import VerifyStrategy


def test_builtin_provider_descriptors_cover_registry() -> None:
    registry = default_provider_registry()
    assert registry.list_names() == sorted(item.provider_id for item in BUILTIN_PROVIDER_DESCRIPTORS)
    for name in registry.list_names():
        descriptor = registry.get_descriptor(name)
        assert descriptor is not None
        assert descriptor.provider_id == name


def test_descriptor_for_aliases() -> None:
    assert descriptor_for("playwright") is not None
    assert descriptor_for("playwright").provider_id == "browser"
    assert descriptor_for("a11y").provider_id == "atspi"


def test_terminal_descriptor_declares_session_and_grid() -> None:
    terminal = descriptor_for("terminal")
    assert terminal is not None
    assert terminal.session_kind == SessionKind.TERMINAL
    assert terminal.capabilities.has_terminal_grid is True
    assert VerifyStrategy.TEXT in terminal.verify_strategies


def test_extension_catalog_shape() -> None:
    catalog = extension_catalog()
    assert "platform" in catalog
    assert "terminology" in catalog
    assert "host_environment" in catalog["terminology"]
    assert "providers" in catalog
    assert len(catalog["providers"]) == 7
    assert "browser_engine_profiles" in catalog
    assert "application_profiles" in catalog
    assert "selector_extensions" in catalog
    assert "session_kinds" in catalog
    assert "verify_strategies" in catalog


def test_detect_platform_profile_has_os_family() -> None:
    profile = detect_platform_profile()
    assert profile.os_family
    assert profile.display_stack in {"x11", "wayland", "headless"}
    assert isinstance(profile.host_environment, HostEnvironmentKind)
    assert profile.to_dict()["host_environment"] == profile.host_environment.value


def test_resolve_host_environment_linux_mapping() -> None:
    assert resolve_host_environment(os_family="linux", display_stack="x11") == HostEnvironmentKind.LINUX_X11
    assert resolve_host_environment(os_family="linux", display_stack="wayland") == HostEnvironmentKind.LINUX_WAYLAND
    assert resolve_host_environment(os_family="linux", display_stack="headless") == HostEnvironmentKind.LINUX_HEADLESS


def test_resolve_host_environment_other_os() -> None:
    assert resolve_host_environment(os_family="windows", display_stack="x11") == HostEnvironmentKind.WINDOWS
    assert resolve_host_environment(os_family="darwin", display_stack="wayland") == HostEnvironmentKind.DARWIN
    assert resolve_host_environment(os_family="freebsd", display_stack="x11") == HostEnvironmentKind.UNKNOWN


def test_detect_platform_profile_host_environment_matches_display_stack(monkeypatch) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("DISPLAY", raising=False)
    profile = detect_platform_profile()
    if profile.os_family == "linux":
        assert profile.host_environment == HostEnvironmentKind(f"linux_{profile.display_stack}")

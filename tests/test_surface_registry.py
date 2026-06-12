"""Unit tests for surface correlation (X11 + GNOME + AT-SPI + ps)."""

from __future__ import annotations

from vdisplay.windows.surface_registry import (
    apply_jetbrains_wayland_heuristic,
    correlate_surfaces,
    summarize_app_surfaces,
)


def test_correlate_surfaces_merges_same_pid() -> None:
    monitors = [{"monitor_index": 0, "name": "HDMI-1"}]
    x11 = [
        {
            "window_id": "123",
            "title": "VSCodium",
            "wm_class": "VSCodium",
            "pid": 1001,
            "monitor_name": "DP-1",
            "x": 0,
            "y": 0,
            "width": 800,
            "height": 600,
            "process_name": "codium",
        }
    ]
    gnome = [
        {
            "title": "VSCodium",
            "wm_class": "VSCodium",
            "pid": 1001,
            "monitor_index": 1,
            "x": 0,
            "y": 2560,
            "width": 800,
            "height": 600,
        }
    ]
    atspi = [{"pid": 1001, "name": "VSCodium", "window_title": "VSCodium"}]
    processes = [{"pid": 1001, "comm": "codium", "cmdline": "/usr/bin/codium"}]

    surfaces = correlate_surfaces(
        x11_windows=x11,
        gnome_windows=gnome,
        atspi_apps=atspi,
        processes=processes,
        monitors=monitors,
    )
    assert len(surfaces) == 1
    row = surfaces[0]
    assert row["pid"] == 1001
    assert row["ide_hint"] == "vscode"
    assert row["stack"] == "xwayland"
    assert row["confidence"] >= 0.9
    assert "process_pid" in row["match_reasons"]
    assert "gnome_shell_pid" in row["match_reasons"]
    assert row["sources"]["x11"]["window_id"] == "123"
    assert row["sources"]["gnome_shell"]["title"] == "VSCodium"


def test_correlate_surfaces_wayland_native_pycharm() -> None:
    monitors = [{"monitor_index": 0, "name": "HDMI-1"}]
    gnome = [
        {
            "title": "koru – PyCharm",
            "wm_class": "jetbrains-pycharm",
            "pid": 1377491,
            "monitor_index": 0,
            "x": 100,
            "y": 2600,
            "width": 1920,
            "height": 1080,
        }
    ]
    processes = [
        {
            "pid": 1377491,
            "comm": "java",
            "cmdline": "java ... pycharm ...",
        }
    ]

    surfaces = correlate_surfaces(
        x11_windows=[],
        gnome_windows=gnome,
        atspi_apps=[],
        processes=processes,
        monitors=monitors,
    )
    assert len(surfaces) == 1
    row = surfaces[0]
    assert row["ide_hint"] == "jetbrains"
    assert row["stack"] == "wayland_native"
    assert row["monitor_name"] == "HDMI-1"
    assert row["pid"] == 1377491


def test_correlate_surfaces_title_match_orphan_gnome() -> None:
    x11 = [
        {
            "window_id": "456",
            "title": "README.md - project",
            "app_label": "README.md - project",
            "wm_class": "code",
            "pid": None,
            "monitor_name": "DP-1",
            "x": 10,
            "y": 10,
            "width": 1200,
            "height": 900,
        }
    ]
    gnome = [
        {
            "title": "README.md - project",
            "wm_class": "code",
            "pid": None,
            "monitor_index": 1,
            "x": 10,
            "y": 10,
            "width": 1200,
            "height": 900,
        }
    ]

    surfaces = correlate_surfaces(
        x11_windows=x11,
        gnome_windows=gnome,
        atspi_apps=[],
        processes=[],
        monitors=[],
    )
    matched = [row for row in surfaces if row.get("stack") == "xwayland"]
    assert len(matched) == 1
    assert matched[0]["sources"]["x11"]["window_id"] == "456"
    assert matched[0]["sources"]["gnome_shell"]["title"] == "README.md - project"


def test_summarize_app_surfaces_drops_helpers_and_toolbox() -> None:
    surfaces = [
        {
            "display_name": "Toolbox",
            "ide_hint": "jetbrains",
            "stack": "x11",
            "monitor_name": "HDMI-1",
            "confidence": 0.7,
            "bounds": {"x": 1, "y": 2, "width": 3, "height": 4},
            "sources": {"process": {"comm": "jetbrains-toolb", "cmdline": "toolbox"}},
        },
        {
            "display_name": "pycharm",
            "ide_hint": "jetbrains",
            "stack": "process_only",
            "monitor_name": None,
            "confidence": 0.5,
            "sources": {"process": {"comm": "pycharm", "cmdline": "/opt/pycharm"}},
        },
        {
            "display_name": "Web",
            "ide_hint": "firefox",
            "stack": "process_only",
            "monitor_name": None,
            "confidence": 0.5,
            "sources": {"process": {"comm": "Web", "cmdline": "firefox --type=utility"}},
        },
        {
            "display_name": "Untitled - VSCodium",
            "ide_hint": "vscode",
            "stack": "x11",
            "monitor_name": "DP-1",
            "confidence": 0.7,
            "bounds": {"x": 0, "y": 0, "width": 800, "height": 600},
            "sources": {"process": {"comm": "codium", "cmdline": "/usr/bin/codium"}},
        },
    ]
    summary = summarize_app_surfaces(surfaces)
    hints = {row["ide_hint"] for row in summary}
    assert hints == {"jetbrains", "vscode"}
    jetbrains = next(row for row in summary if row["ide_hint"] == "jetbrains")
    assert jetbrains["display_name"] == "pycharm"


def test_jetbrains_wayland_heuristic_links_pycharm_to_awt_proxies() -> None:
    monitors = [
        {
            "monitor_index": 0,
            "name": "HDMI-1",
            "x": 0,
            "y": 2560,
            "width": 4096,
            "height": 2560,
        }
    ]
    awt_proxies = [
        {
            "window_id": "8388636",
            "title": "Content window",
            "wm_class": "kotlinx-coroutines-scheduling-CoroutineScheduler$Worker",
            "x": 3216,
            "y": 2550,
            "width": 880,
            "height": 1400,
            "monitor_name": "HDMI-1",
        },
        {
            "window_id": "8388640",
            "title": "sun-awt-X11-XCanvasPeer",
            "wm_class": "kotlinx-coroutines-scheduling-CoroutineScheduler$Worker",
            "x": 3216,
            "y": 2772,
            "width": 880,
            "height": 1326,
            "monitor_name": "HDMI-1",
        },
    ]
    surfaces = [
        {
            "display_name": "pycharm",
            "ide_hint": "jetbrains",
            "stack": "process_only",
            "monitor_name": None,
            "pid": 1377491,
            "confidence": 0.5,
            "match_reasons": ["process_pid"],
            "sources": {
                "process": {
                    "pid": 1377491,
                    "comm": "pycharm",
                    "cmdline": "/home/tom/.local/share/JetBrains/Toolbox/apps/pycharm-2/bin/pycharm",
                }
            },
        }
    ]

    upgraded = apply_jetbrains_wayland_heuristic(
        surfaces,
        awt_proxies=awt_proxies,
        monitors=monitors,
    )
    row = upgraded[0]
    assert row["display_name"] == "PyCharm"
    assert row["stack"] == "jetbrains_xwayland"
    assert row["monitor_name"] == "HDMI-1"
    assert row["bounds"]["width"] == 880
    assert row["bounds"]["height"] == 1548
    assert "jetbrains_awt_x11_proxy" in row["match_reasons"]
    assert len(row["sources"]["x11_awt_proxies"]) == 2

    summary = summarize_app_surfaces(
        upgraded
        + [
            {
                "display_name": "Toolbox",
                "ide_hint": "jetbrains",
                "stack": "x11",
                "monitor_name": "HDMI-1",
                "confidence": 0.7,
                "bounds": {"x": 1, "y": 2, "width": 3, "height": 4},
                "sources": {"process": {"comm": "jetbrains-toolb", "cmdline": "toolbox"}},
            }
        ]
    )
    jetbrains = next(item for item in summary if item["ide_hint"] == "jetbrains")
    assert jetbrains["display_name"] == "PyCharm"
    assert jetbrains["monitor_name"] == "HDMI-1"

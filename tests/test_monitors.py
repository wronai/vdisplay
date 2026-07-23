"""Cover `vdisplay.monitors`, moved from koru on 2026-07-23.

koru keeps a thin binding that reads KORU_VDISPLAY_SOURCE and forwards it as
`explicit_source`, so the behaviour pinned here is what koru's capture path
sees.
"""

from __future__ import annotations

import json

import pytest

from vdisplay import monitors


def _identity(ide):
    return ide


def _probe(names):
    return {
        "monitor_names": list(names),
        "monitors": [{"name": n, "primary": n == names[0]} for n in names],
    }


class TestResolveSource:
    def test_explicit_source_wins_when_connected(self):
        probe = _probe(["DP-1", "DP-2"])
        chosen, out = monitors.resolve_vdisplay_source_for_ide(
            "vscode", canonical_ide=_identity, desktop_probe=lambda **k: probe,
            probe=probe, explicit_source="DP-2",
        )
        assert chosen == "DP-2"
        assert out["ok"] is True

    def test_no_env_read_without_explicit_source(self, monkeypatch):
        # The whole point of the move: the resolver must not reach into the
        # environment itself. Setting koru's variable must have no effect here.
        monkeypatch.setenv("KORU_VDISPLAY_SOURCE", "DP-2")
        probe = _probe(["DP-1", "DP-2"])
        chosen, _ = monitors.resolve_vdisplay_source_for_ide(
            "vscode", canonical_ide=_identity, desktop_probe=lambda **k: probe,
            probe=probe,
        )
        assert chosen == "DP-1"  # IDE default, not the env var

    def test_explicit_source_not_connected_fails_closed(self):
        probe = _probe(["DP-1"])
        chosen, out = monitors.resolve_vdisplay_source_for_ide(
            "vscode", canonical_ide=_identity, desktop_probe=lambda **k: probe,
            probe=probe, explicit_source="HDMI-9",
        )
        assert chosen == "HDMI-9"
        assert out["ok"] is False
        assert "not connected" in out["error"]

    def test_falls_back_to_first_connected_when_default_absent(self):
        probe = _probe(["HDMI-1"])  # no DP-1
        chosen, _ = monitors.resolve_vdisplay_source_for_ide(
            "vscode", canonical_ide=_identity, desktop_probe=lambda **k: probe,
            probe=probe,
        )
        assert chosen == "HDMI-1"

    def test_probe_is_fetched_when_not_supplied(self):
        calls = []

        def probe_fn(**kwargs):
            calls.append(kwargs)
            return _probe(["DP-1"])

        monitors.resolve_vdisplay_source_for_ide(
            "vscode", canonical_ide=_identity, desktop_probe=probe_fn,
        )
        assert calls and calls[0]["ide"] == "vscode"


class TestCaptureMonitorMismatch:
    def test_mismatch_message_names_no_koru_variable(self, tmp_path):
        map_path = tmp_path / "map.json"
        map_path.write_text(
            json.dumps({"capture_meta": {"source": "DP-2"}, "elements": {}}),
            encoding="utf-8",
        )
        result = monitors.map_capture_monitor_mismatch(str(map_path), source="HDMI-1")
        assert result is not None
        assert result["map_source"] == "DP-2"
        assert result["capture_source"] == "HDMI-1"
        # The message is vdisplay's now, so it must not mention koru's env var.
        assert "KORU_" not in result["message"]
        assert "override the capture source" in result["message"]

    def test_no_mismatch_when_sources_agree(self, tmp_path):
        map_path = tmp_path / "map.json"
        map_path.write_text(
            json.dumps({"capture_meta": {"source": "DP-2"}, "elements": {}}),
            encoding="utf-8",
        )
        assert monitors.map_capture_monitor_mismatch(str(map_path), source="DP-2") is None

    def test_unloadable_map_reports_an_error_not_a_crash(self, tmp_path):
        result = monitors.map_capture_monitor_mismatch(
            str(tmp_path / "absent.json"), source="DP-1"
        )
        assert result is not None
        assert "could not load GUI map" in result["message"]


def test_module_does_not_import_koru():
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(monitors.__file__).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert "koru" not in roots, f"vdisplay.monitors imports koru: {sorted(roots)}"


@pytest.mark.parametrize("name", monitors.__all__)
def test_exports_exist(name):
    assert callable(getattr(monitors, name))

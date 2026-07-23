"""Cover `vdisplay.vql`, the sidecar reader extracted from koru on 2026-07-22.

koru keeps thin re-export shims pointing at these functions, so a behaviour
change here reaches koru's drive path directly.
"""

from __future__ import annotations

import json
import os
import time

import pytest

from vdisplay import vql


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


class TestSidecarPaths:
    def test_png_path_resolves_only_for_existing_capture(self, tmp_path):
        png = tmp_path / "capture.png"
        png.write_bytes(b"\x89PNG")
        sidecar = str(tmp_path / "capture.png.vql.json")

        assert vql.png_path_for_vql_sidecar(sidecar) == png

        png.unlink()
        assert vql.png_path_for_vql_sidecar(sidecar) is None

    def test_png_path_ignores_sidecars_that_do_not_describe_a_capture(self, tmp_path):
        assert vql.png_path_for_vql_sidecar(str(tmp_path / "ui.vql.json")) is None

    def test_imgl_sibling_found_only_when_present(self, tmp_path):
        base = tmp_path / "capture.png.vql.json"
        _write(base, {})
        imgl = tmp_path / "capture.png.vql.imgl.json"

        assert vql.imgl_sidecar_path_for_vql(str(base)) is None
        _write(imgl, {})
        assert vql.imgl_sidecar_path_for_vql(str(base)) == str(imgl)

    def test_non_vql_paths_have_no_imgl_sibling(self, tmp_path):
        assert vql.imgl_sidecar_path_for_vql(str(tmp_path / "notes.txt")) is None


class TestLayerCount:
    def test_missing_or_unreadable_sidecar_counts_zero(self, tmp_path):
        assert vql.main_vql_layer_count(tmp_path / "absent.vql.json") == 0

        broken = tmp_path / "broken.vql.json"
        broken.write_text("{not json", encoding="utf-8")
        assert vql.main_vql_layer_count(broken) == 0


class TestImglFallbackLayers:
    def test_stale_imgl_sidecar_is_refused(self, tmp_path):
        """An imgl sidecar older than its capture describes a screen that moved on."""
        png = tmp_path / "capture.png"
        png.write_bytes(b"\x89PNG")
        base = _write(tmp_path / "capture.png.vql.json", {})
        imgl = tmp_path / "capture.png.vql.imgl.json"
        _write(imgl, {"elements": []})

        old = time.time() - 600
        os.utime(imgl, (old, old))

        assert vql.layers_from_imgl_sidecar_file(base) == ([], None)

    def test_no_sibling_yields_no_layers(self, tmp_path):
        base = _write(tmp_path / "capture.png.vql.json", {})
        assert vql.layers_from_imgl_sidecar_file(base) == ([], None)


class TestCaptureValidation:
    def test_existing_top_level_block_is_kept(self):
        meta = {"capture_validation": {"capture_confirmed": True}}
        assert vql.with_embedded_capture_validation(meta, {}) is meta

    def test_nested_block_is_lifted_from_raw(self):
        out = vql.with_embedded_capture_validation(
            {}, {"metadata": {"capture_validation": {"capture_confirmed": False}}}
        )
        assert out["capture_validation"] == {"capture_confirmed": False}

    def test_absent_block_leaves_metadata_untouched(self):
        assert vql.with_embedded_capture_validation({"a": 1}, {}) == {"a": 1}


class TestNormalizationShapes:
    def test_ui_elements_sidecar_mirrors_layers_and_tags_source(self):
        out = vql.vql_from_ui_elements({"ui_elements": [{"id": "x"}]}, "cand.json", None)
        assert out["_source"] == "cand.json"
        assert out["layers"] == out["ui_elements"]

    def test_program_wrapper_is_unwrapped(self):
        out = vql.vql_from_program_wrapper(
            {"vql": {"program": {"ui_elements": [{"id": "a"}]}}}, "cand.json"
        )
        assert out is not None
        assert out["_source"] == "cand.json"
        assert out["layers"] == [{"id": "a"}]

    def test_program_wrapper_returns_none_so_dispatch_continues(self):
        assert vql.vql_from_program_wrapper({"ui_elements": []}, "cand.json") is None

    def test_sidecar_layers_carry_environment_from_metadata(self):
        out = vql.vql_from_sidecar_layers(
            {"metadata": {"environment": {"display": ":1"}}}, "cand.json", [{"id": "l"}], None
        )
        assert out["environment"] == {"display": ":1"}
        assert out["ui_elements"] == out["layers"] == [{"id": "l"}]

    def test_default_normalization_tags_source_and_defaults_layers(self):
        assert vql.vql_metadata_default({}, "cand.json") == {"_source": "cand.json", "layers": []}


def test_module_does_not_import_koru():
    """The whole point of the extraction: vdisplay must not depend on its consumer.

    Checked over the parsed import statements rather than the raw text —
    prose mentioning koru is expected and must not fail the contract.
    """
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(vql.__file__).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])

    assert "koru" not in roots, f"vdisplay.vql imports koru: {sorted(roots)}"


@pytest.mark.parametrize("name", vql.__all__)
def test_every_exported_name_exists(name):
    assert callable(getattr(vql, name))

#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "common"))

from screenshot_meta import build_screenshot_meta, describe_screenshot_nl, meta_path_for


def test_describe_screenshot_nl() -> None:
    nl = describe_screenshot_nl(
        width=1280,
        height=720,
        session_kind="virtual",
        display=":99",
        monitors=[{"name": "VIRTUAL0"}],
        windows=[{"app_label": "xclock", "is_internal": False}],
    )
    assert "1280×720" in nl
    assert "virtual display :99" in nl
    assert "xclock" in nl


def test_build_and_meta_path(tmp_path: Path) -> None:
    png = tmp_path / "sample.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x10\x00\x00\x00\x08"
        b"\x08\x02\x00\x00\x00\x90\x91h6"
        b"\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe"
        b"\xa7V\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    meta = build_screenshot_meta(
        png,
        label="Test capture",
        phase="baseline",
        session_kind="virtual",
        display=":99",
    )
    assert meta["width"] == 16
    assert meta["height"] == 8
    assert meta_path_for(png).name == "sample.png.meta.json"
    assert "Test capture" in meta["nl"]

    sidecar = meta_path_for(png)
    sidecar.write_text(json.dumps(meta), encoding="utf-8")
    loaded = json.loads(sidecar.read_text(encoding="utf-8"))
    assert loaded["bytes"] == meta["bytes"]

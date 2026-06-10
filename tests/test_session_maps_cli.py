"""Session map archival and session CLI commands."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from vdisplay.application.commands import CommandRequest, CommandResult, CommandVerb
from vdisplay.application.executor import execute
from vdisplay.application.session_recorder import (
    archive_map_artifacts,
    discover_session_dirs,
    export_session_zip,
    extract_diagnostics,
    load_session_document,
)
from vdisplay.cli import build_parser
from vdisplay.control.gui_map import GuiMapBounds, GuiMapPack, GuiMapRegion, element_from_ocr_box, save_gui_map
from vdisplay.control.models import ControlBounds
from vdisplay.control.vision_ocr import OcrTextBox


def _sample_map(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    box = OcrTextBox("Ask", ControlBounds(x=1, y=2, width=40, height=20), 0.9)
    element = element_from_ocr_box(
        box,
        element_id="ask",
        region_id="chat",
        capture_meta={"width": 400, "height": 200},
        monitor="DP-2",
        rotation="normal",
        png=b"",
    )
    pack = GuiMapPack(
        version=1,
        monitor="DP-2",
        regions={
            "chat": GuiMapRegion(
                id="chat",
                label="chat",
                scope_bounds=GuiMapBounds(x=0, y=0, width=400, height=200),
                elements=["ask"],
            )
        },
        elements={"ask": element},
    )
    save_gui_map(path, pack)
    return path


def test_archive_map_artifacts_copies_json_and_md(tmp_path: Path) -> None:
    map_path = _sample_map(tmp_path / "chat.json")
    session_root = tmp_path / "session"
    session_root.mkdir()
    cmd = CommandRequest(verb=CommandVerb.CONTROL_CLICK, extra={"map_path": str(map_path)})
    result = CommandResult.success(
        action="control_click",
        data={"map_path": str(map_path), "map_target": "ask"},
    )
    diagnostics = extract_diagnostics(result)
    diagnostics["control"] = {"map": {"path": str(map_path), "target": "ask"}}

    entries = archive_map_artifacts(session_root, cmd, result, diagnostics)

    assert (session_root / "maps" / "chat.json").is_file()
    assert (session_root / "maps" / "chat.md").is_file()
    kinds = {entry["kind"] for entry in entries}
    assert "map" in kinds
    assert "map-md" in kinds


def test_executor_archives_map_in_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    map_path = _sample_map(tmp_path / "maps" / "chat.json")
    session_dir = tmp_path / "audit"
    monkeypatch.setenv("VDISPLAY_SESSION_DIR", str(session_dir))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "vdisplay.application.executor.execute_local",
        lambda cmd: {
            "ok": True,
            "map_path": str(map_path),
            "map_target": "ask",
            "diagnostics": {
                "control": {
                    "action": "click",
                    "map": {"path": str(map_path), "target": "ask"},
                    "routing": {"selected_provider": "vision"},
                }
            },
        },
    )

    execute(
        CommandRequest(verb=CommandVerb.CONTROL_CLICK, request_source="cli"),
        force_route="local",
    )

    doc = load_session_document(session_dir)
    assert doc.maps
    assert (session_dir / "maps" / "chat.json").is_file()
    readme = (session_dir / "README.md").read_text(encoding="utf-8")
    assert "## Maps" in readme


def test_session_cli_list_show_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session_dir = tmp_path / ".vdisplay" / "demo-session"
    (session_dir / "steps" / "0001").mkdir(parents=True)
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "version": 1,
                "session_id": "demo-session",
                "started_at": "2026-06-10T10:00:00Z",
                "updated_at": "2026-06-10T10:00:01Z",
                "summary": {"total_steps": 1, "ok_steps": 1, "failed_steps": 0},
                "steps": [],
                "maps": [],
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "README.md").write_text("# demo session\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    parser = build_parser()
    list_args = parser.parse_args(["session", "list", "--root", ".vdisplay"])
    assert list_args.func(list_args) == 0

    sessions = discover_session_dirs(root=tmp_path / ".vdisplay")
    assert sessions[0].name == "demo-session"

    show_args = parser.parse_args(["session", "show", "--dir", str(session_dir)])
    assert show_args.func(show_args) == 0

    zip_path = tmp_path / "out.zip"
    export_args = parser.parse_args(
        ["session", "export", "--dir", str(session_dir), "-o", str(zip_path)]
    )
    assert export_args.func(export_args) == 0
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    assert any(name.endswith("session.json") for name in names)

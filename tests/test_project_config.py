from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.auto.defaults import apply_project_defaults, build_decision_data, vql_decision_slice
from vdisplay.application.auto.feedback import (
    finalize_result_ok,
    is_control_actuation,
    parse_vision_stub_from_output,
    prepare_command,
)
from vdisplay.application.auto.tasks import AutoTask
from vdisplay.application.project_config import load_project_config


def test_load_project_vdisplay_yaml(tmp_path: Path) -> None:
    (tmp_path / "vdisplay.yaml").write_text(
        """
version: "1"
project:
  name: demo
automation:
  default_monitor: DP-2
  metadata_dir: .vdisplay
monitors:
  - name: DP-2
    default: true
actions:
  cursor_chat:
    monitor: DP-2
    vision_anchor: Chat
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    assert config.project_name == "demo"
    assert config.default_monitor == "DP-2"
    assert config.action("cursor_chat") is not None
    assert config.action("cursor_chat").vision_anchor == "Chat"


def test_apply_project_defaults_action_ref(tmp_path: Path) -> None:
    (tmp_path / "vdisplay.yaml").write_text(
        """
automation:
  default_monitor: DP-1
actions:
  cursor_ask:
    monitor: DP-1
    vision_anchor: Ask
    vision_anchor_rel: below
    backend: vision
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    task = AutoTask(
        id="t",
        title="find",
        command="vdisplay control find --backend vision",
        source="yaml",
        raw={"action_ref": "cursor_ask"},
    )
    merged = apply_project_defaults(task, config)
    assert merged.monitor == "DP-1"
    assert "--vision-anchor Ask" in merged.command
    assert "--vision-anchor-rel below" in merged.command


def test_apply_project_defaults_injects_vision_on_focus(tmp_path: Path) -> None:
    (tmp_path / "vdisplay.yaml").write_text(
        """
automation:
  default_monitor: DP-1
actions:
  cursor_chat:
    app: cursor
    monitor: DP-1
    vision_anchor: Chat
    vision_anchor_rel: below
    backend: vision
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    task = AutoTask(
        id="t",
        title="focus",
        command="vdisplay control focus",
        source="yaml",
        raw={"action_ref": "cursor_chat"},
    )
    merged = apply_project_defaults(task, config)
    assert "--vision-anchor Chat" in merged.command
    assert "--vision-anchor-rel below" in merged.command
    assert "--backend vision" in merged.command


def test_resolve_action_map_from_conventional_path(tmp_path: Path) -> None:
    maps_dir = tmp_path / "maps"
    maps_dir.mkdir()
    (maps_dir / "cursor-chat.json").write_text('{"version": 1}', encoding="utf-8")
    (tmp_path / "vdisplay.yaml").write_text(
        """
actions:
  cursor_chat:
    app: cursor
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    task = AutoTask(
        id="t",
        title="click",
        command="vdisplay control click --target chat",
        source="yaml",
        raw={"action_ref": "cursor_chat"},
    )
    merged = apply_project_defaults(task, config)
    assert merged.map_path is not None
    assert merged.map_path.endswith("maps/cursor-chat.json")


def test_build_decision_data_includes_locations(tmp_path: Path) -> None:
    (tmp_path / "vdisplay.yaml").write_text(
        """
automation:
  metadata_dir: .vdisplay
actions:
  cursor_chat:
    app: cursor
    monitor: DP-1
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    task = AutoTask(
        id="t",
        title="focus",
        command="vdisplay control focus",
        source="yaml",
        monitor="DP-1",
        raw={"action_ref": "cursor_chat"},
    )
    data = build_decision_data(task, config, prepared_command="vdisplay control focus --backend vision")
    assert data["action_ref"] == "cursor_chat"
    assert data["monitor"] == "DP-1"
    assert "data_locations" in data
    assert str(tmp_path / ".vdisplay" / "observe") in data["data_locations"]["observe"]


def test_vql_decision_slice_reads_render_intent_layers(tmp_path: Path) -> None:
    vql_path = tmp_path / "screen.png.vql.json"
    vql_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "render_intent": {
                        "layers": [
                            {
                                "kind": "input",
                                "id": "editor",
                                "text": "editor",
                                "click_center": {"x": 50, "y": 25},
                            },
                            {
                                "kind": "ocr",
                                "text": "Ask",
                                "click_center": {"x": 10, "y": 10},
                            },
                            {
                                "kind": "ocr",
                                "text": "x" * 60,
                                "click_center": {"x": 1, "y": 1},
                            },
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    data = build_decision_data(
        AutoTask(id="t", title="x", command="vdisplay control click", source="yaml"),
        load_project_config(tmp_path),
        vql_path=vql_path,
    )
    assert data["vql_layer_count"] == 3
    assert len(data["vql_targets"]) == 2
    assert data["vql_targets"][0]["kind"] == "input"
    assert vql_decision_slice(vql_path)["vql_targets"][0]["click_center"] == {"x": 50, "y": 25}


def test_config_options_load_from_vdisplay_yaml(tmp_path: Path) -> None:
    (tmp_path / "vdisplay.yaml").write_text(
        """
options:
  control_backends: [auto, vision, custom]
  task_priorities:
    urgent: -1
    normal: 2
  planfile_task_keys: [automation, my_tasks]
  vql:
    target_limit: 10
    kind_priority:
      panel: -1
      input: 0
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    assert "custom" in config.options.control_backends
    assert config.options.priority_rank("urgent") == -1
    assert config.options.planfile_task_keys == ["automation", "my_tasks"]
    assert config.options.vql.target_limit == 10
    assert config.options.vql.kind_priority["panel"] == -1


def test_apply_project_defaults_skips_vision_on_ide_prompt(tmp_path: Path) -> None:
    (tmp_path / "vdisplay.yaml").write_text(
        """
actions:
  pycharm_chat:
    monitor: DP-2
    map: maps/pycharm-chat.json
    vision_anchor: Ask
    backend: vision
""",
        encoding="utf-8",
    )
    maps_dir = tmp_path / "maps"
    maps_dir.mkdir()
    (maps_dir / "pycharm-chat.json").write_text('{"version": 1}', encoding="utf-8")
    config = load_project_config(tmp_path)
    task = AutoTask(
        id="t",
        title="prompt",
        command="vdisplay ide prompt --ide pycharm --target ai-chat-input --text hi",
        source="yaml",
        raw={"action_ref": "pycharm_chat"},
    )
    merged = apply_project_defaults(task, config)
    assert "--vision-anchor" not in merged.command
    assert merged.map_path is not None


def test_finalize_rejects_verify_none_when_strict() -> None:
    from vdisplay.application.auto.executor import ExecuteResult
    from vdisplay.application.auto.feedback import TaskFeedback
    from vdisplay.application.project_config import AutomationDefaults, ProjectConfig

    config = ProjectConfig(automation=AutomationDefaults(verify_strict=True))
    result = ExecuteResult(ok=True, method="vdisplay-cli", output='{"ok": true}')
    feedback = TaskFeedback(verify_requested=True)
    assert finalize_result_ok(result, feedback, config=config) is False
    assert feedback.verify_passed is None


def test_finalize_rejects_vision_stub_on_actuation() -> None:
    from vdisplay.application.auto.executor import ExecuteResult
    from vdisplay.application.auto.feedback import TaskFeedback
    from vdisplay.application.project_config import ProjectConfig

    config = ProjectConfig()
    stub_json = '{"selected": {"backend": "vision", "bounds": {"width": 0, "height": 0}, "state": {"stub": true}}}'
    result = ExecuteResult(ok=True, method="vdisplay-cli", output=stub_json)
    feedback = TaskFeedback(prepared_command="vdisplay control focus --backend vision")
    assert parse_vision_stub_from_output(stub_json) is True
    assert is_control_actuation("vdisplay control focus --backend vision") is True
    assert finalize_result_ok(result, feedback, config=config) is False


def test_finalize_allows_vision_stub_on_find() -> None:
    from vdisplay.application.auto.executor import ExecuteResult
    from vdisplay.application.auto.feedback import TaskFeedback
    from vdisplay.application.project_config import ProjectConfig

    config = ProjectConfig()
    stub_json = '{"selected": {"backend": "vision", "bounds": {"width": 0, "height": 0}, "state": {"stub": true}}}'
    result = ExecuteResult(ok=True, method="vdisplay-cli", output=stub_json)
    feedback = TaskFeedback(prepared_command="vdisplay control find --backend vision")
    assert finalize_result_ok(result, feedback, config=config) is True

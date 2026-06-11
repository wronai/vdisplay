from __future__ import annotations

import json
from pathlib import Path

import pytest

from vdisplay.application.auto.executor import execute_task_command
from vdisplay.application.auto.runner import run_auto_loop, run_auto_once
from vdisplay.application.auto.tasks import (
    ensure_auto_dependencies,
    load_auto_tasks,
    next_auto_task,
    write_yaml_task_status,
)
from vdisplay.cli import build_parser, main


def test_parser_has_auto_command() -> None:
    parser = build_parser()
    kinds = parser._subparsers._group_actions[0].choices  # type: ignore[index]
    assert "auto" in kinds


def test_load_automation_tasks_from_yaml(tmp_path: Path) -> None:
    plan = tmp_path / "planfile.yaml"
    plan.write_text(
        """
automation:
  - id: shot-dp1
    title: Capture DP-1
    status: todo
    priority: high
    handler: vdisplay monitors
  - id: done-task
    title: Already done
    status: done
    handler: vdisplay monitors
""".strip(),
        encoding="utf-8",
    )
    tasks = load_auto_tasks(project=tmp_path, source="yaml")
    assert len(tasks) == 1
    assert tasks[0].id == "shot-dp1"
    assert tasks[0].command == "vdisplay monitors"


def test_next_auto_task_prefers_high_priority(tmp_path: Path) -> None:
    plan = tmp_path / "planfile.yaml"
    plan.write_text(
        """
automation:
  - id: low
    title: low
    status: todo
    priority: low
    handler: echo low
  - id: high
    title: high
    status: todo
    priority: high
    handler: echo high
""".strip(),
        encoding="utf-8",
    )
    tasks = load_auto_tasks(project=tmp_path, source="yaml")
    nxt = next_auto_task(tasks)
    assert nxt is not None
    assert nxt.id == "high"


def test_execute_dsl_command_dry_run() -> None:
    result = execute_task_command("MONITORS", dry_run=True)
    assert result.ok is True
    assert result.method == "dry-run"


def test_auto_once_dry_run(tmp_path: Path, capsys) -> None:
    plan = tmp_path / "planfile.yaml"
    plan.write_text(
        """
automation:
  - id: one
    title: list monitors
    status: todo
    handler: vdisplay monitors
""".strip(),
        encoding="utf-8",
    )
    rc = main(["auto", "--project", str(tmp_path), "--dry-run", "once"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["executed"][0]["ok"] is True
    assert payload["executed"][0]["method"] == "dry-run"


def test_auto_list_cli(tmp_path: Path, capsys) -> None:
    plan = tmp_path / "planfile.yaml"
    plan.write_text(
        """
automation:
  - id: one
    title: list monitors
    status: todo
    handler: vdisplay monitors
""".strip(),
        encoding="utf-8",
    )
    rc = main(["auto", "--project", str(tmp_path), "list"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 1


def test_run_auto_once_executes_vdisplay_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = tmp_path / "planfile.yaml"
    plan.write_text(
        """
automation:
  - id: one
    title: list monitors
    status: todo
    handler: vdisplay monitors
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "vdisplay.application.auto.executor._execute_vdisplay_cli",
        lambda command, project=None: type(
            "R",
            (),
            {"ok": True, "method": "vdisplay-cli", "output": "{}", "error": "", "exit_code": 0},
        )(),
    )

    result = run_auto_once(project=tmp_path, source="yaml")
    assert result.ok is True
    assert result.executed[0]["ok"] is True


def test_write_yaml_task_status_updates_automation_section(tmp_path: Path) -> None:
    plan = tmp_path / "planfile.yaml"
    plan.write_text(
        """
automation:
  - id: shot-dp1
    title: Capture DP-1
    status: todo
    priority: high
    handler: vdisplay monitors
""".strip(),
        encoding="utf-8",
    )
    write_yaml_task_status(plan, "shot-dp1", status="done", note="ok")
    tasks = load_auto_tasks(project=tmp_path, source="yaml")
    assert tasks == []


def test_yaml_auto_install_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    import sys
    import types

    monkeypatch.delitem(sys.modules, "yaml", raising=False)
    installed: list[str] = []
    real_import = builtins.__import__

    def fake_install(package_name: str, **kwargs) -> None:
        installed.append(package_name)
        yaml_mod = types.ModuleType("yaml")
        yaml_mod.safe_load = lambda text: {}
        yaml_mod.safe_dump = lambda data, **kwargs: ""
        sys.modules["yaml"] = yaml_mod

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "yaml" and "yaml" not in sys.modules:
            raise ImportError("no yaml")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr("vdisplay.utils.auto_install_package", fake_install)

    ensure_auto_dependencies(source="yaml")
    assert installed == ["PyYAML>=6.0"]


def test_run_auto_advances_past_first_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = tmp_path / "planfile.yaml"
    plan.write_text(
        """
automation:
  - id: first
    title: first
    status: todo
    priority: high
    handler: vdisplay monitors
  - id: second
    title: second
    status: todo
    priority: normal
    handler: echo second
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "vdisplay.application.auto.runner.execute_task_command",
        lambda command, dry_run=False, project=None: type(
            "R",
            (),
            {"ok": True, "method": "test", "output": command, "error": "", "exit_code": 0},
        )(),
    )

    result = run_auto_loop(project=tmp_path, source="yaml", max_tasks=2)
    assert result.ok is True
    assert len(result.executed) == 2
    assert result.executed[0]["task"]["id"] == "first"
    assert result.executed[1]["task"]["id"] == "second"
    tasks = load_auto_tasks(project=tmp_path, source="yaml")
    assert len(tasks) == 0

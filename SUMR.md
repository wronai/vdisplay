# vdisplay

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `vdisplay`
- **version**: `0.1.21`
- **python_requires**: `>=3.10,<3.14`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(1), app.doql.less, goal.yaml, .env.example, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: vdisplay;
  version: 0.1.21;
}

dependencies {
  windows: comtypes>=1.4.0;
  macos: "pyobjc-framework-ApplicationServices>=10.0, pyobjc-framework-Cocoa>=10.0";
  pillow: Pillow>=10.0;
  sampler: Pillow>=10.0;
  dev: "pytest>=8.0, Pillow>=10.0, fastapi>=0.110, httpx>=0.27, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, dsl2vdisplay, vdisplay-agent, uvicorn>=0.27, pydantic>=2, sqlmodel>=0.0.22";
  core: "pydantic>=2, tenacity>=8.0, structlog>=24.0";
  control: "dsl2vdisplay, nlp2vdisplay";
  auto: "PyYAML>=6.0, dsl2vdisplay, planfile>=0.1.103";
  browser: playwright>=1.40;
  e2e: "playwright>=1.40, pytest>=8.0";
  vision: "Pillow>=10.0, pytesseract>=0.3.10, opencv-python>=4.8";
  terminal: "pyte>=0.8.1, pexpect>=4.9, wcwidth>=0.2.13";
  agent: "vdisplay-agent, fastapi>=0.110, uvicorn>=0.27, sqlmodel>=0.0.22";
  img2nl: img2nl[analyze];
  imgl: imgl;
  vql: "vql, img2vql; sys_platform == "linux"";
  observe: "imgl, vql, img2vql; sys_platform == "linux"";
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="vdisplay"] {
  entry: vdisplay.cli:main;
}

tests {
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, VDISPLAY_IDE_FIND_TIMEOUT_S, VDISPLAY_AGENT_AUTO, VDISPLAY_AGENT_HOST, VDISPLAY_AGENT_PORT, VDISPLAY_AGENT_URL, VDISPLAY_AGENT_TOKEN, VDISPLAY_AGENT_BROKER, DISPLAY, XDG_SESSION_TYPE, VDISPLAY_SESSION_DIR, VDISPLAY_VISION_BACKEND, VDISPLAY_OCR_CACHE, VDISPLAY_SCREEN_CONTEXT_JSON, VDISPLAY_SCREEN_CONTEXT_PATH, XDG_CURRENT_DESKTOP, DESKTOP_SESSION, VDISPLAY_VISION_PREVIEW, VDISPLAY_CONTROL_MAX_ATTEMPTS, VDISPLAY_CONTROL_RETRY_DELAY_MS, VDISPLAY_CONTROL_RETRY_STRATEGIES, VDISPLAY_CONTROL_RETRY, VDISPLAY_BROWSER_DETACHED, VDISPLAY_VISION_LLM_MODE, VDISPLAY_VISION_LLM_MODALITIES, VDISPLAY_VISION_LLM, VDISPLAY_VISION_LLM_TIMEOUT_S, VDISPLAY_VISION_LLM_ENABLED, VDISPLAY_CONTROL_FOCUS_MS, VDISPLAY_CONTROL_POINTER_SETTLE_MS, WAYLAND_DISPLAY, XDG_RUNTIME_DIR, DBUS_SESSION_BUS_ADDRESS, VDISPLAY_SCREENCAST_MULTIPLE, VDISPLAY_PIPEWIRE_CAPTURE_TIMEOUT_S, VDISPLAY_SCREENCAST_CURSOR, VDISPLAY_AGENT_FORCE_REMOTE, VDISPLAY_SESSION, VDISPLAY_SESSION_ID, VDISPLAY_AGENT_AUDIT_DELEGATE, VDISPLAY_EVENT_STORE, VDISPLAY_PROJECTIONS, VDISPLAY_REPLAY_DELAY_S, VDISPLAY_VQL, VDISPLAY_OBSERVE_CACHE, VDISPLAY_SESSION_BASE, VDISPLAY_OBSERVE, VDISPLAY_IMGL, VDISPLAY_IMGL_SKIP_BLANK, VDISPLAY_IMGL_LANG, YDOTOOL_SOCKET, VDISPLAY_ALLOW_YDOTOOL_TYPING, VDISPLAY_IMG2NL, VDISPLAY_IMG2NL_LOCALE, VDISPLAY_DESCRIBE_BACKEND, VDISPLAY_SCREENCAST_LOCAL_START_COOLDOWN_S, VDISPLAY_CONTROL_SETTLE_MS, XDG_CONFIG_HOME, VDISPLAY_EVENT_FORMAT, VDISPLAY_CAPTURE_ALLOW_PORTAL, PYTEST_CURRENT_TEST, VDISPLAY_ATSPI_TIMEOUT_S;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.10,<3.14;
  vars: LLM_MODEL, OPENROUTER_API_KEY;
  runtime_llm: OPENROUTER_API_KEY;
}
```

## Dependencies

### Runtime

*(see pyproject.toml)*

### Development

```text markpact:deps python scope=dev
pytest>=8.0
Pillow>=10.0
fastapi>=0.110
httpx>=0.27
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
dsl2vdisplay
vdisplay-agent
uvicorn>=0.27
pydantic>=2
sqlmodel>=0.0.22
```

## Call Graph

*444 nodes · 500 edges · 125 modules · CC̄=3.9*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `register_routes` *(in packages.vdisplay-agent.src.vdisplay_agent.routes.control)* | 1 | 0 | 68 | **68** |
| `print_json` *(in src.vdisplay.cli_handlers)* | 1 | 59 | 1 | **60** |
| `register` *(in src.vdisplay.commands.control)* | 1 | 0 | 46 | **46** |
| `pick_flag` *(in packages.dsl2vdisplay.src.dsl2vdisplay.grammar)* | 3 | 44 | 2 | **46** |
| `handle` *(in src.vdisplay.commands.ide)* | 8 | 0 | 45 | **45** |
| `start_sampler` *(in packages.vdisplay-agent.src.vdisplay_agent.services.sampler)* | 7 | 0 | 42 | **42** |
| `dispatch` *(in packages.dsl2vdisplay.src.dsl2vdisplay.bus)* | 14 ⚠ | 14 | 27 | **41** |
| `create_app` *(in packages.rest2vdisplay.src.rest2vdisplay.app)* | 2 | 3 | 38 | **41** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/vdisplay
# generated in 0.24s
# nodes: 444 | edges: 500 | modules: 125
# CC̄=3.9

HUBS[20]:
  packages.vdisplay-agent.src.vdisplay_agent.routes.control.register_routes
    CC=1  in:0  out:68  total:68
  src.vdisplay.cli_handlers.print_json
    CC=1  in:59  out:1  total:60
  src.vdisplay.commands.control.register
    CC=1  in:0  out:46  total:46
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
    CC=3  in:44  out:2  total:46
  src.vdisplay.commands.ide.handle
    CC=8  in:0  out:45  total:45
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler.start_sampler
    CC=7  in:0  out:42  total:42
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=14  in:14  out:27  total:41
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  src.vdisplay.application.executor.execute
    CC=15  in:8  out:30  total:38
  src.vdisplay.discovery.resolve_host_display
    CC=11  in:31  out:7  total:38
  src.vdisplay.utils.run_command
    CC=2  in:33  out:4  total:37
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  examples.agent-broker.broker_demo.main
    CC=9  in:0  out:35  total:35
  src.vdisplay.application.session_recorder.load_session_document
    CC=13  in:4  out:29  total:33
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  packages.vdisplay-agent.src.vdisplay_agent.routes.health.register_routes
    CC=1  in:0  out:33  total:33
  src.vdisplay.application.session_recorder_diagnostics.extract_diagnostics
    CC=13  in:5  out:28  total:33
  src.vdisplay.commands.session.command_request_from_control_args
    CC=8  in:1  out:32  total:33
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:32  total:32
  examples.control-plane.control_demo.run_browser_demo
    CC=6  in:1  out:30  total:31

MODULES:
  examples.agent-broker.broker_demo  [1 funcs]
    main  CC=9  out:35
  examples.common.host_capture  [1 funcs]
    capture_host_screenshot  CC=1  out:2
  examples.common.screenshot_meta  [9 funcs]
    build_screenshot_meta  CC=6  out:10
    describe_screenshot_nl  CC=14  out:15
    ensure_common_on_path  CC=2  out:4
    examples_common_dir  CC=2  out:4
    meta_path_for  CC=1  out:2
    png_dimensions  CC=5  out:10
    print_artifact  CC=1  out:2
    save_png_with_meta  CC=2  out:6
    write_screenshot_meta  CC=1  out:4
  examples.common.validate_artifacts  [3 funcs]
    main  CC=6  out:8
    validate_directory  CC=3  out:4
    validate_image_and_meta  CC=12  out:22
  examples.control-plane.control_demo  [5 funcs]
    main  CC=1  out:8
    run_browser_demo  CC=6  out:30
    run_diagnostics  CC=1  out:5
    run_terminal_demo  CC=6  out:26
    show_active_controls  CC=6  out:21
  examples.control-plugin-ax.src.vdisplay_example_ax_plugin  [1 funcs]
    register_plugin  CC=1  out:1
  examples.control-plugin-ax.src.vdisplay_example_ax_plugin.provider  [4 funcs]
    __init__  CC=3  out:4
    _demo_backend  CC=1  out:1
    _use_mock_backend  CC=2  out:3
    build_example_ax  CC=3  out:3
  examples.control-plugin-uia.src.vdisplay_example_uia_plugin  [1 funcs]
    register_plugin  CC=1  out:1
  examples.control-plugin-uia.src.vdisplay_example_uia_plugin.provider  [4 funcs]
    __init__  CC=3  out:4
    _demo_backend  CC=1  out:1
    _use_mock_backend  CC=2  out:3
    build_example_uia  CC=3  out:3
  examples.control-plugin.src.vdisplay_example_plugin  [1 funcs]
    register_plugin  CC=1  out:1
  examples.host-mirror.mirror_demo  [1 funcs]
    main  CC=7  out:31
  examples.host-relay.relay_demo  [2 funcs]
    _capture_phase  CC=1  out:6
    main  CC=11  out:33
  packages.cli2vdisplay.src.cli2vdisplay.cli  [1 funcs]
    main  CC=7  out:16
  packages.dsl2vdisplay.src.dsl2vdisplay.bus  [3 funcs]
    _dispatch_legacy  CC=3  out:13
    dispatch  CC=14  out:27
    execute_dsl_line  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.cli  [3 funcs]
    _main_legacy  CC=10  out:17
    _main_subcommand  CC=9  out:19
    main  CC=4  out:3
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar  [23 funcs]
    _has_flag  CC=1  out:0
    _parse_adopt  CC=6  out:5
    _parse_browser_open  CC=11  out:10
    _parse_control_click  CC=1  out:1
    _parse_control_common  CC=9  out:12
    _parse_control_focus  CC=1  out:1
    _parse_control_set_value  CC=2  out:2
    _parse_controls_find  CC=1  out:1
    _parse_controls_list  CC=3  out:4
    _parse_diagnose_control  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command  [7 funcs]
    _err  CC=2  out:1
    _ok  CC=1  out:2
    handle_adopt  CC=3  out:13
    handle_mirror  CC=3  out:13
    handle_release  CC=3  out:12
    handle_screenshot  CC=2  out:10
    handle_virtual_start  CC=2  out:10
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query  [3 funcs]
    handle_monitors  CC=1  out:6
    handle_outputs  CC=1  out:1
    handle_windows  CC=1  out:9
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry  [4 funcs]
    _load_schema  CC=1  out:4
    all_schemas  CC=3  out:2
    schema_for_verb  CC=1  out:3
    validate_command_dict  CC=3  out:6
  packages.mcp2vdisplay.src.mcp2vdisplay.cli  [2 funcs]
    create_server  CC=1  out:1
    main  CC=2  out:6
  packages.mcp2vdisplay.src.mcp2vdisplay.server  [1 funcs]
    create_server  CC=1  out:32
  packages.rest2vdisplay.src.rest2vdisplay.app  [1 funcs]
    create_app  CC=2  out:38
  packages.uri2vdisplay.src.uri2vdisplay.cli  [1 funcs]
    main  CC=4  out:13
  packages.uri2vdisplay.src.uri2vdisplay.decode  [1 funcs]
    uri_to_dsl  CC=7  out:12
  packages.vdisplay-agent.src.vdisplay_agent.audit_context  [3 funcs]
    apply_audit_env  CC=7  out:6
    audit_context_from_fastapi_headers  CC=1  out:1
    audit_context_from_headers  CC=1  out:1
  packages.vdisplay-agent.src.vdisplay_agent.broker_events  [2 funcs]
    _broker_log_path  CC=4  out:8
    log_broker_event  CC=3  out:7
  packages.vdisplay-agent.src.vdisplay_agent.cli  [1 funcs]
    main  CC=6  out:22
  packages.vdisplay-agent.src.vdisplay_agent.envelope  [7 funcs]
    agent_meta  CC=1  out:0
    failure  CC=3  out:2
    from_runtime  CC=3  out:8
    json_error  CC=7  out:12
    json_from_runtime  CC=1  out:2
    json_success  CC=1  out:2
    success  CC=2  out:1
  packages.vdisplay-agent.src.vdisplay_agent.routes  [1 funcs]
    register_all_routes  CC=2  out:3
  packages.vdisplay-agent.src.vdisplay_agent.routes._audit_execute  [3 funcs]
    _json_from_command_result  CC=8  out:6
    execute_audit_route  CC=5  out:16
    execute_audited_service  CC=5  out:17
  packages.vdisplay-agent.src.vdisplay_agent.routes._audit_headers  [1 funcs]
    read_audit_headers  CC=1  out:5
  packages.vdisplay-agent.src.vdisplay_agent.routes.auth  [2 funcs]
    expected_token  CC=2  out:2
    make_check_auth  CC=1  out:5
  packages.vdisplay-agent.src.vdisplay_agent.routes.capture  [1 funcs]
    register_routes  CC=1  out:5
  packages.vdisplay-agent.src.vdisplay_agent.routes.control  [1 funcs]
    register_routes  CC=1  out:68
  packages.vdisplay-agent.src.vdisplay_agent.routes.health  [1 funcs]
    register_routes  CC=1  out:33
  packages.vdisplay-agent.src.vdisplay_agent.routes.sampler  [1 funcs]
    register_routes  CC=1  out:18
  packages.vdisplay-agent.src.vdisplay_agent.routes.tasks  [1 funcs]
    register_routes  CC=1  out:27
  packages.vdisplay-agent.src.vdisplay_agent.routes.windows  [1 funcs]
    register_routes  CC=1  out:10
  packages.vdisplay-agent.src.vdisplay_agent.serve_port  [11 funcs]
    _cmdline  CC=2  out:5
    _is_vdisplay_agent_pid  CC=2  out:2
    _parse_ss_pids  CC=2  out:4
    _partition_listener_pids  CC=4  out:6
    _pid_alive  CC=3  out:1
    _pids_from_lsof  CC=5  out:6
    _pids_from_ss  CC=3  out:2
    _probe_is_vdisplay_agent  CC=6  out:11
    ensure_broker_port_free  CC=10  out:13
    find_listener_pids  CC=4  out:4
  packages.vdisplay-agent.src.vdisplay_agent.server  [1 funcs]
    create_app  CC=4  out:10
  packages.vdisplay-agent.src.vdisplay_agent.services.capabilities  [2 funcs]
    diagnostics  CC=4  out:10
    platform_capabilities  CC=6  out:18
  packages.vdisplay-agent.src.vdisplay_agent.services.capture  [5 funcs]
    _capture_all_monitors  CC=2  out:8
    _capture_host  CC=11  out:23
    _capture_session  CC=3  out:13
    _region_from_body  CC=8  out:13
    capture_frame  CC=3  out:6
  packages.vdisplay-agent.src.vdisplay_agent.services.control  [7 funcs]
    _run_on_browser_thread  CC=1  out:2
    _selector_kwargs  CC=1  out:23
    find_controls  CC=2  out:10
    focus_control  CC=2  out:9
    invoke_control  CC=2  out:11
    list_controls  CC=4  out:11
    set_control_value  CC=3  out:13
  packages.vdisplay-agent.src.vdisplay_agent.services.outputs  [1 funcs]
    list_outputs_payload  CC=2  out:4
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler  [5 funcs]
    _capture_virtual_persistent  CC=5  out:12
    _config_from_body  CC=12  out:26
    _ensure_virtual_session  CC=4  out:5
    _recover_screencast  CC=3  out:1
    start_sampler  CC=7  out:42
  packages.vdisplay-agent.src.vdisplay_agent.services.screencast_recovery  [3 funcs]
    _mark_recovery_attempt  CC=1  out:1
    screencast_recovery_cooldown_remaining  CC=1  out:2
    try_recover_screencast  CC=8  out:5
  packages.vdisplay-agent.src.vdisplay_agent.services.sessions  [15 funcs]
    _release_store_screencast_if_different  CC=9  out:6
    _screencast_payload  CC=6  out:2
    _session_started  CC=1  out:2
    adopt_screencast  CC=7  out:11
    list_sessions  CC=1  out:2
    screencast_status  CC=3  out:2
    shutdown  CC=4  out:8
    start_browser  CC=3  out:4
    start_mirror  CC=3  out:5
    start_relay  CC=4  out:5
  packages.vdisplay-agent.src.vdisplay_agent.services.tasks  [9 funcs]
    end_sampler_task  CC=1  out:1
    end_screencast_task  CC=1  out:1
    get_task  CC=2  out:3
    heartbeat_task  CC=2  out:3
    list_tasks  CC=3  out:4
    register_session_task  CC=4  out:10
    shutdown_tasks  CC=5  out:7
    stop_task  CC=5  out:5
    unregister_session_task  CC=1  out:1
  packages.vdisplay-agent.src.vdisplay_agent.services.web_console  [1 funcs]
    click_monitor_pointer  CC=1  out:2
  packages.vdisplay-agent.src.vdisplay_agent.services.web_frame_cache  [9 funcs]
    _capture_bulk_or_fallback  CC=9  out:13
    _get_cached_all_frames  CC=4  out:6
    _persist_captures_to_cache  CC=9  out:18
    _require_screencast  CC=3  out:1
    cache_get  CC=4  out:3
    cache_put  CC=1  out:1
    capture_all_monitor_frames  CC=4  out:4
    capture_monitor_frame  CC=1  out:1
    capture_monitor_frame_with_meta  CC=9  out:18
  packages.vdisplay-agent.src.vdisplay_agent.services.web_replay  [2 funcs]
    list_replay_sessions  CC=9  out:21
    queue_replay  CC=4  out:3
  packages.vdisplay-agent.src.vdisplay_agent.session_store  [1 funcs]
    register  CC=1  out:2
  packages.vdisplay-agent.src.vdisplay_agent.task_store  [7 funcs]
    __init__  CC=2  out:5
    create_task  CC=3  out:9
    mark_orphan_running_as_stale  CC=3  out:8
    update_task  CC=7  out:9
    _utcnow  CC=1  out:1
    default_task_db_path  CC=3  out:9
    task_to_dict  CC=4  out:5
  src.vdisplay.agent_config  [9 funcs]
    _default_agent_base  CC=3  out:4
    _is_vdisplay_agent_health  CC=6  out:9
    _probe_agent_url  CC=5  out:7
    _probe_default_agent  CC=3  out:3
    agent_auto_enabled  CC=1  out:3
    reset_agent_probe_cache  CC=1  out:0
    resolve_agent_token  CC=3  out:2
    resolve_agent_url  CC=6  out:5
    use_agent  CC=2  out:4
  src.vdisplay.agent_dispatch  [2 funcs]
    agent_client  CC=2  out:3
    dispatch_via_agent  CC=1  out:4
  src.vdisplay.agent_envelope  [1 funcs]
    flatten_agent_envelope  CC=6  out:3
  src.vdisplay.api  [7 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.application.auto.runner  [3 funcs]
    list_auto_tasks  CC=3  out:6
    run_auto_loop  CC=11  out:20
    run_auto_once  CC=6  out:12
  src.vdisplay.application.auto.tasks  [1 funcs]
    ensure_auto_dependencies  CC=5  out:4
  src.vdisplay.application.errors  [1 funcs]
    error_from_exception  CC=4  out:11
  src.vdisplay.application.executor  [1 funcs]
    execute  CC=15  out:30
  src.vdisplay.application.handlers.control  [1 funcs]
    control_request_body  CC=3  out:3
  src.vdisplay.application.replay  [1 funcs]
    queue_session_replay  CC=4  out:10
  src.vdisplay.application.services.capture  [1 funcs]
    capture_screenshot  CC=3  out:3
  src.vdisplay.application.services.sampler  [2 funcs]
    run_sampler  CC=5  out:18
    start_sampler_via_agent  CC=1  out:1
  src.vdisplay.application.services.web_pointer  [1 funcs]
    pointer_click_at_monitor  CC=11  out:20
  src.vdisplay.application.session_context  [4 funcs]
    apply_cli_session_args  CC=3  out:6
    audit_context_from_mapping  CC=3  out:12
    current_audit_headers  CC=2  out:2
    enrich_command_request  CC=6  out:5
  src.vdisplay.application.session_recorder  [6 funcs]
    discover_session_dirs  CC=6  out:7
    export_session_zip  CC=4  out:10
    load_session_document  CC=13  out:29
    record_execution  CC=5  out:4
    reprocess_session_diagnostics  CC=3  out:12
    session_recording_enabled  CC=2  out:5
  src.vdisplay.application.session_recorder_diagnostics  [1 funcs]
    extract_diagnostics  CC=13  out:28
  src.vdisplay.application.session_recorder_readme  [1 funcs]
    render_readme  CC=3  out:8
  src.vdisplay.backends.base  [1 funcs]
    save_screenshot  CC=1  out:3
  src.vdisplay.backends.linux_x11_mirror  [14 funcs]
    __init__  CC=1  out:4
    screenshot_bytes  CC=2  out:3
    start  CC=5  out:10
    stop  CC=5  out:3
    _list_connected_outputs  CC=3  out:5
    _mirror_exhausted_error  CC=5  out:3
    _mirror_target_candidates  CC=7  out:1
    _output_capture_region  CC=5  out:10
    _output_mode  CC=7  out:6
    _primary_output_from_xrandr  CC=3  out:4
  src.vdisplay.backends.linux_x11_relay  [18 funcs]
    __init__  CC=1  out:3
    adopt_window  CC=12  out:27
    list_adopted  CC=4  out:4
    release_window  CC=6  out:10
    start  CC=2  out:3
    _find_window_id  CC=12  out:11
    _load_stash  CC=5  out:8
    _move_window  CC=1  out:3
    _pick_primary_release_id  CC=4  out:1
    _related_adopted_ids  CC=7  out:8
  src.vdisplay.backends.linux_xvfb  [6 funcs]
    _acquire_display  CC=8  out:14
    screenshot_bytes  CC=2  out:2
    start  CC=4  out:6
    _display_candidates  CC=4  out:4
    _probe_display  CC=2  out:2
    _wait_for_display  CC=7  out:10
  src.vdisplay.capture.host  [2 funcs]
    capture_all_monitors  CC=8  out:12
    capture_host_to_file  CC=3  out:10
  src.vdisplay.capture.linux_xwd  [2 funcs]
    _capture_xwd_png  CC=1  out:3
    capture_display_png  CC=2  out:2
  src.vdisplay.capture.portal_screencast  [9 funcs]
    _screencast_multiple  CC=3  out:3
    _set_active  CC=1  out:0
    _set_active_if_self  CC=1  out:0
    ensure_portal_session_env  CC=11  out:10
    get_active_screencast  CC=1  out:0
    portal_session_env_status  CC=5  out:5
    prepare_portal_screencast_start  CC=1  out:2
    start_screencast_session  CC=5  out:8
    stop_screencast_session  CC=2  out:2
  src.vdisplay.capture.providers.engine  [1 funcs]
    list_capture_providers  CC=4  out:6
  src.vdisplay.cli  [2 funcs]
    build_parser  CC=1  out:4
    main  CC=2  out:5
  src.vdisplay.cli_handlers  [1 funcs]
    print_json  CC=1  out:1
  src.vdisplay.client  [1 funcs]
    request  CC=3  out:8
  src.vdisplay.client_http  [3 funcs]
    __init__  CC=2  out:2
    build_request  CC=3  out:5
    normalize_payload  CC=1  out:1
  src.vdisplay.client_routes  [6 funcs]
    _route_browser_open  CC=4  out:0
    _route_control_command  CC=5  out:0
    _route_outputs_query  CC=4  out:3
    _route_terminal_open  CC=4  out:0
    _route_windows_query  CC=6  out:4
    route_command  CC=7  out:7
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.all_cmd  [4 funcs]
    handle  CC=1  out:3
    handle_outputs  CC=1  out:3
    register  CC=1  out:4
    register_outputs  CC=1  out:4
  src.vdisplay.commands.app  [1 funcs]
    handle  CC=6  out:17
  src.vdisplay.commands.auto  [1 funcs]
    handle  CC=8  out:18
  src.vdisplay.commands.common  [9 funcs]
    add_all_arg  CC=1  out:1
    add_control_selector_args  CC=1  out:21
    add_display_arg  CC=1  out:1
    add_map_args  CC=1  out:3
    add_preview_args  CC=1  out:3
    add_window_filter_args  CC=1  out:7
    control_selector_kwargs_for_service  CC=1  out:2
    control_selector_kwargs_from_args  CC=1  out:24
    include_all_from_args  CC=2  out:3
  src.vdisplay.commands.control  [9 funcs]
    _add_selector_args  CC=1  out:2
    _handle_browser_open  CC=5  out:8
    _handle_control_click  CC=1  out:1
    _handle_control_find  CC=1  out:1
    _handle_control_focus  CC=1  out:1
    _handle_control_list  CC=4  out:6
    _handle_control_set_value  CC=1  out:1
    _run_control  CC=5  out:6
    register  CC=1  out:46
  src.vdisplay.commands.diagnose  [2 funcs]
    handle  CC=5  out:13
    register  CC=1  out:8
  src.vdisplay.commands.hmi  [1 funcs]
    handle  CC=7  out:6
  src.vdisplay.commands.ide  [2 funcs]
    handle  CC=8  out:45
    register  CC=1  out:17
  src.vdisplay.commands.info  [1 funcs]
    handle  CC=1  out:2
  src.vdisplay.commands.map  [1 funcs]
    handle  CC=7  out:31
  src.vdisplay.commands.mirror  [1 funcs]
    handle  CC=3  out:5
  src.vdisplay.commands.monitors  [2 funcs]
    handle  CC=1  out:3
    register  CC=1  out:4
  src.vdisplay.commands.nlp  [1 funcs]
    handle  CC=2  out:4
  src.vdisplay.commands.observe  [1 funcs]
    handle_observe  CC=9  out:25
  src.vdisplay.commands.relay  [2 funcs]
    handle  CC=5  out:9
    handle_list_windows  CC=1  out:2
  src.vdisplay.commands.sampler  [8 funcs]
    _config_from_args  CC=1  out:1
    _handle_start  CC=4  out:6
    _handle_status  CC=2  out:4
    _handle_stop  CC=2  out:4
    _start_agent  CC=2  out:4
    _wait_for_sampler  CC=9  out:12
    handle  CC=3  out:4
    register  CC=1  out:22
  src.vdisplay.commands.screenshot  [2 funcs]
    handle  CC=1  out:2
    register  CC=1  out:14
  src.vdisplay.commands.session  [7 funcs]
    _resolve_session_dir  CC=9  out:21
    add_root_session_args  CC=1  out:2
    command_request_from_control_args  CC=8  out:32
    handle_export  CC=3  out:12
    handle_list  CC=3  out:14
    handle_reprocess  CC=2  out:4
    handle_show  CC=10  out:21
  src.vdisplay.commands.virtual  [1 funcs]
    handle  CC=6  out:9
  src.vdisplay.commands.windows  [2 funcs]
    handle  CC=1  out:3
    register  CC=1  out:4
  src.vdisplay.control.gui_map  [1 funcs]
    load_gui_map  CC=2  out:6
  src.vdisplay.control.gui_map_resolve  [1 funcs]
    map_element_to_node  CC=5  out:7
  src.vdisplay.control.plugins  [1 funcs]
    register_control_provider  CC=1  out:2
  src.vdisplay.control.policy  [1 funcs]
    assess_control_capability  CC=7  out:9
  src.vdisplay.control.providers.browser_session  [1 funcs]
    open  CC=1  out:1
  src.vdisplay.control.providers.browser_sync_executor  [1 funcs]
    run_browser_sync  CC=2  out:6
  src.vdisplay.control.providers.terminal_session  [1 funcs]
    default_registry  CC=1  out:0
  src.vdisplay.control.registry  [1 funcs]
    build  CC=3  out:6
  src.vdisplay.control.session  [2 funcs]
    build_catalog_from_agent_store  CC=11  out:17
    parse_session_kind  CC=3  out:5
  src.vdisplay.desktop_apps  [20 funcs]
    _binary_launch  CC=3  out:2
    _build_registry  CC=8  out:20
    _default_map_candidates  CC=5  out:18
    _desktop_launch  CC=2  out:2
    _expand_variants  CC=3  out:4
    _is_gui_map_file  CC=6  out:8
    _variants_for  CC=9  out:11
    _xwayland_variant  CC=1  out:3
    chat_selectors_for  CC=2  out:1
    get_desktop_app  CC=3  out:6
  src.vdisplay.discovery  [13 funcs]
    _attach_output_nl  CC=2  out:3
    _display_hint  CC=3  out:2
    _display_socket_exists  CC=2  out:5
    _list_monitors  CC=6  out:10
    _looks_like_xvfb_only  CC=4  out:4
    _merge_output_metadata  CC=4  out:22
    _parse_xrandr_query  CC=8  out:12
    diagnose_display  CC=10  out:19
    find_window_suggestions  CC=2  out:2
    list_monitors  CC=1  out:1
  src.vdisplay.hmi.pointer_probes  [2 funcs]
    is_wayland_session  CC=2  out:5
    probe_all_sources  CC=8  out:12
  src.vdisplay.hmi.watch  [1 funcs]
    run_hmi_watch  CC=6  out:8
  src.vdisplay.ide_prompt  [16 funcs]
    _build_map_missing_result  CC=2  out:2
    _build_no_selector_result  CC=10  out:7
    _build_write_kwargs  CC=9  out:10
    _find_first_selector  CC=11  out:10
    _find_map_target  CC=4  out:8
    _handle_focus_window  CC=2  out:3
    _handle_submit  CC=11  out:19
    _handle_wait_window  CC=9  out:10
    _ide_find_timeout_seconds  CC=2  out:3
    _is_wayland_session  CC=1  out:1
  src.vdisplay.integrations.pipeline  [1 funcs]
    observe_screen  CC=22  out:28
  src.vdisplay.integrations.vql_bridge  [1 funcs]
    reverse_generation_descriptor  CC=9  out:13
  src.vdisplay.nl  [8 funcs]
    _user_visible_app_labels  CC=9  out:9
    assign_windows_to_monitors  CC=3  out:6
    describe_output_nl  CC=13  out:13
    describe_window_nl  CC=14  out:16
    enrich_outputs_nl  CC=4  out:2
    ensure_monitor_ids  CC=5  out:6
    find_monitor_for_window  CC=3  out:1
    window_center_on_output  CC=3  out:18
  src.vdisplay.nlp  [10 funcs]
    _default_all  CC=1  out:1
    _default_display_suffix  CC=2  out:1
    _default_monitors  CC=1  out:1
    _default_windows  CC=1  out:1
    _display_suffix  CC=2  out:0
    _run_local_dsl  CC=7  out:7
    _validate_dsl  CC=1  out:2
    nl_to_dsl  CC=4  out:6
    parse_display  CC=10  out:6
    run_nl_prompt  CC=5  out:7
  src.vdisplay.payloads  [1 funcs]
    all_payload  CC=1  out:1
  src.vdisplay.utils  [2 funcs]
    run_command  CC=2  out:4
    run_command_bytes  CC=1  out:1
  src.vdisplay.windows.query  [3 funcs]
    find_companion_frames  CC=8  out:10
    find_windows  CC=6  out:5
    list_windows_enriched  CC=2  out:5

EDGES:
  packages.mcp2vdisplay.src.mcp2vdisplay.cli.main → packages.mcp2vdisplay.src.mcp2vdisplay.cli.create_server
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server → src.vdisplay.agent_config.resolve_agent_url
  packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_legacy → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_legacy
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.dsl2vdisplay.src.dsl2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy
  packages.dsl2vdisplay.src.dsl2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy → src.vdisplay.control.providers.browser_session.BrowserSessionRegistry.open
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry._load_schema
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.resolve_verb → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.normalize_tokens
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_windows → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_windows → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_screenshot → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_virtual_start → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_launch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_mirror → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_adopt → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._has_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_controls_list → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_controls_list → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_controls_find → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_click → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_focus → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_set_value → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_set_value → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_diagnose_control → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_browser_open → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_terminal_open → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_release → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.split_command
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.resolve_verb
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_screenshot → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_screenshot → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_virtual_start → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_virtual_start → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror → src.vdisplay.discovery.resolve_host_display
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror → src.vdisplay.discovery.list_outputs
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_adopt → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_adopt → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/vdisplay
# generated in 0.24s
# nodes: 444 | edges: 500 | modules: 125
# CC̄=3.9

HUBS[20]:
  packages.vdisplay-agent.src.vdisplay_agent.routes.control.register_routes
    CC=1  in:0  out:68  total:68
  src.vdisplay.cli_handlers.print_json
    CC=1  in:59  out:1  total:60
  src.vdisplay.commands.control.register
    CC=1  in:0  out:46  total:46
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
    CC=3  in:44  out:2  total:46
  src.vdisplay.commands.ide.handle
    CC=8  in:0  out:45  total:45
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler.start_sampler
    CC=7  in:0  out:42  total:42
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=14  in:14  out:27  total:41
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  src.vdisplay.application.executor.execute
    CC=15  in:8  out:30  total:38
  src.vdisplay.discovery.resolve_host_display
    CC=11  in:31  out:7  total:38
  src.vdisplay.utils.run_command
    CC=2  in:33  out:4  total:37
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  examples.agent-broker.broker_demo.main
    CC=9  in:0  out:35  total:35
  src.vdisplay.application.session_recorder.load_session_document
    CC=13  in:4  out:29  total:33
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  packages.vdisplay-agent.src.vdisplay_agent.routes.health.register_routes
    CC=1  in:0  out:33  total:33
  src.vdisplay.application.session_recorder_diagnostics.extract_diagnostics
    CC=13  in:5  out:28  total:33
  src.vdisplay.commands.session.command_request_from_control_args
    CC=8  in:1  out:32  total:33
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:32  total:32
  examples.control-plane.control_demo.run_browser_demo
    CC=6  in:1  out:30  total:31

MODULES:
  examples.agent-broker.broker_demo  [1 funcs]
    main  CC=9  out:35
  examples.common.host_capture  [1 funcs]
    capture_host_screenshot  CC=1  out:2
  examples.common.screenshot_meta  [9 funcs]
    build_screenshot_meta  CC=6  out:10
    describe_screenshot_nl  CC=14  out:15
    ensure_common_on_path  CC=2  out:4
    examples_common_dir  CC=2  out:4
    meta_path_for  CC=1  out:2
    png_dimensions  CC=5  out:10
    print_artifact  CC=1  out:2
    save_png_with_meta  CC=2  out:6
    write_screenshot_meta  CC=1  out:4
  examples.common.validate_artifacts  [3 funcs]
    main  CC=6  out:8
    validate_directory  CC=3  out:4
    validate_image_and_meta  CC=12  out:22
  examples.control-plane.control_demo  [5 funcs]
    main  CC=1  out:8
    run_browser_demo  CC=6  out:30
    run_diagnostics  CC=1  out:5
    run_terminal_demo  CC=6  out:26
    show_active_controls  CC=6  out:21
  examples.control-plugin-ax.src.vdisplay_example_ax_plugin  [1 funcs]
    register_plugin  CC=1  out:1
  examples.control-plugin-ax.src.vdisplay_example_ax_plugin.provider  [4 funcs]
    __init__  CC=3  out:4
    _demo_backend  CC=1  out:1
    _use_mock_backend  CC=2  out:3
    build_example_ax  CC=3  out:3
  examples.control-plugin-uia.src.vdisplay_example_uia_plugin  [1 funcs]
    register_plugin  CC=1  out:1
  examples.control-plugin-uia.src.vdisplay_example_uia_plugin.provider  [4 funcs]
    __init__  CC=3  out:4
    _demo_backend  CC=1  out:1
    _use_mock_backend  CC=2  out:3
    build_example_uia  CC=3  out:3
  examples.control-plugin.src.vdisplay_example_plugin  [1 funcs]
    register_plugin  CC=1  out:1
  examples.host-mirror.mirror_demo  [1 funcs]
    main  CC=7  out:31
  examples.host-relay.relay_demo  [2 funcs]
    _capture_phase  CC=1  out:6
    main  CC=11  out:33
  packages.cli2vdisplay.src.cli2vdisplay.cli  [1 funcs]
    main  CC=7  out:16
  packages.dsl2vdisplay.src.dsl2vdisplay.bus  [3 funcs]
    _dispatch_legacy  CC=3  out:13
    dispatch  CC=14  out:27
    execute_dsl_line  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.cli  [3 funcs]
    _main_legacy  CC=10  out:17
    _main_subcommand  CC=9  out:19
    main  CC=4  out:3
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar  [23 funcs]
    _has_flag  CC=1  out:0
    _parse_adopt  CC=6  out:5
    _parse_browser_open  CC=11  out:10
    _parse_control_click  CC=1  out:1
    _parse_control_common  CC=9  out:12
    _parse_control_focus  CC=1  out:1
    _parse_control_set_value  CC=2  out:2
    _parse_controls_find  CC=1  out:1
    _parse_controls_list  CC=3  out:4
    _parse_diagnose_control  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command  [7 funcs]
    _err  CC=2  out:1
    _ok  CC=1  out:2
    handle_adopt  CC=3  out:13
    handle_mirror  CC=3  out:13
    handle_release  CC=3  out:12
    handle_screenshot  CC=2  out:10
    handle_virtual_start  CC=2  out:10
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query  [3 funcs]
    handle_monitors  CC=1  out:6
    handle_outputs  CC=1  out:1
    handle_windows  CC=1  out:9
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry  [4 funcs]
    _load_schema  CC=1  out:4
    all_schemas  CC=3  out:2
    schema_for_verb  CC=1  out:3
    validate_command_dict  CC=3  out:6
  packages.mcp2vdisplay.src.mcp2vdisplay.cli  [2 funcs]
    create_server  CC=1  out:1
    main  CC=2  out:6
  packages.mcp2vdisplay.src.mcp2vdisplay.server  [1 funcs]
    create_server  CC=1  out:32
  packages.rest2vdisplay.src.rest2vdisplay.app  [1 funcs]
    create_app  CC=2  out:38
  packages.uri2vdisplay.src.uri2vdisplay.cli  [1 funcs]
    main  CC=4  out:13
  packages.uri2vdisplay.src.uri2vdisplay.decode  [1 funcs]
    uri_to_dsl  CC=7  out:12
  packages.vdisplay-agent.src.vdisplay_agent.audit_context  [3 funcs]
    apply_audit_env  CC=7  out:6
    audit_context_from_fastapi_headers  CC=1  out:1
    audit_context_from_headers  CC=1  out:1
  packages.vdisplay-agent.src.vdisplay_agent.broker_events  [2 funcs]
    _broker_log_path  CC=4  out:8
    log_broker_event  CC=3  out:7
  packages.vdisplay-agent.src.vdisplay_agent.cli  [1 funcs]
    main  CC=6  out:22
  packages.vdisplay-agent.src.vdisplay_agent.envelope  [7 funcs]
    agent_meta  CC=1  out:0
    failure  CC=3  out:2
    from_runtime  CC=3  out:8
    json_error  CC=7  out:12
    json_from_runtime  CC=1  out:2
    json_success  CC=1  out:2
    success  CC=2  out:1
  packages.vdisplay-agent.src.vdisplay_agent.routes  [1 funcs]
    register_all_routes  CC=2  out:3
  packages.vdisplay-agent.src.vdisplay_agent.routes._audit_execute  [3 funcs]
    _json_from_command_result  CC=8  out:6
    execute_audit_route  CC=5  out:16
    execute_audited_service  CC=5  out:17
  packages.vdisplay-agent.src.vdisplay_agent.routes._audit_headers  [1 funcs]
    read_audit_headers  CC=1  out:5
  packages.vdisplay-agent.src.vdisplay_agent.routes.auth  [2 funcs]
    expected_token  CC=2  out:2
    make_check_auth  CC=1  out:5
  packages.vdisplay-agent.src.vdisplay_agent.routes.capture  [1 funcs]
    register_routes  CC=1  out:5
  packages.vdisplay-agent.src.vdisplay_agent.routes.control  [1 funcs]
    register_routes  CC=1  out:68
  packages.vdisplay-agent.src.vdisplay_agent.routes.health  [1 funcs]
    register_routes  CC=1  out:33
  packages.vdisplay-agent.src.vdisplay_agent.routes.sampler  [1 funcs]
    register_routes  CC=1  out:18
  packages.vdisplay-agent.src.vdisplay_agent.routes.tasks  [1 funcs]
    register_routes  CC=1  out:27
  packages.vdisplay-agent.src.vdisplay_agent.routes.windows  [1 funcs]
    register_routes  CC=1  out:10
  packages.vdisplay-agent.src.vdisplay_agent.serve_port  [11 funcs]
    _cmdline  CC=2  out:5
    _is_vdisplay_agent_pid  CC=2  out:2
    _parse_ss_pids  CC=2  out:4
    _partition_listener_pids  CC=4  out:6
    _pid_alive  CC=3  out:1
    _pids_from_lsof  CC=5  out:6
    _pids_from_ss  CC=3  out:2
    _probe_is_vdisplay_agent  CC=6  out:11
    ensure_broker_port_free  CC=10  out:13
    find_listener_pids  CC=4  out:4
  packages.vdisplay-agent.src.vdisplay_agent.server  [1 funcs]
    create_app  CC=4  out:10
  packages.vdisplay-agent.src.vdisplay_agent.services.capabilities  [2 funcs]
    diagnostics  CC=4  out:10
    platform_capabilities  CC=6  out:18
  packages.vdisplay-agent.src.vdisplay_agent.services.capture  [5 funcs]
    _capture_all_monitors  CC=2  out:8
    _capture_host  CC=11  out:23
    _capture_session  CC=3  out:13
    _region_from_body  CC=8  out:13
    capture_frame  CC=3  out:6
  packages.vdisplay-agent.src.vdisplay_agent.services.control  [7 funcs]
    _run_on_browser_thread  CC=1  out:2
    _selector_kwargs  CC=1  out:23
    find_controls  CC=2  out:10
    focus_control  CC=2  out:9
    invoke_control  CC=2  out:11
    list_controls  CC=4  out:11
    set_control_value  CC=3  out:13
  packages.vdisplay-agent.src.vdisplay_agent.services.outputs  [1 funcs]
    list_outputs_payload  CC=2  out:4
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler  [5 funcs]
    _capture_virtual_persistent  CC=5  out:12
    _config_from_body  CC=12  out:26
    _ensure_virtual_session  CC=4  out:5
    _recover_screencast  CC=3  out:1
    start_sampler  CC=7  out:42
  packages.vdisplay-agent.src.vdisplay_agent.services.screencast_recovery  [3 funcs]
    _mark_recovery_attempt  CC=1  out:1
    screencast_recovery_cooldown_remaining  CC=1  out:2
    try_recover_screencast  CC=8  out:5
  packages.vdisplay-agent.src.vdisplay_agent.services.sessions  [15 funcs]
    _release_store_screencast_if_different  CC=9  out:6
    _screencast_payload  CC=6  out:2
    _session_started  CC=1  out:2
    adopt_screencast  CC=7  out:11
    list_sessions  CC=1  out:2
    screencast_status  CC=3  out:2
    shutdown  CC=4  out:8
    start_browser  CC=3  out:4
    start_mirror  CC=3  out:5
    start_relay  CC=4  out:5
  packages.vdisplay-agent.src.vdisplay_agent.services.tasks  [9 funcs]
    end_sampler_task  CC=1  out:1
    end_screencast_task  CC=1  out:1
    get_task  CC=2  out:3
    heartbeat_task  CC=2  out:3
    list_tasks  CC=3  out:4
    register_session_task  CC=4  out:10
    shutdown_tasks  CC=5  out:7
    stop_task  CC=5  out:5
    unregister_session_task  CC=1  out:1
  packages.vdisplay-agent.src.vdisplay_agent.services.web_console  [1 funcs]
    click_monitor_pointer  CC=1  out:2
  packages.vdisplay-agent.src.vdisplay_agent.services.web_frame_cache  [9 funcs]
    _capture_bulk_or_fallback  CC=9  out:13
    _get_cached_all_frames  CC=4  out:6
    _persist_captures_to_cache  CC=9  out:18
    _require_screencast  CC=3  out:1
    cache_get  CC=4  out:3
    cache_put  CC=1  out:1
    capture_all_monitor_frames  CC=4  out:4
    capture_monitor_frame  CC=1  out:1
    capture_monitor_frame_with_meta  CC=9  out:18
  packages.vdisplay-agent.src.vdisplay_agent.services.web_replay  [2 funcs]
    list_replay_sessions  CC=9  out:21
    queue_replay  CC=4  out:3
  packages.vdisplay-agent.src.vdisplay_agent.session_store  [1 funcs]
    register  CC=1  out:2
  packages.vdisplay-agent.src.vdisplay_agent.task_store  [7 funcs]
    __init__  CC=2  out:5
    create_task  CC=3  out:9
    mark_orphan_running_as_stale  CC=3  out:8
    update_task  CC=7  out:9
    _utcnow  CC=1  out:1
    default_task_db_path  CC=3  out:9
    task_to_dict  CC=4  out:5
  src.vdisplay.agent_config  [9 funcs]
    _default_agent_base  CC=3  out:4
    _is_vdisplay_agent_health  CC=6  out:9
    _probe_agent_url  CC=5  out:7
    _probe_default_agent  CC=3  out:3
    agent_auto_enabled  CC=1  out:3
    reset_agent_probe_cache  CC=1  out:0
    resolve_agent_token  CC=3  out:2
    resolve_agent_url  CC=6  out:5
    use_agent  CC=2  out:4
  src.vdisplay.agent_dispatch  [2 funcs]
    agent_client  CC=2  out:3
    dispatch_via_agent  CC=1  out:4
  src.vdisplay.agent_envelope  [1 funcs]
    flatten_agent_envelope  CC=6  out:3
  src.vdisplay.api  [7 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.application.auto.runner  [3 funcs]
    list_auto_tasks  CC=3  out:6
    run_auto_loop  CC=11  out:20
    run_auto_once  CC=6  out:12
  src.vdisplay.application.auto.tasks  [1 funcs]
    ensure_auto_dependencies  CC=5  out:4
  src.vdisplay.application.errors  [1 funcs]
    error_from_exception  CC=4  out:11
  src.vdisplay.application.executor  [1 funcs]
    execute  CC=15  out:30
  src.vdisplay.application.handlers.control  [1 funcs]
    control_request_body  CC=3  out:3
  src.vdisplay.application.replay  [1 funcs]
    queue_session_replay  CC=4  out:10
  src.vdisplay.application.services.capture  [1 funcs]
    capture_screenshot  CC=3  out:3
  src.vdisplay.application.services.sampler  [2 funcs]
    run_sampler  CC=5  out:18
    start_sampler_via_agent  CC=1  out:1
  src.vdisplay.application.services.web_pointer  [1 funcs]
    pointer_click_at_monitor  CC=11  out:20
  src.vdisplay.application.session_context  [4 funcs]
    apply_cli_session_args  CC=3  out:6
    audit_context_from_mapping  CC=3  out:12
    current_audit_headers  CC=2  out:2
    enrich_command_request  CC=6  out:5
  src.vdisplay.application.session_recorder  [6 funcs]
    discover_session_dirs  CC=6  out:7
    export_session_zip  CC=4  out:10
    load_session_document  CC=13  out:29
    record_execution  CC=5  out:4
    reprocess_session_diagnostics  CC=3  out:12
    session_recording_enabled  CC=2  out:5
  src.vdisplay.application.session_recorder_diagnostics  [1 funcs]
    extract_diagnostics  CC=13  out:28
  src.vdisplay.application.session_recorder_readme  [1 funcs]
    render_readme  CC=3  out:8
  src.vdisplay.backends.base  [1 funcs]
    save_screenshot  CC=1  out:3
  src.vdisplay.backends.linux_x11_mirror  [14 funcs]
    __init__  CC=1  out:4
    screenshot_bytes  CC=2  out:3
    start  CC=5  out:10
    stop  CC=5  out:3
    _list_connected_outputs  CC=3  out:5
    _mirror_exhausted_error  CC=5  out:3
    _mirror_target_candidates  CC=7  out:1
    _output_capture_region  CC=5  out:10
    _output_mode  CC=7  out:6
    _primary_output_from_xrandr  CC=3  out:4
  src.vdisplay.backends.linux_x11_relay  [18 funcs]
    __init__  CC=1  out:3
    adopt_window  CC=12  out:27
    list_adopted  CC=4  out:4
    release_window  CC=6  out:10
    start  CC=2  out:3
    _find_window_id  CC=12  out:11
    _load_stash  CC=5  out:8
    _move_window  CC=1  out:3
    _pick_primary_release_id  CC=4  out:1
    _related_adopted_ids  CC=7  out:8
  src.vdisplay.backends.linux_xvfb  [6 funcs]
    _acquire_display  CC=8  out:14
    screenshot_bytes  CC=2  out:2
    start  CC=4  out:6
    _display_candidates  CC=4  out:4
    _probe_display  CC=2  out:2
    _wait_for_display  CC=7  out:10
  src.vdisplay.capture.host  [2 funcs]
    capture_all_monitors  CC=8  out:12
    capture_host_to_file  CC=3  out:10
  src.vdisplay.capture.linux_xwd  [2 funcs]
    _capture_xwd_png  CC=1  out:3
    capture_display_png  CC=2  out:2
  src.vdisplay.capture.portal_screencast  [9 funcs]
    _screencast_multiple  CC=3  out:3
    _set_active  CC=1  out:0
    _set_active_if_self  CC=1  out:0
    ensure_portal_session_env  CC=11  out:10
    get_active_screencast  CC=1  out:0
    portal_session_env_status  CC=5  out:5
    prepare_portal_screencast_start  CC=1  out:2
    start_screencast_session  CC=5  out:8
    stop_screencast_session  CC=2  out:2
  src.vdisplay.capture.providers.engine  [1 funcs]
    list_capture_providers  CC=4  out:6
  src.vdisplay.cli  [2 funcs]
    build_parser  CC=1  out:4
    main  CC=2  out:5
  src.vdisplay.cli_handlers  [1 funcs]
    print_json  CC=1  out:1
  src.vdisplay.client  [1 funcs]
    request  CC=3  out:8
  src.vdisplay.client_http  [3 funcs]
    __init__  CC=2  out:2
    build_request  CC=3  out:5
    normalize_payload  CC=1  out:1
  src.vdisplay.client_routes  [6 funcs]
    _route_browser_open  CC=4  out:0
    _route_control_command  CC=5  out:0
    _route_outputs_query  CC=4  out:3
    _route_terminal_open  CC=4  out:0
    _route_windows_query  CC=6  out:4
    route_command  CC=7  out:7
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.all_cmd  [4 funcs]
    handle  CC=1  out:3
    handle_outputs  CC=1  out:3
    register  CC=1  out:4
    register_outputs  CC=1  out:4
  src.vdisplay.commands.app  [1 funcs]
    handle  CC=6  out:17
  src.vdisplay.commands.auto  [1 funcs]
    handle  CC=8  out:18
  src.vdisplay.commands.common  [9 funcs]
    add_all_arg  CC=1  out:1
    add_control_selector_args  CC=1  out:21
    add_display_arg  CC=1  out:1
    add_map_args  CC=1  out:3
    add_preview_args  CC=1  out:3
    add_window_filter_args  CC=1  out:7
    control_selector_kwargs_for_service  CC=1  out:2
    control_selector_kwargs_from_args  CC=1  out:24
    include_all_from_args  CC=2  out:3
  src.vdisplay.commands.control  [9 funcs]
    _add_selector_args  CC=1  out:2
    _handle_browser_open  CC=5  out:8
    _handle_control_click  CC=1  out:1
    _handle_control_find  CC=1  out:1
    _handle_control_focus  CC=1  out:1
    _handle_control_list  CC=4  out:6
    _handle_control_set_value  CC=1  out:1
    _run_control  CC=5  out:6
    register  CC=1  out:46
  src.vdisplay.commands.diagnose  [2 funcs]
    handle  CC=5  out:13
    register  CC=1  out:8
  src.vdisplay.commands.hmi  [1 funcs]
    handle  CC=7  out:6
  src.vdisplay.commands.ide  [2 funcs]
    handle  CC=8  out:45
    register  CC=1  out:17
  src.vdisplay.commands.info  [1 funcs]
    handle  CC=1  out:2
  src.vdisplay.commands.map  [1 funcs]
    handle  CC=7  out:31
  src.vdisplay.commands.mirror  [1 funcs]
    handle  CC=3  out:5
  src.vdisplay.commands.monitors  [2 funcs]
    handle  CC=1  out:3
    register  CC=1  out:4
  src.vdisplay.commands.nlp  [1 funcs]
    handle  CC=2  out:4
  src.vdisplay.commands.observe  [1 funcs]
    handle_observe  CC=9  out:25
  src.vdisplay.commands.relay  [2 funcs]
    handle  CC=5  out:9
    handle_list_windows  CC=1  out:2
  src.vdisplay.commands.sampler  [8 funcs]
    _config_from_args  CC=1  out:1
    _handle_start  CC=4  out:6
    _handle_status  CC=2  out:4
    _handle_stop  CC=2  out:4
    _start_agent  CC=2  out:4
    _wait_for_sampler  CC=9  out:12
    handle  CC=3  out:4
    register  CC=1  out:22
  src.vdisplay.commands.screenshot  [2 funcs]
    handle  CC=1  out:2
    register  CC=1  out:14
  src.vdisplay.commands.session  [7 funcs]
    _resolve_session_dir  CC=9  out:21
    add_root_session_args  CC=1  out:2
    command_request_from_control_args  CC=8  out:32
    handle_export  CC=3  out:12
    handle_list  CC=3  out:14
    handle_reprocess  CC=2  out:4
    handle_show  CC=10  out:21
  src.vdisplay.commands.virtual  [1 funcs]
    handle  CC=6  out:9
  src.vdisplay.commands.windows  [2 funcs]
    handle  CC=1  out:3
    register  CC=1  out:4
  src.vdisplay.control.gui_map  [1 funcs]
    load_gui_map  CC=2  out:6
  src.vdisplay.control.gui_map_resolve  [1 funcs]
    map_element_to_node  CC=5  out:7
  src.vdisplay.control.plugins  [1 funcs]
    register_control_provider  CC=1  out:2
  src.vdisplay.control.policy  [1 funcs]
    assess_control_capability  CC=7  out:9
  src.vdisplay.control.providers.browser_session  [1 funcs]
    open  CC=1  out:1
  src.vdisplay.control.providers.browser_sync_executor  [1 funcs]
    run_browser_sync  CC=2  out:6
  src.vdisplay.control.providers.terminal_session  [1 funcs]
    default_registry  CC=1  out:0
  src.vdisplay.control.registry  [1 funcs]
    build  CC=3  out:6
  src.vdisplay.control.session  [2 funcs]
    build_catalog_from_agent_store  CC=11  out:17
    parse_session_kind  CC=3  out:5
  src.vdisplay.desktop_apps  [20 funcs]
    _binary_launch  CC=3  out:2
    _build_registry  CC=8  out:20
    _default_map_candidates  CC=5  out:18
    _desktop_launch  CC=2  out:2
    _expand_variants  CC=3  out:4
    _is_gui_map_file  CC=6  out:8
    _variants_for  CC=9  out:11
    _xwayland_variant  CC=1  out:3
    chat_selectors_for  CC=2  out:1
    get_desktop_app  CC=3  out:6
  src.vdisplay.discovery  [13 funcs]
    _attach_output_nl  CC=2  out:3
    _display_hint  CC=3  out:2
    _display_socket_exists  CC=2  out:5
    _list_monitors  CC=6  out:10
    _looks_like_xvfb_only  CC=4  out:4
    _merge_output_metadata  CC=4  out:22
    _parse_xrandr_query  CC=8  out:12
    diagnose_display  CC=10  out:19
    find_window_suggestions  CC=2  out:2
    list_monitors  CC=1  out:1
  src.vdisplay.hmi.pointer_probes  [2 funcs]
    is_wayland_session  CC=2  out:5
    probe_all_sources  CC=8  out:12
  src.vdisplay.hmi.watch  [1 funcs]
    run_hmi_watch  CC=6  out:8
  src.vdisplay.ide_prompt  [16 funcs]
    _build_map_missing_result  CC=2  out:2
    _build_no_selector_result  CC=10  out:7
    _build_write_kwargs  CC=9  out:10
    _find_first_selector  CC=11  out:10
    _find_map_target  CC=4  out:8
    _handle_focus_window  CC=2  out:3
    _handle_submit  CC=11  out:19
    _handle_wait_window  CC=9  out:10
    _ide_find_timeout_seconds  CC=2  out:3
    _is_wayland_session  CC=1  out:1
  src.vdisplay.integrations.pipeline  [1 funcs]
    observe_screen  CC=22  out:28
  src.vdisplay.integrations.vql_bridge  [1 funcs]
    reverse_generation_descriptor  CC=9  out:13
  src.vdisplay.nl  [8 funcs]
    _user_visible_app_labels  CC=9  out:9
    assign_windows_to_monitors  CC=3  out:6
    describe_output_nl  CC=13  out:13
    describe_window_nl  CC=14  out:16
    enrich_outputs_nl  CC=4  out:2
    ensure_monitor_ids  CC=5  out:6
    find_monitor_for_window  CC=3  out:1
    window_center_on_output  CC=3  out:18
  src.vdisplay.nlp  [10 funcs]
    _default_all  CC=1  out:1
    _default_display_suffix  CC=2  out:1
    _default_monitors  CC=1  out:1
    _default_windows  CC=1  out:1
    _display_suffix  CC=2  out:0
    _run_local_dsl  CC=7  out:7
    _validate_dsl  CC=1  out:2
    nl_to_dsl  CC=4  out:6
    parse_display  CC=10  out:6
    run_nl_prompt  CC=5  out:7
  src.vdisplay.payloads  [1 funcs]
    all_payload  CC=1  out:1
  src.vdisplay.utils  [2 funcs]
    run_command  CC=2  out:4
    run_command_bytes  CC=1  out:1
  src.vdisplay.windows.query  [3 funcs]
    find_companion_frames  CC=8  out:10
    find_windows  CC=6  out:5
    list_windows_enriched  CC=2  out:5

EDGES:
  packages.mcp2vdisplay.src.mcp2vdisplay.cli.main → packages.mcp2vdisplay.src.mcp2vdisplay.cli.create_server
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server → src.vdisplay.agent_config.resolve_agent_url
  packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_legacy → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_legacy
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.dsl2vdisplay.src.dsl2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy
  packages.dsl2vdisplay.src.dsl2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy → src.vdisplay.control.providers.browser_session.BrowserSessionRegistry.open
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry._load_schema
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.resolve_verb → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.normalize_tokens
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_windows → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_windows → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_screenshot → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_virtual_start → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_launch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_mirror → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_adopt → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._has_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_controls_list → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_controls_list → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_controls_find → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_click → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_focus → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_set_value → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_common
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_control_set_value → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_diagnose_control → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_browser_open → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_terminal_open → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_release → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.split_command
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.resolve_verb
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_screenshot → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_screenshot → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_virtual_start → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_virtual_start → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror → src.vdisplay.discovery.resolve_host_display
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror → src.vdisplay.discovery.list_outputs
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_adopt → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_adopt → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 339f 48219L | python:273,json:26,toml:11,shell:7,yaml:6,yml:5,proto:4,txt:2 | 2026-06-11
# generated in 0.12s
# CC̅=3.9 | critical:16/2085 | dups:0 | cycles:0

HEALTH[16]:
  🟡 CC    send_ide_prompt CC=15 (limit:15)
  🟡 CC    _handle_set_value_verification CC=16 (limit:15)
  🟡 CC    _aggregate CC=16 (limit:15)
  🟡 CC    global_region_to_capture_local CC=16 (limit:15)
  🟡 CC    execute CC=15 (limit:15)
  🟡 CC    apply_step_verify_drift CC=19 (limit:15)
  🟡 CC    _execute_one CC=19 (limit:15)
  🟡 CC    _task_from_mapping CC=22 (limit:15)
  🟡 CC    sample_pointer CC=16 (limit:15)
  🟡 CC    _drift_recommends_refresh CC=16 (limit:15)
  🟡 CC    observe_screen CC=22 (limit:15)
  🟡 CC    from_portal_payload CC=31 (limit:15)
  🟡 CC    screencast_stream_region_for_monitor CC=15 (limit:15)
  🟡 CC    request_keeper_capture CC=21 (limit:15)
  🟡 CC    try_screencast_capture CC=16 (limit:15)
  🟡 CC    start_screencast_via_agent CC=27 (limit:15)

REFACTOR[1]:
  1. split 16 high-CC methods  (CC>15)

PIPELINES[810]:
  [1] Src [create_server]: create_server → resolve_agent_url → _probe_default_agent → _probe_agent_url → ...(1 more)
      PURITY: 100% pure
  [2] Src [main]: main → _main_legacy → execute_dsl_line → dispatch → ...(5 more)
      PURITY: 100% pure
  [3] Src [_parse_windows]: _parse_windows → _with_display → pick_flag
      PURITY: 100% pure
  [4] Src [_parse_screenshot]: _parse_screenshot → pick_flag
      PURITY: 100% pure
  [5] Src [_parse_virtual_start]: _parse_virtual_start → pick_flag
      PURITY: 100% pure
  [6] Src [_parse_launch]: _parse_launch → pick_flag
      PURITY: 100% pure
  [7] Src [_parse_mirror]: _parse_mirror → pick_flag
      PURITY: 100% pure
  [8] Src [_parse_adopt]: _parse_adopt → pick_flag
      PURITY: 100% pure
  [9] Src [_parse_controls_list]: _parse_controls_list → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [10] Src [_parse_controls_find]: _parse_controls_find → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [11] Src [_parse_control_click]: _parse_control_click → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [12] Src [_parse_control_focus]: _parse_control_focus → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [13] Src [_parse_control_set_value]: _parse_control_set_value → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [14] Src [_parse_diagnose_control]: _parse_diagnose_control → _with_display → pick_flag
      PURITY: 100% pure
  [15] Src [_parse_browser_open]: _parse_browser_open → pick_flag
      PURITY: 100% pure
  [16] Src [_parse_terminal_open]: _parse_terminal_open → pick_flag
      PURITY: 100% pure
  [17] Src [_parse_release]: _parse_release → pick_flag
      PURITY: 100% pure
  [18] Src [_screenshot_to_text]: _screenshot_to_text
      PURITY: 100% pure
  [19] Src [_mirror_to_text]: _mirror_to_text
      PURITY: 100% pure
  [20] Src [_controls_list_to_text]: _controls_list_to_text
      PURITY: 100% pure
  [21] Src [_browser_open_to_text]: _browser_open_to_text
      PURITY: 100% pure
  [22] Src [_terminal_open_to_text]: _terminal_open_to_text
      PURITY: 100% pure
  [23] Src [_control_to_text]: _control_to_text
      PURITY: 100% pure
  [24] Src [handle_screenshot]: handle_screenshot → _ok
      PURITY: 100% pure
  [25] Src [handle_virtual_start]: handle_virtual_start → _ok
      PURITY: 100% pure
  [26] Src [handle_mirror]: handle_mirror → resolve_host_display → _display_socket_exists
      PURITY: 100% pure
  [27] Src [handle_adopt]: handle_adopt → _ok
      PURITY: 100% pure
  [28] Src [handle_release]: handle_release → _ok
      PURITY: 100% pure
  [29] Src [handle_health]: handle_health
      PURITY: 100% pure
  [30] Src [handle_info]: handle_info
      PURITY: 100% pure
  [31] Src [handle_outputs]: handle_outputs → handle_monitors
      PURITY: 100% pure
  [32] Src [handle_all]: handle_all
      PURITY: 100% pure
  [33] Src [handle_capabilities]: handle_capabilities
      PURITY: 100% pure
  [34] Src [handle_validate]: handle_validate
      PURITY: 100% pure
  [35] Src [main]: main → dispatch → _dispatch_legacy → validate_command_dict → ...(3 more)
      PURITY: 100% pure
  [36] Src [main]: main → uri_to_dsl
      PURITY: 100% pure
  [37] Src [main]: main → create_app → resolve_agent_url → _probe_default_agent → ...(2 more)
      PURITY: 100% pure
  [38] Src [main]: main → run_nl_prompt → nl_to_dsl → parse_display
      PURITY: 100% pure
  [39] Src [parse_display]: parse_display
      PURITY: 100% pure
  [40] Src [platform_capabilities]: platform_capabilities
      PURITY: 100% pure
  [41] Src [diagnostics]: diagnostics
      PURITY: 100% pure
  [42] Src [outputs]: outputs
      PURITY: 100% pure
  [43] Src [start_virtual]: start_virtual
      PURITY: 100% pure
  [44] Src [start_mirror]: start_mirror
      PURITY: 100% pure
  [45] Src [start_relay]: start_relay
      PURITY: 100% pure
  [46] Src [start_terminal]: start_terminal
      PURITY: 100% pure
  [47] Src [start_browser]: start_browser
      PURITY: 100% pure
  [48] Src [start_screencast]: start_screencast
      PURITY: 100% pure
  [49] Src [adopt_screencast]: adopt_screencast
      PURITY: 100% pure
  [50] Src [stop_screencast]: stop_screencast
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=4.1    ←in:0  →out:0
  │ !! portal_screencast         1218L  1C   56m  CC=31     ←12
  │ !! control                   1081L  0C   34m  CC=14     ←0
  │ !! scoring                    811L  2C   40m  CC=12     ←6
  │ !! session_recorder           763L  3C   34m  CC=14     ←6
  │ !! provider                   724L  1C   37m  CC=12     ←0
  │ !! verifier                   647L  3C   30m  CC=16     ←1
  │ !! ide_prompt                 601L  0C   17m  CC=15     ←13
  │ !! verify                     519L  0C   21m  CC=16     ←1
  │ !! gui_map_diff               500L  3C   18m  CC=14     ←2
  │ !! screencast_keeper          480L  0C   21m  CC=21     ←5
  │ linux_x11_relay            478L  2C   24m  CC=12     ←0
  │ descriptors                464L  5C   11m  CC=14     ←10
  │ desktop_apps               463L  2C   25m  CC=9      ←3
  │ !! screencast_crop            449L  0C   14m  CC=16     ←1
  │ host                       440L  0C   14m  CC=13     ←7
  │ events                     429L  1C   17m  CC=14     ←3
  │ atspi_impl                 413L  0C   19m  CC=8      ←1
  │ browser_playwright         380L  3C   36m  CC=14     ←2
  │ replay                     372L  3C   16m  CC=11     ←2
  │ vision_ocr                 365L  1C   18m  CC=13     ←7
  │ discovery                  364L  0C   14m  CC=11     ←25
  │ vision_preview             363L  2C   16m  CC=10     ←2
  │ browser_session            351L  2C   22m  CC=11     ←4
  │ selector                   347L  1C   18m  CC=14     ←9
  │ vql_bridge                 347L  0C   20m  CC=9      ←2
  │ !! tasks                      335L  1C   21m  CC=22     ←2
  │ session                    330L  0C   12m  CC=4      ←0
  │ linux_xwd                  320L  0C   21m  CC=12     ←10
  │ parsers                    320L  0C   12m  CC=12     ←1
  │ screenshot_verify          319L  0C   11m  CC=13     ←4
  │ map                        313L  0C    9m  CC=10     ←0
  │ keyboard                   300L  2C   11m  CC=12     ←0
  │ uia_impl                   299L  4C   29m  CC=13     ←3
  │ pointer_probes             297L  0C   12m  CC=13     ←7
  │ watch                      293L  0C   10m  CC=8      ←1
  │ local                      291L  0C   21m  CC=4      ←1
  │ sampler_loop               284L  3C   13m  CC=8      ←1
  │ agent                      284L  0C    7m  CC=14     ←0
  │ vision_template            280L  1C   11m  CC=11     ←5
  │ router                     271L  2C   10m  CC=9      ←2
  │ profile_inference          271L  1C   11m  CC=14     ←3
  │ !! coordinate_map             271L  0C   10m  CC=16     ←4
  │ ax_impl                    269L  4C   27m  CC=10     ←2
  │ terminal_screen            260L  3C   14m  CC=7      ←3
  │ linux_x11_mirror           259L  1C   17m  CC=10     ←0
  │ session                    257L  0C    8m  CC=10     ←2
  │ agent                      251L  0C   23m  CC=6      ←1
  │ atspi                      249L  1C   15m  CC=11     ←0
  │ codec                      246L  5C   16m  CC=14     ←1
  │ gui_map                    245L  6C   16m  CC=9      ←6
  │ img2nl_enrich              245L  0C   13m  CC=14     ←0
  │ gui_map_build              243L  0C   11m  CC=9      ←3
  │ policy                     242L  1C    8m  CC=7      ←2
  │ client_api                 242L  1C   27m  CC=9      ←0
  │ discovery                  239L  0C   11m  CC=4      ←0
  │ vision_llm                 236L  1C   12m  CC=12     ←2
  │ !! pointer_sampling           231L  0C    8m  CC=16     ←1
  │ mouse                      231L  2C   16m  CC=13     ←1
  │ capture                    230L  0C    6m  CC=13     ←1
  │ terminal_session           227L  2C   16m  CC=7      ←6
  │ portal                     221L  1C    7m  CC=11     ←1
  │ session                    216L  3C   11m  CC=11     ←2
  │ backend_scores             216L  0C   14m  CC=12     ←3
  │ models                     214L  3C    7m  CC=6      ←0
  │ !! observe_cache              214L  0C   13m  CC=16     ←2
  │ query                      209L  0C    6m  CC=9      ←5
  │ executor                   203L  1C    7m  CC=11     ←1
  │ browser_session_store      196L  1C   14m  CC=7      ←2
  │ api                        193L  3C   32m  CC=6      ←4
  │ !! runner                     192L  1C    6m  CC=19     ←1
  │ models                     187L  9C    7m  CC=4      ←0
  │ retry_policy               181L  2C    9m  CC=10     ←1
  │ gui_map_export             179L  0C    7m  CC=8      ←2
  │ filter                     173L  0C   12m  CC=14     ←2
  │ vision_backend             171L  0C    7m  CC=7      ←1
  │ uia                        169L  1C   10m  CC=6      ←0
  │ ax                         169L  1C   10m  CC=6      ←0
  │ control                    166L  0C   10m  CC=5      ←0
  │ session_recorder_diagnostics   165L  0C   11m  CC=13     ←3
  │ linux_xvfb                 164L  1C   14m  CC=8      ←0
  │ contracts                  164L  5C    7m  CC=4      ←1
  │ screen_context             164L  1C   10m  CC=12     ←1
  │ plugins                    163L  1C   11m  CC=8      ←6
  │ nl                         158L  0C    8m  CC=14     ←3
  │ nlp                        158L  0C   14m  CC=10     ←2
  │ routing_semantics          158L  1C    8m  CC=7      ←4
  │ !! pipeline                   151L  0C    6m  CC=22     ←2
  │ x11                        150L  1C   13m  CC=9      ←0
  │ terminal                   147L  1C   13m  CC=14     ←0
  │ screencast_stream_matching   146L  0C   13m  CC=8      ←1
  │ policy                     140L  1C    4m  CC=11     ←2
  │ coordinate_rotation        140L  0C   12m  CC=11     ←0
  │ !! map_health_handlers        139L  0C    8m  CC=19     ←1
  │ common                     137L  0C    9m  CC=2      ←10
  │ session_recorder_readme    133L  0C    8m  CC=14     ←2
  │ sampler                    132L  0C    8m  CC=9      ←0
  │ web_pointer                130L  0C    5m  CC=11     ←1
  │ !! screencast_cli             129L  0C    4m  CC=27     ←2
  │ client_routes              128L  0C    6m  CC=7      ←1
  │ !! executor                   125L  0C    6m  CC=15     ←6
  │ imgl_bridge                125L  0C    7m  CC=12     ←4
  │ session_context            124L  1C    8m  CC=6      ←6
  │ registry                   117L  1C   14m  CC=3      ←4
  │ ide                        115L  0C    2m  CC=8      ←0
  │ event_store                114L  1C   12m  CC=5      ←4
  │ linux_ydotool              114L  1C    9m  CC=8      ←0
  │ runtime                    111L  1C    8m  CC=10     ←3
  │ relay                      110L  0C    3m  CC=5      ←0
  │ scan                       110L  0C    7m  CC=6      ←2
  │ gui_map_resolve            109L  0C    9m  CC=6      ←3
  │ sampler                    109L  1C    3m  CC=5      ←1
  │ client_http                107L  1C    7m  CC=5      ←0
  │ context                    106L  1C    6m  CC=14     ←1
  │ normalize                  103L  0C    7m  CC=14     ←1
  │ artifacts                  102L  0C    5m  CC=13     ←1
  │ hmi                         99L  0C    2m  CC=7      ←0
  │ screencast_stream_meta      99L  0C    6m  CC=12     ←4
  │ engine                      99L  0C    6m  CC=11     ←4
  │ map                         98L  0C    2m  CC=7      ←0
  │ verify_policy               95L  0C    5m  CC=12     ←1
  │ auto                        94L  0C    2m  CC=8      ←0
  │ agent_config                93L  0C    9m  CC=6      ←18
  │ observe                     92L  0C    2m  CC=9      ←0
  │ drm                         92L  1C    5m  CC=11     ←0
  │ gui_map_events              91L  0C    4m  CC=6      ←2
  │ payloads                    86L  0C    5m  CC=1      ←2
  │ __init__                    83L  0C    2m  CC=5      ←2
  │ virtual                     81L  0C    2m  CC=6      ←0
  │ vision_disambiguate         78L  1C    6m  CC=4      ←4
  │ fbdev                       77L  1C    5m  CC=7      ←0
  │ capabilities                76L  1C    1m  CC=1      ←0
  │ watch_format                74L  0C    7m  CC=11     ←1
  │ control                     72L  0C    4m  CC=3      ←3
  │ base                        69L  1C   10m  CC=2      ←0
  │ action_state                69L  2C    4m  CC=6      ←1
  │ __init__                    69L  0C    0m  CC=0.0    ←0
  │ utils                       68L  0C    4m  CC=4      ←17
  │ mss                         68L  1C    5m  CC=8      ←0
  │ linux_xdotool               68L  1C    9m  CC=3      ←0
  │ engine                      67L  0C    3m  CC=2      ←1
  │ verbs                       67L  1C    0m  CC=0.0    ←0
  │ base                        64L  1C   11m  CC=1      ←0
  │ app                         59L  0C    2m  CC=6      ←0
  │ __init__                    58L  0C    1m  CC=2      ←1
  │ browser_engine              55L  1C    4m  CC=3      ←5
  │ mirror                      53L  0C    2m  CC=3      ←0
  │ screenshot                  53L  0C    2m  CC=1      ←0
  │ diagnose                    53L  0C    2m  CC=5      ←0
  │ pointer_types               52L  1C    3m  CC=11     ←0
  │ browser_sync_executor       51L  0C    4m  CC=2      ←5
  │ info                        51L  0C    1m  CC=6      ←0
  │ client                      49L  1C    2m  CC=3      ←0
  │ all_cmd                     46L  0C    4m  CC=1      ←0
  │ __init__                    46L  0C    0m  CC=0.0    ←0
  │ rank                        43L  0C    5m  CC=9      ←1
  │ map_health                  41L  0C    2m  CC=5      ←1
  │ errors                      39L  2C    2m  CC=4      ←5
  │ cli                         36L  0C    2m  CC=2      ←0
  │ x11                         35L  1C    4m  CC=4      ←0
  │ watch_seed                  35L  0C    1m  CC=7      ←0
  │ cli_handlers                34L  0C    6m  CC=1      ←19
  │ monitor_geometry            34L  0C    1m  CC=3      ←0
  │ mirror_stub                 34L  1C    4m  CC=1      ←0
  │ pointer                     33L  0C    0m  CC=0.0    ←0
  │ __init__                    31L  0C    0m  CC=0.0    ←0
  │ agent_dispatch              30L  0C    2m  CC=2      ←0
  │ coords                      30L  0C    1m  CC=4      ←0
  │ windows                     29L  0C    2m  CC=1      ←0
  │ capture                     27L  1C    1m  CC=4      ←0
  │ resolve                     27L  1C    4m  CC=4      ←2
  │ models                      26L  2C    0m  CC=0.0    ←0
  │ action_bounds               24L  0C    2m  CC=2      ←3
  │ nlp                         23L  0C    2m  CC=2      ←0
  │ timing                      23L  0C    2m  CC=2      ←3
  │ __init__                    23L  0C    0m  CC=0.0    ←0
  │ base                        22L  2C    3m  CC=1      ←0
  │ monitors                    19L  0C    2m  CC=1      ←0
  │ commands                    19L  0C    0m  CC=0.0    ←0
  │ constants                   19L  0C    0m  CC=0.0    ←0
  │ __init__                    18L  0C    0m  CC=0.0    ←0
  │ agent_envelope              17L  0C    1m  CC=6      ←1
  │ info                        16L  0C    2m  CC=1      ←0
  │ verify_strategy             16L  1C    0m  CC=0.0    ←0
  │ session_kind                15L  1C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    1m  CC=2      ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ __init__                    11L  0C    0m  CC=0.0    ←0
  │ __init__                    11L  0C    0m  CC=0.0    ←0
  │ exceptions                  10L  3C    0m  CC=0.0    ←0
  │ base                         9L  1C    1m  CC=1      ←0
  │ io                           7L  0C    1m  CC=1      ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __main__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  brain/                          CC̄=4.1    ←in:0  →out:0
  │ scratch_atspi_dump.txt     311L  0C    0m  CC=0.0    ←0
  │ scratch_test_screencast    123L  0C    1m  CC=2      ←0
  │ scratch_find_pycharm_chat    95L  0C    6m  CC=7      ←0
  │ scratch_atspi               18L  0C    0m  CC=0.0    ←0
  │
  packages/                       CC̄=3.2    ←in:0  →out:0
  │ sessions                   407L  0C   15m  CC=9      ←0
  │ grammar                    406L  0C   30m  CC=11     ←2
  │ task_store                 197L  3C   10m  CC=7      ←1
  │ sampler                    197L  0C    7m  CC=12     ←0
  │ serve_port                 190L  0C   11m  CC=13     ←2
  │ tasks                      190L  0C   13m  CC=5      ←0
  │ control                    190L  0C    1m  CC=1      ←0
  │ web                        189L  0C    2m  CC=3      ←0
  │ web_frame_cache            178L  0C    9m  CC=9      ←1
  │ session                    175L  0C    1m  CC=1      ←0
  │ runtime                    153L  1C   34m  CC=1      ←3
  │ bus                        137L  0C    4m  CC=14     ←8
  │ control                    131L  0C    9m  CC=4      ←0
  │ command                    120L  0C    7m  CC=3      ←0
  │ query                      115L  0C    8m  CC=4      ←1
  │ capture                    109L  0C    5m  CC=11     ←0
  │ _audit_execute             106L  0C    3m  CC=8      ←3
  │ envelope                    97L  0C    9m  CC=7      ←7
  │ server                      95L  0C    1m  CC=1      ←0
  │ schemas                     93L  0C    0m  CC=0.0    ←0
  │ app                         87L  0C    1m  CC=2      ←3
  │ health                      82L  0C    2m  CC=2      ←0
  │ capabilities                79L  0C    2m  CC=6      ←0
  │ screencast_recovery         75L  0C    4m  CC=8      ←2
  │ cli                         70L  0C    3m  CC=10     ←0
  │ tasks                       69L  0C    1m  CC=1      ←0
  │ session_store               65L  2C    5m  CC=5      ←1
  │ web_console                 62L  0C    2m  CC=2      ←0
  │ audit_context               57L  0C    3m  CC=7      ←3
  │ cli                         54L  0C    1m  CC=6      ←0
  │ schema_registry             53L  0C    4m  CC=3      ←3
  │ windows                     52L  0C    1m  CC=1      ←0
  │ web_replay                  49L  0C    2m  CC=9      ←0
  │ sampler                     47L  0C    1m  CC=1      ←0
  │ cli                         41L  0C    1m  CC=7      ←0
  │ server                      41L  0C    1m  CC=4      ←0
  │ broker_events               37L  0C    2m  CC=4      ←2
  │ cli                         35L  0C    1m  CC=3      ←0
  │ capture                     35L  0C    1m  CC=1      ←0
  │ cli                         34L  0C    1m  CC=7      ←0
  │ relay                       32L  0C    2m  CC=6      ←0
  │ decode                      31L  0C    1m  CC=7      ←1
  │ windows                     31L  0C    1m  CC=8      ←0
  │ cli                         30L  0C    1m  CC=4      ←0
  │ control_set_value.schema.json    30L  0C    0m  CC=0.0    ←0
  │ control_click.schema.json    29L  0C    0m  CC=0.0    ←0
  │ control_focus.schema.json    29L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              28L  0C    0m  CC=0.0    ←0
  │ _audit_headers              27L  0C    1m  CC=1      ←0
  │ result                      26L  1C    1m  CC=1      ←0
  │ controls_find.schema.json    25L  0C    0m  CC=0.0    ←0
  │ auth                        24L  0C    2m  CC=2      ←1
  │ cli                         23L  0C    2m  CC=2      ←1
  │ outputs                     19L  0C    1m  CC=2      ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ controls_list.schema.json    17L  0C    0m  CC=0.0    ←0
  │ browser_open.schema.json    16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ __init__                    15L  0C    1m  CC=2      ←1
  │ terminal_open.schema.json    14L  0C    0m  CC=0.0    ←0
  │ to_dsl                      13L  0C    2m  CC=1      ←1
  │ mirror.schema.json          13L  0C    0m  CC=0.0    ←0
  │ screenshot.schema.json      13L  0C    0m  CC=0.0    ←0
  │ outputs.schema.json         10L  0C    0m  CC=0.0    ←0
  │ diagnose_control.schema.json    10L  0C    0m  CC=0.0    ←0
  │ info.schema.json            10L  0C    0m  CC=0.0    ←0
  │ validate.schema.json        10L  0C    0m  CC=0.0    ←0
  │ health.schema.json           9L  0C    0m  CC=0.0    ←0
  │ __init__                     7L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=2.6    ←in:0  →out:0
  │ control_demo               172L  0C    5m  CC=6      ←0
  │ planfile-automation.yaml   170L  0C    0m  CC=0.0    ←0
  │ screenshot_meta            162L  0C    9m  CC=14     ←5
  │ run_all_examples.sh        158L  0C    9m  CC=0.0    ←0
  │ relay_demo                 137L  0C    3m  CC=11     ←0
  │ mirror_demo                 97L  0C    2m  CC=7      ←0
  │ provider                    94L  1C    5m  CC=3      ←1
  │ provider                    93L  1C    5m  CC=3      ←0
  │ my_provider                 92L  1C    8m  CC=3      ←1
  │ validate_artifacts          84L  0C    3m  CC=12     ←0
  │ agent                       73L  0C    2m  CC=4      ←0
  │ run_virtual                 63L  0C    2m  CC=4      ←0
  │ broker_demo                 57L  0C    1m  CC=9      ←0
  │ run.sh                      53L  0C    1m  CC=0.0    ←0
  │ run.sh                      47L  0C    1m  CC=0.0    ←0
  │ frame-001.png.meta.json     35L  0C    0m  CC=0.0    ←0
  │ frame-002.png.meta.json     35L  0C    0m  CC=0.0    ←0
  │ frame-000.png.meta.json     35L  0C    0m  CC=0.0    ←0
  │ host_capture                29L  0C    1m  CC=1      ←2
  │ Dockerfile                  29L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  29L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  28L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  28L  0C    0m  CC=0.0    ←0
  │ screen.png.meta.json        28L  0C    0m  CC=0.0    ←0
  │ __init__                    27L  0C    2m  CC=1      ←0
  │ run.sh                      26L  0C    1m  CC=0.0    ←0
  │ run-host.sh                 25L  0C    0m  CC=0.0    ←0
  │ run-host.sh                 24L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              24L  0C    0m  CC=0.0    ←0
  │ __init__                    23L  0C    1m  CC=1      ←0
  │ __init__                    23L  0C    1m  CC=1      ←0
  │ pyproject.toml              23L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  19L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          17L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          14L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          12L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          11L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ tree.txt                   241L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             189L  0C    0m  CC=0.0    ←0
  │ koru.yaml                  141L  0C    0m  CC=0.0    ←0
  │ app.vql.json               127L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ ui.vql.json                 80L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │
  maps/                           CC̄=0.0    ←in:0  →out:0
  │ !! pycharm-chat.json         1588L  0C    0m  CC=0.0    ←0
  │ !! pycharm-chat-fresh.json    795L  0C    0m  CC=0.0    ←0
  │ pycharm-chat-input.json     48L  0C    0m  CC=0.0    ←0
  │ cursor-chat.manifest.json    13L  0C    0m  CC=0.0    ←0
  │ pycharm-chat.manifest.json    13L  0C    0m  CC=0.0    ←0
  │ vscode-chat.manifest.json    13L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  proto/                          CC̄=0.0    ←in:0  →out:0
  │ common.proto                27L  0C    0m  CC=0.0    ←0
  │ command.proto               20L  0C    0m  CC=0.0    ←0
  │ result.proto                16L  0C    0m  CC=0.0    ←0
  │ event.proto                 16L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     packages/vdisplay-agent/src/vdisplay_agent/static/__init__.py  0L

COUPLING:
                                              src.vdisplay      packages.vdisplay-agent        packages.dsl2vdisplay              examples.common        packages.mcp2vdisplay       packages.rest2vdisplay         examples.host-mirror          examples.host-relay   examples.control-plugin-ax  examples.control-plugin-uia            examples.ci-agent      examples.control-plugin    examples.headless-virtual        packages.cli2vdisplay        packages.nlp2vdisplay
                 src.vdisplay                           ──                            5                            9                           ←1                            1                            1                           ←3                           ←3                           ←1                           ←1                                                         1                                                                                     ←1  hub
      packages.vdisplay-agent                           60                           ──                                                                                                                   1                                                                                                                                                                                                                                                                       hub
        packages.dsl2vdisplay                            6                                                        ──                                                        ←2                           ←4                                                                                                                                                                                                                                      ←2                               hub
              examples.common                            1                                                                                     ──                                                                                     ←3                           ←3                                                                                     ←2                                                        ←2                                                            hub
        packages.mcp2vdisplay                            4                                                         2                                                        ──                                                                                                                                                                                                                                                                                                 1
       packages.rest2vdisplay                            2                           ←1                            4                                                                                     ──                                                                                                                                                                                                                                                                     
         examples.host-mirror                            3                                                                                      3                                                                                     ──                                                                                                                                                                                                                                        
          examples.host-relay                            3                                                                                      3                                                                                                                  ──                                                                                                                                                                                                           
   examples.control-plugin-ax                            1                                                                                                                                                                                                                                      ──                            2                                                                                                                                                 
  examples.control-plugin-uia                            1                                                                                                                                                                                                                                      ←2                           ──                                                                                                                                                 
            examples.ci-agent                                                                                                                   2                                                                                                                                                                                                         ──                                                                                                                    
      examples.control-plugin                            1                                                                                                                                                                                                                                                                                                                             ──                                                                                       
    examples.headless-virtual                                                                                                                   2                                                                                                                                                                                                                                                                   ──                                                          
        packages.cli2vdisplay                                                                                      2                                                                                                                                                                                                                                                                                                                             ──                             
        packages.nlp2vdisplay                            1                                                                                                                  ←1                                                                                                                                                                                                                                                                                                ──
  CYCLES: none
  HUB: packages.vdisplay-agent/ (fan-in=5)
  HUB: packages.dsl2vdisplay/ (fan-in=18)
  HUB: src.vdisplay/ (fan-in=85)
  HUB: examples.common/ (fan-in=10)
  SMELL: packages.vdisplay-agent/ fan-out=61 → split needed
  SMELL: src.vdisplay/ fan-out=17 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 52 groups | 271f 41087L | 2026-06-11

SUMMARY:
  files_scanned: 271
  total_lines:   41087
  dup_groups:    52
  dup_fragments: 122
  saved_lines:   508
  scan_ms:       3490

HOTSPOTS[7] (files with most duplication):
  src/vdisplay/control/scoring.py  dup=105L  groups=3  frags=7  (0.3%)
  src/vdisplay/control/providers/ax.py  dup=76L  groups=6  frags=6  (0.2%)
  src/vdisplay/control/providers/uia.py  dup=76L  groups=6  frags=6  (0.2%)
  src/vdisplay/payloads.py  dup=46L  groups=1  frags=2  (0.1%)
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py  dup=34L  groups=1  frags=2  (0.1%)
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py  dup=30L  groups=2  frags=4  (0.1%)
  src/vdisplay/control/registry.py  dup=28L  groups=3  frags=7  (0.1%)

DUPLICATES[52] (ranked by impact):
  [920423ffadef7598] ! STRU  _score_uia_provider  L=35 N=2 saved=35 sim=1.00
      src/vdisplay/control/scoring.py:325-359  (_score_uia_provider)
      src/vdisplay/control/scoring.py:362-396  (_score_ax_provider)
  [443c93126a62d7a9] ! EXAC  _load_common  L=11 N=4 saved=33 sim=1.00
      examples/ci-agent/agent.py:15-25  (_load_common)
      examples/headless-virtual/run_virtual.py:13-23  (_load_common)
      examples/host-mirror/mirror_demo.py:16-26  (_load_common)
      examples/host-relay/relay_demo.py:17-27  (_load_common)
  [673d29d90b55293e]   STRU  local_windows_payload  L=23 N=2 saved=23 sim=1.00
      src/vdisplay/payloads.py:14-36  (local_windows_payload)
      src/vdisplay/payloads.py:39-61  (windows_payload)
  [6db29bc8a1ce32c0]   EXAC  snapshot  L=19 N=2 saved=19 sim=1.00
      src/vdisplay/control/providers/ax.py:67-85  (snapshot)
      src/vdisplay/control/providers/uia.py:67-85  (snapshot)
  [e186fafefced47c9]   EXAC  set_value  L=19 N=2 saved=19 sim=1.00
      src/vdisplay/control/providers/ax.py:141-159  (set_value)
      src/vdisplay/control/providers/uia.py:141-159  (set_value)
  [0c83678d9296d127]   EXAC  find  L=18 N=2 saved=18 sim=1.00
      src/vdisplay/control/providers/ax.py:87-104  (find)
      src/vdisplay/control/providers/uia.py:87-104  (find)
  [a8460ee697bc2dd5]   STRU  register_plugin  L=9 N=3 saved=18 sim=1.00
      examples/control-plugin/src/vdisplay_example_plugin/__init__.py:19-27  (register_plugin)
      examples/control-plugin-ax/src/vdisplay_example_ax_plugin/__init__.py:15-23  (register_plugin)
      examples/control-plugin-uia/src/vdisplay_example_uia_plugin/__init__.py:15-23  (register_plugin)
  [1e6593980c4874fb]   STRU  handle_windows  L=17 N=2 saved=17 sim=1.00
      packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py:46-62  (handle_windows)
      packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py:65-81  (handle_all)
  [94948b88ff78a042]   STRU  _controls_list  L=4 N=5 saved=16 sim=1.00
      src/vdisplay/application/handlers/agent.py:190-193  (_controls_list)
      src/vdisplay/application/handlers/agent.py:196-199  (_controls_find)
      src/vdisplay/application/handlers/agent.py:202-205  (_control_click)
      src/vdisplay/application/handlers/agent.py:208-211  (_control_focus)
      src/vdisplay/application/handlers/agent.py:214-217  (_control_set_value)
  [83f6aff43414a50f]   STRU  _uia_ready  L=7 N=3 saved=14 sim=1.00
      src/vdisplay/control/scoring.py:119-125  (_uia_ready)
      src/vdisplay/control/scoring.py:128-134  (_ax_ready)
      src/vdisplay/control/scoring.py:137-143  (_browser_ready)
  [1fe3c7539f2901fb]   STRU  _imgl_item_to_ocr_box  L=14 N=2 saved=14 sim=1.00
      src/vdisplay/integrations/imgl_bridge.py:103-116  (_imgl_item_to_ocr_box)
      src/vdisplay/integrations/observe_cache.py:190-203  (_item_to_ocr_box)
  [2daecba5919bff35]   STRU  enrich_screencast_stream_meta  L=13 N=2 saved=13 sim=1.00
      src/vdisplay/capture/screencast_stream_meta.py:42-54  (enrich_screencast_stream_meta)
      src/vdisplay/control/screenshot_verify.py:26-38  (enrich_screencast_stream_meta)
  [3930b9c0e70097f2]   EXAC  to_dict  L=4 N=4 saved=12 sim=1.00
      src/vdisplay/control/contracts.py:40-43  (to_dict)
      src/vdisplay/control/contracts.py:55-58  (to_dict)
      src/vdisplay/control/contracts.py:70-73  (to_dict)
      src/vdisplay/control/contracts.py:84-87  (to_dict)
  [2d7b9210c1b65241]   STRU  img2nl_enabled  L=3 N=5 saved=12 sim=1.00
      src/vdisplay/application/services/img2nl_enrich.py:10-12  (img2nl_enabled)
      src/vdisplay/control/browser_session_store.py:34-36  (detached_sessions_enabled)
      src/vdisplay/integrations/imgl_bridge.py:12-14  (imgl_enabled)
      src/vdisplay/integrations/observe_cache.py:13-15  (observe_cache_enabled)
      src/vdisplay/integrations/vql_bridge.py:14-16  (vql_enabled)
  [80f1f837300b8376]   STRU  _route_terminal_open  L=12 N=2 saved=12 sim=1.00
      src/vdisplay/client_routes.py:52-63  (_route_terminal_open)
      src/vdisplay/client_routes.py:66-77  (_route_browser_open)
  [69fb9fca8945007f]   STRU  _prefer_imgl_annotate  L=12 N=2 saved=12 sim=1.00
      src/vdisplay/control/vision_preview.py:135-146  (_prefer_imgl_annotate)
      src/vdisplay/integrations/vision_backend.py:13-24  (prefer_imgl_backend)
  [7168a023bfc45913]   EXAC  _system_python  L=5 N=3 saved=10 sim=1.00
      src/vdisplay/capture/portal.py:81-85  (_system_python)
      src/vdisplay/capture/portal_screencast.py:437-441  (_system_python)
      src/vdisplay/control/providers/atspi.py:40-44  (_system_python)
  [074206dcbb6b73b7]   STRU  _parse_mirror  L=10 N=2 saved=10 sim=1.00
      packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:112-121  (_parse_mirror)
      packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:248-257  (_parse_release)
  [25fa0495b0a2c2f8]   STRU  register  L=5 N=3 saved=10 sim=1.00
      src/vdisplay/commands/all_cmd.py:12-16  (register)
      src/vdisplay/commands/monitors.py:10-14  (register)
      src/vdisplay/commands/windows.py:10-14  (register)
  [388e0803312a61ae]   STRU  _safe_info  L=10 N=2 saved=10 sim=1.00
      src/vdisplay/control/session.py:70-79  (_safe_info)
      src/vdisplay/control/session.py:82-91  (_safe_capabilities)
  [e4a4ab03a683f2c7]   STRU  build_example_ax  L=9 N=2 saved=9 sim=1.00
      examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py:85-93  (build_example_ax)
      examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py:86-94  (build_example_uia)
  [81fae0599a2d525e]   STRU  imgl_available  L=9 N=2 saved=9 sim=1.00
      src/vdisplay/integrations/imgl_bridge.py:17-25  (imgl_available)
      src/vdisplay/integrations/vql_bridge.py:19-27  (vql_available)
  [b8e2782d68a777c3]   STRU  _default_virtual_backend  L=4 N=3 saved=8 sim=1.00
      src/vdisplay/api.py:13-16  (_default_virtual_backend)
      src/vdisplay/api.py:19-22  (_default_mirror_backend)
      src/vdisplay/api.py:25-28  (_default_relay_backend)
  [fe376659b495c4e6]   STRU  ax_deps_available  L=8 N=2 saved=8 sim=1.00
      src/vdisplay/control/providers/ax_impl.py:57-64  (ax_deps_available)
      src/vdisplay/control/providers/uia_impl.py:57-64  (uia_deps_available)
  [aeb0b4ebee84950e]   STRU  _build_uia  L=4 N=3 saved=8 sim=1.00
      src/vdisplay/control/registry.py:67-70  (_build_uia)
      src/vdisplay/control/registry.py:73-76  (_build_ax)
      src/vdisplay/control/registry.py:97-100  (_build_vision)
  [cf70134602883aa7]   STRU  _build_browser  L=4 N=3 saved=8 sim=1.00
      src/vdisplay/control/registry.py:79-82  (_build_browser)
      src/vdisplay/control/registry.py:85-88  (_build_x11)
      src/vdisplay/control/registry.py:91-94  (_build_terminal)
  [ce7590c6f8584f2d]   EXAC  invoke  L=7 N=2 saved=7 sim=1.00
      src/vdisplay/control/providers/ax.py:125-131  (invoke)
      src/vdisplay/control/providers/uia.py:125-131  (invoke)
  [e7968443c0e0ad00]   EXAC  focus  L=7 N=2 saved=7 sim=1.00
      src/vdisplay/control/providers/ax.py:133-139  (focus)
      src/vdisplay/control/providers/uia.py:133-139  (focus)
  [d7079f3dea9cd702]   STRU  _atspi_ready  L=7 N=2 saved=7 sim=1.00
      src/vdisplay/control/scoring.py:110-116  (_atspi_ready)
      src/vdisplay/control/scoring.py:180-186  (_terminal_ready)
  [93f796dd58175244]   STRU  _terminal_line_matches  L=7 N=2 saved=7 sim=1.00
      src/vdisplay/control/selector.py:183-189  (_terminal_line_matches)
      src/vdisplay/control/selector.py:192-198  (_terminal_col_matches)
  [6fc9c2a6260f7dbb]   STRU  control_focus_type_seconds  L=7 N=2 saved=7 sim=1.00
      src/vdisplay/control/timing.py:8-14  (control_focus_type_seconds)
      src/vdisplay/control/timing.py:17-23  (control_pointer_settle_seconds)
  [1d15d7ed86dd4da6]   EXAC  find  L=6 N=2 saved=6 sim=1.00
      src/vdisplay/control/providers/atspi.py:215-220  (find)
      src/vdisplay/control/providers/x11.py:59-64  (find)
  [ab50b6c9821c38ed]   EXAC  bounds  L=6 N=2 saved=6 sim=1.00
      src/vdisplay/control/providers/ax.py:161-166  (bounds)
      src/vdisplay/control/providers/uia.py:161-166  (bounds)
  [e85a846f8e6e994c]   STRU  keeper_state_path  L=3 N=3 saved=6 sim=1.00
      src/vdisplay/capture/screencast_keeper.py:31-33  (keeper_state_path)
      src/vdisplay/capture/screencast_keeper.py:36-38  (keeper_stop_path)
      src/vdisplay/capture/screencast_keeper.py:41-43  (keeper_socket_path)
  [74ff44f1b5a82c2b]   STRU  _matches_name_fields  L=6 N=2 saved=6 sim=1.00
      src/vdisplay/control/providers/ax_impl.py:95-100  (_matches_name_fields)
      src/vdisplay/control/providers/uia_impl.py:88-93  (_matches_name_fields)
  [da81c4e42f1334a8]   STRU  _matches_selector  L=6 N=2 saved=6 sim=1.00
      src/vdisplay/control/providers/ax_impl.py:113-118  (_matches_selector)
      src/vdisplay/control/providers/uia_impl.py:108-113  (_matches_selector)
  [5177a541164fa53c]   EXAC  _vdisplay_src_path  L=5 N=2 saved=5 sim=1.00
      src/vdisplay/capture/portal_screencast.py:1165-1169  (_vdisplay_src_path)
      src/vdisplay/control/providers/atspi.py:47-51  (_vdisplay_src_path)
  [5fc23137774f78a9]   STRU  _get_name_safe  L=5 N=2 saved=5 sim=1.00
      brain/scratch_find_pycharm_chat.py:16-20  (_get_name_safe)
      brain/scratch_find_pycharm_chat.py:23-27  (_get_desc_safe)
  [3dd47853913ce2b2]   STRU  _use_mock_backend  L=5 N=2 saved=5 sim=1.00
      examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py:52-56  (_use_mock_backend)
      examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py:53-57  (_use_mock_backend)
  [8a91889b8e161c42]   STRU  _screenshot_to_text  L=5 N=2 saved=5 sim=1.00
      packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:298-302  (_screenshot_to_text)
      packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:305-309  (_mirror_to_text)
  [69ba40a4847babb6]   STRU  resolve_map_element  L=5 N=2 saved=5 sim=1.00
      src/vdisplay/control/gui_map_resolve.py:12-16  (resolve_map_element)
      src/vdisplay/control/gui_map_resolve.py:19-23  (resolve_map_region)
  [758bd50dec4060e6]   STRU  cache_dir  L=5 N=2 saved=5 sim=1.00
      src/vdisplay/integrations/observe_cache.py:39-43  (cache_dir)
      src/vdisplay/integrations/observe_cache.py:46-50  (vql_cache_dir)
  [084cc31ae50eea8e]   EXAC  bounds  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/control/providers/atspi.py:246-249  (bounds)
      src/vdisplay/control/providers/terminal.py:124-127  (bounds)
  [1b4a3820cac967b7]   STRU  _remember_screencast_path  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/capture/portal_screencast.py:24-27  (_remember_screencast_path)
      src/vdisplay/capture/portal_screencast.py:30-33  (_forget_screencast_path)
  [256755d12aec5824]   STRU  create_ax_backend  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/control/providers/ax_impl.py:266-269  (create_ax_backend)
      src/vdisplay/control/providers/uia_impl.py:296-299  (create_uia_backend)
  [b0f54d48b543ed9a]   STRU  default_provider_registry  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/control/registry.py:114-117  (default_provider_registry)
      src/vdisplay/ide_prompt.py:26-29  (_is_wayland_session)
  [bd065add6cf51e32]   STRU  _vertical_overlap  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/control/vision_ocr.py:209-212  (_vertical_overlap)
      src/vdisplay/control/vision_ocr.py:215-218  (_horizontal_overlap)
  [9063575af46509c9]   STRU  available  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/input/linux_xdotool.py:18-21  (available)
      src/vdisplay/input/linux_ydotool.py:27-30  (available)
  [cbe2ba609e614f7d]   EXAC  close_all  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/control/providers/browser_session.py:342-344  (close_all)
      src/vdisplay/control/providers/terminal_session.py:218-220  (close_all)
  [7e769be7bd62da72]   EXAC  bounds  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/control/providers/vision/provider.py:719-721  (bounds)
      src/vdisplay/control/providers/x11.py:105-107  (bounds)
  [2bae6c54b401ddd7]   STRU  vision_llm_fallback_enabled  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/control/vision_llm.py:73-75  (vision_llm_fallback_enabled)
      src/vdisplay/control/vision_llm.py:78-80  (vision_llm_enrich_enabled)
  [f5bfacfda8981cef]   STRU  looks_like_internal_class  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/windows/filter.py:8-10  (looks_like_internal_class)
      src/vdisplay/windows/filter.py:13-15  (looks_like_internal_name)

REFACTOR[52] (ranked by priority):
  [1] ○ extract_function   → src/vdisplay/control/utils/_score_uia_provider.py
      WHY: 2 occurrences of 35-line block across 1 files — saves 35 lines
      FILES: src/vdisplay/control/scoring.py
  [2] ○ extract_function   → examples/utils/_load_common.py
      WHY: 4 occurrences of 11-line block across 4 files — saves 33 lines
      FILES: examples/ci-agent/agent.py, examples/headless-virtual/run_virtual.py, examples/host-mirror/mirror_demo.py, examples/host-relay/relay_demo.py
  [3] ○ extract_function   → src/vdisplay/utils/local_windows_payload.py
      WHY: 2 occurrences of 23-line block across 1 files — saves 23 lines
      FILES: src/vdisplay/payloads.py
  [4] ○ extract_function   → src/vdisplay/control/providers/utils/snapshot.py
      WHY: 2 occurrences of 19-line block across 2 files — saves 19 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [5] ○ extract_function   → src/vdisplay/control/providers/utils/set_value.py
      WHY: 2 occurrences of 19-line block across 2 files — saves 19 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [6] ○ extract_function   → src/vdisplay/control/providers/utils/find.py
      WHY: 2 occurrences of 18-line block across 2 files — saves 18 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [7] ○ extract_function   → examples/utils/register_plugin.py
      WHY: 3 occurrences of 9-line block across 3 files — saves 18 lines
      FILES: examples/control-plugin-ax/src/vdisplay_example_ax_plugin/__init__.py, examples/control-plugin-uia/src/vdisplay_example_uia_plugin/__init__.py, examples/control-plugin/src/vdisplay_example_plugin/__init__.py
  [8] ○ extract_function   → packages/dsl2vdisplay/src/dsl2vdisplay/handlers/utils/handle_windows.py
      WHY: 2 occurrences of 17-line block across 1 files — saves 17 lines
      FILES: packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py
  [9] ○ extract_function   → src/vdisplay/application/handlers/utils/_controls_list.py
      WHY: 5 occurrences of 4-line block across 1 files — saves 16 lines
      FILES: src/vdisplay/application/handlers/agent.py
  [10] ○ extract_function   → src/vdisplay/control/utils/_uia_ready.py
      WHY: 3 occurrences of 7-line block across 1 files — saves 14 lines
      FILES: src/vdisplay/control/scoring.py
  [11] ○ extract_function   → src/vdisplay/integrations/utils/_imgl_item_to_ocr_box.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: src/vdisplay/integrations/imgl_bridge.py, src/vdisplay/integrations/observe_cache.py
  [12] ○ extract_function   → src/vdisplay/utils/enrich_screencast_stream_meta.py
      WHY: 2 occurrences of 13-line block across 2 files — saves 13 lines
      FILES: src/vdisplay/capture/screencast_stream_meta.py, src/vdisplay/control/screenshot_verify.py
  [13] ○ extract_function   → src/vdisplay/control/utils/to_dict.py
      WHY: 4 occurrences of 4-line block across 1 files — saves 12 lines
      FILES: src/vdisplay/control/contracts.py
  [14] ○ extract_function   → src/vdisplay/utils/img2nl_enabled.py
      WHY: 5 occurrences of 3-line block across 5 files — saves 12 lines
      FILES: src/vdisplay/application/services/img2nl_enrich.py, src/vdisplay/control/browser_session_store.py, src/vdisplay/integrations/imgl_bridge.py, src/vdisplay/integrations/observe_cache.py, src/vdisplay/integrations/vql_bridge.py
  [15] ○ extract_function   → src/vdisplay/utils/_route_terminal_open.py
      WHY: 2 occurrences of 12-line block across 1 files — saves 12 lines
      FILES: src/vdisplay/client_routes.py
  [16] ○ extract_function   → src/vdisplay/utils/_prefer_imgl_annotate.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: src/vdisplay/control/vision_preview.py, src/vdisplay/integrations/vision_backend.py
  [17] ○ extract_function   → src/vdisplay/utils/_system_python.py
      WHY: 3 occurrences of 5-line block across 3 files — saves 10 lines
      FILES: src/vdisplay/capture/portal.py, src/vdisplay/capture/portal_screencast.py, src/vdisplay/control/providers/atspi.py
  [18] ○ extract_function   → packages/dsl2vdisplay/src/dsl2vdisplay/utils/_parse_mirror.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py
  [19] ○ extract_function   → src/vdisplay/commands/utils/register.py
      WHY: 3 occurrences of 5-line block across 3 files — saves 10 lines
      FILES: src/vdisplay/commands/all_cmd.py, src/vdisplay/commands/monitors.py, src/vdisplay/commands/windows.py
  [20] ○ extract_function   → src/vdisplay/control/utils/_safe_info.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: src/vdisplay/control/session.py
  [21] ○ extract_function   → examples/utils/build_example_ax.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py, examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py
  [22] ○ extract_function   → src/vdisplay/integrations/utils/imgl_available.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: src/vdisplay/integrations/imgl_bridge.py, src/vdisplay/integrations/vql_bridge.py
  [23] ○ extract_function   → src/vdisplay/utils/_default_virtual_backend.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/api.py
  [24] ○ extract_function   → src/vdisplay/control/providers/utils/ax_deps_available.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: src/vdisplay/control/providers/ax_impl.py, src/vdisplay/control/providers/uia_impl.py
  [25] ○ extract_function   → src/vdisplay/control/utils/_build_uia.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/control/registry.py
  [26] ○ extract_function   → src/vdisplay/control/utils/_build_browser.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/control/registry.py
  [27] ○ extract_function   → src/vdisplay/control/providers/utils/invoke.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [28] ○ extract_function   → src/vdisplay/control/providers/utils/focus.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [29] ○ extract_function   → src/vdisplay/control/utils/_atspi_ready.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: src/vdisplay/control/scoring.py
  [30] ○ extract_function   → src/vdisplay/control/utils/_terminal_line_matches.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: src/vdisplay/control/selector.py
  [31] ○ extract_function   → src/vdisplay/control/utils/control_focus_type_seconds.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: src/vdisplay/control/timing.py
  [32] ○ extract_function   → src/vdisplay/control/providers/utils/find.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/vdisplay/control/providers/atspi.py, src/vdisplay/control/providers/x11.py
  [33] ○ extract_function   → src/vdisplay/control/providers/utils/bounds.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [34] ○ extract_function   → src/vdisplay/capture/utils/keeper_state_path.py
      WHY: 3 occurrences of 3-line block across 1 files — saves 6 lines
      FILES: src/vdisplay/capture/screencast_keeper.py
  [35] ○ extract_function   → src/vdisplay/control/providers/utils/_matches_name_fields.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/vdisplay/control/providers/ax_impl.py, src/vdisplay/control/providers/uia_impl.py
  [36] ○ extract_function   → src/vdisplay/control/providers/utils/_matches_selector.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/vdisplay/control/providers/ax_impl.py, src/vdisplay/control/providers/uia_impl.py
  [37] ○ extract_function   → src/vdisplay/utils/_vdisplay_src_path.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: src/vdisplay/capture/portal_screencast.py, src/vdisplay/control/providers/atspi.py
  [38] ○ extract_function   → brain/utils/_get_name_safe.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: brain/scratch_find_pycharm_chat.py
  [39] ○ extract_function   → examples/utils/_use_mock_backend.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py, examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py
  [40] ○ extract_function   → packages/dsl2vdisplay/src/dsl2vdisplay/utils/_screenshot_to_text.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py
  [41] ○ extract_function   → src/vdisplay/control/utils/resolve_map_element.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: src/vdisplay/control/gui_map_resolve.py
  [42] ○ extract_function   → src/vdisplay/integrations/utils/cache_dir.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: src/vdisplay/integrations/observe_cache.py
  [43] ○ extract_function   → src/vdisplay/control/providers/utils/bounds.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/control/providers/atspi.py, src/vdisplay/control/providers/terminal.py
  [44] ○ extract_function   → src/vdisplay/capture/utils/_remember_screencast_path.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: src/vdisplay/capture/portal_screencast.py
  [45] ○ extract_function   → src/vdisplay/control/providers/utils/create_ax_backend.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/control/providers/ax_impl.py, src/vdisplay/control/providers/uia_impl.py
  [46] ○ extract_function   → src/vdisplay/utils/default_provider_registry.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/control/registry.py, src/vdisplay/ide_prompt.py
  [47] ○ extract_function   → src/vdisplay/control/utils/_vertical_overlap.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: src/vdisplay/control/vision_ocr.py
  [48] ○ extract_function   → src/vdisplay/input/utils/available.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/input/linux_xdotool.py, src/vdisplay/input/linux_ydotool.py
  [49] ○ extract_function   → src/vdisplay/control/providers/utils/close_all.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: src/vdisplay/control/providers/browser_session.py, src/vdisplay/control/providers/terminal_session.py
  [50] ○ extract_function   → src/vdisplay/control/providers/utils/bounds.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: src/vdisplay/control/providers/vision/provider.py, src/vdisplay/control/providers/x11.py
  [51] ○ extract_function   → src/vdisplay/control/utils/vision_llm_fallback_enabled.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/vdisplay/control/vision_llm.py
  [52] ○ extract_function   → src/vdisplay/windows/utils/looks_like_internal_class.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/vdisplay/windows/filter.py

QUICK_WINS[36] (low risk, high savings — do first):
  [1] extract_function   saved=35L  → src/vdisplay/control/utils/_score_uia_provider.py
      FILES: scoring.py
  [2] extract_function   saved=33L  → examples/utils/_load_common.py
      FILES: agent.py, run_virtual.py, mirror_demo.py +1
  [3] extract_function   saved=23L  → src/vdisplay/utils/local_windows_payload.py
      FILES: payloads.py
  [4] extract_function   saved=19L  → src/vdisplay/control/providers/utils/snapshot.py
      FILES: ax.py, uia.py
  [5] extract_function   saved=19L  → src/vdisplay/control/providers/utils/set_value.py
      FILES: ax.py, uia.py
  [6] extract_function   saved=18L  → src/vdisplay/control/providers/utils/find.py
      FILES: ax.py, uia.py
  [7] extract_function   saved=18L  → examples/utils/register_plugin.py
      FILES: __init__.py, __init__.py, __init__.py
  [8] extract_function   saved=17L  → packages/dsl2vdisplay/src/dsl2vdisplay/handlers/utils/handle_windows.py
      FILES: query.py
  [9] extract_function   saved=16L  → src/vdisplay/application/handlers/utils/_controls_list.py
      FILES: agent.py
  [10] extract_function   saved=14L  → src/vdisplay/control/utils/_uia_ready.py
      FILES: scoring.py

EFFORT_ESTIMATE (total ≈ 17.5h):
  hard   _score_uia_provider                 saved=35L  ~105min
  medium _load_common                        saved=33L  ~66min
  medium local_windows_payload               saved=23L  ~46min
  medium snapshot                            saved=19L  ~38min
  medium set_value                           saved=19L  ~38min
  medium find                                saved=18L  ~36min
  medium register_plugin                     saved=18L  ~36min
  medium handle_windows                      saved=17L  ~34min
  medium _controls_list                      saved=16L  ~32min
  easy   _uia_ready                          saved=14L  ~28min
  ... +42 more (~592min)

METRICS-TARGET:
  dup_groups:  52 → 0
  saved_lines: 508 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 2023 func | 227f | 2026-06-11
# generated in 0.01s

NEXT[10] (ranked by impact):
  [1] !! SPLIT           src/vdisplay/capture/portal_screencast.py
      WHY: 1218L, 1 classes, max CC=31
      EFFORT: ~4h  IMPACT: 37758

  [2] !! SPLIT-FUNC      start_screencast_via_agent  CC=27  fan=21
      WHY: CC=27 exceeds 15
      EFFORT: ~1h  IMPACT: 567

  [3] !! SPLIT-FUNC      PortalScreenCastSession.from_portal_payload  CC=31  fan=18
      WHY: CC=31 exceeds 15
      EFFORT: ~1h  IMPACT: 558

  [4] !  SPLIT-FUNC      observe_screen  CC=22  fan=23
      WHY: CC=22 exceeds 15
      EFFORT: ~1h  IMPACT: 506

  [5] !  SPLIT-FUNC      request_keeper_capture  CC=21  fan=24
      WHY: CC=21 exceeds 15
      EFFORT: ~1h  IMPACT: 504

  [6] !  SPLIT-FUNC      execute  CC=15  fan=25
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 375

  [7] !  SPLIT-FUNC      apply_step_verify_drift  CC=19  fan=16
      WHY: CC=19 exceeds 15
      EFFORT: ~1h  IMPACT: 304

  [8] !  SPLIT-FUNC      send_ide_prompt  CC=15  fan=19
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 285

  [9] !  SPLIT-FUNC      sample_pointer  CC=16  fan=16
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 256

  [10] !  SPLIT-FUNC      _execute_one  CC=19  fan=12
      WHY: CC=19 exceeds 15
      EFFORT: ~1h  IMPACT: 228


RISKS[3]:
  ⚠ Splitting maps/pycharm-chat.json may break 0 import paths
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting src/vdisplay/capture/portal_screencast.py may break 56 import paths

METRICS-TARGET:
  CC̄:          4.0 → ≤2.8
  max-CC:      31 → ≤15
  god-modules: 13 → 0
  high-CC(≥15): 16 → ≤8
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=4.0 → now CC̄=4.0
```

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

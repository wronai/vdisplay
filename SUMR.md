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
- **version**: `0.1.16`
- **python_requires**: `>=3.10`
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
  version: 0.1.16;
}

dependencies {
  windows: comtypes>=1.4.0;
  macos: "pyobjc-framework-ApplicationServices>=10.0, pyobjc-framework-Cocoa>=10.0";
  pillow: Pillow>=10.0;
  sampler: Pillow>=10.0;
  dev: "pytest>=8.0, Pillow>=10.0, fastapi>=0.110, httpx>=0.27, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, dsl2vdisplay, vdisplay-agent, uvicorn>=0.27, pydantic>=2, sqlmodel>=0.0.22";
  core: "pydantic>=2, tenacity>=8.0, structlog>=24.0";
  control: "dsl2vdisplay, nlp2vdisplay";
  browser: playwright>=1.40;
  vision: "Pillow>=10.0, pytesseract>=0.3.10, opencv-python>=4.8";
  terminal: "pyte>=0.8.1, pexpect>=4.9, wcwidth>=0.2.13";
  agent: "vdisplay-agent, fastapi>=0.110, uvicorn>=0.27, sqlmodel>=0.0.22";
  img2nl: img2nl[analyze];
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
  keys: OPENROUTER_API_KEY, LLM_MODEL, VDISPLAY_AGENT_AUTO, VDISPLAY_AGENT_HOST, VDISPLAY_AGENT_PORT, VDISPLAY_AGENT_URL, VDISPLAY_AGENT_TOKEN, VDISPLAY_AGENT_BROKER, DISPLAY, XDG_SESSION_TYPE, XDG_CURRENT_DESKTOP, DESKTOP_SESSION, VDISPLAY_BROWSER_DETACHED, VDISPLAY_VISION_LLM_MODE, VDISPLAY_VISION_LLM_MODALITIES, VDISPLAY_VISION_LLM, VDISPLAY_VISION_LLM_TIMEOUT_S, VDISPLAY_VISION_LLM_ENABLED, VDISPLAY_CONTROL_FOCUS_MS, VDISPLAY_CONTROL_POINTER_SETTLE_MS, WAYLAND_DISPLAY, VDISPLAY_SCREENCAST_MULTIPLE, VDISPLAY_SCREENCAST_CURSOR, VDISPLAY_SESSION_DIR, VDISPLAY_SESSION, VDISPLAY_SESSION_ID, YDOTOOL_SOCKET, VDISPLAY_ALLOW_YDOTOOL_TYPING, VDISPLAY_IMG2NL, VDISPLAY_IMG2NL_LOCALE, VDISPLAY_CONTROL_SETTLE_MS, VDISPLAY_CAPTURE_ALLOW_PORTAL, PYTEST_CURRENT_TEST;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.10;
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

*465 nodes · 500 edges · 114 modules · CC̄=3.5*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `register_routes` *(in packages.vdisplay-agent.src.vdisplay_agent.routes.control)* | 1 | 0 | 53 | **53** |
| `pick_flag` *(in packages.dsl2vdisplay.src.dsl2vdisplay.grammar)* | 3 | 44 | 2 | **46** |
| `register` *(in src.vdisplay.commands.control)* | 1 | 0 | 46 | **46** |
| `create_app` *(in packages.rest2vdisplay.src.rest2vdisplay.app)* | 2 | 3 | 38 | **41** |
| `dispatch` *(in packages.dsl2vdisplay.src.dsl2vdisplay.bus)* | 14 ⚠ | 13 | 27 | **40** |
| `run_command` *(in src.vdisplay.utils)* | 2 | 33 | 4 | **37** |
| `print_json` *(in src.vdisplay.cli_handlers)* | 1 | 36 | 1 | **37** |
| `list_outputs` *(in src.vdisplay.discovery)* | 8 | 9 | 27 | **36** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/vdisplay
# generated in 0.24s
# nodes: 465 | edges: 500 | modules: 114
# CC̄=3.5

HUBS[20]:
  packages.vdisplay-agent.src.vdisplay_agent.routes.control.register_routes
    CC=1  in:0  out:53  total:53
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
    CC=3  in:44  out:2  total:46
  src.vdisplay.commands.control.register
    CC=1  in:0  out:46  total:46
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=14  in:13  out:27  total:40
  src.vdisplay.utils.run_command
    CC=2  in:33  out:4  total:37
  src.vdisplay.cli_handlers.print_json
    CC=1  in:36  out:1  total:37
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  examples.agent-broker.broker_demo.main
    CC=9  in:0  out:35  total:35
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  src.vdisplay.commands.session.command_request_from_control_args
    CC=8  in:1  out:32  total:33
  packages.vdisplay-agent.src.vdisplay_agent.routes.health.register_routes
    CC=1  in:0  out:33  total:33
  src.vdisplay.discovery.resolve_host_display
    CC=11  in:26  out:7  total:33
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:32  total:32
  examples.control-plane.control_demo.run_browser_demo
    CC=6  in:1  out:30  total:31
  src.vdisplay.commands.map.handle
    CC=7  in:0  out:31  total:31
  examples.host-mirror.mirror_demo.main
    CC=7  in:0  out:31  total:31
  src.vdisplay.control.descriptors.detect_platform_profile
    CC=14  in:8  out:23  total:31
  src.vdisplay.agent_config.resolve_agent_url
    CC=6  in:24  out:5  total:29
  packages.vdisplay-agent.src.vdisplay_agent.envelope.json_error
    CC=5  in:21  out:8  total:29

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
  packages.vdisplay-agent.src.vdisplay_agent.cli  [1 funcs]
    main  CC=4  out:18
  packages.vdisplay-agent.src.vdisplay_agent.envelope  [7 funcs]
    agent_meta  CC=1  out:0
    failure  CC=3  out:2
    from_runtime  CC=3  out:8
    json_error  CC=5  out:8
    json_from_runtime  CC=1  out:2
    json_success  CC=1  out:2
    success  CC=2  out:1
  packages.vdisplay-agent.src.vdisplay_agent.routes  [1 funcs]
    register_all_routes  CC=2  out:3
  packages.vdisplay-agent.src.vdisplay_agent.routes.auth  [2 funcs]
    expected_token  CC=2  out:2
    make_check_auth  CC=1  out:5
  packages.vdisplay-agent.src.vdisplay_agent.routes.capture  [1 funcs]
    register_routes  CC=1  out:6
  packages.vdisplay-agent.src.vdisplay_agent.routes.control  [1 funcs]
    register_routes  CC=1  out:53
  packages.vdisplay-agent.src.vdisplay_agent.routes.health  [1 funcs]
    register_routes  CC=1  out:33
  packages.vdisplay-agent.src.vdisplay_agent.routes.sampler  [1 funcs]
    register_routes  CC=1  out:18
  packages.vdisplay-agent.src.vdisplay_agent.routes.tasks  [1 funcs]
    register_routes  CC=1  out:27
  packages.vdisplay-agent.src.vdisplay_agent.routes.windows  [1 funcs]
    register_routes  CC=1  out:12
  packages.vdisplay-agent.src.vdisplay_agent.runtime  [1 funcs]
    list_control_plugins  CC=1  out:1
  packages.vdisplay-agent.src.vdisplay_agent.serve_port  [8 funcs]
    _parse_ss_pids  CC=2  out:4
    _pid_alive  CC=3  out:1
    _pids_from_lsof  CC=5  out:6
    _pids_from_ss  CC=3  out:2
    _probe_is_vdisplay_agent  CC=6  out:11
    ensure_broker_port_free  CC=4  out:5
    find_listener_pids  CC=4  out:4
    stop_pids  CC=13  out:10
  packages.vdisplay-agent.src.vdisplay_agent.server  [1 funcs]
    create_app  CC=2  out:7
  packages.vdisplay-agent.src.vdisplay_agent.services.capabilities  [2 funcs]
    diagnostics  CC=1  out:4
    platform_capabilities  CC=5  out:13
  packages.vdisplay-agent.src.vdisplay_agent.services.capture  [5 funcs]
    _capture_all_monitors  CC=2  out:8
    _capture_host  CC=7  out:16
    _capture_session  CC=3  out:13
    _region_from_body  CC=8  out:13
    capture_frame  CC=3  out:6
  packages.vdisplay-agent.src.vdisplay_agent.services.control  [5 funcs]
    _selector_kwargs  CC=1  out:20
    find_controls  CC=2  out:10
    focus_control  CC=2  out:9
    invoke_control  CC=2  out:11
    set_control_value  CC=3  out:13
  packages.vdisplay-agent.src.vdisplay_agent.services.outputs  [1 funcs]
    list_outputs_payload  CC=2  out:4
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler  [5 funcs]
    _capture_virtual_persistent  CC=5  out:12
    _config_from_body  CC=12  out:24
    _ensure_virtual_session  CC=4  out:5
    _recover_screencast  CC=3  out:3
    start_sampler  CC=7  out:13
  packages.vdisplay-agent.src.vdisplay_agent.services.sessions  [12 funcs]
    _session_started  CC=1  out:2
    list_sessions  CC=1  out:2
    screencast_status  CC=3  out:2
    shutdown  CC=4  out:8
    start_browser  CC=3  out:4
    start_mirror  CC=3  out:5
    start_relay  CC=4  out:5
    start_screencast  CC=3  out:4
    start_terminal  CC=5  out:5
    start_virtual  CC=3  out:5
  packages.vdisplay-agent.src.vdisplay_agent.services.tasks  [9 funcs]
    end_sampler_task  CC=1  out:1
    end_screencast_task  CC=1  out:1
    get_task  CC=2  out:3
    heartbeat_task  CC=2  out:3
    list_tasks  CC=3  out:4
    register_session_task  CC=2  out:7
    shutdown_tasks  CC=5  out:7
    stop_task  CC=5  out:5
    unregister_session_task  CC=1  out:1
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
  src.vdisplay.agent_config  [8 funcs]
    _default_agent_base  CC=3  out:4
    _probe_agent_url  CC=3  out:3
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
  src.vdisplay.api  [8 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    info  CC=1  out:2
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.application.errors  [1 funcs]
    error_from_exception  CC=4  out:11
  src.vdisplay.application.executor  [1 funcs]
    execute  CC=6  out:18
  src.vdisplay.application.handlers.control  [1 funcs]
    control_request_body  CC=3  out:3
  src.vdisplay.application.services.capture  [1 funcs]
    capture_screenshot  CC=3  out:3
  src.vdisplay.application.services.sampler  [2 funcs]
    run_sampler  CC=5  out:18
    start_sampler_via_agent  CC=1  out:1
  src.vdisplay.application.session_context  [1 funcs]
    apply_cli_session_args  CC=3  out:6
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
  src.vdisplay.backends.linux_x11_relay  [22 funcs]
    __init__  CC=1  out:3
    adopt_window  CC=12  out:27
    list_adopted  CC=4  out:4
    release_window  CC=6  out:10
    start  CC=2  out:3
    _find_window_id  CC=12  out:11
    _load_stash  CC=5  out:8
    _move_window  CC=1  out:3
    _offscreen_coordinates  CC=1  out:1
    _output_origin  CC=11  out:20
  src.vdisplay.backends.linux_xvfb  [6 funcs]
    _acquire_display  CC=8  out:14
    screenshot_bytes  CC=2  out:2
    start  CC=4  out:6
    _display_candidates  CC=4  out:4
    _probe_display  CC=2  out:2
    _wait_for_display  CC=7  out:10
  src.vdisplay.capture.host  [3 funcs]
    capture_all_monitors  CC=8  out:12
    capture_host_png  CC=13  out:18
    capture_host_to_file  CC=3  out:10
  src.vdisplay.capture.linux_xwd  [5 funcs]
    _capture_xwd_png  CC=1  out:3
    _crop_png  CC=2  out:15
    _is_wayland_session  CC=3  out:4
    capture_display_png  CC=2  out:2
    is_blank_png  CC=8  out:14
  src.vdisplay.capture.portal_screencast  [6 funcs]
    _screencast_multiple  CC=2  out:3
    get_active_screencast  CC=1  out:0
    invalidate_screencast_session  CC=4  out:4
    screencast_stream_region  CC=11  out:11
    start_screencast_session  CC=6  out:7
    stop_screencast_session  CC=2  out:2
  src.vdisplay.capture.providers.engine  [1 funcs]
    list_capture_providers  CC=4  out:6
  src.vdisplay.cli  [2 funcs]
    build_parser  CC=1  out:4
    main  CC=2  out:5
  src.vdisplay.cli_handlers  [1 funcs]
    print_json  CC=1  out:1
  src.vdisplay.client  [9 funcs]
    __init__  CC=2  out:2
    _normalize_payload  CC=1  out:1
    request  CC=3  out:8
    _route_browser_open  CC=4  out:0
    _route_command  CC=7  out:7
    _route_control_command  CC=5  out:0
    _route_outputs_query  CC=4  out:3
    _route_terminal_open  CC=4  out:0
    _route_windows_query  CC=6  out:4
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.all_cmd  [4 funcs]
    handle  CC=1  out:3
    handle_outputs  CC=1  out:3
    register  CC=1  out:4
    register_outputs  CC=1  out:4
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
    _handle_browser_open  CC=2  out:5
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
  src.vdisplay.commands.session  [2 funcs]
    add_root_session_args  CC=1  out:2
    command_request_from_control_args  CC=8  out:32
  src.vdisplay.commands.virtual  [1 funcs]
    handle  CC=6  out:9
  src.vdisplay.commands.windows  [2 funcs]
    handle  CC=1  out:3
    register  CC=1  out:4
  src.vdisplay.control.base  [3 funcs]
    capabilities  CC=2  out:2
    session_kind  CC=2  out:1
    verify_modes  CC=2  out:2
  src.vdisplay.control.browser_engine  [4 funcs]
    browser_engine_profile  CC=3  out:1
    engine_profile_id  CC=2  out:3
    normalize_browser_engine  CC=3  out:6
    resolve_session_browser_engine  CC=3  out:4
  src.vdisplay.control.browser_session_store  [1 funcs]
    session_available  CC=3  out:3
  src.vdisplay.control.descriptors  [5 funcs]
    all_provider_descriptors  CC=1  out:2
    all_selector_extensions  CC=1  out:0
    descriptor_for  CC=1  out:1
    detect_platform_profile  CC=14  out:23
    extension_catalog  CC=8  out:10
  src.vdisplay.control.engine  [3 funcs]
    resolve_provider  CC=1  out:1
    resolve_provider_routing  CC=2  out:2
    resolve_route  CC=2  out:2
  src.vdisplay.control.gui_map  [1 funcs]
    save_gui_map  CC=1  out:4
  src.vdisplay.control.gui_map_export  [1 funcs]
    write_map_artifacts  CC=4  out:14
  src.vdisplay.control.plugins  [10 funcs]
    _bootstrap_builtin_registry  CC=3  out:3
    _register_plugin  CC=1  out:2
    get_provider_registry  CC=3  out:3
    get_registered_descriptor  CC=5  out:3
    iter_provider_names  CC=1  out:2
    list_control_plugins  CC=2  out:3
    load_entry_point_plugins  CC=8  out:12
    register_control_provider  CC=1  out:2
    reset_control_plugins_for_tests  CC=1  out:2
    unregister_control_provider  CC=4  out:6
  src.vdisplay.control.policy  [1 funcs]
    assess_control_capability  CC=7  out:9
  src.vdisplay.control.profile_inference  [3 funcs]
    infer_application_profile  CC=6  out:10
    profile_for  CC=3  out:2
    profile_provider_boost  CC=6  out:4
  src.vdisplay.control.providers.ax_impl  [1 funcs]
    ax_deps_available  CC=3  out:0
  src.vdisplay.control.providers.browser_playwright  [1 funcs]
    _playwright_available  CC=3  out:1
  src.vdisplay.control.providers.browser_session  [1 funcs]
    open  CC=14  out:21
  src.vdisplay.control.providers.terminal_session  [1 funcs]
    default_registry  CC=1  out:0
  src.vdisplay.control.providers.uia_impl  [1 funcs]
    uia_deps_available  CC=3  out:0
  src.vdisplay.control.registry  [4 funcs]
    build  CC=3  out:6
    get_descriptor  CC=2  out:2
    register  CC=2  out:1
    default_provider_registry  CC=1  out:1
  src.vdisplay.control.router  [1 funcs]
    default_router  CC=2  out:1
  src.vdisplay.control.routing_semantics  [1 funcs]
    build_routing_semantics  CC=1  out:8
  src.vdisplay.control.scoring  [37 funcs]
    _all_provider_names  CC=3  out:4
    _apply_routing_boosts  CC=7  out:6
    _atspi_ready  CC=2  out:3
    _ax_ready  CC=2  out:2
    _base_score  CC=2  out:1
    _browser_context_score  CC=4  out:4
    _browser_ready  CC=2  out:2
    _browser_session_check  CC=6  out:4
    _browser_session_ready  CC=5  out:5
    _is_browser_context  CC=3  out:1
  src.vdisplay.control.screenshot_verify  [10 funcs]
    _capture_via_agent  CC=6  out:9
    _maybe_crop_capture  CC=7  out:4
    _region_from_agent_screencast_status  CC=14  out:17
    _region_from_bounds  CC=1  out:2
    _resolve_screencast_stream_region  CC=2  out:3
    _target_region  CC=5  out:1
    capture_control_screenshot  CC=3  out:8
    diff_png_bytes  CC=13  out:15
    enrich_screencast_stream_meta  CC=4  out:4
    verify_screenshot_pair  CC=1  out:4
  src.vdisplay.control.session  [8 funcs]
    _safe_capabilities  CC=4  out:4
    _safe_info  CC=4  out:4
    build_catalog_from_agent_store  CC=11  out:17
    build_catalog_local  CC=4  out:12
    metadata_from_agent_record  CC=1  out:12
    metadata_from_browser_session  CC=1  out:5
    metadata_from_terminal_session  CC=1  out:6
    parse_session_kind  CC=3  out:5
  src.vdisplay.control.vision_disambiguate  [4 funcs]
    filter_by_confidence  CC=4  out:5
    item_confidence  CC=3  out:4
    pick_by_index  CC=3  out:3
    resolve_vision_matches  CC=1  out:4
  src.vdisplay.control.vision_ocr  [15 funcs]
    _box_matches  CC=3  out:2
    _find_anchor_boxes  CC=1  out:2
    _horizontal_overlap  CC=2  out:0
    _match_by_text_fields  CC=13  out:4
    _match_by_vision_anchor  CC=7  out:5
    _normalize  CC=2  out:2
    _vertical_overlap  CC=2  out:0
    anchor_based_find  CC=1  out:1
    anchor_spatial_find  CC=10  out:11
    anchor_spatial_relation  CC=10  out:6
  src.vdisplay.control.vision_preview  [6 funcs]
    _match_kind  CC=5  out:3
    action_pick_index  CC=2  out:2
    build_vision_preview  CC=10  out:13
    preview_available  CC=2  out:0
    preview_matches_from_nodes  CC=7  out:5
    render_match_overlay  CC=10  out:25
  src.vdisplay.control.vision_template  [2 funcs]
    template_anchor_find  CC=2  out:11
    template_available  CC=2  out:0
  src.vdisplay.discovery  [13 funcs]
    _attach_output_nl  CC=2  out:3
    _display_hint  CC=3  out:2
    _display_socket_exists  CC=2  out:5
    _list_monitors  CC=6  out:10
    _looks_like_xvfb_only  CC=4  out:4
    _merge_output_metadata  CC=3  out:18
    _parse_xrandr_query  CC=8  out:12
    diagnose_display  CC=10  out:19
    find_window_suggestions  CC=2  out:2
    list_monitors  CC=1  out:1
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
  src.vdisplay.windows.query  [5 funcs]
    find_companion_frames  CC=8  out:10
    find_windows  CC=6  out:5
    inspect_window  CC=9  out:21
    list_windows_enriched  CC=2  out:5
    pick_best_window  CC=8  out:3

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
# nodes: 465 | edges: 500 | modules: 114
# CC̄=3.5

HUBS[20]:
  packages.vdisplay-agent.src.vdisplay_agent.routes.control.register_routes
    CC=1  in:0  out:53  total:53
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
    CC=3  in:44  out:2  total:46
  src.vdisplay.commands.control.register
    CC=1  in:0  out:46  total:46
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=14  in:13  out:27  total:40
  src.vdisplay.utils.run_command
    CC=2  in:33  out:4  total:37
  src.vdisplay.cli_handlers.print_json
    CC=1  in:36  out:1  total:37
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  examples.agent-broker.broker_demo.main
    CC=9  in:0  out:35  total:35
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  src.vdisplay.commands.session.command_request_from_control_args
    CC=8  in:1  out:32  total:33
  packages.vdisplay-agent.src.vdisplay_agent.routes.health.register_routes
    CC=1  in:0  out:33  total:33
  src.vdisplay.discovery.resolve_host_display
    CC=11  in:26  out:7  total:33
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:32  total:32
  examples.control-plane.control_demo.run_browser_demo
    CC=6  in:1  out:30  total:31
  src.vdisplay.commands.map.handle
    CC=7  in:0  out:31  total:31
  examples.host-mirror.mirror_demo.main
    CC=7  in:0  out:31  total:31
  src.vdisplay.control.descriptors.detect_platform_profile
    CC=14  in:8  out:23  total:31
  src.vdisplay.agent_config.resolve_agent_url
    CC=6  in:24  out:5  total:29
  packages.vdisplay-agent.src.vdisplay_agent.envelope.json_error
    CC=5  in:21  out:8  total:29

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
  packages.vdisplay-agent.src.vdisplay_agent.cli  [1 funcs]
    main  CC=4  out:18
  packages.vdisplay-agent.src.vdisplay_agent.envelope  [7 funcs]
    agent_meta  CC=1  out:0
    failure  CC=3  out:2
    from_runtime  CC=3  out:8
    json_error  CC=5  out:8
    json_from_runtime  CC=1  out:2
    json_success  CC=1  out:2
    success  CC=2  out:1
  packages.vdisplay-agent.src.vdisplay_agent.routes  [1 funcs]
    register_all_routes  CC=2  out:3
  packages.vdisplay-agent.src.vdisplay_agent.routes.auth  [2 funcs]
    expected_token  CC=2  out:2
    make_check_auth  CC=1  out:5
  packages.vdisplay-agent.src.vdisplay_agent.routes.capture  [1 funcs]
    register_routes  CC=1  out:6
  packages.vdisplay-agent.src.vdisplay_agent.routes.control  [1 funcs]
    register_routes  CC=1  out:53
  packages.vdisplay-agent.src.vdisplay_agent.routes.health  [1 funcs]
    register_routes  CC=1  out:33
  packages.vdisplay-agent.src.vdisplay_agent.routes.sampler  [1 funcs]
    register_routes  CC=1  out:18
  packages.vdisplay-agent.src.vdisplay_agent.routes.tasks  [1 funcs]
    register_routes  CC=1  out:27
  packages.vdisplay-agent.src.vdisplay_agent.routes.windows  [1 funcs]
    register_routes  CC=1  out:12
  packages.vdisplay-agent.src.vdisplay_agent.runtime  [1 funcs]
    list_control_plugins  CC=1  out:1
  packages.vdisplay-agent.src.vdisplay_agent.serve_port  [8 funcs]
    _parse_ss_pids  CC=2  out:4
    _pid_alive  CC=3  out:1
    _pids_from_lsof  CC=5  out:6
    _pids_from_ss  CC=3  out:2
    _probe_is_vdisplay_agent  CC=6  out:11
    ensure_broker_port_free  CC=4  out:5
    find_listener_pids  CC=4  out:4
    stop_pids  CC=13  out:10
  packages.vdisplay-agent.src.vdisplay_agent.server  [1 funcs]
    create_app  CC=2  out:7
  packages.vdisplay-agent.src.vdisplay_agent.services.capabilities  [2 funcs]
    diagnostics  CC=1  out:4
    platform_capabilities  CC=5  out:13
  packages.vdisplay-agent.src.vdisplay_agent.services.capture  [5 funcs]
    _capture_all_monitors  CC=2  out:8
    _capture_host  CC=7  out:16
    _capture_session  CC=3  out:13
    _region_from_body  CC=8  out:13
    capture_frame  CC=3  out:6
  packages.vdisplay-agent.src.vdisplay_agent.services.control  [5 funcs]
    _selector_kwargs  CC=1  out:20
    find_controls  CC=2  out:10
    focus_control  CC=2  out:9
    invoke_control  CC=2  out:11
    set_control_value  CC=3  out:13
  packages.vdisplay-agent.src.vdisplay_agent.services.outputs  [1 funcs]
    list_outputs_payload  CC=2  out:4
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler  [5 funcs]
    _capture_virtual_persistent  CC=5  out:12
    _config_from_body  CC=12  out:24
    _ensure_virtual_session  CC=4  out:5
    _recover_screencast  CC=3  out:3
    start_sampler  CC=7  out:13
  packages.vdisplay-agent.src.vdisplay_agent.services.sessions  [12 funcs]
    _session_started  CC=1  out:2
    list_sessions  CC=1  out:2
    screencast_status  CC=3  out:2
    shutdown  CC=4  out:8
    start_browser  CC=3  out:4
    start_mirror  CC=3  out:5
    start_relay  CC=4  out:5
    start_screencast  CC=3  out:4
    start_terminal  CC=5  out:5
    start_virtual  CC=3  out:5
  packages.vdisplay-agent.src.vdisplay_agent.services.tasks  [9 funcs]
    end_sampler_task  CC=1  out:1
    end_screencast_task  CC=1  out:1
    get_task  CC=2  out:3
    heartbeat_task  CC=2  out:3
    list_tasks  CC=3  out:4
    register_session_task  CC=2  out:7
    shutdown_tasks  CC=5  out:7
    stop_task  CC=5  out:5
    unregister_session_task  CC=1  out:1
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
  src.vdisplay.agent_config  [8 funcs]
    _default_agent_base  CC=3  out:4
    _probe_agent_url  CC=3  out:3
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
  src.vdisplay.api  [8 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    info  CC=1  out:2
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.application.errors  [1 funcs]
    error_from_exception  CC=4  out:11
  src.vdisplay.application.executor  [1 funcs]
    execute  CC=6  out:18
  src.vdisplay.application.handlers.control  [1 funcs]
    control_request_body  CC=3  out:3
  src.vdisplay.application.services.capture  [1 funcs]
    capture_screenshot  CC=3  out:3
  src.vdisplay.application.services.sampler  [2 funcs]
    run_sampler  CC=5  out:18
    start_sampler_via_agent  CC=1  out:1
  src.vdisplay.application.session_context  [1 funcs]
    apply_cli_session_args  CC=3  out:6
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
  src.vdisplay.backends.linux_x11_relay  [22 funcs]
    __init__  CC=1  out:3
    adopt_window  CC=12  out:27
    list_adopted  CC=4  out:4
    release_window  CC=6  out:10
    start  CC=2  out:3
    _find_window_id  CC=12  out:11
    _load_stash  CC=5  out:8
    _move_window  CC=1  out:3
    _offscreen_coordinates  CC=1  out:1
    _output_origin  CC=11  out:20
  src.vdisplay.backends.linux_xvfb  [6 funcs]
    _acquire_display  CC=8  out:14
    screenshot_bytes  CC=2  out:2
    start  CC=4  out:6
    _display_candidates  CC=4  out:4
    _probe_display  CC=2  out:2
    _wait_for_display  CC=7  out:10
  src.vdisplay.capture.host  [3 funcs]
    capture_all_monitors  CC=8  out:12
    capture_host_png  CC=13  out:18
    capture_host_to_file  CC=3  out:10
  src.vdisplay.capture.linux_xwd  [5 funcs]
    _capture_xwd_png  CC=1  out:3
    _crop_png  CC=2  out:15
    _is_wayland_session  CC=3  out:4
    capture_display_png  CC=2  out:2
    is_blank_png  CC=8  out:14
  src.vdisplay.capture.portal_screencast  [6 funcs]
    _screencast_multiple  CC=2  out:3
    get_active_screencast  CC=1  out:0
    invalidate_screencast_session  CC=4  out:4
    screencast_stream_region  CC=11  out:11
    start_screencast_session  CC=6  out:7
    stop_screencast_session  CC=2  out:2
  src.vdisplay.capture.providers.engine  [1 funcs]
    list_capture_providers  CC=4  out:6
  src.vdisplay.cli  [2 funcs]
    build_parser  CC=1  out:4
    main  CC=2  out:5
  src.vdisplay.cli_handlers  [1 funcs]
    print_json  CC=1  out:1
  src.vdisplay.client  [9 funcs]
    __init__  CC=2  out:2
    _normalize_payload  CC=1  out:1
    request  CC=3  out:8
    _route_browser_open  CC=4  out:0
    _route_command  CC=7  out:7
    _route_control_command  CC=5  out:0
    _route_outputs_query  CC=4  out:3
    _route_terminal_open  CC=4  out:0
    _route_windows_query  CC=6  out:4
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.all_cmd  [4 funcs]
    handle  CC=1  out:3
    handle_outputs  CC=1  out:3
    register  CC=1  out:4
    register_outputs  CC=1  out:4
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
    _handle_browser_open  CC=2  out:5
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
  src.vdisplay.commands.session  [2 funcs]
    add_root_session_args  CC=1  out:2
    command_request_from_control_args  CC=8  out:32
  src.vdisplay.commands.virtual  [1 funcs]
    handle  CC=6  out:9
  src.vdisplay.commands.windows  [2 funcs]
    handle  CC=1  out:3
    register  CC=1  out:4
  src.vdisplay.control.base  [3 funcs]
    capabilities  CC=2  out:2
    session_kind  CC=2  out:1
    verify_modes  CC=2  out:2
  src.vdisplay.control.browser_engine  [4 funcs]
    browser_engine_profile  CC=3  out:1
    engine_profile_id  CC=2  out:3
    normalize_browser_engine  CC=3  out:6
    resolve_session_browser_engine  CC=3  out:4
  src.vdisplay.control.browser_session_store  [1 funcs]
    session_available  CC=3  out:3
  src.vdisplay.control.descriptors  [5 funcs]
    all_provider_descriptors  CC=1  out:2
    all_selector_extensions  CC=1  out:0
    descriptor_for  CC=1  out:1
    detect_platform_profile  CC=14  out:23
    extension_catalog  CC=8  out:10
  src.vdisplay.control.engine  [3 funcs]
    resolve_provider  CC=1  out:1
    resolve_provider_routing  CC=2  out:2
    resolve_route  CC=2  out:2
  src.vdisplay.control.gui_map  [1 funcs]
    save_gui_map  CC=1  out:4
  src.vdisplay.control.gui_map_export  [1 funcs]
    write_map_artifacts  CC=4  out:14
  src.vdisplay.control.plugins  [10 funcs]
    _bootstrap_builtin_registry  CC=3  out:3
    _register_plugin  CC=1  out:2
    get_provider_registry  CC=3  out:3
    get_registered_descriptor  CC=5  out:3
    iter_provider_names  CC=1  out:2
    list_control_plugins  CC=2  out:3
    load_entry_point_plugins  CC=8  out:12
    register_control_provider  CC=1  out:2
    reset_control_plugins_for_tests  CC=1  out:2
    unregister_control_provider  CC=4  out:6
  src.vdisplay.control.policy  [1 funcs]
    assess_control_capability  CC=7  out:9
  src.vdisplay.control.profile_inference  [3 funcs]
    infer_application_profile  CC=6  out:10
    profile_for  CC=3  out:2
    profile_provider_boost  CC=6  out:4
  src.vdisplay.control.providers.ax_impl  [1 funcs]
    ax_deps_available  CC=3  out:0
  src.vdisplay.control.providers.browser_playwright  [1 funcs]
    _playwright_available  CC=3  out:1
  src.vdisplay.control.providers.browser_session  [1 funcs]
    open  CC=14  out:21
  src.vdisplay.control.providers.terminal_session  [1 funcs]
    default_registry  CC=1  out:0
  src.vdisplay.control.providers.uia_impl  [1 funcs]
    uia_deps_available  CC=3  out:0
  src.vdisplay.control.registry  [4 funcs]
    build  CC=3  out:6
    get_descriptor  CC=2  out:2
    register  CC=2  out:1
    default_provider_registry  CC=1  out:1
  src.vdisplay.control.router  [1 funcs]
    default_router  CC=2  out:1
  src.vdisplay.control.routing_semantics  [1 funcs]
    build_routing_semantics  CC=1  out:8
  src.vdisplay.control.scoring  [37 funcs]
    _all_provider_names  CC=3  out:4
    _apply_routing_boosts  CC=7  out:6
    _atspi_ready  CC=2  out:3
    _ax_ready  CC=2  out:2
    _base_score  CC=2  out:1
    _browser_context_score  CC=4  out:4
    _browser_ready  CC=2  out:2
    _browser_session_check  CC=6  out:4
    _browser_session_ready  CC=5  out:5
    _is_browser_context  CC=3  out:1
  src.vdisplay.control.screenshot_verify  [10 funcs]
    _capture_via_agent  CC=6  out:9
    _maybe_crop_capture  CC=7  out:4
    _region_from_agent_screencast_status  CC=14  out:17
    _region_from_bounds  CC=1  out:2
    _resolve_screencast_stream_region  CC=2  out:3
    _target_region  CC=5  out:1
    capture_control_screenshot  CC=3  out:8
    diff_png_bytes  CC=13  out:15
    enrich_screencast_stream_meta  CC=4  out:4
    verify_screenshot_pair  CC=1  out:4
  src.vdisplay.control.session  [8 funcs]
    _safe_capabilities  CC=4  out:4
    _safe_info  CC=4  out:4
    build_catalog_from_agent_store  CC=11  out:17
    build_catalog_local  CC=4  out:12
    metadata_from_agent_record  CC=1  out:12
    metadata_from_browser_session  CC=1  out:5
    metadata_from_terminal_session  CC=1  out:6
    parse_session_kind  CC=3  out:5
  src.vdisplay.control.vision_disambiguate  [4 funcs]
    filter_by_confidence  CC=4  out:5
    item_confidence  CC=3  out:4
    pick_by_index  CC=3  out:3
    resolve_vision_matches  CC=1  out:4
  src.vdisplay.control.vision_ocr  [15 funcs]
    _box_matches  CC=3  out:2
    _find_anchor_boxes  CC=1  out:2
    _horizontal_overlap  CC=2  out:0
    _match_by_text_fields  CC=13  out:4
    _match_by_vision_anchor  CC=7  out:5
    _normalize  CC=2  out:2
    _vertical_overlap  CC=2  out:0
    anchor_based_find  CC=1  out:1
    anchor_spatial_find  CC=10  out:11
    anchor_spatial_relation  CC=10  out:6
  src.vdisplay.control.vision_preview  [6 funcs]
    _match_kind  CC=5  out:3
    action_pick_index  CC=2  out:2
    build_vision_preview  CC=10  out:13
    preview_available  CC=2  out:0
    preview_matches_from_nodes  CC=7  out:5
    render_match_overlay  CC=10  out:25
  src.vdisplay.control.vision_template  [2 funcs]
    template_anchor_find  CC=2  out:11
    template_available  CC=2  out:0
  src.vdisplay.discovery  [13 funcs]
    _attach_output_nl  CC=2  out:3
    _display_hint  CC=3  out:2
    _display_socket_exists  CC=2  out:5
    _list_monitors  CC=6  out:10
    _looks_like_xvfb_only  CC=4  out:4
    _merge_output_metadata  CC=3  out:18
    _parse_xrandr_query  CC=8  out:12
    diagnose_display  CC=10  out:19
    find_window_suggestions  CC=2  out:2
    list_monitors  CC=1  out:1
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
  src.vdisplay.windows.query  [5 funcs]
    find_companion_frames  CC=8  out:10
    find_windows  CC=6  out:5
    inspect_window  CC=9  out:21
    list_windows_enriched  CC=2  out:5
    pick_best_window  CC=8  out:3

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
# code2llm | 253f 34318L | python:199,json:20,toml:11,shell:7,yaml:5,yml:5,txt:1 | 2026-06-10
# generated in 0.08s
# CC̅=3.5 | critical:0/1497 | dups:0 | cycles:0

HEALTH[0]: ok

REFACTOR[0]: none needed

PIPELINES[680]:
  [1] Src [main]: main → create_server
      PURITY: 100% pure
  [2] Src [create_server]: create_server → resolve_agent_url → _probe_default_agent → _probe_agent_url
      PURITY: 100% pure
  [3] Src [main]: main → _main_legacy → execute_dsl_line → dispatch → ...(5 more)
      PURITY: 100% pure
  [4] Src [_parse_windows]: _parse_windows → _with_display → pick_flag
      PURITY: 100% pure
  [5] Src [_parse_screenshot]: _parse_screenshot → pick_flag
      PURITY: 100% pure
  [6] Src [_parse_virtual_start]: _parse_virtual_start → pick_flag
      PURITY: 100% pure
  [7] Src [_parse_launch]: _parse_launch → pick_flag
      PURITY: 100% pure
  [8] Src [_parse_mirror]: _parse_mirror → pick_flag
      PURITY: 100% pure
  [9] Src [_parse_adopt]: _parse_adopt → pick_flag
      PURITY: 100% pure
  [10] Src [_parse_controls_list]: _parse_controls_list → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [11] Src [_parse_controls_find]: _parse_controls_find → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [12] Src [_parse_control_click]: _parse_control_click → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [13] Src [_parse_control_focus]: _parse_control_focus → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [14] Src [_parse_control_set_value]: _parse_control_set_value → _parse_control_common → _with_display → pick_flag
      PURITY: 100% pure
  [15] Src [_parse_diagnose_control]: _parse_diagnose_control → _with_display → pick_flag
      PURITY: 100% pure
  [16] Src [_parse_browser_open]: _parse_browser_open → pick_flag
      PURITY: 100% pure
  [17] Src [_parse_terminal_open]: _parse_terminal_open → pick_flag
      PURITY: 100% pure
  [18] Src [_parse_release]: _parse_release → pick_flag
      PURITY: 100% pure
  [19] Src [_screenshot_to_text]: _screenshot_to_text
      PURITY: 100% pure
  [20] Src [_mirror_to_text]: _mirror_to_text
      PURITY: 100% pure
  [21] Src [_controls_list_to_text]: _controls_list_to_text
      PURITY: 100% pure
  [22] Src [_browser_open_to_text]: _browser_open_to_text
      PURITY: 100% pure
  [23] Src [_terminal_open_to_text]: _terminal_open_to_text
      PURITY: 100% pure
  [24] Src [_control_to_text]: _control_to_text
      PURITY: 100% pure
  [25] Src [handle_screenshot]: handle_screenshot → _ok
      PURITY: 100% pure
  [26] Src [handle_virtual_start]: handle_virtual_start → _ok
      PURITY: 100% pure
  [27] Src [handle_mirror]: handle_mirror → resolve_host_display → _display_socket_exists
      PURITY: 100% pure
  [28] Src [handle_adopt]: handle_adopt → _ok
      PURITY: 100% pure
  [29] Src [handle_release]: handle_release → _ok
      PURITY: 100% pure
  [30] Src [handle_health]: handle_health
      PURITY: 100% pure
  [31] Src [handle_info]: handle_info
      PURITY: 100% pure
  [32] Src [handle_outputs]: handle_outputs → handle_monitors
      PURITY: 100% pure
  [33] Src [handle_all]: handle_all
      PURITY: 100% pure
  [34] Src [handle_capabilities]: handle_capabilities
      PURITY: 100% pure
  [35] Src [handle_validate]: handle_validate
      PURITY: 100% pure
  [36] Src [main]: main → dispatch → _dispatch_legacy → validate_command_dict → ...(3 more)
      PURITY: 100% pure
  [37] Src [main]: main → uri_to_dsl
      PURITY: 100% pure
  [38] Src [main]: main → create_app → resolve_agent_url → _probe_default_agent → ...(1 more)
      PURITY: 100% pure
  [39] Src [main]: main → run_nl_prompt → nl_to_dsl → parse_display
      PURITY: 100% pure
  [40] Src [parse_display]: parse_display
      PURITY: 100% pure
  [41] Src [platform_capabilities]: platform_capabilities
      PURITY: 100% pure
  [42] Src [diagnostics]: diagnostics
      PURITY: 100% pure
  [43] Src [outputs]: outputs
      PURITY: 100% pure
  [44] Src [start_virtual]: start_virtual
      PURITY: 100% pure
  [45] Src [start_mirror]: start_mirror
      PURITY: 100% pure
  [46] Src [start_relay]: start_relay
      PURITY: 100% pure
  [47] Src [start_terminal]: start_terminal
      PURITY: 100% pure
  [48] Src [start_browser]: start_browser
      PURITY: 100% pure
  [49] Src [start_screencast]: start_screencast
      PURITY: 100% pure
  [50] Src [stop_screencast]: stop_screencast
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=3.7    ←in:0  →out:0
  │ !! scoring                    801L  2C   40m  CC=12     ←6
  │ !! portal_screencast          779L  1C   34m  CC=11     ←6
  │ !! control                    763L  0C   23m  CC=14     ←0
  │ !! provider                   715L  1C   37m  CC=12     ←0
  │ !! verifier                   567L  3C   24m  CC=13     ←1
  │ !! host                       555L  0C   15m  CC=14     ←6
  │ !! gui_map_diff               500L  3C   18m  CC=14     ←1
  │ !! session_recorder           500L  3C   25m  CC=13     ←1
  │ verify                     498L  0C   21m  CC=12     ←1
  │ linux_x11_relay            478L  2C   24m  CC=12     ←0
  │ descriptors                464L  5C   11m  CC=14     ←9
  │ client                     422L  1C   40m  CC=7      ←0
  │ atspi_impl                 413L  0C   19m  CC=8      ←1
  │ commands                   370L  4C   11m  CC=9      ←0
  │ discovery                  363L  0C   14m  CC=11     ←21
  │ selector                   347L  1C   18m  CC=14     ←9
  │ browser_playwright         339L  3C   30m  CC=14     ←2
  │ session                    326L  0C   12m  CC=4      ←0
  │ linux_xwd                  320L  0C   21m  CC=12     ←15
  │ vision_ocr                 315L  1C   16m  CC=13     ←6
  │ uia_impl                   299L  4C   29m  CC=13     ←3
  │ local                      291L  0C   21m  CC=4      ←1
  │ sampler_loop               280L  3C   12m  CC=10     ←1
  │ map                        275L  0C    9m  CC=7      ←0
  │ router                     271L  2C   10m  CC=9      ←2
  │ profile_inference          271L  1C   11m  CC=14     ←3
  │ ax_impl                    269L  4C   27m  CC=10     ←2
  │ screenshot_verify          265L  0C   10m  CC=14     ←5
  │ terminal_screen            260L  3C   14m  CC=7      ←3
  │ linux_x11_mirror           259L  1C   17m  CC=10     ←0
  │ vision_template            258L  1C   10m  CC=11     ←4
  │ browser_session            246L  2C   13m  CC=14     ←3
  │ gui_map                    245L  6C   16m  CC=9      ←3
  │ gui_map_build              243L  0C   11m  CC=9      ←3
  │ policy                     242L  1C    8m  CC=7      ←2
  │ agent                      241L  0C   22m  CC=6      ←1
  │ atspi                      240L  1C   15m  CC=8      ←0
  │ discovery                  239L  0C   11m  CC=4      ←0
  │ vision_preview             238L  2C   11m  CC=10     ←1
  │ vision_llm                 236L  1C   12m  CC=12     ←2
  │ terminal_session           227L  2C   16m  CC=7      ←6
  │ portal                     221L  1C    7m  CC=11     ←1
  │ coords                     219L  0C    8m  CC=12     ←1
  │ session                    216L  3C   11m  CC=11     ←2
  │ query                      209L  0C    6m  CC=9      ←4
  │ browser_session_store      196L  1C   14m  CC=7      ←2
  │ api                        193L  3C   32m  CC=6      ←4
  │ models                     187L  9C    7m  CC=4      ←0
  │ capture                    182L  0C    5m  CC=9      ←1
  │ gui_map_export             179L  0C    7m  CC=8      ←1
  │ filter                     173L  0C   12m  CC=14     ←2
  │ uia                        169L  1C   10m  CC=6      ←0
  │ ax                         169L  1C   10m  CC=6      ←0
  │ linux_xvfb                 164L  1C   14m  CC=8      ←0
  │ contracts                  164L  5C    7m  CC=4      ←1
  │ plugins                    163L  1C   11m  CC=8      ←6
  │ control                    159L  0C   10m  CC=5      ←0
  │ nl                         158L  0C    8m  CC=14     ←3
  │ nlp                        158L  0C   14m  CC=10     ←2
  │ routing_semantics          158L  1C    8m  CC=7      ←4
  │ agent                      155L  0C    6m  CC=5      ←0
  │ x11                        150L  1C   13m  CC=9      ←0
  │ terminal                   147L  1C   13m  CC=14     ←0
  │ policy                     140L  1C    4m  CC=11     ←2
  │ common                     137L  0C    9m  CC=2      ←9
  │ sampler                    132L  0C    8m  CC=9      ←0
  │ img2nl_enrich              124L  0C    6m  CC=12     ←0
  │ registry                   117L  1C   14m  CC=3      ←2
  │ linux_ydotool              114L  1C    9m  CC=8      ←0
  │ relay                      110L  0C    3m  CC=5      ←0
  │ scan                       110L  0C    7m  CC=6      ←2
  │ sampler                    109L  1C    3m  CC=5      ←1
  │ gui_map_resolve            109L  0C    9m  CC=6      ←2
  │ normalize                  103L  0C    7m  CC=14     ←1
  │ artifacts                  102L  0C    5m  CC=13     ←1
  │ engine                      99L  0C    6m  CC=11     ←4
  │ map                         98L  0C    2m  CC=7      ←0
  │ drm                         92L  1C    5m  CC=11     ←0
  │ payloads                    86L  0C    5m  CC=1      ←2
  │ runtime                     86L  1C    7m  CC=6      ←3
  │ virtual                     81L  0C    2m  CC=6      ←0
  │ session                     79L  0C    2m  CC=8      ←2
  │ vision_disambiguate         78L  1C    6m  CC=4      ←4
  │ fbdev                       77L  1C    5m  CC=7      ←0
  │ capabilities                76L  1C    1m  CC=1      ←0
  │ control                     72L  0C    4m  CC=3      ←3
  │ agent_config                71L  0C    8m  CC=6      ←16
  │ base                        69L  1C   10m  CC=2      ←0
  │ __init__                    69L  0C    0m  CC=0.0    ←0
  │ utils                       68L  0C    4m  CC=4      ←15
  │ mss                         68L  1C    5m  CC=8      ←0
  │ linux_xdotool               68L  1C    9m  CC=3      ←0
  │ engine                      67L  0C    3m  CC=2      ←1
  │ executor                    67L  0C    2m  CC=6      ←5
  │ base                        64L  1C   11m  CC=1      ←0
  │ browser_engine              55L  1C    4m  CC=3      ←5
  │ mirror                      53L  0C    2m  CC=3      ←0
  │ screenshot                  53L  0C    2m  CC=1      ←0
  │ diagnose                    53L  0C    2m  CC=5      ←0
  │ info                        51L  0C    1m  CC=6      ←0
  │ all_cmd                     46L  0C    4m  CC=1      ←0
  │ __init__                    46L  0C    1m  CC=2      ←1
  │ __init__                    46L  0C    0m  CC=0.0    ←0
  │ rank                        43L  0C    5m  CC=9      ←1
  │ errors                      39L  2C    2m  CC=4      ←3
  │ cli                         36L  0C    2m  CC=2      ←0
  │ x11                         35L  1C    4m  CC=4      ←0
  │ cli_handlers                34L  0C    6m  CC=1      ←13
  │ mirror_stub                 34L  1C    4m  CC=1      ←0
  │ session_context             32L  0C    2m  CC=6      ←2
  │ agent_dispatch              30L  0C    2m  CC=2      ←0
  │ windows                     29L  0C    2m  CC=1      ←0
  │ resolve                     27L  1C    4m  CC=4      ←1
  │ models                      26L  2C    0m  CC=0.0    ←0
  │ action_bounds               24L  0C    2m  CC=2      ←3
  │ nlp                         23L  0C    2m  CC=2      ←0
  │ timing                      23L  0C    2m  CC=2      ←2
  │ base                        22L  2C    3m  CC=1      ←0
  │ monitors                    19L  0C    2m  CC=1      ←0
  │ constants                   19L  0C    0m  CC=0.0    ←0
  │ __init__                    18L  0C    0m  CC=0.0    ←0
  │ agent_envelope              17L  0C    1m  CC=6      ←1
  │ info                        16L  0C    2m  CC=1      ←0
  │ verify_strategy             16L  1C    0m  CC=0.0    ←0
  │ session_kind                15L  1C    0m  CC=0.0    ←0
  │ __init__                    15L  0C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    1m  CC=2      ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ __init__                    11L  0C    0m  CC=0.0    ←0
  │ exceptions                  10L  3C    0m  CC=0.0    ←0
  │ base                         9L  1C    1m  CC=1      ←0
  │ io                           7L  0C    1m  CC=1      ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  packages/                       CC̄=2.9    ←in:0  →out:0
  │ grammar                    406L  0C   30m  CC=11     ←1
  │ sessions                   262L  0C   12m  CC=6      ←0
  │ task_store                 197L  3C   10m  CC=7      ←1
  │ sampler                    183L  0C    7m  CC=12     ←0
  │ tasks                      181L  0C   13m  CC=5      ←0
  │ serve_port                 146L  0C    8m  CC=13     ←2
  │ runtime                    145L  1C   33m  CC=1      ←2
  │ bus                        137L  0C    4m  CC=14     ←7
  │ session                    136L  0C    1m  CC=1      ←0
  │ control                    122L  0C    1m  CC=1      ←0
  │ command                    120L  0C    7m  CC=3      ←0
  │ query                      115L  0C    8m  CC=4      ←1
  │ control                    113L  0C    8m  CC=4      ←0
  │ capture                     96L  0C    5m  CC=8      ←0
  │ server                      95L  0C    1m  CC=1      ←0
  │ app                         87L  0C    1m  CC=2      ←3
  │ envelope                    85L  0C    9m  CC=6      ←7
  │ schemas                     84L  0C    0m  CC=0.0    ←0
  │ health                      76L  0C    2m  CC=2      ←0
  │ cli                         70L  0C    3m  CC=10     ←0
  │ tasks                       69L  0C    1m  CC=1      ←0
  │ session_store               65L  2C    5m  CC=5      ←1
  │ capabilities                56L  0C    2m  CC=5      ←0
  │ schema_registry             53L  0C    4m  CC=3      ←3
  │ sampler                     47L  0C    1m  CC=1      ←0
  │ cli                         43L  0C    1m  CC=4      ←0
  │ cli                         41L  0C    1m  CC=7      ←0
  │ windows                     41L  0C    1m  CC=1      ←0
  │ cli                         35L  0C    1m  CC=3      ←0
  │ cli                         34L  0C    1m  CC=7      ←0
  │ relay                       32L  0C    2m  CC=6      ←0
  │ capture                     32L  0C    1m  CC=1      ←0
  │ decode                      31L  0C    1m  CC=7      ←1
  │ windows                     31L  0C    1m  CC=8      ←0
  │ cli                         30L  0C    1m  CC=4      ←0
  │ server                      30L  0C    1m  CC=2      ←0
  │ control_set_value.schema.json    30L  0C    0m  CC=0.0    ←0
  │ control_click.schema.json    29L  0C    0m  CC=0.0    ←0
  │ control_focus.schema.json    29L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              28L  0C    0m  CC=0.0    ←0
  │ result                      26L  1C    1m  CC=1      ←0
  │ controls_find.schema.json    25L  0C    0m  CC=0.0    ←0
  │ auth                        24L  0C    2m  CC=2      ←1
  │ cli                         23L  0C    2m  CC=2      ←0
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
  │
  examples/                       CC̄=2.6    ←in:0  →out:0
  │ control_demo               172L  0C    5m  CC=6      ←0
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
  │ pyproject.toml             160L  0C    0m  CC=0.0    ←0
  │ koru.yaml                  141L  0C    0m  CC=0.0    ←0
  │ app.vql.json               127L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │
  maps/                           CC̄=0.0    ←in:0  →out:0
  │ !! pycharm-chat.json         2503L  0C    0m  CC=0.0    ←0
  │
  brain/                          CC̄=0.0    ←in:0  →out:0
  │ scratch_atspi               18L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                              src.vdisplay      packages.vdisplay-agent        packages.dsl2vdisplay              examples.common       packages.rest2vdisplay        packages.mcp2vdisplay         examples.host-mirror          examples.host-relay   examples.control-plugin-ax  examples.control-plugin-uia            examples.ci-agent      examples.control-plugin    examples.headless-virtual        packages.cli2vdisplay        packages.nlp2vdisplay
                 src.vdisplay                           ──                            4                            6                           ←1                            1                           ←4                           ←3                           ←3                           ←1                           ←1                                                         1                                                                                     ←1  hub
      packages.vdisplay-agent                           28                           ──                                                                                      1                                                                                                                                                                                                                                                                                                    !! fan-out
        packages.dsl2vdisplay                            6                                                        ──                                                        ←4                           ←2                                                                                                                                                                                                                                      ←2                               hub
              examples.common                            1                                                                                     ──                                                                                     ←3                           ←3                                                                                     ←2                                                        ←2                                                            hub
       packages.rest2vdisplay                            2                           ←1                            4                                                        ──                                                                                                                                                                                                                                                                                                  
        packages.mcp2vdisplay                            4                                                         2                                                                                     ──                                                                                                                                                                                                                                                                    1
         examples.host-mirror                            3                                                                                      3                                                                                     ──                                                                                                                                                                                                                                        
          examples.host-relay                            3                                                                                      3                                                                                                                  ──                                                                                                                                                                                                           
   examples.control-plugin-ax                            1                                                                                                                                                                                                                                      ──                            2                                                                                                                                                 
  examples.control-plugin-uia                            1                                                                                                                                                                                                                                      ←2                           ──                                                                                                                                                 
            examples.ci-agent                                                                                                                   2                                                                                                                                                                                                         ──                                                                                                                    
      examples.control-plugin                            1                                                                                                                                                                                                                                                                                                                             ──                                                                                       
    examples.headless-virtual                                                                                                                   2                                                                                                                                                                                                                                                                   ──                                                          
        packages.cli2vdisplay                                                                                      2                                                                                                                                                                                                                                                                                                                             ──                             
        packages.nlp2vdisplay                            1                                                                                                                                               ←1                                                                                                                                                                                                                                                                   ──
  CYCLES: none
  HUB: examples.common/ (fan-in=10)
  HUB: src.vdisplay/ (fan-in=53)
  HUB: packages.dsl2vdisplay/ (fan-in=15)
  SMELL: packages.vdisplay-agent/ fan-out=29 → split needed
  SMELL: src.vdisplay/ fan-out=12 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 43 groups | 198f 27957L | 2026-06-10

SUMMARY:
  files_scanned: 198
  total_lines:   27957
  dup_groups:    43
  dup_fragments: 100
  saved_lines:   427
  scan_ms:       3619

HOTSPOTS[7] (files with most duplication):
  src/vdisplay/control/scoring.py  dup=105L  groups=3  frags=7  (0.4%)
  src/vdisplay/control/providers/ax.py  dup=76L  groups=6  frags=6  (0.3%)
  src/vdisplay/control/providers/uia.py  dup=76L  groups=6  frags=6  (0.3%)
  src/vdisplay/payloads.py  dup=46L  groups=1  frags=2  (0.2%)
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py  dup=34L  groups=1  frags=2  (0.1%)
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py  dup=30L  groups=2  frags=4  (0.1%)
  src/vdisplay/client.py  dup=24L  groups=1  frags=2  (0.1%)

DUPLICATES[43] (ranked by impact):
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
      src/vdisplay/application/handlers/agent.py:181-184  (_controls_list)
      src/vdisplay/application/handlers/agent.py:187-190  (_controls_find)
      src/vdisplay/application/handlers/agent.py:193-196  (_control_click)
      src/vdisplay/application/handlers/agent.py:199-202  (_control_focus)
      src/vdisplay/application/handlers/agent.py:205-208  (_control_set_value)
  [83f6aff43414a50f]   STRU  _uia_ready  L=7 N=3 saved=14 sim=1.00
      src/vdisplay/control/scoring.py:119-125  (_uia_ready)
      src/vdisplay/control/scoring.py:128-134  (_ax_ready)
      src/vdisplay/control/scoring.py:137-143  (_browser_ready)
  [3930b9c0e70097f2]   EXAC  to_dict  L=4 N=4 saved=12 sim=1.00
      src/vdisplay/control/contracts.py:40-43  (to_dict)
      src/vdisplay/control/contracts.py:55-58  (to_dict)
      src/vdisplay/control/contracts.py:70-73  (to_dict)
      src/vdisplay/control/contracts.py:84-87  (to_dict)
  [80f1f837300b8376]   STRU  _route_terminal_open  L=12 N=2 saved=12 sim=1.00
      src/vdisplay/client.py:58-69  (_route_terminal_open)
      src/vdisplay/client.py:72-83  (_route_browser_open)
  [7168a023bfc45913]   EXAC  _system_python  L=5 N=3 saved=10 sim=1.00
      src/vdisplay/capture/portal.py:81-85  (_system_python)
      src/vdisplay/capture/portal_screencast.py:206-210  (_system_python)
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
      src/vdisplay/control/providers/atspi.py:206-211  (find)
      src/vdisplay/control/providers/x11.py:59-64  (find)
  [ab50b6c9821c38ed]   EXAC  bounds  L=6 N=2 saved=6 sim=1.00
      src/vdisplay/control/providers/ax.py:161-166  (bounds)
      src/vdisplay/control/providers/uia.py:161-166  (bounds)
  [74ff44f1b5a82c2b]   STRU  _matches_name_fields  L=6 N=2 saved=6 sim=1.00
      src/vdisplay/control/providers/ax_impl.py:95-100  (_matches_name_fields)
      src/vdisplay/control/providers/uia_impl.py:88-93  (_matches_name_fields)
  [da81c4e42f1334a8]   STRU  _matches_selector  L=6 N=2 saved=6 sim=1.00
      src/vdisplay/control/providers/ax_impl.py:113-118  (_matches_selector)
      src/vdisplay/control/providers/uia_impl.py:108-113  (_matches_selector)
  [5177a541164fa53c]   EXAC  _vdisplay_src_path  L=5 N=2 saved=5 sim=1.00
      src/vdisplay/capture/portal_screencast.py:728-732  (_vdisplay_src_path)
      src/vdisplay/control/providers/atspi.py:47-51  (_vdisplay_src_path)
  [3dd47853913ce2b2]   STRU  _use_mock_backend  L=5 N=2 saved=5 sim=1.00
      examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py:52-56  (_use_mock_backend)
      examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py:53-57  (_use_mock_backend)
  [8a91889b8e161c42]   STRU  _screenshot_to_text  L=5 N=2 saved=5 sim=1.00
      packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:298-302  (_screenshot_to_text)
      packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:305-309  (_mirror_to_text)
  [69ba40a4847babb6]   STRU  resolve_map_element  L=5 N=2 saved=5 sim=1.00
      src/vdisplay/control/gui_map_resolve.py:12-16  (resolve_map_element)
      src/vdisplay/control/gui_map_resolve.py:19-23  (resolve_map_region)
  [084cc31ae50eea8e]   EXAC  bounds  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/control/providers/atspi.py:237-240  (bounds)
      src/vdisplay/control/providers/terminal.py:124-127  (bounds)
  [256755d12aec5824]   STRU  create_ax_backend  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/control/providers/ax_impl.py:266-269  (create_ax_backend)
      src/vdisplay/control/providers/uia_impl.py:296-299  (create_uia_backend)
  [bd065add6cf51e32]   STRU  _vertical_overlap  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/control/vision_ocr.py:159-162  (_vertical_overlap)
      src/vdisplay/control/vision_ocr.py:165-168  (_horizontal_overlap)
  [9063575af46509c9]   STRU  available  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/input/linux_xdotool.py:18-21  (available)
      src/vdisplay/input/linux_ydotool.py:27-30  (available)
  [cbe2ba609e614f7d]   EXAC  close_all  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/control/providers/browser_session.py:237-239  (close_all)
      src/vdisplay/control/providers/terminal_session.py:218-220  (close_all)
  [7e769be7bd62da72]   EXAC  bounds  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/control/providers/vision/provider.py:710-712  (bounds)
      src/vdisplay/control/providers/x11.py:105-107  (bounds)
  [2d7b9210c1b65241]   STRU  img2nl_enabled  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/application/services/img2nl_enrich.py:10-12  (img2nl_enabled)
      src/vdisplay/control/browser_session_store.py:34-36  (detached_sessions_enabled)
  [2bae6c54b401ddd7]   STRU  vision_llm_fallback_enabled  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/control/vision_llm.py:73-75  (vision_llm_fallback_enabled)
      src/vdisplay/control/vision_llm.py:78-80  (vision_llm_enrich_enabled)
  [f5bfacfda8981cef]   STRU  looks_like_internal_class  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/windows/filter.py:8-10  (looks_like_internal_class)
      src/vdisplay/windows/filter.py:13-15  (looks_like_internal_name)

REFACTOR[43] (ranked by priority):
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
  [11] ○ extract_function   → src/vdisplay/control/utils/to_dict.py
      WHY: 4 occurrences of 4-line block across 1 files — saves 12 lines
      FILES: src/vdisplay/control/contracts.py
  [12] ○ extract_function   → src/vdisplay/utils/_route_terminal_open.py
      WHY: 2 occurrences of 12-line block across 1 files — saves 12 lines
      FILES: src/vdisplay/client.py
  [13] ○ extract_function   → src/vdisplay/utils/_system_python.py
      WHY: 3 occurrences of 5-line block across 3 files — saves 10 lines
      FILES: src/vdisplay/capture/portal.py, src/vdisplay/capture/portal_screencast.py, src/vdisplay/control/providers/atspi.py
  [14] ○ extract_function   → packages/dsl2vdisplay/src/dsl2vdisplay/utils/_parse_mirror.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py
  [15] ○ extract_function   → src/vdisplay/commands/utils/register.py
      WHY: 3 occurrences of 5-line block across 3 files — saves 10 lines
      FILES: src/vdisplay/commands/all_cmd.py, src/vdisplay/commands/monitors.py, src/vdisplay/commands/windows.py
  [16] ○ extract_function   → src/vdisplay/control/utils/_safe_info.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: src/vdisplay/control/session.py
  [17] ○ extract_function   → examples/utils/build_example_ax.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py, examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py
  [18] ○ extract_function   → src/vdisplay/utils/_default_virtual_backend.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/api.py
  [19] ○ extract_function   → src/vdisplay/control/providers/utils/ax_deps_available.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: src/vdisplay/control/providers/ax_impl.py, src/vdisplay/control/providers/uia_impl.py
  [20] ○ extract_function   → src/vdisplay/control/utils/_build_uia.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/control/registry.py
  [21] ○ extract_function   → src/vdisplay/control/utils/_build_browser.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/control/registry.py
  [22] ○ extract_function   → src/vdisplay/control/providers/utils/invoke.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [23] ○ extract_function   → src/vdisplay/control/providers/utils/focus.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [24] ○ extract_function   → src/vdisplay/control/utils/_atspi_ready.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: src/vdisplay/control/scoring.py
  [25] ○ extract_function   → src/vdisplay/control/utils/_terminal_line_matches.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: src/vdisplay/control/selector.py
  [26] ○ extract_function   → src/vdisplay/control/utils/control_focus_type_seconds.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: src/vdisplay/control/timing.py
  [27] ○ extract_function   → src/vdisplay/control/providers/utils/find.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/vdisplay/control/providers/atspi.py, src/vdisplay/control/providers/x11.py
  [28] ○ extract_function   → src/vdisplay/control/providers/utils/bounds.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/vdisplay/control/providers/ax.py, src/vdisplay/control/providers/uia.py
  [29] ○ extract_function   → src/vdisplay/control/providers/utils/_matches_name_fields.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/vdisplay/control/providers/ax_impl.py, src/vdisplay/control/providers/uia_impl.py
  [30] ○ extract_function   → src/vdisplay/control/providers/utils/_matches_selector.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/vdisplay/control/providers/ax_impl.py, src/vdisplay/control/providers/uia_impl.py
  [31] ○ extract_function   → src/vdisplay/utils/_vdisplay_src_path.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: src/vdisplay/capture/portal_screencast.py, src/vdisplay/control/providers/atspi.py
  [32] ○ extract_function   → examples/utils/_use_mock_backend.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py, examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py
  [33] ○ extract_function   → packages/dsl2vdisplay/src/dsl2vdisplay/utils/_screenshot_to_text.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py
  [34] ○ extract_function   → src/vdisplay/control/utils/resolve_map_element.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: src/vdisplay/control/gui_map_resolve.py
  [35] ○ extract_function   → src/vdisplay/control/providers/utils/bounds.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/control/providers/atspi.py, src/vdisplay/control/providers/terminal.py
  [36] ○ extract_function   → src/vdisplay/control/providers/utils/create_ax_backend.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/control/providers/ax_impl.py, src/vdisplay/control/providers/uia_impl.py
  [37] ○ extract_function   → src/vdisplay/control/utils/_vertical_overlap.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: src/vdisplay/control/vision_ocr.py
  [38] ○ extract_function   → src/vdisplay/input/utils/available.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/input/linux_xdotool.py, src/vdisplay/input/linux_ydotool.py
  [39] ○ extract_function   → src/vdisplay/control/providers/utils/close_all.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: src/vdisplay/control/providers/browser_session.py, src/vdisplay/control/providers/terminal_session.py
  [40] ○ extract_function   → src/vdisplay/control/providers/utils/bounds.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: src/vdisplay/control/providers/vision/provider.py, src/vdisplay/control/providers/x11.py
  [41] ○ extract_function   → src/vdisplay/utils/img2nl_enabled.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: src/vdisplay/application/services/img2nl_enrich.py, src/vdisplay/control/browser_session_store.py
  [42] ○ extract_function   → src/vdisplay/control/utils/vision_llm_fallback_enabled.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/vdisplay/control/vision_llm.py
  [43] ○ extract_function   → src/vdisplay/windows/utils/looks_like_internal_class.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/vdisplay/windows/filter.py

QUICK_WINS[30] (low risk, high savings — do first):
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

EFFORT_ESTIMATE (total ≈ 14.8h):
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
  ... +33 more (~430min)

METRICS-TARGET:
  dup_groups:  43 → 0
  saved_lines: 427 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 1435 func | 162f | 2026-06-10
# generated in 0.01s

NEXT[3] (ranked by impact):
  [1] !! SPLIT           src/vdisplay/control/scoring.py
      WHY: 801L, 2 classes, max CC=12
      EFFORT: ~4h  IMPACT: 9612

  [2] !! SPLIT           maps/pycharm-chat.json
      WHY: 2503L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [3] !! SPLIT           planfile.yaml
      WHY: 1319L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting maps/pycharm-chat.json may break 0 import paths
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting src/vdisplay/control/scoring.py may break 40 import paths

METRICS-TARGET:
  CC̄:          3.6 → ≤2.5
  max-CC:      14 → ≤7
  god-modules: 11 → 0
  high-CC(≥15): 0 → ≤0
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
  prev CC̄=3.6 → now CC̄=3.6
```

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

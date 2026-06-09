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
- **version**: `0.1.5`
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
  version: 0.1.5;
}

dependencies {
  pillow: Pillow>=10.0;
  sampler: Pillow>=10.0;
  dev: "pytest>=8.0, Pillow>=10.0, fastapi>=0.110, httpx>=0.27, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60, dsl2vdisplay, vdisplay-agent, uvicorn>=0.27";
  control: "dsl2vdisplay, nlp2vdisplay";
  agent: "vdisplay-agent, fastapi>=0.110, uvicorn>=0.27";
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
  keys: OPENROUTER_API_KEY, LLM_MODEL, VDISPLAY_AGENT_AUTO, VDISPLAY_AGENT_HOST, VDISPLAY_AGENT_PORT, VDISPLAY_AGENT_URL, VDISPLAY_AGENT_TOKEN, VDISPLAY_AGENT_BROKER, DISPLAY, XDG_SESSION_TYPE, WAYLAND_DISPLAY, VDISPLAY_SCREENCAST_MULTIPLE, VDISPLAY_SCREENCAST_CURSOR, VDISPLAY_IMG2NL, VDISPLAY_IMG2NL_LOCALE, VDISPLAY_CAPTURE_ALLOW_PORTAL, PYTEST_CURRENT_TEST;
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
```

## Call Graph

*397 nodes · 494 edges · 84 modules · CC̄=3.2*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_start_screencast_impl` *(in src.vdisplay.capture.portal_screencast)* | 9 | 1 | 71 | **72** |
| `capture_host_png` *(in src.vdisplay.capture.host)* | 15 ⚠ | 2 | 44 | **46** |
| `create_app` *(in packages.rest2vdisplay.src.rest2vdisplay.app)* | 2 | 3 | 38 | **41** |
| `dispatch` *(in packages.dsl2vdisplay.src.dsl2vdisplay.bus)* | 13 ⚠ | 9 | 27 | **36** |
| `list_outputs` *(in src.vdisplay.discovery)* | 8 | 9 | 27 | **36** |
| `main` *(in examples.agent-broker.broker_demo)* | 9 | 0 | 35 | **35** |
| `run_command` *(in src.vdisplay.utils)* | 2 | 29 | 4 | **33** |
| `main` *(in examples.host-relay.relay_demo)* | 11 ⚠ | 0 | 33 | **33** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/vdisplay
# generated in 0.23s
# nodes: 397 | edges: 494 | modules: 84
# CC̄=3.2

HUBS[20]:
  src.vdisplay.capture.portal_screencast._start_screencast_impl
    CC=9  in:1  out:71  total:72
  src.vdisplay.capture.host.capture_host_png
    CC=15  in:2  out:44  total:46
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=13  in:9  out:27  total:36
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  examples.agent-broker.broker_demo.main
    CC=9  in:0  out:35  total:35
  src.vdisplay.utils.run_command
    CC=2  in:29  out:4  total:33
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:32  total:32
  examples.host-mirror.mirror_demo.main
    CC=7  in:0  out:31  total:31
  src.vdisplay.commands.sampler.handle
    CC=17  in:0  out:30  total:30
  src.vdisplay.capture.portal._portal_impl
    CC=4  in:1  out:28  total:29
  src.vdisplay.cli_handlers.print_json
    CC=1  in:26  out:1  total:27
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window
    CC=12  in:0  out:27  total:27
  src.vdisplay.application.services.sampler_loop.SamplerLoop._run
    CC=17  in:0  out:26  total:26
  src.vdisplay.capture.portal_screencast.PortalScreenCastSession.start
    CC=19  in:0  out:26  total:26
  src.vdisplay.capture.host.resolve_window_region
    CC=10  in:1  out:24  total:25
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler._config_from_body
    CC=12  in:1  out:24  total:25
  src.vdisplay.capture.host.capture_all_monitors
    CC=21  in:2  out:23  total:25
  src.vdisplay.discovery.resolve_host_display
    CC=9  in:19  out:6  total:25

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
  examples.host-mirror.mirror_demo  [1 funcs]
    main  CC=7  out:31
  examples.host-relay.relay_demo  [2 funcs]
    _capture_phase  CC=1  out:6
    main  CC=11  out:33
  packages.cli2vdisplay.src.cli2vdisplay.cli  [1 funcs]
    main  CC=7  out:16
  packages.dsl2vdisplay.src.dsl2vdisplay.bus  [3 funcs]
    _dispatch_legacy  CC=3  out:13
    dispatch  CC=13  out:27
    execute_dsl_line  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.cli  [3 funcs]
    _main_legacy  CC=10  out:17
    _main_subcommand  CC=9  out:19
    main  CC=4  out:3
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar  [11 funcs]
    _parse_adopt  CC=6  out:5
    _parse_launch  CC=5  out:7
    _parse_mirror  CC=5  out:4
    _parse_release  CC=5  out:4
    _parse_screenshot  CC=5  out:6
    _parse_virtual_start  CC=4  out:5
    _parse_windows  CC=3  out:2
    _with_display  CC=2  out:1
    parse_line  CC=3  out:4
    pick_flag  CC=3  out:2
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
  packages.vdisplay-agent.src.vdisplay_agent.runtime  [1 funcs]
    list_windows  CC=1  out:1
  packages.vdisplay-agent.src.vdisplay_agent.serve_port  [8 funcs]
    _parse_ss_pids  CC=2  out:4
    _pid_alive  CC=3  out:1
    _pids_from_lsof  CC=5  out:6
    _pids_from_ss  CC=3  out:2
    _probe_is_vdisplay_agent  CC=6  out:11
    ensure_broker_port_free  CC=4  out:5
    find_listener_pids  CC=4  out:4
    stop_pids  CC=13  out:10
  packages.vdisplay-agent.src.vdisplay_agent.services.capabilities  [2 funcs]
    diagnostics  CC=1  out:4
    platform_capabilities  CC=5  out:11
  packages.vdisplay-agent.src.vdisplay_agent.services.capture  [5 funcs]
    _capture_all_monitors  CC=2  out:8
    _capture_host  CC=7  out:16
    _capture_session  CC=3  out:13
    _region_from_body  CC=8  out:13
    capture_frame  CC=3  out:6
  packages.vdisplay-agent.src.vdisplay_agent.services.outputs  [1 funcs]
    list_outputs_payload  CC=2  out:4
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler  [5 funcs]
    _capture_virtual_persistent  CC=5  out:12
    _config_from_body  CC=12  out:24
    _ensure_virtual_session  CC=4  out:5
    _recover_screencast  CC=3  out:3
    start_sampler  CC=5  out:11
  packages.vdisplay-agent.src.vdisplay_agent.services.sessions  [9 funcs]
    _session_started  CC=1  out:2
    screencast_status  CC=3  out:2
    shutdown  CC=4  out:6
    start_mirror  CC=1  out:4
    start_relay  CC=2  out:4
    start_screencast  CC=1  out:3
    start_virtual  CC=1  out:4
    stop_screencast  CC=3  out:2
    stop_session  CC=3  out:3
  packages.vdisplay-agent.src.vdisplay_agent.session_store  [1 funcs]
    register  CC=1  out:2
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
    create  CC=4  out:6
    list_adopted  CC=1  out:1
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.application.errors  [1 funcs]
    error_from_exception  CC=4  out:11
  src.vdisplay.application.executor  [2 funcs]
    _maybe_enrich_screenshot  CC=3  out:2
    execute  CC=6  out:11
  src.vdisplay.application.handlers.agent  [7 funcs]
    _all  CC=3  out:12
    _capabilities  CC=1  out:2
    _monitors  CC=1  out:2
    _strip_ok  CC=1  out:2
    _validate  CC=4  out:9
    _windows  CC=1  out:2
    execute_agent  CC=2  out:4
  src.vdisplay.application.handlers.local  [1 funcs]
    execute_local  CC=2  out:3
  src.vdisplay.application.runtime  [7 funcs]
    meta_for  CC=2  out:1
    route  CC=6  out:4
    agent_client_optional  CC=2  out:2
    agent_client_required  CC=2  out:3
    get_execution_policy  CC=1  out:0
    prefer_agent  CC=1  out:1
    resolve_apps_only  CC=3  out:0
  src.vdisplay.application.services.capture  [5 funcs]
    _capture_via_agent  CC=9  out:13
    capture_screenshot  CC=3  out:3
    capture_screenshot_local  CC=7  out:9
    capture_screenshot_via_client  CC=1  out:1
    resolve_screenshot_routing  CC=7  out:1
  src.vdisplay.application.services.discovery  [11 funcs]
    _run_discovery  CC=3  out:2
    _sampler_hint  CC=3  out:0
    diagnose  CC=2  out:2
    diagnose_unattended  CC=2  out:7
    list_adopted  CC=1  out:4
    list_all  CC=4  out:2
    list_all_local  CC=1  out:4
    list_monitors  CC=1  out:2
    list_monitors_local  CC=2  out:4
    list_windows_local  CC=2  out:6
  src.vdisplay.application.services.img2nl_enrich  [5 funcs]
    _image_path  CC=3  out:2
    describe_screenshot_image  CC=9  out:9
    enrich_screenshot_payload  CC=9  out:11
    img2nl_enabled  CC=1  out:3
    img2nl_locale  CC=2  out:2
  src.vdisplay.application.services.info  [1 funcs]
    platform_info  CC=6  out:17
  src.vdisplay.application.services.sampler  [2 funcs]
    run_sampler  CC=5  out:18
    start_sampler_via_agent  CC=1  out:1
  src.vdisplay.application.services.sampler_loop  [6 funcs]
    _run  CC=17  out:26
    start  CC=2  out:10
    frame_extension  CC=1  out:0
    resolve_capture_mode  CC=5  out:1
    transcode_frame  CC=5  out:8
    validate_sampler_config  CC=7  out:6
  src.vdisplay.application.services.session  [2 funcs]
    mirror_screenshot  CC=2  out:4
    relay_screenshot  CC=4  out:10
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
  src.vdisplay.backends.linux_xvfb  [7 funcs]
    _acquire_display  CC=8  out:14
    screenshot_bytes  CC=2  out:2
    start  CC=4  out:6
    _display_candidates  CC=4  out:4
    _display_socket_exists  CC=1  out:3
    _probe_display  CC=2  out:2
    _wait_for_display  CC=7  out:10
  src.vdisplay.capture.host  [10 funcs]
    _capture_all_from_driver_full  CC=7  out:15
    _capture_all_from_screencast  CC=13  out:18
    _host_capture_error  CC=3  out:2
    _monitor_capture_region  CC=4  out:10
    _monitor_source_name  CC=9  out:13
    _wayland_host_session  CC=2  out:2
    capture_all_monitors  CC=21  out:23
    capture_host_png  CC=15  out:44
    capture_host_to_file  CC=3  out:10
    resolve_window_region  CC=10  out:24
  src.vdisplay.capture.linux_xwd  [21 funcs]
    _capture_full_display_png  CC=1  out:1
    _capture_gnome_screenshot_png  CC=4  out:10
    _capture_grim_png  CC=4  out:11
    _capture_hint  CC=2  out:1
    _capture_portal_png  CC=1  out:1
    _capture_scrot_png  CC=5  out:11
    _capture_xwd_png  CC=1  out:3
    _crop_png  CC=2  out:15
    _decode_pixels  CC=12  out:7
    _header_fields  CC=1  out:0
  src.vdisplay.capture.policy  [1 funcs]
    assess_unattended_capture  CC=17  out:19
  src.vdisplay.capture.portal  [6 funcs]
    capture_full  CC=1  out:1
    capture_region  CC=1  out:2
    _capture_portal_to_file  CC=11  out:13
    _portal_impl  CC=4  out:28
    _system_python  CC=4  out:3
    capture_portal_png  CC=4  out:11
  src.vdisplay.capture.portal_screencast  [29 funcs]
    capture_png  CC=6  out:9
    start  CC=19  out:26
    stop  CC=5  out:4
    _capture_pipewire_frame_gi_subprocess  CC=6  out:12
    _capture_pipewire_frame_gst_launch  CC=8  out:15
    _capture_pipewire_node  CC=1  out:1
    _capture_pipewire_stream  CC=2  out:9
    _close_pipewire_fd  CC=2  out:1
    _close_screencast_session  CC=2  out:4
    _dbus_fd  CC=5  out:8
  src.vdisplay.capture.providers.drm  [3 funcs]
    _capture  CC=11  out:19
    available  CC=3  out:2
    _drm_devices  CC=5  out:7
  src.vdisplay.capture.providers.engine  [6 funcs]
    _allow_portal  CC=1  out:3
    _providers  CC=4  out:13
    _try_providers  CC=11  out:15
    capture_full_png  CC=1  out:2
    capture_region_png  CC=1  out:2
    list_capture_providers  CC=4  out:6
  src.vdisplay.capture.providers.fbdev  [3 funcs]
    _capture  CC=7  out:22
    available  CC=3  out:4
    _fb_info  CC=2  out:11
  src.vdisplay.capture.providers.x11  [2 funcs]
    capture_full  CC=4  out:6
    capture_region  CC=2  out:3
  src.vdisplay.cli  [2 funcs]
    build_parser  CC=1  out:3
    main  CC=2  out:4
  src.vdisplay.cli_handlers  [1 funcs]
    print_json  CC=1  out:1
  src.vdisplay.client  [4 funcs]
    __init__  CC=2  out:2
    _normalize_payload  CC=1  out:1
    request  CC=3  out:8
    _route_command  CC=14  out:8
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.agent  [2 funcs]
    _agent_client  CC=2  out:3
    handle  CC=12  out:23
  src.vdisplay.commands.all_cmd  [4 funcs]
    handle  CC=1  out:3
    handle_outputs  CC=1  out:3
    register  CC=1  out:4
    register_outputs  CC=1  out:4
  src.vdisplay.commands.common  [4 funcs]
    add_all_arg  CC=1  out:1
    add_display_arg  CC=1  out:1
    add_window_filter_args  CC=1  out:7
    include_all_from_args  CC=2  out:3
  src.vdisplay.commands.diagnose  [2 funcs]
    handle  CC=2  out:4
    register  CC=1  out:4
  src.vdisplay.commands.info  [1 funcs]
    handle  CC=1  out:2
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
  src.vdisplay.commands.sampler  [3 funcs]
    _config_from_args  CC=1  out:1
    handle  CC=17  out:30
    register  CC=1  out:22
  src.vdisplay.commands.screenshot  [2 funcs]
    handle  CC=1  out:2
    register  CC=1  out:14
  src.vdisplay.commands.virtual  [1 funcs]
    handle  CC=6  out:9
  src.vdisplay.commands.windows  [2 funcs]
    handle  CC=1  out:3
    register  CC=1  out:4
  src.vdisplay.discovery  [13 funcs]
    _attach_output_nl  CC=2  out:3
    _display_hint  CC=3  out:2
    _list_monitors  CC=6  out:10
    _looks_like_xvfb_only  CC=4  out:4
    _merge_output_metadata  CC=3  out:18
    _parse_xrandr_query  CC=8  out:12
    diagnose_display  CC=10  out:19
    find_window_suggestions  CC=2  out:2
    list_monitors  CC=1  out:1
    list_outputs  CC=8  out:27
  src.vdisplay.input.linux_xdotool  [4 funcs]
    click  CC=1  out:4
    hotkey  CC=1  out:3
    move  CC=1  out:5
    type_text  CC=1  out:3
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
  src.vdisplay.utils  [3 funcs]
    require_command  CC=2  out:2
    run_command  CC=2  out:4
    run_command_bytes  CC=1  out:1
  src.vdisplay.windows.filter  [12 funcs]
    filter_windows  CC=14  out:6
    is_companion_frame  CC=9  out:11
    is_internal_window  CC=13  out:6
    is_junk_title  CC=6  out:2
    is_trivial_internal  CC=5  out:0
    is_visible_app  CC=9  out:1
    looks_like_internal_class  CC=3  out:2
    looks_like_internal_name  CC=3  out:2
    matches_app  CC=7  out:6
    matches_class  CC=5  out:4
  src.vdisplay.windows.normalize  [7 funcs]
    derive_app_label  CC=14  out:4
    derive_role  CC=10  out:3
    normalize_atom_list  CC=3  out:6
    parse_wm_class  CC=7  out:9
    process_info  CC=6  out:10
    resolve_window_pid  CC=3  out:8
    usable_title  CC=3  out:3
  src.vdisplay.windows.query  [6 funcs]
    find_companion_frames  CC=8  out:10
    find_windows  CC=6  out:5
    inspect_window  CC=9  out:21
    list_windows_enriched  CC=2  out:5
    pick_best_window  CC=8  out:3
    scan_windows  CC=4  out:4
  src.vdisplay.windows.rank  [3 funcs]
    dedupe_app_windows  CC=5  out:9
    pick_best_from_group  CC=9  out:7
    pick_largest  CC=1  out:1
  src.vdisplay.windows.scan  [7 funcs]
    decode_xprop_value  CC=6  out:6
    format_window_id  CC=3  out:3
    root_window_id  CC=3  out:6
    search_window_ids  CC=4  out:6
    window_geometry  CC=4  out:8
    xdotool  CC=1  out:1
    xprop  CC=5  out:11

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
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry._load_schema
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_windows → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_windows → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_screenshot → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_virtual_start → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_launch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_mirror → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_adopt → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_release → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.split_command
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
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_adopt → src.vdisplay.discovery.resolve_host_display
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_release → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_release → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_release → src.vdisplay.discovery.resolve_host_display
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_outputs → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_monitors
  packages.cli2vdisplay.src.cli2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.uri2vdisplay.src.uri2vdisplay.cli.main → packages.uri2vdisplay.src.uri2vdisplay.decode.uri_to_dsl
  packages.uri2vdisplay.src.uri2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app → src.vdisplay.agent_config.resolve_agent_url
  packages.vdisplay-agent.src.vdisplay_agent.cli.main → packages.rest2vdisplay.src.rest2vdisplay.app.create_app
  packages.vdisplay-agent.src.vdisplay_agent.serve_port._pids_from_ss → packages.vdisplay-agent.src.vdisplay_agent.serve_port._parse_ss_pids
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.find_listener_pids → packages.vdisplay-agent.src.vdisplay_agent.serve_port._pids_from_ss
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.find_listener_pids → packages.vdisplay-agent.src.vdisplay_agent.serve_port._pids_from_lsof
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.stop_pids → packages.vdisplay-agent.src.vdisplay_agent.serve_port._pid_alive
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.ensure_broker_port_free → packages.vdisplay-agent.src.vdisplay_agent.serve_port.find_listener_pids
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.ensure_broker_port_free → packages.vdisplay-agent.src.vdisplay_agent.serve_port._probe_is_vdisplay_agent
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
# generated in 0.23s
# nodes: 397 | edges: 494 | modules: 84
# CC̄=3.2

HUBS[20]:
  src.vdisplay.capture.portal_screencast._start_screencast_impl
    CC=9  in:1  out:71  total:72
  src.vdisplay.capture.host.capture_host_png
    CC=15  in:2  out:44  total:46
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=13  in:9  out:27  total:36
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  examples.agent-broker.broker_demo.main
    CC=9  in:0  out:35  total:35
  src.vdisplay.utils.run_command
    CC=2  in:29  out:4  total:33
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:32  total:32
  examples.host-mirror.mirror_demo.main
    CC=7  in:0  out:31  total:31
  src.vdisplay.commands.sampler.handle
    CC=17  in:0  out:30  total:30
  src.vdisplay.capture.portal._portal_impl
    CC=4  in:1  out:28  total:29
  src.vdisplay.cli_handlers.print_json
    CC=1  in:26  out:1  total:27
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window
    CC=12  in:0  out:27  total:27
  src.vdisplay.application.services.sampler_loop.SamplerLoop._run
    CC=17  in:0  out:26  total:26
  src.vdisplay.capture.portal_screencast.PortalScreenCastSession.start
    CC=19  in:0  out:26  total:26
  src.vdisplay.capture.host.resolve_window_region
    CC=10  in:1  out:24  total:25
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler._config_from_body
    CC=12  in:1  out:24  total:25
  src.vdisplay.capture.host.capture_all_monitors
    CC=21  in:2  out:23  total:25
  src.vdisplay.discovery.resolve_host_display
    CC=9  in:19  out:6  total:25

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
  examples.host-mirror.mirror_demo  [1 funcs]
    main  CC=7  out:31
  examples.host-relay.relay_demo  [2 funcs]
    _capture_phase  CC=1  out:6
    main  CC=11  out:33
  packages.cli2vdisplay.src.cli2vdisplay.cli  [1 funcs]
    main  CC=7  out:16
  packages.dsl2vdisplay.src.dsl2vdisplay.bus  [3 funcs]
    _dispatch_legacy  CC=3  out:13
    dispatch  CC=13  out:27
    execute_dsl_line  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.cli  [3 funcs]
    _main_legacy  CC=10  out:17
    _main_subcommand  CC=9  out:19
    main  CC=4  out:3
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar  [11 funcs]
    _parse_adopt  CC=6  out:5
    _parse_launch  CC=5  out:7
    _parse_mirror  CC=5  out:4
    _parse_release  CC=5  out:4
    _parse_screenshot  CC=5  out:6
    _parse_virtual_start  CC=4  out:5
    _parse_windows  CC=3  out:2
    _with_display  CC=2  out:1
    parse_line  CC=3  out:4
    pick_flag  CC=3  out:2
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
  packages.vdisplay-agent.src.vdisplay_agent.runtime  [1 funcs]
    list_windows  CC=1  out:1
  packages.vdisplay-agent.src.vdisplay_agent.serve_port  [8 funcs]
    _parse_ss_pids  CC=2  out:4
    _pid_alive  CC=3  out:1
    _pids_from_lsof  CC=5  out:6
    _pids_from_ss  CC=3  out:2
    _probe_is_vdisplay_agent  CC=6  out:11
    ensure_broker_port_free  CC=4  out:5
    find_listener_pids  CC=4  out:4
    stop_pids  CC=13  out:10
  packages.vdisplay-agent.src.vdisplay_agent.services.capabilities  [2 funcs]
    diagnostics  CC=1  out:4
    platform_capabilities  CC=5  out:11
  packages.vdisplay-agent.src.vdisplay_agent.services.capture  [5 funcs]
    _capture_all_monitors  CC=2  out:8
    _capture_host  CC=7  out:16
    _capture_session  CC=3  out:13
    _region_from_body  CC=8  out:13
    capture_frame  CC=3  out:6
  packages.vdisplay-agent.src.vdisplay_agent.services.outputs  [1 funcs]
    list_outputs_payload  CC=2  out:4
  packages.vdisplay-agent.src.vdisplay_agent.services.sampler  [5 funcs]
    _capture_virtual_persistent  CC=5  out:12
    _config_from_body  CC=12  out:24
    _ensure_virtual_session  CC=4  out:5
    _recover_screencast  CC=3  out:3
    start_sampler  CC=5  out:11
  packages.vdisplay-agent.src.vdisplay_agent.services.sessions  [9 funcs]
    _session_started  CC=1  out:2
    screencast_status  CC=3  out:2
    shutdown  CC=4  out:6
    start_mirror  CC=1  out:4
    start_relay  CC=2  out:4
    start_screencast  CC=1  out:3
    start_virtual  CC=1  out:4
    stop_screencast  CC=3  out:2
    stop_session  CC=3  out:3
  packages.vdisplay-agent.src.vdisplay_agent.session_store  [1 funcs]
    register  CC=1  out:2
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
    create  CC=4  out:6
    list_adopted  CC=1  out:1
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.application.errors  [1 funcs]
    error_from_exception  CC=4  out:11
  src.vdisplay.application.executor  [2 funcs]
    _maybe_enrich_screenshot  CC=3  out:2
    execute  CC=6  out:11
  src.vdisplay.application.handlers.agent  [7 funcs]
    _all  CC=3  out:12
    _capabilities  CC=1  out:2
    _monitors  CC=1  out:2
    _strip_ok  CC=1  out:2
    _validate  CC=4  out:9
    _windows  CC=1  out:2
    execute_agent  CC=2  out:4
  src.vdisplay.application.handlers.local  [1 funcs]
    execute_local  CC=2  out:3
  src.vdisplay.application.runtime  [7 funcs]
    meta_for  CC=2  out:1
    route  CC=6  out:4
    agent_client_optional  CC=2  out:2
    agent_client_required  CC=2  out:3
    get_execution_policy  CC=1  out:0
    prefer_agent  CC=1  out:1
    resolve_apps_only  CC=3  out:0
  src.vdisplay.application.services.capture  [5 funcs]
    _capture_via_agent  CC=9  out:13
    capture_screenshot  CC=3  out:3
    capture_screenshot_local  CC=7  out:9
    capture_screenshot_via_client  CC=1  out:1
    resolve_screenshot_routing  CC=7  out:1
  src.vdisplay.application.services.discovery  [11 funcs]
    _run_discovery  CC=3  out:2
    _sampler_hint  CC=3  out:0
    diagnose  CC=2  out:2
    diagnose_unattended  CC=2  out:7
    list_adopted  CC=1  out:4
    list_all  CC=4  out:2
    list_all_local  CC=1  out:4
    list_monitors  CC=1  out:2
    list_monitors_local  CC=2  out:4
    list_windows_local  CC=2  out:6
  src.vdisplay.application.services.img2nl_enrich  [5 funcs]
    _image_path  CC=3  out:2
    describe_screenshot_image  CC=9  out:9
    enrich_screenshot_payload  CC=9  out:11
    img2nl_enabled  CC=1  out:3
    img2nl_locale  CC=2  out:2
  src.vdisplay.application.services.info  [1 funcs]
    platform_info  CC=6  out:17
  src.vdisplay.application.services.sampler  [2 funcs]
    run_sampler  CC=5  out:18
    start_sampler_via_agent  CC=1  out:1
  src.vdisplay.application.services.sampler_loop  [6 funcs]
    _run  CC=17  out:26
    start  CC=2  out:10
    frame_extension  CC=1  out:0
    resolve_capture_mode  CC=5  out:1
    transcode_frame  CC=5  out:8
    validate_sampler_config  CC=7  out:6
  src.vdisplay.application.services.session  [2 funcs]
    mirror_screenshot  CC=2  out:4
    relay_screenshot  CC=4  out:10
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
  src.vdisplay.backends.linux_xvfb  [7 funcs]
    _acquire_display  CC=8  out:14
    screenshot_bytes  CC=2  out:2
    start  CC=4  out:6
    _display_candidates  CC=4  out:4
    _display_socket_exists  CC=1  out:3
    _probe_display  CC=2  out:2
    _wait_for_display  CC=7  out:10
  src.vdisplay.capture.host  [10 funcs]
    _capture_all_from_driver_full  CC=7  out:15
    _capture_all_from_screencast  CC=13  out:18
    _host_capture_error  CC=3  out:2
    _monitor_capture_region  CC=4  out:10
    _monitor_source_name  CC=9  out:13
    _wayland_host_session  CC=2  out:2
    capture_all_monitors  CC=21  out:23
    capture_host_png  CC=15  out:44
    capture_host_to_file  CC=3  out:10
    resolve_window_region  CC=10  out:24
  src.vdisplay.capture.linux_xwd  [21 funcs]
    _capture_full_display_png  CC=1  out:1
    _capture_gnome_screenshot_png  CC=4  out:10
    _capture_grim_png  CC=4  out:11
    _capture_hint  CC=2  out:1
    _capture_portal_png  CC=1  out:1
    _capture_scrot_png  CC=5  out:11
    _capture_xwd_png  CC=1  out:3
    _crop_png  CC=2  out:15
    _decode_pixels  CC=12  out:7
    _header_fields  CC=1  out:0
  src.vdisplay.capture.policy  [1 funcs]
    assess_unattended_capture  CC=17  out:19
  src.vdisplay.capture.portal  [6 funcs]
    capture_full  CC=1  out:1
    capture_region  CC=1  out:2
    _capture_portal_to_file  CC=11  out:13
    _portal_impl  CC=4  out:28
    _system_python  CC=4  out:3
    capture_portal_png  CC=4  out:11
  src.vdisplay.capture.portal_screencast  [29 funcs]
    capture_png  CC=6  out:9
    start  CC=19  out:26
    stop  CC=5  out:4
    _capture_pipewire_frame_gi_subprocess  CC=6  out:12
    _capture_pipewire_frame_gst_launch  CC=8  out:15
    _capture_pipewire_node  CC=1  out:1
    _capture_pipewire_stream  CC=2  out:9
    _close_pipewire_fd  CC=2  out:1
    _close_screencast_session  CC=2  out:4
    _dbus_fd  CC=5  out:8
  src.vdisplay.capture.providers.drm  [3 funcs]
    _capture  CC=11  out:19
    available  CC=3  out:2
    _drm_devices  CC=5  out:7
  src.vdisplay.capture.providers.engine  [6 funcs]
    _allow_portal  CC=1  out:3
    _providers  CC=4  out:13
    _try_providers  CC=11  out:15
    capture_full_png  CC=1  out:2
    capture_region_png  CC=1  out:2
    list_capture_providers  CC=4  out:6
  src.vdisplay.capture.providers.fbdev  [3 funcs]
    _capture  CC=7  out:22
    available  CC=3  out:4
    _fb_info  CC=2  out:11
  src.vdisplay.capture.providers.x11  [2 funcs]
    capture_full  CC=4  out:6
    capture_region  CC=2  out:3
  src.vdisplay.cli  [2 funcs]
    build_parser  CC=1  out:3
    main  CC=2  out:4
  src.vdisplay.cli_handlers  [1 funcs]
    print_json  CC=1  out:1
  src.vdisplay.client  [4 funcs]
    __init__  CC=2  out:2
    _normalize_payload  CC=1  out:1
    request  CC=3  out:8
    _route_command  CC=14  out:8
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.agent  [2 funcs]
    _agent_client  CC=2  out:3
    handle  CC=12  out:23
  src.vdisplay.commands.all_cmd  [4 funcs]
    handle  CC=1  out:3
    handle_outputs  CC=1  out:3
    register  CC=1  out:4
    register_outputs  CC=1  out:4
  src.vdisplay.commands.common  [4 funcs]
    add_all_arg  CC=1  out:1
    add_display_arg  CC=1  out:1
    add_window_filter_args  CC=1  out:7
    include_all_from_args  CC=2  out:3
  src.vdisplay.commands.diagnose  [2 funcs]
    handle  CC=2  out:4
    register  CC=1  out:4
  src.vdisplay.commands.info  [1 funcs]
    handle  CC=1  out:2
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
  src.vdisplay.commands.sampler  [3 funcs]
    _config_from_args  CC=1  out:1
    handle  CC=17  out:30
    register  CC=1  out:22
  src.vdisplay.commands.screenshot  [2 funcs]
    handle  CC=1  out:2
    register  CC=1  out:14
  src.vdisplay.commands.virtual  [1 funcs]
    handle  CC=6  out:9
  src.vdisplay.commands.windows  [2 funcs]
    handle  CC=1  out:3
    register  CC=1  out:4
  src.vdisplay.discovery  [13 funcs]
    _attach_output_nl  CC=2  out:3
    _display_hint  CC=3  out:2
    _list_monitors  CC=6  out:10
    _looks_like_xvfb_only  CC=4  out:4
    _merge_output_metadata  CC=3  out:18
    _parse_xrandr_query  CC=8  out:12
    diagnose_display  CC=10  out:19
    find_window_suggestions  CC=2  out:2
    list_monitors  CC=1  out:1
    list_outputs  CC=8  out:27
  src.vdisplay.input.linux_xdotool  [4 funcs]
    click  CC=1  out:4
    hotkey  CC=1  out:3
    move  CC=1  out:5
    type_text  CC=1  out:3
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
  src.vdisplay.utils  [3 funcs]
    require_command  CC=2  out:2
    run_command  CC=2  out:4
    run_command_bytes  CC=1  out:1
  src.vdisplay.windows.filter  [12 funcs]
    filter_windows  CC=14  out:6
    is_companion_frame  CC=9  out:11
    is_internal_window  CC=13  out:6
    is_junk_title  CC=6  out:2
    is_trivial_internal  CC=5  out:0
    is_visible_app  CC=9  out:1
    looks_like_internal_class  CC=3  out:2
    looks_like_internal_name  CC=3  out:2
    matches_app  CC=7  out:6
    matches_class  CC=5  out:4
  src.vdisplay.windows.normalize  [7 funcs]
    derive_app_label  CC=14  out:4
    derive_role  CC=10  out:3
    normalize_atom_list  CC=3  out:6
    parse_wm_class  CC=7  out:9
    process_info  CC=6  out:10
    resolve_window_pid  CC=3  out:8
    usable_title  CC=3  out:3
  src.vdisplay.windows.query  [6 funcs]
    find_companion_frames  CC=8  out:10
    find_windows  CC=6  out:5
    inspect_window  CC=9  out:21
    list_windows_enriched  CC=2  out:5
    pick_best_window  CC=8  out:3
    scan_windows  CC=4  out:4
  src.vdisplay.windows.rank  [3 funcs]
    dedupe_app_windows  CC=5  out:9
    pick_best_from_group  CC=9  out:7
    pick_largest  CC=1  out:1
  src.vdisplay.windows.scan  [7 funcs]
    decode_xprop_value  CC=6  out:6
    format_window_id  CC=3  out:3
    root_window_id  CC=3  out:6
    search_window_ids  CC=4  out:6
    window_geometry  CC=4  out:8
    xdotool  CC=1  out:1
    xprop  CC=5  out:11

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
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry._load_schema
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_windows → packages.dsl2vdisplay.src.dsl2vdisplay.grammar._with_display
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_windows → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_screenshot → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_virtual_start → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_launch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_mirror → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_adopt → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar._parse_release → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.split_command
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
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_adopt → src.vdisplay.discovery.resolve_host_display
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_release → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._ok
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_release → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command._err
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_release → src.vdisplay.discovery.resolve_host_display
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_outputs → packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_monitors
  packages.cli2vdisplay.src.cli2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.uri2vdisplay.src.uri2vdisplay.cli.main → packages.uri2vdisplay.src.uri2vdisplay.decode.uri_to_dsl
  packages.uri2vdisplay.src.uri2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app → src.vdisplay.agent_config.resolve_agent_url
  packages.vdisplay-agent.src.vdisplay_agent.cli.main → packages.rest2vdisplay.src.rest2vdisplay.app.create_app
  packages.vdisplay-agent.src.vdisplay_agent.serve_port._pids_from_ss → packages.vdisplay-agent.src.vdisplay_agent.serve_port._parse_ss_pids
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.find_listener_pids → packages.vdisplay-agent.src.vdisplay_agent.serve_port._pids_from_ss
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.find_listener_pids → packages.vdisplay-agent.src.vdisplay_agent.serve_port._pids_from_lsof
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.stop_pids → packages.vdisplay-agent.src.vdisplay_agent.serve_port._pid_alive
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.ensure_broker_port_free → packages.vdisplay-agent.src.vdisplay_agent.serve_port.find_listener_pids
  packages.vdisplay-agent.src.vdisplay_agent.serve_port.ensure_broker_port_free → packages.vdisplay-agent.src.vdisplay_agent.serve_port._probe_is_vdisplay_agent
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 161f 16344L | python:117,json:14,toml:8,shell:7,yml:5,yaml:4,txt:1 | 2026-06-09
# generated in 0.03s
# CC̅=3.2 | critical:6/613 | dups:0 | cycles:0

HEALTH[6]:
  🟡 CC    handle CC=17 (limit:15)
  🟡 CC    capture_host_png CC=15 (limit:15)
  🟡 CC    capture_all_monitors CC=21 (limit:15)
  🟡 CC    assess_unattended_capture CC=17 (limit:15)
  🟡 CC    start CC=19 (limit:15)
  🟡 CC    _run CC=17 (limit:15)

REFACTOR[1]:
  1. split 6 high-CC methods  (CC>15)

PIPELINES[298]:
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
  [10] Src [_parse_release]: _parse_release → pick_flag
      PURITY: 100% pure
  [11] Src [handle_screenshot]: handle_screenshot → _ok
      PURITY: 100% pure
  [12] Src [handle_virtual_start]: handle_virtual_start → _ok
      PURITY: 100% pure
  [13] Src [handle_mirror]: handle_mirror → resolve_host_display → _looks_like_xvfb_only
      PURITY: 100% pure
  [14] Src [handle_adopt]: handle_adopt → _ok
      PURITY: 100% pure
  [15] Src [handle_release]: handle_release → _ok
      PURITY: 100% pure
  [16] Src [handle_health]: handle_health
      PURITY: 100% pure
  [17] Src [handle_info]: handle_info
      PURITY: 100% pure
  [18] Src [handle_outputs]: handle_outputs → handle_monitors
      PURITY: 100% pure
  [19] Src [handle_all]: handle_all
      PURITY: 100% pure
  [20] Src [handle_capabilities]: handle_capabilities
      PURITY: 100% pure
  [21] Src [handle_validate]: handle_validate
      PURITY: 100% pure
  [22] Src [main]: main → dispatch → _dispatch_legacy → validate_command_dict → ...(3 more)
      PURITY: 100% pure
  [23] Src [main]: main → uri_to_dsl
      PURITY: 100% pure
  [24] Src [main]: main → create_app → resolve_agent_url → _probe_default_agent → ...(1 more)
      PURITY: 100% pure
  [25] Src [main]: main → run_nl_prompt → nl_to_dsl → parse_display
      PURITY: 100% pure
  [26] Src [parse_display]: parse_display
      PURITY: 100% pure
  [27] Src [platform_capabilities]: platform_capabilities
      PURITY: 100% pure
  [28] Src [diagnostics]: diagnostics
      PURITY: 100% pure
  [29] Src [outputs]: outputs
      PURITY: 100% pure
  [30] Src [start_virtual]: start_virtual
      PURITY: 100% pure
  [31] Src [start_mirror]: start_mirror
      PURITY: 100% pure
  [32] Src [start_relay]: start_relay
      PURITY: 100% pure
  [33] Src [start_screencast]: start_screencast
      PURITY: 100% pure
  [34] Src [stop_screencast]: stop_screencast
      PURITY: 100% pure
  [35] Src [screencast_status]: screencast_status
      PURITY: 100% pure
  [36] Src [stop_session]: stop_session
      PURITY: 100% pure
  [37] Src [start_sampler]: start_sampler
      PURITY: 100% pure
  [38] Src [stop_sampler]: stop_sampler
      PURITY: 100% pure
  [39] Src [sampler_status]: sampler_status
      PURITY: 100% pure
  [40] Src [capture_frame]: capture_frame
      PURITY: 100% pure
  [41] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [42] Src [release_window]: release_window
      PURITY: 100% pure
  [43] Src [shutdown]: shutdown
      PURITY: 100% pure
  [44] Src [main]: main → create_app → resolve_agent_url → _probe_default_agent → ...(1 more)
      PURITY: 100% pure
  [45] Src [create_app]: create_app → success → agent_meta
      PURITY: 100% pure
  [46] Src [get]: get
      PURITY: 100% pure
  [47] Src [pop]: pop
      PURITY: 100% pure
  [48] Src [relay_session]: relay_session
      PURITY: 100% pure
  [49] Src [clear_relay]: clear_relay
      PURITY: 100% pure
  [50] Src [json_success]: json_success → from_runtime → success → agent_meta
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=3.3    ←in:0  →out:0
  │ !! portal_screencast          741L  1C   31m  CC=19     ←5
  │ !! host                       543L  0C   10m  CC=21     ←4
  │ linux_x11_relay            478L  2C   24m  CC=12     ←0
  │ discovery                  352L  0C   13m  CC=10     ←14
  │ linux_xwd                  320L  0C   21m  CC=12     ←11
  │ client                     307L  1C   28m  CC=14     ←0
  │ !! sampler_loop               277L  3C   10m  CC=17     ←1
  │ linux_x11_mirror           259L  1C   17m  CC=10     ←1
  │ session                    245L  0C   10m  CC=4      ←0
  │ discovery                  236L  0C   11m  CC=4      ←0
  │ portal                     221L  1C    7m  CC=11     ←1
  │ query                      209L  0C    6m  CC=9      ←3
  │ api                        193L  3C   32m  CC=6      ←3
  │ agent                      191L  0C   14m  CC=6      ←1
  │ commands                   183L  3C    5m  CC=4      ←0
  │ capture                    182L  0C    5m  CC=9      ←1
  │ local                      173L  0C   13m  CC=4      ←1
  │ filter                     173L  0C   12m  CC=14     ←2
  │ linux_xvfb                 164L  1C   14m  CC=8      ←0
  │ nl                         158L  0C    8m  CC=14     ←3
  │ nlp                        158L  0C   14m  CC=10     ←2
  │ !! policy                     141L  1C    2m  CC=17     ←2
  │ !! sampler                    118L  0C    3m  CC=17     ←0
  │ relay                      110L  0C    3m  CC=5      ←0
  │ agent                      110L  0C    3m  CC=12     ←0
  │ scan                       110L  0C    7m  CC=6      ←2
  │ sampler                    109L  1C    3m  CC=5      ←1
  │ normalize                  103L  0C    7m  CC=14     ←1
  │ engine                      99L  0C    6m  CC=11     ←4
  │ img2nl_enrich               97L  0C    5m  CC=9      ←0
  │ drm                         92L  1C    5m  CC=11     ←0
  │ payloads                    86L  0C    5m  CC=1      ←2
  │ runtime                     82L  1C    7m  CC=6      ←3
  │ virtual                     81L  0C    2m  CC=6      ←0
  │ fbdev                       77L  1C    5m  CC=7      ←0
  │ agent_config                71L  0C    8m  CC=6      ←14
  │ base                        64L  1C   11m  CC=1      ←0
  │ mss                         60L  1C    5m  CC=8      ←0
  │ mirror                      53L  0C    2m  CC=3      ←0
  │ screenshot                  53L  0C    2m  CC=1      ←0
  │ executor                    51L  0C    2m  CC=6      ←4
  │ info                        51L  0C    1m  CC=6      ←0
  │ utils                       46L  0C    3m  CC=2      ←8
  │ all_cmd                     46L  0C    4m  CC=1      ←0
  │ __init__                    46L  0C    0m  CC=0.0    ←0
  │ linux_xdotool               45L  1C    6m  CC=2      ←0
  │ rank                        43L  0C    5m  CC=9      ←1
  │ __init__                    42L  0C    1m  CC=2      ←1
  │ errors                      39L  2C    2m  CC=4      ←3
  │ common                      35L  0C    4m  CC=2      ←7
  │ x11                         35L  1C    4m  CC=4      ←0
  │ cli_handlers                34L  0C    6m  CC=1      ←11
  │ mirror_stub                 34L  1C    4m  CC=1      ←0
  │ cli                         32L  0C    2m  CC=2      ←0
  │ agent_dispatch              30L  0C    2m  CC=2      ←0
  │ windows                     29L  0C    2m  CC=1      ←0
  │ diagnose                    26L  0C    2m  CC=2      ←0
  │ models                      26L  2C    0m  CC=0.0    ←0
  │ nlp                         23L  0C    2m  CC=2      ←0
  │ base                        22L  2C    3m  CC=1      ←0
  │ monitors                    19L  0C    2m  CC=1      ←0
  │ constants                   19L  0C    0m  CC=0.0    ←0
  │ agent_envelope              17L  0C    1m  CC=6      ←1
  │ info                        16L  0C    2m  CC=1      ←0
  │ __init__                    15L  0C    0m  CC=0.0    ←0
  │ __init__                    14L  0C    1m  CC=2      ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ exceptions                  10L  3C    0m  CC=0.0    ←0
  │ base                         9L  1C    1m  CC=1      ←0
  │ io                           7L  0C    1m  CC=1      ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  packages/                       CC̄=3.1    ←in:0  →out:0
  │ server                     223L  0C    1m  CC=3      ←0
  │ grammar                    160L  0C   12m  CC=7      ←1
  │ serve_port                 146L  0C    8m  CC=13     ←2
  │ sampler                    144L  0C    7m  CC=12     ←0
  │ sessions                   123L  0C    9m  CC=4      ←0
  │ command                    120L  0C    7m  CC=3      ←0
  │ query                      115L  0C    8m  CC=4      ←1
  │ bus                        108L  0C    4m  CC=13     ←6
  │ capture                     96L  0C    5m  CC=8      ←0
  │ server                      95L  0C    1m  CC=1      ←0
  │ app                         87L  0C    1m  CC=2      ←3
  │ envelope                    85L  0C    9m  CC=6      ←1
  │ runtime                     80L  1C   18m  CC=1      ←1
  │ cli                         70L  0C    3m  CC=10     ←0
  │ session_store               63L  2C    5m  CC=5      ←1
  │ capabilities                51L  0C    2m  CC=5      ←0
  │ schemas                     50L  0C    0m  CC=0.0    ←0
  │ cli                         43L  0C    1m  CC=4      ←0
  │ cli                         41L  0C    1m  CC=7      ←0
  │ schema_registry             38L  0C    4m  CC=3      ←3
  │ cli                         35L  0C    1m  CC=3      ←0
  │ cli                         34L  0C    1m  CC=7      ←0
  │ relay                       32L  0C    2m  CC=6      ←0
  │ decode                      31L  0C    1m  CC=7      ←1
  │ windows                     31L  0C    1m  CC=8      ←0
  │ cli                         30L  0C    1m  CC=4      ←0
  │ pyproject.toml              28L  0C    0m  CC=0.0    ←0
  │ result                      26L  1C    1m  CC=1      ←0
  │ cli                         23L  0C    2m  CC=2      ←0
  │ outputs                     19L  0C    1m  CC=2      ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ to_dsl                      13L  0C    2m  CC=1      ←1
  │ mirror.schema.json          13L  0C    0m  CC=0.0    ←0
  │ screenshot.schema.json      13L  0C    0m  CC=0.0    ←0
  │ outputs.schema.json         10L  0C    0m  CC=0.0    ←0
  │ info.schema.json            10L  0C    0m  CC=0.0    ←0
  │ validate.schema.json        10L  0C    0m  CC=0.0    ←0
  │ health.schema.json           9L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=3.0    ←in:0  →out:0
  │ !! after_adopt.png.meta.json   584L  0C    0m  CC=0.0    ←0
  │ !! after_release.png.meta.json   551L  0C    0m  CC=0.0    ←0
  │ !! before_automation.png.meta.json   551L  0C    0m  CC=0.0    ←0
  │ screenshot_meta            162L  0C    9m  CC=14     ←5
  │ run_all_examples.sh        152L  0C    9m  CC=0.0    ←0
  │ relay_demo                 137L  0C    3m  CC=11     ←0
  │ mirror_demo                 97L  0C    2m  CC=7      ←0
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
  │ run.sh                      26L  0C    1m  CC=0.0    ←0
  │ run-host.sh                 25L  0C    0m  CC=0.0    ←0
  │ run-host.sh                 24L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  19L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          17L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          16L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          14L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          12L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          11L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ tree.txt                   241L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             128L  0C    0m  CC=0.0    ←0
  │ app.vql.json               127L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                          src.vdisplay    packages.vdisplay-agent      packages.dsl2vdisplay            examples.common     packages.rest2vdisplay      packages.mcp2vdisplay       examples.host-mirror        examples.host-relay          examples.ci-agent  examples.headless-virtual      packages.cli2vdisplay      packages.nlp2vdisplay      examples.agent-broker      packages.uri2vdisplay
               src.vdisplay                         ──                          3                          2                         ←1                          1                         ←4                         ←3                         ←3                                                                                                          ←1                         ←1                             hub
    packages.vdisplay-agent                         21                         ──                                                                                1                                                                                                                                                                                                                                                     !! fan-out
      packages.dsl2vdisplay                          5                                                    ──                                                    ←4                         ←2                                                                                                                                     ←2                                                                               ←1  hub
            examples.common                          1                                                                               ──                                                                               ←3                         ←3                         ←2                         ←2                                                                                                              hub
     packages.rest2vdisplay                          2                         ←1                          4                                                    ──                                                                                                                                                                                                                                                   
      packages.mcp2vdisplay                          4                                                     2                                                                               ──                                                                                                                                                                 1                                                      
       examples.host-mirror                          3                                                                                3                                                                               ──                                                                                                                                                                                             
        examples.host-relay                          3                                                                                3                                                                                                          ──                                                                                                                                                                  
          examples.ci-agent                                                                                                           2                                                                                                                                     ──                                                                                                                                       
  examples.headless-virtual                                                                                                           2                                                                                                                                                                ──                                                                                                            
      packages.cli2vdisplay                                                                                2                                                                                                                                                                                                                      ──                                                                                 
      packages.nlp2vdisplay                          1                                                                                                                                     ←1                                                                                                                                                                ──                                                      
      examples.agent-broker                          1                                                                                                                                                                                                                                                                                                                                  ──                           
      packages.uri2vdisplay                                                                                1                                                                                                                                                                                                                                                                                                       ──
  CYCLES: none
  HUB: packages.dsl2vdisplay/ (fan-in=11)
  HUB: src.vdisplay/ (fan-in=41)
  HUB: examples.common/ (fan-in=10)
  SMELL: packages.vdisplay-agent/ fan-out=22 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 8 groups | 116f 11212L | 2026-06-09

SUMMARY:
  files_scanned: 116
  total_lines:   11212
  dup_groups:    8
  dup_fragments: 20
  saved_lines:   109
  scan_ms:       2351

HOTSPOTS[7] (files with most duplication):
  src/vdisplay/payloads.py  dup=46L  groups=1  frags=2  (0.4%)
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py  dup=34L  groups=1  frags=2  (0.3%)
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py  dup=20L  groups=1  frags=2  (0.2%)
  src/vdisplay/api.py  dup=12L  groups=1  frags=3  (0.1%)
  examples/ci-agent/agent.py  dup=11L  groups=1  frags=1  (0.1%)
  examples/headless-virtual/run_virtual.py  dup=11L  groups=1  frags=1  (0.1%)
  examples/host-mirror/mirror_demo.py  dup=11L  groups=1  frags=1  (0.1%)

DUPLICATES[8] (ranked by impact):
  [443c93126a62d7a9] ! EXAC  _load_common  L=11 N=4 saved=33 sim=1.00
      examples/ci-agent/agent.py:15-25  (_load_common)
      examples/headless-virtual/run_virtual.py:13-23  (_load_common)
      examples/host-mirror/mirror_demo.py:16-26  (_load_common)
      examples/host-relay/relay_demo.py:17-27  (_load_common)
  [673d29d90b55293e]   STRU  local_windows_payload  L=23 N=2 saved=23 sim=1.00
      src/vdisplay/payloads.py:14-36  (local_windows_payload)
      src/vdisplay/payloads.py:39-61  (windows_payload)
  [1e6593980c4874fb]   STRU  handle_windows  L=17 N=2 saved=17 sim=1.00
      packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py:46-62  (handle_windows)
      packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py:65-81  (handle_all)
  [074206dcbb6b73b7]   STRU  _parse_mirror  L=10 N=2 saved=10 sim=1.00
      packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:76-85  (_parse_mirror)
      packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:102-111  (_parse_release)
  [25fa0495b0a2c2f8]   STRU  register  L=5 N=3 saved=10 sim=1.00
      src/vdisplay/commands/all_cmd.py:12-16  (register)
      src/vdisplay/commands/monitors.py:10-14  (register)
      src/vdisplay/commands/windows.py:10-14  (register)
  [b8e2782d68a777c3]   STRU  _default_virtual_backend  L=4 N=3 saved=8 sim=1.00
      src/vdisplay/api.py:13-16  (_default_virtual_backend)
      src/vdisplay/api.py:19-22  (_default_mirror_backend)
      src/vdisplay/api.py:25-28  (_default_relay_backend)
  [7168a023bfc45913]   EXAC  _system_python  L=5 N=2 saved=5 sim=1.00
      src/vdisplay/capture/portal.py:81-85  (_system_python)
      src/vdisplay/capture/portal_screencast.py:198-202  (_system_python)
  [f5bfacfda8981cef]   STRU  looks_like_internal_class  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/windows/filter.py:8-10  (looks_like_internal_class)
      src/vdisplay/windows/filter.py:13-15  (looks_like_internal_name)

REFACTOR[8] (ranked by priority):
  [1] ○ extract_function   → examples/utils/_load_common.py
      WHY: 4 occurrences of 11-line block across 4 files — saves 33 lines
      FILES: examples/ci-agent/agent.py, examples/headless-virtual/run_virtual.py, examples/host-mirror/mirror_demo.py, examples/host-relay/relay_demo.py
  [2] ○ extract_function   → src/vdisplay/utils/local_windows_payload.py
      WHY: 2 occurrences of 23-line block across 1 files — saves 23 lines
      FILES: src/vdisplay/payloads.py
  [3] ○ extract_function   → packages/dsl2vdisplay/src/dsl2vdisplay/handlers/utils/handle_windows.py
      WHY: 2 occurrences of 17-line block across 1 files — saves 17 lines
      FILES: packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py
  [4] ○ extract_function   → packages/dsl2vdisplay/src/dsl2vdisplay/utils/_parse_mirror.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py
  [5] ○ extract_function   → src/vdisplay/commands/utils/register.py
      WHY: 3 occurrences of 5-line block across 3 files — saves 10 lines
      FILES: src/vdisplay/commands/all_cmd.py, src/vdisplay/commands/monitors.py, src/vdisplay/commands/windows.py
  [6] ○ extract_function   → src/vdisplay/utils/_default_virtual_backend.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/api.py
  [7] ○ extract_function   → src/vdisplay/capture/utils/_system_python.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: src/vdisplay/capture/portal.py, src/vdisplay/capture/portal_screencast.py
  [8] ○ extract_function   → src/vdisplay/windows/utils/looks_like_internal_class.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/vdisplay/windows/filter.py

QUICK_WINS[6] (low risk, high savings — do first):
  [1] extract_function   saved=33L  → examples/utils/_load_common.py
      FILES: agent.py, run_virtual.py, mirror_demo.py +1
  [2] extract_function   saved=23L  → src/vdisplay/utils/local_windows_payload.py
      FILES: payloads.py
  [3] extract_function   saved=17L  → packages/dsl2vdisplay/src/dsl2vdisplay/handlers/utils/handle_windows.py
      FILES: query.py
  [4] extract_function   saved=10L  → packages/dsl2vdisplay/src/dsl2vdisplay/utils/_parse_mirror.py
      FILES: grammar.py
  [5] extract_function   saved=10L  → src/vdisplay/commands/utils/register.py
      FILES: all_cmd.py, monitors.py, windows.py
  [6] extract_function   saved=8L  → src/vdisplay/utils/_default_virtual_backend.py
      FILES: api.py

EFFORT_ESTIMATE (total ≈ 3.6h):
  medium _load_common                        saved=33L  ~66min
  medium local_windows_payload               saved=23L  ~46min
  medium handle_windows                      saved=17L  ~34min
  easy   _parse_mirror                       saved=10L  ~20min
  easy   register                            saved=10L  ~20min
  easy   _default_virtual_backend            saved=8L  ~16min
  easy   _system_python                      saved=5L  ~10min
  easy   looks_like_internal_class           saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  8 → 0
  saved_lines: 109 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 578 func | 93f | 2026-06-09
# generated in 0.00s

NEXT[9] (ranked by impact):
  [1] !! SPLIT           src/vdisplay/capture/portal_screencast.py
      WHY: 741L, 1 classes, max CC=19
      EFFORT: ~4h  IMPACT: 14079

  [2] !! SPLIT           src/vdisplay/capture/host.py
      WHY: 543L, 0 classes, max CC=21
      EFFORT: ~4h  IMPACT: 11403

  [3] !  SPLIT-FUNC      capture_all_monitors  CC=21  fan=20
      WHY: CC=21 exceeds 15
      EFFORT: ~1h  IMPACT: 420

  [4] !  SPLIT-FUNC      capture_host_png  CC=15  fan=26
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 390

  [5] !  SPLIT-FUNC      SamplerLoop._run  CC=17  fan=22
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 374

  [6] !  SPLIT-FUNC      handle  CC=17  fan=17
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 289

  [7] !  SPLIT-FUNC      PortalScreenCastSession.start  CC=19  fan=13
      WHY: CC=19 exceeds 15
      EFFORT: ~1h  IMPACT: 247

  [8] !  SPLIT-FUNC      assess_unattended_capture  CC=17  fan=12
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 204

  [9] !! SPLIT           planfile.yaml
      WHY: 1319L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting src/vdisplay/capture/portal_screencast.py may break 31 import paths
  ⚠ Splitting src/vdisplay/capture/host.py may break 10 import paths

METRICS-TARGET:
  CC̄:          3.2 → ≤2.2
  max-CC:      21 → ≤10
  god-modules: 4 → 0
  high-CC(≥15): 6 → ≤3
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
  prev CC̄=3.2 → now CC̄=3.2
```

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

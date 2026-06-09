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
- **version**: `0.1.3`
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
  version: 0.1.3;
}

dependencies {
  pillow: Pillow>=10.0;
  dev: "pytest>=8.0, Pillow>=10.0, fastapi>=0.110, httpx>=0.27, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
  control: "dsl2vdisplay, nlp2vdisplay";
  agent: "vdisplay-agent, fastapi>=0.110, uvicorn>=0.27";
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
  keys: OPENROUTER_API_KEY, LLM_MODEL, VDISPLAY_AGENT_URL, VDISPLAY_AGENT_TOKEN, VDISPLAY_AGENT_BROKER, DISPLAY, XDG_SESSION_TYPE, VDISPLAY_AGENT_HOST, VDISPLAY_AGENT_PORT, WAYLAND_DISPLAY, VDISPLAY_CAPTURE_ALLOW_PORTAL;
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
```

## Call Graph

*295 nodes · 382 edges · 62 modules · CC̄=3.2*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `capture_frame` *(in packages.vdisplay-agent.src.vdisplay_agent.runtime.AgentRuntime)* | 10 ⚠ | 0 | 41 | **41** |
| `create_app` *(in packages.rest2vdisplay.src.rest2vdisplay.app)* | 2 | 3 | 38 | **41** |
| `list_outputs` *(in src.vdisplay.discovery)* | 8 | 9 | 27 | **36** |
| `run_command` *(in src.vdisplay.utils)* | 2 | 29 | 4 | **33** |
| `main` *(in examples.host-relay.relay_demo)* | 11 ⚠ | 0 | 33 | **33** |
| `capture_host_png` *(in src.vdisplay.capture.host)* | 13 ⚠ | 2 | 29 | **31** |
| `dispatch` *(in packages.dsl2vdisplay.src.dsl2vdisplay.bus)* | 10 ⚠ | 9 | 21 | **30** |
| `_portal_impl` *(in src.vdisplay.capture.portal)* | 4 | 1 | 28 | **29** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/vdisplay
# generated in 0.20s
# nodes: 295 | edges: 382 | modules: 62
# CC̄=3.2

HUBS[20]:
  packages.vdisplay-agent.src.vdisplay_agent.runtime.AgentRuntime.capture_frame
    CC=10  in:0  out:41  total:41
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  src.vdisplay.utils.run_command
    CC=2  in:29  out:4  total:33
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  src.vdisplay.capture.host.capture_host_png
    CC=13  in:2  out:29  total:31
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=10  in:9  out:21  total:30
  src.vdisplay.capture.portal._portal_impl
    CC=4  in:1  out:28  total:29
  examples.host-mirror.mirror_demo.main
    CC=5  in:0  out:28  total:28
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window
    CC=12  in:0  out:27  total:27
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
    CC=3  in:23  out:2  total:25
  src.vdisplay.discovery.resolve_host_display
    CC=9  in:17  out:6  total:23
  src.vdisplay.windows.query.inspect_window
    CC=9  in:2  out:21  total:23
  examples.common.validate_artifacts.validate_image_and_meta
    CC=12  in:1  out:22  total:23
  src.vdisplay.capture.providers.fbdev.FbdevProvider._capture
    CC=7  in:0  out:22  total:22
  src.vdisplay.backends.linux_x11_relay._output_origin
    CC=11  in:1  out:20  total:21
  src.vdisplay.agent_dispatch._dispatch_all
    CC=1  in:0  out:20  total:20
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:20  total:20
  src.vdisplay.nl.window_center_on_output
    CC=3  in:2  out:18  total:20
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand
    CC=9  in:1  out:19  total:20

MODULES:
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
    main  CC=5  out:28
  examples.host-relay.relay_demo  [2 funcs]
    _capture_phase  CC=1  out:6
    main  CC=11  out:33
  packages.cli2vdisplay.src.cli2vdisplay.cli  [1 funcs]
    main  CC=7  out:16
  packages.dsl2vdisplay.src.dsl2vdisplay.bus  [4 funcs]
    _dispatch_cmd  CC=3  out:11
    _dispatch_query  CC=2  out:7
    dispatch  CC=10  out:21
    execute_dsl_line  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.cli  [3 funcs]
    _main_legacy  CC=10  out:17
    _main_subcommand  CC=9  out:19
    main  CC=4  out:3
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar  [12 funcs]
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
    create_server  CC=1  out:20
  packages.rest2vdisplay.src.rest2vdisplay.app  [1 funcs]
    create_app  CC=2  out:38
  packages.uri2vdisplay.src.uri2vdisplay.cli  [1 funcs]
    main  CC=4  out:13
  packages.uri2vdisplay.src.uri2vdisplay.decode  [1 funcs]
    uri_to_dsl  CC=7  out:12
  packages.vdisplay-agent.src.vdisplay_agent.cli  [1 funcs]
    main  CC=3  out:13
  packages.vdisplay-agent.src.vdisplay_agent.runtime  [4 funcs]
    capture_frame  CC=10  out:41
    diagnostics  CC=1  out:4
    outputs  CC=2  out:4
    platform_capabilities  CC=3  out:10
  src.vdisplay.agent_config  [3 funcs]
    resolve_agent_token  CC=3  out:2
    resolve_agent_url  CC=4  out:3
    use_agent  CC=2  out:4
  src.vdisplay.agent_dispatch  [16 funcs]
    _dispatch_adopt  CC=1  out:10
    _dispatch_all  CC=1  out:20
    _dispatch_capabilities  CC=1  out:3
    _dispatch_health  CC=1  out:2
    _dispatch_info  CC=3  out:3
    _dispatch_mirror  CC=5  out:17
    _dispatch_monitors  CC=2  out:9
    _dispatch_release  CC=1  out:9
    _dispatch_screenshot  CC=5  out:12
    _dispatch_validate  CC=4  out:11
  src.vdisplay.api  [7 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.application.runtime  [4 funcs]
    agent_client_optional  CC=2  out:2
    agent_client_required  CC=2  out:2
    prefer_agent  CC=1  out:1
    resolve_apps_only  CC=3  out:0
  src.vdisplay.application.services.capture  [4 funcs]
    _capture_local  CC=7  out:10
    _capture_via_agent  CC=8  out:10
    capture_screenshot  CC=3  out:4
    capture_screenshot_via_client  CC=1  out:1
  src.vdisplay.application.services.discovery  [6 funcs]
    diagnose  CC=2  out:2
    list_adopted  CC=1  out:4
    list_all  CC=4  out:4
    list_monitors  CC=4  out:8
    list_windows_local  CC=2  out:6
    list_windows_payload  CC=10  out:9
  src.vdisplay.application.services.info  [1 funcs]
    platform_info  CC=2  out:8
  src.vdisplay.application.services.session  [2 funcs]
    mirror_screenshot  CC=1  out:3
    relay_screenshot  CC=1  out:1
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
  src.vdisplay.capture.host  [6 funcs]
    _capture_all_from_driver_full  CC=7  out:15
    _monitor_capture_region  CC=4  out:10
    _monitor_source_name  CC=9  out:13
    capture_all_monitors  CC=11  out:16
    capture_host_png  CC=13  out:29
    capture_host_to_file  CC=3  out:10
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
  src.vdisplay.capture.portal  [6 funcs]
    capture_full  CC=1  out:1
    capture_region  CC=1  out:2
    _capture_portal_to_file  CC=11  out:13
    _portal_impl  CC=4  out:28
    _system_python  CC=4  out:3
    capture_portal_png  CC=4  out:11
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
  src.vdisplay.cli_handlers  [2 funcs]
    all_payload  CC=1  out:1
    print_json  CC=1  out:1
  src.vdisplay.client  [1 funcs]
    __init__  CC=2  out:2
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.agent  [1 funcs]
    handle  CC=7  out:12
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
    handle  CC=1  out:2
    register  CC=1  out:3
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
  src.vdisplay.commands.screenshot  [2 funcs]
    handle  CC=1  out:2
    register  CC=1  out:13
  src.vdisplay.commands.virtual  [1 funcs]
    handle  CC=4  out:7
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
    diagnose_display  CC=5  out:12
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
  packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_cmd → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → src.vdisplay.agent_config.use_agent
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_query
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_cmd
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.to_text
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
  packages.cli2vdisplay.src.cli2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.uri2vdisplay.src.uri2vdisplay.cli.main → packages.uri2vdisplay.src.uri2vdisplay.decode.uri_to_dsl
  packages.uri2vdisplay.src.uri2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app → src.vdisplay.agent_config.resolve_agent_url
  packages.vdisplay-agent.src.vdisplay_agent.cli.main → packages.rest2vdisplay.src.rest2vdisplay.app.create_app
  examples.host-mirror.mirror_demo.main → src.vdisplay.discovery.diagnose_display
  examples.host-mirror.mirror_demo.main → src.vdisplay.discovery.list_monitors
  examples.host-mirror.mirror_demo.main → src.vdisplay.cli_handlers.all_payload
  examples.host-relay.relay_demo._capture_phase → src.vdisplay.cli_handlers.all_payload
  examples.host-relay.relay_demo._capture_phase → src.vdisplay.capture.linux_xwd.capture_display_png
  examples.host-relay.relay_demo._capture_phase → examples.common.screenshot_meta.save_png_with_meta
  examples.host-relay.relay_demo._capture_phase → examples.common.screenshot_meta.print_artifact
  examples.host-relay.relay_demo.main → src.vdisplay.discovery.resolve_host_display
  examples.host-relay.relay_demo.main → examples.host-relay.relay_demo._capture_phase
  examples.common.validate_artifacts.validate_image_and_meta → examples.common.screenshot_meta.meta_path_for
  examples.common.validate_artifacts.validate_image_and_meta → examples.common.screenshot_meta.png_dimensions
  examples.common.validate_artifacts.validate_directory → examples.common.validate_artifacts.validate_image_and_meta
  examples.common.validate_artifacts.main → examples.common.validate_artifacts.validate_directory
  examples.common.screenshot_meta.ensure_common_on_path → examples.common.screenshot_meta.examples_common_dir
  examples.common.screenshot_meta.build_screenshot_meta → examples.common.screenshot_meta.png_dimensions
  examples.common.screenshot_meta.build_screenshot_meta → examples.common.screenshot_meta.describe_screenshot_nl
  examples.common.screenshot_meta.build_screenshot_meta → examples.common.screenshot_meta.meta_path_for
  examples.common.screenshot_meta.write_screenshot_meta → examples.common.screenshot_meta.build_screenshot_meta
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
# generated in 0.20s
# nodes: 295 | edges: 382 | modules: 62
# CC̄=3.2

HUBS[20]:
  packages.vdisplay-agent.src.vdisplay_agent.runtime.AgentRuntime.capture_frame
    CC=10  in:0  out:41  total:41
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  src.vdisplay.utils.run_command
    CC=2  in:29  out:4  total:33
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  src.vdisplay.capture.host.capture_host_png
    CC=13  in:2  out:29  total:31
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=10  in:9  out:21  total:30
  src.vdisplay.capture.portal._portal_impl
    CC=4  in:1  out:28  total:29
  examples.host-mirror.mirror_demo.main
    CC=5  in:0  out:28  total:28
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window
    CC=12  in:0  out:27  total:27
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
    CC=3  in:23  out:2  total:25
  src.vdisplay.discovery.resolve_host_display
    CC=9  in:17  out:6  total:23
  src.vdisplay.windows.query.inspect_window
    CC=9  in:2  out:21  total:23
  examples.common.validate_artifacts.validate_image_and_meta
    CC=12  in:1  out:22  total:23
  src.vdisplay.capture.providers.fbdev.FbdevProvider._capture
    CC=7  in:0  out:22  total:22
  src.vdisplay.backends.linux_x11_relay._output_origin
    CC=11  in:1  out:20  total:21
  src.vdisplay.agent_dispatch._dispatch_all
    CC=1  in:0  out:20  total:20
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:20  total:20
  src.vdisplay.nl.window_center_on_output
    CC=3  in:2  out:18  total:20
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand
    CC=9  in:1  out:19  total:20

MODULES:
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
    main  CC=5  out:28
  examples.host-relay.relay_demo  [2 funcs]
    _capture_phase  CC=1  out:6
    main  CC=11  out:33
  packages.cli2vdisplay.src.cli2vdisplay.cli  [1 funcs]
    main  CC=7  out:16
  packages.dsl2vdisplay.src.dsl2vdisplay.bus  [4 funcs]
    _dispatch_cmd  CC=3  out:11
    _dispatch_query  CC=2  out:7
    dispatch  CC=10  out:21
    execute_dsl_line  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.cli  [3 funcs]
    _main_legacy  CC=10  out:17
    _main_subcommand  CC=9  out:19
    main  CC=4  out:3
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar  [12 funcs]
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
    create_server  CC=1  out:20
  packages.rest2vdisplay.src.rest2vdisplay.app  [1 funcs]
    create_app  CC=2  out:38
  packages.uri2vdisplay.src.uri2vdisplay.cli  [1 funcs]
    main  CC=4  out:13
  packages.uri2vdisplay.src.uri2vdisplay.decode  [1 funcs]
    uri_to_dsl  CC=7  out:12
  packages.vdisplay-agent.src.vdisplay_agent.cli  [1 funcs]
    main  CC=3  out:13
  packages.vdisplay-agent.src.vdisplay_agent.runtime  [4 funcs]
    capture_frame  CC=10  out:41
    diagnostics  CC=1  out:4
    outputs  CC=2  out:4
    platform_capabilities  CC=3  out:10
  src.vdisplay.agent_config  [3 funcs]
    resolve_agent_token  CC=3  out:2
    resolve_agent_url  CC=4  out:3
    use_agent  CC=2  out:4
  src.vdisplay.agent_dispatch  [16 funcs]
    _dispatch_adopt  CC=1  out:10
    _dispatch_all  CC=1  out:20
    _dispatch_capabilities  CC=1  out:3
    _dispatch_health  CC=1  out:2
    _dispatch_info  CC=3  out:3
    _dispatch_mirror  CC=5  out:17
    _dispatch_monitors  CC=2  out:9
    _dispatch_release  CC=1  out:9
    _dispatch_screenshot  CC=5  out:12
    _dispatch_validate  CC=4  out:11
  src.vdisplay.api  [7 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.application.runtime  [4 funcs]
    agent_client_optional  CC=2  out:2
    agent_client_required  CC=2  out:2
    prefer_agent  CC=1  out:1
    resolve_apps_only  CC=3  out:0
  src.vdisplay.application.services.capture  [4 funcs]
    _capture_local  CC=7  out:10
    _capture_via_agent  CC=8  out:10
    capture_screenshot  CC=3  out:4
    capture_screenshot_via_client  CC=1  out:1
  src.vdisplay.application.services.discovery  [6 funcs]
    diagnose  CC=2  out:2
    list_adopted  CC=1  out:4
    list_all  CC=4  out:4
    list_monitors  CC=4  out:8
    list_windows_local  CC=2  out:6
    list_windows_payload  CC=10  out:9
  src.vdisplay.application.services.info  [1 funcs]
    platform_info  CC=2  out:8
  src.vdisplay.application.services.session  [2 funcs]
    mirror_screenshot  CC=1  out:3
    relay_screenshot  CC=1  out:1
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
  src.vdisplay.capture.host  [6 funcs]
    _capture_all_from_driver_full  CC=7  out:15
    _monitor_capture_region  CC=4  out:10
    _monitor_source_name  CC=9  out:13
    capture_all_monitors  CC=11  out:16
    capture_host_png  CC=13  out:29
    capture_host_to_file  CC=3  out:10
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
  src.vdisplay.capture.portal  [6 funcs]
    capture_full  CC=1  out:1
    capture_region  CC=1  out:2
    _capture_portal_to_file  CC=11  out:13
    _portal_impl  CC=4  out:28
    _system_python  CC=4  out:3
    capture_portal_png  CC=4  out:11
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
  src.vdisplay.cli_handlers  [2 funcs]
    all_payload  CC=1  out:1
    print_json  CC=1  out:1
  src.vdisplay.client  [1 funcs]
    __init__  CC=2  out:2
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.agent  [1 funcs]
    handle  CC=7  out:12
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
    handle  CC=1  out:2
    register  CC=1  out:3
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
  src.vdisplay.commands.screenshot  [2 funcs]
    handle  CC=1  out:2
    register  CC=1  out:13
  src.vdisplay.commands.virtual  [1 funcs]
    handle  CC=4  out:7
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
    diagnose_display  CC=5  out:12
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
  packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_cmd → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → src.vdisplay.agent_config.use_agent
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_query
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_cmd
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.to_text
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
  packages.cli2vdisplay.src.cli2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.uri2vdisplay.src.uri2vdisplay.cli.main → packages.uri2vdisplay.src.uri2vdisplay.decode.uri_to_dsl
  packages.uri2vdisplay.src.uri2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app → src.vdisplay.agent_config.resolve_agent_url
  packages.vdisplay-agent.src.vdisplay_agent.cli.main → packages.rest2vdisplay.src.rest2vdisplay.app.create_app
  examples.host-mirror.mirror_demo.main → src.vdisplay.discovery.diagnose_display
  examples.host-mirror.mirror_demo.main → src.vdisplay.discovery.list_monitors
  examples.host-mirror.mirror_demo.main → src.vdisplay.cli_handlers.all_payload
  examples.host-relay.relay_demo._capture_phase → src.vdisplay.cli_handlers.all_payload
  examples.host-relay.relay_demo._capture_phase → src.vdisplay.capture.linux_xwd.capture_display_png
  examples.host-relay.relay_demo._capture_phase → examples.common.screenshot_meta.save_png_with_meta
  examples.host-relay.relay_demo._capture_phase → examples.common.screenshot_meta.print_artifact
  examples.host-relay.relay_demo.main → src.vdisplay.discovery.resolve_host_display
  examples.host-relay.relay_demo.main → examples.host-relay.relay_demo._capture_phase
  examples.common.validate_artifacts.validate_image_and_meta → examples.common.screenshot_meta.meta_path_for
  examples.common.validate_artifacts.validate_image_and_meta → examples.common.screenshot_meta.png_dimensions
  examples.common.validate_artifacts.validate_directory → examples.common.validate_artifacts.validate_image_and_meta
  examples.common.validate_artifacts.main → examples.common.validate_artifacts.validate_directory
  examples.common.screenshot_meta.ensure_common_on_path → examples.common.screenshot_meta.examples_common_dir
  examples.common.screenshot_meta.build_screenshot_meta → examples.common.screenshot_meta.png_dimensions
  examples.common.screenshot_meta.build_screenshot_meta → examples.common.screenshot_meta.describe_screenshot_nl
  examples.common.screenshot_meta.build_screenshot_meta → examples.common.screenshot_meta.meta_path_for
  examples.common.screenshot_meta.write_screenshot_meta → examples.common.screenshot_meta.build_screenshot_meta
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 132f 12993L | python:90,json:14,toml:8,shell:5,yml:5,yaml:4,txt:1 | 2026-06-09
# generated in 0.04s
# CC̅=3.2 | critical:0/439 | dups:0 | cycles:0

HEALTH[0]: ok

REFACTOR[0]: none needed

PIPELINES[216]:
  [1] Src [main]: main → create_server
      PURITY: 100% pure
  [2] Src [create_server]: create_server → resolve_agent_url
      PURITY: 100% pure
  [3] Src [main]: main → _main_legacy → execute_dsl_line → dispatch → ...(2 more)
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
  [11] Src [main]: main → dispatch → use_agent → resolve_agent_url
      PURITY: 100% pure
  [12] Src [main]: main → uri_to_dsl
      PURITY: 100% pure
  [13] Src [main]: main → create_app → resolve_agent_url
      PURITY: 100% pure
  [14] Src [main]: main → run_nl_prompt → nl_to_dsl → parse_display
      PURITY: 100% pure
  [15] Src [parse_display]: parse_display
      PURITY: 100% pure
  [16] Src [main]: main → create_app → resolve_agent_url
      PURITY: 100% pure
  [17] Src [create_app]: create_app
      PURITY: 100% pure
  [18] Src [_load_common]: _load_common
      PURITY: 100% pure
  [19] Src [main]: main → diagnose_display → resolve_host_display → _looks_like_xvfb_only
      PURITY: 100% pure
  [20] Src [_load_common]: _load_common
      PURITY: 100% pure
  [21] Src [main]: main → write_screenshot_meta → build_screenshot_meta → png_dimensions
      PURITY: 100% pure
  [22] Src [_load_common]: _load_common
      PURITY: 100% pure
  [23] Src [main]: main → write_screenshot_meta → build_screenshot_meta → png_dimensions
      PURITY: 100% pure
  [24] Src [_load_common]: _load_common
      PURITY: 100% pure
  [25] Src [main]: main → resolve_host_display → _looks_like_xvfb_only
      PURITY: 100% pure
  [26] Src [main]: main → validate_directory → validate_image_and_meta → meta_path_for
      PURITY: 100% pure
  [27] Src [ensure_common_on_path]: ensure_common_on_path → examples_common_dir
      PURITY: 100% pure
  [28] Src [__init__]: __init__ → resolve_agent_token
      PURITY: 100% pure
  [29] Src [_request]: _request
      PURITY: 100% pure
  [30] Src [health]: health
      PURITY: 100% pure
  [31] Src [capabilities]: capabilities
      PURITY: 100% pure
  [32] Src [diagnostics]: diagnostics
      PURITY: 100% pure
  [33] Src [outputs]: outputs
      PURITY: 100% pure
  [34] Src [windows]: windows
      PURITY: 100% pure
  [35] Src [start_virtual]: start_virtual
      PURITY: 100% pure
  [36] Src [start_mirror]: start_mirror
      PURITY: 100% pure
  [37] Src [start_relay]: start_relay
      PURITY: 100% pure
  [38] Src [stop_session]: stop_session
      PURITY: 100% pure
  [39] Src [capture_frame]: capture_frame
      PURITY: 100% pure
  [40] Src [capture_png_bytes]: capture_png_bytes
      PURITY: 100% pure
  [41] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [42] Src [release_window]: release_window
      PURITY: 100% pure
  [43] Src [create]: create → _default_virtual_backend
      PURITY: 100% pure
  [44] Src [start]: start
      PURITY: 100% pure
  [45] Src [stop]: stop
      PURITY: 100% pure
  [46] Src [launch]: launch
      PURITY: 100% pure
  [47] Src [screenshot_bytes]: screenshot_bytes
      PURITY: 100% pure
  [48] Src [save_screenshot]: save_screenshot
      PURITY: 100% pure
  [49] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [50] Src [release_window]: release_window
      PURITY: 100% pure

LAYERS:
  examples/                       CC̄=3.7    ←in:0  →out:0
  │ !! after_adopt.png.meta.json   584L  0C    0m  CC=0.0    ←0
  │ !! mirror.png.meta.json       565L  0C    0m  CC=0.0    ←0
  │ !! after_release.png.meta.json   551L  0C    0m  CC=0.0    ←0
  │ !! before_automation.png.meta.json   551L  0C    0m  CC=0.0    ←0
  │ screenshot_meta            162L  0C    9m  CC=14     ←5
  │ relay_demo                 138L  0C    3m  CC=11     ←0
  │ mirror_demo                 88L  0C    2m  CC=5      ←0
  │ validate_artifacts          84L  0C    3m  CC=12     ←0
  │ agent                       73L  0C    2m  CC=4      ←0
  │ run_virtual                 63L  0C    2m  CC=4      ←0
  │ run_all_examples.sh         62L  0C    2m  CC=0.0    ←0
  │ run.sh                      53L  0C    1m  CC=0.0    ←0
  │ run.sh                      47L  0C    1m  CC=0.0    ←0
  │ frame-001.png.meta.json     35L  0C    0m  CC=0.0    ←0
  │ frame-002.png.meta.json     35L  0C    0m  CC=0.0    ←0
  │ frame-000.png.meta.json     35L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  29L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  29L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  28L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  28L  0C    0m  CC=0.0    ←0
  │ screen.png.meta.json        28L  0C    0m  CC=0.0    ←0
  │ run-host.sh                 24L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  19L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          17L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          16L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          14L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          12L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          11L  0C    0m  CC=0.0    ←0
  │
  packages/                       CC̄=3.4    ←in:0  →out:0
  │ runtime                    253L  2C   13m  CC=10     ←0
  │ grammar                    160L  0C   12m  CC=7      ←1
  │ server                     155L  0C    1m  CC=3      ←0
  │ command                    120L  0C    7m  CC=3      ←0
  │ query                      115L  0C    8m  CC=4      ←1
  │ app                         87L  0C    1m  CC=2      ←3
  │ bus                         86L  0C    4m  CC=10     ←6
  │ cli                         70L  0C    3m  CC=10     ←0
  │ server                      53L  0C    1m  CC=1      ←0
  │ cli                         41L  0C    1m  CC=7      ←0
  │ schema_registry             38L  0C    4m  CC=3      ←3
  │ cli                         35L  0C    1m  CC=3      ←0
  │ cli                         34L  0C    1m  CC=7      ←0
  │ cli                         33L  0C    1m  CC=3      ←0
  │ decode                      31L  0C    1m  CC=7      ←1
  │ cli                         30L  0C    1m  CC=4      ←0
  │ pyproject.toml              28L  0C    0m  CC=0.0    ←0
  │ result                      26L  1C    1m  CC=1      ←0
  │ cli                         23L  0C    2m  CC=2      ←0
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
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  src/                            CC̄=3.1    ←in:0  →out:0
  │ linux_x11_relay            478L  2C   24m  CC=12     ←0
  │ discovery                  329L  0C   13m  CC=9      ←11
  │ linux_xwd                  319L  0C   21m  CC=12     ←7
  │ host                       288L  0C    6m  CC=13     ←3
  │ linux_x11_mirror           259L  1C   17m  CC=10     ←1
  │ agent_dispatch             251L  0C   16m  CC=5      ←1
  │ portal                     221L  1C    7m  CC=11     ←1
  │ query                      209L  0C    6m  CC=9      ←2
  │ api                        193L  3C   32m  CC=6      ←2
  │ session                    190L  0C   10m  CC=2      ←0
  │ filter                     173L  0C   12m  CC=14     ←2
  │ discovery                  170L  0C    6m  CC=10     ←0
  │ capture                    167L  0C    4m  CC=8      ←1
  │ linux_xvfb                 164L  1C   14m  CC=8      ←0
  │ client                     161L  1C   15m  CC=13     ←0
  │ nl                         158L  0C    8m  CC=14     ←3
  │ nlp                        158L  0C   14m  CC=10     ←2
  │ scan                       110L  0C    7m  CC=6      ←2
  │ normalize                  103L  0C    7m  CC=14     ←1
  │ engine                      99L  0C    6m  CC=11     ←4
  │ relay                       97L  0C    3m  CC=5      ←0
  │ drm                         89L  1C    5m  CC=11     ←0
  │ payloads                    86L  0C    5m  CC=1      ←0
  │ fbdev                       77L  1C    5m  CC=7      ←0
  │ virtual                     72L  0C    2m  CC=4      ←0
  │ base                        64L  1C   11m  CC=1      ←0
  │ mss                         60L  1C    5m  CC=8      ←0
  │ mirror                      53L  0C    2m  CC=3      ←0
  │ screenshot                  47L  0C    2m  CC=1      ←0
  │ utils                       46L  0C    3m  CC=2      ←8
  │ all_cmd                     46L  0C    4m  CC=1      ←1
  │ __init__                    46L  0C    0m  CC=0.0    ←0
  │ linux_xdotool               45L  1C    6m  CC=2      ←0
  │ agent                       45L  0C    2m  CC=7      ←0
  │ runtime                     45L  0C    4m  CC=3      ←2
  │ rank                        43L  0C    5m  CC=9      ←1
  │ __init__                    40L  0C    1m  CC=2      ←1
  │ x11                         35L  1C    4m  CC=4      ←0
  │ common                      35L  0C    4m  CC=2      ←6
  │ mirror_stub                 34L  1C    4m  CC=1      ←0
  │ cli_handlers                34L  0C    6m  CC=1      ←12
  │ cli                         32L  0C    2m  CC=2      ←0
  │ windows                     29L  0C    2m  CC=1      ←0
  │ models                      26L  2C    0m  CC=0.0    ←0
  │ info                        24L  0C    1m  CC=2      ←0
  │ nlp                         23L  0C    2m  CC=2      ←0
  │ agent_config                22L  0C    3m  CC=4      ←7
  │ base                        22L  2C    3m  CC=1      ←0
  │ monitors                    19L  0C    2m  CC=1      ←0
  │ constants                   19L  0C    0m  CC=0.0    ←0
  │ diagnose                    18L  0C    2m  CC=1      ←0
  │ info                        16L  0C    2m  CC=1      ←0
  │ __init__                    15L  0C    0m  CC=0.0    ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ exceptions                  10L  3C    0m  CC=0.0    ←0
  │ base                         9L  1C    1m  CC=1      ←0
  │ io                           7L  0C    1m  CC=1      ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ tree.txt                   241L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              99L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                          src.vdisplay      packages.dsl2vdisplay    packages.vdisplay-agent            examples.common     packages.rest2vdisplay        examples.host-relay       examples.host-mirror      packages.mcp2vdisplay          examples.ci-agent  examples.headless-virtual      packages.cli2vdisplay      packages.nlp2vdisplay      packages.uri2vdisplay
               src.vdisplay                         ──                          2                         ←9                                                     1                         ←4                         ←3                         ←1                                                                                                          ←1                             hub
      packages.dsl2vdisplay                          6                         ──                                                                               ←4                                                                               ←2                                                                               ←2                                                    ←1  hub
    packages.vdisplay-agent                          9                                                    ──                                                     1                                                                                                                                                                                                                          !! fan-out
            examples.common                                                                                                          ──                                                    ←2                         ←2                                                    ←2                         ←2                                                                                   hub
     packages.rest2vdisplay                          2                          4                         ←1                                                    ──                                                                                                                                                                                                                        
        examples.host-relay                          4                                                                                2                                                    ──                                                                                                                                                                                             
       examples.host-mirror                          3                                                                                2                                                                               ──                                                                                                                                                                  
      packages.mcp2vdisplay                          1                          2                                                                                                                                                                ──                                                                                                           1                           
          examples.ci-agent                                                                                                           2                                                                                                                                     ──                                                                                                            
  examples.headless-virtual                                                                                                           2                                                                                                                                                                ──                                                                                 
      packages.cli2vdisplay                                                     2                                                                                                                                                                                                                                                 ──                                                      
      packages.nlp2vdisplay                          1                                                                                                                                                                                           ←1                                                                                                          ──                           
      packages.uri2vdisplay                                                     1                                                                                                                                                                                                                                                                                                       ──
  CYCLES: none
  HUB: packages.dsl2vdisplay/ (fan-in=11)
  HUB: src.vdisplay/ (fan-in=26)
  HUB: examples.common/ (fan-in=8)
  SMELL: packages.vdisplay-agent/ fan-out=10 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 7 groups | 90f 7678L | 2026-06-09

SUMMARY:
  files_scanned: 90
  total_lines:   7678
  dup_groups:    7
  dup_fragments: 18
  saved_lines:   104
  scan_ms:       2319

HOTSPOTS[7] (files with most duplication):
  src/vdisplay/payloads.py  dup=46L  groups=1  frags=2  (0.6%)
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py  dup=34L  groups=1  frags=2  (0.4%)
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py  dup=20L  groups=1  frags=2  (0.3%)
  src/vdisplay/api.py  dup=12L  groups=1  frags=3  (0.2%)
  examples/ci-agent/agent.py  dup=11L  groups=1  frags=1  (0.1%)
  examples/headless-virtual/run_virtual.py  dup=11L  groups=1  frags=1  (0.1%)
  examples/host-mirror/mirror_demo.py  dup=11L  groups=1  frags=1  (0.1%)

DUPLICATES[7] (ranked by impact):
  [443c93126a62d7a9] ! EXAC  _load_common  L=11 N=4 saved=33 sim=1.00
      examples/ci-agent/agent.py:15-25  (_load_common)
      examples/headless-virtual/run_virtual.py:13-23  (_load_common)
      examples/host-mirror/mirror_demo.py:16-26  (_load_common)
      examples/host-relay/relay_demo.py:18-28  (_load_common)
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
  [f5bfacfda8981cef]   STRU  looks_like_internal_class  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/windows/filter.py:8-10  (looks_like_internal_class)
      src/vdisplay/windows/filter.py:13-15  (looks_like_internal_name)

REFACTOR[7] (ranked by priority):
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
  [7] ○ extract_function   → src/vdisplay/windows/utils/looks_like_internal_class.py
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

EFFORT_ESTIMATE (total ≈ 3.5h):
  medium _load_common                        saved=33L  ~66min
  medium local_windows_payload               saved=23L  ~46min
  medium handle_windows                      saved=17L  ~34min
  easy   _parse_mirror                       saved=10L  ~20min
  easy   register                            saved=10L  ~20min
  easy   _default_virtual_backend            saved=8L  ~16min
  easy   looks_like_internal_class           saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  7 → 0
  saved_lines: 104 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 414 func | 70f | 2026-06-09
# generated in 0.00s

NEXT[2] (ranked by impact):
  [1] !! SPLIT           planfile.yaml
      WHY: 1319L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [2] !! SPLIT           goal.yaml
      WHY: 512L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[2]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting goal.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          3.1 → ≤2.2
  max-CC:      14 → ≤7
  god-modules: 2 → 0
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
  prev CC̄=3.4 → now CC̄=3.1
```

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

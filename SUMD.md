# vdisplay

Cross-platform virtual display orchestration with virtual and mirror sessions

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `vdisplay`
- **version**: `0.1.3`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(1), app.doql.less, goal.yaml, .env.example, project/(3 analysis files)

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

## Interfaces

### CLI Entry Points

- `vdisplay`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m vdisplay
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m vdisplay --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m vdisplay --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m vdisplay --help" 10000
ASSERT_EXIT_CODE 0
```

## Configuration

```yaml
project:
  name: vdisplay
  version: 0.1.3
  env: local
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

## Deployment

```bash markpact:run
pip install vdisplay

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | OpenRouter API Key (required for real cost calculation) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Default AI model for cost analysis |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`vdisplay`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `venv/lib/python3.13/site-packages/cryptography/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# vdisplay | 118f 9169L | python:111,shell:6,less:1 | 2026-06-09
# stats: 377 func | 29 cls | 118 mod | CC̄=3.5 | critical:23 | cycles:0
# alerts[5]: CC describe_screenshot_nl=14; CC describe_window_nl=14; CC filter_windows=14; CC derive_app_label=14; CC capture_host_png=13
# hotspots[5]: create_app fan=29; create_app fan=22; _portal_impl fan=22; main fan=19; main fan=19
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[118]:
  app.doql.less,47
  examples/ci-agent/agent.py,74
  examples/common/screenshot_meta.py,163
  examples/common/validate_artifacts.py,85
  examples/headless-virtual/run_virtual.py,64
  examples/host-mirror/mirror_demo.py,89
  examples/host-mirror/run.sh,54
  examples/host-relay/relay_demo.py,139
  examples/host-relay/run-host.sh,25
  examples/host-relay/run.sh,48
  examples/run_all_examples.sh,63
  packages/cli2vdisplay/src/cli2vdisplay/cli.py,35
  packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py,5
  packages/dsl2vdisplay/src/dsl2vdisplay/bus.py,87
  packages/dsl2vdisplay/src/dsl2vdisplay/cli.py,71
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py,161
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py,2
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py,121
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py,116
  packages/dsl2vdisplay/src/dsl2vdisplay/result.py,27
  packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py,39
  packages/dsl2vdisplay/tests/test_parity.py,15
  packages/mcp2vdisplay/src/mcp2vdisplay/cli.py,24
  packages/mcp2vdisplay/src/mcp2vdisplay/server.py,54
  packages/nlp2vdisplay/src/nlp2vdisplay/cli.py,42
  packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py,14
  packages/rest2vdisplay/src/rest2vdisplay/app.py,88
  packages/rest2vdisplay/src/rest2vdisplay/cli.py,36
  packages/uri2vdisplay/src/uri2vdisplay/cli.py,31
  packages/uri2vdisplay/src/uri2vdisplay/decode.py,32
  packages/vdisplay-agent/src/vdisplay_agent/__init__.py,6
  packages/vdisplay-agent/src/vdisplay_agent/cli.py,34
  packages/vdisplay-agent/src/vdisplay_agent/runtime.py,254
  packages/vdisplay-agent/src/vdisplay_agent/server.py,156
  project.sh,59
  src/vdisplay/__init__.py,13
  src/vdisplay/agent_config.py,23
  src/vdisplay/agent_dispatch.py,252
  src/vdisplay/api.py,194
  src/vdisplay/application/__init__.py,6
  src/vdisplay/application/runtime.py,46
  src/vdisplay/application/services/__init__.py,4
  src/vdisplay/application/services/capture.py,168
  src/vdisplay/application/services/discovery.py,171
  src/vdisplay/application/services/info.py,25
  src/vdisplay/application/services/session.py,191
  src/vdisplay/backends/__init__.py,2
  src/vdisplay/backends/base.py,65
  src/vdisplay/backends/linux_x11_mirror.py,260
  src/vdisplay/backends/linux_x11_relay.py,479
  src/vdisplay/backends/linux_xvfb.py,165
  src/vdisplay/backends/mirror_stub.py,35
  src/vdisplay/capture/__init__.py,16
  src/vdisplay/capture/base.py,10
  src/vdisplay/capture/host.py,289
  src/vdisplay/capture/linux_xwd.py,320
  src/vdisplay/capture/portal.py,222
  src/vdisplay/capture/providers/__init__.py,4
  src/vdisplay/capture/providers/base.py,23
  src/vdisplay/capture/providers/drm.py,90
  src/vdisplay/capture/providers/engine.py,100
  src/vdisplay/capture/providers/fbdev.py,78
  src/vdisplay/capture/providers/mss.py,61
  src/vdisplay/capture/providers/x11.py,36
  src/vdisplay/cli.py,33
  src/vdisplay/cli_handlers.py,35
  src/vdisplay/client.py,162
  src/vdisplay/commands/__init__.py,41
  src/vdisplay/commands/agent.py,46
  src/vdisplay/commands/all_cmd.py,47
  src/vdisplay/commands/common.py,36
  src/vdisplay/commands/diagnose.py,19
  src/vdisplay/commands/info.py,17
  src/vdisplay/commands/io.py,8
  src/vdisplay/commands/mirror.py,54
  src/vdisplay/commands/monitors.py,20
  src/vdisplay/commands/nlp.py,24
  src/vdisplay/commands/relay.py,98
  src/vdisplay/commands/screenshot.py,48
  src/vdisplay/commands/virtual.py,73
  src/vdisplay/commands/windows.py,30
  src/vdisplay/discovery.py,330
  src/vdisplay/exceptions.py,11
  src/vdisplay/input/__init__.py,4
  src/vdisplay/input/linux_xdotool.py,46
  src/vdisplay/models.py,27
  src/vdisplay/nl.py,159
  src/vdisplay/nlp.py,159
  src/vdisplay/payloads.py,87
  src/vdisplay/utils.py,47
  src/vdisplay/windows/__init__.py,47
  src/vdisplay/windows/constants.py,20
  src/vdisplay/windows/filter.py,174
  src/vdisplay/windows/normalize.py,104
  src/vdisplay/windows/query.py,210
  src/vdisplay/windows/rank.py,44
  src/vdisplay/windows/scan.py,111
  tests/conftest.py,15
  tests/test_agent.py,57
  tests/test_agent_client.py,24
  tests/test_agent_dispatch.py,43
  tests/test_agent_integration.py,113
  tests/test_capture_crop.py,50
  tests/test_capture_providers.py,67
  tests/test_capture_xwd.py,53
  tests/test_cli_commands.py,106
  tests/test_host_capture.py,38
  tests/test_import.py,23
  tests/test_linux_xvfb_integration.py,22
  tests/test_mirror_primary.py,43
  tests/test_nl.py,145
  tests/test_nlp_pipeline.py,60
  tests/test_outputs_rotation.py,35
  tests/test_relay_release.py,66
  tests/test_screenshot_meta.py,54
  tests/test_windows.py,48
  tests/test_windows_dedupe.py,26
  tree.sh,2
D:
  examples/ci-agent/agent.py:
    e: _load_common,main
    _load_common()
    main()
  examples/common/screenshot_meta.py:
    e: examples_common_dir,ensure_common_on_path,meta_path_for,png_dimensions,describe_screenshot_nl,build_screenshot_meta,write_screenshot_meta,save_png_with_meta,print_artifact
    examples_common_dir()
    ensure_common_on_path()
    meta_path_for(image_path)
    png_dimensions(path)
    describe_screenshot_nl()
    build_screenshot_meta(image_path)
    write_screenshot_meta(image_path)
    save_png_with_meta(image_path;png_bytes)
    print_artifact(meta)
  examples/common/validate_artifacts.py:
    e: validate_image_and_meta,validate_directory,main
    validate_image_and_meta(image_path)
    validate_directory(root)
    main(argv)
  examples/headless-virtual/run_virtual.py:
    e: _load_common,main
    _load_common()
    main()
  examples/host-mirror/mirror_demo.py:
    e: _load_common,main
    _load_common()
    main()
  examples/host-relay/relay_demo.py:
    e: _load_common,_capture_phase,main
    _load_common()
    _capture_phase(output_dir)
    main()
  packages/cli2vdisplay/src/cli2vdisplay/cli.py:
    e: main
    main(argv)
  packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py:
  packages/dsl2vdisplay/src/dsl2vdisplay/bus.py:
    e: _dispatch_query,_dispatch_cmd,dispatch,execute_dsl_line
    _dispatch_query(cmd)
    _dispatch_cmd(cmd)
    dispatch(envelope)
    execute_dsl_line(line)
  packages/dsl2vdisplay/src/dsl2vdisplay/cli.py:
    e: main,_main_legacy,_main_subcommand
    main(argv)
    _main_legacy(argv)
    _main_subcommand(argv)
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:
    e: split_command,pick_flag,_with_display,_parse_windows,_parse_screenshot,_parse_virtual_start,_parse_launch,_parse_mirror,_parse_adopt,_parse_release,parse_line,to_text
    split_command(line)
    pick_flag(tokens;flag)
    _with_display(rest;cmd)
    _parse_windows(rest;cmd)
    _parse_screenshot(rest;cmd)
    _parse_virtual_start(rest;cmd)
    _parse_launch(rest;cmd)
    _parse_mirror(rest;cmd)
    _parse_adopt(rest;cmd)
    _parse_release(rest;cmd)
    parse_line(line)
    to_text(cmd)
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py:
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py:
    e: _ok,_err,handle_screenshot,handle_virtual_start,handle_mirror,handle_adopt,handle_release
    _ok(line;action;data)
    _err(line;action;error;data)
    handle_screenshot(cmd)
    handle_virtual_start(cmd)
    handle_mirror(cmd)
    handle_adopt(cmd)
    handle_release(cmd)
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py:
    e: handle_health,handle_info,handle_monitors,handle_outputs,handle_windows,handle_all,handle_capabilities,handle_validate
    handle_health(cmd)
    handle_info(cmd)
    handle_monitors(cmd)
    handle_outputs(cmd)
    handle_windows(cmd)
    handle_all(cmd)
    handle_capabilities(cmd)
    handle_validate(cmd)
  packages/dsl2vdisplay/src/dsl2vdisplay/result.py:
    e: DslResult
    DslResult: to_dict(0)
  packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py:
    e: _load_schema,all_schemas,schema_for_verb,validate_command_dict
    _load_schema(name)
    all_schemas()
    schema_for_verb(verb)
    validate_command_dict(cmd)
  packages/dsl2vdisplay/tests/test_parity.py:
    e: test_parity_info_text_vs_dict,test_health
    test_parity_info_text_vs_dict()
    test_health()
  packages/mcp2vdisplay/src/mcp2vdisplay/cli.py:
    e: main,create_server
    main()
    create_server()
  packages/mcp2vdisplay/src/mcp2vdisplay/server.py:
    e: create_server
    create_server()
  packages/nlp2vdisplay/src/nlp2vdisplay/cli.py:
    e: main
    main(argv)
  packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py:
    e: parse_display,nl_to_dsl
    parse_display(text)
    nl_to_dsl(prompt)
  packages/rest2vdisplay/src/rest2vdisplay/app.py:
    e: create_app
    create_app()
  packages/rest2vdisplay/src/rest2vdisplay/cli.py:
    e: main
    main()
  packages/uri2vdisplay/src/uri2vdisplay/cli.py:
    e: main
    main(argv)
  packages/uri2vdisplay/src/uri2vdisplay/decode.py:
    e: uri_to_dsl
    uri_to_dsl(uri)
  packages/vdisplay-agent/src/vdisplay_agent/__init__.py:
  packages/vdisplay-agent/src/vdisplay_agent/cli.py:
    e: main
    main(argv)
  packages/vdisplay-agent/src/vdisplay_agent/runtime.py:
    e: SessionRecord,AgentRuntime
    SessionRecord:
    AgentRuntime: platform_capabilities(0),diagnostics(0),outputs(0),list_windows(0),start_virtual(0),start_mirror(0),start_relay(0),stop_session(1),capture_frame(1),adopt_window(1),release_window(1),_relay_session(1),shutdown(0)  # Privileged runtime: owns sessions and native capture provide
  packages/vdisplay-agent/src/vdisplay_agent/server.py:
    e: create_app
    create_app(runtime)
  src/vdisplay/__init__.py:
  src/vdisplay/agent_config.py:
    e: resolve_agent_url,resolve_agent_token,use_agent
    resolve_agent_url(explicit)
    resolve_agent_token()
    use_agent(explicit)
  src/vdisplay/agent_dispatch.py:
    e: agent_client,_ok_result,_err_result,_dispatch_health,_dispatch_info,_dispatch_monitors,_dispatch_windows,_dispatch_all,_dispatch_capabilities,_dispatch_validate,_dispatch_screenshot,_dispatch_virtual_start,_dispatch_mirror,_dispatch_adopt,_dispatch_release,dispatch_via_agent
    agent_client(url)
    _ok_result()
    _err_result()
    _dispatch_health(client;cmd)
    _dispatch_info(client;cmd)
    _dispatch_monitors(client;cmd)
    _dispatch_windows(client;cmd)
    _dispatch_all(client;cmd)
    _dispatch_capabilities(client;cmd)
    _dispatch_validate(client;cmd)
    _dispatch_screenshot(client;cmd)
    _dispatch_virtual_start(client;cmd)
    _dispatch_mirror(client;cmd)
    _dispatch_adopt(client;cmd)
    _dispatch_release(client;cmd)
    dispatch_via_agent(cmd)
  src/vdisplay/api.py:
    e: _default_virtual_backend,_default_mirror_backend,_default_relay_backend,platform_summary,VirtualDisplaySession,MirrorSession,WindowRelaySession
    VirtualDisplaySession: __init__(1),create(5),start(0),stop(0),launch(1),screenshot_bytes(0),save_screenshot(1),adopt_window(0),release_window(0),info(0),capabilities(0)
    MirrorSession: __init__(1),create(5),start(0),stop(0),screenshot_bytes(0),save_screenshot(1),info(0),capabilities(0)
    WindowRelaySession: __init__(1),create(3),start(0),stop(0),adopt_window(0),release_window(0),list_adopted(0),info(0),capabilities(0)
    _default_virtual_backend()
    _default_mirror_backend()
    _default_relay_backend()
    platform_summary()
  src/vdisplay/application/__init__.py:
  src/vdisplay/application/runtime.py:
    e: agent_client_optional,agent_client_required,prefer_agent,resolve_apps_only
    agent_client_optional()
    agent_client_required()
    prefer_agent()
    resolve_apps_only()
  src/vdisplay/application/services/__init__.py:
  src/vdisplay/application/services/capture.py:
    e: capture_screenshot,_capture_via_agent,_capture_local,capture_screenshot_via_client
    capture_screenshot()
    _capture_via_agent(client)
    _capture_local()
    capture_screenshot_via_client(client)
  src/vdisplay/application/services/discovery.py:
    e: list_monitors,list_windows_payload,list_windows_local,list_adopted,list_all,diagnose
    list_monitors(display)
    list_windows_payload(display)
    list_windows_local(display)
    list_adopted(display)
    list_all(display)
    diagnose(display)
  src/vdisplay/application/services/info.py:
    e: platform_info
    platform_info()
  src/vdisplay/application/services/session.py:
    e: virtual_start,virtual_launch,virtual_screenshot,mirror_start,mirror_screenshot,relay_adopt,relay_release,relay_list_adopted,relay_screenshot,unsupported_session_action
    virtual_start()
    virtual_launch(command)
    virtual_screenshot(output)
    mirror_start()
    mirror_screenshot(output)
    relay_adopt()
    relay_release()
    relay_list_adopted(display)
    relay_screenshot(output)
    unsupported_session_action(kind;action)
  src/vdisplay/backends/__init__.py:
  src/vdisplay/backends/base.py:
    e: BaseBackend
    BaseBackend: __init__(0),capabilities(0),info(0),start(0),stop(0),launch(1),screenshot_bytes(0),save_screenshot(1),adopt_window(0),release_window(0),as_dict(0)
  src/vdisplay/backends/linux_x11_mirror.py:
    e: _require_xrandr,_resolve_mirror_targets,_try_mirror,_mirror_exhausted_error,_list_connected_outputs,_resolve_output,_primary_output_from_xrandr,_output_capture_region,_mirror_target_candidates,_output_mode,LinuxX11MirrorBackend
    LinuxX11MirrorBackend: __init__(3),capabilities(0),info(0),start(0),_activate_mirror(2),stop(0),screenshot_bytes(0)
    _require_xrandr()
    _resolve_mirror_targets(target;source;outputs;display)
    _try_mirror(display;source;target)
    _mirror_exhausted_error(source;targets;outputs;failures)
    _list_connected_outputs(display)
    _resolve_output(name;outputs;display)
    _primary_output_from_xrandr(display)
    _output_capture_region(display;output_name)
    _mirror_target_candidates(display;source;outputs)
    _output_mode(display;output)
  src/vdisplay/backends/linux_x11_relay.py:
    e: _stash_path,_load_stash,_save_stash,_state_as_match_info,_state_matches,_select_adopted_for_release,_related_adopted_ids,_pick_primary_release_id,_restore_window,_find_window_id,_move_window,_window_metadata,_window_geometry,_window_title,_offscreen_coordinates,_screen_geometry,_output_origin,WindowState,LinuxX11RelayBackend
    WindowState:
    LinuxX11RelayBackend: __init__(2),capabilities(0),info(0),start(0),adopt_window(0),release_window(0),list_adopted(0)  # Move windows between monitors/outputs within the same X11 se
    _stash_path(display;stash_prefix)
    _load_stash(display;stash_prefix)
    _save_stash(display;stash_prefix;adopted)
    _state_as_match_info(state)
    _state_matches(state)
    _select_adopted_for_release(adopted)
    _related_adopted_ids(adopted;seed_id)
    _pick_primary_release_id(adopted;window_ids)
    _restore_window(display;state)
    _find_window_id(display)
    _move_window(display;window_id;x;y)
    _window_metadata(display;window_id)
    _window_geometry(display;window_id)
    _window_title(display;window_id)
    _offscreen_coordinates(display)
    _screen_geometry(display)
    _output_origin(display;target)
  src/vdisplay/backends/linux_xvfb.py:
    e: _display_candidates,_display_socket_exists,_probe_display,_wait_for_display,LinuxXvfbBackend
    LinuxXvfbBackend: __init__(3),capabilities(0),info(0),start(0),stop(0),launch(1),screenshot_bytes(0),adopt_window(0),release_window(0),_acquire_display(1)
    _display_candidates(preferred)
    _display_socket_exists(display)
    _probe_display(display)
    _wait_for_display(display)
  src/vdisplay/backends/mirror_stub.py:
    e: MirrorStubBackend
    MirrorStubBackend: __init__(2),capabilities(0),info(0),screenshot_bytes(0)
  src/vdisplay/capture/__init__.py:
  src/vdisplay/capture/base.py:
    e: CaptureBackend
    CaptureBackend: screenshot_png(0)
  src/vdisplay/capture/host.py:
    e: _monitor_source_name,_monitor_capture_region,_capture_all_from_driver_full,capture_host_png,capture_host_to_file,capture_all_monitors
    _monitor_source_name(display;monitor;source)
    _monitor_capture_region(display;output_name)
    _capture_all_from_driver_full(display;monitors;output_dir)
    capture_host_png()
    capture_host_to_file(path)
    capture_all_monitors()
  src/vdisplay/capture/linux_xwd.py:
    e: _is_valid_png,is_blank_png,_is_wayland_session,_capture_hint,_crop_png,_capture_full_display_png,capture_display_png,_capture_xwd_png,_capture_scrot_png,_capture_gnome_screenshot_png,_capture_portal_png,_capture_grim_png,xwd_bytes_to_png,_xwd_dimensions,_xwd_to_rgb_bytes,_parse_xwd_header,_read_xwd_header,_header_fields,_decode_pixels,_rgb_to_png,_rgb_to_png_minimal
    _is_valid_png(data)
    is_blank_png(data)
    _is_wayland_session()
    _capture_hint(display)
    _crop_png(full_png;region)
    _capture_full_display_png(display)
    capture_display_png(display)
    _capture_xwd_png(display)
    _capture_scrot_png(display;region)
    _capture_gnome_screenshot_png()
    _capture_portal_png()
    _capture_grim_png()
    xwd_bytes_to_png(data)
    _xwd_dimensions(data)
    _xwd_to_rgb_bytes(data)
    _parse_xwd_header(data)
    _read_xwd_header(stream)
    _header_fields(fields)
    _decode_pixels(header;pixels)
    _rgb_to_png(rgb;width;height)
    _rgb_to_png_minimal(rgb;width;height)
  src/vdisplay/capture/portal.py:
    e: _portal_impl,_system_python,capture_portal_png,_capture_portal_to_file,PortalProvider
    PortalProvider: available(0),capture_full(0),capture_region(1)  # Opt-in portal capture (VDISPLAY_CAPTURE_ALLOW_PORTAL=1). Not
    _portal_impl(out)
    _system_python()
    capture_portal_png()
    _capture_portal_to_file(out)
  src/vdisplay/capture/providers/__init__.py:
  src/vdisplay/capture/providers/base.py:
    e: ProviderResult,CaptureProvider
    ProviderResult:
    CaptureProvider: available(0),capture_full(0),capture_region(1)
  src/vdisplay/capture/providers/drm.py:
    e: _drm_devices,DrmProvider
    DrmProvider: available(0),capture_full(0),capture_region(1),_capture(1)
    _drm_devices()
  src/vdisplay/capture/providers/engine.py:
    e: _allow_portal,_providers,capture_full_png,capture_region_png,list_capture_providers,_try_providers
    _allow_portal()
    _providers(display)
    capture_full_png(display)
    capture_region_png(display;region)
    list_capture_providers(display)
    _try_providers(providers)
  src/vdisplay/capture/providers/fbdev.py:
    e: _fb_info,FbdevProvider
    FbdevProvider: available(0),capture_full(0),capture_region(1),_capture(1)
    _fb_info()
  src/vdisplay/capture/providers/mss.py:
    e: MssProvider
    MssProvider: __init__(1),available(0),capture_full(0),capture_region(1),_grab(1)
  src/vdisplay/capture/providers/x11.py:
    e: X11Provider
    X11Provider: __init__(1),available(0),capture_full(0),capture_region(1)
  src/vdisplay/cli.py:
    e: build_parser,main
    build_parser()
    main(argv)
  src/vdisplay/cli_handlers.py:
    e: print_json,monitors_payload,windows_payload,all_payload,screenshot_payload,dispatch_cli
    print_json(payload)
    monitors_payload()
    windows_payload()
    all_payload()
    screenshot_payload()
    dispatch_cli(args)
  src/vdisplay/client.py:
    e: AgentClient
    AgentClient: __init__(1),_request(2),health(0),capabilities(0),diagnostics(0),outputs(0),windows(0),start_virtual(0),start_mirror(0),start_relay(0),stop_session(1),capture_frame(0),capture_png_bytes(0),adopt_window(0),release_window(0)  # HTTP client for the local vdisplay-agent broker.
  src/vdisplay/commands/__init__.py:
    e: register_all
    register_all(sub)
  src/vdisplay/commands/agent.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/all_cmd.py:
    e: register,handle,register_outputs,handle_outputs
    register(sub)
    handle(args)
    register_outputs(sub)
    handle_outputs(args)
  src/vdisplay/commands/common.py:
    e: add_display_arg,add_all_arg,add_window_filter_args,include_all_from_args
    add_display_arg(parser)
    add_all_arg(parser)
    add_window_filter_args(parser)
    include_all_from_args(args)
  src/vdisplay/commands/diagnose.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/info.py:
    e: register,handle
    register(sub)
    handle(_args)
  src/vdisplay/commands/io.py:
    e: print_json
    print_json(payload)
  src/vdisplay/commands/mirror.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/monitors.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/nlp.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/relay.py:
    e: register,handle_list_windows,handle
    register(sub)
    handle_list_windows(args)
    handle(args)
  src/vdisplay/commands/screenshot.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/virtual.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/windows.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/discovery.py:
    e: resolve_host_display,_looks_like_xvfb_only,list_outputs,_attach_output_nl,_list_monitors,_parse_xrandr_query,_merge_output_metadata,list_windows,find_window_suggestions,diagnose_display,_display_hint,list_monitors,window_discovery_meta
    resolve_host_display(preferred)
    _looks_like_xvfb_only(display)
    list_outputs(display)
    _attach_output_nl(display;outputs)
    _list_monitors(display)
    _parse_xrandr_query(display)
    _merge_output_metadata(monitors;query_meta)
    list_windows(display)
    find_window_suggestions(display;match_title;limit)
    diagnose_display(display)
    _display_hint(display;resolved;outputs)
    list_monitors(display)
    window_discovery_meta(display)
  src/vdisplay/exceptions.py:
    e: VDisplayError,BackendNotAvailableError,CapabilityError
    VDisplayError:
    BackendNotAvailableError:
    CapabilityError:
  src/vdisplay/input/__init__.py:
  src/vdisplay/input/linux_xdotool.py:
    e: LinuxXdotoolInput
    LinuxXdotoolInput: __init__(1),_env(0),move(2),click(1),type_text(1),hotkey(0)
  src/vdisplay/models.py:
    e: Capabilities,SessionInfo
    Capabilities:
    SessionInfo:
  src/vdisplay/nl.py:
    e: describe_window_nl,_user_visible_app_labels,describe_output_nl,window_center_on_output,ensure_monitor_ids,find_monitor_for_window,assign_windows_to_monitors,enrich_outputs_nl
    describe_window_nl(info)
    _user_visible_app_labels(windows)
    describe_output_nl(output;windows)
    window_center_on_output(window;output)
    ensure_monitor_ids(monitors)
    find_monitor_for_window(window;monitors)
    assign_windows_to_monitors(windows;monitors)
    enrich_outputs_nl(outputs;windows)
  src/vdisplay/nlp.py:
    e: parse_display,_display_suffix,_default_display_suffix,_default_all,_default_monitors,_default_windows,_screenshot_dsl,_mirror_dsl,_release_dsl,_adopt_dsl,_validate_dsl,nl_to_dsl,run_nl_prompt,_run_local_dsl
    parse_display(text)
    _display_suffix(display)
    _default_display_suffix(display)
    _default_all(_text;display)
    _default_monitors(_text;display)
    _default_windows(_text;display)
    _screenshot_dsl(prompt;_display)
    _mirror_dsl(_prompt;_display)
    _release_dsl(text;_display)
    _adopt_dsl(text;_display)
    _validate_dsl(_text;display)
    nl_to_dsl(prompt)
    run_nl_prompt(prompt)
    _run_local_dsl(line)
  src/vdisplay/payloads.py:
    e: monitors_payload,local_windows_payload,windows_payload,adopted_payload,all_payload
    monitors_payload(display)
    local_windows_payload(display)
    windows_payload(display)
    adopted_payload(display)
    all_payload(display)
  src/vdisplay/utils.py:
    e: require_command,run_command,run_command_bytes
    require_command(name)
    run_command(args)
    run_command_bytes(args)
  src/vdisplay/windows/__init__.py:
  src/vdisplay/windows/constants.py:
  src/vdisplay/windows/filter.py:
    e: looks_like_internal_class,looks_like_internal_name,is_trivial_internal,is_junk_title,is_visible_app,is_internal_window,matches_title,matches_class,matches_app,window_passes_filters,filter_windows,is_companion_frame
    looks_like_internal_class(value)
    looks_like_internal_name(value)
    is_trivial_internal()
    is_junk_title(title;net_wm_name)
    is_visible_app(role;title;net_wm_name;width;height)
    is_internal_window()
    matches_title(info;needle)
    matches_class(info;needle)
    matches_app(info;needle)
    window_passes_filters(info)
    filter_windows(windows)
    is_companion_frame(candidate;window)
  src/vdisplay/windows/normalize.py:
    e: parse_wm_class,normalize_atom_list,resolve_window_pid,process_info,usable_title,derive_app_label,derive_role
    parse_wm_class(raw)
    normalize_atom_list(raw)
    resolve_window_pid(display;window_id;props)
    process_info(pid)
    usable_title(candidate)
    derive_app_label()
    derive_role()
  src/vdisplay/windows/query.py:
    e: list_windows_enriched,scan_windows,inspect_window,find_windows,pick_best_window,find_companion_frames
    list_windows_enriched(display)
    scan_windows(display)
    inspect_window(display;window_id)
    find_windows(display)
    pick_best_window(matches)
    find_companion_frames(display;window)
  src/vdisplay/windows/rank.py:
    e: window_area,pick_largest,pick_best_from_group,dedupe_app_windows,window_sort_key
    window_area(window)
    pick_largest(windows)
    pick_best_from_group(group)
    dedupe_app_windows(windows)
    window_sort_key(info)
  src/vdisplay/windows/scan.py:
    e: root_window_id,xdotool,format_window_id,xprop,decode_xprop_value,window_geometry,search_window_ids
    root_window_id(display)
    xdotool(display)
    format_window_id(window_id)
    xprop(display;window_id)
    decode_xprop_value(raw)
    window_geometry(display;window_id)
    search_window_ids(display)
  tests/conftest.py:
    e: _isolate_agent_env
    _isolate_agent_env(monkeypatch)
  tests/test_agent.py:
    e: agent_client,test_agent_health,test_agent_capabilities,test_agent_virtual_session_capture
    agent_client()
    test_agent_health(agent_client)
    test_agent_capabilities(agent_client)
    test_agent_virtual_session_capture(agent_client;tmp_path)
  tests/test_agent_client.py:
    e: test_use_agent_false_by_default,test_client_unreachable_raises
    test_use_agent_false_by_default(monkeypatch)
    test_client_unreachable_raises(monkeypatch)
  tests/test_agent_dispatch.py:
    e: test_dispatch_monitors_via_agent,test_dsl_bus_uses_agent_when_configured
    test_dispatch_monitors_via_agent(monkeypatch)
    test_dsl_bus_uses_agent_when_configured(monkeypatch)
  tests/test_agent_integration.py:
    e: _wait_for_url,live_agent_url,test_agent_client_round_trip_monitors,test_dsl_dispatch_round_trip,test_rest2vdisplay_round_trip,test_virtual_screenshot_round_trip
    _wait_for_url(url)
    live_agent_url()
    test_agent_client_round_trip_monitors(live_agent_url;monkeypatch)
    test_dsl_dispatch_round_trip(live_agent_url;monkeypatch)
    test_rest2vdisplay_round_trip(live_agent_url;monkeypatch)
    test_virtual_screenshot_round_trip(live_agent_url;monkeypatch;tmp_path)
  tests/test_capture_crop.py:
    e: _make_png,test_crop_png_extracts_region,test_capture_display_png_region_uses_provider_engine,test_is_blank_png_detects_black
    _make_png(width;height;color)
    test_crop_png_extracts_region()
    test_capture_display_png_region_uses_provider_engine(monkeypatch)
    test_is_blank_png_detects_black()
  tests/test_capture_providers.py:
    e: _make_png,test_try_providers_prefers_first_non_blank,test_list_capture_providers_includes_drm,test_x11_provider_region_falls_back_to_crop,_StubProvider
    _StubProvider: __init__(1),available(0),capture_full(0),capture_region(1)
    _make_png(width;height;color)
    test_try_providers_prefers_first_non_blank()
    test_list_capture_providers_includes_drm()
    test_x11_provider_region_falls_back_to_crop(monkeypatch)
  tests/test_capture_xwd.py:
    e: _make_xwd,test_xwd_to_png_red_pixel,test_xwd_to_png_2x1,test_is_blank_png_detects_black_frame
    _make_xwd(width;height;pixels)
    test_xwd_to_png_red_pixel()
    test_xwd_to_png_2x1()
    test_is_blank_png_detects_black_frame()
  tests/test_cli_commands.py:
    e: test_parser_has_discovery_commands,test_monitors_command_registered,test_windows_defaults_to_include_all,test_windows_apps_only_flag,test_payload_defaults_include_all,test_all_command_structure
    test_parser_has_discovery_commands()
    test_monitors_command_registered()
    test_windows_defaults_to_include_all(monkeypatch)
    test_windows_apps_only_flag(monkeypatch)
    test_payload_defaults_include_all()
    test_all_command_structure(monkeypatch)
  tests/test_host_capture.py:
    e: test_capture_host_png_prefers_mirror
    test_capture_host_png_prefers_mirror(monkeypatch)
  tests/test_import.py:
    e: test_imports,test_platform_summary,test_capabilities
    test_imports()
    test_platform_summary()
    test_capabilities()
  tests/test_linux_xvfb_integration.py:
    e: test_virtual_display_screenshot
    test_virtual_display_screenshot(tmp_path)
  tests/test_mirror_primary.py:
    e: test_primary_output_from_xrandr,test_mirror_target_candidates_prefers_non_primary,_FakeResult
    _FakeResult: __init__(2)
    test_primary_output_from_xrandr(monkeypatch)
    test_mirror_target_candidates_prefers_non_primary(monkeypatch)
  tests/test_nl.py:
    e: test_describe_window_nl_application,test_describe_output_nl_with_apps,test_describe_output_nl_skips_internal_helpers,test_describe_output_nl_empty_monitor,test_window_center_on_output,test_assign_windows_to_monitors,test_ensure_monitor_ids,test_enrich_outputs_nl_adds_field
    test_describe_window_nl_application()
    test_describe_output_nl_with_apps()
    test_describe_output_nl_skips_internal_helpers()
    test_describe_output_nl_empty_monitor()
    test_window_center_on_output()
    test_assign_windows_to_monitors()
    test_ensure_monitor_ids()
    test_enrich_outputs_nl_adds_field()
  tests/test_nlp_pipeline.py:
    e: test_nl_to_dsl_monitors_on_display_zero,test_nl_to_dsl_windows,test_run_nl_prompt_dsl_only,test_run_nl_prompt_full_pipeline,test_dsl2vdisplay_monitors_matches_payload
    test_nl_to_dsl_monitors_on_display_zero()
    test_nl_to_dsl_windows()
    test_run_nl_prompt_dsl_only()
    test_run_nl_prompt_full_pipeline(monkeypatch)
    test_dsl2vdisplay_monitors_matches_payload(monkeypatch)
  tests/test_outputs_rotation.py:
    e: test_rotation_degrees_mapping,test_parse_xrandr_query_rotation_from_sample
    test_rotation_degrees_mapping()
    test_parse_xrandr_query_rotation_from_sample()
  tests/test_relay_release.py:
    e: _toolbox_states,test_state_matches_app_jetbrains,test_select_adopted_for_release_by_app_includes_frame,test_stash_roundtrip
    _toolbox_states()
    test_state_matches_app_jetbrains()
    test_select_adopted_for_release_by_app_includes_frame()
    test_stash_roundtrip(tmp_path;monkeypatch)
  tests/test_screenshot_meta.py:
    e: test_describe_screenshot_nl,test_build_and_meta_path
    test_describe_screenshot_nl()
    test_build_and_meta_path(tmp_path)
  tests/test_windows.py:
    e: test_parse_wm_class,test_derive_app_label_prefers_title,test_internal_helper_window,test_matches_title_on_app_label
    test_parse_wm_class()
    test_derive_app_label_prefers_title()
    test_internal_helper_window()
    test_matches_title_on_app_label()
  tests/test_windows_dedupe.py:
    e: test_dedupe_prefers_application_over_mutter_frame
    test_dedupe_prefers_application_over_mutter_frame()
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('vdisplay', '0.1.3', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 47, 'less').
project_file('examples/ci-agent/agent.py', 74, 'python').
project_file('examples/common/screenshot_meta.py', 163, 'python').
project_file('examples/common/validate_artifacts.py', 85, 'python').
project_file('examples/headless-virtual/run_virtual.py', 64, 'python').
project_file('examples/host-mirror/mirror_demo.py', 89, 'python').
project_file('examples/host-mirror/run.sh', 54, 'shell').
project_file('examples/host-relay/relay_demo.py', 139, 'python').
project_file('examples/host-relay/run-host.sh', 25, 'shell').
project_file('examples/host-relay/run.sh', 48, 'shell').
project_file('examples/run_all_examples.sh', 63, 'shell').
project_file('packages/cli2vdisplay/src/cli2vdisplay/cli.py', 35, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py', 5, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 87, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', 71, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 161, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py', 2, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 121, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 116, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/result.py', 27, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py', 39, 'python').
project_file('packages/dsl2vdisplay/tests/test_parity.py', 15, 'python').
project_file('packages/mcp2vdisplay/src/mcp2vdisplay/cli.py', 24, 'python').
project_file('packages/mcp2vdisplay/src/mcp2vdisplay/server.py', 54, 'python').
project_file('packages/nlp2vdisplay/src/nlp2vdisplay/cli.py', 42, 'python').
project_file('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 14, 'python').
project_file('packages/rest2vdisplay/src/rest2vdisplay/app.py', 88, 'python').
project_file('packages/rest2vdisplay/src/rest2vdisplay/cli.py', 36, 'python').
project_file('packages/uri2vdisplay/src/uri2vdisplay/cli.py', 31, 'python').
project_file('packages/uri2vdisplay/src/uri2vdisplay/decode.py', 32, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/__init__.py', 6, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/cli.py', 34, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/runtime.py', 254, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/server.py', 156, 'python').
project_file('project.sh', 59, 'shell').
project_file('src/vdisplay/__init__.py', 13, 'python').
project_file('src/vdisplay/agent_config.py', 23, 'python').
project_file('src/vdisplay/agent_dispatch.py', 252, 'python').
project_file('src/vdisplay/api.py', 194, 'python').
project_file('src/vdisplay/application/__init__.py', 6, 'python').
project_file('src/vdisplay/application/runtime.py', 46, 'python').
project_file('src/vdisplay/application/services/__init__.py', 4, 'python').
project_file('src/vdisplay/application/services/capture.py', 168, 'python').
project_file('src/vdisplay/application/services/discovery.py', 171, 'python').
project_file('src/vdisplay/application/services/info.py', 25, 'python').
project_file('src/vdisplay/application/services/session.py', 191, 'python').
project_file('src/vdisplay/backends/__init__.py', 2, 'python').
project_file('src/vdisplay/backends/base.py', 65, 'python').
project_file('src/vdisplay/backends/linux_x11_mirror.py', 260, 'python').
project_file('src/vdisplay/backends/linux_x11_relay.py', 479, 'python').
project_file('src/vdisplay/backends/linux_xvfb.py', 165, 'python').
project_file('src/vdisplay/backends/mirror_stub.py', 35, 'python').
project_file('src/vdisplay/capture/__init__.py', 16, 'python').
project_file('src/vdisplay/capture/base.py', 10, 'python').
project_file('src/vdisplay/capture/host.py', 289, 'python').
project_file('src/vdisplay/capture/linux_xwd.py', 320, 'python').
project_file('src/vdisplay/capture/portal.py', 222, 'python').
project_file('src/vdisplay/capture/providers/__init__.py', 4, 'python').
project_file('src/vdisplay/capture/providers/base.py', 23, 'python').
project_file('src/vdisplay/capture/providers/drm.py', 90, 'python').
project_file('src/vdisplay/capture/providers/engine.py', 100, 'python').
project_file('src/vdisplay/capture/providers/fbdev.py', 78, 'python').
project_file('src/vdisplay/capture/providers/mss.py', 61, 'python').
project_file('src/vdisplay/capture/providers/x11.py', 36, 'python').
project_file('src/vdisplay/cli.py', 33, 'python').
project_file('src/vdisplay/cli_handlers.py', 35, 'python').
project_file('src/vdisplay/client.py', 162, 'python').
project_file('src/vdisplay/commands/__init__.py', 41, 'python').
project_file('src/vdisplay/commands/agent.py', 46, 'python').
project_file('src/vdisplay/commands/all_cmd.py', 47, 'python').
project_file('src/vdisplay/commands/common.py', 36, 'python').
project_file('src/vdisplay/commands/diagnose.py', 19, 'python').
project_file('src/vdisplay/commands/info.py', 17, 'python').
project_file('src/vdisplay/commands/io.py', 8, 'python').
project_file('src/vdisplay/commands/mirror.py', 54, 'python').
project_file('src/vdisplay/commands/monitors.py', 20, 'python').
project_file('src/vdisplay/commands/nlp.py', 24, 'python').
project_file('src/vdisplay/commands/relay.py', 98, 'python').
project_file('src/vdisplay/commands/screenshot.py', 48, 'python').
project_file('src/vdisplay/commands/virtual.py', 73, 'python').
project_file('src/vdisplay/commands/windows.py', 30, 'python').
project_file('src/vdisplay/discovery.py', 330, 'python').
project_file('src/vdisplay/exceptions.py', 11, 'python').
project_file('src/vdisplay/input/__init__.py', 4, 'python').
project_file('src/vdisplay/input/linux_xdotool.py', 46, 'python').
project_file('src/vdisplay/models.py', 27, 'python').
project_file('src/vdisplay/nl.py', 159, 'python').
project_file('src/vdisplay/nlp.py', 159, 'python').
project_file('src/vdisplay/payloads.py', 87, 'python').
project_file('src/vdisplay/utils.py', 47, 'python').
project_file('src/vdisplay/windows/__init__.py', 47, 'python').
project_file('src/vdisplay/windows/constants.py', 20, 'python').
project_file('src/vdisplay/windows/filter.py', 174, 'python').
project_file('src/vdisplay/windows/normalize.py', 104, 'python').
project_file('src/vdisplay/windows/query.py', 210, 'python').
project_file('src/vdisplay/windows/rank.py', 44, 'python').
project_file('src/vdisplay/windows/scan.py', 111, 'python').
project_file('tests/conftest.py', 15, 'python').
project_file('tests/test_agent.py', 57, 'python').
project_file('tests/test_agent_client.py', 24, 'python').
project_file('tests/test_agent_dispatch.py', 43, 'python').
project_file('tests/test_agent_integration.py', 113, 'python').
project_file('tests/test_capture_crop.py', 50, 'python').
project_file('tests/test_capture_providers.py', 67, 'python').
project_file('tests/test_capture_xwd.py', 53, 'python').
project_file('tests/test_cli_commands.py', 106, 'python').
project_file('tests/test_host_capture.py', 38, 'python').
project_file('tests/test_import.py', 23, 'python').
project_file('tests/test_linux_xvfb_integration.py', 22, 'python').
project_file('tests/test_mirror_primary.py', 43, 'python').
project_file('tests/test_nl.py', 145, 'python').
project_file('tests/test_nlp_pipeline.py', 60, 'python').
project_file('tests/test_outputs_rotation.py', 35, 'python').
project_file('tests/test_relay_release.py', 66, 'python').
project_file('tests/test_screenshot_meta.py', 54, 'python').
project_file('tests/test_windows.py', 48, 'python').
project_file('tests/test_windows_dedupe.py', 26, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('examples/ci-agent/agent.py', '_load_common', 0, 4, 6).
python_function('examples/ci-agent/agent.py', 'main', 0, 3, 19).
python_function('examples/common/screenshot_meta.py', 'examples_common_dir', 0, 2, 4).
python_function('examples/common/screenshot_meta.py', 'ensure_common_on_path', 0, 2, 3).
python_function('examples/common/screenshot_meta.py', 'meta_path_for', 1, 1, 2).
python_function('examples/common/screenshot_meta.py', 'png_dimensions', 1, 5, 6).
python_function('examples/common/screenshot_meta.py', 'describe_screenshot_nl', 0, 14, 7).
python_function('examples/common/screenshot_meta.py', 'build_screenshot_meta', 1, 6, 9).
python_function('examples/common/screenshot_meta.py', 'write_screenshot_meta', 1, 1, 4).
python_function('examples/common/screenshot_meta.py', 'save_png_with_meta', 2, 2, 6).
python_function('examples/common/screenshot_meta.py', 'print_artifact', 1, 1, 2).
python_function('examples/common/validate_artifacts.py', 'validate_image_and_meta', 1, 12, 10).
python_function('examples/common/validate_artifacts.py', 'validate_directory', 1, 3, 4).
python_function('examples/common/validate_artifacts.py', 'main', 1, 6, 6).
python_function('examples/headless-virtual/run_virtual.py', '_load_common', 0, 4, 6).
python_function('examples/headless-virtual/run_virtual.py', 'main', 0, 1, 14).
python_function('examples/host-mirror/mirror_demo.py', '_load_common', 0, 4, 6).
python_function('examples/host-mirror/mirror_demo.py', 'main', 0, 5, 19).
python_function('examples/host-relay/relay_demo.py', '_load_common', 0, 4, 6).
python_function('examples/host-relay/relay_demo.py', '_capture_phase', 1, 1, 5).
python_function('examples/host-relay/relay_demo.py', 'main', 0, 11, 17).
python_function('packages/cli2vdisplay/src/cli2vdisplay/cli.py', 'main', 1, 7, 10).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', '_dispatch_query', 1, 2, 6).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', '_dispatch_cmd', 1, 3, 8).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 'dispatch', 1, 10, 15).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 'execute_dsl_line', 1, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', 'main', 1, 4, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', '_main_legacy', 1, 10, 11).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', '_main_subcommand', 1, 9, 13).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'split_command', 1, 4, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'pick_flag', 2, 3, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_with_display', 2, 2, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_windows', 2, 3, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_screenshot', 2, 5, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_virtual_start', 2, 4, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_launch', 2, 5, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_mirror', 2, 5, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_adopt', 2, 6, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_release', 2, 5, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'parse_line', 1, 3, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'to_text', 1, 7, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', '_ok', 3, 1, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', '_err', 4, 2, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_screenshot', 1, 2, 6).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_virtual_start', 1, 2, 6).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_mirror', 1, 3, 8).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_adopt', 1, 3, 7).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_release', 1, 3, 7).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_health', 1, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_info', 1, 1, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_monitors', 1, 1, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_outputs', 1, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_windows', 1, 1, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_all', 1, 1, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_capabilities', 1, 1, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_validate', 1, 4, 7).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py', '_load_schema', 1, 1, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py', 'all_schemas', 0, 3, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py', 'schema_for_verb', 1, 1, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py', 'validate_command_dict', 1, 3, 5).
python_function('packages/dsl2vdisplay/tests/test_parity.py', 'test_parity_info_text_vs_dict', 0, 3, 1).
python_function('packages/dsl2vdisplay/tests/test_parity.py', 'test_health', 0, 3, 1).
python_function('packages/mcp2vdisplay/src/mcp2vdisplay/cli.py', 'main', 0, 2, 6).
python_function('packages/mcp2vdisplay/src/mcp2vdisplay/cli.py', 'create_server', 0, 1, 1).
python_function('packages/mcp2vdisplay/src/mcp2vdisplay/server.py', 'create_server', 0, 1, 14).
python_function('packages/nlp2vdisplay/src/nlp2vdisplay/cli.py', 'main', 1, 7, 9).
python_function('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 'parse_display', 1, 1, 2).
python_function('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 'nl_to_dsl', 1, 1, 1).
python_function('packages/rest2vdisplay/src/rest2vdisplay/app.py', 'create_app', 0, 2, 22).
python_function('packages/rest2vdisplay/src/rest2vdisplay/cli.py', 'main', 0, 3, 9).
python_function('packages/uri2vdisplay/src/uri2vdisplay/cli.py', 'main', 1, 4, 10).
python_function('packages/uri2vdisplay/src/uri2vdisplay/decode.py', 'uri_to_dsl', 1, 7, 10).
python_function('packages/vdisplay-agent/src/vdisplay_agent/cli.py', 'main', 1, 3, 10).
python_function('packages/vdisplay-agent/src/vdisplay_agent/server.py', 'create_app', 1, 3, 29).
python_function('src/vdisplay/agent_config.py', 'resolve_agent_url', 1, 4, 3).
python_function('src/vdisplay/agent_config.py', 'resolve_agent_token', 0, 3, 2).
python_function('src/vdisplay/agent_config.py', 'use_agent', 1, 2, 4).
python_function('src/vdisplay/agent_dispatch.py', 'agent_client', 1, 2, 3).
python_function('src/vdisplay/agent_dispatch.py', '_ok_result', 0, 1, 2).
python_function('src/vdisplay/agent_dispatch.py', '_err_result', 0, 2, 1).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_health', 2, 1, 2).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_info', 2, 3, 3).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_monitors', 2, 2, 7).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_windows', 2, 1, 7).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_all', 2, 1, 8).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_capabilities', 2, 1, 3).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_validate', 2, 4, 8).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_screenshot', 2, 5, 7).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_virtual_start', 2, 1, 4).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_mirror', 2, 5, 9).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_adopt', 2, 1, 4).
python_function('src/vdisplay/agent_dispatch.py', '_dispatch_release', 2, 1, 4).
python_function('src/vdisplay/agent_dispatch.py', 'dispatch_via_agent', 1, 3, 7).
python_function('src/vdisplay/api.py', '_default_virtual_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', '_default_mirror_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', '_default_relay_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', 'platform_summary', 0, 1, 5).
python_function('src/vdisplay/application/runtime.py', 'agent_client_optional', 0, 2, 2).
python_function('src/vdisplay/application/runtime.py', 'agent_client_required', 0, 2, 2).
python_function('src/vdisplay/application/runtime.py', 'prefer_agent', 0, 1, 1).
python_function('src/vdisplay/application/runtime.py', 'resolve_apps_only', 0, 3, 0).
python_function('src/vdisplay/application/services/capture.py', 'capture_screenshot', 0, 3, 4).
python_function('src/vdisplay/application/services/capture.py', '_capture_via_agent', 1, 8, 6).
python_function('src/vdisplay/application/services/capture.py', '_capture_local', 0, 7, 10).
python_function('src/vdisplay/application/services/capture.py', 'capture_screenshot_via_client', 1, 1, 1).
python_function('src/vdisplay/application/services/discovery.py', 'list_monitors', 1, 4, 8).
python_function('src/vdisplay/application/services/discovery.py', 'list_windows_payload', 1, 10, 7).
python_function('src/vdisplay/application/services/discovery.py', 'list_windows_local', 1, 2, 6).
python_function('src/vdisplay/application/services/discovery.py', 'list_adopted', 1, 1, 4).
python_function('src/vdisplay/application/services/discovery.py', 'list_all', 1, 4, 4).
python_function('src/vdisplay/application/services/discovery.py', 'diagnose', 1, 2, 2).
python_function('src/vdisplay/application/services/info.py', 'platform_info', 0, 2, 4).
python_function('src/vdisplay/application/services/session.py', 'virtual_start', 0, 1, 4).
python_function('src/vdisplay/application/services/session.py', 'virtual_launch', 1, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'virtual_screenshot', 1, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'mirror_start', 0, 2, 6).
python_function('src/vdisplay/application/services/session.py', 'mirror_screenshot', 1, 1, 3).
python_function('src/vdisplay/application/services/session.py', 'relay_adopt', 0, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'relay_release', 0, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'relay_list_adopted', 1, 1, 4).
python_function('src/vdisplay/application/services/session.py', 'relay_screenshot', 1, 1, 1).
python_function('src/vdisplay/application/services/session.py', 'unsupported_session_action', 2, 1, 1).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_require_xrandr', 0, 2, 2).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_resolve_mirror_targets', 4, 3, 4).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_try_mirror', 3, 5, 2).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_mirror_exhausted_error', 4, 5, 2).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_list_connected_outputs', 1, 3, 5).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_resolve_output', 3, 10, 9).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_primary_output_from_xrandr', 1, 3, 4).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_output_capture_region', 2, 5, 3).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_mirror_target_candidates', 3, 7, 1).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_output_mode', 2, 7, 5).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_stash_path', 2, 2, 4).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_load_stash', 2, 5, 8).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_save_stash', 3, 4, 7).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_state_as_match_info', 1, 1, 0).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_state_matches', 1, 10, 5).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_select_adopted_for_release', 1, 7, 6).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_related_adopted_ids', 2, 7, 5).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_pick_primary_release_id', 2, 4, 1).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_restore_window', 2, 1, 2).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_find_window_id', 1, 12, 8).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_move_window', 4, 1, 2).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_window_metadata', 2, 1, 1).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_window_geometry', 2, 4, 4).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_window_title', 2, 1, 2).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_offscreen_coordinates', 1, 1, 1).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_screen_geometry', 1, 2, 6).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_output_origin', 2, 11, 12).
python_function('src/vdisplay/backends/linux_xvfb.py', '_display_candidates', 1, 4, 4).
python_function('src/vdisplay/backends/linux_xvfb.py', '_display_socket_exists', 1, 1, 3).
python_function('src/vdisplay/backends/linux_xvfb.py', '_probe_display', 1, 2, 2).
python_function('src/vdisplay/backends/linux_xvfb.py', '_wait_for_display', 1, 7, 8).
python_function('src/vdisplay/capture/host.py', '_monitor_source_name', 3, 9, 7).
python_function('src/vdisplay/capture/host.py', '_monitor_capture_region', 2, 4, 3).
python_function('src/vdisplay/capture/host.py', '_capture_all_from_driver_full', 3, 7, 13).
python_function('src/vdisplay/capture/host.py', 'capture_host_png', 0, 13, 18).
python_function('src/vdisplay/capture/host.py', 'capture_host_to_file', 1, 3, 9).
python_function('src/vdisplay/capture/host.py', 'capture_all_monitors', 0, 11, 15).
python_function('src/vdisplay/capture/linux_xwd.py', '_is_valid_png', 1, 2, 1).
python_function('src/vdisplay/capture/linux_xwd.py', 'is_blank_png', 1, 8, 11).
python_function('src/vdisplay/capture/linux_xwd.py', '_is_wayland_session', 0, 3, 3).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_hint', 1, 2, 1).
python_function('src/vdisplay/capture/linux_xwd.py', '_crop_png', 2, 2, 8).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_full_display_png', 1, 1, 1).
python_function('src/vdisplay/capture/linux_xwd.py', 'capture_display_png', 1, 2, 2).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_xwd_png', 1, 1, 3).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_scrot_png', 2, 5, 11).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_gnome_screenshot_png', 0, 4, 10).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_portal_png', 0, 1, 1).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_grim_png', 0, 4, 11).
python_function('src/vdisplay/capture/linux_xwd.py', 'xwd_bytes_to_png', 1, 1, 3).
python_function('src/vdisplay/capture/linux_xwd.py', '_xwd_dimensions', 1, 1, 1).
python_function('src/vdisplay/capture/linux_xwd.py', '_xwd_to_rgb_bytes', 1, 6, 6).
python_function('src/vdisplay/capture/linux_xwd.py', '_parse_xwd_header', 1, 3, 4).
python_function('src/vdisplay/capture/linux_xwd.py', '_read_xwd_header', 1, 2, 5).
python_function('src/vdisplay/capture/linux_xwd.py', '_header_fields', 1, 1, 0).
python_function('src/vdisplay/capture/linux_xwd.py', '_decode_pixels', 2, 12, 5).
python_function('src/vdisplay/capture/linux_xwd.py', '_rgb_to_png', 3, 2, 5).
python_function('src/vdisplay/capture/linux_xwd.py', '_rgb_to_png_minimal', 3, 2, 7).
python_function('src/vdisplay/capture/portal.py', '_portal_impl', 1, 4, 22).
python_function('src/vdisplay/capture/portal.py', '_system_python', 0, 4, 3).
python_function('src/vdisplay/capture/portal.py', 'capture_portal_png', 0, 4, 9).
python_function('src/vdisplay/capture/portal.py', '_capture_portal_to_file', 1, 11, 8).
python_function('src/vdisplay/capture/providers/drm.py', '_drm_devices', 0, 5, 7).
python_function('src/vdisplay/capture/providers/engine.py', '_allow_portal', 0, 1, 3).
python_function('src/vdisplay/capture/providers/engine.py', '_providers', 1, 4, 9).
python_function('src/vdisplay/capture/providers/engine.py', 'capture_full_png', 1, 1, 2).
python_function('src/vdisplay/capture/providers/engine.py', 'capture_region_png', 2, 1, 2).
python_function('src/vdisplay/capture/providers/engine.py', 'list_capture_providers', 1, 4, 6).
python_function('src/vdisplay/capture/providers/engine.py', '_try_providers', 1, 11, 12).
python_function('src/vdisplay/capture/providers/fbdev.py', '_fb_info', 0, 2, 7).
python_function('src/vdisplay/cli.py', 'build_parser', 0, 1, 3).
python_function('src/vdisplay/cli.py', 'main', 1, 2, 4).
python_function('src/vdisplay/cli_handlers.py', 'print_json', 1, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'monitors_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'windows_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'all_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'screenshot_payload', 0, 1, 2).
python_function('src/vdisplay/cli_handlers.py', 'dispatch_cli', 1, 1, 2).
python_function('src/vdisplay/commands/__init__.py', 'register_all', 1, 2, 1).
python_function('src/vdisplay/commands/agent.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/agent.py', 'handle', 1, 7, 9).
python_function('src/vdisplay/commands/all_cmd.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/all_cmd.py', 'handle', 1, 1, 3).
python_function('src/vdisplay/commands/all_cmd.py', 'register_outputs', 1, 1, 4).
python_function('src/vdisplay/commands/all_cmd.py', 'handle_outputs', 1, 1, 3).
python_function('src/vdisplay/commands/common.py', 'add_display_arg', 1, 1, 1).
python_function('src/vdisplay/commands/common.py', 'add_all_arg', 1, 1, 1).
python_function('src/vdisplay/commands/common.py', 'add_window_filter_args', 1, 1, 2).
python_function('src/vdisplay/commands/common.py', 'include_all_from_args', 1, 2, 2).
python_function('src/vdisplay/commands/diagnose.py', 'register', 1, 1, 3).
python_function('src/vdisplay/commands/diagnose.py', 'handle', 1, 1, 2).
python_function('src/vdisplay/commands/info.py', 'register', 1, 1, 2).
python_function('src/vdisplay/commands/info.py', 'handle', 1, 1, 2).
python_function('src/vdisplay/commands/io.py', 'print_json', 1, 1, 2).
python_function('src/vdisplay/commands/mirror.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/mirror.py', 'handle', 1, 3, 4).
python_function('src/vdisplay/commands/monitors.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/monitors.py', 'handle', 1, 1, 3).
python_function('src/vdisplay/commands/nlp.py', 'register', 1, 1, 3).
python_function('src/vdisplay/commands/nlp.py', 'handle', 1, 2, 2).
python_function('src/vdisplay/commands/relay.py', 'register', 1, 1, 6).
python_function('src/vdisplay/commands/relay.py', 'handle_list_windows', 1, 1, 2).
python_function('src/vdisplay/commands/relay.py', 'handle', 1, 5, 6).
python_function('src/vdisplay/commands/screenshot.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/screenshot.py', 'handle', 1, 1, 2).
python_function('src/vdisplay/commands/virtual.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/virtual.py', 'handle', 1, 4, 5).
python_function('src/vdisplay/commands/windows.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/windows.py', 'handle', 1, 1, 3).
python_function('src/vdisplay/discovery.py', 'resolve_host_display', 1, 9, 5).
python_function('src/vdisplay/discovery.py', '_looks_like_xvfb_only', 1, 4, 4).
python_function('src/vdisplay/discovery.py', 'list_outputs', 1, 8, 15).
python_function('src/vdisplay/discovery.py', '_attach_output_nl', 2, 2, 3).
python_function('src/vdisplay/discovery.py', '_list_monitors', 1, 6, 9).
python_function('src/vdisplay/discovery.py', '_parse_xrandr_query', 1, 8, 8).
python_function('src/vdisplay/discovery.py', '_merge_output_metadata', 2, 3, 3).
python_function('src/vdisplay/discovery.py', 'list_windows', 1, 2, 4).
python_function('src/vdisplay/discovery.py', 'find_window_suggestions', 3, 2, 2).
python_function('src/vdisplay/discovery.py', 'diagnose_display', 1, 5, 10).
python_function('src/vdisplay/discovery.py', '_display_hint', 3, 3, 2).
python_function('src/vdisplay/discovery.py', 'list_monitors', 1, 1, 1).
python_function('src/vdisplay/discovery.py', 'window_discovery_meta', 1, 2, 1).
python_function('src/vdisplay/nl.py', 'describe_window_nl', 1, 14, 3).
python_function('src/vdisplay/nl.py', '_user_visible_app_labels', 1, 9, 5).
python_function('src/vdisplay/nl.py', 'describe_output_nl', 2, 13, 5).
python_function('src/vdisplay/nl.py', 'window_center_on_output', 2, 3, 2).
python_function('src/vdisplay/nl.py', 'ensure_monitor_ids', 1, 5, 4).
python_function('src/vdisplay/nl.py', 'find_monitor_for_window', 2, 3, 1).
python_function('src/vdisplay/nl.py', 'assign_windows_to_monitors', 2, 3, 4).
python_function('src/vdisplay/nl.py', 'enrich_outputs_nl', 2, 4, 2).
python_function('src/vdisplay/nlp.py', 'parse_display', 1, 10, 4).
python_function('src/vdisplay/nlp.py', '_display_suffix', 1, 2, 0).
python_function('src/vdisplay/nlp.py', '_default_display_suffix', 1, 2, 1).
python_function('src/vdisplay/nlp.py', '_default_all', 2, 1, 1).
python_function('src/vdisplay/nlp.py', '_default_monitors', 2, 1, 1).
python_function('src/vdisplay/nlp.py', '_default_windows', 2, 1, 1).
python_function('src/vdisplay/nlp.py', '_screenshot_dsl', 2, 2, 2).
python_function('src/vdisplay/nlp.py', '_mirror_dsl', 2, 1, 0).
python_function('src/vdisplay/nlp.py', '_release_dsl', 2, 4, 0).
python_function('src/vdisplay/nlp.py', '_adopt_dsl', 2, 3, 0).
python_function('src/vdisplay/nlp.py', '_validate_dsl', 2, 1, 2).
python_function('src/vdisplay/nlp.py', 'nl_to_dsl', 1, 4, 6).
python_function('src/vdisplay/nlp.py', 'run_nl_prompt', 1, 5, 6).
python_function('src/vdisplay/nlp.py', '_run_local_dsl', 1, 7, 7).
python_function('src/vdisplay/payloads.py', 'monitors_payload', 1, 1, 1).
python_function('src/vdisplay/payloads.py', 'local_windows_payload', 1, 1, 1).
python_function('src/vdisplay/payloads.py', 'windows_payload', 1, 1, 1).
python_function('src/vdisplay/payloads.py', 'adopted_payload', 1, 1, 1).
python_function('src/vdisplay/payloads.py', 'all_payload', 1, 1, 1).
python_function('src/vdisplay/utils.py', 'require_command', 1, 2, 2).
python_function('src/vdisplay/utils.py', 'run_command', 1, 2, 4).
python_function('src/vdisplay/utils.py', 'run_command_bytes', 1, 1, 1).
python_function('src/vdisplay/windows/filter.py', 'looks_like_internal_class', 1, 3, 2).
python_function('src/vdisplay/windows/filter.py', 'looks_like_internal_name', 1, 3, 2).
python_function('src/vdisplay/windows/filter.py', 'is_trivial_internal', 0, 5, 0).
python_function('src/vdisplay/windows/filter.py', 'is_junk_title', 2, 6, 1).
python_function('src/vdisplay/windows/filter.py', 'is_visible_app', 5, 9, 1).
python_function('src/vdisplay/windows/filter.py', 'is_internal_window', 0, 13, 5).
python_function('src/vdisplay/windows/filter.py', 'matches_title', 2, 4, 3).
python_function('src/vdisplay/windows/filter.py', 'matches_class', 2, 5, 3).
python_function('src/vdisplay/windows/filter.py', 'matches_app', 2, 7, 4).
python_function('src/vdisplay/windows/filter.py', 'window_passes_filters', 1, 11, 3).
python_function('src/vdisplay/windows/filter.py', 'filter_windows', 1, 14, 6).
python_function('src/vdisplay/windows/filter.py', 'is_companion_frame', 2, 9, 4).
python_function('src/vdisplay/windows/normalize.py', 'parse_wm_class', 1, 7, 4).
python_function('src/vdisplay/windows/normalize.py', 'normalize_atom_list', 1, 3, 5).
python_function('src/vdisplay/windows/normalize.py', 'resolve_window_pid', 3, 3, 5).
python_function('src/vdisplay/windows/normalize.py', 'process_info', 1, 6, 7).
python_function('src/vdisplay/windows/normalize.py', 'usable_title', 1, 3, 3).
python_function('src/vdisplay/windows/normalize.py', 'derive_app_label', 0, 14, 3).
python_function('src/vdisplay/windows/normalize.py', 'derive_role', 0, 10, 3).
python_function('src/vdisplay/windows/query.py', 'list_windows_enriched', 1, 2, 5).
python_function('src/vdisplay/windows/query.py', 'scan_windows', 1, 4, 4).
python_function('src/vdisplay/windows/query.py', 'inspect_window', 2, 9, 14).
python_function('src/vdisplay/windows/query.py', 'find_windows', 1, 6, 3).
python_function('src/vdisplay/windows/query.py', 'pick_best_window', 1, 8, 2).
python_function('src/vdisplay/windows/query.py', 'find_companion_frames', 2, 8, 6).
python_function('src/vdisplay/windows/rank.py', 'window_area', 1, 3, 1).
python_function('src/vdisplay/windows/rank.py', 'pick_largest', 1, 1, 1).
python_function('src/vdisplay/windows/rank.py', 'pick_best_from_group', 1, 9, 4).
python_function('src/vdisplay/windows/rank.py', 'dedupe_app_windows', 1, 5, 7).
python_function('src/vdisplay/windows/rank.py', 'window_sort_key', 1, 5, 1).
python_function('src/vdisplay/windows/scan.py', 'root_window_id', 1, 3, 6).
python_function('src/vdisplay/windows/scan.py', 'xdotool', 1, 1, 1).
python_function('src/vdisplay/windows/scan.py', 'format_window_id', 1, 3, 3).
python_function('src/vdisplay/windows/scan.py', 'xprop', 2, 5, 8).
python_function('src/vdisplay/windows/scan.py', 'decode_xprop_value', 1, 6, 5).
python_function('src/vdisplay/windows/scan.py', 'window_geometry', 2, 4, 5).
python_function('src/vdisplay/windows/scan.py', 'search_window_ids', 1, 4, 5).
python_function('tests/conftest.py', '_isolate_agent_env', 1, 1, 2).
python_function('tests/test_agent.py', 'agent_client', 0, 1, 3).
python_function('tests/test_agent.py', 'test_agent_health', 1, 4, 2).
python_function('tests/test_agent.py', 'test_agent_capabilities', 1, 4, 2).
python_function('tests/test_agent.py', 'test_agent_virtual_session_capture', 2, 7, 7).
python_function('tests/test_agent_client.py', 'test_use_agent_false_by_default', 1, 3, 3).
python_function('tests/test_agent_client.py', 'test_client_unreachable_raises', 1, 1, 4).
python_function('tests/test_agent_dispatch.py', 'test_dispatch_monitors_via_agent', 1, 4, 4).
python_function('tests/test_agent_dispatch.py', 'test_dsl_bus_uses_agent_when_configured', 1, 3, 5).
python_function('tests/test_agent_integration.py', '_wait_for_url', 1, 4, 4).
python_function('tests/test_agent_integration.py', 'live_agent_url', 0, 1, 12).
python_function('tests/test_agent_integration.py', 'test_agent_client_round_trip_monitors', 2, 3, 4).
python_function('tests/test_agent_integration.py', 'test_dsl_dispatch_round_trip', 2, 6, 2).
python_function('tests/test_agent_integration.py', 'test_rest2vdisplay_round_trip', 2, 5, 7).
python_function('tests/test_agent_integration.py', 'test_virtual_screenshot_round_trip', 3, 4, 7).
python_function('tests/test_capture_crop.py', '_make_png', 3, 1, 4).
python_function('tests/test_capture_crop.py', 'test_crop_png_extracts_region', 0, 3, 4).
python_function('tests/test_capture_crop.py', 'test_capture_display_png_region_uses_provider_engine', 1, 2, 4).
python_function('tests/test_capture_crop.py', 'test_is_blank_png_detects_black', 0, 3, 2).
python_function('tests/test_capture_providers.py', '_make_png', 3, 1, 4).
python_function('tests/test_capture_providers.py', 'test_try_providers_prefers_first_non_blank', 0, 3, 3).
python_function('tests/test_capture_providers.py', 'test_list_capture_providers_includes_drm', 0, 3, 2).
python_function('tests/test_capture_providers.py', 'test_x11_provider_region_falls_back_to_crop', 1, 3, 3).
python_function('tests/test_capture_xwd.py', '_make_xwd', 3, 1, 1).
python_function('tests/test_capture_xwd.py', 'test_xwd_to_png_red_pixel', 0, 2, 3).
python_function('tests/test_capture_xwd.py', 'test_xwd_to_png_2x1', 0, 3, 5).
python_function('tests/test_capture_xwd.py', 'test_is_blank_png_detects_black_frame', 0, 3, 4).
python_function('tests/test_cli_commands.py', 'test_parser_has_discovery_commands', 0, 6, 1).
python_function('tests/test_cli_commands.py', 'test_monitors_command_registered', 0, 2, 2).
python_function('tests/test_cli_commands.py', 'test_windows_defaults_to_include_all', 1, 3, 5).
python_function('tests/test_cli_commands.py', 'test_windows_apps_only_flag', 1, 3, 5).
python_function('tests/test_cli_commands.py', 'test_payload_defaults_include_all', 0, 3, 1).
python_function('tests/test_cli_commands.py', 'test_all_command_structure', 1, 7, 5).
python_function('tests/test_host_capture.py', 'test_capture_host_png_prefers_mirror', 1, 3, 5).
python_function('tests/test_import.py', 'test_imports', 0, 4, 0).
python_function('tests/test_import.py', 'test_platform_summary', 0, 3, 1).
python_function('tests/test_import.py', 'test_capabilities', 0, 4, 2).
python_function('tests/test_linux_xvfb_integration.py', 'test_virtual_display_screenshot', 1, 3, 9).
python_function('tests/test_mirror_primary.py', 'test_primary_output_from_xrandr', 1, 2, 4).
python_function('tests/test_mirror_primary.py', 'test_mirror_target_candidates_prefers_non_primary', 1, 2, 3).
python_function('tests/test_nl.py', 'test_describe_window_nl_application', 0, 4, 1).
python_function('tests/test_nl.py', 'test_describe_output_nl_with_apps', 0, 4, 1).
python_function('tests/test_nl.py', 'test_describe_output_nl_skips_internal_helpers', 0, 3, 1).
python_function('tests/test_nl.py', 'test_describe_output_nl_empty_monitor', 0, 2, 1).
python_function('tests/test_nl.py', 'test_window_center_on_output', 0, 2, 1).
python_function('tests/test_nl.py', 'test_assign_windows_to_monitors', 0, 5, 1).
python_function('tests/test_nl.py', 'test_ensure_monitor_ids', 0, 3, 1).
python_function('tests/test_nl.py', 'test_enrich_outputs_nl_adds_field', 0, 4, 1).
python_function('tests/test_nlp_pipeline.py', 'test_nl_to_dsl_monitors_on_display_zero', 0, 2, 1).
python_function('tests/test_nlp_pipeline.py', 'test_nl_to_dsl_windows', 0, 2, 1).
python_function('tests/test_nlp_pipeline.py', 'test_run_nl_prompt_dsl_only', 0, 4, 1).
python_function('tests/test_nlp_pipeline.py', 'test_run_nl_prompt_full_pipeline', 1, 6, 3).
python_function('tests/test_nlp_pipeline.py', 'test_dsl2vdisplay_monitors_matches_payload', 1, 5, 3).
python_function('tests/test_outputs_rotation.py', 'test_rotation_degrees_mapping', 0, 5, 0).
python_function('tests/test_outputs_rotation.py', 'test_parse_xrandr_query_rotation_from_sample', 0, 7, 3).
python_function('tests/test_relay_release.py', '_toolbox_states', 0, 1, 1).
python_function('tests/test_relay_release.py', 'test_state_matches_app_jetbrains', 0, 3, 2).
python_function('tests/test_relay_release.py', 'test_select_adopted_for_release_by_app_includes_frame', 0, 2, 3).
python_function('tests/test_relay_release.py', 'test_stash_roundtrip', 2, 4, 5).
python_function('tests/test_screenshot_meta.py', 'test_describe_screenshot_nl', 0, 4, 1).
python_function('tests/test_screenshot_meta.py', 'test_build_and_meta_path', 1, 6, 7).
python_function('tests/test_windows.py', 'test_parse_wm_class', 0, 3, 1).
python_function('tests/test_windows.py', 'test_derive_app_label_prefers_title', 0, 2, 1).
python_function('tests/test_windows.py', 'test_internal_helper_window', 0, 2, 1).
python_function('tests/test_windows.py', 'test_matches_title_on_app_label', 0, 3, 2).
python_function('tests/test_windows_dedupe.py', 'test_dedupe_prefers_application_over_mutter_frame', 0, 3, 2).

% ── Python Classes ───────────────────────────────────────
python_class('packages/dsl2vdisplay/src/dsl2vdisplay/result.py', 'DslResult').
python_method('DslResult', 'to_dict', 0, 1, 0).
python_class('packages/vdisplay-agent/src/vdisplay_agent/runtime.py', 'SessionRecord').
python_class('packages/vdisplay-agent/src/vdisplay_agent/runtime.py', 'AgentRuntime').
python_method('AgentRuntime', 'platform_capabilities', 0, 3, 8).
python_method('AgentRuntime', 'diagnostics', 0, 1, 4).
python_method('AgentRuntime', 'outputs', 0, 2, 4).
python_method('AgentRuntime', 'list_windows', 0, 8, 6).
python_method('AgentRuntime', 'start_virtual', 0, 1, 6).
python_method('AgentRuntime', 'start_mirror', 0, 1, 6).
python_method('AgentRuntime', 'start_relay', 0, 2, 6).
python_method('AgentRuntime', 'stop_session', 1, 4, 3).
python_method('AgentRuntime', 'capture_frame', 1, 10, 17).
python_method('AgentRuntime', 'adopt_window', 1, 6, 4).
python_method('AgentRuntime', 'release_window', 1, 5, 4).
python_method('AgentRuntime', '_relay_session', 1, 5, 5).
python_method('AgentRuntime', 'shutdown', 0, 4, 3).
python_class('src/vdisplay/api.py', 'VirtualDisplaySession').
python_method('VirtualDisplaySession', '__init__', 1, 1, 0).
python_method('VirtualDisplaySession', 'create', 5, 4, 5).
python_method('VirtualDisplaySession', 'start', 0, 1, 1).
python_method('VirtualDisplaySession', 'stop', 0, 1, 1).
python_method('VirtualDisplaySession', 'launch', 1, 1, 1).
python_method('VirtualDisplaySession', 'screenshot_bytes', 0, 1, 1).
python_method('VirtualDisplaySession', 'save_screenshot', 1, 1, 1).
python_method('VirtualDisplaySession', 'adopt_window', 0, 1, 1).
python_method('VirtualDisplaySession', 'release_window', 0, 1, 1).
python_method('VirtualDisplaySession', 'info', 0, 1, 2).
python_method('VirtualDisplaySession', 'capabilities', 0, 1, 2).
python_class('src/vdisplay/api.py', 'MirrorSession').
python_method('MirrorSession', '__init__', 1, 1, 1).
python_method('MirrorSession', 'create', 5, 4, 6).
python_method('MirrorSession', 'start', 0, 1, 1).
python_method('MirrorSession', 'stop', 0, 1, 1).
python_method('MirrorSession', 'screenshot_bytes', 0, 1, 1).
python_method('MirrorSession', 'save_screenshot', 1, 1, 1).
python_method('MirrorSession', 'info', 0, 1, 2).
python_method('MirrorSession', 'capabilities', 0, 1, 2).
python_class('src/vdisplay/api.py', 'WindowRelaySession').
python_method('WindowRelaySession', '__init__', 1, 1, 0).
python_method('WindowRelaySession', 'create', 3, 4, 5).
python_method('WindowRelaySession', 'start', 0, 1, 1).
python_method('WindowRelaySession', 'stop', 0, 1, 1).
python_method('WindowRelaySession', 'adopt_window', 0, 1, 1).
python_method('WindowRelaySession', 'release_window', 0, 1, 1).
python_method('WindowRelaySession', 'list_adopted', 0, 1, 1).
python_method('WindowRelaySession', 'info', 0, 1, 2).
python_method('WindowRelaySession', 'capabilities', 0, 1, 2).
python_class('src/vdisplay/backends/base.py', 'BaseBackend').
python_method('BaseBackend', '__init__', 0, 1, 0).
python_method('BaseBackend', 'capabilities', 0, 1, 1).
python_method('BaseBackend', 'info', 0, 1, 1).
python_method('BaseBackend', 'start', 0, 1, 0).
python_method('BaseBackend', 'stop', 0, 1, 0).
python_method('BaseBackend', 'launch', 1, 1, 1).
python_method('BaseBackend', 'screenshot_bytes', 0, 1, 1).
python_method('BaseBackend', 'save_screenshot', 1, 1, 3).
python_method('BaseBackend', 'adopt_window', 0, 1, 1).
python_method('BaseBackend', 'release_window', 0, 1, 1).
python_method('BaseBackend', 'as_dict', 0, 1, 2).
python_class('src/vdisplay/backends/linux_x11_mirror.py', 'LinuxX11MirrorBackend').
python_method('LinuxX11MirrorBackend', '__init__', 3, 1, 4).
python_method('LinuxX11MirrorBackend', 'capabilities', 0, 1, 1).
python_method('LinuxX11MirrorBackend', 'info', 0, 3, 1).
python_method('LinuxX11MirrorBackend', 'start', 0, 5, 10).
python_method('LinuxX11MirrorBackend', '_activate_mirror', 2, 1, 0).
python_method('LinuxX11MirrorBackend', 'stop', 0, 5, 1).
python_method('LinuxX11MirrorBackend', 'screenshot_bytes', 0, 2, 3).
python_class('src/vdisplay/backends/linux_x11_relay.py', 'WindowState').
python_class('src/vdisplay/backends/linux_x11_relay.py', 'LinuxX11RelayBackend').
python_method('LinuxX11RelayBackend', '__init__', 2, 1, 3).
python_method('LinuxX11RelayBackend', 'capabilities', 0, 1, 1).
python_method('LinuxX11RelayBackend', 'info', 0, 1, 2).
python_method('LinuxX11RelayBackend', 'start', 0, 2, 3).
python_method('LinuxX11RelayBackend', 'adopt_window', 0, 12, 13).
python_method('LinuxX11RelayBackend', 'release_window', 0, 6, 8).
python_method('LinuxX11RelayBackend', 'list_adopted', 0, 4, 4).
python_class('src/vdisplay/backends/linux_xvfb.py', 'LinuxXvfbBackend').
python_method('LinuxXvfbBackend', '__init__', 3, 1, 2).
python_method('LinuxXvfbBackend', 'capabilities', 0, 1, 1).
python_method('LinuxXvfbBackend', 'info', 0, 1, 1).
python_method('LinuxXvfbBackend', 'start', 0, 4, 4).
python_method('LinuxXvfbBackend', 'stop', 0, 4, 3).
python_method('LinuxXvfbBackend', 'launch', 1, 2, 4).
python_method('LinuxXvfbBackend', 'screenshot_bytes', 0, 2, 2).
python_method('LinuxXvfbBackend', 'adopt_window', 0, 1, 1).
python_method('LinuxXvfbBackend', 'release_window', 0, 1, 1).
python_method('LinuxXvfbBackend', '_acquire_display', 1, 8, 12).
python_class('src/vdisplay/backends/mirror_stub.py', 'MirrorStubBackend').
python_method('MirrorStubBackend', '__init__', 2, 1, 2).
python_method('MirrorStubBackend', 'capabilities', 0, 1, 1).
python_method('MirrorStubBackend', 'info', 0, 1, 1).
python_method('MirrorStubBackend', 'screenshot_bytes', 0, 1, 0).
python_class('src/vdisplay/capture/base.py', 'CaptureBackend').
python_method('CaptureBackend', 'screenshot_png', 0, 1, 0).
python_class('src/vdisplay/capture/portal.py', 'PortalProvider').
python_method('PortalProvider', 'available', 0, 1, 0).
python_method('PortalProvider', 'capture_full', 0, 1, 1).
python_method('PortalProvider', 'capture_region', 1, 1, 2).
python_class('src/vdisplay/capture/providers/base.py', 'ProviderResult').
python_class('src/vdisplay/capture/providers/base.py', 'CaptureProvider').
python_method('CaptureProvider', 'available', 0, 1, 0).
python_method('CaptureProvider', 'capture_full', 0, 1, 0).
python_method('CaptureProvider', 'capture_region', 1, 1, 0).
python_class('src/vdisplay/capture/providers/drm.py', 'DrmProvider').
python_method('DrmProvider', 'available', 0, 3, 2).
python_method('DrmProvider', 'capture_full', 0, 1, 1).
python_method('DrmProvider', 'capture_region', 1, 1, 1).
python_method('DrmProvider', '_capture', 1, 11, 15).
python_class('src/vdisplay/capture/providers/fbdev.py', 'FbdevProvider').
python_method('FbdevProvider', 'available', 0, 3, 4).
python_method('FbdevProvider', 'capture_full', 0, 1, 1).
python_method('FbdevProvider', 'capture_region', 1, 1, 1).
python_method('FbdevProvider', '_capture', 1, 7, 13).
python_class('src/vdisplay/capture/providers/mss.py', 'MssProvider').
python_method('MssProvider', '__init__', 1, 1, 0).
python_method('MssProvider', 'available', 0, 2, 0).
python_method('MssProvider', 'capture_full', 0, 1, 1).
python_method('MssProvider', 'capture_region', 1, 1, 1).
python_method('MssProvider', '_grab', 1, 8, 10).
python_class('src/vdisplay/capture/providers/x11.py', 'X11Provider').
python_method('X11Provider', '__init__', 1, 1, 0).
python_method('X11Provider', 'available', 0, 1, 0).
python_method('X11Provider', 'capture_full', 0, 4, 5).
python_method('X11Provider', 'capture_region', 1, 2, 3).
python_class('src/vdisplay/client.py', 'AgentClient').
python_method('AgentClient', '__init__', 1, 2, 2).
python_method('AgentClient', '_request', 2, 13, 12).
python_method('AgentClient', 'health', 0, 1, 1).
python_method('AgentClient', 'capabilities', 0, 1, 1).
python_method('AgentClient', 'diagnostics', 0, 1, 1).
python_method('AgentClient', 'outputs', 0, 4, 3).
python_method('AgentClient', 'windows', 0, 4, 3).
python_method('AgentClient', 'start_virtual', 0, 1, 1).
python_method('AgentClient', 'start_mirror', 0, 1, 1).
python_method('AgentClient', 'start_relay', 0, 1, 1).
python_method('AgentClient', 'stop_session', 1, 1, 1).
python_method('AgentClient', 'capture_frame', 0, 1, 1).
python_method('AgentClient', 'capture_png_bytes', 0, 2, 6).
python_method('AgentClient', 'adopt_window', 0, 1, 1).
python_method('AgentClient', 'release_window', 0, 1, 1).
python_class('src/vdisplay/exceptions.py', 'VDisplayError').
python_class('src/vdisplay/exceptions.py', 'BackendNotAvailableError').
python_class('src/vdisplay/exceptions.py', 'CapabilityError').
python_class('src/vdisplay/input/linux_xdotool.py', 'LinuxXdotoolInput').
python_method('LinuxXdotoolInput', '__init__', 1, 1, 0).
python_method('LinuxXdotoolInput', '_env', 0, 2, 0).
python_method('LinuxXdotoolInput', 'move', 2, 1, 4).
python_method('LinuxXdotoolInput', 'click', 1, 1, 4).
python_method('LinuxXdotoolInput', 'type_text', 1, 1, 3).
python_method('LinuxXdotoolInput', 'hotkey', 0, 1, 3).
python_class('src/vdisplay/models.py', 'Capabilities').
python_class('src/vdisplay/models.py', 'SessionInfo').
python_class('tests/test_capture_providers.py', '_StubProvider').
python_method('_StubProvider', '__init__', 1, 1, 0).
python_method('_StubProvider', 'available', 0, 1, 0).
python_method('_StubProvider', 'capture_full', 0, 1, 0).
python_method('_StubProvider', 'capture_region', 1, 1, 0).
python_class('tests/test_mirror_primary.py', '_FakeResult').
python_method('_FakeResult', '__init__', 2, 1, 0).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', 'sk-or-v1-...', 'OpenRouter API Key (required for real cost calculation)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Default AI model for cost analysis').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('api', '').
sumd_interface('cli', 'argparse').
sumd_interface('cli', '').
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

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

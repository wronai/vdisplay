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
- **version**: `0.1.2`
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
  version: 0.1.2;
}

dependencies {
  pillow: Pillow>=10.0;
  dev: "pytest>=8.0, Pillow>=10.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
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
  keys: OPENROUTER_API_KEY, LLM_MODEL, DISPLAY;
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
  version: 0.1.2
  env: local
```

## Dependencies

### Runtime

*(see pyproject.toml)*

### Development

```text markpact:deps python scope=dev
pytest>=8.0
Pillow>=10.0
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
# vdisplay | 54f 3843L | python:49,shell:4,less:1 | 2026-06-09
# stats: 133 func | 18 cls | 54 mod | CC̄=4.8 | critical:16 | cycles:0
# alerts[5]: CC parse_line=40; CC _is_internal_window=30; CC find_windows=28; CC main=21; CC _dedupe_app_windows=18
# hotspots[5]: main fan=21; main fan=16; create_app fan=16; main fan=15; dispatch fan=13
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[54]:
  app.doql.less,45
  examples/ci-agent/agent.py,44
  examples/headless-virtual/run_virtual.py,35
  examples/host-mirror/mirror_demo.py,56
  examples/host-mirror/run.sh,54
  examples/host-relay/relay_demo.py,39
  examples/host-relay/run.sh,48
  packages/cli2vdisplay/src/cli2vdisplay/cli.py,35
  packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py,5
  packages/dsl2vdisplay/src/dsl2vdisplay/bus.py,76
  packages/dsl2vdisplay/src/dsl2vdisplay/cli.py,71
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py,121
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py,2
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py,97
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py,98
  packages/dsl2vdisplay/src/dsl2vdisplay/result.py,27
  packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py,39
  packages/dsl2vdisplay/tests/test_parity.py,15
  packages/mcp2vdisplay/src/mcp2vdisplay/cli.py,24
  packages/mcp2vdisplay/src/mcp2vdisplay/server.py,38
  packages/nlp2vdisplay/src/nlp2vdisplay/cli.py,31
  packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py,25
  packages/rest2vdisplay/src/rest2vdisplay/app.py,47
  packages/rest2vdisplay/src/rest2vdisplay/cli.py,25
  packages/uri2vdisplay/src/uri2vdisplay/cli.py,31
  packages/uri2vdisplay/src/uri2vdisplay/decode.py,32
  project.sh,59
  src/vdisplay/__init__.py,13
  src/vdisplay/api.py,185
  src/vdisplay/backends/__init__.py,2
  src/vdisplay/backends/base.py,62
  src/vdisplay/backends/linux_x11_mirror.py,227
  src/vdisplay/backends/linux_x11_relay.py,311
  src/vdisplay/backends/linux_xvfb.py,164
  src/vdisplay/backends/mirror_stub.py,35
  src/vdisplay/capture/__init__.py,4
  src/vdisplay/capture/base.py,10
  src/vdisplay/capture/linux_xwd.py,209
  src/vdisplay/cli.py,241
  src/vdisplay/discovery.py,267
  src/vdisplay/exceptions.py,11
  src/vdisplay/input/__init__.py,4
  src/vdisplay/input/linux_xdotool.py,46
  src/vdisplay/models.py,27
  src/vdisplay/utils.py,47
  src/vdisplay/windows.py,514
  tests/test_capture_xwd.py,46
  tests/test_import.py,23
  tests/test_linux_xvfb_integration.py,22
  tests/test_mirror_primary.py,43
  tests/test_outputs_rotation.py,35
  tests/test_windows.py,48
  tests/test_windows_dedupe.py,26
  tree.sh,2
D:
  examples/ci-agent/agent.py:
    e: main
    main()
  examples/headless-virtual/run_virtual.py:
    e: main
    main()
  examples/host-mirror/mirror_demo.py:
    e: main
    main()
  examples/host-relay/relay_demo.py:
    e: main
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
    e: split_command,pick_flag,parse_line,to_text
    split_command(line)
    pick_flag(tokens;flag)
    parse_line(line)
    to_text(cmd)
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py:
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py:
    e: handle_screenshot,handle_virtual_start,handle_mirror,handle_adopt,handle_release
    handle_screenshot(cmd)
    handle_virtual_start(cmd)
    handle_mirror(cmd)
    handle_adopt(cmd)
    handle_release(cmd)
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py:
    e: handle_health,handle_info,handle_outputs,handle_windows,handle_capabilities,handle_validate
    handle_health(cmd)
    handle_info(cmd)
    handle_outputs(cmd)
    handle_windows(cmd)
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
    e: nl_to_dsl
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
  src/vdisplay/__init__.py:
  src/vdisplay/api.py:
    e: _default_virtual_backend,_default_mirror_backend,_default_relay_backend,platform_summary,VirtualDisplaySession,MirrorSession,WindowRelaySession
    VirtualDisplaySession: __init__(1),create(5),start(0),stop(0),launch(1),screenshot_bytes(0),save_screenshot(1),adopt_window(0),release_window(0),info(0),capabilities(0)
    MirrorSession: __init__(1),create(5),start(0),stop(0),screenshot_bytes(0),save_screenshot(1),info(0),capabilities(0)
    WindowRelaySession: __init__(1),create(3),start(0),stop(0),adopt_window(0),release_window(0),list_adopted(0),info(0),capabilities(0)
    _default_virtual_backend()
    _default_mirror_backend()
    _default_relay_backend()
    platform_summary()
  src/vdisplay/backends/__init__.py:
  src/vdisplay/backends/base.py:
    e: BaseBackend
    BaseBackend: __init__(0),capabilities(0),info(0),start(0),stop(0),launch(1),screenshot_bytes(0),save_screenshot(1),adopt_window(0),release_window(0),as_dict(0)
  src/vdisplay/backends/linux_x11_mirror.py:
    e: _list_connected_outputs,_resolve_output,_primary_output_from_xrandr,_output_capture_region,_mirror_target_candidates,_output_mode,LinuxX11MirrorBackend
    LinuxX11MirrorBackend: __init__(3),capabilities(0),info(0),start(0),stop(0),screenshot_bytes(0)
    _list_connected_outputs(display)
    _resolve_output(name;outputs;display)
    _primary_output_from_xrandr(display)
    _output_capture_region(display;output_name)
    _mirror_target_candidates(display;source;outputs)
    _output_mode(display;output)
  src/vdisplay/backends/linux_x11_relay.py:
    e: _find_window_id,_move_window,_window_metadata,_window_geometry,_window_title,_offscreen_coordinates,_screen_geometry,_output_origin,WindowState,LinuxX11RelayBackend
    WindowState:
    LinuxX11RelayBackend: __init__(2),capabilities(0),info(0),start(0),adopt_window(0),release_window(0),list_adopted(0)  # Move windows between monitors/outputs within the same X11 se
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
  src/vdisplay/capture/linux_xwd.py:
    e: capture_display_png,_capture_xwd_png,_capture_scrot_png,xwd_bytes_to_png,_xwd_dimensions,_xwd_to_rgb_bytes,_parse_xwd_header,_read_xwd_header,_header_fields,_decode_pixels,_rgb_to_png,_rgb_to_png_minimal
    capture_display_png(display)
    _capture_xwd_png(display)
    _capture_scrot_png(display;region)
    xwd_bytes_to_png(data)
    _xwd_dimensions(data)
    _xwd_to_rgb_bytes(data)
    _parse_xwd_header(data)
    _read_xwd_header(stream)
    _header_fields(fields)
    _decode_pixels(header;pixels)
    _rgb_to_png(rgb;width;height)
    _rgb_to_png_minimal(rgb;width;height)
  src/vdisplay/cli.py:
    e: build_parser,_print_json,main
    build_parser()
    _print_json(payload)
    main(argv)
  src/vdisplay/discovery.py:
    e: resolve_host_display,_looks_like_xvfb_only,list_outputs,_list_monitors,_parse_xrandr_query,_merge_output_metadata,list_windows,find_window_suggestions,diagnose_display,_display_hint
    resolve_host_display(preferred)
    _looks_like_xvfb_only(display)
    list_outputs(display)
    _list_monitors(display)
    _parse_xrandr_query(display)
    _merge_output_metadata(monitors;query_meta)
    list_windows(display)
    find_window_suggestions(display;match_title;limit)
    diagnose_display(display)
    _display_hint(display;resolved;outputs)
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
  src/vdisplay/utils.py:
    e: require_command,run_command,run_command_bytes
    require_command(name)
    run_command(args)
    run_command_bytes(args)
  src/vdisplay/windows.py:
    e: list_windows_enriched,_dedupe_app_windows,find_companion_frames,inspect_window,find_windows,pick_best_window,_derive_app_label,_derive_role,_is_internal_window,_looks_like_internal_class,_looks_like_internal_name,_matches_title,_matches_class,_matches_app,_window_sort_key,_root_window_id,_xdotool,_xprop,_decode_xprop_value,_parse_wm_class,_normalize_atom_list,_resolve_window_pid,_process_info,_window_geometry,_format_window_id
    list_windows_enriched(display)
    _dedupe_app_windows(windows)
    find_companion_frames(display;window)
    inspect_window(display;window_id)
    find_windows(display)
    pick_best_window(matches)
    _derive_app_label()
    _derive_role()
    _is_internal_window()
    _looks_like_internal_class(value)
    _looks_like_internal_name(value)
    _matches_title(info;needle)
    _matches_class(info;needle)
    _matches_app(info;needle)
    _window_sort_key(info)
    _root_window_id(display)
    _xdotool(display)
    _xprop(display;window_id)
    _decode_xprop_value(raw)
    _parse_wm_class(raw)
    _normalize_atom_list(raw)
    _resolve_window_pid(display;window_id;props)
    _process_info(pid)
    _window_geometry(display;window_id)
    _format_window_id(window_id)
  tests/test_capture_xwd.py:
    e: _make_xwd,test_xwd_to_png_red_pixel,test_xwd_to_png_2x1
    _make_xwd(width;height;pixels)
    test_xwd_to_png_red_pixel()
    test_xwd_to_png_2x1()
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
  tests/test_outputs_rotation.py:
    e: test_rotation_degrees_mapping,test_parse_xrandr_query_rotation_from_sample
    test_rotation_degrees_mapping()
    test_parse_xrandr_query_rotation_from_sample()
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
project_metadata('vdisplay', '0.1.2', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 45, 'less').
project_file('examples/ci-agent/agent.py', 44, 'python').
project_file('examples/headless-virtual/run_virtual.py', 35, 'python').
project_file('examples/host-mirror/mirror_demo.py', 56, 'python').
project_file('examples/host-mirror/run.sh', 54, 'shell').
project_file('examples/host-relay/relay_demo.py', 39, 'python').
project_file('examples/host-relay/run.sh', 48, 'shell').
project_file('packages/cli2vdisplay/src/cli2vdisplay/cli.py', 35, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py', 5, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 76, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', 71, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 121, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py', 2, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 97, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 98, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/result.py', 27, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py', 39, 'python').
project_file('packages/dsl2vdisplay/tests/test_parity.py', 15, 'python').
project_file('packages/mcp2vdisplay/src/mcp2vdisplay/cli.py', 24, 'python').
project_file('packages/mcp2vdisplay/src/mcp2vdisplay/server.py', 38, 'python').
project_file('packages/nlp2vdisplay/src/nlp2vdisplay/cli.py', 31, 'python').
project_file('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 25, 'python').
project_file('packages/rest2vdisplay/src/rest2vdisplay/app.py', 47, 'python').
project_file('packages/rest2vdisplay/src/rest2vdisplay/cli.py', 25, 'python').
project_file('packages/uri2vdisplay/src/uri2vdisplay/cli.py', 31, 'python').
project_file('packages/uri2vdisplay/src/uri2vdisplay/decode.py', 32, 'python').
project_file('project.sh', 59, 'shell').
project_file('src/vdisplay/__init__.py', 13, 'python').
project_file('src/vdisplay/api.py', 185, 'python').
project_file('src/vdisplay/backends/__init__.py', 2, 'python').
project_file('src/vdisplay/backends/base.py', 62, 'python').
project_file('src/vdisplay/backends/linux_x11_mirror.py', 227, 'python').
project_file('src/vdisplay/backends/linux_x11_relay.py', 311, 'python').
project_file('src/vdisplay/backends/linux_xvfb.py', 164, 'python').
project_file('src/vdisplay/backends/mirror_stub.py', 35, 'python').
project_file('src/vdisplay/capture/__init__.py', 4, 'python').
project_file('src/vdisplay/capture/base.py', 10, 'python').
project_file('src/vdisplay/capture/linux_xwd.py', 209, 'python').
project_file('src/vdisplay/cli.py', 241, 'python').
project_file('src/vdisplay/discovery.py', 267, 'python').
project_file('src/vdisplay/exceptions.py', 11, 'python').
project_file('src/vdisplay/input/__init__.py', 4, 'python').
project_file('src/vdisplay/input/linux_xdotool.py', 46, 'python').
project_file('src/vdisplay/models.py', 27, 'python').
project_file('src/vdisplay/utils.py', 47, 'python').
project_file('src/vdisplay/windows.py', 514, 'python').
project_file('tests/test_capture_xwd.py', 46, 'python').
project_file('tests/test_import.py', 23, 'python').
project_file('tests/test_linux_xvfb_integration.py', 22, 'python').
project_file('tests/test_mirror_primary.py', 43, 'python').
project_file('tests/test_outputs_rotation.py', 35, 'python').
project_file('tests/test_windows.py', 48, 'python').
project_file('tests/test_windows_dedupe.py', 26, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('examples/ci-agent/agent.py', 'main', 0, 3, 15).
python_function('examples/headless-virtual/run_virtual.py', 'main', 0, 1, 11).
python_function('examples/host-mirror/mirror_demo.py', 'main', 0, 5, 16).
python_function('examples/host-relay/relay_demo.py', 'main', 0, 1, 10).
python_function('packages/cli2vdisplay/src/cli2vdisplay/cli.py', 'main', 1, 7, 10).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', '_dispatch_query', 1, 2, 6).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', '_dispatch_cmd', 1, 3, 8).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 'dispatch', 1, 8, 13).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 'execute_dsl_line', 1, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', 'main', 1, 4, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', '_main_legacy', 1, 10, 11).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', '_main_subcommand', 1, 9, 13).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'split_command', 1, 4, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'pick_flag', 2, 3, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'parse_line', 1, 40, 7).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'to_text', 1, 7, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_screenshot', 1, 1, 9).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_virtual_start', 1, 1, 7).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_mirror', 1, 3, 11).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_adopt', 1, 1, 9).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 'handle_release', 1, 1, 9).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_health', 1, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_info', 1, 1, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_outputs', 1, 1, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 'handle_windows', 1, 1, 5).
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
python_function('packages/mcp2vdisplay/src/mcp2vdisplay/server.py', 'create_server', 0, 1, 10).
python_function('packages/nlp2vdisplay/src/nlp2vdisplay/cli.py', 'main', 1, 4, 10).
python_function('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 'nl_to_dsl', 1, 15, 4).
python_function('packages/rest2vdisplay/src/rest2vdisplay/app.py', 'create_app', 0, 1, 16).
python_function('packages/rest2vdisplay/src/rest2vdisplay/cli.py', 'main', 0, 2, 7).
python_function('packages/uri2vdisplay/src/uri2vdisplay/cli.py', 'main', 1, 4, 10).
python_function('packages/uri2vdisplay/src/uri2vdisplay/decode.py', 'uri_to_dsl', 1, 7, 10).
python_function('src/vdisplay/api.py', '_default_virtual_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', '_default_mirror_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', '_default_relay_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', 'platform_summary', 0, 1, 5).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_list_connected_outputs', 1, 3, 5).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_resolve_output', 3, 10, 9).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_primary_output_from_xrandr', 1, 3, 4).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_output_capture_region', 2, 5, 3).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_mirror_target_candidates', 3, 7, 1).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_output_mode', 2, 7, 5).
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
python_function('src/vdisplay/capture/linux_xwd.py', 'capture_display_png', 1, 6, 4).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_xwd_png', 1, 1, 3).
python_function('src/vdisplay/capture/linux_xwd.py', '_capture_scrot_png', 2, 2, 7).
python_function('src/vdisplay/capture/linux_xwd.py', 'xwd_bytes_to_png', 1, 1, 3).
python_function('src/vdisplay/capture/linux_xwd.py', '_xwd_dimensions', 1, 1, 1).
python_function('src/vdisplay/capture/linux_xwd.py', '_xwd_to_rgb_bytes', 1, 6, 6).
python_function('src/vdisplay/capture/linux_xwd.py', '_parse_xwd_header', 1, 3, 4).
python_function('src/vdisplay/capture/linux_xwd.py', '_read_xwd_header', 1, 2, 5).
python_function('src/vdisplay/capture/linux_xwd.py', '_header_fields', 1, 1, 0).
python_function('src/vdisplay/capture/linux_xwd.py', '_decode_pixels', 2, 12, 5).
python_function('src/vdisplay/capture/linux_xwd.py', '_rgb_to_png', 3, 2, 5).
python_function('src/vdisplay/capture/linux_xwd.py', '_rgb_to_png_minimal', 3, 2, 7).
python_function('src/vdisplay/cli.py', 'build_parser', 0, 1, 4).
python_function('src/vdisplay/cli.py', '_print_json', 1, 1, 2).
python_function('src/vdisplay/cli.py', 'main', 1, 21, 21).
python_function('src/vdisplay/discovery.py', 'resolve_host_display', 1, 9, 5).
python_function('src/vdisplay/discovery.py', '_looks_like_xvfb_only', 1, 4, 4).
python_function('src/vdisplay/discovery.py', 'list_outputs', 1, 7, 13).
python_function('src/vdisplay/discovery.py', '_list_monitors', 1, 6, 9).
python_function('src/vdisplay/discovery.py', '_parse_xrandr_query', 1, 8, 8).
python_function('src/vdisplay/discovery.py', '_merge_output_metadata', 2, 3, 3).
python_function('src/vdisplay/discovery.py', 'list_windows', 1, 1, 2).
python_function('src/vdisplay/discovery.py', 'find_window_suggestions', 3, 2, 2).
python_function('src/vdisplay/discovery.py', 'diagnose_display', 1, 4, 9).
python_function('src/vdisplay/discovery.py', '_display_hint', 3, 3, 2).
python_function('src/vdisplay/utils.py', 'require_command', 1, 2, 2).
python_function('src/vdisplay/utils.py', 'run_command', 1, 2, 4).
python_function('src/vdisplay/utils.py', 'run_command_bytes', 1, 1, 1).
python_function('src/vdisplay/windows.py', 'list_windows_enriched', 1, 16, 13).
python_function('src/vdisplay/windows.py', '_dedupe_app_windows', 1, 18, 8).
python_function('src/vdisplay/windows.py', 'find_companion_frames', 2, 16, 5).
python_function('src/vdisplay/windows.py', 'inspect_window', 2, 9, 13).
python_function('src/vdisplay/windows.py', 'find_windows', 1, 28, 6).
python_function('src/vdisplay/windows.py', 'pick_best_window', 1, 10, 2).
python_function('src/vdisplay/windows.py', '_derive_app_label', 0, 16, 4).
python_function('src/vdisplay/windows.py', '_derive_role', 0, 10, 3).
python_function('src/vdisplay/windows.py', '_is_internal_window', 0, 30, 3).
python_function('src/vdisplay/windows.py', '_looks_like_internal_class', 1, 3, 2).
python_function('src/vdisplay/windows.py', '_looks_like_internal_name', 1, 3, 2).
python_function('src/vdisplay/windows.py', '_matches_title', 2, 4, 3).
python_function('src/vdisplay/windows.py', '_matches_class', 2, 5, 3).
python_function('src/vdisplay/windows.py', '_matches_app', 2, 5, 3).
python_function('src/vdisplay/windows.py', '_window_sort_key', 1, 5, 1).
python_function('src/vdisplay/windows.py', '_root_window_id', 1, 3, 6).
python_function('src/vdisplay/windows.py', '_xdotool', 1, 1, 1).
python_function('src/vdisplay/windows.py', '_xprop', 2, 5, 8).
python_function('src/vdisplay/windows.py', '_decode_xprop_value', 1, 6, 5).
python_function('src/vdisplay/windows.py', '_parse_wm_class', 1, 7, 4).
python_function('src/vdisplay/windows.py', '_normalize_atom_list', 1, 3, 5).
python_function('src/vdisplay/windows.py', '_resolve_window_pid', 3, 3, 5).
python_function('src/vdisplay/windows.py', '_process_info', 1, 6, 7).
python_function('src/vdisplay/windows.py', '_window_geometry', 2, 4, 5).
python_function('src/vdisplay/windows.py', '_format_window_id', 1, 3, 3).
python_function('tests/test_capture_xwd.py', '_make_xwd', 3, 1, 1).
python_function('tests/test_capture_xwd.py', 'test_xwd_to_png_red_pixel', 0, 2, 3).
python_function('tests/test_capture_xwd.py', 'test_xwd_to_png_2x1', 0, 2, 4).
python_function('tests/test_import.py', 'test_imports', 0, 4, 0).
python_function('tests/test_import.py', 'test_platform_summary', 0, 3, 1).
python_function('tests/test_import.py', 'test_capabilities', 0, 4, 2).
python_function('tests/test_linux_xvfb_integration.py', 'test_virtual_display_screenshot', 1, 3, 9).
python_function('tests/test_mirror_primary.py', 'test_primary_output_from_xrandr', 1, 2, 4).
python_function('tests/test_mirror_primary.py', 'test_mirror_target_candidates_prefers_non_primary', 1, 2, 3).
python_function('tests/test_outputs_rotation.py', 'test_rotation_degrees_mapping', 0, 5, 0).
python_function('tests/test_outputs_rotation.py', 'test_parse_xrandr_query_rotation_from_sample', 0, 7, 3).
python_function('tests/test_windows.py', 'test_parse_wm_class', 0, 3, 1).
python_function('tests/test_windows.py', 'test_derive_app_label_prefers_title', 0, 2, 1).
python_function('tests/test_windows.py', 'test_internal_helper_window', 0, 2, 1).
python_function('tests/test_windows.py', 'test_matches_title_on_app_label', 0, 3, 2).
python_function('tests/test_windows_dedupe.py', 'test_dedupe_prefers_application_over_mutter_frame', 0, 3, 2).

% ── Python Classes ───────────────────────────────────────
python_class('packages/dsl2vdisplay/src/dsl2vdisplay/result.py', 'DslResult').
python_method('DslResult', 'to_dict', 0, 1, 0).
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
python_method('LinuxX11MirrorBackend', 'start', 0, 15, 11).
python_method('LinuxX11MirrorBackend', 'stop', 0, 5, 1).
python_method('LinuxX11MirrorBackend', 'screenshot_bytes', 0, 2, 3).
python_class('src/vdisplay/backends/linux_x11_relay.py', 'WindowState').
python_class('src/vdisplay/backends/linux_x11_relay.py', 'LinuxX11RelayBackend').
python_method('LinuxX11RelayBackend', '__init__', 2, 1, 3).
python_method('LinuxX11RelayBackend', 'capabilities', 0, 1, 1).
python_method('LinuxX11RelayBackend', 'info', 0, 1, 2).
python_method('LinuxX11RelayBackend', 'start', 0, 2, 2).
python_method('LinuxX11RelayBackend', 'adopt_window', 0, 12, 12).
python_method('LinuxX11RelayBackend', 'release_window', 0, 10, 8).
python_method('LinuxX11RelayBackend', 'list_adopted', 0, 2, 1).
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

*121 nodes · 148 edges · 26 modules · CC̄=3.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `build_parser` *(in src.vdisplay.cli)* | 1 | 1 | 61 | **62** |
| `main` *(in src.vdisplay.cli)* | 21 ⚠ | 0 | 55 | **55** |
| `parse_line` *(in packages.dsl2vdisplay.src.dsl2vdisplay.grammar)* | 40 ⚠ | 2 | 36 | **38** |
| `list_outputs` *(in src.vdisplay.discovery)* | 7 | 6 | 25 | **31** |
| `run_command` *(in src.vdisplay.utils)* | 2 | 27 | 4 | **31** |
| `dispatch` *(in packages.dsl2vdisplay.src.dsl2vdisplay.bus)* | 8 | 9 | 19 | **28** |
| `create_app` *(in packages.rest2vdisplay.src.rest2vdisplay.app)* | 1 | 1 | 27 | **28** |
| `adopt_window` *(in src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend)* | 12 ⚠ | 0 | 26 | **26** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/vdisplay
# generated in 0.06s
# nodes: 121 | edges: 148 | modules: 26
# CC̄=3.8

HUBS[20]:
  src.vdisplay.cli.build_parser
    CC=1  in:1  out:61  total:62
  src.vdisplay.cli.main
    CC=21  in:0  out:55  total:55
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line
    CC=40  in:2  out:36  total:38
  src.vdisplay.discovery.list_outputs
    CC=7  in:6  out:25  total:31
  src.vdisplay.utils.run_command
    CC=2  in:27  out:4  total:31
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=8  in:9  out:19  total:28
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=1  in:1  out:27  total:28
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window
    CC=12  in:0  out:26  total:26
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
    CC=3  in:24  out:2  total:26
  src.vdisplay.windows._dedupe_app_windows
    CC=18  in:1  out:22  total:23
  examples.host-mirror.mirror_demo.main
    CC=5  in:0  out:23  total:23
  src.vdisplay.windows.inspect_window
    CC=9  in:2  out:20  total:22
  src.vdisplay.windows.list_windows_enriched
    CC=16  in:4  out:17  total:21
  src.vdisplay.windows.find_companion_frames
    CC=16  in:1  out:20  total:21
  src.vdisplay.backends.linux_x11_relay._output_origin
    CC=11  in:1  out:20  total:21
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand
    CC=9  in:1  out:19  total:20
  src.vdisplay.discovery._merge_output_metadata
    CC=3  in:1  out:18  total:19
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy
    CC=10  in:1  out:17  total:18
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command.handle_mirror
    CC=3  in:0  out:16  total:16
  src.vdisplay.discovery.resolve_host_display
    CC=9  in:10  out:6  total:16

MODULES:
  examples.host-mirror.mirror_demo  [1 funcs]
    main  CC=5  out:23
  packages.cli2vdisplay.src.cli2vdisplay.cli  [1 funcs]
    main  CC=7  out:16
  packages.dsl2vdisplay.src.dsl2vdisplay.bus  [4 funcs]
    _dispatch_cmd  CC=3  out:11
    _dispatch_query  CC=2  out:7
    dispatch  CC=8  out:19
    execute_dsl_line  CC=1  out:1
  packages.dsl2vdisplay.src.dsl2vdisplay.cli  [3 funcs]
    _main_legacy  CC=10  out:17
    _main_subcommand  CC=9  out:19
    main  CC=4  out:3
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar  [4 funcs]
    parse_line  CC=40  out:36
    pick_flag  CC=3  out:2
    split_command  CC=4  out:4
    to_text  CC=7  out:12
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.command  [3 funcs]
    handle_adopt  CC=1  out:12
    handle_mirror  CC=3  out:16
    handle_release  CC=1  out:11
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query  [4 funcs]
    handle_info  CC=1  out:9
    handle_outputs  CC=1  out:5
    handle_validate  CC=4  out:10
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
    create_server  CC=1  out:14
  packages.nlp2vdisplay.src.nlp2vdisplay.cli  [1 funcs]
    main  CC=4  out:13
  packages.nlp2vdisplay.src.nlp2vdisplay.to_dsl  [1 funcs]
    nl_to_dsl  CC=15  out:4
  packages.rest2vdisplay.src.rest2vdisplay.app  [1 funcs]
    create_app  CC=1  out:27
  packages.rest2vdisplay.src.rest2vdisplay.cli  [1 funcs]
    main  CC=2  out:8
  packages.uri2vdisplay.src.uri2vdisplay.cli  [1 funcs]
    main  CC=4  out:13
  packages.uri2vdisplay.src.uri2vdisplay.decode  [1 funcs]
    uri_to_dsl  CC=7  out:12
  src.vdisplay.api  [7 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.backends.linux_x11_mirror  [9 funcs]
    __init__  CC=1  out:4
    screenshot_bytes  CC=2  out:2
    start  CC=15  out:16
    stop  CC=5  out:3
    _list_connected_outputs  CC=3  out:5
    _mirror_target_candidates  CC=7  out:1
    _output_mode  CC=7  out:6
    _primary_output_from_xrandr  CC=3  out:4
    _resolve_output  CC=10  out:13
  src.vdisplay.backends.linux_x11_relay  [11 funcs]
    __init__  CC=1  out:3
    adopt_window  CC=12  out:26
    release_window  CC=10  out:15
    _find_window_id  CC=12  out:11
    _move_window  CC=1  out:3
    _offscreen_coordinates  CC=1  out:1
    _output_origin  CC=11  out:20
    _screen_geometry  CC=2  out:7
    _window_geometry  CC=4  out:4
    _window_metadata  CC=1  out:1
  src.vdisplay.backends.linux_xvfb  [7 funcs]
    _acquire_display  CC=8  out:14
    screenshot_bytes  CC=2  out:2
    start  CC=4  out:6
    _display_candidates  CC=4  out:4
    _display_socket_exists  CC=1  out:3
    _probe_display  CC=2  out:2
    _wait_for_display  CC=7  out:10
  src.vdisplay.capture.linux_xwd  [10 funcs]
    _decode_pixels  CC=12  out:7
    _header_fields  CC=1  out:0
    _parse_xwd_header  CC=3  out:5
    _read_xwd_header  CC=2  out:5
    _rgb_to_png  CC=2  out:5
    _rgb_to_png_minimal  CC=2  out:11
    _xwd_dimensions  CC=1  out:1
    _xwd_to_rgb_bytes  CC=6  out:9
    capture_display_png  CC=1  out:3
    xwd_bytes_to_png  CC=1  out:3
  src.vdisplay.cli  [3 funcs]
    _print_json  CC=1  out:2
    build_parser  CC=1  out:61
    main  CC=21  out:55
  src.vdisplay.discovery  [10 funcs]
    _display_hint  CC=3  out:2
    _list_monitors  CC=6  out:10
    _looks_like_xvfb_only  CC=4  out:4
    _merge_output_metadata  CC=3  out:18
    _parse_xrandr_query  CC=8  out:12
    diagnose_display  CC=4  out:10
    find_window_suggestions  CC=2  out:2
    list_outputs  CC=7  out:25
    list_windows  CC=1  out:2
    resolve_host_display  CC=9  out:6
  src.vdisplay.input.linux_xdotool  [4 funcs]
    click  CC=1  out:4
    hotkey  CC=1  out:3
    move  CC=1  out:5
    type_text  CC=1  out:3
  src.vdisplay.utils  [3 funcs]
    require_command  CC=2  out:2
    run_command  CC=2  out:4
    run_command_bytes  CC=1  out:1
  src.vdisplay.windows  [24 funcs]
    _decode_xprop_value  CC=6  out:6
    _dedupe_app_windows  CC=18  out:22
    _derive_app_label  CC=16  out:5
    _derive_role  CC=10  out:3
    _format_window_id  CC=3  out:3
    _is_internal_window  CC=30  out:5
    _looks_like_internal_class  CC=3  out:2
    _looks_like_internal_name  CC=3  out:2
    _matches_app  CC=5  out:4
    _matches_class  CC=5  out:4

EDGES:
  src.vdisplay.utils.run_command_bytes → src.vdisplay.utils.run_command
  src.vdisplay.capture.linux_xwd.capture_display_png → src.vdisplay.utils.require_command
  src.vdisplay.capture.linux_xwd.capture_display_png → src.vdisplay.utils.run_command_bytes
  src.vdisplay.capture.linux_xwd.capture_display_png → src.vdisplay.capture.linux_xwd.xwd_bytes_to_png
  src.vdisplay.capture.linux_xwd.xwd_bytes_to_png → src.vdisplay.capture.linux_xwd._xwd_to_rgb_bytes
  src.vdisplay.capture.linux_xwd.xwd_bytes_to_png → src.vdisplay.capture.linux_xwd._xwd_dimensions
  src.vdisplay.capture.linux_xwd.xwd_bytes_to_png → src.vdisplay.capture.linux_xwd._rgb_to_png
  src.vdisplay.capture.linux_xwd._xwd_dimensions → src.vdisplay.capture.linux_xwd._parse_xwd_header
  src.vdisplay.capture.linux_xwd._xwd_to_rgb_bytes → src.vdisplay.capture.linux_xwd._read_xwd_header
  src.vdisplay.capture.linux_xwd._xwd_to_rgb_bytes → src.vdisplay.capture.linux_xwd._decode_pixels
  src.vdisplay.capture.linux_xwd._parse_xwd_header → src.vdisplay.capture.linux_xwd._header_fields
  src.vdisplay.capture.linux_xwd._read_xwd_header → src.vdisplay.capture.linux_xwd._header_fields
  src.vdisplay.capture.linux_xwd._rgb_to_png → src.vdisplay.capture.linux_xwd._rgb_to_png_minimal
  src.vdisplay.input.linux_xdotool.LinuxXdotoolInput.move → src.vdisplay.utils.require_command
  src.vdisplay.input.linux_xdotool.LinuxXdotoolInput.move → src.vdisplay.utils.run_command
  src.vdisplay.input.linux_xdotool.LinuxXdotoolInput.click → src.vdisplay.utils.require_command
  src.vdisplay.input.linux_xdotool.LinuxXdotoolInput.click → src.vdisplay.utils.run_command
  src.vdisplay.input.linux_xdotool.LinuxXdotoolInput.type_text → src.vdisplay.utils.require_command
  src.vdisplay.input.linux_xdotool.LinuxXdotoolInput.type_text → src.vdisplay.utils.run_command
  src.vdisplay.input.linux_xdotool.LinuxXdotoolInput.hotkey → src.vdisplay.utils.require_command
  src.vdisplay.input.linux_xdotool.LinuxXdotoolInput.hotkey → src.vdisplay.utils.run_command
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_info → src.vdisplay.api.platform_summary
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_outputs → src.vdisplay.discovery.diagnose_display
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_outputs → src.vdisplay.discovery.list_outputs
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_windows → src.vdisplay.discovery.list_windows
  packages.dsl2vdisplay.src.dsl2vdisplay.handlers.query.handle_validate → src.vdisplay.discovery.diagnose_display
  packages.nlp2vdisplay.src.nlp2vdisplay.cli.main → packages.nlp2vdisplay.src.nlp2vdisplay.to_dsl.nl_to_dsl
  packages.nlp2vdisplay.src.nlp2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.mcp2vdisplay.src.mcp2vdisplay.cli.main → packages.mcp2vdisplay.src.mcp2vdisplay.cli.create_server
  packages.cli2vdisplay.src.cli2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server → packages.nlp2vdisplay.src.nlp2vdisplay.to_dsl.nl_to_dsl
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  examples.host-mirror.mirror_demo.main → src.vdisplay.discovery.diagnose_display
  examples.host-mirror.mirror_demo.main → src.vdisplay.discovery.list_outputs
  packages.dsl2vdisplay.src.dsl2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy
  packages.dsl2vdisplay.src.dsl2vdisplay.cli.main → packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_legacy → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line
  packages.dsl2vdisplay.src.dsl2vdisplay.cli._main_subcommand → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.all_schemas
  packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_cmd → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.validate_command_dict
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_query
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.bus._dispatch_cmd
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.parse_line
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch → packages.dsl2vdisplay.src.dsl2vdisplay.grammar.to_text
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.execute_dsl_line → packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app → packages.dsl2vdisplay.src.dsl2vdisplay.schema_registry.schema_for_verb
  src.vdisplay.api.VirtualDisplaySession.create → src.vdisplay.api._default_virtual_backend
  src.vdisplay.api.MirrorSession.create → src.vdisplay.api._default_mirror_backend
  src.vdisplay.api.WindowRelaySession.create → src.vdisplay.api._default_relay_backend
  src.vdisplay.api.platform_summary → src.vdisplay.api._default_virtual_backend
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

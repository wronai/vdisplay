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
- **version**: `0.1.2`
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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

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

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 72f 5026L | python:41,toml:7,json:6,yml:5,shell:4,yaml:4 | 2026-06-09
# generated in 0.01s
# CC̅=3.8 | critical:10/188 | dups:0 | cycles:0

HEALTH[10]:
  🟡 CC    nl_to_dsl CC=15 (limit:15)
  🟡 CC    main CC=21 (limit:15)
  🟡 CC    start CC=15 (limit:15)
  🟡 CC    list_windows_enriched CC=16 (limit:15)
  🟡 CC    _dedupe_app_windows CC=18 (limit:15)
  🟡 CC    find_companion_frames CC=16 (limit:15)
  🟡 CC    find_windows CC=28 (limit:15)
  🟡 CC    _derive_app_label CC=16 (limit:15)
  🟡 CC    _is_internal_window CC=30 (limit:15)
  🟡 CC    parse_line CC=40 (limit:15)

REFACTOR[1]:
  1. split 10 high-CC methods  (CC>15)

PIPELINES[89]:
  [1] Src [__init__]: __init__
      PURITY: 100% pure
  [2] Src [capabilities]: capabilities
      PURITY: 100% pure
  [3] Src [info]: info
      PURITY: 100% pure
  [4] Src [move]: move → require_command
      PURITY: 100% pure
  [5] Src [click]: click → require_command
      PURITY: 100% pure
  [6] Src [type_text]: type_text → require_command
      PURITY: 100% pure
  [7] Src [hotkey]: hotkey → require_command
      PURITY: 100% pure
  [8] Src [handle_health]: handle_health
      PURITY: 100% pure
  [9] Src [handle_info]: handle_info → platform_summary → _default_virtual_backend
      PURITY: 100% pure
  [10] Src [handle_outputs]: handle_outputs → diagnose_display → resolve_host_display → _looks_like_xvfb_only
      PURITY: 100% pure
  [11] Src [handle_windows]: handle_windows → list_windows → resolve_host_display → _looks_like_xvfb_only
      PURITY: 100% pure
  [12] Src [handle_capabilities]: handle_capabilities
      PURITY: 100% pure
  [13] Src [handle_validate]: handle_validate → diagnose_display → resolve_host_display → _looks_like_xvfb_only
      PURITY: 100% pure
  [14] Src [main]: main → nl_to_dsl
      PURITY: 100% pure
  [15] Src [main]: main → create_server
      PURITY: 100% pure
  [16] Src [main]: main
      PURITY: 100% pure
  [17] Src [main]: main → dispatch → _dispatch_query
      PURITY: 100% pure
  [18] Src [create_server]: create_server → nl_to_dsl
      PURITY: 100% pure
  [19] Src [main]: main → diagnose_display → resolve_host_display → _looks_like_xvfb_only
      PURITY: 100% pure
  [20] Src [main]: main → _main_legacy → execute_dsl_line → dispatch → ...(1 more)
      PURITY: 100% pure
  [21] Src [main]: main
      PURITY: 100% pure
  [22] Src [main]: main
      PURITY: 100% pure
  [23] Src [capabilities]: capabilities
      PURITY: 100% pure
  [24] Src [info]: info
      PURITY: 100% pure
  [25] Src [launch]: launch
      PURITY: 100% pure
  [26] Src [screenshot_bytes]: screenshot_bytes
      PURITY: 100% pure
  [27] Src [save_screenshot]: save_screenshot
      PURITY: 100% pure
  [28] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [29] Src [release_window]: release_window
      PURITY: 100% pure
  [30] Src [as_dict]: as_dict
      PURITY: 100% pure
  [31] Src [create]: create → _default_virtual_backend
      PURITY: 100% pure
  [32] Src [start]: start
      PURITY: 100% pure
  [33] Src [stop]: stop
      PURITY: 100% pure
  [34] Src [launch]: launch
      PURITY: 100% pure
  [35] Src [screenshot_bytes]: screenshot_bytes
      PURITY: 100% pure
  [36] Src [save_screenshot]: save_screenshot
      PURITY: 100% pure
  [37] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [38] Src [release_window]: release_window
      PURITY: 100% pure
  [39] Src [info]: info
      PURITY: 100% pure
  [40] Src [capabilities]: capabilities
      PURITY: 100% pure
  [41] Src [__init__]: __init__
      PURITY: 100% pure
  [42] Src [create]: create → _default_mirror_backend
      PURITY: 100% pure
  [43] Src [start]: start
      PURITY: 100% pure
  [44] Src [stop]: stop
      PURITY: 100% pure
  [45] Src [screenshot_bytes]: screenshot_bytes
      PURITY: 100% pure
  [46] Src [save_screenshot]: save_screenshot
      PURITY: 100% pure
  [47] Src [info]: info
      PURITY: 100% pure
  [48] Src [capabilities]: capabilities
      PURITY: 100% pure
  [49] Src [create]: create → _default_relay_backend
      PURITY: 100% pure
  [50] Src [start]: start
      PURITY: 100% pure

LAYERS:
  packages/                       CC̄=4.3    ←in:0  →out:0
  │ !! grammar                    120L  0C    4m  CC=40     ←1
  │ query                       97L  0C    6m  CC=4      ←0
  │ command                     96L  0C    5m  CC=3      ←0
  │ bus                         75L  0C    4m  CC=8      ←6
  │ cli                         70L  0C    3m  CC=10     ←0
  │ app                         46L  0C    1m  CC=1      ←1
  │ schema_registry             38L  0C    4m  CC=3      ←3
  │ server                      37L  0C    1m  CC=1      ←0
  │ cli                         34L  0C    1m  CC=7      ←0
  │ decode                      31L  0C    1m  CC=7      ←1
  │ cli                         30L  0C    1m  CC=4      ←0
  │ cli                         30L  0C    1m  CC=4      ←0
  │ pyproject.toml              28L  0C    0m  CC=0.0    ←0
  │ result                      26L  1C    1m  CC=1      ←0
  │ !! to_dsl                      24L  0C    1m  CC=15     ←2
  │ cli                         24L  0C    1m  CC=2      ←0
  │ cli                         23L  0C    2m  CC=2      ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ mirror.schema.json          13L  0C    0m  CC=0.0    ←0
  │ screenshot.schema.json      13L  0C    0m  CC=0.0    ←0
  │ outputs.schema.json         10L  0C    0m  CC=0.0    ←0
  │ info.schema.json            10L  0C    0m  CC=0.0    ←0
  │ validate.schema.json        10L  0C    0m  CC=0.0    ←0
  │ health.schema.json           9L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  src/                            CC̄=3.8    ←in:0  →out:0
  │ !! windows                    513L  0C   25m  CC=30     ←2
  │ linux_x11_relay            310L  2C   15m  CC=12     ←0
  │ discovery                  266L  0C   10m  CC=9      ←6
  │ !! cli                        240L  0C    3m  CC=21     ←0
  │ !! linux_x11_mirror           208L  1C   11m  CC=15     ←0
  │ api                        184L  3C   32m  CC=6      ←2
  │ linux_xwd                  164L  0C   10m  CC=12     ←2
  │ linux_xvfb                 163L  1C   14m  CC=8      ←0
  │ base                        61L  1C   11m  CC=1      ←0
  │ utils                       46L  0C    3m  CC=2      ←6
  │ linux_xdotool               45L  1C    6m  CC=2      ←0
  │ mirror_stub                 34L  1C    4m  CC=1      ←0
  │ models                      26L  2C    0m  CC=0.0    ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ exceptions                  10L  3C    0m  CC=0.0    ←0
  │ base                         9L  1C    1m  CC=1      ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=1.7    ←in:0  →out:0
  │ mirror_demo                 55L  0C    1m  CC=5      ←0
  │ run.sh                      53L  0C    1m  CC=0.0    ←0
  │ run.sh                      47L  0C    1m  CC=0.0    ←0
  │ agent                       43L  0C    1m  CC=3      ←0
  │ relay_demo                  38L  0C    1m  CC=1      ←0
  │ run_virtual                 34L  0C    1m  CC=1      ←0
  │ Dockerfile                  26L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  25L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  23L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  23L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  19L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          16L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          14L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          14L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          12L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          11L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml              539L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              65L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                           packages.dsl2vdisplay            src.vdisplay  packages.rest2vdisplay   packages.mcp2vdisplay    examples.host-mirror   packages.cli2vdisplay   packages.nlp2vdisplay   packages.uri2vdisplay
   packages.dsl2vdisplay                      ──                       9                      ←4                      ←2                                              ←2                      ←1                      ←1  hub
            src.vdisplay                      ←9                      ──                                                                      ←2                                                                          hub
  packages.rest2vdisplay                       4                                              ──                                                                                                                        
   packages.mcp2vdisplay                       2                                                                      ──                                                                       1                        
    examples.host-mirror                                               2                                                                      ──                                                                        
   packages.cli2vdisplay                       2                                                                                                                      ──                                                
   packages.nlp2vdisplay                       1                                                                      ←1                                                                      ──                        
   packages.uri2vdisplay                       1                                                                                                                                                                      ──
  CYCLES: none
  HUB: packages.dsl2vdisplay/ (fan-in=10)
  HUB: src.vdisplay/ (fan-in=11)
  SMELL: packages.dsl2vdisplay/ fan-out=9 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 3 groups | 41f 3274L | 2026-06-09

SUMMARY:
  files_scanned: 41
  total_lines:   3274
  dup_groups:    3
  dup_fragments: 7
  saved_lines:   15
  scan_ms:       2213

HOTSPOTS[4] (files with most duplication):
  src/vdisplay/api.py  dup=12L  groups=1  frags=3  (0.4%)
  src/vdisplay/windows.py  dup=6L  groups=1  frags=2  (0.2%)
  src/vdisplay/backends/linux_x11_mirror.py  dup=4L  groups=1  frags=1  (0.1%)
  src/vdisplay/backends/linux_xvfb.py  dup=4L  groups=1  frags=1  (0.1%)

DUPLICATES[3] (ranked by impact):
  [b8e2782d68a777c3]   STRU  _default_virtual_backend  L=4 N=3 saved=8 sim=1.00
      src/vdisplay/api.py:13-16  (_default_virtual_backend)
      src/vdisplay/api.py:19-22  (_default_mirror_backend)
      src/vdisplay/api.py:25-28  (_default_relay_backend)
  [3d902e6f1c31b63f]   STRU  screenshot_bytes  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/backends/linux_x11_mirror.py:129-132  (screenshot_bytes)
      src/vdisplay/backends/linux_xvfb.py:78-81  (screenshot_bytes)
  [f5bfacfda8981cef]   STRU  _looks_like_internal_class  L=3 N=2 saved=3 sim=1.00
      src/vdisplay/windows.py:332-334  (_looks_like_internal_class)
      src/vdisplay/windows.py:337-339  (_looks_like_internal_name)

REFACTOR[3] (ranked by priority):
  [1] ○ extract_function   → src/vdisplay/utils/_default_virtual_backend.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/api.py
  [2] ○ extract_function   → src/vdisplay/backends/utils/screenshot_bytes.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/backends/linux_x11_mirror.py, src/vdisplay/backends/linux_xvfb.py
  [3] ○ extract_function   → src/vdisplay/utils/_looks_like_internal_class.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/vdisplay/windows.py

QUICK_WINS[1] (low risk, high savings — do first):
  [1] extract_function   saved=8L  → src/vdisplay/utils/_default_virtual_backend.py
      FILES: api.py

EFFORT_ESTIMATE (total ≈ 0.5h):
  easy   _default_virtual_backend            saved=8L  ~16min
  easy   screenshot_bytes                    saved=4L  ~8min
  easy   _looks_like_internal_class          saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  3 → 0
  saved_lines: 15 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 182 func | 29f | 2026-06-09
# generated in 0.00s

NEXT[10] (ranked by impact):
  [1] !! SPLIT           src/vdisplay/windows.py
      WHY: 513L, 0 classes, max CC=30
      EFFORT: ~4h  IMPACT: 15390

  [2] !  SPLIT-FUNC      main  CC=21  fan=24
      WHY: CC=21 exceeds 15
      EFFORT: ~1h  IMPACT: 504

  [3] !! SPLIT-FUNC      parse_line  CC=40  fan=7
      WHY: CC=40 exceeds 15
      EFFORT: ~1h  IMPACT: 280

  [4] !  SPLIT-FUNC      list_windows_enriched  CC=16  fan=14
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 224

  [5] !  SPLIT-FUNC      _dedupe_app_windows  CC=18  fan=10
      WHY: CC=18 exceeds 15
      EFFORT: ~1h  IMPACT: 180

  [6] !! SPLIT-FUNC      find_windows  CC=28  fan=6
      WHY: CC=28 exceeds 15
      EFFORT: ~1h  IMPACT: 168

  [7] !  SPLIT-FUNC      LinuxX11MirrorBackend.start  CC=15  fan=11
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 165

  [8] !  SPLIT-FUNC      find_companion_frames  CC=16  fan=6
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 96

  [9] !! SPLIT-FUNC      _is_internal_window  CC=30  fan=3
      WHY: CC=30 exceeds 15
      EFFORT: ~1h  IMPACT: 90

  [10] !! SPLIT           planfile.yaml
      WHY: 539L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting src/vdisplay/windows.py may break 25 import paths
  ⚠ Splitting goal.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          3.9 → ≤2.7
  max-CC:      40 → ≤20
  god-modules: 3 → 0
  high-CC(≥15): 10 → ≤5
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
  prev CC̄=2.2 → now CC̄=3.9
```

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

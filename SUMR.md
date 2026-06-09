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
- **version**: `0.1.1`
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
  version: 0.1.1;
}

dependencies {
  pillow: Pillow>=10.0;
  dev: "pytest>=8.0, Pillow>=10.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="vdisplay"] {
  entry: vdisplay.cli:main;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, DISPLAY;
}

deploy {
  target: pip;
}

environment[name="local"] {
  runtime: python;
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

*46 nodes · 59 edges · 8 modules · CC̄=2.2*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `main` *(in src.vdisplay.cli)* | 14 ⚠ | 0 | 45 | **45** |
| `build_parser` *(in src.vdisplay.cli)* | 1 | 1 | 43 | **44** |
| `run_command` *(in src.vdisplay.utils)* | 2 | 20 | 4 | **24** |
| `_output_origin` *(in src.vdisplay.backends.linux_x11_relay)* | 11 ⚠ | 1 | 20 | **21** |
| `_resolve_output` *(in src.vdisplay.backends.linux_x11_mirror)* | 9 | 2 | 12 | **14** |
| `release_window` *(in src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend)* | 8 | 0 | 13 | **13** |
| `_rgb_to_png_minimal` *(in src.vdisplay.capture.linux_xwd)* | 2 | 1 | 11 | **12** |
| `adopt_window` *(in src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend)* | 4 | 0 | 10 | **10** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/vdisplay
# generated in 0.02s
# nodes: 46 | edges: 59 | modules: 8
# CC̄=2.2

HUBS[20]:
  src.vdisplay.cli.main
    CC=14  in:0  out:45  total:45
  src.vdisplay.cli.build_parser
    CC=1  in:1  out:43  total:44
  src.vdisplay.utils.run_command
    CC=2  in:20  out:4  total:24
  src.vdisplay.backends.linux_x11_relay._output_origin
    CC=11  in:1  out:20  total:21
  src.vdisplay.backends.linux_x11_mirror._resolve_output
    CC=9  in:2  out:12  total:14
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.release_window
    CC=8  in:0  out:13  total:13
  src.vdisplay.capture.linux_xwd._rgb_to_png_minimal
    CC=2  in:1  out:11  total:12
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window
    CC=4  in:0  out:10  total:10
  src.vdisplay.capture.linux_xwd._xwd_to_rgb_bytes
    CC=6  in:1  out:9  total:10
  src.vdisplay.cli._print_json
    CC=1  in:8  out:2  total:10
  src.vdisplay.backends.linux_x11_relay._find_window_id
    CC=5  in:2  out:7  total:9
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start
    CC=8  in:0  out:9  total:9
  src.vdisplay.backends.linux_x11_relay._screen_geometry
    CC=2  in:1  out:7  total:8
  src.vdisplay.api.MirrorSession.create
    CC=6  in:0  out:8  total:8
  src.vdisplay.utils.require_command
    CC=2  in:6  out:2  total:8
  src.vdisplay.capture.linux_xwd._decode_pixels
    CC=12  in:1  out:7  total:8
  src.vdisplay.backends.linux_x11_mirror._output_mode
    CC=7  in:1  out:6  total:7
  src.vdisplay.backends.linux_x11_relay._debug_windows
    CC=3  in:0  out:7  total:7
  src.vdisplay.capture.linux_xwd._read_xwd_header
    CC=2  in:1  out:5  total:6
  src.vdisplay.capture.linux_xwd._rgb_to_png
    CC=2  in:1  out:5  total:6

MODULES:
  src.vdisplay.api  [7 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.backends.linux_x11_mirror  [7 funcs]
    screenshot_bytes  CC=2  out:2
    start  CC=8  out:9
    stop  CC=5  out:3
    _list_connected_outputs  CC=3  out:5
    _output_mode  CC=7  out:6
    _primary_output  CC=4  out:1
    _resolve_output  CC=9  out:12
  src.vdisplay.backends.linux_x11_relay  [9 funcs]
    adopt_window  CC=4  out:10
    release_window  CC=8  out:13
    _debug_windows  CC=3  out:7
    _find_window_id  CC=5  out:7
    _offscreen_coordinates  CC=1  out:1
    _output_origin  CC=11  out:20
    _screen_geometry  CC=2  out:7
    _window_geometry  CC=4  out:4
    _window_title  CC=1  out:2
  src.vdisplay.backends.linux_xvfb  [3 funcs]
    screenshot_bytes  CC=2  out:2
    start  CC=3  out:4
    _wait_for_display  CC=3  out:5
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
    build_parser  CC=1  out:43
    main  CC=14  out:45
  src.vdisplay.input.linux_xdotool  [4 funcs]
    click  CC=1  out:4
    hotkey  CC=1  out:3
    move  CC=1  out:5
    type_text  CC=1  out:3
  src.vdisplay.utils  [3 funcs]
    require_command  CC=2  out:2
    run_command  CC=2  out:4
    run_command_bytes  CC=1  out:1

EDGES:
  src.vdisplay.cli.main → src.vdisplay.cli.build_parser
  src.vdisplay.cli.main → src.vdisplay.cli._print_json
  src.vdisplay.api.VirtualDisplaySession.create → src.vdisplay.api._default_virtual_backend
  src.vdisplay.api.MirrorSession.create → src.vdisplay.api._default_mirror_backend
  src.vdisplay.api.WindowRelaySession.create → src.vdisplay.api._default_relay_backend
  src.vdisplay.api.platform_summary → src.vdisplay.api._default_virtual_backend
  src.vdisplay.api.platform_summary → src.vdisplay.api._default_mirror_backend
  src.vdisplay.api.platform_summary → src.vdisplay.api._default_relay_backend
  src.vdisplay.utils.run_command_bytes → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start → src.vdisplay.backends.linux_x11_mirror._list_connected_outputs
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start → src.vdisplay.backends.linux_x11_mirror._resolve_output
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start → src.vdisplay.backends.linux_x11_mirror._output_mode
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.stop → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.screenshot_bytes → src.vdisplay.capture.linux_xwd.capture_display_png
  src.vdisplay.backends.linux_x11_mirror._list_connected_outputs → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_mirror._resolve_output → src.vdisplay.backends.linux_x11_mirror._primary_output
  src.vdisplay.backends.linux_x11_mirror._output_mode → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_xvfb.LinuxXvfbBackend.start → src.vdisplay.backends.linux_xvfb._wait_for_display
  src.vdisplay.backends.linux_xvfb.LinuxXvfbBackend.screenshot_bytes → src.vdisplay.capture.linux_xwd.capture_display_png
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._window_geometry
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._window_title
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._find_window_id
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._offscreen_coordinates
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._output_origin
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.release_window → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.release_window → src.vdisplay.backends.linux_x11_relay._find_window_id
  src.vdisplay.backends.linux_x11_relay._find_window_id → src.vdisplay.utils.require_command
  src.vdisplay.backends.linux_x11_relay._find_window_id → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._window_geometry → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._window_title → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._offscreen_coordinates → src.vdisplay.backends.linux_x11_relay._screen_geometry
  src.vdisplay.backends.linux_x11_relay._screen_geometry → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._output_origin → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._output_origin → src.vdisplay.backends.linux_x11_relay._offscreen_coordinates
  src.vdisplay.backends.linux_x11_relay._debug_windows → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._debug_windows → src.vdisplay.backends.linux_x11_relay._window_title
  src.vdisplay.backends.linux_x11_relay._debug_windows → src.vdisplay.backends.linux_x11_relay._window_geometry
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
# generated in 0.02s
# nodes: 46 | edges: 59 | modules: 8
# CC̄=2.2

HUBS[20]:
  src.vdisplay.cli.main
    CC=14  in:0  out:45  total:45
  src.vdisplay.cli.build_parser
    CC=1  in:1  out:43  total:44
  src.vdisplay.utils.run_command
    CC=2  in:20  out:4  total:24
  src.vdisplay.backends.linux_x11_relay._output_origin
    CC=11  in:1  out:20  total:21
  src.vdisplay.backends.linux_x11_mirror._resolve_output
    CC=9  in:2  out:12  total:14
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.release_window
    CC=8  in:0  out:13  total:13
  src.vdisplay.capture.linux_xwd._rgb_to_png_minimal
    CC=2  in:1  out:11  total:12
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window
    CC=4  in:0  out:10  total:10
  src.vdisplay.capture.linux_xwd._xwd_to_rgb_bytes
    CC=6  in:1  out:9  total:10
  src.vdisplay.cli._print_json
    CC=1  in:8  out:2  total:10
  src.vdisplay.backends.linux_x11_relay._find_window_id
    CC=5  in:2  out:7  total:9
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start
    CC=8  in:0  out:9  total:9
  src.vdisplay.backends.linux_x11_relay._screen_geometry
    CC=2  in:1  out:7  total:8
  src.vdisplay.api.MirrorSession.create
    CC=6  in:0  out:8  total:8
  src.vdisplay.utils.require_command
    CC=2  in:6  out:2  total:8
  src.vdisplay.capture.linux_xwd._decode_pixels
    CC=12  in:1  out:7  total:8
  src.vdisplay.backends.linux_x11_mirror._output_mode
    CC=7  in:1  out:6  total:7
  src.vdisplay.backends.linux_x11_relay._debug_windows
    CC=3  in:0  out:7  total:7
  src.vdisplay.capture.linux_xwd._read_xwd_header
    CC=2  in:1  out:5  total:6
  src.vdisplay.capture.linux_xwd._rgb_to_png
    CC=2  in:1  out:5  total:6

MODULES:
  src.vdisplay.api  [7 funcs]
    create  CC=6  out:8
    create  CC=4  out:6
    create  CC=4  out:6
    _default_mirror_backend  CC=2  out:1
    _default_relay_backend  CC=2  out:1
    _default_virtual_backend  CC=2  out:1
    platform_summary  CC=1  out:5
  src.vdisplay.backends.linux_x11_mirror  [7 funcs]
    screenshot_bytes  CC=2  out:2
    start  CC=8  out:9
    stop  CC=5  out:3
    _list_connected_outputs  CC=3  out:5
    _output_mode  CC=7  out:6
    _primary_output  CC=4  out:1
    _resolve_output  CC=9  out:12
  src.vdisplay.backends.linux_x11_relay  [9 funcs]
    adopt_window  CC=4  out:10
    release_window  CC=8  out:13
    _debug_windows  CC=3  out:7
    _find_window_id  CC=5  out:7
    _offscreen_coordinates  CC=1  out:1
    _output_origin  CC=11  out:20
    _screen_geometry  CC=2  out:7
    _window_geometry  CC=4  out:4
    _window_title  CC=1  out:2
  src.vdisplay.backends.linux_xvfb  [3 funcs]
    screenshot_bytes  CC=2  out:2
    start  CC=3  out:4
    _wait_for_display  CC=3  out:5
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
    build_parser  CC=1  out:43
    main  CC=14  out:45
  src.vdisplay.input.linux_xdotool  [4 funcs]
    click  CC=1  out:4
    hotkey  CC=1  out:3
    move  CC=1  out:5
    type_text  CC=1  out:3
  src.vdisplay.utils  [3 funcs]
    require_command  CC=2  out:2
    run_command  CC=2  out:4
    run_command_bytes  CC=1  out:1

EDGES:
  src.vdisplay.cli.main → src.vdisplay.cli.build_parser
  src.vdisplay.cli.main → src.vdisplay.cli._print_json
  src.vdisplay.api.VirtualDisplaySession.create → src.vdisplay.api._default_virtual_backend
  src.vdisplay.api.MirrorSession.create → src.vdisplay.api._default_mirror_backend
  src.vdisplay.api.WindowRelaySession.create → src.vdisplay.api._default_relay_backend
  src.vdisplay.api.platform_summary → src.vdisplay.api._default_virtual_backend
  src.vdisplay.api.platform_summary → src.vdisplay.api._default_mirror_backend
  src.vdisplay.api.platform_summary → src.vdisplay.api._default_relay_backend
  src.vdisplay.utils.run_command_bytes → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start → src.vdisplay.backends.linux_x11_mirror._list_connected_outputs
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start → src.vdisplay.backends.linux_x11_mirror._resolve_output
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start → src.vdisplay.backends.linux_x11_mirror._output_mode
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.start → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.stop → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_mirror.LinuxX11MirrorBackend.screenshot_bytes → src.vdisplay.capture.linux_xwd.capture_display_png
  src.vdisplay.backends.linux_x11_mirror._list_connected_outputs → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_mirror._resolve_output → src.vdisplay.backends.linux_x11_mirror._primary_output
  src.vdisplay.backends.linux_x11_mirror._output_mode → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_xvfb.LinuxXvfbBackend.start → src.vdisplay.backends.linux_xvfb._wait_for_display
  src.vdisplay.backends.linux_xvfb.LinuxXvfbBackend.screenshot_bytes → src.vdisplay.capture.linux_xwd.capture_display_png
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._window_geometry
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._window_title
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._find_window_id
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._offscreen_coordinates
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window → src.vdisplay.backends.linux_x11_relay._output_origin
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.release_window → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.release_window → src.vdisplay.backends.linux_x11_relay._find_window_id
  src.vdisplay.backends.linux_x11_relay._find_window_id → src.vdisplay.utils.require_command
  src.vdisplay.backends.linux_x11_relay._find_window_id → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._window_geometry → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._window_title → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._offscreen_coordinates → src.vdisplay.backends.linux_x11_relay._screen_geometry
  src.vdisplay.backends.linux_x11_relay._screen_geometry → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._output_origin → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._output_origin → src.vdisplay.backends.linux_x11_relay._offscreen_coordinates
  src.vdisplay.backends.linux_x11_relay._debug_windows → src.vdisplay.utils.run_command
  src.vdisplay.backends.linux_x11_relay._debug_windows → src.vdisplay.backends.linux_x11_relay._window_title
  src.vdisplay.backends.linux_x11_relay._debug_windows → src.vdisplay.backends.linux_x11_relay._window_geometry
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
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 21f 1915L | python:17,shell:2,yaml:1,toml:1 | 2026-06-09
# generated in 0.00s
# CC̅=2.2 | critical:0/104 | dups:0 | cycles:0

HEALTH[0]: ok

REFACTOR[0]: none needed

PIPELINES[65]:
  [1] Src [main]: main → build_parser
      PURITY: 100% pure
  [2] Src [create]: create → _default_virtual_backend
      PURITY: 100% pure
  [3] Src [start]: start
      PURITY: 100% pure
  [4] Src [stop]: stop
      PURITY: 100% pure
  [5] Src [launch]: launch
      PURITY: 100% pure
  [6] Src [screenshot_bytes]: screenshot_bytes
      PURITY: 100% pure
  [7] Src [save_screenshot]: save_screenshot
      PURITY: 100% pure
  [8] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [9] Src [release_window]: release_window
      PURITY: 100% pure
  [10] Src [info]: info
      PURITY: 100% pure
  [11] Src [capabilities]: capabilities
      PURITY: 100% pure
  [12] Src [__init__]: __init__
      PURITY: 100% pure
  [13] Src [create]: create → _default_mirror_backend
      PURITY: 100% pure
  [14] Src [start]: start
      PURITY: 100% pure
  [15] Src [stop]: stop
      PURITY: 100% pure
  [16] Src [screenshot_bytes]: screenshot_bytes
      PURITY: 100% pure
  [17] Src [save_screenshot]: save_screenshot
      PURITY: 100% pure
  [18] Src [info]: info
      PURITY: 100% pure
  [19] Src [capabilities]: capabilities
      PURITY: 100% pure
  [20] Src [create]: create → _default_relay_backend
      PURITY: 100% pure
  [21] Src [start]: start
      PURITY: 100% pure
  [22] Src [stop]: stop
      PURITY: 100% pure
  [23] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [24] Src [release_window]: release_window
      PURITY: 100% pure
  [25] Src [list_adopted]: list_adopted
      PURITY: 100% pure
  [26] Src [info]: info
      PURITY: 100% pure
  [27] Src [capabilities]: capabilities
      PURITY: 100% pure
  [28] Src [__init__]: __init__
      PURITY: 100% pure
  [29] Src [capabilities]: capabilities
      PURITY: 100% pure
  [30] Src [info]: info
      PURITY: 100% pure
  [31] Src [start]: start → _list_connected_outputs → run_command
      PURITY: 100% pure
  [32] Src [stop]: stop → run_command
      PURITY: 100% pure
  [33] Src [screenshot_bytes]: screenshot_bytes → capture_display_png → require_command
      PURITY: 100% pure
  [34] Src [capabilities]: capabilities
      PURITY: 100% pure
  [35] Src [info]: info
      PURITY: 100% pure
  [36] Src [launch]: launch
      PURITY: 100% pure
  [37] Src [screenshot_bytes]: screenshot_bytes
      PURITY: 100% pure
  [38] Src [save_screenshot]: save_screenshot
      PURITY: 100% pure
  [39] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [40] Src [release_window]: release_window
      PURITY: 100% pure
  [41] Src [as_dict]: as_dict
      PURITY: 100% pure
  [42] Src [__init__]: __init__
      PURITY: 100% pure
  [43] Src [capabilities]: capabilities
      PURITY: 100% pure
  [44] Src [info]: info
      PURITY: 100% pure
  [45] Src [start]: start → _wait_for_display
      PURITY: 100% pure
  [46] Src [stop]: stop
      PURITY: 100% pure
  [47] Src [launch]: launch
      PURITY: 100% pure
  [48] Src [screenshot_bytes]: screenshot_bytes → capture_display_png → require_command
      PURITY: 100% pure
  [49] Src [adopt_window]: adopt_window
      PURITY: 100% pure
  [50] Src [release_window]: release_window
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=2.2    ←in:0  →out:0
  │ linux_x11_relay            250L  2C   14m  CC=11     ←0
  │ api                        178L  3C   32m  CC=6      ←1
  │ cli                        173L  0C    3m  CC=14     ←0
  │ linux_x11_mirror           173L  1C   10m  CC=9      ←0
  │ linux_xwd                  164L  0C   10m  CC=12     ←2
  │ linux_xvfb                  98L  1C   10m  CC=3      ←0
  │ base                        58L  1C   11m  CC=1      ←0
  │ utils                       46L  0C    3m  CC=2      ←4
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
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              61L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │

COUPLING: no cross-package imports detected

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 2 groups | 17f 1283L | 2026-06-09

SUMMARY:
  files_scanned: 17
  total_lines:   1283
  dup_groups:    2
  dup_fragments: 5
  saved_lines:   12
  scan_ms:       1964

HOTSPOTS[3] (files with most duplication):
  src/vdisplay/api.py  dup=12L  groups=1  frags=3  (0.9%)
  src/vdisplay/backends/linux_x11_mirror.py  dup=4L  groups=1  frags=1  (0.3%)
  src/vdisplay/backends/linux_xvfb.py  dup=4L  groups=1  frags=1  (0.3%)

DUPLICATES[2] (ranked by impact):
  [b8e2782d68a777c3]   STRU  _default_virtual_backend  L=4 N=3 saved=8 sim=1.00
      src/vdisplay/api.py:13-16  (_default_virtual_backend)
      src/vdisplay/api.py:19-22  (_default_mirror_backend)
      src/vdisplay/api.py:25-28  (_default_relay_backend)
  [3d902e6f1c31b63f]   STRU  screenshot_bytes  L=4 N=2 saved=4 sim=1.00
      src/vdisplay/backends/linux_x11_mirror.py:113-116  (screenshot_bytes)
      src/vdisplay/backends/linux_xvfb.py:72-75  (screenshot_bytes)

REFACTOR[2] (ranked by priority):
  [1] ○ extract_function   → src/vdisplay/utils/_default_virtual_backend.py
      WHY: 3 occurrences of 4-line block across 1 files — saves 8 lines
      FILES: src/vdisplay/api.py
  [2] ○ extract_function   → src/vdisplay/backends/utils/screenshot_bytes.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: src/vdisplay/backends/linux_x11_mirror.py, src/vdisplay/backends/linux_xvfb.py

QUICK_WINS[1] (low risk, high savings — do first):
  [1] extract_function   saved=8L  → src/vdisplay/utils/_default_virtual_backend.py
      FILES: api.py

EFFORT_ESTIMATE (total ≈ 0.4h):
  easy   _default_virtual_backend            saved=8L  ~16min
  easy   screenshot_bytes                    saved=4L  ~8min

METRICS-TARGET:
  dup_groups:  2 → 0
  saved_lines: 12 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 104 func | 11f | 2026-06-09
# generated in 0.00s

NEXT[1] (ranked by impact):
  [1] !! SPLIT           goal.yaml
      WHY: 511L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[1]:
  ⚠ Splitting goal.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          2.2 → ≤1.5
  max-CC:      14 → ≤7
  god-modules: 1 → 0
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
  (first run — no previous data)
```

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

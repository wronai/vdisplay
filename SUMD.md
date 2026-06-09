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
- **version**: `0.1.1`
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
  version: 0.1.1
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
- **version files**: `pyproject.toml:version`, `venv/lib/python3.13/site-packages/cryptography/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# vdisplay | 23f 1465L | python:20,shell:2,less:1 | 2026-06-09
# stats: 38 func | 16 cls | 23 mod | CC̄=3.4 | critical:3 | cycles:0
# alerts[5]: CC main=14; CC _decode_pixels=12; CC _output_origin=11; CC _resolve_output=9; CC _output_mode=7
# hotspots[5]: main fan=16; _output_origin fan=12; _resolve_output fan=9; test_virtual_display_screenshot fan=9; _rgb_to_png_minimal fan=7
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[23]:
  app.doql.less,36
  project.sh,59
  src/vdisplay/__init__.py,13
  src/vdisplay/api.py,179
  src/vdisplay/backends/__init__.py,2
  src/vdisplay/backends/base.py,59
  src/vdisplay/backends/linux_x11_mirror.py,174
  src/vdisplay/backends/linux_x11_relay.py,228
  src/vdisplay/backends/linux_xvfb.py,99
  src/vdisplay/backends/mirror_stub.py,35
  src/vdisplay/capture/__init__.py,4
  src/vdisplay/capture/base.py,10
  src/vdisplay/capture/linux_xwd.py,165
  src/vdisplay/cli.py,174
  src/vdisplay/exceptions.py,11
  src/vdisplay/input/__init__.py,4
  src/vdisplay/input/linux_xdotool.py,46
  src/vdisplay/models.py,27
  src/vdisplay/utils.py,47
  tests/test_capture_xwd.py,46
  tests/test_import.py,23
  tests/test_linux_xvfb_integration.py,22
  tree.sh,2
D:
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
    e: _list_connected_outputs,_resolve_output,_primary_output,_output_mode,LinuxX11MirrorBackend
    LinuxX11MirrorBackend: __init__(3),capabilities(0),info(0),start(0),stop(0),screenshot_bytes(0)
    _list_connected_outputs(display)
    _resolve_output(name;outputs)
    _primary_output(outputs)
    _output_mode(display;output)
  src/vdisplay/backends/linux_x11_relay.py:
    e: _find_window_id,_window_geometry,_window_title,_offscreen_coordinates,_screen_geometry,_output_origin,WindowState,LinuxX11RelayBackend
    WindowState:
    LinuxX11RelayBackend: __init__(2),capabilities(0),info(0),start(0),adopt_window(0),release_window(0),list_adopted(0)  # Move windows between monitors/outputs within the same X11 se
    _find_window_id(display;match_title)
    _window_geometry(display;window_id)
    _window_title(display;window_id)
    _offscreen_coordinates(display)
    _screen_geometry(display)
    _output_origin(display;target)
  src/vdisplay/backends/linux_xvfb.py:
    e: _wait_for_display,LinuxXvfbBackend
    LinuxXvfbBackend: __init__(3),capabilities(0),info(0),start(0),stop(0),launch(1),screenshot_bytes(0),adopt_window(0),release_window(0)
    _wait_for_display(display;timeout)
  src/vdisplay/backends/mirror_stub.py:
    e: MirrorStubBackend
    MirrorStubBackend: __init__(2),capabilities(0),info(0),screenshot_bytes(0)
  src/vdisplay/capture/__init__.py:
  src/vdisplay/capture/base.py:
    e: CaptureBackend
    CaptureBackend: screenshot_png(0)
  src/vdisplay/capture/linux_xwd.py:
    e: capture_display_png,xwd_bytes_to_png,_xwd_dimensions,_xwd_to_rgb_bytes,_parse_xwd_header,_read_xwd_header,_header_fields,_decode_pixels,_rgb_to_png,_rgb_to_png_minimal
    capture_display_png(display)
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
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('vdisplay', '0.1.1', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 36, 'less').
project_file('project.sh', 59, 'shell').
project_file('src/vdisplay/__init__.py', 13, 'python').
project_file('src/vdisplay/api.py', 179, 'python').
project_file('src/vdisplay/backends/__init__.py', 2, 'python').
project_file('src/vdisplay/backends/base.py', 59, 'python').
project_file('src/vdisplay/backends/linux_x11_mirror.py', 174, 'python').
project_file('src/vdisplay/backends/linux_x11_relay.py', 228, 'python').
project_file('src/vdisplay/backends/linux_xvfb.py', 99, 'python').
project_file('src/vdisplay/backends/mirror_stub.py', 35, 'python').
project_file('src/vdisplay/capture/__init__.py', 4, 'python').
project_file('src/vdisplay/capture/base.py', 10, 'python').
project_file('src/vdisplay/capture/linux_xwd.py', 165, 'python').
project_file('src/vdisplay/cli.py', 174, 'python').
project_file('src/vdisplay/exceptions.py', 11, 'python').
project_file('src/vdisplay/input/__init__.py', 4, 'python').
project_file('src/vdisplay/input/linux_xdotool.py', 46, 'python').
project_file('src/vdisplay/models.py', 27, 'python').
project_file('src/vdisplay/utils.py', 47, 'python').
project_file('tests/test_capture_xwd.py', 46, 'python').
project_file('tests/test_import.py', 23, 'python').
project_file('tests/test_linux_xvfb_integration.py', 22, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('src/vdisplay/api.py', '_default_virtual_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', '_default_mirror_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', '_default_relay_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', 'platform_summary', 0, 1, 5).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_list_connected_outputs', 1, 3, 5).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_resolve_output', 2, 9, 9).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_primary_output', 1, 4, 1).
python_function('src/vdisplay/backends/linux_x11_mirror.py', '_output_mode', 2, 7, 5).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_find_window_id', 2, 5, 5).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_window_geometry', 2, 4, 4).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_window_title', 2, 1, 2).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_offscreen_coordinates', 1, 1, 1).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_screen_geometry', 1, 2, 6).
python_function('src/vdisplay/backends/linux_x11_relay.py', '_output_origin', 2, 11, 12).
python_function('src/vdisplay/backends/linux_xvfb.py', '_wait_for_display', 2, 3, 4).
python_function('src/vdisplay/capture/linux_xwd.py', 'capture_display_png', 1, 1, 3).
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
python_function('src/vdisplay/cli.py', 'main', 1, 14, 16).
python_function('src/vdisplay/utils.py', 'require_command', 1, 2, 2).
python_function('src/vdisplay/utils.py', 'run_command', 1, 2, 4).
python_function('src/vdisplay/utils.py', 'run_command_bytes', 1, 1, 1).
python_function('tests/test_capture_xwd.py', '_make_xwd', 3, 1, 1).
python_function('tests/test_capture_xwd.py', 'test_xwd_to_png_red_pixel', 0, 2, 3).
python_function('tests/test_capture_xwd.py', 'test_xwd_to_png_2x1', 0, 2, 4).
python_function('tests/test_import.py', 'test_imports', 0, 4, 0).
python_function('tests/test_import.py', 'test_platform_summary', 0, 3, 1).
python_function('tests/test_import.py', 'test_capabilities', 0, 4, 2).
python_function('tests/test_linux_xvfb_integration.py', 'test_virtual_display_screenshot', 1, 3, 9).

% ── Python Classes ───────────────────────────────────────
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
python_method('LinuxX11MirrorBackend', '__init__', 3, 2, 4).
python_method('LinuxX11MirrorBackend', 'capabilities', 0, 1, 1).
python_method('LinuxX11MirrorBackend', 'info', 0, 3, 1).
python_method('LinuxX11MirrorBackend', 'start', 0, 8, 6).
python_method('LinuxX11MirrorBackend', 'stop', 0, 5, 1).
python_method('LinuxX11MirrorBackend', 'screenshot_bytes', 0, 2, 2).
python_class('src/vdisplay/backends/linux_x11_relay.py', 'WindowState').
python_class('src/vdisplay/backends/linux_x11_relay.py', 'LinuxX11RelayBackend').
python_method('LinuxX11RelayBackend', '__init__', 2, 2, 3).
python_method('LinuxX11RelayBackend', 'capabilities', 0, 1, 1).
python_method('LinuxX11RelayBackend', 'info', 0, 1, 2).
python_method('LinuxX11RelayBackend', 'start', 0, 2, 2).
python_method('LinuxX11RelayBackend', 'adopt_window', 0, 4, 9).
python_method('LinuxX11RelayBackend', 'release_window', 0, 8, 8).
python_method('LinuxX11RelayBackend', 'list_adopted', 0, 2, 1).
python_class('src/vdisplay/backends/linux_xvfb.py', 'LinuxXvfbBackend').
python_method('LinuxXvfbBackend', '__init__', 3, 1, 2).
python_method('LinuxXvfbBackend', 'capabilities', 0, 1, 1).
python_method('LinuxXvfbBackend', 'info', 0, 1, 1).
python_method('LinuxXvfbBackend', 'start', 0, 3, 4).
python_method('LinuxXvfbBackend', 'stop', 0, 3, 3).
python_method('LinuxXvfbBackend', 'launch', 1, 2, 4).
python_method('LinuxXvfbBackend', 'screenshot_bytes', 0, 2, 2).
python_method('LinuxXvfbBackend', 'adopt_window', 0, 1, 1).
python_method('LinuxXvfbBackend', 'release_window', 0, 1, 1).
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

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', 'sk-or-v1-...', 'OpenRouter API Key (required for real cost calculation)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Default AI model for cost analysis').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').

% ── Semantic Facts from SUMD.md ──────────────────────────
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

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

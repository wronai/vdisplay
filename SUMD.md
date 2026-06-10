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
- **version**: `0.1.14`
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
  version: 0.1.14;
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
  keys: OPENROUTER_API_KEY, LLM_MODEL, VDISPLAY_AGENT_AUTO, VDISPLAY_AGENT_HOST, VDISPLAY_AGENT_PORT, VDISPLAY_AGENT_URL, VDISPLAY_AGENT_TOKEN, VDISPLAY_AGENT_BROKER, DISPLAY, XDG_SESSION_TYPE, XDG_CURRENT_DESKTOP, DESKTOP_SESSION, VDISPLAY_BROWSER_DETACHED, VDISPLAY_VISION_LLM_MODE, VDISPLAY_VISION_LLM_MODALITIES, VDISPLAY_VISION_LLM, VDISPLAY_VISION_LLM_TIMEOUT_S, VDISPLAY_VISION_LLM_ENABLED, WAYLAND_DISPLAY, VDISPLAY_SCREENCAST_MULTIPLE, VDISPLAY_SCREENCAST_CURSOR, VDISPLAY_SESSION_DIR, VDISPLAY_SESSION, VDISPLAY_SESSION_ID, YDOTOOL_SOCKET, VDISPLAY_ALLOW_YDOTOOL_TYPING, VDISPLAY_IMG2NL, VDISPLAY_IMG2NL_LOCALE, VDISPLAY_CONTROL_SETTLE_MS, VDISPLAY_CAPTURE_ALLOW_PORTAL, PYTEST_CURRENT_TEST;
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
  version: 0.1.14
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
dsl2vdisplay
vdisplay-agent
uvicorn>=0.27
pydantic>=2
sqlmodel>=0.0.22
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
# vdisplay | 300f 37581L | python:290,shell:9,less:1 | 2026-06-10
# stats: 1462 func | 141 cls | 300 mod | CC̄=3.9 | critical:85 | cycles:0
# alerts[5]: CC test_sampler_creates_persisted_task=18; CC describe_screenshot_nl=14; CC dispatch=14; CC diagnose_control=14; CC _capture_all_from_screencast=14
# hotspots[5]: _start_screencast_impl fan=33; create_app fan=22; _portal_impl fan=22; register_routes fan=21; snapshot_dict fan=21
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[300]:
  app.doql.less,55
  brain/scratch_atspi.py,19
  examples/agent-broker/broker_demo.py,58
  examples/agent-broker/run.sh,27
  examples/ci-agent/agent.py,74
  examples/common/host_capture.py,30
  examples/common/screenshot_meta.py,163
  examples/common/validate_artifacts.py,85
  examples/control-plane/control_demo.py,173
  examples/control-plugin/src/vdisplay_example_plugin/__init__.py,28
  examples/control-plugin/src/vdisplay_example_plugin/my_provider.py,93
  examples/control-plugin-ax/src/vdisplay_example_ax_plugin/__init__.py,24
  examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py,94
  examples/control-plugin-uia/src/vdisplay_example_uia_plugin/__init__.py,24
  examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py,95
  examples/headless-virtual/run_virtual.py,64
  examples/host-mirror/mirror_demo.py,98
  examples/host-mirror/run-host.sh,26
  examples/host-mirror/run.sh,54
  examples/host-relay/relay_demo.py,138
  examples/host-relay/run-host.sh,25
  examples/host-relay/run.sh,48
  examples/run_all_examples.sh,159
  packages/cli2vdisplay/src/cli2vdisplay/cli.py,35
  packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py,5
  packages/dsl2vdisplay/src/dsl2vdisplay/bus.py,138
  packages/dsl2vdisplay/src/dsl2vdisplay/cli.py,71
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py,407
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py,2
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py,121
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py,116
  packages/dsl2vdisplay/src/dsl2vdisplay/result.py,27
  packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py,54
  packages/dsl2vdisplay/tests/test_dsl_control.py,170
  packages/dsl2vdisplay/tests/test_parity.py,15
  packages/mcp2vdisplay/src/mcp2vdisplay/cli.py,24
  packages/mcp2vdisplay/src/mcp2vdisplay/server.py,96
  packages/nlp2vdisplay/src/nlp2vdisplay/cli.py,42
  packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py,14
  packages/rest2vdisplay/src/rest2vdisplay/app.py,88
  packages/rest2vdisplay/src/rest2vdisplay/cli.py,36
  packages/uri2vdisplay/src/uri2vdisplay/cli.py,31
  packages/uri2vdisplay/src/uri2vdisplay/decode.py,32
  packages/vdisplay-agent/src/vdisplay_agent/__init__.py,8
  packages/vdisplay-agent/src/vdisplay_agent/cli.py,44
  packages/vdisplay-agent/src/vdisplay_agent/envelope.py,86
  packages/vdisplay-agent/src/vdisplay_agent/routes/__init__.py,16
  packages/vdisplay-agent/src/vdisplay_agent/routes/auth.py,25
  packages/vdisplay-agent/src/vdisplay_agent/routes/capture.py,33
  packages/vdisplay-agent/src/vdisplay_agent/routes/control.py,123
  packages/vdisplay-agent/src/vdisplay_agent/routes/health.py,77
  packages/vdisplay-agent/src/vdisplay_agent/routes/sampler.py,48
  packages/vdisplay-agent/src/vdisplay_agent/routes/session.py,137
  packages/vdisplay-agent/src/vdisplay_agent/routes/tasks.py,70
  packages/vdisplay-agent/src/vdisplay_agent/routes/windows.py,42
  packages/vdisplay-agent/src/vdisplay_agent/runtime.py,146
  packages/vdisplay-agent/src/vdisplay_agent/schemas.py,85
  packages/vdisplay-agent/src/vdisplay_agent/serve_port.py,147
  packages/vdisplay-agent/src/vdisplay_agent/server.py,31
  packages/vdisplay-agent/src/vdisplay_agent/services/__init__.py,6
  packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py,57
  packages/vdisplay-agent/src/vdisplay_agent/services/capture.py,97
  packages/vdisplay-agent/src/vdisplay_agent/services/control.py,114
  packages/vdisplay-agent/src/vdisplay_agent/services/outputs.py,20
  packages/vdisplay-agent/src/vdisplay_agent/services/relay.py,33
  packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py,184
  packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py,263
  packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py,182
  packages/vdisplay-agent/src/vdisplay_agent/services/windows.py,32
  packages/vdisplay-agent/src/vdisplay_agent/session_store.py,66
  packages/vdisplay-agent/src/vdisplay_agent/task_store.py,198
  project.sh,59
  src/vdisplay/__init__.py,13
  src/vdisplay/agent_config.py,72
  src/vdisplay/agent_dispatch.py,31
  src/vdisplay/agent_envelope.py,18
  src/vdisplay/api.py,194
  src/vdisplay/application/__init__.py,15
  src/vdisplay/application/artifacts.py,103
  src/vdisplay/application/commands.py,371
  src/vdisplay/application/errors.py,40
  src/vdisplay/application/executor.py,68
  src/vdisplay/application/handlers/__init__.py,7
  src/vdisplay/application/handlers/agent.py,242
  src/vdisplay/application/handlers/control.py,73
  src/vdisplay/application/handlers/local.py,292
  src/vdisplay/application/runtime.py,87
  src/vdisplay/application/services/__init__.py,4
  src/vdisplay/application/services/capture.py,183
  src/vdisplay/application/services/control.py,761
  src/vdisplay/application/services/discovery.py,240
  src/vdisplay/application/services/img2nl_enrich.py,125
  src/vdisplay/application/services/info.py,52
  src/vdisplay/application/services/map.py,276
  src/vdisplay/application/services/sampler.py,110
  src/vdisplay/application/services/sampler_loop.py,281
  src/vdisplay/application/services/session.py,327
  src/vdisplay/application/session_context.py,33
  src/vdisplay/application/session_recorder.py,501
  src/vdisplay/backends/__init__.py,2
  src/vdisplay/backends/base.py,65
  src/vdisplay/backends/linux_x11_mirror.py,260
  src/vdisplay/backends/linux_x11_relay.py,479
  src/vdisplay/backends/linux_xvfb.py,165
  src/vdisplay/backends/mirror_stub.py,35
  src/vdisplay/capture/__init__.py,16
  src/vdisplay/capture/base.py,10
  src/vdisplay/capture/host.py,556
  src/vdisplay/capture/linux_xwd.py,321
  src/vdisplay/capture/policy.py,141
  src/vdisplay/capture/portal.py,222
  src/vdisplay/capture/portal_screencast.py,780
  src/vdisplay/capture/providers/__init__.py,4
  src/vdisplay/capture/providers/base.py,23
  src/vdisplay/capture/providers/drm.py,93
  src/vdisplay/capture/providers/engine.py,100
  src/vdisplay/capture/providers/fbdev.py,78
  src/vdisplay/capture/providers/mss.py,69
  src/vdisplay/capture/providers/x11.py,36
  src/vdisplay/cli.py,37
  src/vdisplay/cli_handlers.py,35
  src/vdisplay/client.py,423
  src/vdisplay/commands/__init__.py,47
  src/vdisplay/commands/agent.py,156
  src/vdisplay/commands/all_cmd.py,47
  src/vdisplay/commands/common.py,138
  src/vdisplay/commands/control.py,160
  src/vdisplay/commands/diagnose.py,54
  src/vdisplay/commands/info.py,17
  src/vdisplay/commands/io.py,8
  src/vdisplay/commands/map.py,99
  src/vdisplay/commands/mirror.py,54
  src/vdisplay/commands/monitors.py,20
  src/vdisplay/commands/nlp.py,24
  src/vdisplay/commands/relay.py,111
  src/vdisplay/commands/sampler.py,133
  src/vdisplay/commands/screenshot.py,54
  src/vdisplay/commands/session.py,80
  src/vdisplay/commands/virtual.py,82
  src/vdisplay/commands/windows.py,30
  src/vdisplay/control/__init__.py,70
  src/vdisplay/control/action_bounds.py,25
  src/vdisplay/control/base.py,70
  src/vdisplay/control/browser_engine.py,56
  src/vdisplay/control/browser_session_store.py,197
  src/vdisplay/control/capabilities.py,77
  src/vdisplay/control/contracts.py,165
  src/vdisplay/control/descriptors.py,465
  src/vdisplay/control/engine.py,68
  src/vdisplay/control/gui_map.py,517
  src/vdisplay/control/gui_map_diff.py,501
  src/vdisplay/control/gui_map_export.py,180
  src/vdisplay/control/models.py,188
  src/vdisplay/control/plugins.py,164
  src/vdisplay/control/policy.py,243
  src/vdisplay/control/profile_inference.py,272
  src/vdisplay/control/providers/__init__.py,19
  src/vdisplay/control/providers/atspi.py,241
  src/vdisplay/control/providers/atspi_impl.py,414
  src/vdisplay/control/providers/ax.py,170
  src/vdisplay/control/providers/ax_impl.py,270
  src/vdisplay/control/providers/browser_playwright.py,340
  src/vdisplay/control/providers/browser_session.py,247
  src/vdisplay/control/providers/terminal.py,148
  src/vdisplay/control/providers/terminal_screen.py,261
  src/vdisplay/control/providers/terminal_session.py,228
  src/vdisplay/control/providers/uia.py,170
  src/vdisplay/control/providers/uia_impl.py,300
  src/vdisplay/control/providers/vision/__init__.py,4
  src/vdisplay/control/providers/vision/provider.py,705
  src/vdisplay/control/providers/x11.py,141
  src/vdisplay/control/registry.py,118
  src/vdisplay/control/router.py,272
  src/vdisplay/control/routing_semantics.py,159
  src/vdisplay/control/scoring.py,802
  src/vdisplay/control/screenshot_verify.py,266
  src/vdisplay/control/selector.py,348
  src/vdisplay/control/session.py,217
  src/vdisplay/control/session_kind.py,16
  src/vdisplay/control/verifier.py,568
  src/vdisplay/control/verify.py,499
  src/vdisplay/control/verify_strategy.py,17
  src/vdisplay/control/vision_disambiguate.py,79
  src/vdisplay/control/vision_llm.py,237
  src/vdisplay/control/vision_ocr.py,316
  src/vdisplay/control/vision_preview.py,239
  src/vdisplay/control/vision_template.py,259
  src/vdisplay/discovery.py,364
  src/vdisplay/exceptions.py,11
  src/vdisplay/input/__init__.py,12
  src/vdisplay/input/coords.py,220
  src/vdisplay/input/linux_xdotool.py,69
  src/vdisplay/input/linux_ydotool.py,115
  src/vdisplay/input/resolve.py,28
  src/vdisplay/models.py,27
  src/vdisplay/nl.py,159
  src/vdisplay/nlp.py,159
  src/vdisplay/payloads.py,87
  src/vdisplay/utils.py,69
  src/vdisplay/windows/__init__.py,47
  src/vdisplay/windows/constants.py,20
  src/vdisplay/windows/filter.py,174
  src/vdisplay/windows/normalize.py,104
  src/vdisplay/windows/query.py,210
  src/vdisplay/windows/rank.py,44
  src/vdisplay/windows/scan.py,111
  tests/conftest.py,87
  tests/contract/test_contracts.py,41
  tests/contract/test_descriptors.py,79
  tests/contract/test_providers.py,70
  tests/fixtures/__init__.py,2
  tests/fixtures/fake_browser.py,93
  tests/fixtures/gtk_demo_app.py,61
  tests/fixtures/run_gtk_demo.sh,12
  tests/test_agent.py,44
  tests/test_agent_api_contract.py,43
  tests/test_agent_browser_session.py,60
  tests/test_agent_client.py,119
  tests/test_agent_dispatch.py,53
  tests/test_agent_integration.py,68
  tests/test_agent_sampler.py,66
  tests/test_agent_serve_port.py,67
  tests/test_agent_tasks.py,130
  tests/test_agent_terminal_session.py,27
  tests/test_ax_invoke.py,89
  tests/test_browser_engine_profiles.py,190
  tests/test_browser_session_detached.py,75
  tests/test_capture_all_monitors.py,48
  tests/test_capture_crop.py,50
  tests/test_capture_providers.py,67
  tests/test_capture_xwd.py,53
  tests/test_cli_commands.py,97
  tests/test_cli_control_args.py,103
  tests/test_cli_session.py,109
  tests/test_client_request.py,43
  tests/test_command_contract.py,71
  tests/test_control_agent.py,36
  tests/test_control_app_matching.py,49
  tests/test_control_atspi.py,52
  tests/test_control_browser.py,52
  tests/test_control_browser_session.py,56
  tests/test_control_browser_verify.py,39
  tests/test_control_capabilities.py,84
  tests/test_control_executor.py,71
  tests/test_control_gtk_demo.py,207
  tests/test_control_plugins.py,107
  tests/test_control_policy.py,39
  tests/test_control_policy_v2.py,135
  tests/test_control_screenshot_verify.py,227
  tests/test_control_selector.py,36
  tests/test_control_selector_v2.py,88
  tests/test_control_set_value_verify.py,153
  tests/test_control_terminal.py,184
  tests/test_control_verifier_hybrid.py,200
  tests/test_control_verify.py,265
  tests/test_coords_rotation.py,39
  tests/test_cross_platform_providers.py,179
  tests/test_dsl_browser_open.py,176
  tests/test_dsl_terminal_control.py,42
  tests/test_dsl_terminal_open.py,69
  tests/test_example_control_plugin.py,103
  tests/test_example_uia_ax_plugins.py,145
  tests/test_execution_policy.py,65
  tests/test_gui_map.py,373
  tests/test_gui_map_diff.py,210
  tests/test_host_capture.py,43
  tests/test_host_capture_errors.py,37
  tests/test_img2nl_enrich.py,102
  tests/test_import.py,23
  tests/test_linux_xvfb_integration.py,22
  tests/test_mirror_primary.py,43
  tests/test_nl.py,145
  tests/test_nlp_pipeline.py,67
  tests/test_outputs_rotation.py,35
  tests/test_portal_screencast.py,146
  tests/test_profile_inference.py,79
  tests/test_relay_release.py,66
  tests/test_relay_window_region.py,70
  tests/test_routing_semantics.py,239
  tests/test_sampler_policy.py,91
  tests/test_sampler_recovery.py,100
  tests/test_screencast_multiple.py,20
  tests/test_screenshot_meta.py,54
  tests/test_screenshot_routing.py,105
  tests/test_session_catalog.py,72
  tests/test_session_recorder.py,112
  tests/test_uia_invoke.py,98
  tests/test_vision_anchor_matching.py,153
  tests/test_vision_anchor_visible_verify.py,126
  tests/test_vision_llm.py,181
  tests/test_vision_multimatch_disambiguation.py,159
  tests/test_vision_ocr_invoke.py,189
  tests/test_vision_preview.py,126
  tests/test_vision_provider_stub.py,164
  tests/test_vision_template_matching.py,93
  tests/test_wayland_capture_fastfail.py,65
  tests/test_wayland_input.py,134
  tests/test_windows.py,48
  tests/test_windows_dedupe.py,26
  tree.sh,2
D:
  brain/scratch_atspi.py:
  examples/agent-broker/broker_demo.py:
    e: main
    main()
  examples/ci-agent/agent.py:
    e: _load_common,main
    _load_common()
    main()
  examples/common/host_capture.py:
    e: capture_host_screenshot
    capture_host_screenshot(path)
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
  examples/control-plane/control_demo.py:
    e: run_diagnostics,show_active_controls,run_terminal_demo,run_browser_demo,main
    run_diagnostics(display)
    show_active_controls(display)
    run_terminal_demo(display)
    run_browser_demo(display)
    main()
  examples/control-plugin/src/vdisplay_example_plugin/__init__.py:
    e: _build_echo,register_plugin
    _build_echo()
    register_plugin(registry)
  examples/control-plugin/src/vdisplay_example_plugin/my_provider.py:
    e: EchoControlProvider
    EchoControlProvider: __init__(0),available(0),snapshot(0),find(1),invoke(1),focus(1),set_value(2),bounds(1)  # Returns synthetic nodes — useful for CI and plugin integrati
  examples/control-plugin-ax/src/vdisplay_example_ax_plugin/__init__.py:
    e: register_plugin
    register_plugin(registry)
  examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py:
    e: _use_mock_backend,_demo_backend,build_example_ax,ExampleAxProvider
    ExampleAxProvider: __init__(0),available(0)  # AX adapter — native on macOS, mock tree elsewhere for CI/doc
    _use_mock_backend()
    _demo_backend()
    build_example_ax()
  examples/control-plugin-uia/src/vdisplay_example_uia_plugin/__init__.py:
    e: register_plugin
    register_plugin(registry)
  examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py:
    e: _use_mock_backend,_demo_backend,build_example_uia,ExampleUiaProvider
    ExampleUiaProvider: __init__(0),available(0)  # UIA adapter — native on Windows, mock tree elsewhere for CI/
    _use_mock_backend()
    _demo_backend()
    build_example_uia()
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
    e: _dispatch_legacy,dispatch,_dispatch_fallback,execute_dsl_line
    _dispatch_legacy(cmd)
    dispatch(envelope)
    _dispatch_fallback(cmd)
    execute_dsl_line(line)
  packages/dsl2vdisplay/src/dsl2vdisplay/cli.py:
    e: main,_main_legacy,_main_subcommand
    main(argv)
    _main_legacy(argv)
    _main_subcommand(argv)
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py:
    e: split_command,normalize_tokens,resolve_verb,pick_flag,_with_display,_parse_windows,_parse_screenshot,_parse_virtual_start,_parse_launch,_parse_mirror,_parse_adopt,_has_flag,_parse_control_common,_parse_controls_list,_parse_controls_find,_parse_control_click,_parse_control_focus,_parse_control_set_value,_parse_diagnose_control,_parse_browser_open,_parse_terminal_open,_parse_release,parse_line,_screenshot_to_text,_mirror_to_text,_controls_list_to_text,_browser_open_to_text,_terminal_open_to_text,to_text,_control_to_text
    split_command(line)
    normalize_tokens(tokens)
    resolve_verb(tokens)
    pick_flag(tokens;flag)
    _with_display(rest;cmd)
    _parse_windows(rest;cmd)
    _parse_screenshot(rest;cmd)
    _parse_virtual_start(rest;cmd)
    _parse_launch(rest;cmd)
    _parse_mirror(rest;cmd)
    _parse_adopt(rest;cmd)
    _has_flag(tokens;flag)
    _parse_control_common(rest;cmd)
    _parse_controls_list(rest;cmd)
    _parse_controls_find(rest;cmd)
    _parse_control_click(rest;cmd)
    _parse_control_focus(rest;cmd)
    _parse_control_set_value(rest;cmd)
    _parse_diagnose_control(rest;cmd)
    _parse_browser_open(rest;cmd)
    _parse_terminal_open(rest;cmd)
    _parse_release(rest;cmd)
    parse_line(line)
    _screenshot_to_text(cmd)
    _mirror_to_text(cmd)
    _controls_list_to_text(cmd)
    _browser_open_to_text(cmd)
    _terminal_open_to_text(cmd)
    to_text(cmd)
    _control_to_text(action;cmd)
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
  packages/dsl2vdisplay/tests/test_dsl_control.py:
    e: test_parse_controls_list_uppercase,test_parse_controls_list_human_readable,test_parse_control_click_with_verify,test_parse_control_click_with_screenshot_verify,test_parse_control_set_value_requires_value_schema,test_parse_controls_find_with_provider_ref,test_command_request_from_dsl_control,test_command_request_provider_ref,test_parse_control_terminal_fields,test_parse_control_terminal_uppercase_flags,test_to_text_roundtrip_terminal_control,test_to_text_roundtrip_control_click,test_dispatch_control_verbs_via_executor
    test_parse_controls_list_uppercase()
    test_parse_controls_list_human_readable()
    test_parse_control_click_with_verify()
    test_parse_control_click_with_screenshot_verify()
    test_parse_control_set_value_requires_value_schema()
    test_parse_controls_find_with_provider_ref()
    test_command_request_from_dsl_control()
    test_command_request_provider_ref()
    test_parse_control_terminal_fields()
    test_parse_control_terminal_uppercase_flags()
    test_to_text_roundtrip_terminal_control()
    test_to_text_roundtrip_control_click()
    test_dispatch_control_verbs_via_executor(monkeypatch;line;action)
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
  packages/vdisplay-agent/src/vdisplay_agent/envelope.py:
    e: agent_meta,success,failure,from_runtime,json_success,json_from_runtime,json_error,strip_ok,flatten_envelope
    agent_meta()
    success(action;data)
    failure(action;error)
    from_runtime(action;payload)
    json_success(action;data)
    json_from_runtime(action;payload)
    json_error(action;exc)
    strip_ok(payload)
    flatten_envelope(payload)
  packages/vdisplay-agent/src/vdisplay_agent/routes/__init__.py:
    e: register_all_routes
    register_all_routes(app;broker)
  packages/vdisplay-agent/src/vdisplay_agent/routes/auth.py:
    e: expected_token,make_check_auth
    expected_token()
    make_check_auth(token)
  packages/vdisplay-agent/src/vdisplay_agent/routes/capture.py:
    e: register_routes
    register_routes(app;broker;check_auth)
  packages/vdisplay-agent/src/vdisplay_agent/routes/control.py:
    e: register_routes
    register_routes(app;broker;check_auth)
  packages/vdisplay-agent/src/vdisplay_agent/routes/health.py:
    e: _control_api_enabled,register_routes
    _control_api_enabled(app)
    register_routes(app;broker;check_auth)
  packages/vdisplay-agent/src/vdisplay_agent/routes/sampler.py:
    e: register_routes
    register_routes(app;broker;check_auth)
  packages/vdisplay-agent/src/vdisplay_agent/routes/session.py:
    e: register_routes
    register_routes(app;broker;check_auth)
  packages/vdisplay-agent/src/vdisplay_agent/routes/tasks.py:
    e: register_routes
    register_routes(app;broker;check_auth)
  packages/vdisplay-agent/src/vdisplay_agent/routes/windows.py:
    e: register_routes
    register_routes(app;broker;check_auth)
  packages/vdisplay-agent/src/vdisplay_agent/runtime.py:
    e: AgentRuntime
    AgentRuntime: sessions(0),relay(0),platform_capabilities(0),diagnostics(0),outputs(0),list_windows(0),start_virtual(0),start_mirror(0),start_relay(0),start_terminal(0),start_browser(0),start_screencast(0),stop_screencast(0),screencast_status(0),stop_session(1),recover_tasks(0),list_tasks(0),get_task(1),heartbeat_task(1),stop_task(1),list_sessions(0),start_sampler(1),stop_sampler(0),sampler_status(0),capture_frame(1),list_control_plugins(0),diagnose_control(0),list_controls(1),find_controls(1),invoke_control(1),focus_control(1),set_control_value(1),adopt_window(1),release_window(1),shutdown(0)  # Privileged runtime: owns session store and broker services.
  packages/vdisplay-agent/src/vdisplay_agent/schemas.py:
  packages/vdisplay-agent/src/vdisplay_agent/serve_port.py:
    e: _pid_alive,_parse_ss_pids,_pids_from_ss,_pids_from_lsof,find_listener_pids,_probe_is_vdisplay_agent,stop_pids,ensure_broker_port_free
    _pid_alive(pid)
    _parse_ss_pids(output)
    _pids_from_ss(port)
    _pids_from_lsof(port)
    find_listener_pids(port)
    _probe_is_vdisplay_agent(host;port)
    stop_pids(pids)
    ensure_broker_port_free(host;port)
  packages/vdisplay-agent/src/vdisplay_agent/server.py:
    e: create_app
    create_app(runtime)
  packages/vdisplay-agent/src/vdisplay_agent/services/__init__.py:
  packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py:
    e: platform_capabilities,diagnostics
    platform_capabilities()
    diagnostics(store)
  packages/vdisplay-agent/src/vdisplay_agent/services/capture.py:
    e: capture_frame,_capture_session,_capture_all_monitors,_region_from_body,_capture_host
    capture_frame(store;body)
    _capture_session(store;session_id;body)
    _capture_all_monitors(store;body)
    _region_from_body(body)
    _capture_host(store;body)
  packages/vdisplay-agent/src/vdisplay_agent/services/control.py:
    e: _selector_kwargs,list_control_plugins,diagnose_control,list_controls,find_controls,invoke_control,focus_control,set_control_value
    _selector_kwargs(body)
    list_control_plugins()
    diagnose_control()
    list_controls(body)
    find_controls(body)
    invoke_control(body)
    focus_control(body)
    set_control_value(body)
  packages/vdisplay-agent/src/vdisplay_agent/services/outputs.py:
    e: list_outputs_payload
    list_outputs_payload()
  packages/vdisplay-agent/src/vdisplay_agent/services/relay.py:
    e: adopt_window,release_window
    adopt_window(store;body)
    release_window(store;body)
  packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py:
    e: _config_from_body,_ensure_virtual_session,_capture_virtual_persistent,_recover_screencast,start_sampler,stop_sampler,sampler_status
    _config_from_body(body)
    _ensure_virtual_session(store)
    _capture_virtual_persistent(store)
    _recover_screencast(store)
    start_sampler(store;body)
    stop_sampler(store)
    sampler_status(store)
  packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py:
    e: _session_started,start_virtual,start_mirror,start_relay,start_screencast,stop_screencast,screencast_status,start_terminal,start_browser,stop_session,list_sessions,shutdown
    _session_started(record)
    start_virtual(store)
    start_mirror(store)
    start_relay(store)
    start_screencast(store)
    stop_screencast(store)
    screencast_status(store)
    start_terminal(store)
    start_browser(store)
    stop_session(store;session_id)
    list_sessions(store)
    shutdown(store)
  packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py:
    e: recover_on_startup,list_tasks,get_task,heartbeat_task,stop_task,register_session_task,unregister_session_task,begin_sampler_task,touch_sampler_task,end_sampler_task,begin_screencast_task,end_screencast_task,shutdown_tasks
    recover_on_startup(task_store;broker_id)
    list_tasks(task_store)
    get_task(task_store;task_id)
    heartbeat_task(task_store;task_id)
    stop_task(task_store;task_id)
    register_session_task(task_store)
    unregister_session_task(task_store;task_id)
    begin_sampler_task(task_store)
    touch_sampler_task(task_store;task_id)
    end_sampler_task(task_store;task_id)
    begin_screencast_task(task_store)
    end_screencast_task(task_store;task_id)
    shutdown_tasks(task_store;store)
  packages/vdisplay-agent/src/vdisplay_agent/services/windows.py:
    e: list_windows
    list_windows()
  packages/vdisplay-agent/src/vdisplay_agent/session_store.py:
    e: SessionRecord,SessionStore
    SessionRecord:
    SessionStore: register(0),get(1),pop(1),relay_session(1),clear_relay(0)
  packages/vdisplay-agent/src/vdisplay_agent/task_store.py:
    e: _utcnow,default_task_db_path,task_to_dict,TaskStatus,AgentTask,TaskStore
    TaskStatus:
    AgentTask:
    TaskStore: __init__(1),create_task(0),get_task(1),list_tasks(0),update_task(1),heartbeat(1),mark_orphan_running_as_stale(1)  # Thin repository over agent-tasks.db.
    _utcnow()
    default_task_db_path()
    task_to_dict(task)
  src/vdisplay/__init__.py:
  src/vdisplay/agent_config.py:
    e: agent_auto_enabled,reset_agent_probe_cache,_default_agent_base,_probe_agent_url,_probe_default_agent,resolve_agent_url,resolve_agent_token,use_agent
    agent_auto_enabled()
    reset_agent_probe_cache()
    _default_agent_base()
    _probe_agent_url(base_url)
    _probe_default_agent()
    resolve_agent_url(explicit)
    resolve_agent_token()
    use_agent(explicit)
  src/vdisplay/agent_dispatch.py:
    e: agent_client,dispatch_via_agent
    agent_client(url)
    dispatch_via_agent(cmd)
  src/vdisplay/agent_envelope.py:
    e: flatten_agent_envelope
    flatten_agent_envelope(payload)
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
    e: __getattr__
    __getattr__(name)
  src/vdisplay/application/artifacts.py:
    e: _file_ref,_append_unique,artifacts_from_screenshot,artifacts_from_control,build_artifacts
    _file_ref(kind;path)
    _append_unique(artifacts;seen;ref)
    artifacts_from_screenshot(data)
    artifacts_from_control(data)
    build_artifacts(cmd;data)
  src/vdisplay/application/commands.py:
    e: _resolve_browser_engine_from_dsl,_control_session_id_from_dsl,_control_fields_from_dsl,_terminal_fields_from_dsl,_browser_fields_from_dsl,CommandVerb,ArtifactRef,CommandRequest,CommandResult
    CommandVerb:
    ArtifactRef: to_dict(0)
    CommandRequest: action(0),from_dsl(2)
    CommandResult: to_dict(0),to_dsl_result(0),success(1),failure(1)
    _resolve_browser_engine_from_dsl(cmd)
    _control_session_id_from_dsl(cmd;verb)
    _control_fields_from_dsl(cmd)
    _terminal_fields_from_dsl(cmd;verb)
    _browser_fields_from_dsl(cmd;verb)
  src/vdisplay/application/errors.py:
    e: error_from_exception,ErrorCode,ApplicationError
    ErrorCode:
    ApplicationError: to_dict(0)
    error_from_exception(exc)
  src/vdisplay/application/executor.py:
    e: _maybe_enrich_screenshot,execute
    _maybe_enrich_screenshot(cmd;data)
    execute(cmd)
  src/vdisplay/application/handlers/__init__.py:
  src/vdisplay/application/handlers/agent.py:
    e: _strip_ok,_health,_info,_monitors,_windows,_all,_capabilities,_validate,_screenshot,_virtual_start,_terminal_open,_browser_open,_mirror,_adopt,_release,_diagnose_control,_controls_list,_controls_find,_control_click,_control_focus,_control_set_value,execute_agent
    _strip_ok(payload)
    _health(client;cmd)
    _info(client;_cmd)
    _monitors(client;cmd)
    _windows(client;cmd)
    _all(client;cmd)
    _capabilities(client;cmd)
    _validate(client;cmd)
    _screenshot(client;cmd)
    _virtual_start(client;cmd)
    _terminal_open(client;cmd)
    _browser_open(client;cmd)
    _mirror(client;cmd)
    _adopt(client;cmd)
    _release(client;cmd)
    _diagnose_control(client;cmd)
    _controls_list(client;cmd)
    _controls_find(client;cmd)
    _control_click(client;cmd)
    _control_focus(client;cmd)
    _control_set_value(client;cmd)
    execute_agent(cmd)
  src/vdisplay/application/handlers/control.py:
    e: control_selector_kwargs,control_service_kwargs,control_selector_only_kwargs,control_request_body
    control_selector_kwargs(cmd)
    control_service_kwargs(cmd)
    control_selector_only_kwargs(cmd)
    control_request_body(cmd)
  src/vdisplay/application/handlers/local.py:
    e: _health,_info,_monitors,_windows,_all,_capabilities,_validate,_screenshot,_virtual_start,_terminal_open,_browser_open,_mirror,_adopt,_release,_diagnose_control,_controls_list,_controls_find,_control_click,_control_focus,_control_set_value,execute_local
    _health(_cmd)
    _info(_cmd)
    _monitors(cmd)
    _windows(cmd)
    _all(cmd)
    _capabilities(_cmd)
    _validate(cmd)
    _screenshot(cmd)
    _virtual_start(cmd)
    _terminal_open(cmd)
    _browser_open(cmd)
    _mirror(cmd)
    _adopt(cmd)
    _release(cmd)
    _diagnose_control(cmd)
    _controls_list(cmd)
    _controls_find(cmd)
    _control_click(cmd)
    _control_focus(cmd)
    _control_set_value(cmd)
    execute_local(cmd)
  src/vdisplay/application/runtime.py:
    e: agent_client_optional,agent_client_required,prefer_agent,resolve_apps_only,get_execution_policy,ExecutionPolicy
    ExecutionPolicy: route(1),meta_for(1)  # Decide whether a command runs via vdisplay-agent or in-proce
    agent_client_optional()
    agent_client_required()
    prefer_agent()
    resolve_apps_only()
    get_execution_policy()
  src/vdisplay/application/services/__init__.py:
  src/vdisplay/application/services/capture.py:
    e: resolve_screenshot_routing,capture_screenshot,capture_screenshot_local,_capture_via_agent,capture_screenshot_via_client
    resolve_screenshot_routing(cmd)
    capture_screenshot()
    capture_screenshot_local()
    _capture_via_agent(client)
    capture_screenshot_via_client(client)
  src/vdisplay/application/services/control.py:
    e: _resolve_verify_mode,_control_settle_seconds,_apply_selector_overrides,_selector_from_kwargs,_provider_kwargs,_resolve_target,_load_map_pack,_resolve_map_target,_map_find_payload,_execute_map_action,list_control_plugins,diagnose_control,controls_list,_attach_vision_preview,controls_find,control_click,control_focus,control_set_value,_perform_action,_capture_before_state,_build_action_payload,_execute_action,_build_tree
    _resolve_verify_mode()
    _control_settle_seconds()
    _apply_selector_overrides(selector)
    _selector_from_kwargs()
    _provider_kwargs()
    _resolve_target(provider;snapshot;selector)
    _load_map_pack(map_path)
    _resolve_map_target(map_path;map_target)
    _map_find_payload(map_path;map_scope)
    _execute_map_action()
    list_control_plugins()
    diagnose_control()
    controls_list()
    _attach_vision_preview(payload)
    controls_find()
    control_click()
    control_focus()
    control_set_value()
    _perform_action(provider;action;target;value)
    _capture_before_state()
    _build_action_payload()
    _execute_action()
    _build_tree(snapshot)
  src/vdisplay/application/services/discovery.py:
    e: _run_discovery,list_monitors,list_monitors_local,list_windows_payload,list_windows_local,list_adopted,list_all,list_all_local,diagnose,diagnose_unattended,_sampler_hint
    _run_discovery(cmd)
    list_monitors(display)
    list_monitors_local(display)
    list_windows_payload(display)
    list_windows_local(display)
    list_adopted(display)
    list_all(display)
    list_all_local(display)
    diagnose(display)
    diagnose_unattended(display)
    _sampler_hint(contract)
  src/vdisplay/application/services/img2nl_enrich.py:
    e: img2nl_enabled,img2nl_locale,_image_path,describe_screenshot_image,_maybe_vision_llm_enrich,enrich_screenshot_payload
    img2nl_enabled()
    img2nl_locale()
    _image_path(payload)
    describe_screenshot_image(image_path)
    _maybe_vision_llm_enrich(image_path)
    enrich_screenshot_payload(payload)
  src/vdisplay/application/services/info.py:
    e: platform_info
    platform_info()
  src/vdisplay/application/services/map.py:
    e: _prepare_capture_meta,map_build,map_show,map_diff,map_refresh,_capture,_capture_via_agent,_monitor_index,_monitor_rotation
    _prepare_capture_meta()
    map_build()
    map_show()
    map_diff()
    map_refresh()
    _capture()
    _capture_via_agent()
    _monitor_index(display;monitor)
    _monitor_rotation(display;monitor)
  src/vdisplay/application/services/sampler.py:
    e: run_sampler,start_sampler_via_agent,SamplerConfig
    SamplerConfig: to_loop_config(0)
    run_sampler(config)
    start_sampler_via_agent(client;config)
  src/vdisplay/application/services/sampler_loop.py:
    e: resolve_capture_mode,is_screencast_recoverable_error,frame_extension,transcode_frame,validate_sampler_config,SamplerLoopConfig,SamplerLoopState,SamplerLoop
    SamplerLoopConfig:
    SamplerLoopState:
    SamplerLoop: __init__(2),start(0),stop(0),status(0),_run(0),_capture_frame_iteration(3),_handle_capture_error(1)  # Capture frames on an interval; safe to run in a daemon threa
    resolve_capture_mode(mode)
    is_screencast_recoverable_error(error)
    frame_extension(fmt)
    transcode_frame(path;fmt)
    validate_sampler_config(config)
  src/vdisplay/application/services/session.py:
    e: virtual_start,virtual_launch,virtual_screenshot,mirror_start,mirror_screenshot,relay_adopt,relay_release,relay_list_adopted,relay_screenshot,browser_open,terminal_open,unsupported_session_action
    virtual_start()
    virtual_launch(command)
    virtual_screenshot(output)
    mirror_start()
    mirror_screenshot(output)
    relay_adopt()
    relay_release()
    relay_list_adopted(display)
    relay_screenshot(output)
    browser_open()
    terminal_open()
    unsupported_session_action(kind;action)
  src/vdisplay/application/session_context.py:
    e: apply_cli_session_args,enrich_command_request
    apply_cli_session_args(args)
    enrich_command_request(cmd)
  src/vdisplay/application/session_recorder.py:
    e: session_recording_enabled,_redact_env,_collect_env_snapshot,_slugify,_default_session_name,resolve_session_root,get_session_recorder,record_execution,request_to_dict,result_to_dict,collect_artifacts,_artifacts_from_data,_collect_top_level_artifacts,_collect_block_artifacts,_collect_routing_artifacts,copy_artifact,extract_diagnostics,_build_summary,_utc_now,render_readme,StepRecord,SessionDocument,SessionRecorder
    StepRecord:
    SessionDocument: to_dict(0)
    SessionRecorder: __init__(1),session_dir(0),_load_or_create_document(0),record(2),flush(0)
    session_recording_enabled()
    _redact_env(env)
    _collect_env_snapshot()
    _slugify(value)
    _default_session_name()
    resolve_session_root(cmd)
    get_session_recorder(cmd)
    record_execution(cmd;result)
    request_to_dict(cmd)
    result_to_dict(result)
    collect_artifacts(result)
    _artifacts_from_data(data)
    _collect_top_level_artifacts(data;add)
    _collect_block_artifacts(data;add)
    _collect_routing_artifacts(data;add)
    copy_artifact(step_dir;artifact)
    extract_diagnostics(result)
    _build_summary(steps)
    _utc_now()
    render_readme(doc)
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
    e: _wayland_host_session,_monitor_source_name,resolve_window_region,_monitor_capture_region,_capture_all_from_driver_full,_capture_all_from_screencast,_try_screencast_capture,_try_mirror_capture,_try_driver_capture,capture_host_png,_host_capture_error,capture_host_to_file,_capture_individual_monitors,_try_bulk_capture,capture_all_monitors
    _wayland_host_session(display)
    _monitor_source_name(display;monitor;source)
    resolve_window_region(display)
    _monitor_capture_region(display;output_name)
    _capture_all_from_driver_full(display;monitors;output_dir)
    _capture_all_from_screencast(display;monitors;output_dir;screencast_session)
    _try_screencast_capture(screencast_session;region;errors)
    _try_mirror_capture(monitors;source_name;target;resolved;errors)
    _try_driver_capture(resolved;region;errors)
    capture_host_png()
    _host_capture_error(display;source;errors)
    capture_host_to_file(path)
    _capture_individual_monitors(monitors;resolved;output_dir;target;method;prefer_mirror;screencast_session)
    _try_bulk_capture(resolved;monitors;output_dir;method;prefer_mirror;screencast_session)
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
  src/vdisplay/capture/policy.py:
    e: assess_unattended_capture,_assess_virtual,_assess_wayland,CaptureCapabilityContract
    CaptureCapabilityContract: to_dict(0)  # Whether this host can do prompt-free continuous capture.
    assess_unattended_capture()
    _assess_virtual(reason)
    _assess_wayland(agent_url;screencast_ready)
  src/vdisplay/capture/portal.py:
    e: _portal_impl,_system_python,capture_portal_png,_capture_portal_to_file,PortalProvider
    PortalProvider: available(0),capture_full(0),capture_region(1)  # Opt-in portal capture (VDISPLAY_CAPTURE_ALLOW_PORTAL=1). Not
    _portal_impl(out)
    _system_python()
    capture_portal_png()
    _capture_portal_to_file(out)
  src/vdisplay/capture/portal_screencast.py:
    e: get_active_screencast,_set_active,_set_active_if_self,_screencast_multiple,start_screencast_session,stop_screencast_session,invalidate_screencast_session,_system_python,_ensure_portal_deps,_open_screencast_pipewire_fd,_start_screencast,_portal_request_path,_stream_properties,_stream_serial,_stream_target,screencast_stream_region,_ensure_fd_inheritable,_dbus_fd,_close_pipewire_fd,_start_screencast_impl,_listen_portal_request,_close_screencast_session,_capture_pipewire_stream,_capture_pipewire_frame_gi_subprocess,_capture_pipewire_frame_gst_launch,_capture_pipewire_node,_vdisplay_src_path,_start_screencast_subprocess,PortalScreenCastSession
    PortalScreenCastSession: is_ready(0),start(0),_parse_node_ids(1),_parse_stream_targets(1),status(0),capture_png(0),stop(0)  # Hold an open portal ScreenCast session and grab PNG frames f
    get_active_screencast()
    _set_active(session)
    _set_active_if_self(session)
    _screencast_multiple(explicit)
    start_screencast_session()
    stop_screencast_session()
    invalidate_screencast_session(session)
    _system_python()
    _ensure_portal_deps()
    _open_screencast_pipewire_fd(session_path)
    _start_screencast()
    _portal_request_path(bus;token)
    _stream_properties(raw)
    _stream_serial(properties)
    _stream_target(node_id;properties)
    screencast_stream_region(session)
    _ensure_fd_inheritable(fd)
    _dbus_fd(value)
    _close_pipewire_fd(fd)
    _start_screencast_impl()
    _listen_portal_request(bus;request_path;callback)
    _close_screencast_session(session_path)
    _capture_pipewire_stream()
    _capture_pipewire_frame_gi_subprocess(cap_fd;node_id;target_object;out)
    _capture_pipewire_frame_gst_launch(cap_fd;node_id;target_object;out)
    _capture_pipewire_node(node_id)
    _vdisplay_src_path()
    _start_screencast_subprocess()
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
    e: _route_outputs_query,_route_windows_query,_route_control_command,_route_terminal_open,_route_browser_open,_route_command,AgentClient
    AgentClient: __init__(1),_request(2),_send(2),_build_request(2),_http_error_message(1),_raise_on_error(1),_normalize_payload(1),request(1),health(0),capabilities(0),diagnostics(0),outputs(0),windows(0),start_virtual(0),start_mirror(0),start_relay(0),browser_open(0),start_screencast(0),stop_screencast(0),screencast_status(0),stop_session(1),sampler_start(0),sampler_stop(0),sampler_status(0),diagnose_control(0),list_controls(1),find_controls(1),invoke_control(1),focus_control(1),set_control_value(1),capture_frame(0),capture_png_bytes(0),adopt_window(0),release_window(0)  # HTTP client for the local vdisplay-agent broker.
    _route_outputs_query(cmd)
    _route_windows_query(cmd)
    _route_control_command(verb;body)
    _route_terminal_open(cmd)
    _route_browser_open(cmd)
    _route_command(cmd)
  src/vdisplay/commands/__init__.py:
    e: register_all
    register_all(sub)
  src/vdisplay/commands/agent.py:
    e: register,_agent_client,handle,_handle_serve,_handle_browser_open,_handle_screencast
    register(sub)
    _agent_client()
    handle(args)
    _handle_serve(args)
    _handle_browser_open(args)
    _handle_screencast(args)
  src/vdisplay/commands/all_cmd.py:
    e: register,handle,register_outputs,handle_outputs
    register(sub)
    handle(args)
    register_outputs(sub)
    handle_outputs(args)
  src/vdisplay/commands/common.py:
    e: add_display_arg,add_all_arg,add_window_filter_args,include_all_from_args,add_control_selector_args,add_map_args,add_preview_args,control_selector_kwargs_from_args,control_selector_kwargs_for_service
    add_display_arg(parser)
    add_all_arg(parser)
    add_window_filter_args(parser)
    include_all_from_args(args)
    add_control_selector_args(parser)
    add_map_args(parser)
    add_preview_args(parser)
    control_selector_kwargs_from_args(args)
    control_selector_kwargs_for_service(args)
  src/vdisplay/commands/control.py:
    e: register,_add_selector_args,_run_control,_handle_browser_open,_handle_control_list,_handle_control_find,_handle_control_click,_handle_control_focus,_handle_control_set_value,handle
    register(sub)
    _add_selector_args(parser)
    _run_control(args;verb)
    _handle_browser_open(args)
    _handle_control_list(args)
    _handle_control_find(args)
    _handle_control_click(args)
    _handle_control_focus(args)
    _handle_control_set_value(args)
    handle(args)
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
  src/vdisplay/commands/map.py:
    e: register,handle
    register(sub)
    handle(args)
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
  src/vdisplay/commands/sampler.py:
    e: register,_config_from_args,handle,_handle_stop,_handle_status,_handle_start,_start_agent,_wait_for_sampler
    register(sub)
    _config_from_args(args)
    handle(args)
    _handle_stop(url)
    _handle_status(url)
    _handle_start(args;url)
    _start_agent(args;url;config)
    _wait_for_sampler(client;progress;interval_s)
  src/vdisplay/commands/screenshot.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/session.py:
    e: add_root_session_args,command_request_from_control_args
    add_root_session_args(parser)
    command_request_from_control_args(args;verb)
  src/vdisplay/commands/virtual.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/commands/windows.py:
    e: register,handle
    register(sub)
    handle(args)
  src/vdisplay/control/__init__.py:
  src/vdisplay/control/action_bounds.py:
    e: action_bounds_for_vision,click_point_for_vision
    action_bounds_for_vision(bounds)
    click_point_for_vision(bounds)
  src/vdisplay/control/base.py:
    e: ControlProvider
    ControlProvider: available(0),snapshot(0),find(1),invoke(1),focus(1),set_value(2),bounds(1),capabilities(0),verify_modes(0),session_kind(0)
  src/vdisplay/control/browser_engine.py:
    e: normalize_browser_engine,engine_profile_id,browser_engine_profile,resolve_session_browser_engine,BrowserEngineKind
    BrowserEngineKind:
    normalize_browser_engine(value)
    engine_profile_id(engine)
    browser_engine_profile(engine)
    resolve_session_browser_engine(session_id)
  src/vdisplay/control/browser_session_store.py:
    e: detached_sessions_enabled,meta_path,profile_dir,save_meta,load_meta,remove_meta,process_alive,find_free_port,_chromium_executable,wait_for_cdp,launch_detached_chromium,stop_detached,session_available,DetachedBrowserMeta
    DetachedBrowserMeta: to_dict(0)
    detached_sessions_enabled()
    meta_path(session_id)
    profile_dir(session_id)
    save_meta(meta)
    load_meta(session_id)
    remove_meta(session_id)
    process_alive(pid)
    find_free_port()
    _chromium_executable()
    wait_for_cdp(cdp_url)
    launch_detached_chromium()
    stop_detached(session_id)
    session_available(session_id)
  src/vdisplay/control/capabilities.py:
    e: ProviderCapabilities
    ProviderCapabilities: to_dict(0)
  src/vdisplay/control/contracts.py:
    e: provider_score_from_dataclass,control_route_request_from_command,ProviderScoreContract,ExecutionContext,VerifySpec,ProviderResult,ControlRouteRequest
    ProviderScoreContract: to_dict(0)
    ExecutionContext: to_dict(0)
    VerifySpec: to_dict(0)
    ProviderResult: to_dict(0)
    ControlRouteRequest: to_dict(0)
    provider_score_from_dataclass(score)
    control_route_request_from_command(cmd)
  src/vdisplay/control/descriptors.py:
    e: resolve_host_environment,descriptor_for,all_provider_descriptors,all_application_profiles,all_selector_extensions,detect_platform_profile,extension_catalog,SelectorExtension,HostEnvironmentKind,PlatformProfile,ApplicationProfile,ProviderDescriptor
    SelectorExtension: to_dict(0)  # Backend- or profile-specific selector fields beyond the core
    HostEnvironmentKind:  # Host / execution environment — capability probes, deps, poli
    PlatformProfile: to_dict(0)
    ApplicationProfile: to_dict(0)  # Class-of-app hints — not a first-class backend.
    ProviderDescriptor: to_dict(0)
    resolve_host_environment()
    descriptor_for(provider_id)
    all_provider_descriptors()
    all_application_profiles()
    all_selector_extensions()
    detect_platform_profile()
    extension_catalog()
  src/vdisplay/control/engine.py:
    e: resolve_provider_routing,resolve_route,resolve_provider
    resolve_provider_routing(backend)
    resolve_route(backend)
    resolve_provider(backend)
  src/vdisplay/control/gui_map.py:
    e: load_gui_map,save_gui_map,_slug,tile_fingerprint,element_from_ocr_box,crop_png_bounds,_translate_ocr_boxes,parse_crop_bounds,_boxes_in_scope_for_build,_prepare_ocr_boxes_for_build,build_gui_map_from_ocr,resolve_map_element,resolve_map_region,map_element_to_node,scoped_capture_region,verify_hints_from_map_element,resolve_map_verify_mode,GuiMapBounds,GuiMapPoint,GuiMapIdentity,GuiMapElement,GuiMapRegion,GuiMapPack
    GuiMapBounds: from_dict(2),to_dict(0),from_control_bounds(2),to_control_bounds(0),center(0)
    GuiMapPoint: from_dict(2),to_dict(0)
    GuiMapIdentity: from_dict(2),to_dict(0)
    GuiMapElement: from_dict(2),to_dict(0)
    GuiMapRegion: from_dict(2),to_dict(0)
    GuiMapPack: from_dict(2),to_dict(0)
    load_gui_map(path)
    save_gui_map(path;pack)
    _slug(text)
    tile_fingerprint(png;bounds)
    element_from_ocr_box(box)
    crop_png_bounds(png;scope)
    _translate_ocr_boxes(boxes;offset_x;offset_y)
    parse_crop_bounds(raw)
    _boxes_in_scope_for_build(boxes;scope)
    _prepare_ocr_boxes_for_build(png;capture_meta)
    build_gui_map_from_ocr(png;capture_meta)
    resolve_map_element(pack;target_id)
    resolve_map_region(pack;scope_id)
    map_element_to_node(element)
    scoped_capture_region(pack;scope_id)
    verify_hints_from_map_element(element)
    resolve_map_verify_mode(element)
  src/vdisplay/control/gui_map_diff.py:
    e: _center,_distance,_box_to_bounds,_normalize_label,_labels_match,_boxes_in_scope,match_ocr_box_for_element,assess_map_drift,_classify_element_drift,_region_drifts_for,_new_ocr_labels,diff_gui_map,_refresh_known_elements,_append_new_elements,refresh_gui_map,ElementDrift,RegionDrift,GuiMapDiff
    ElementDrift: to_dict(0)
    RegionDrift: to_dict(0)
    GuiMapDiff: to_dict(0)
    _center(bounds)
    _distance(a;b)
    _box_to_bounds(box)
    _normalize_label(text)
    _labels_match(stored;live)
    _boxes_in_scope(boxes;scope)
    match_ocr_box_for_element(element;boxes)
    assess_map_drift(diff)
    _classify_element_drift(element;live_box)
    _region_drifts_for(region_items;png)
    _new_ocr_labels(pack;boxes;matched_box_ids)
    diff_gui_map(pack;png;capture_meta)
    _refresh_known_elements(pack;diff;boxes)
    _append_new_elements(pack)
    refresh_gui_map(pack;png;capture_meta)
  src/vdisplay/control/gui_map_export.py:
    e: render_map_markdown,_region_markdown,_element_markdown,render_map_svg,_element_svg,_png_b64,write_map_artifacts
    render_map_markdown(pack)
    _region_markdown(region;pack)
    _element_markdown(element)
    render_map_svg(png;pack)
    _element_svg(element)
    _png_b64(png)
    write_map_artifacts(pack)
  src/vdisplay/control/models.py:
    e: EnvironmentKind,ControlRole,ControlActionKind,ControlBounds,ControlAction,ElementCapabilities,ControlNode,ControlSnapshot,ActionResult
    EnvironmentKind:  # Target automation environment for provider routing.
    ControlRole:
    ControlActionKind:
    ControlBounds: to_dict(0),center(0)
    ControlAction: to_dict(0)
    ElementCapabilities: to_dict(0),from_dict(2)  # Backend-agnostic capability flags for a control element.
    ControlNode: to_dict(0)
    ControlSnapshot: to_dict(0)
    ActionResult: to_dict(0)
  src/vdisplay/control/plugins.py:
    e: _register_plugin,_bootstrap_builtin_registry,load_entry_point_plugins,get_provider_registry,register_control_provider,unregister_control_provider,list_control_plugins,iter_provider_names,reset_control_plugins_for_tests,get_registered_descriptor,RegisteredPlugin
    RegisteredPlugin: to_dict(0)
    _register_plugin(registry;descriptor;factory)
    _bootstrap_builtin_registry()
    load_entry_point_plugins(registry)
    get_provider_registry()
    register_control_provider(descriptor;factory)
    unregister_control_provider(provider_id)
    list_control_plugins()
    iter_provider_names()
    reset_control_plugins_for_tests()
    get_registered_descriptor(provider_id)
  src/vdisplay/control/policy.py:
    e: evaluate_provider_routing,_evaluate_platform_backends,_evaluate_pointer_fallback,_evaluate_readiness,_pointer_fallback_for_host,assess_control_capability,_append_accessibility_env_vars,ControlCapabilityContract
    ControlCapabilityContract: to_dict(0)
    evaluate_provider_routing()
    _evaluate_platform_backends(host)
    _evaluate_pointer_fallback(host)
    _evaluate_readiness()
    _pointer_fallback_for_host()
    assess_control_capability()
    _append_accessibility_env_vars(reasons)
  src/vdisplay/control/profile_inference.py:
    e: profile_for,_score_vision_only_surface,_score_browser_engine,_score_web_spa,_score_terminal_pty,_score_electron_desktop,_score_native_desktop,_score_candidate,infer_application_profile,profile_provider_boost,ProfileInference
    ProfileInference: to_dict(0)
    profile_for(profile_id)
    _score_vision_only_surface(selector)
    _score_browser_engine(profile)
    _score_web_spa(selector)
    _score_terminal_pty(selector;sid)
    _score_electron_desktop(selector)
    _score_native_desktop(selector)
    _score_candidate(profile)
    infer_application_profile(selector)
    profile_provider_boost(provider;profile)
  src/vdisplay/control/providers/__init__.py:
  src/vdisplay/control/providers/atspi.py:
    e: _gi_available,_system_python,_vdisplay_src_path,_run_subprocess,_actions_from_dict,_snapshot_from_dict,AtspiControlProvider
    AtspiControlProvider: __init__(0),available(0),probe_integration(0),snapshot(0),find(1),invoke(1),focus(1),set_value(2),bounds(1)
    _gi_available()
    _system_python()
    _vdisplay_src_path()
    _run_subprocess(payload)
    _actions_from_dict(raw_actions)
    _snapshot_from_dict(data)
  src/vdisplay/control/providers/atspi_impl.py:
    e: _atspi,_map_role,_atspi_module,_iface,_node_actions,_text_iface,_node_text_value,_provider_ref,_node_state,_node_capabilities,_node_bounds,_application_matches,snapshot_dict,_resolve_accessible,dispatch,_handle_available,_handle_invoke,_handle_focus,_handle_set_value
    _atspi()
    _map_role(role_name)
    _atspi_module()
    _iface(accessible;name)
    _node_actions(accessible)
    _text_iface(accessible)
    _node_text_value(accessible)
    _provider_ref(accessible;node_id)
    _node_state(accessible;role_name)
    _node_capabilities(accessible;actions;role)
    _node_bounds(accessible)
    _application_matches(application;app_filter)
    snapshot_dict()
    _resolve_accessible(element_id)
    dispatch(payload)
    _handle_available()
    _handle_invoke(payload)
    _handle_focus(payload)
    _handle_set_value(payload)
  src/vdisplay/control/providers/ax.py:
    e: AxControlProvider
    AxControlProvider: __init__(0),available(0),_records_to_nodes(1),snapshot(0),find(1),_record_for(1),invoke(1),focus(1),set_value(2),bounds(1)  # macOS desktop semantic control via Accessibility API.
  src/vdisplay/control/providers/ax_impl.py:
    e: ax_deps_available,_role_from_ax,_ax_bounds,_matches_role,_matches_name_fields,_matches_window_fields,_matches_selector,filter_records,create_ax_backend,AxElementRecord,AxBackend,PyobjcAxBackend,MockAxBackend
    AxElementRecord:
    AxBackend: connect(0),collect_elements(0),invoke(1),focus(1),set_value(2)
    PyobjcAxBackend: __init__(0),connect(0),collect_elements(0),_require_record(1),invoke(1),focus(1),set_value(2)  # Native macOS AX via ApplicationServices.
    MockAxBackend: __init__(1),connect(0),collect_elements(0),invoke(1),focus(1),set_value(2)  # In-memory AX backend for tests.
    ax_deps_available()
    _role_from_ax(role_value)
    _ax_bounds(element)
    _matches_role(record;role)
    _matches_name_fields(record;selector)
    _matches_window_fields(record;selector)
    _matches_selector(record;selector)
    filter_records(records;selector)
    create_ax_backend(backend)
  src/vdisplay/control/providers/browser_playwright.py:
    e: _playwright_available,_role_for_element,_capabilities_for,_actions_for,_bounds_from_box,_dom_state,_node_from_element,_PageLike,_ElementLike,BrowserPlaywrightProvider
    _PageLike: goto(1),title(0),query_selector_all(1),locator(1)
    _ElementLike: evaluate(1),bounding_box(0),inner_text(0),get_attribute(1),click(0),fill(1),focus(0)
    BrowserPlaywrightProvider: __init__(0),available(0),_resolve_session_id(0),_page_for(0),snapshot(0),find(1),_resolve_element(1),invoke(1),focus(1),set_value(2),bounds(1),close(0)
    _playwright_available()
    _role_for_element(element)
    _capabilities_for(role)
    _actions_for(role)
    _bounds_from_box(box)
    _dom_state(element)
    _node_from_element(element)
  src/vdisplay/control/providers/browser_session.py:
    e: new_session_id,default_registry,BrowserSession,BrowserSessionRegistry
    BrowserSession: close(0)
    BrowserSessionRegistry: __init__(0),_tracks_detached_sessions(0),list_ids(0),get(1),require(1),open(1),_attach(1),open_mock(1),close(1),close_all(0)  # Browser sessions — in-process registry with optional CDP rea
    new_session_id()
    default_registry()
  src/vdisplay/control/providers/terminal.py:
    e: _terminal_deps_available,_parse_ref,_matches_terminal_node,_find_terminal_nodes,TerminalControlProvider
    TerminalControlProvider: __init__(0),available(0),_resolve_session_id(0),snapshot(0),find(1),invoke(1),focus(1),set_value(2),bounds(1)
    _terminal_deps_available()
    _parse_ref(element_id)
    _matches_terminal_node(node;selector)
    _find_terminal_nodes(nodes;selector)
  src/vdisplay/control/providers/terminal_screen.py:
    e: _line_node_id,_cursor_node_id,nodes_from_screen,new_session_id,ScreenLine,ScreenSnapshot,ScreenBuffer
    ScreenLine: stripped(0)  # One terminal row (1-based line number).
    ScreenSnapshot: line_at(1)  # Parsed terminal screen state.
    ScreenBuffer: __init__(0),_init_pyte(0),resize(0),feed(1),_sync_from_pyte(0),_feed_simple(1),set_lines(1),snapshot(0)  # Mutable terminal screen fed by PTY output bytes.
    _line_node_id(session_id;line_no)
    _cursor_node_id(session_id)
    nodes_from_screen(screen)
    new_session_id()
  src/vdisplay/control/providers/terminal_session.py:
    e: default_registry,TerminalSession,TerminalSessionRegistry
    TerminalSession: write(1),send_enter(0),sent_text(0),stop(0),close(0),_start_reader(0)  # One controllable terminal session.
    TerminalSessionRegistry: __init__(0),list_ids(0),get(1),require(1),open_mock(0),open_process(1),open_pexpect(1),close(1),close_all(0)  # In-memory registry of open terminal sessions.
    default_registry()
  src/vdisplay/control/providers/uia.py:
    e: UiaControlProvider
    UiaControlProvider: __init__(0),available(0),_records_to_nodes(1),snapshot(0),find(1),_record_for(1),invoke(1),focus(1),set_value(2),bounds(1)  # Windows desktop semantic control via UI Automation.
  src/vdisplay/control/providers/uia_impl.py:
    e: uia_deps_available,_role_from_uia,_rect_to_bounds,_matches_role,_matches_name_fields,_matches_window_fields,_matches_selector,_record_from_uia_element,_passes_uia_filters,filter_records,create_uia_backend,UiaElementRecord,UiaBackend,ComtypesUiaBackend,MockUiaBackend
    UiaElementRecord:
    UiaBackend: connect(0),collect_elements(0),invoke(1),focus(1),set_value(2)
    ComtypesUiaBackend: __init__(0),connect(0),collect_elements(0),_require_record(1),invoke(1),focus(1),set_value(2)  # Native Windows UIA via UIAutomationCore.dll.
    MockUiaBackend: __init__(1),connect(0),collect_elements(0),invoke(1),focus(1),set_value(2)  # In-memory UIA backend for tests.
    uia_deps_available()
    _role_from_uia(control_type_name)
    _rect_to_bounds(rect)
    _matches_role(record;role)
    _matches_name_fields(record;selector)
    _matches_window_fields(record;selector)
    _matches_selector(record;selector)
    _record_from_uia_element(element)
    _passes_uia_filters(record)
    filter_records(records;selector)
    create_uia_backend(backend)
  src/vdisplay/control/providers/vision/__init__.py:
  src/vdisplay/control/providers/vision/provider.py:
    e: VisionStubProvider
    VisionStubProvider: __init__(0),available(0),_capture_png(0),last_capture(0),last_find_debug(0),enable_preview_debug(1),_box_key(1),_record_find_debug(0),_build_rejected_preview(2),_node_from_ocr(1),_node_from_template(1),_node_from_anchor(1),_selector_wants_ocr(1),_find_nodes(1),_try_ocr_nodes(1),_try_template_nodes(1),_try_anchor_nodes(1),_maybe_stub_fast_path(1),_maybe_stub_fallback(1),_ensure_png(2),_template_nodes_from_png(3),_anchor_nodes_from_png(3),_ocr_nodes_from_png(3),_stub_anchor_node(1),snapshot(0),find(1),_node_for(1),_click_node(1),invoke_map_node(1),focus_map_node(1),set_value_map_node(2),_pointer_click_at(1),invoke(1),focus(1),set_value(2),_paste_value(2),bounds(1)  # Canvas/game/stream surfaces — semantic tree unavailable; OCR
  src/vdisplay/control/providers/x11.py:
    e: _snapshot_hint,_window_to_snapshot,X11ControlProvider
    X11ControlProvider: __init__(0),available(0),snapshot(0)
    _snapshot_hint(app;display)
    _window_to_snapshot(window)
  src/vdisplay/control/registry.py:
    e: _build_atspi,_build_uia,_build_ax,_build_browser,_build_x11,_build_terminal,_build_vision,default_provider_registry,ProviderRegistry
    ProviderRegistry: __init__(0),register(2),list_names(0),list_descriptors(0),get_descriptor(1),build(1)
    _build_atspi()
    _build_uia()
    _build_ax()
    _build_browser()
    _build_x11()
    _build_terminal()
    _build_vision()
    default_provider_registry()
  src/vdisplay/control/router.py:
    e: _eligible_for_profile,_select_winner,default_router,RouteResult,ControlRouter
    RouteResult: to_dict(0)
    ControlRouter: __init__(1),_normalize_request(1),evaluate(1),route(1),route_command(1),_build_decision(0)
    _eligible_for_profile(candidates;application_profile)
    _select_winner(backend;candidates)
    default_router()
  src/vdisplay/control/routing_semantics.py:
    e: host_environment_constraints,infer_target_environment,session_kind_for_target,legal_verify_modes_for_target,requires_open_session,build_routing_semantics,host_environment_from_capture_session_type,RoutingSemantics
    RoutingSemantics: to_dict(0)  # Unified routing contract: host, target, session, verify.
    host_environment_constraints(host)
    infer_target_environment(selector)
    session_kind_for_target(target)
    legal_verify_modes_for_target(target)
    requires_open_session(target)
    build_routing_semantics()
    host_environment_from_capture_session_type(session_type)
  src/vdisplay/control/scoring.py:
    e: _all_provider_names,_base_score,normalize_backend,score_to_confidence,_atspi_ready,_uia_ready,_ax_ready,_browser_ready,_xdotool_ready,_xwayland_reachable,_terminal_ready,_browser_session_ready,_vision_ready,_terminal_session_ready,_is_terminal_context,_is_browser_context,_is_desktop_context,selector_context,_linux_desktop_hosts,_score_atspi_provider,_score_uia_provider,_score_ax_provider,_score_terminal_provider,_score_browser_provider,_browser_context_score,_browser_session_check,_x11_linux_eligibility,_x11_invoke_capabilities,_x11_context_score,_score_x11_provider,_score_vision_provider,_score_plugin_provider,_apply_routing_boosts,score_provider,rank_providers,_verify_screenshot_only,_verify_hybrid,select_verify_provider,ProviderScore,ProviderRoutingDecision
    ProviderScore: to_dict(0)
    ProviderRoutingDecision: to_dict(0)
    _all_provider_names()
    _base_score(provider)
    normalize_backend(backend)
    score_to_confidence(score)
    _atspi_ready()
    _uia_ready()
    _ax_ready()
    _browser_ready()
    _xdotool_ready()
    _xwayland_reachable(display)
    _terminal_ready()
    _browser_session_ready(session_id)
    _vision_ready()
    _terminal_session_ready(session_id)
    _is_terminal_context(selector;sid)
    _is_browser_context(selector)
    _is_desktop_context(selector)
    selector_context(selector;session_id)
    _linux_desktop_hosts()
    _score_atspi_provider(context)
    _score_uia_provider(context)
    _score_ax_provider(context)
    _score_terminal_provider(context;session_id)
    _score_browser_provider(context;session_id)
    _browser_context_score(context;reasons)
    _browser_session_check(context;session_id;eligible;missing;reasons)
    _x11_linux_eligibility(host;display)
    _x11_invoke_capabilities()
    _x11_context_score(context)
    _score_x11_provider(context;display)
    _score_vision_provider(context)
    _score_plugin_provider(provider;context)
    _apply_routing_boosts(provider;score;reasons)
    score_provider(provider)
    rank_providers()
    _verify_screenshot_only(candidates;action_provider)
    _verify_hybrid(candidates;action_provider)
    select_verify_provider(candidates)
  src/vdisplay/control/screenshot_verify.py:
    e: _region_from_bounds,enrich_screencast_stream_meta,_resolve_screencast_stream_region,_region_from_agent_screencast_status,capture_control_screenshot,_target_region,_maybe_crop_capture,_capture_via_agent,diff_png_bytes,verify_screenshot_pair
    _region_from_bounds(bounds)
    enrich_screencast_stream_meta(meta)
    _resolve_screencast_stream_region()
    _region_from_agent_screencast_status()
    capture_control_screenshot()
    _target_region(target)
    _maybe_crop_capture(payload;region)
    _capture_via_agent()
    diff_png_bytes(before;after)
    verify_screenshot_pair(before;after)
  src/vdisplay/control/selector.py:
    e: _infer_selector_environment,_normalize,_role_matches,_app_matches,_window_title_matches,_name_matches,_text_matches,_terminal_line_matches,_terminal_col_matches,_score,find_matches,pick_match,parse_role,_apply_attr,parse_selector,ControlSelector
    ControlSelector: from_dict(2),to_dict(0),active_fields(0)  # Unified selector for desktop, browser, terminal, and vision 
    _infer_selector_environment(selector)
    _normalize(value)
    _role_matches(node;role)
    _app_matches(node;app)
    _window_title_matches(node;window_title)
    _name_matches(node)
    _text_matches(node)
    _terminal_line_matches(node;line)
    _terminal_col_matches(node;col)
    _score(node;selector)
    find_matches(nodes;selector)
    pick_match(nodes;selector)
    parse_role(value)
    _apply_attr(selector;key;op;val)
    parse_selector(expr)
  src/vdisplay/control/session.py:
    e: parse_session_kind,_safe_info,_safe_capabilities,metadata_from_agent_record,metadata_from_browser_session,metadata_from_terminal_session,build_catalog_from_agent_store,build_catalog_local,merge_catalogs,SessionMetadata,SessionCatalog,AgentSessionStore
    SessionMetadata: to_dict(0)  # Portable session record for APIs and diagnostics.
    SessionCatalog: to_dict(0)
    AgentSessionStore:
    parse_session_kind(kind)
    _safe_info(handle)
    _safe_capabilities(handle)
    metadata_from_agent_record(record)
    metadata_from_browser_session(session)
    metadata_from_terminal_session(session)
    build_catalog_from_agent_store(store)
    build_catalog_local()
    merge_catalogs()
  src/vdisplay/control/session_kind.py:
    e: SessionKind
    SessionKind:
  src/vdisplay/control/verifier.py:
    e: verify_spec_from_flags,_region_for_verify,_ocr_text_contains,_vision_rescue_result,_aggregate_dual,_aggregate_screenshot_only,_aggregate_semantic_only,default_verifier,VerifyContext,VerificationResult,VerifierPipeline
    VerifyContext:
    VerificationResult: to_dict(0)
    VerifierPipeline: _run_semantic_if_needed(1),_run_visual_if_needed(3),_maybe_ocr_rescue(4),_evaluate_runs(2),verify_after_action(1),_verify_anchor_visible(2),_verify_ocr_contains(2),_verify_with_vision_rescue(2),_verify_combined(2),_run_semantic(1),_run_visual(2),_run_ocr(3),_maybe_vision_llm_fallback(2),_run_anchor_visible(2),_aggregate(0)
    verify_spec_from_flags()
    _region_for_verify(ctx;spec)
    _ocr_text_contains(expected;text)
    _vision_rescue_result()
    _aggregate_dual(semantic_ok;visual_ok)
    _aggregate_screenshot_only(visual_ok)
    _aggregate_semantic_only(spec_mode;semantic_ok;visual_ok)
    default_verifier()
  src/vdisplay/control/verify.py:
    e: _node_changes,_node_key,_display_text,_subtree_ids,_scope_root_id,_structural_key,_nodes_by_match_key,diff_snapshots,snapshot_diff,collect_changed_nodes,_label_prefix_changes,_label_prefix_changes_by_identity,_selector_change,_handle_selector_verification,_handle_label_verification,_handle_set_value_verification,_handle_focus_verification,_handle_invoke_verification,_add_diff_nodes,verify_action_result,_is_verified
    _node_changes(before_node;after_node)
    _node_key(node)
    _display_text(node)
    _subtree_ids(snapshot;root_id)
    _scope_root_id(snapshot;target)
    _structural_key(snapshot;node_id;scope_root_id)
    _nodes_by_match_key(snapshot;node_ids)
    diff_snapshots(before;after)
    snapshot_diff(before;after)
    collect_changed_nodes(diff)
    _label_prefix_changes(before;after)
    _label_prefix_changes_by_identity(before;after)
    _selector_change(before;after;selector)
    _handle_selector_verification(before;after;verify_selector)
    _handle_label_verification(before;after;verify_label;scope_root_id)
    _handle_set_value_verification(after;target;scope_root;expected_value)
    _handle_focus_verification(diff)
    _handle_invoke_verification(after;target;diff;has_label_or_selector)
    _add_diff_nodes(diff)
    verify_action_result()
    _is_verified(action;state_diff)
  src/vdisplay/control/verify_strategy.py:
    e: VerifyStrategy
    VerifyStrategy:
  src/vdisplay/control/vision_disambiguate.py:
    e: item_confidence,filter_by_confidence,pick_by_index,resolve_vision_matches,vision_threshold,disambiguation_meta,_HasConfidence
    _HasConfidence:
    item_confidence(item)
    filter_by_confidence(matches)
    pick_by_index(matches;index)
    resolve_vision_matches(matches;selector)
    vision_threshold(selector)
    disambiguation_meta()
  src/vdisplay/control/vision_llm.py:
    e: _truthy,_normalize_model,vision_llm_settings,vision_llm_available,vision_llm_fallback_enabled,vision_llm_enrich_enabled,_png_to_data_url,_parse_yes_no,_tokenize_expected,query_vision_llm,verify_text_in_region,summarize_region,VisionLlmSettings
    VisionLlmSettings:
    _truthy(raw)
    _normalize_model(model)
    vision_llm_settings()
    vision_llm_available()
    vision_llm_fallback_enabled()
    vision_llm_enrich_enabled()
    _png_to_data_url(png)
    _parse_yes_no(text)
    _tokenize_expected(text)
    query_vision_llm(png;prompt)
    verify_text_in_region(png;expected_text)
    summarize_region(png)
  src/vdisplay/control/vision_ocr.py:
    e: ocr_available,ocr_png,_normalize,_box_matches,_match_by_vision_anchor,_match_by_text_fields,match_selector_boxes,ocr_find_selector,_vertical_overlap,_horizontal_overlap,anchor_spatial_relation,_find_anchor_boxes,anchor_spatial_find,anchor_based_find,ocr_anchor_combined_find,OcrTextBox
    OcrTextBox: to_dict(0)
    ocr_available()
    ocr_png(png)
    _normalize(value)
    _box_matches(box;needle)
    _match_by_vision_anchor(boxes;selector)
    _match_by_text_fields(boxes;selector)
    match_selector_boxes(boxes;selector)
    ocr_find_selector(png;selector)
    _vertical_overlap(a;b)
    _horizontal_overlap(a;b)
    anchor_spatial_relation(candidate;anchor;rel)
    _find_anchor_boxes(boxes;anchor_text)
    anchor_spatial_find(boxes)
    anchor_based_find(boxes)
    ocr_anchor_combined_find(png)
  src/vdisplay/control/vision_preview.py:
    e: preview_available,action_pick_index,_match_kind,preview_matches_from_nodes,confidence_color,render_match_overlay,build_vision_preview,write_preview_png,decode_preview_png,PreviewMatch,VisionPreviewDebug
    PreviewMatch: to_dict(0)
    VisionPreviewDebug: to_dict(0)
    preview_available()
    action_pick_index(selector)
    _match_kind(node)
    preview_matches_from_nodes(nodes)
    confidence_color(confidence)
    render_match_overlay(png;matches)
    build_vision_preview(png;nodes)
    write_preview_png(png;path)
    decode_preview_png(payload)
  src/vdisplay/control/vision_template.py:
    e: template_available,load_template_png,_png_to_gray_array,match_template,_dedupe_matches,_search_region_for_relation,template_find_selector,match_template_bounds,template_anchor_find,TemplateMatch
    TemplateMatch: to_dict(0)
    template_available()
    load_template_png(source)
    _png_to_gray_array(png)
    match_template(png;template_png)
    _dedupe_matches(matches)
    _search_region_for_relation(anchor;rel)
    template_find_selector(png;selector)
    match_template_bounds(png;template_path;anchor_box;relation)
    template_anchor_find(png)
  src/vdisplay/discovery.py:
    e: resolve_host_display,_display_socket_exists,_looks_like_xvfb_only,list_outputs,_attach_output_nl,_list_monitors,_parse_xrandr_query,_merge_output_metadata,list_windows,find_window_suggestions,diagnose_display,_display_hint,list_monitors,window_discovery_meta
    resolve_host_display(preferred)
    _display_socket_exists(display)
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
  src/vdisplay/input/coords.py:
    e: global_pointer_coords,_global_from_region,_global_from_monitor,_local_to_region_coords,_rotate_local_to_region,_aspect_mismatch,_rotation_for_monitor,_monitor_by_name
    global_pointer_coords(local_x;local_y;capture_meta)
    _global_from_region(local_x;local_y)
    _global_from_monitor(local_x;local_y)
    _local_to_region_coords(local_x;local_y)
    _rotate_local_to_region(local_x;local_y)
    _aspect_mismatch(monitor_w;monitor_h;png_w;png_h)
    _rotation_for_monitor(display;name)
    _monitor_by_name(display;name)
  src/vdisplay/input/linux_xdotool.py:
    e: LinuxXdotoolInput
    LinuxXdotoolInput: __init__(1),_env(0),available(0),can_type(0),can_paste(0),move(2),click(1),type_text(1),hotkey(0)
  src/vdisplay/input/linux_ydotool.py:
    e: _ydotool_env,LinuxYdotoolInput
    LinuxYdotoolInput: __init__(0),available(0),can_type(0),can_paste(0),move(2),click(1),type_text(1),hotkey(0)  # Drive mouse/keyboard on Wayland through ``ydotool`` / ``ydot
    _ydotool_env()
  src/vdisplay/input/resolve.py:
    e: resolve_pointer_input,PointerInput
    PointerInput: move(2),click(1),type_text(1)
    resolve_pointer_input()
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
    e: require_command,run_command,run_command_bytes,auto_install_package
    require_command(name)
    run_command(args)
    run_command_bytes(args)
    auto_install_package(package_name)
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
    e: _isolate_agent_env,_reset_portal_screencast_state,_wait_for_url,live_agent_url,agent_client
    _isolate_agent_env(monkeypatch)
    _reset_portal_screencast_state()
    _wait_for_url(url)
    live_agent_url()
    agent_client()
  tests/contract/test_contracts.py:
    e: test_provider_score_contract_maps_confidence,test_control_route_request_from_command
    test_provider_score_contract_maps_confidence()
    test_control_route_request_from_command()
  tests/contract/test_descriptors.py:
    e: test_builtin_provider_descriptors_cover_registry,test_descriptor_for_aliases,test_terminal_descriptor_declares_session_and_grid,test_extension_catalog_shape,test_detect_platform_profile_has_os_family,test_resolve_host_environment_linux_mapping,test_resolve_host_environment_other_os,test_detect_platform_profile_host_environment_matches_display_stack
    test_builtin_provider_descriptors_cover_registry()
    test_descriptor_for_aliases()
    test_terminal_descriptor_declares_session_and_grid()
    test_extension_catalog_shape()
    test_detect_platform_profile_has_os_family()
    test_resolve_host_environment_linux_mapping()
    test_resolve_host_environment_other_os()
    test_detect_platform_profile_host_environment_matches_display_stack(monkeypatch)
  tests/contract/test_providers.py:
    e: test_registry_lists_builtin_providers,test_router_evaluate_without_building_provider,test_provider_contract_surface,test_rank_providers_returns_contract_scores
    test_registry_lists_builtin_providers()
    test_router_evaluate_without_building_provider(monkeypatch)
    test_provider_contract_surface(name)
    test_rank_providers_returns_contract_scores(monkeypatch)
  tests/fixtures/__init__.py:
  tests/fixtures/fake_browser.py:
    e: FakeElement,FakeLocator,FakePage
    FakeElement: __init__(1),evaluate(1),bounding_box(0),inner_text(0),get_attribute(1),click(0),fill(1),focus(0)
    FakeLocator: __init__(1),count(0),nth(1),first(0)
    FakePage: __init__(0),goto(1),title(0),query_selector_all(1),locator(1)
  tests/fixtures/gtk_demo_app.py:
    e: main
    main()
  tests/test_agent.py:
    e: test_agent_health,test_agent_capabilities,test_agent_virtual_session_capture
    test_agent_health(agent_client)
    test_agent_capabilities(agent_client)
    test_agent_virtual_session_capture(agent_client;tmp_path)
  tests/test_agent_api_contract.py:
    e: test_agent_health_envelope,test_agent_version_envelope,test_agent_capabilities_envelope,test_flatten_envelope_for_sdk
    test_agent_health_envelope(agent_client)
    test_agent_version_envelope(agent_client)
    test_agent_capabilities_envelope(agent_client)
    test_flatten_envelope_for_sdk()
  tests/test_agent_browser_session.py:
    e: agent_client_with_browser,test_agent_browser_open_list_stop
    agent_client_with_browser(monkeypatch)
    test_agent_browser_open_list_stop(agent_client_with_browser)
  tests/test_agent_client.py:
    e: test_use_agent_false_by_default,test_resolve_agent_url_auto_detects_live_agent,test_client_unreachable_raises,test_probe_retries_after_initial_miss,test_flatten_agent_envelope_without_vdisplay_agent_package,test_client_flattens_agent_envelope,test_virtual_screenshot_routes_local_when_agent_up
    test_use_agent_false_by_default(monkeypatch)
    test_resolve_agent_url_auto_detects_live_agent(live_agent_url;monkeypatch)
    test_client_unreachable_raises(monkeypatch)
    test_probe_retries_after_initial_miss(monkeypatch)
    test_flatten_agent_envelope_without_vdisplay_agent_package()
    test_client_flattens_agent_envelope(monkeypatch)
    test_virtual_screenshot_routes_local_when_agent_up(live_agent_url;monkeypatch)
  tests/test_agent_dispatch.py:
    e: test_dispatch_monitors_via_agent,test_dsl_bus_uses_executor_when_agent_configured
    test_dispatch_monitors_via_agent(monkeypatch)
    test_dsl_bus_uses_executor_when_agent_configured(monkeypatch)
  tests/test_agent_integration.py:
    e: test_agent_client_round_trip_monitors,test_dsl_dispatch_round_trip,test_rest2vdisplay_round_trip,test_virtual_screenshot_round_trip
    test_agent_client_round_trip_monitors(live_agent_url;monkeypatch)
    test_dsl_dispatch_round_trip(live_agent_url;monkeypatch)
    test_rest2vdisplay_round_trip(live_agent_url;monkeypatch)
    test_virtual_screenshot_round_trip(live_agent_url;monkeypatch;tmp_path)
  tests/test_agent_sampler.py:
    e: test_agent_sampler_start_status_stop
    test_agent_sampler_start_status_stop(agent_client;tmp_path;monkeypatch)
  tests/test_agent_serve_port.py:
    e: test_parse_ss_pids,test_ensure_broker_port_free_no_listeners,test_ensure_broker_port_free_stops_vdisplay_agent,test_ensure_broker_port_free_rejects_foreign_service,test_find_listener_pids_excludes_current_pid,test_stop_pids_ignores_current_pid
    test_parse_ss_pids()
    test_ensure_broker_port_free_no_listeners(monkeypatch)
    test_ensure_broker_port_free_stops_vdisplay_agent(monkeypatch)
    test_ensure_broker_port_free_rejects_foreign_service(monkeypatch)
    test_find_listener_pids_excludes_current_pid(monkeypatch)
    test_stop_pids_ignores_current_pid(monkeypatch)
  tests/test_agent_tasks.py:
    e: agent_client_with_db,test_startup_marks_orphan_tasks_stale,test_sampler_creates_persisted_task,test_virtual_session_registers_task
    agent_client_with_db(tmp_path;monkeypatch)
    test_startup_marks_orphan_tasks_stale(agent_client_with_db)
    test_sampler_creates_persisted_task(agent_client_with_db;tmp_path;monkeypatch)
    test_virtual_session_registers_task(agent_client_with_db)
  tests/test_agent_terminal_session.py:
    e: test_agent_open_terminal_session_and_find
    test_agent_open_terminal_session_and_find()
  tests/test_ax_invoke.py:
    e: _submit_button,_search_field,test_ax_deps_unavailable_on_linux,test_ax_find_element_by_title,test_ax_click,test_ax_set_value,test_ax_focus,test_ax_fallback_when_unavailable_on_linux
    _submit_button()
    _search_field()
    test_ax_deps_unavailable_on_linux()
    test_ax_find_element_by_title()
    test_ax_click()
    test_ax_set_value()
    test_ax_focus()
    test_ax_fallback_when_unavailable_on_linux()
  tests/test_browser_engine_profiles.py:
    e: test_normalize_browser_engine_aliases,test_browser_engine_application_profiles_exist,test_browser_session_stores_engine,test_infer_browser_firefox_profile_from_session,test_routing_prefers_browser_with_firefox_session,test_web_spa_fallback_without_engine_session,test_dsl_browser_open_vendor_flag,test_diagnose_control_includes_browser_engine,test_builtin_provider_count_unchanged,test_dispatch_browser_open_passes_engine
    test_normalize_browser_engine_aliases()
    test_browser_engine_application_profiles_exist()
    test_browser_session_stores_engine(monkeypatch)
    test_infer_browser_firefox_profile_from_session(monkeypatch)
    test_routing_prefers_browser_with_firefox_session(monkeypatch)
    test_web_spa_fallback_without_engine_session()
    test_dsl_browser_open_vendor_flag()
    test_diagnose_control_includes_browser_engine(monkeypatch)
    test_builtin_provider_count_unchanged()
    test_dispatch_browser_open_passes_engine(monkeypatch)
  tests/test_browser_session_detached.py:
    e: clean_web1,test_detached_session_survives_registry_reset
    clean_web1()
    test_detached_session_survives_registry_reset(monkeypatch;clean_web1)
  tests/test_capture_all_monitors.py:
    e: _make_png,test_capture_all_monitors_uses_single_screencast_frame
    _make_png(width;height;color)
    test_capture_all_monitors_uses_single_screencast_frame(monkeypatch;tmp_path)
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
  tests/test_cli_control_args.py:
    e: test_control_list_accepts_session_id,test_diagnose_control_accepts_selector_and_session_id,test_selector_from_kwargs_merges_session_id_after_css_parse,test_control_browser_open_parser,test_control_click_does_not_duplicate_backend,test_control_list_invokes_service_with_session_id
    test_control_list_accepts_session_id()
    test_diagnose_control_accepts_selector_and_session_id()
    test_selector_from_kwargs_merges_session_id_after_css_parse()
    test_control_browser_open_parser()
    test_control_click_does_not_duplicate_backend(monkeypatch)
    test_control_list_invokes_service_with_session_id(monkeypatch)
  tests/test_cli_session.py:
    e: test_root_parser_accepts_audit_session_flags,test_apply_cli_session_args_sets_env,test_enrich_command_request_uses_env_session_id,test_artifacts_from_screenshot_paths,test_artifacts_from_control_preview_and_diff,test_executor_records_control_cli_step,test_build_artifacts_for_screenshot_verb
    test_root_parser_accepts_audit_session_flags()
    test_apply_cli_session_args_sets_env(monkeypatch)
    test_enrich_command_request_uses_env_session_id(monkeypatch)
    test_artifacts_from_screenshot_paths(tmp_path)
    test_artifacts_from_control_preview_and_diff(tmp_path)
    test_executor_records_control_cli_step(monkeypatch;tmp_path)
    test_build_artifacts_for_screenshot_verb(tmp_path)
  tests/test_client_request.py:
    e: test_route_command_health,test_route_command_windows_query,test_request_delegates_to_http
    test_route_command_health()
    test_route_command_windows_query()
    test_request_delegates_to_http(monkeypatch)
  tests/test_command_contract.py:
    e: test_command_request_from_dsl_monitors,test_command_request_from_dsl_apps_only,test_command_result_envelope_success,test_command_result_envelope_failure,test_command_request_from_dsl_control_click,test_command_result_to_dsl_result
    test_command_request_from_dsl_monitors()
    test_command_request_from_dsl_apps_only()
    test_command_result_envelope_success()
    test_command_result_envelope_failure()
    test_command_request_from_dsl_control_click()
    test_command_result_to_dsl_result()
  tests/test_control_agent.py:
    e: test_agent_control_diagnostics,test_agent_controls_list
    test_agent_control_diagnostics(agent_client;monkeypatch)
    test_agent_controls_list(agent_client;monkeypatch)
  tests/test_control_app_matching.py:
    e: _node,test_app_matches_process_name,test_app_matches_window_title,test_window_title_selector
    _node(node_id)
    test_app_matches_process_name()
    test_app_matches_window_title()
    test_window_title_selector()
  tests/test_control_atspi.py:
    e: _probe_atspi_integration,_atspi_integration_ready,atspi_provider,test_atspi_snapshot_lists_nodes,test_controls_list_cli_integration
    _probe_atspi_integration()
    _atspi_integration_ready()
    atspi_provider()
    test_atspi_snapshot_lists_nodes(atspi_provider)
    test_controls_list_cli_integration(atspi_provider)
  tests/test_control_browser.py:
    e: test_browser_provider_snapshot_and_find,test_browser_provider_actions,test_resolve_browser_backend_with_injected_page,test_resolve_browser_backend_without_playwright
    test_browser_provider_snapshot_and_find()
    test_browser_provider_actions()
    test_resolve_browser_backend_with_injected_page()
    test_resolve_browser_backend_without_playwright(monkeypatch)
  tests/test_control_browser_session.py:
    e: registry,test_browser_registry_open_mock_and_close,test_provider_requires_session_without_legacy_page,test_provider_uses_registry_session,test_browser_session_scoring_ineligible_without_open_session
    registry(monkeypatch)
    test_browser_registry_open_mock_and_close(registry)
    test_provider_requires_session_without_legacy_page(registry)
    test_provider_uses_registry_session(registry)
    test_browser_session_scoring_ineligible_without_open_session(monkeypatch)
  tests/test_control_browser_verify.py:
    e: test_dom_verify_set_value
    test_dom_verify_set_value()
  tests/test_control_capabilities.py:
    e: test_element_capabilities_roundtrip,test_control_node_serializes_capabilities_and_actions,test_atspi_snapshot_deserializes_actions_and_capabilities
    test_element_capabilities_roundtrip()
    test_control_node_serializes_capabilities_and_actions()
    test_atspi_snapshot_deserializes_actions_and_capabilities(monkeypatch)
  tests/test_control_executor.py:
    e: test_executor_control_click_local,test_executor_controls_find_local,test_executor_diagnose_control_local
    test_executor_control_click_local(monkeypatch)
    test_executor_controls_find_local(monkeypatch)
    test_executor_diagnose_control_local(monkeypatch)
  tests/test_control_gtk_demo.py:
    e: _atspi_available,_display_available,_app_selector,_find_selector,_find_increment,_wait_for_gtk_demo,_ensure_gtk_demo_ready,gtk_demo_session,gtk_demo_process,gtk_demo_window,test_gtk_demo_find_increment_button,test_gtk_demo_list_by_window_title,test_gtk_demo_click_verify_label,test_gtk_demo_set_value_verify,GtkDemoSession
    GtkDemoSession:
    _atspi_available()
    _display_available()
    _app_selector()
    _find_selector()
    _find_increment()
    _wait_for_gtk_demo()
    _ensure_gtk_demo_ready(session)
    gtk_demo_session()
    gtk_demo_process(gtk_demo_session)
    gtk_demo_window(gtk_demo_session)
    test_gtk_demo_find_increment_button(gtk_demo_window)
    test_gtk_demo_list_by_window_title(gtk_demo_window)
    test_gtk_demo_click_verify_label(gtk_demo_window)
    test_gtk_demo_set_value_verify(gtk_demo_window)
  tests/test_control_plugins.py:
    e: _reset_plugins,test_register_and_list_plugin,test_unregister_manual_plugin,test_extension_catalog_includes_plugins,_StubPluginProvider
    _StubPluginProvider: available(0),snapshot(0),find(1),invoke(1),focus(1),set_value(2),bounds(1)
    _reset_plugins()
    test_register_and_list_plugin()
    test_unregister_manual_plugin()
    test_extension_catalog_includes_plugins(agent_client)
  tests/test_control_policy.py:
    e: test_assess_control_capability_returns_contract
    test_assess_control_capability_returns_contract(monkeypatch)
  tests/test_control_policy_v2.py:
    e: _mock_ready,test_auto_prefers_atspi_for_desktop_selector,test_auto_prefers_terminal_for_terminal_context,test_auto_prefers_browser_for_dom_selector,test_terminal_ineligible_without_open_session,test_explicit_backend_respects_forced_provider,test_explicit_backend_raises_when_ineligible,test_rank_providers_orders_by_score,test_diagnose_control_includes_routing,test_routing_decision_serializes
    _mock_ready(monkeypatch)
    test_auto_prefers_atspi_for_desktop_selector(monkeypatch)
    test_auto_prefers_terminal_for_terminal_context(monkeypatch)
    test_auto_prefers_browser_for_dom_selector(monkeypatch)
    test_terminal_ineligible_without_open_session(monkeypatch)
    test_explicit_backend_respects_forced_provider(monkeypatch)
    test_explicit_backend_raises_when_ineligible(monkeypatch)
    test_rank_providers_orders_by_score(monkeypatch)
    test_diagnose_control_includes_routing(monkeypatch)
    test_routing_decision_serializes(monkeypatch)
  tests/test_control_screenshot_verify.py:
    e: _png,test_diff_png_detects_change,test_diff_png_identical_is_not_verified,test_diff_png_small_change_on_large_frame,test_verify_screenshot_pair_payload,test_capture_via_agent_when_configured,test_capture_control_screenshot_uses_target_region,test_execute_action_screenshot_verify_only,test_execute_action_dual_verify_requires_both
    _png(color)
    test_diff_png_detects_change()
    test_diff_png_identical_is_not_verified()
    test_diff_png_small_change_on_large_frame()
    test_verify_screenshot_pair_payload()
    test_capture_via_agent_when_configured(monkeypatch)
    test_capture_control_screenshot_uses_target_region()
    test_execute_action_screenshot_verify_only(monkeypatch)
    test_execute_action_dual_verify_requires_both(monkeypatch)
  tests/test_control_selector.py:
    e: _node,test_parse_selector_button_name,test_find_and_pick_match
    _node(node_id)
    test_parse_selector_button_name()
    test_find_and_pick_match()
  tests/test_control_selector_v2.py:
    e: _node,test_selector_roundtrip,test_parse_css_and_xpath,test_parse_window_title_and_text_attrs,test_find_by_accessibility_id_and_text,test_active_fields_per_environment
    _node(node_id)
    test_selector_roundtrip()
    test_parse_css_and_xpath()
    test_parse_window_title_and_text_attrs()
    test_find_by_accessibility_id_and_text()
    test_active_fields_per_environment()
  tests/test_control_set_value_verify.py:
    e: test_resolve_verify_mode_set_value_uses_ocr_contains_for_vision,test_build_action_payload_fails_ok_when_verify_false,test_control_set_value_verify_mode_ocr_contains
    test_resolve_verify_mode_set_value_uses_ocr_contains_for_vision()
    test_build_action_payload_fails_ok_when_verify_false()
    test_control_set_value_verify_mode_ocr_contains(monkeypatch)
  tests/test_control_terminal.py:
    e: _demo_registry,_seed_default_demo,test_terminal_screen_nodes,test_terminal_provider_snapshot_and_find,test_terminal_provider_actions,test_terminal_selector_parse_and_match,test_terminal_service_set_value,test_terminal_service_verify_text_change,test_resolve_provider_terminal_backend,test_resolve_provider_auto_routes_terminal_environment,test_resolve_provider_unknown_backend,test_terminal_service_missing_session_raises
    _demo_registry()
    _seed_default_demo()
    test_terminal_screen_nodes()
    test_terminal_provider_snapshot_and_find()
    test_terminal_provider_actions()
    test_terminal_selector_parse_and_match()
    test_terminal_service_set_value()
    test_terminal_service_verify_text_change()
    test_resolve_provider_terminal_backend()
    test_resolve_provider_auto_routes_terminal_environment()
    test_resolve_provider_unknown_backend()
    test_terminal_service_missing_session_raises()
  tests/test_control_verifier_hybrid.py:
    e: _png,test_verify_spec_from_dual_flags,test_hybrid_rescues_failed_semantic_with_visual,test_strict_dual_verify_still_requires_both,test_verifier_pipeline_semantic_only
    _png(color)
    test_verify_spec_from_dual_flags()
    test_hybrid_rescues_failed_semantic_with_visual(monkeypatch)
    test_strict_dual_verify_still_requires_both(monkeypatch)
    test_verifier_pipeline_semantic_only()
  tests/test_control_verify.py:
    e: _node,_gtk_demo_snapshots,test_diff_snapshots_detects_label_change,test_verify_click_detects_sibling_label_change,test_verify_click_with_verify_label,test_verify_label_falls_back_to_identity_when_structure_shifts,test_verify_click_with_verify_selector,test_verify_set_value_checks_expected_text,test_snapshot_diff_alias_matches_diff_snapshots,test_collect_changed_nodes_flattens_diff,test_verify_detects_focus_change_without_value_change,test_verify_fails_when_nothing_changes
    _node(node_id)
    _gtk_demo_snapshots()
    test_diff_snapshots_detects_label_change()
    test_verify_click_detects_sibling_label_change()
    test_verify_click_with_verify_label()
    test_verify_label_falls_back_to_identity_when_structure_shifts()
    test_verify_click_with_verify_selector()
    test_verify_set_value_checks_expected_text()
    test_snapshot_diff_alias_matches_diff_snapshots()
    test_collect_changed_nodes_flattens_diff()
    test_verify_detects_focus_change_without_value_change()
    test_verify_fails_when_nothing_changes()
  tests/test_coords_rotation.py:
    e: test_global_pointer_coords_rotated_left_aspect_mismatch,test_global_pointer_coords_monitor_1to1_on_normal_rotation
    test_global_pointer_coords_rotated_left_aspect_mismatch()
    test_global_pointer_coords_monitor_1to1_on_normal_rotation(monkeypatch)
  tests/test_cross_platform_providers.py:
    e: _mock_linux_readiness,_mock_platform,test_builtin_provider_count_includes_cross_platform_stubs,test_uia_stub_unavailable_on_linux,test_ax_stub_unavailable_on_linux,test_linux_desktop_routes_atspi_not_uia_or_ax,test_windows_desktop_routes_uia,test_macos_desktop_routes_ax,test_native_windows_profile_only_on_windows_host,test_uia_find_by_accessibility_id
    _mock_linux_readiness(monkeypatch)
    _mock_platform(monkeypatch)
    test_builtin_provider_count_includes_cross_platform_stubs()
    test_uia_stub_unavailable_on_linux()
    test_ax_stub_unavailable_on_linux()
    test_linux_desktop_routes_atspi_not_uia_or_ax(monkeypatch)
    test_windows_desktop_routes_uia(monkeypatch)
    test_macos_desktop_routes_ax(monkeypatch)
    test_native_windows_profile_only_on_windows_host(monkeypatch)
    test_uia_find_by_accessibility_id()
  tests/test_dsl_browser_open.py:
    e: test_parse_browser_open_session_alias,test_parse_browser_open_line,test_browser_open_schema_requires_url,test_command_request_from_dsl_browser_open,test_to_text_roundtrip_browser_open,test_dispatch_browser_open_local,test_browser_open_e2e_local,test_browser_open_enables_dom_provider_eligibility,test_agent_client_browser_open_route,test_dispatch_browser_open_via_executor
    test_parse_browser_open_session_alias()
    test_parse_browser_open_line()
    test_browser_open_schema_requires_url()
    test_command_request_from_dsl_browser_open()
    test_to_text_roundtrip_browser_open()
    test_dispatch_browser_open_local(monkeypatch)
    test_browser_open_e2e_local(monkeypatch)
    test_browser_open_enables_dom_provider_eligibility(monkeypatch)
    test_agent_client_browser_open_route()
    test_dispatch_browser_open_via_executor(monkeypatch)
  tests/test_dsl_terminal_control.py:
    e: test_dsl_terminal_set_value_end_to_end
    test_dsl_terminal_set_value_end_to_end(monkeypatch)
  tests/test_dsl_terminal_open.py:
    e: test_parse_terminal_open_line,test_command_request_from_dsl_terminal_open,test_dispatch_terminal_open_local,test_terminal_open_e2e_local,test_dispatch_terminal_open_via_executor
    test_parse_terminal_open_line()
    test_command_request_from_dsl_terminal_open()
    test_dispatch_terminal_open_local(monkeypatch)
    test_terminal_open_e2e_local()
    test_dispatch_terminal_open_via_executor(monkeypatch)
  tests/test_example_control_plugin.py:
    e: _reset_plugins,test_echo_provider_contract,test_register_plugin_via_entry_point_helper,test_unregister_echo_restores_builtin_count,test_echo_routing_eligible_with_forced_backend
    _reset_plugins()
    test_echo_provider_contract()
    test_register_plugin_via_entry_point_helper()
    test_unregister_echo_restores_builtin_count()
    test_echo_routing_eligible_with_forced_backend(monkeypatch)
  tests/test_example_uia_ax_plugins.py:
    e: _reset_plugins,_mock_readiness,test_example_uia_mock_contract,test_example_ax_mock_contract,test_register_uia_plugin_via_entry_point,test_register_ax_plugin_via_entry_point,test_unregister_example_plugins_restores_builtin_count,test_example_uia_forced_routing,test_example_ax_forced_routing
    _reset_plugins()
    _mock_readiness(monkeypatch)
    test_example_uia_mock_contract()
    test_example_ax_mock_contract()
    test_register_uia_plugin_via_entry_point()
    test_register_ax_plugin_via_entry_point()
    test_unregister_example_plugins_restores_builtin_count()
    test_example_uia_forced_routing(monkeypatch)
    test_example_ax_forced_routing(monkeypatch)
  tests/test_execution_policy.py:
    e: test_execution_policy_routes_to_agent_when_url_set,test_execution_policy_routes_local_inside_broker,test_execution_policy_routes_local_without_url,test_execute_health_local,test_execute_monitors_via_agent
    test_execution_policy_routes_to_agent_when_url_set(monkeypatch)
    test_execution_policy_routes_local_inside_broker(monkeypatch)
    test_execution_policy_routes_local_without_url(monkeypatch)
    test_execute_health_local(monkeypatch)
    test_execute_monitors_via_agent(monkeypatch)
  tests/test_gui_map.py:
    e: _fake_png,test_action_bounds_expands_narrow_ocr_box,test_element_from_ocr_box_records_raw_and_action_bounds,test_build_and_load_gui_map_roundtrip,test_map_markdown_and_svg_export,test_verify_hints_from_map_element,test_resolve_map_verify_mode_prefers_vision_only_paths,test_map_action_verify_uses_resolved_mode_not_semantic,test_map_based_control_click_uses_stored_click_point
    _fake_png()
    test_action_bounds_expands_narrow_ocr_box()
    test_element_from_ocr_box_records_raw_and_action_bounds()
    test_build_and_load_gui_map_roundtrip(tmp_path;monkeypatch)
    test_map_markdown_and_svg_export()
    test_verify_hints_from_map_element()
    test_resolve_map_verify_mode_prefers_vision_only_paths()
    test_map_action_verify_uses_resolved_mode_not_semantic(monkeypatch;tmp_path)
    test_map_based_control_click_uses_stored_click_point(monkeypatch;tmp_path)
  tests/test_gui_map_diff.py:
    e: _fake_png,_sample_pack,test_match_ocr_box_for_element_prefers_label_and_nearest,test_diff_gui_map_ok_when_stable,test_diff_gui_map_detects_bounds_drift,test_diff_gui_map_detects_missing_anchor,test_refresh_gui_map_updates_bounds,test_map_diff_service,test_assess_map_drift_refresh_required_on_many_missing,test_build_gui_map_scoped_crop_filters_outside_boxes,test_map_capture_prefers_agent_screencast,test_map_capture_requires_screencast_when_agent_running
    _fake_png()
    _sample_pack(png)
    test_match_ocr_box_for_element_prefers_label_and_nearest()
    test_diff_gui_map_ok_when_stable(monkeypatch)
    test_diff_gui_map_detects_bounds_drift(monkeypatch)
    test_diff_gui_map_detects_missing_anchor(monkeypatch)
    test_refresh_gui_map_updates_bounds(monkeypatch;tmp_path)
    test_map_diff_service(tmp_path;monkeypatch)
    test_assess_map_drift_refresh_required_on_many_missing()
    test_build_gui_map_scoped_crop_filters_outside_boxes(monkeypatch)
    test_map_capture_prefers_agent_screencast(monkeypatch)
    test_map_capture_requires_screencast_when_agent_running(monkeypatch)
  tests/test_host_capture.py:
    e: test_capture_host_png_prefers_mirror
    test_capture_host_png_prefers_mirror(monkeypatch)
  tests/test_host_capture_errors.py:
    e: test_host_capture_error_mentions_screencast_on_wayland,test_capture_host_png_records_inactive_screencast
    test_host_capture_error_mentions_screencast_on_wayland(monkeypatch)
    test_capture_host_png_records_inactive_screencast(monkeypatch)
  tests/test_img2nl_enrich.py:
    e: _make_png,test_enrich_screenshot_payload_adds_nl,test_execute_screenshot_enriches_when_img2nl_available,test_execute_screenshot_skip_img2nl
    _make_png(width;height;color)
    test_enrich_screenshot_payload_adds_nl(monkeypatch;tmp_path)
    test_execute_screenshot_enriches_when_img2nl_available(monkeypatch;tmp_path)
    test_execute_screenshot_skip_img2nl(monkeypatch;tmp_path)
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
  tests/test_portal_screencast.py:
    e: _make_png,test_screencast_session_capture_requires_ready,_stub_ready_session,test_host_capture_uses_active_screencast,test_agent_screencast_status_endpoint,test_stop_screencast_when_inactive,test_portal_request_path_uses_bus_unique_name,test_stream_target_prefers_pipewire_serial,test_cli_agent_screencast_status,test_agent_capture_uses_store_screencast,test_capture_pipewire_stream_uses_num_buffers,test_agent_client_screencast_status
    _make_png(width;height;color)
    test_screencast_session_capture_requires_ready()
    _stub_ready_session(png)
    test_host_capture_uses_active_screencast(monkeypatch)
    test_agent_screencast_status_endpoint(agent_client)
    test_stop_screencast_when_inactive()
    test_portal_request_path_uses_bus_unique_name()
    test_stream_target_prefers_pipewire_serial()
    test_cli_agent_screencast_status(live_agent_url;monkeypatch;capsys)
    test_agent_capture_uses_store_screencast(agent_client;monkeypatch;tmp_path)
    test_capture_pipewire_stream_uses_num_buffers(monkeypatch)
    test_agent_client_screencast_status(live_agent_url;monkeypatch)
  tests/test_profile_inference.py:
    e: test_infer_web_spa_from_dom_css,test_infer_terminal_pty_from_coordinates,test_infer_native_gtk_from_role,test_infer_vision_from_anchor,test_profile_boost_prefers_browser_for_web_spa,test_router_includes_application_profile,test_profile_for_builtin_ids
    test_infer_web_spa_from_dom_css()
    test_infer_terminal_pty_from_coordinates()
    test_infer_native_gtk_from_role()
    test_infer_vision_from_anchor()
    test_profile_boost_prefers_browser_for_web_spa(monkeypatch)
    test_router_includes_application_profile(monkeypatch)
    test_profile_for_builtin_ids()
  tests/test_relay_release.py:
    e: _toolbox_states,test_state_matches_app_jetbrains,test_select_adopted_for_release_by_app_includes_frame,test_stash_roundtrip
    _toolbox_states()
    test_state_matches_app_jetbrains()
    test_select_adopted_for_release_by_app_includes_frame()
    test_stash_roundtrip(tmp_path;monkeypatch)
  tests/test_relay_window_region.py:
    e: _make_png,test_relay_screenshot_crops_window_region,test_resolve_window_region_requires_match
    _make_png(width;height;color)
    test_relay_screenshot_crops_window_region(monkeypatch;tmp_path)
    test_resolve_window_region_requires_match(monkeypatch)
  tests/test_routing_semantics.py:
    e: test_infer_target_environment_mapping,test_build_routing_semantics_browser_requires_session,test_build_routing_semantics_vision_anchor_visible,test_x11_provider_ineligible_on_wayland_host_without_xwayland,test_x11_provider_eligible_on_wayland_host_with_xwayland,test_routing_decision_includes_semantics,test_assess_control_capability_includes_host_environment,test_assess_control_capability_blocks_pointer_on_wayland,test_assess_control_capability_allows_pointer_via_xwayland,test_capture_policy_includes_host_environment,test_diagnose_unattended_includes_host_environment,test_diagnose_control_includes_routing_semantics,test_execution_policy_meta_includes_host_environment
    test_infer_target_environment_mapping()
    test_build_routing_semantics_browser_requires_session()
    test_build_routing_semantics_vision_anchor_visible()
    test_x11_provider_ineligible_on_wayland_host_without_xwayland(monkeypatch)
    test_x11_provider_eligible_on_wayland_host_with_xwayland(monkeypatch)
    test_routing_decision_includes_semantics(monkeypatch)
    test_assess_control_capability_includes_host_environment()
    test_assess_control_capability_blocks_pointer_on_wayland(monkeypatch)
    test_assess_control_capability_allows_pointer_via_xwayland(monkeypatch)
    test_capture_policy_includes_host_environment(monkeypatch)
    test_diagnose_unattended_includes_host_environment(monkeypatch)
    test_diagnose_control_includes_routing_semantics(monkeypatch)
    test_execution_policy_meta_includes_host_environment()
  tests/test_sampler_policy.py:
    e: test_assess_unattended_virtual_display,test_assess_unattended_wayland_without_screencast,test_assess_unattended_wayland_with_screencast,test_assess_unattended_uses_in_process_screencast,test_diagnose_unattended_includes_contract,test_sampler_strict_virtual
    test_assess_unattended_virtual_display()
    test_assess_unattended_wayland_without_screencast(monkeypatch)
    test_assess_unattended_wayland_with_screencast(monkeypatch)
    test_assess_unattended_uses_in_process_screencast(monkeypatch)
    test_diagnose_unattended_includes_contract(monkeypatch)
    test_sampler_strict_virtual(tmp_path;monkeypatch)
  tests/test_sampler_recovery.py:
    e: _stub_contract,test_is_screencast_recoverable_error,test_sampler_recovers_from_blank_screencast,test_sampler_marks_reconsent_when_recovery_fails
    _stub_contract(monkeypatch)
    test_is_screencast_recoverable_error()
    test_sampler_recovers_from_blank_screencast(tmp_path;monkeypatch)
    test_sampler_marks_reconsent_when_recovery_fails(tmp_path;monkeypatch)
  tests/test_screencast_multiple.py:
    e: test_screencast_multiple_explicit,test_screencast_multiple_env
    test_screencast_multiple_explicit()
    test_screencast_multiple_env(monkeypatch)
  tests/test_screenshot_meta.py:
    e: test_describe_screenshot_nl,test_build_and_meta_path
    test_describe_screenshot_nl()
    test_build_and_meta_path(tmp_path)
  tests/test_screenshot_routing.py:
    e: test_resolve_screenshot_routing_host_with_source,test_resolve_screenshot_routing_explicit_virtual,test_resolve_screenshot_routing_virtual_display_override,test_local_screenshot_handler_uses_host_for_source,test_agent_screenshot_handler_uses_host_for_source
    test_resolve_screenshot_routing_host_with_source(monkeypatch)
    test_resolve_screenshot_routing_explicit_virtual(monkeypatch)
    test_resolve_screenshot_routing_virtual_display_override(monkeypatch)
    test_local_screenshot_handler_uses_host_for_source(monkeypatch)
    test_agent_screenshot_handler_uses_host_for_source(monkeypatch)
  tests/test_session_catalog.py:
    e: test_parse_session_kind_legacy_strings,test_build_catalog_from_agent_store,test_build_catalog_local_terminal,test_merge_catalogs_dedupes_by_id,_FakeHandle,_TerminalHandle
    _FakeHandle: info(0),capabilities(0)
    _TerminalHandle: info(0),capabilities(0)
    test_parse_session_kind_legacy_strings()
    test_build_catalog_from_agent_store()
    test_build_catalog_local_terminal()
    test_merge_catalogs_dedupes_by_id()
  tests/test_session_recorder.py:
    e: test_session_recording_disabled_by_default,test_executor_writes_session_dir,test_collect_artifacts_from_explicit_and_data,test_render_readme_includes_routing
    test_session_recording_disabled_by_default(monkeypatch)
    test_executor_writes_session_dir(monkeypatch;tmp_path)
    test_collect_artifacts_from_explicit_and_data(tmp_path)
    test_render_readme_includes_routing()
  tests/test_uia_invoke.py:
    e: _ok_button,_name_field,test_uia_deps_unavailable_on_linux,test_uia_find_element_by_name,test_uia_find_by_accessibility_id,test_uia_click_invoke_pattern,test_uia_set_value,test_uia_focus,test_uia_fallback_when_unavailable_on_linux
    _ok_button()
    _name_field()
    test_uia_deps_unavailable_on_linux()
    test_uia_find_element_by_name()
    test_uia_find_by_accessibility_id()
    test_uia_click_invoke_pattern()
    test_uia_set_value()
    test_uia_focus()
    test_uia_fallback_when_unavailable_on_linux()
  tests/test_vision_anchor_matching.py:
    e: _boxes,test_anchor_spatial_relation_right_of,test_anchor_spatial_relation_below,test_anchor_spatial_find_right_of_target,test_anchor_spatial_find_below_target,test_anchor_based_find_alias,test_anchor_fallback_when_ocr_misses,test_vision_find_anchor_spatial_integration,test_ocr_anchor_combined_find_without_template
    _boxes()
    test_anchor_spatial_relation_right_of()
    test_anchor_spatial_relation_below()
    test_anchor_spatial_find_right_of_target()
    test_anchor_spatial_find_below_target()
    test_anchor_based_find_alias()
    test_anchor_fallback_when_ocr_misses(monkeypatch)
    test_vision_find_anchor_spatial_integration(monkeypatch)
    test_ocr_anchor_combined_find_without_template(monkeypatch)
  tests/test_vision_anchor_visible_verify.py:
    e: _png,_template_png,_ctx,test_anchor_visible_ocr_anchor_found,test_select_verify_provider_vision_uses_anchor_visible,test_anchor_visible_template_found
    _png()
    _template_png()
    _ctx()
    test_anchor_visible_ocr_anchor_found(monkeypatch)
    test_select_verify_provider_vision_uses_anchor_visible()
    test_anchor_visible_template_found(monkeypatch;tmp_path)
  tests/test_vision_llm.py:
    e: _png,test_vision_llm_fallback_enabled_requires_mode_and_key,test_verify_text_in_region_parses_yes,test_verifier_vision_llm_fallback_only_when_ocr_fails,test_verifier_skips_vision_llm_when_ocr_succeeds
    _png(color)
    test_vision_llm_fallback_enabled_requires_mode_and_key(monkeypatch)
    test_verify_text_in_region_parses_yes(monkeypatch)
    test_verifier_vision_llm_fallback_only_when_ocr_fails(monkeypatch)
    test_verifier_skips_vision_llm_when_ocr_succeeds(monkeypatch)
  tests/test_vision_multimatch_disambiguation.py:
    e: _boxes_duplicate_anchors,test_filter_by_confidence_drops_weak_matches,test_pick_by_index_selects_nth_match,test_resolve_vision_matches_applies_threshold_and_sort,test_anchor_spatial_find_uses_anchor_index,test_vision_ocr_index_picks_second_submit,test_resolve_target_spatial_anchor_index_is_anchor_only,test_vision_template_min_confidence_filters
    _boxes_duplicate_anchors()
    test_filter_by_confidence_drops_weak_matches()
    test_pick_by_index_selects_nth_match()
    test_resolve_vision_matches_applies_threshold_and_sort()
    test_anchor_spatial_find_uses_anchor_index()
    test_vision_ocr_index_picks_second_submit(monkeypatch)
    test_resolve_target_spatial_anchor_index_is_anchor_only(monkeypatch)
    test_vision_template_min_confidence_filters(monkeypatch;tmp_path)
  tests/test_vision_ocr_invoke.py:
    e: _fake_png,_mock_ocr_boxes,test_match_selector_boxes_vision_anchor_fuzzy,test_match_selector_boxes_text_exact,test_vision_find_ocr_returns_bounds,test_vision_invoke_clicks_expanded_ocr_bounds,test_vision_set_value_types_after_click,test_vision_set_value_chat_anchor_skips_gnome_hotkey,test_vision_ocr_miss_returns_empty_find,test_vision_only_surface_still_routes_x11_when_ocr_ready,test_ocr_find_selector_with_mocked_ocr_png
    _fake_png()
    _mock_ocr_boxes(monkeypatch;boxes)
    test_match_selector_boxes_vision_anchor_fuzzy()
    test_match_selector_boxes_text_exact()
    test_vision_find_ocr_returns_bounds(monkeypatch)
    test_vision_invoke_clicks_expanded_ocr_bounds(monkeypatch)
    test_vision_set_value_types_after_click(monkeypatch)
    test_vision_set_value_chat_anchor_skips_gnome_hotkey(monkeypatch)
    test_vision_ocr_miss_returns_empty_find(monkeypatch)
    test_vision_only_surface_still_routes_x11_when_ocr_ready(monkeypatch)
    test_ocr_find_selector_with_mocked_ocr_png(monkeypatch)
  tests/test_vision_preview.py:
    e: _fake_png,_vision_node,test_render_match_overlay_draws_boxes,test_build_vision_preview_json_and_file,test_action_pick_index_spatial_anchor_uses_zero_for_highlight,test_controls_find_preview_integration,test_preview_matches_from_nodes_skips_empty_bounds
    _fake_png(width;height)
    _vision_node()
    test_render_match_overlay_draws_boxes()
    test_build_vision_preview_json_and_file(tmp_path)
    test_action_pick_index_spatial_anchor_uses_zero_for_highlight()
    test_controls_find_preview_integration(monkeypatch;tmp_path)
    test_preview_matches_from_nodes_skips_empty_bounds()
  tests/test_vision_provider_stub.py:
    e: _mock_readiness,test_vision_stub_provider_available,test_vision_stub_find_by_anchor,test_builtin_provider_count_no_per_engine_explosion,test_infer_vision_only_surface_profile,test_vision_only_surface_routes_to_x11,test_vision_provider_stub_anchor_without_ocr,test_routing_semantics_vision_requires_no_session,test_vision_routing_on_wayland_host,test_x11_fallback_boost_for_vision_profile
    _mock_readiness(monkeypatch)
    test_vision_stub_provider_available()
    test_vision_stub_find_by_anchor(monkeypatch)
    test_builtin_provider_count_no_per_engine_explosion()
    test_infer_vision_only_surface_profile()
    test_vision_only_surface_routes_to_x11(monkeypatch)
    test_vision_provider_stub_anchor_without_ocr(monkeypatch)
    test_routing_semantics_vision_requires_no_session()
    test_vision_routing_on_wayland_host(monkeypatch)
    test_x11_fallback_boost_for_vision_profile(monkeypatch)
  tests/test_vision_template_matching.py:
    e: _template_png,_screen_with_template_at,test_match_template_finds_embedded_pattern,test_vision_find_template_returns_bounds,test_template_match_threshold_tuning,test_vision_invoke_clicks_template_center
    _template_png()
    _screen_with_template_at(x;y)
    test_match_template_finds_embedded_pattern()
    test_vision_find_template_returns_bounds(monkeypatch;tmp_path)
    test_template_match_threshold_tuning()
    test_vision_invoke_clicks_template_center(monkeypatch;tmp_path)
  tests/test_wayland_capture_fastfail.py:
    e: _black_png,test_blank_screencast_invalidates_session,test_wayland_host_capture_skips_slow_driver_fallback
    _black_png()
    test_blank_screencast_invalidates_session(monkeypatch)
    test_wayland_host_capture_skips_slow_driver_fallback(monkeypatch)
  tests/test_wayland_input.py:
    e: test_enrich_screencast_stream_meta_from_agent,test_global_pointer_coords_screencast_stream,test_global_pointer_coords_region_scale,test_global_pointer_coords_monitor_1to1_on_rotation,test_global_pointer_coords_local_fallback,test_resolve_pointer_input_prefers_ydotool_on_wayland,test_resolve_pointer_input_xdotool_on_x11,test_vision_pointer_click_uses_ydotool_on_wayland
    test_enrich_screencast_stream_meta_from_agent(monkeypatch)
    test_global_pointer_coords_screencast_stream()
    test_global_pointer_coords_region_scale()
    test_global_pointer_coords_monitor_1to1_on_rotation(monkeypatch)
    test_global_pointer_coords_local_fallback()
    test_resolve_pointer_input_prefers_ydotool_on_wayland(monkeypatch)
    test_resolve_pointer_input_xdotool_on_x11(monkeypatch)
    test_vision_pointer_click_uses_ydotool_on_wayland(monkeypatch)
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
project_metadata('vdisplay', '0.1.14', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 55, 'less').
project_file('brain/scratch_atspi.py', 19, 'python').
project_file('examples/agent-broker/broker_demo.py', 58, 'python').
project_file('examples/agent-broker/run.sh', 27, 'shell').
project_file('examples/ci-agent/agent.py', 74, 'python').
project_file('examples/common/host_capture.py', 30, 'python').
project_file('examples/common/screenshot_meta.py', 163, 'python').
project_file('examples/common/validate_artifacts.py', 85, 'python').
project_file('examples/control-plane/control_demo.py', 173, 'python').
project_file('examples/control-plugin/src/vdisplay_example_plugin/__init__.py', 28, 'python').
project_file('examples/control-plugin/src/vdisplay_example_plugin/my_provider.py', 93, 'python').
project_file('examples/control-plugin-ax/src/vdisplay_example_ax_plugin/__init__.py', 24, 'python').
project_file('examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py', 94, 'python').
project_file('examples/control-plugin-uia/src/vdisplay_example_uia_plugin/__init__.py', 24, 'python').
project_file('examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py', 95, 'python').
project_file('examples/headless-virtual/run_virtual.py', 64, 'python').
project_file('examples/host-mirror/mirror_demo.py', 98, 'python').
project_file('examples/host-mirror/run-host.sh', 26, 'shell').
project_file('examples/host-mirror/run.sh', 54, 'shell').
project_file('examples/host-relay/relay_demo.py', 138, 'python').
project_file('examples/host-relay/run-host.sh', 25, 'shell').
project_file('examples/host-relay/run.sh', 48, 'shell').
project_file('examples/run_all_examples.sh', 159, 'shell').
project_file('packages/cli2vdisplay/src/cli2vdisplay/cli.py', 35, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py', 5, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 138, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', 71, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 407, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py', 2, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 121, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 116, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/result.py', 27, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py', 54, 'python').
project_file('packages/dsl2vdisplay/tests/test_dsl_control.py', 170, 'python').
project_file('packages/dsl2vdisplay/tests/test_parity.py', 15, 'python').
project_file('packages/mcp2vdisplay/src/mcp2vdisplay/cli.py', 24, 'python').
project_file('packages/mcp2vdisplay/src/mcp2vdisplay/server.py', 96, 'python').
project_file('packages/nlp2vdisplay/src/nlp2vdisplay/cli.py', 42, 'python').
project_file('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 14, 'python').
project_file('packages/rest2vdisplay/src/rest2vdisplay/app.py', 88, 'python').
project_file('packages/rest2vdisplay/src/rest2vdisplay/cli.py', 36, 'python').
project_file('packages/uri2vdisplay/src/uri2vdisplay/cli.py', 31, 'python').
project_file('packages/uri2vdisplay/src/uri2vdisplay/decode.py', 32, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/__init__.py', 8, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/cli.py', 44, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 86, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/__init__.py', 16, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/auth.py', 25, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/capture.py', 33, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/control.py', 123, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/health.py', 77, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/sampler.py', 48, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/session.py', 137, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/tasks.py', 70, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/routes/windows.py', 42, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/runtime.py', 146, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/schemas.py', 85, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', 147, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/server.py', 31, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/__init__.py', 6, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py', 57, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', 97, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', 114, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/outputs.py', 20, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/relay.py', 33, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py', 184, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 263, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 182, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/windows.py', 32, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/session_store.py', 66, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/task_store.py', 198, 'python').
project_file('project.sh', 59, 'shell').
project_file('src/vdisplay/__init__.py', 13, 'python').
project_file('src/vdisplay/agent_config.py', 72, 'python').
project_file('src/vdisplay/agent_dispatch.py', 31, 'python').
project_file('src/vdisplay/agent_envelope.py', 18, 'python').
project_file('src/vdisplay/api.py', 194, 'python').
project_file('src/vdisplay/application/__init__.py', 15, 'python').
project_file('src/vdisplay/application/artifacts.py', 103, 'python').
project_file('src/vdisplay/application/commands.py', 371, 'python').
project_file('src/vdisplay/application/errors.py', 40, 'python').
project_file('src/vdisplay/application/executor.py', 68, 'python').
project_file('src/vdisplay/application/handlers/__init__.py', 7, 'python').
project_file('src/vdisplay/application/handlers/agent.py', 242, 'python').
project_file('src/vdisplay/application/handlers/control.py', 73, 'python').
project_file('src/vdisplay/application/handlers/local.py', 292, 'python').
project_file('src/vdisplay/application/runtime.py', 87, 'python').
project_file('src/vdisplay/application/services/__init__.py', 4, 'python').
project_file('src/vdisplay/application/services/capture.py', 183, 'python').
project_file('src/vdisplay/application/services/control.py', 761, 'python').
project_file('src/vdisplay/application/services/discovery.py', 240, 'python').
project_file('src/vdisplay/application/services/img2nl_enrich.py', 125, 'python').
project_file('src/vdisplay/application/services/info.py', 52, 'python').
project_file('src/vdisplay/application/services/map.py', 276, 'python').
project_file('src/vdisplay/application/services/sampler.py', 110, 'python').
project_file('src/vdisplay/application/services/sampler_loop.py', 281, 'python').
project_file('src/vdisplay/application/services/session.py', 327, 'python').
project_file('src/vdisplay/application/session_context.py', 33, 'python').
project_file('src/vdisplay/application/session_recorder.py', 501, 'python').
project_file('src/vdisplay/backends/__init__.py', 2, 'python').
project_file('src/vdisplay/backends/base.py', 65, 'python').
project_file('src/vdisplay/backends/linux_x11_mirror.py', 260, 'python').
project_file('src/vdisplay/backends/linux_x11_relay.py', 479, 'python').
project_file('src/vdisplay/backends/linux_xvfb.py', 165, 'python').
project_file('src/vdisplay/backends/mirror_stub.py', 35, 'python').
project_file('src/vdisplay/capture/__init__.py', 16, 'python').
project_file('src/vdisplay/capture/base.py', 10, 'python').
project_file('src/vdisplay/capture/host.py', 556, 'python').
project_file('src/vdisplay/capture/linux_xwd.py', 321, 'python').
project_file('src/vdisplay/capture/policy.py', 141, 'python').
project_file('src/vdisplay/capture/portal.py', 222, 'python').
project_file('src/vdisplay/capture/portal_screencast.py', 780, 'python').
project_file('src/vdisplay/capture/providers/__init__.py', 4, 'python').
project_file('src/vdisplay/capture/providers/base.py', 23, 'python').
project_file('src/vdisplay/capture/providers/drm.py', 93, 'python').
project_file('src/vdisplay/capture/providers/engine.py', 100, 'python').
project_file('src/vdisplay/capture/providers/fbdev.py', 78, 'python').
project_file('src/vdisplay/capture/providers/mss.py', 69, 'python').
project_file('src/vdisplay/capture/providers/x11.py', 36, 'python').
project_file('src/vdisplay/cli.py', 37, 'python').
project_file('src/vdisplay/cli_handlers.py', 35, 'python').
project_file('src/vdisplay/client.py', 423, 'python').
project_file('src/vdisplay/commands/__init__.py', 47, 'python').
project_file('src/vdisplay/commands/agent.py', 156, 'python').
project_file('src/vdisplay/commands/all_cmd.py', 47, 'python').
project_file('src/vdisplay/commands/common.py', 138, 'python').
project_file('src/vdisplay/commands/control.py', 160, 'python').
project_file('src/vdisplay/commands/diagnose.py', 54, 'python').
project_file('src/vdisplay/commands/info.py', 17, 'python').
project_file('src/vdisplay/commands/io.py', 8, 'python').
project_file('src/vdisplay/commands/map.py', 99, 'python').
project_file('src/vdisplay/commands/mirror.py', 54, 'python').
project_file('src/vdisplay/commands/monitors.py', 20, 'python').
project_file('src/vdisplay/commands/nlp.py', 24, 'python').
project_file('src/vdisplay/commands/relay.py', 111, 'python').
project_file('src/vdisplay/commands/sampler.py', 133, 'python').
project_file('src/vdisplay/commands/screenshot.py', 54, 'python').
project_file('src/vdisplay/commands/session.py', 80, 'python').
project_file('src/vdisplay/commands/virtual.py', 82, 'python').
project_file('src/vdisplay/commands/windows.py', 30, 'python').
project_file('src/vdisplay/control/__init__.py', 70, 'python').
project_file('src/vdisplay/control/action_bounds.py', 25, 'python').
project_file('src/vdisplay/control/base.py', 70, 'python').
project_file('src/vdisplay/control/browser_engine.py', 56, 'python').
project_file('src/vdisplay/control/browser_session_store.py', 197, 'python').
project_file('src/vdisplay/control/capabilities.py', 77, 'python').
project_file('src/vdisplay/control/contracts.py', 165, 'python').
project_file('src/vdisplay/control/descriptors.py', 465, 'python').
project_file('src/vdisplay/control/engine.py', 68, 'python').
project_file('src/vdisplay/control/gui_map.py', 517, 'python').
project_file('src/vdisplay/control/gui_map_diff.py', 501, 'python').
project_file('src/vdisplay/control/gui_map_export.py', 180, 'python').
project_file('src/vdisplay/control/models.py', 188, 'python').
project_file('src/vdisplay/control/plugins.py', 164, 'python').
project_file('src/vdisplay/control/policy.py', 243, 'python').
project_file('src/vdisplay/control/profile_inference.py', 272, 'python').
project_file('src/vdisplay/control/providers/__init__.py', 19, 'python').
project_file('src/vdisplay/control/providers/atspi.py', 241, 'python').
project_file('src/vdisplay/control/providers/atspi_impl.py', 414, 'python').
project_file('src/vdisplay/control/providers/ax.py', 170, 'python').
project_file('src/vdisplay/control/providers/ax_impl.py', 270, 'python').
project_file('src/vdisplay/control/providers/browser_playwright.py', 340, 'python').
project_file('src/vdisplay/control/providers/browser_session.py', 247, 'python').
project_file('src/vdisplay/control/providers/terminal.py', 148, 'python').
project_file('src/vdisplay/control/providers/terminal_screen.py', 261, 'python').
project_file('src/vdisplay/control/providers/terminal_session.py', 228, 'python').
project_file('src/vdisplay/control/providers/uia.py', 170, 'python').
project_file('src/vdisplay/control/providers/uia_impl.py', 300, 'python').
project_file('src/vdisplay/control/providers/vision/__init__.py', 4, 'python').
project_file('src/vdisplay/control/providers/vision/provider.py', 705, 'python').
project_file('src/vdisplay/control/providers/x11.py', 141, 'python').
project_file('src/vdisplay/control/registry.py', 118, 'python').
project_file('src/vdisplay/control/router.py', 272, 'python').
project_file('src/vdisplay/control/routing_semantics.py', 159, 'python').
project_file('src/vdisplay/control/scoring.py', 802, 'python').
project_file('src/vdisplay/control/screenshot_verify.py', 266, 'python').
project_file('src/vdisplay/control/selector.py', 348, 'python').
project_file('src/vdisplay/control/session.py', 217, 'python').
project_file('src/vdisplay/control/session_kind.py', 16, 'python').
project_file('src/vdisplay/control/verifier.py', 568, 'python').
project_file('src/vdisplay/control/verify.py', 499, 'python').
project_file('src/vdisplay/control/verify_strategy.py', 17, 'python').
project_file('src/vdisplay/control/vision_disambiguate.py', 79, 'python').
project_file('src/vdisplay/control/vision_llm.py', 237, 'python').
project_file('src/vdisplay/control/vision_ocr.py', 316, 'python').
project_file('src/vdisplay/control/vision_preview.py', 239, 'python').
project_file('src/vdisplay/control/vision_template.py', 259, 'python').
project_file('src/vdisplay/discovery.py', 364, 'python').
project_file('src/vdisplay/exceptions.py', 11, 'python').
project_file('src/vdisplay/input/__init__.py', 12, 'python').
project_file('src/vdisplay/input/coords.py', 220, 'python').
project_file('src/vdisplay/input/linux_xdotool.py', 69, 'python').
project_file('src/vdisplay/input/linux_ydotool.py', 115, 'python').
project_file('src/vdisplay/input/resolve.py', 28, 'python').
project_file('src/vdisplay/models.py', 27, 'python').
project_file('src/vdisplay/nl.py', 159, 'python').
project_file('src/vdisplay/nlp.py', 159, 'python').
project_file('src/vdisplay/payloads.py', 87, 'python').
project_file('src/vdisplay/utils.py', 69, 'python').
project_file('src/vdisplay/windows/__init__.py', 47, 'python').
project_file('src/vdisplay/windows/constants.py', 20, 'python').
project_file('src/vdisplay/windows/filter.py', 174, 'python').
project_file('src/vdisplay/windows/normalize.py', 104, 'python').
project_file('src/vdisplay/windows/query.py', 210, 'python').
project_file('src/vdisplay/windows/rank.py', 44, 'python').
project_file('src/vdisplay/windows/scan.py', 111, 'python').
project_file('tests/conftest.py', 87, 'python').
project_file('tests/contract/test_contracts.py', 41, 'python').
project_file('tests/contract/test_descriptors.py', 79, 'python').
project_file('tests/contract/test_providers.py', 70, 'python').
project_file('tests/fixtures/__init__.py', 2, 'python').
project_file('tests/fixtures/fake_browser.py', 93, 'python').
project_file('tests/fixtures/gtk_demo_app.py', 61, 'python').
project_file('tests/fixtures/run_gtk_demo.sh', 12, 'shell').
project_file('tests/test_agent.py', 44, 'python').
project_file('tests/test_agent_api_contract.py', 43, 'python').
project_file('tests/test_agent_browser_session.py', 60, 'python').
project_file('tests/test_agent_client.py', 119, 'python').
project_file('tests/test_agent_dispatch.py', 53, 'python').
project_file('tests/test_agent_integration.py', 68, 'python').
project_file('tests/test_agent_sampler.py', 66, 'python').
project_file('tests/test_agent_serve_port.py', 67, 'python').
project_file('tests/test_agent_tasks.py', 130, 'python').
project_file('tests/test_agent_terminal_session.py', 27, 'python').
project_file('tests/test_ax_invoke.py', 89, 'python').
project_file('tests/test_browser_engine_profiles.py', 190, 'python').
project_file('tests/test_browser_session_detached.py', 75, 'python').
project_file('tests/test_capture_all_monitors.py', 48, 'python').
project_file('tests/test_capture_crop.py', 50, 'python').
project_file('tests/test_capture_providers.py', 67, 'python').
project_file('tests/test_capture_xwd.py', 53, 'python').
project_file('tests/test_cli_commands.py', 97, 'python').
project_file('tests/test_cli_control_args.py', 103, 'python').
project_file('tests/test_cli_session.py', 109, 'python').
project_file('tests/test_client_request.py', 43, 'python').
project_file('tests/test_command_contract.py', 71, 'python').
project_file('tests/test_control_agent.py', 36, 'python').
project_file('tests/test_control_app_matching.py', 49, 'python').
project_file('tests/test_control_atspi.py', 52, 'python').
project_file('tests/test_control_browser.py', 52, 'python').
project_file('tests/test_control_browser_session.py', 56, 'python').
project_file('tests/test_control_browser_verify.py', 39, 'python').
project_file('tests/test_control_capabilities.py', 84, 'python').
project_file('tests/test_control_executor.py', 71, 'python').
project_file('tests/test_control_gtk_demo.py', 207, 'python').
project_file('tests/test_control_plugins.py', 107, 'python').
project_file('tests/test_control_policy.py', 39, 'python').
project_file('tests/test_control_policy_v2.py', 135, 'python').
project_file('tests/test_control_screenshot_verify.py', 227, 'python').
project_file('tests/test_control_selector.py', 36, 'python').
project_file('tests/test_control_selector_v2.py', 88, 'python').
project_file('tests/test_control_set_value_verify.py', 153, 'python').
project_file('tests/test_control_terminal.py', 184, 'python').
project_file('tests/test_control_verifier_hybrid.py', 200, 'python').
project_file('tests/test_control_verify.py', 265, 'python').
project_file('tests/test_coords_rotation.py', 39, 'python').
project_file('tests/test_cross_platform_providers.py', 179, 'python').
project_file('tests/test_dsl_browser_open.py', 176, 'python').
project_file('tests/test_dsl_terminal_control.py', 42, 'python').
project_file('tests/test_dsl_terminal_open.py', 69, 'python').
project_file('tests/test_example_control_plugin.py', 103, 'python').
project_file('tests/test_example_uia_ax_plugins.py', 145, 'python').
project_file('tests/test_execution_policy.py', 65, 'python').
project_file('tests/test_gui_map.py', 373, 'python').
project_file('tests/test_gui_map_diff.py', 210, 'python').
project_file('tests/test_host_capture.py', 43, 'python').
project_file('tests/test_host_capture_errors.py', 37, 'python').
project_file('tests/test_img2nl_enrich.py', 102, 'python').
project_file('tests/test_import.py', 23, 'python').
project_file('tests/test_linux_xvfb_integration.py', 22, 'python').
project_file('tests/test_mirror_primary.py', 43, 'python').
project_file('tests/test_nl.py', 145, 'python').
project_file('tests/test_nlp_pipeline.py', 67, 'python').
project_file('tests/test_outputs_rotation.py', 35, 'python').
project_file('tests/test_portal_screencast.py', 146, 'python').
project_file('tests/test_profile_inference.py', 79, 'python').
project_file('tests/test_relay_release.py', 66, 'python').
project_file('tests/test_relay_window_region.py', 70, 'python').
project_file('tests/test_routing_semantics.py', 239, 'python').
project_file('tests/test_sampler_policy.py', 91, 'python').
project_file('tests/test_sampler_recovery.py', 100, 'python').
project_file('tests/test_screencast_multiple.py', 20, 'python').
project_file('tests/test_screenshot_meta.py', 54, 'python').
project_file('tests/test_screenshot_routing.py', 105, 'python').
project_file('tests/test_session_catalog.py', 72, 'python').
project_file('tests/test_session_recorder.py', 112, 'python').
project_file('tests/test_uia_invoke.py', 98, 'python').
project_file('tests/test_vision_anchor_matching.py', 153, 'python').
project_file('tests/test_vision_anchor_visible_verify.py', 126, 'python').
project_file('tests/test_vision_llm.py', 181, 'python').
project_file('tests/test_vision_multimatch_disambiguation.py', 159, 'python').
project_file('tests/test_vision_ocr_invoke.py', 189, 'python').
project_file('tests/test_vision_preview.py', 126, 'python').
project_file('tests/test_vision_provider_stub.py', 164, 'python').
project_file('tests/test_vision_template_matching.py', 93, 'python').
project_file('tests/test_wayland_capture_fastfail.py', 65, 'python').
project_file('tests/test_wayland_input.py', 134, 'python').
project_file('tests/test_windows.py', 48, 'python').
project_file('tests/test_windows_dedupe.py', 26, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('examples/agent-broker/broker_demo.py', 'main', 0, 9, 17).
python_function('examples/ci-agent/agent.py', '_load_common', 0, 4, 6).
python_function('examples/ci-agent/agent.py', 'main', 0, 3, 19).
python_function('examples/common/host_capture.py', 'capture_host_screenshot', 1, 1, 2).
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
python_function('examples/control-plane/control_demo.py', 'run_diagnostics', 1, 1, 3).
python_function('examples/control-plane/control_demo.py', 'show_active_controls', 1, 6, 7).
python_function('examples/control-plane/control_demo.py', 'run_terminal_demo', 1, 6, 10).
python_function('examples/control-plane/control_demo.py', 'run_browser_demo', 1, 6, 10).
python_function('examples/control-plane/control_demo.py', 'main', 0, 1, 7).
python_function('examples/control-plugin/src/vdisplay_example_plugin/__init__.py', '_build_echo', 0, 1, 1).
python_function('examples/control-plugin/src/vdisplay_example_plugin/__init__.py', 'register_plugin', 1, 1, 1).
python_function('examples/control-plugin-ax/src/vdisplay_example_ax_plugin/__init__.py', 'register_plugin', 1, 1, 1).
python_function('examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py', '_use_mock_backend', 0, 2, 3).
python_function('examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py', '_demo_backend', 0, 1, 1).
python_function('examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py', 'build_example_ax', 0, 3, 3).
python_function('examples/control-plugin-uia/src/vdisplay_example_uia_plugin/__init__.py', 'register_plugin', 1, 1, 1).
python_function('examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py', '_use_mock_backend', 0, 2, 3).
python_function('examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py', '_demo_backend', 0, 1, 1).
python_function('examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py', 'build_example_uia', 0, 3, 3).
python_function('examples/headless-virtual/run_virtual.py', '_load_common', 0, 4, 6).
python_function('examples/headless-virtual/run_virtual.py', 'main', 0, 1, 14).
python_function('examples/host-mirror/mirror_demo.py', '_load_common', 0, 4, 6).
python_function('examples/host-mirror/mirror_demo.py', 'main', 0, 7, 19).
python_function('examples/host-relay/relay_demo.py', '_load_common', 0, 4, 6).
python_function('examples/host-relay/relay_demo.py', '_capture_phase', 1, 1, 5).
python_function('examples/host-relay/relay_demo.py', 'main', 0, 11, 17).
python_function('packages/cli2vdisplay/src/cli2vdisplay/cli.py', 'main', 1, 7, 10).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', '_dispatch_legacy', 1, 3, 9).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 'dispatch', 1, 14, 18).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', '_dispatch_fallback', 1, 4, 6).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 'execute_dsl_line', 1, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', 'main', 1, 4, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', '_main_legacy', 1, 10, 11).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', '_main_subcommand', 1, 9, 13).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'split_command', 1, 4, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'normalize_tokens', 1, 3, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'resolve_verb', 1, 4, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'pick_flag', 2, 3, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_with_display', 2, 2, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_windows', 2, 3, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_screenshot', 2, 5, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_virtual_start', 2, 4, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_launch', 2, 5, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_mirror', 2, 5, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_adopt', 2, 6, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_has_flag', 2, 1, 0).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_control_common', 2, 9, 6).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_controls_list', 2, 3, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_controls_find', 2, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_control_click', 2, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_control_focus', 2, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_control_set_value', 2, 2, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_diagnose_control', 2, 1, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_browser_open', 2, 11, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_terminal_open', 2, 6, 2).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_parse_release', 2, 5, 1).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'parse_line', 1, 3, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_screenshot_to_text', 1, 2, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_mirror_to_text', 1, 2, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_controls_list_to_text', 1, 3, 3).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_browser_open_to_text', 1, 8, 5).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_terminal_open_to_text', 1, 6, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 'to_text', 1, 2, 4).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', '_control_to_text', 2, 8, 5).
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
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_parse_controls_list_uppercase', 0, 7, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_parse_controls_list_human_readable', 0, 6, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_parse_control_click_with_verify', 0, 8, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_parse_control_click_with_screenshot_verify', 0, 5, 3).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_parse_control_set_value_requires_value_schema', 0, 6, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_parse_controls_find_with_provider_ref', 0, 5, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_command_request_from_dsl_control', 0, 8, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_command_request_provider_ref', 0, 3, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_parse_control_terminal_fields', 0, 13, 3).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_parse_control_terminal_uppercase_flags', 0, 7, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_to_text_roundtrip_terminal_control', 0, 6, 2).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_to_text_roundtrip_control_click', 0, 5, 3).
python_function('packages/dsl2vdisplay/tests/test_dsl_control.py', 'test_dispatch_control_verbs_via_executor', 3, 4, 5).
python_function('packages/dsl2vdisplay/tests/test_parity.py', 'test_parity_info_text_vs_dict', 0, 3, 1).
python_function('packages/dsl2vdisplay/tests/test_parity.py', 'test_health', 0, 3, 1).
python_function('packages/mcp2vdisplay/src/mcp2vdisplay/cli.py', 'main', 0, 2, 6).
python_function('packages/mcp2vdisplay/src/mcp2vdisplay/cli.py', 'create_server', 0, 1, 1).
python_function('packages/mcp2vdisplay/src/mcp2vdisplay/server.py', 'create_server', 0, 1, 17).
python_function('packages/nlp2vdisplay/src/nlp2vdisplay/cli.py', 'main', 1, 7, 9).
python_function('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 'parse_display', 1, 1, 2).
python_function('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 'nl_to_dsl', 1, 1, 1).
python_function('packages/rest2vdisplay/src/rest2vdisplay/app.py', 'create_app', 0, 2, 22).
python_function('packages/rest2vdisplay/src/rest2vdisplay/cli.py', 'main', 0, 3, 9).
python_function('packages/uri2vdisplay/src/uri2vdisplay/cli.py', 'main', 1, 4, 10).
python_function('packages/uri2vdisplay/src/uri2vdisplay/decode.py', 'uri_to_dsl', 1, 7, 10).
python_function('packages/vdisplay-agent/src/vdisplay_agent/cli.py', 'main', 1, 4, 14).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'agent_meta', 0, 1, 0).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'success', 2, 2, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'failure', 2, 3, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'from_runtime', 2, 3, 7).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'json_success', 2, 1, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'json_from_runtime', 2, 1, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'json_error', 2, 5, 7).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'strip_ok', 1, 1, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 'flatten_envelope', 1, 6, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/__init__.py', 'register_all_routes', 2, 2, 3).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/auth.py', 'expected_token', 0, 2, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/auth.py', 'make_check_auth', 1, 1, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/capture.py', 'register_routes', 3, 1, 6).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/control.py', 'register_routes', 3, 1, 12).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/health.py', '_control_api_enabled', 1, 2, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/health.py', 'register_routes', 3, 1, 11).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/sampler.py', 'register_routes', 3, 1, 11).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/session.py', 'register_routes', 3, 1, 21).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/tasks.py', 'register_routes', 3, 1, 13).
python_function('packages/vdisplay-agent/src/vdisplay_agent/routes/windows.py', 'register_routes', 3, 1, 7).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_pid_alive', 1, 3, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_parse_ss_pids', 1, 2, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_pids_from_ss', 1, 3, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_pids_from_lsof', 1, 5, 6).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', 'find_listener_pids', 1, 4, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_probe_is_vdisplay_agent', 2, 6, 6).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', 'stop_pids', 1, 13, 7).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', 'ensure_broker_port_free', 2, 4, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/server.py', 'create_app', 1, 2, 6).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py', 'platform_capabilities', 0, 5, 11).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py', 'diagnostics', 1, 1, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', 'capture_frame', 2, 3, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', '_capture_session', 3, 3, 11).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', '_capture_all_monitors', 2, 2, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', '_region_from_body', 1, 8, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', '_capture_host', 2, 7, 10).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', '_selector_kwargs', 1, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', 'list_control_plugins', 0, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', 'diagnose_control', 0, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', 'list_controls', 1, 4, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', 'find_controls', 1, 2, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', 'invoke_control', 1, 2, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', 'focus_control', 1, 2, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/control.py', 'set_control_value', 1, 3, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/outputs.py', 'list_outputs_payload', 0, 2, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/relay.py', 'adopt_window', 2, 6, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/relay.py', 'release_window', 2, 5, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py', '_config_from_body', 1, 12, 8).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py', '_ensure_virtual_session', 1, 4, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py', '_capture_virtual_persistent', 1, 5, 7).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py', '_recover_screencast', 1, 3, 3).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py', 'start_sampler', 2, 7, 9).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py', 'stop_sampler', 1, 4, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sampler.py', 'sampler_status', 1, 5, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', '_session_started', 1, 1, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_virtual', 1, 3, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_mirror', 1, 3, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_relay', 1, 4, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_screencast', 1, 3, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'stop_screencast', 1, 5, 3).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'screencast_status', 1, 3, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_terminal', 1, 5, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_browser', 1, 3, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'stop_session', 2, 6, 6).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'list_sessions', 1, 1, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'shutdown', 1, 4, 8).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'recover_on_startup', 2, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'list_tasks', 1, 3, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'get_task', 2, 2, 3).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'heartbeat_task', 2, 2, 3).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'stop_task', 2, 5, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'register_session_task', 1, 2, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'unregister_session_task', 2, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'begin_sampler_task', 1, 2, 3).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'touch_sampler_task', 2, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'end_sampler_task', 2, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'begin_screencast_task', 1, 2, 3).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'end_screencast_task', 2, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/tasks.py', 'shutdown_tasks', 2, 5, 7).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/windows.py', 'list_windows', 0, 8, 6).
python_function('packages/vdisplay-agent/src/vdisplay_agent/task_store.py', '_utcnow', 0, 1, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/task_store.py', 'default_task_db_path', 0, 3, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/task_store.py', 'task_to_dict', 1, 4, 2).
python_function('src/vdisplay/agent_config.py', 'agent_auto_enabled', 0, 1, 3).
python_function('src/vdisplay/agent_config.py', 'reset_agent_probe_cache', 0, 1, 0).
python_function('src/vdisplay/agent_config.py', '_default_agent_base', 0, 3, 2).
python_function('src/vdisplay/agent_config.py', '_probe_agent_url', 1, 3, 2).
python_function('src/vdisplay/agent_config.py', '_probe_default_agent', 0, 3, 3).
python_function('src/vdisplay/agent_config.py', 'resolve_agent_url', 1, 6, 5).
python_function('src/vdisplay/agent_config.py', 'resolve_agent_token', 0, 3, 2).
python_function('src/vdisplay/agent_config.py', 'use_agent', 1, 2, 4).
python_function('src/vdisplay/agent_dispatch.py', 'agent_client', 1, 2, 3).
python_function('src/vdisplay/agent_dispatch.py', 'dispatch_via_agent', 1, 1, 4).
python_function('src/vdisplay/agent_envelope.py', 'flatten_agent_envelope', 1, 6, 2).
python_function('src/vdisplay/api.py', '_default_virtual_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', '_default_mirror_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', '_default_relay_backend', 0, 2, 1).
python_function('src/vdisplay/api.py', 'platform_summary', 0, 1, 5).
python_function('src/vdisplay/application/__init__.py', '__getattr__', 1, 2, 1).
python_function('src/vdisplay/application/artifacts.py', '_file_ref', 2, 4, 5).
python_function('src/vdisplay/application/artifacts.py', '_append_unique', 3, 3, 2).
python_function('src/vdisplay/application/artifacts.py', 'artifacts_from_screenshot', 1, 8, 6).
python_function('src/vdisplay/application/artifacts.py', 'artifacts_from_control', 1, 13, 7).
python_function('src/vdisplay/application/artifacts.py', 'build_artifacts', 2, 3, 2).
python_function('src/vdisplay/application/commands.py', '_resolve_browser_engine_from_dsl', 1, 5, 6).
python_function('src/vdisplay/application/commands.py', '_control_session_id_from_dsl', 2, 2, 1).
python_function('src/vdisplay/application/commands.py', '_control_fields_from_dsl', 1, 9, 4).
python_function('src/vdisplay/application/commands.py', '_terminal_fields_from_dsl', 2, 2, 1).
python_function('src/vdisplay/application/commands.py', '_browser_fields_from_dsl', 2, 2, 3).
python_function('src/vdisplay/application/errors.py', 'error_from_exception', 1, 4, 3).
python_function('src/vdisplay/application/executor.py', '_maybe_enrich_screenshot', 2, 3, 2).
python_function('src/vdisplay/application/executor.py', 'execute', 1, 6, 15).
python_function('src/vdisplay/application/handlers/agent.py', '_strip_ok', 1, 1, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_health', 2, 1, 1).
python_function('src/vdisplay/application/handlers/agent.py', '_info', 2, 3, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_monitors', 2, 1, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_windows', 2, 1, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_all', 2, 3, 7).
python_function('src/vdisplay/application/handlers/agent.py', '_capabilities', 2, 1, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_validate', 2, 4, 6).
python_function('src/vdisplay/application/handlers/agent.py', '_screenshot', 2, 3, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_virtual_start', 2, 1, 1).
python_function('src/vdisplay/application/handlers/agent.py', '_terminal_open', 2, 1, 1).
python_function('src/vdisplay/application/handlers/agent.py', '_browser_open', 2, 1, 1).
python_function('src/vdisplay/application/handlers/agent.py', '_mirror', 2, 6, 8).
python_function('src/vdisplay/application/handlers/agent.py', '_adopt', 2, 2, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_release', 2, 1, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_diagnose_control', 2, 1, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_controls_list', 2, 1, 3).
python_function('src/vdisplay/application/handlers/agent.py', '_controls_find', 2, 1, 3).
python_function('src/vdisplay/application/handlers/agent.py', '_control_click', 2, 1, 3).
python_function('src/vdisplay/application/handlers/agent.py', '_control_focus', 2, 1, 3).
python_function('src/vdisplay/application/handlers/agent.py', '_control_set_value', 2, 1, 3).
python_function('src/vdisplay/application/handlers/agent.py', 'execute_agent', 1, 2, 4).
python_function('src/vdisplay/application/handlers/control.py', 'control_selector_kwargs', 1, 1, 0).
python_function('src/vdisplay/application/handlers/control.py', 'control_service_kwargs', 1, 3, 3).
python_function('src/vdisplay/application/handlers/control.py', 'control_selector_only_kwargs', 1, 2, 2).
python_function('src/vdisplay/application/handlers/control.py', 'control_request_body', 1, 3, 3).
python_function('src/vdisplay/application/handlers/local.py', '_health', 1, 1, 0).
python_function('src/vdisplay/application/handlers/local.py', '_info', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_monitors', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_windows', 1, 2, 1).
python_function('src/vdisplay/application/handlers/local.py', '_all', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_capabilities', 1, 1, 2).
python_function('src/vdisplay/application/handlers/local.py', '_validate', 1, 4, 5).
python_function('src/vdisplay/application/handlers/local.py', '_screenshot', 1, 3, 2).
python_function('src/vdisplay/application/handlers/local.py', '_virtual_start', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_terminal_open', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_browser_open', 1, 2, 2).
python_function('src/vdisplay/application/handlers/local.py', '_mirror', 1, 2, 1).
python_function('src/vdisplay/application/handlers/local.py', '_adopt', 1, 2, 1).
python_function('src/vdisplay/application/handlers/local.py', '_release', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_diagnose_control', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_controls_list', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_controls_find', 1, 1, 5).
python_function('src/vdisplay/application/handlers/local.py', '_control_click', 1, 1, 2).
python_function('src/vdisplay/application/handlers/local.py', '_control_focus', 1, 1, 2).
python_function('src/vdisplay/application/handlers/local.py', '_control_set_value', 1, 2, 3).
python_function('src/vdisplay/application/handlers/local.py', 'execute_local', 1, 2, 3).
python_function('src/vdisplay/application/runtime.py', 'agent_client_optional', 0, 2, 2).
python_function('src/vdisplay/application/runtime.py', 'agent_client_required', 0, 2, 3).
python_function('src/vdisplay/application/runtime.py', 'prefer_agent', 0, 1, 1).
python_function('src/vdisplay/application/runtime.py', 'resolve_apps_only', 0, 3, 0).
python_function('src/vdisplay/application/runtime.py', 'get_execution_policy', 0, 1, 0).
python_function('src/vdisplay/application/services/capture.py', 'resolve_screenshot_routing', 1, 7, 1).
python_function('src/vdisplay/application/services/capture.py', 'capture_screenshot', 0, 3, 3).
python_function('src/vdisplay/application/services/capture.py', 'capture_screenshot_local', 0, 7, 9).
python_function('src/vdisplay/application/services/capture.py', '_capture_via_agent', 1, 9, 7).
python_function('src/vdisplay/application/services/capture.py', 'capture_screenshot_via_client', 1, 1, 1).
python_function('src/vdisplay/application/services/control.py', '_resolve_verify_mode', 0, 5, 0).
python_function('src/vdisplay/application/services/control.py', '_control_settle_seconds', 0, 4, 3).
python_function('src/vdisplay/application/services/control.py', '_apply_selector_overrides', 1, 9, 4).
python_function('src/vdisplay/application/services/control.py', '_selector_from_kwargs', 0, 10, 9).
python_function('src/vdisplay/application/services/control.py', '_provider_kwargs', 0, 2, 0).
python_function('src/vdisplay/application/services/control.py', '_resolve_target', 3, 5, 6).
python_function('src/vdisplay/application/services/control.py', '_load_map_pack', 1, 2, 1).
python_function('src/vdisplay/application/services/control.py', '_resolve_map_target', 2, 1, 2).
python_function('src/vdisplay/application/services/control.py', '_map_find_payload', 2, 5, 7).
python_function('src/vdisplay/application/services/control.py', '_execute_map_action', 0, 10, 17).
python_function('src/vdisplay/application/services/control.py', 'list_control_plugins', 0, 1, 2).
python_function('src/vdisplay/application/services/control.py', 'diagnose_control', 0, 14, 12).
python_function('src/vdisplay/application/services/control.py', 'controls_list', 0, 4, 5).
python_function('src/vdisplay/application/services/control.py', '_attach_vision_preview', 1, 7, 8).
python_function('src/vdisplay/application/services/control.py', 'controls_find', 0, 12, 15).
python_function('src/vdisplay/application/services/control.py', 'control_click', 0, 1, 1).
python_function('src/vdisplay/application/services/control.py', 'control_focus', 0, 1, 1).
python_function('src/vdisplay/application/services/control.py', 'control_set_value', 0, 1, 1).
python_function('src/vdisplay/application/services/control.py', '_perform_action', 4, 9, 8).
python_function('src/vdisplay/application/services/control.py', '_capture_before_state', 0, 4, 1).
python_function('src/vdisplay/application/services/control.py', '_build_action_payload', 0, 13, 6).
python_function('src/vdisplay/application/services/control.py', '_execute_action', 0, 8, 19).
python_function('src/vdisplay/application/services/control.py', '_build_tree', 1, 3, 2).
python_function('src/vdisplay/application/services/discovery.py', '_run_discovery', 1, 3, 2).
python_function('src/vdisplay/application/services/discovery.py', 'list_monitors', 1, 1, 2).
python_function('src/vdisplay/application/services/discovery.py', 'list_monitors_local', 1, 2, 4).
python_function('src/vdisplay/application/services/discovery.py', 'list_windows_payload', 1, 2, 4).
python_function('src/vdisplay/application/services/discovery.py', 'list_windows_local', 1, 2, 6).
python_function('src/vdisplay/application/services/discovery.py', 'list_adopted', 1, 1, 4).
python_function('src/vdisplay/application/services/discovery.py', 'list_all', 1, 4, 2).
python_function('src/vdisplay/application/services/discovery.py', 'list_all_local', 1, 1, 4).
python_function('src/vdisplay/application/services/discovery.py', 'diagnose', 1, 2, 2).
python_function('src/vdisplay/application/services/discovery.py', 'diagnose_unattended', 1, 2, 8).
python_function('src/vdisplay/application/services/discovery.py', '_sampler_hint', 1, 3, 0).
python_function('src/vdisplay/application/services/img2nl_enrich.py', 'img2nl_enabled', 0, 1, 3).
python_function('src/vdisplay/application/services/img2nl_enrich.py', 'img2nl_locale', 0, 2, 2).
python_function('src/vdisplay/application/services/img2nl_enrich.py', '_image_path', 1, 3, 2).
python_function('src/vdisplay/application/services/img2nl_enrich.py', 'describe_screenshot_image', 1, 10, 9).
python_function('src/vdisplay/application/services/img2nl_enrich.py', '_maybe_vision_llm_enrich', 1, 4, 7).
python_function('src/vdisplay/application/services/img2nl_enrich.py', 'enrich_screenshot_payload', 1, 12, 8).
python_function('src/vdisplay/application/services/info.py', 'platform_info', 0, 6, 10).
python_function('src/vdisplay/application/services/map.py', '_prepare_capture_meta', 0, 4, 8).
python_function('src/vdisplay/application/services/map.py', 'map_build', 0, 6, 8).
python_function('src/vdisplay/application/services/map.py', 'map_show', 0, 3, 3).
python_function('src/vdisplay/application/services/map.py', 'map_diff', 0, 3, 5).
python_function('src/vdisplay/application/services/map.py', 'map_refresh', 0, 7, 6).
python_function('src/vdisplay/application/services/map.py', '_capture', 0, 7, 6).
python_function('src/vdisplay/application/services/map.py', '_capture_via_agent', 0, 4, 11).
python_function('src/vdisplay/application/services/map.py', '_monitor_index', 2, 5, 5).
python_function('src/vdisplay/application/services/map.py', '_monitor_rotation', 2, 5, 4).
python_function('src/vdisplay/application/services/sampler.py', 'run_sampler', 1, 5, 12).
python_function('src/vdisplay/application/services/sampler.py', 'start_sampler_via_agent', 2, 1, 1).
python_function('src/vdisplay/application/services/sampler_loop.py', 'resolve_capture_mode', 1, 5, 1).
python_function('src/vdisplay/application/services/sampler_loop.py', 'is_screencast_recoverable_error', 1, 2, 2).
python_function('src/vdisplay/application/services/sampler_loop.py', 'frame_extension', 1, 1, 0).
python_function('src/vdisplay/application/services/sampler_loop.py', 'transcode_frame', 2, 5, 7).
python_function('src/vdisplay/application/services/sampler_loop.py', 'validate_sampler_config', 1, 7, 5).
python_function('src/vdisplay/application/services/session.py', 'virtual_start', 0, 1, 4).
python_function('src/vdisplay/application/services/session.py', 'virtual_launch', 1, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'virtual_screenshot', 1, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'mirror_start', 0, 2, 6).
python_function('src/vdisplay/application/services/session.py', 'mirror_screenshot', 1, 2, 4).
python_function('src/vdisplay/application/services/session.py', 'relay_adopt', 0, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'relay_release', 0, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'relay_list_adopted', 1, 1, 4).
python_function('src/vdisplay/application/services/session.py', 'relay_screenshot', 1, 4, 10).
python_function('src/vdisplay/application/services/session.py', 'browser_open', 0, 2, 4).
python_function('src/vdisplay/application/services/session.py', 'terminal_open', 0, 3, 3).
python_function('src/vdisplay/application/services/session.py', 'unsupported_session_action', 2, 1, 1).
python_function('src/vdisplay/application/session_context.py', 'apply_cli_session_args', 1, 3, 4).
python_function('src/vdisplay/application/session_context.py', 'enrich_command_request', 1, 6, 5).
python_function('src/vdisplay/application/session_recorder.py', 'session_recording_enabled', 0, 2, 3).
python_function('src/vdisplay/application/session_recorder.py', '_redact_env', 1, 5, 3).
python_function('src/vdisplay/application/session_recorder.py', '_collect_env_snapshot', 0, 3, 2).
python_function('src/vdisplay/application/session_recorder.py', '_slugify', 1, 2, 2).
python_function('src/vdisplay/application/session_recorder.py', '_default_session_name', 0, 2, 5).
python_function('src/vdisplay/application/session_recorder.py', 'resolve_session_root', 1, 6, 8).
python_function('src/vdisplay/application/session_recorder.py', 'get_session_recorder', 1, 4, 4).
python_function('src/vdisplay/application/session_recorder.py', 'record_execution', 2, 5, 4).
python_function('src/vdisplay/application/session_recorder.py', 'request_to_dict', 1, 1, 2).
python_function('src/vdisplay/application/session_recorder.py', 'result_to_dict', 1, 2, 2).
python_function('src/vdisplay/application/session_recorder.py', 'collect_artifacts', 1, 6, 4).
python_function('src/vdisplay/application/session_recorder.py', '_artifacts_from_data', 1, 1, 9).
python_function('src/vdisplay/application/session_recorder.py', '_collect_top_level_artifacts', 2, 7, 6).
python_function('src/vdisplay/application/session_recorder.py', '_collect_block_artifacts', 2, 7, 3).
python_function('src/vdisplay/application/session_recorder.py', '_collect_routing_artifacts', 2, 3, 3).
python_function('src/vdisplay/application/session_recorder.py', 'copy_artifact', 2, 6, 8).
python_function('src/vdisplay/application/session_recorder.py', 'extract_diagnostics', 1, 5, 4).
python_function('src/vdisplay/application/session_recorder.py', '_build_summary', 1, 6, 7).
python_function('src/vdisplay/application/session_recorder.py', '_utc_now', 0, 1, 3).
python_function('src/vdisplay/application/session_recorder.py', 'render_readme', 1, 13, 7).
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
python_function('src/vdisplay/capture/host.py', '_wayland_host_session', 1, 2, 2).
python_function('src/vdisplay/capture/host.py', '_monitor_source_name', 3, 9, 7).
python_function('src/vdisplay/capture/host.py', 'resolve_window_region', 1, 10, 6).
python_function('src/vdisplay/capture/host.py', '_monitor_capture_region', 2, 4, 3).
python_function('src/vdisplay/capture/host.py', '_capture_all_from_driver_full', 3, 7, 13).
python_function('src/vdisplay/capture/host.py', '_capture_all_from_screencast', 4, 14, 15).
python_function('src/vdisplay/capture/host.py', '_try_screencast_capture', 3, 11, 8).
python_function('src/vdisplay/capture/host.py', '_try_mirror_capture', 5, 5, 9).
python_function('src/vdisplay/capture/host.py', '_try_driver_capture', 3, 6, 3).
python_function('src/vdisplay/capture/host.py', 'capture_host_png', 0, 13, 12).
python_function('src/vdisplay/capture/host.py', '_host_capture_error', 3, 3, 2).
python_function('src/vdisplay/capture/host.py', 'capture_host_to_file', 1, 3, 9).
python_function('src/vdisplay/capture/host.py', '_capture_individual_monitors', 7, 4, 8).
python_function('src/vdisplay/capture/host.py', '_try_bulk_capture', 6, 12, 4).
python_function('src/vdisplay/capture/host.py', 'capture_all_monitors', 0, 8, 11).
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
python_function('src/vdisplay/capture/policy.py', 'assess_unattended_capture', 0, 6, 7).
python_function('src/vdisplay/capture/policy.py', '_assess_virtual', 1, 1, 1).
python_function('src/vdisplay/capture/policy.py', '_assess_wayland', 2, 11, 7).
python_function('src/vdisplay/capture/portal.py', '_portal_impl', 1, 4, 22).
python_function('src/vdisplay/capture/portal.py', '_system_python', 0, 4, 3).
python_function('src/vdisplay/capture/portal.py', 'capture_portal_png', 0, 4, 9).
python_function('src/vdisplay/capture/portal.py', '_capture_portal_to_file', 1, 11, 8).
python_function('src/vdisplay/capture/portal_screencast.py', 'get_active_screencast', 0, 1, 0).
python_function('src/vdisplay/capture/portal_screencast.py', '_set_active', 1, 1, 0).
python_function('src/vdisplay/capture/portal_screencast.py', '_set_active_if_self', 1, 1, 0).
python_function('src/vdisplay/capture/portal_screencast.py', '_screencast_multiple', 1, 2, 3).
python_function('src/vdisplay/capture/portal_screencast.py', 'start_screencast_session', 0, 6, 6).
python_function('src/vdisplay/capture/portal_screencast.py', 'stop_screencast_session', 0, 2, 2).
python_function('src/vdisplay/capture/portal_screencast.py', 'invalidate_screencast_session', 1, 4, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_system_python', 0, 4, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_ensure_portal_deps', 0, 5, 2).
python_function('src/vdisplay/capture/portal_screencast.py', '_open_screencast_pipewire_fd', 1, 3, 11).
python_function('src/vdisplay/capture/portal_screencast.py', '_start_screencast', 0, 2, 4).
python_function('src/vdisplay/capture/portal_screencast.py', '_portal_request_path', 2, 1, 2).
python_function('src/vdisplay/capture/portal_screencast.py', '_stream_properties', 1, 3, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_stream_serial', 1, 2, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_stream_target', 2, 2, 2).
python_function('src/vdisplay/capture/portal_screencast.py', 'screencast_stream_region', 1, 11, 5).
python_function('src/vdisplay/capture/portal_screencast.py', '_ensure_fd_inheritable', 1, 1, 1).
python_function('src/vdisplay/capture/portal_screencast.py', '_dbus_fd', 1, 5, 5).
python_function('src/vdisplay/capture/portal_screencast.py', '_close_pipewire_fd', 1, 2, 1).
python_function('src/vdisplay/capture/portal_screencast.py', '_start_screencast_impl', 0, 9, 33).
python_function('src/vdisplay/capture/portal_screencast.py', '_listen_portal_request', 3, 1, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_close_screencast_session', 1, 2, 4).
python_function('src/vdisplay/capture/portal_screencast.py', '_capture_pipewire_stream', 0, 2, 9).
python_function('src/vdisplay/capture/portal_screencast.py', '_capture_pipewire_frame_gi_subprocess', 4, 6, 9).
python_function('src/vdisplay/capture/portal_screencast.py', '_capture_pipewire_frame_gst_launch', 4, 8, 13).
python_function('src/vdisplay/capture/portal_screencast.py', '_capture_pipewire_node', 1, 1, 1).
python_function('src/vdisplay/capture/portal_screencast.py', '_vdisplay_src_path', 0, 3, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_start_screencast_subprocess', 0, 8, 11).
python_function('src/vdisplay/capture/providers/drm.py', '_drm_devices', 0, 5, 7).
python_function('src/vdisplay/capture/providers/engine.py', '_allow_portal', 0, 1, 3).
python_function('src/vdisplay/capture/providers/engine.py', '_providers', 1, 4, 9).
python_function('src/vdisplay/capture/providers/engine.py', 'capture_full_png', 1, 1, 2).
python_function('src/vdisplay/capture/providers/engine.py', 'capture_region_png', 2, 1, 2).
python_function('src/vdisplay/capture/providers/engine.py', 'list_capture_providers', 1, 4, 6).
python_function('src/vdisplay/capture/providers/engine.py', '_try_providers', 1, 11, 12).
python_function('src/vdisplay/capture/providers/fbdev.py', '_fb_info', 0, 2, 7).
python_function('src/vdisplay/cli.py', 'build_parser', 0, 1, 4).
python_function('src/vdisplay/cli.py', 'main', 1, 2, 5).
python_function('src/vdisplay/cli_handlers.py', 'print_json', 1, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'monitors_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'windows_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'all_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'screenshot_payload', 0, 1, 2).
python_function('src/vdisplay/cli_handlers.py', 'dispatch_cli', 1, 1, 2).
python_function('src/vdisplay/client.py', '_route_outputs_query', 1, 4, 2).
python_function('src/vdisplay/client.py', '_route_windows_query', 1, 6, 4).
python_function('src/vdisplay/client.py', '_route_control_command', 2, 5, 0).
python_function('src/vdisplay/client.py', '_route_terminal_open', 1, 4, 0).
python_function('src/vdisplay/client.py', '_route_browser_open', 1, 4, 0).
python_function('src/vdisplay/client.py', '_route_command', 1, 7, 7).
python_function('src/vdisplay/commands/__init__.py', 'register_all', 1, 2, 1).
python_function('src/vdisplay/commands/agent.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/agent.py', '_agent_client', 0, 2, 3).
python_function('src/vdisplay/commands/agent.py', 'handle', 1, 5, 7).
python_function('src/vdisplay/commands/agent.py', '_handle_serve', 1, 5, 9).
python_function('src/vdisplay/commands/agent.py', '_handle_browser_open', 1, 3, 5).
python_function('src/vdisplay/commands/agent.py', '_handle_screencast', 1, 5, 6).
python_function('src/vdisplay/commands/all_cmd.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/all_cmd.py', 'handle', 1, 1, 3).
python_function('src/vdisplay/commands/all_cmd.py', 'register_outputs', 1, 1, 4).
python_function('src/vdisplay/commands/all_cmd.py', 'handle_outputs', 1, 1, 3).
python_function('src/vdisplay/commands/common.py', 'add_display_arg', 1, 1, 1).
python_function('src/vdisplay/commands/common.py', 'add_all_arg', 1, 1, 1).
python_function('src/vdisplay/commands/common.py', 'add_window_filter_args', 1, 1, 2).
python_function('src/vdisplay/commands/common.py', 'include_all_from_args', 1, 2, 2).
python_function('src/vdisplay/commands/common.py', 'add_control_selector_args', 1, 1, 1).
python_function('src/vdisplay/commands/common.py', 'add_map_args', 1, 1, 1).
python_function('src/vdisplay/commands/common.py', 'add_preview_args', 1, 1, 1).
python_function('src/vdisplay/commands/common.py', 'control_selector_kwargs_from_args', 1, 1, 1).
python_function('src/vdisplay/commands/common.py', 'control_selector_kwargs_for_service', 1, 1, 2).
python_function('src/vdisplay/commands/control.py', 'register', 1, 1, 7).
python_function('src/vdisplay/commands/control.py', '_add_selector_args', 1, 1, 2).
python_function('src/vdisplay/commands/control.py', '_run_control', 2, 5, 6).
python_function('src/vdisplay/commands/control.py', '_handle_browser_open', 1, 2, 3).
python_function('src/vdisplay/commands/control.py', '_handle_control_list', 1, 4, 6).
python_function('src/vdisplay/commands/control.py', '_handle_control_find', 1, 1, 1).
python_function('src/vdisplay/commands/control.py', '_handle_control_click', 1, 1, 1).
python_function('src/vdisplay/commands/control.py', '_handle_control_focus', 1, 1, 1).
python_function('src/vdisplay/commands/control.py', '_handle_control_set_value', 1, 1, 1).
python_function('src/vdisplay/commands/control.py', 'handle', 1, 2, 2).
python_function('src/vdisplay/commands/diagnose.py', 'register', 1, 1, 6).
python_function('src/vdisplay/commands/diagnose.py', 'handle', 1, 5, 6).
python_function('src/vdisplay/commands/info.py', 'register', 1, 1, 2).
python_function('src/vdisplay/commands/info.py', 'handle', 1, 1, 2).
python_function('src/vdisplay/commands/io.py', 'print_json', 1, 1, 2).
python_function('src/vdisplay/commands/map.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/map.py', 'handle', 1, 7, 7).
python_function('src/vdisplay/commands/mirror.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/mirror.py', 'handle', 1, 3, 4).
python_function('src/vdisplay/commands/monitors.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/monitors.py', 'handle', 1, 1, 3).
python_function('src/vdisplay/commands/nlp.py', 'register', 1, 1, 3).
python_function('src/vdisplay/commands/nlp.py', 'handle', 1, 2, 2).
python_function('src/vdisplay/commands/relay.py', 'register', 1, 1, 6).
python_function('src/vdisplay/commands/relay.py', 'handle_list_windows', 1, 1, 2).
python_function('src/vdisplay/commands/relay.py', 'handle', 1, 5, 6).
python_function('src/vdisplay/commands/sampler.py', 'register', 1, 1, 5).
python_function('src/vdisplay/commands/sampler.py', '_config_from_args', 1, 1, 1).
python_function('src/vdisplay/commands/sampler.py', 'handle', 1, 3, 4).
python_function('src/vdisplay/commands/sampler.py', '_handle_stop', 1, 2, 4).
python_function('src/vdisplay/commands/sampler.py', '_handle_status', 1, 2, 3).
python_function('src/vdisplay/commands/sampler.py', '_handle_start', 2, 4, 6).
python_function('src/vdisplay/commands/sampler.py', '_start_agent', 3, 2, 4).
python_function('src/vdisplay/commands/sampler.py', '_wait_for_sampler', 3, 9, 8).
python_function('src/vdisplay/commands/screenshot.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/screenshot.py', 'handle', 1, 1, 2).
python_function('src/vdisplay/commands/session.py', 'add_root_session_args', 1, 1, 1).
python_function('src/vdisplay/commands/session.py', 'command_request_from_control_args', 2, 8, 7).
python_function('src/vdisplay/commands/virtual.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/virtual.py', 'handle', 1, 6, 7).
python_function('src/vdisplay/commands/windows.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/windows.py', 'handle', 1, 1, 3).
python_function('src/vdisplay/control/action_bounds.py', 'action_bounds_for_vision', 1, 2, 2).
python_function('src/vdisplay/control/action_bounds.py', 'click_point_for_vision', 1, 1, 1).
python_function('src/vdisplay/control/browser_engine.py', 'normalize_browser_engine', 1, 3, 6).
python_function('src/vdisplay/control/browser_engine.py', 'engine_profile_id', 1, 2, 3).
python_function('src/vdisplay/control/browser_engine.py', 'browser_engine_profile', 1, 3, 1).
python_function('src/vdisplay/control/browser_engine.py', 'resolve_session_browser_engine', 1, 3, 4).
python_function('src/vdisplay/control/browser_session_store.py', 'detached_sessions_enabled', 0, 1, 3).
python_function('src/vdisplay/control/browser_session_store.py', 'meta_path', 1, 1, 0).
python_function('src/vdisplay/control/browser_session_store.py', 'profile_dir', 1, 1, 0).
python_function('src/vdisplay/control/browser_session_store.py', 'save_meta', 1, 1, 5).
python_function('src/vdisplay/control/browser_session_store.py', 'load_meta', 1, 5, 9).
python_function('src/vdisplay/control/browser_session_store.py', 'remove_meta', 1, 2, 3).
python_function('src/vdisplay/control/browser_session_store.py', 'process_alive', 1, 4, 1).
python_function('src/vdisplay/control/browser_session_store.py', 'find_free_port', 0, 1, 4).
python_function('src/vdisplay/control/browser_session_store.py', '_chromium_executable', 0, 2, 4).
python_function('src/vdisplay/control/browser_session_store.py', 'wait_for_cdp', 1, 4, 5).
python_function('src/vdisplay/control/browser_session_store.py', 'launch_detached_chromium', 0, 7, 15).
python_function('src/vdisplay/control/browser_session_store.py', 'stop_detached', 1, 6, 7).
python_function('src/vdisplay/control/browser_session_store.py', 'session_available', 1, 3, 3).
python_function('src/vdisplay/control/contracts.py', 'provider_score_from_dataclass', 1, 4, 3).
python_function('src/vdisplay/control/contracts.py', 'control_route_request_from_command', 1, 4, 7).
python_function('src/vdisplay/control/descriptors.py', 'resolve_host_environment', 0, 4, 2).
python_function('src/vdisplay/control/descriptors.py', 'descriptor_for', 1, 1, 1).
python_function('src/vdisplay/control/descriptors.py', 'all_provider_descriptors', 0, 1, 2).
python_function('src/vdisplay/control/descriptors.py', 'all_application_profiles', 0, 1, 1).
python_function('src/vdisplay/control/descriptors.py', 'all_selector_extensions', 0, 1, 0).
python_function('src/vdisplay/control/descriptors.py', 'detect_platform_profile', 0, 14, 12).
python_function('src/vdisplay/control/descriptors.py', 'extension_catalog', 0, 8, 6).
python_function('src/vdisplay/control/engine.py', 'resolve_provider_routing', 1, 2, 2).
python_function('src/vdisplay/control/engine.py', 'resolve_route', 1, 2, 2).
python_function('src/vdisplay/control/engine.py', 'resolve_provider', 1, 1, 1).
python_function('src/vdisplay/control/gui_map.py', 'load_gui_map', 1, 2, 6).
python_function('src/vdisplay/control/gui_map.py', 'save_gui_map', 2, 1, 4).
python_function('src/vdisplay/control/gui_map.py', '_slug', 1, 2, 3).
python_function('src/vdisplay/control/gui_map.py', 'tile_fingerprint', 2, 4, 11).
python_function('src/vdisplay/control/gui_map.py', 'element_from_ocr_box', 1, 9, 9).
python_function('src/vdisplay/control/gui_map.py', 'crop_png_bounds', 2, 3, 7).
python_function('src/vdisplay/control/gui_map.py', '_translate_ocr_boxes', 3, 4, 3).
python_function('src/vdisplay/control/gui_map.py', 'parse_crop_bounds', 1, 6, 6).
python_function('src/vdisplay/control/gui_map.py', '_boxes_in_scope_for_build', 2, 4, 2).
python_function('src/vdisplay/control/gui_map.py', '_prepare_ocr_boxes_for_build', 2, 13, 9).
python_function('src/vdisplay/control/gui_map.py', 'build_gui_map_from_ocr', 2, 7, 11).
python_function('src/vdisplay/control/gui_map.py', 'resolve_map_element', 2, 2, 2).
python_function('src/vdisplay/control/gui_map.py', 'resolve_map_region', 2, 2, 2).
python_function('src/vdisplay/control/gui_map.py', 'map_element_to_node', 1, 5, 4).
python_function('src/vdisplay/control/gui_map.py', 'scoped_capture_region', 2, 2, 1).
python_function('src/vdisplay/control/gui_map.py', 'verify_hints_from_map_element', 1, 3, 0).
python_function('src/vdisplay/control/gui_map.py', 'resolve_map_verify_mode', 1, 11, 2).
python_function('src/vdisplay/control/gui_map_diff.py', '_center', 1, 1, 1).
python_function('src/vdisplay/control/gui_map_diff.py', '_distance', 2, 1, 2).
python_function('src/vdisplay/control/gui_map_diff.py', '_box_to_bounds', 1, 1, 1).
python_function('src/vdisplay/control/gui_map_diff.py', '_normalize_label', 1, 1, 4).
python_function('src/vdisplay/control/gui_map_diff.py', '_labels_match', 2, 5, 1).
python_function('src/vdisplay/control/gui_map_diff.py', '_boxes_in_scope', 2, 5, 2).
python_function('src/vdisplay/control/gui_map_diff.py', 'match_ocr_box_for_element', 2, 9, 4).
python_function('src/vdisplay/control/gui_map_diff.py', 'assess_map_drift', 1, 13, 5).
python_function('src/vdisplay/control/gui_map_diff.py', '_classify_element_drift', 2, 6, 5).
python_function('src/vdisplay/control/gui_map_diff.py', '_region_drifts_for', 2, 5, 3).
python_function('src/vdisplay/control/gui_map_diff.py', '_new_ocr_labels', 3, 7, 3).
python_function('src/vdisplay/control/gui_map_diff.py', 'diff_gui_map', 3, 9, 18).
python_function('src/vdisplay/control/gui_map_diff.py', '_refresh_known_elements', 3, 5, 6).
python_function('src/vdisplay/control/gui_map_diff.py', '_append_new_elements', 1, 14, 12).
python_function('src/vdisplay/control/gui_map_diff.py', 'refresh_gui_map', 3, 7, 7).
python_function('src/vdisplay/control/gui_map_export.py', 'render_map_markdown', 1, 8, 8).
python_function('src/vdisplay/control/gui_map_export.py', '_region_markdown', 2, 6, 3).
python_function('src/vdisplay/control/gui_map_export.py', '_element_markdown', 1, 5, 2).
python_function('src/vdisplay/control/gui_map_export.py', 'render_map_svg', 2, 4, 13).
python_function('src/vdisplay/control/gui_map_export.py', '_element_svg', 1, 5, 3).
python_function('src/vdisplay/control/gui_map_export.py', '_png_b64', 1, 1, 2).
python_function('src/vdisplay/control/gui_map_export.py', 'write_map_artifacts', 1, 4, 8).
python_function('src/vdisplay/control/plugins.py', '_register_plugin', 3, 1, 2).
python_function('src/vdisplay/control/plugins.py', '_bootstrap_builtin_registry', 0, 3, 3).
python_function('src/vdisplay/control/plugins.py', 'load_entry_point_plugins', 1, 8, 9).
python_function('src/vdisplay/control/plugins.py', 'get_provider_registry', 0, 3, 3).
python_function('src/vdisplay/control/plugins.py', 'register_control_provider', 2, 1, 2).
python_function('src/vdisplay/control/plugins.py', 'unregister_control_provider', 1, 4, 3).
python_function('src/vdisplay/control/plugins.py', 'list_control_plugins', 0, 2, 3).
python_function('src/vdisplay/control/plugins.py', 'iter_provider_names', 0, 1, 2).
python_function('src/vdisplay/control/plugins.py', 'reset_control_plugins_for_tests', 0, 1, 2).
python_function('src/vdisplay/control/plugins.py', 'get_registered_descriptor', 1, 5, 3).
python_function('src/vdisplay/control/policy.py', 'evaluate_provider_routing', 0, 1, 2).
python_function('src/vdisplay/control/policy.py', '_evaluate_platform_backends', 1, 7, 1).
python_function('src/vdisplay/control/policy.py', '_evaluate_pointer_fallback', 1, 6, 2).
python_function('src/vdisplay/control/policy.py', '_evaluate_readiness', 0, 7, 11).
python_function('src/vdisplay/control/policy.py', '_pointer_fallback_for_host', 0, 6, 2).
python_function('src/vdisplay/control/policy.py', 'assess_control_capability', 0, 7, 9).
python_function('src/vdisplay/control/policy.py', '_append_accessibility_env_vars', 1, 3, 2).
python_function('src/vdisplay/control/profile_inference.py', 'profile_for', 1, 3, 2).
python_function('src/vdisplay/control/profile_inference.py', '_score_vision_only_surface', 1, 8, 1).
python_function('src/vdisplay/control/profile_inference.py', '_score_browser_engine', 1, 8, 4).
python_function('src/vdisplay/control/profile_inference.py', '_score_web_spa', 1, 6, 1).
python_function('src/vdisplay/control/profile_inference.py', '_score_terminal_pty', 2, 7, 1).
python_function('src/vdisplay/control/profile_inference.py', '_score_electron_desktop', 1, 5, 7).
python_function('src/vdisplay/control/profile_inference.py', '_score_native_desktop', 1, 14, 1).
python_function('src/vdisplay/control/profile_inference.py', '_score_candidate', 1, 12, 11).
python_function('src/vdisplay/control/profile_inference.py', 'infer_application_profile', 1, 6, 8).
python_function('src/vdisplay/control/profile_inference.py', 'profile_provider_boost', 2, 6, 1).
python_function('src/vdisplay/control/providers/atspi.py', '_gi_available', 0, 2, 1).
python_function('src/vdisplay/control/providers/atspi.py', '_system_python', 0, 4, 3).
python_function('src/vdisplay/control/providers/atspi.py', '_vdisplay_src_path', 0, 3, 3).
python_function('src/vdisplay/control/providers/atspi.py', '_run_subprocess', 1, 8, 10).
python_function('src/vdisplay/control/providers/atspi.py', '_actions_from_dict', 1, 4, 4).
python_function('src/vdisplay/control/providers/atspi.py', '_snapshot_from_dict', 1, 8, 10).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_atspi', 0, 2, 2).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_map_role', 1, 2, 3).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_atspi_module', 0, 1, 1).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_iface', 2, 5, 2).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_node_actions', 1, 8, 10).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_text_iface', 1, 3, 2).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_node_text_value', 1, 4, 6).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_provider_ref', 2, 3, 3).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_node_state', 2, 5, 4).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_node_capabilities', 3, 5, 6).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_node_bounds', 1, 7, 5).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_application_matches', 2, 4, 5).
python_function('src/vdisplay/control/providers/atspi_impl.py', 'snapshot_dict', 0, 6, 21).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_resolve_accessible', 1, 5, 9).
python_function('src/vdisplay/control/providers/atspi_impl.py', 'dispatch', 1, 6, 7).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_handle_available', 0, 2, 3).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_handle_invoke', 1, 6, 11).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_handle_focus', 1, 3, 5).
python_function('src/vdisplay/control/providers/atspi_impl.py', '_handle_set_value', 1, 7, 10).
python_function('src/vdisplay/control/providers/ax_impl.py', 'ax_deps_available', 0, 3, 0).
python_function('src/vdisplay/control/providers/ax_impl.py', '_role_from_ax', 1, 4, 2).
python_function('src/vdisplay/control/providers/ax_impl.py', '_ax_bounds', 1, 5, 3).
python_function('src/vdisplay/control/providers/ax_impl.py', '_matches_role', 2, 2, 2).
python_function('src/vdisplay/control/providers/ax_impl.py', '_matches_name_fields', 2, 6, 2).
python_function('src/vdisplay/control/providers/ax_impl.py', '_matches_window_fields', 2, 10, 1).
python_function('src/vdisplay/control/providers/ax_impl.py', '_matches_selector', 2, 3, 3).
python_function('src/vdisplay/control/providers/ax_impl.py', 'filter_records', 2, 3, 1).
python_function('src/vdisplay/control/providers/ax_impl.py', 'create_ax_backend', 1, 2, 1).
python_function('src/vdisplay/control/providers/browser_playwright.py', '_playwright_available', 0, 3, 1).
python_function('src/vdisplay/control/providers/browser_playwright.py', '_role_for_element', 1, 8, 6).
python_function('src/vdisplay/control/providers/browser_playwright.py', '_capabilities_for', 1, 5, 1).
python_function('src/vdisplay/control/providers/browser_playwright.py', '_actions_for', 1, 3, 1).
python_function('src/vdisplay/control/providers/browser_playwright.py', '_bounds_from_box', 1, 2, 3).
python_function('src/vdisplay/control/providers/browser_playwright.py', '_dom_state', 1, 3, 2).
python_function('src/vdisplay/control/providers/browser_playwright.py', '_node_from_element', 1, 11, 12).
python_function('src/vdisplay/control/providers/browser_session.py', 'new_session_id', 0, 1, 1).
python_function('src/vdisplay/control/providers/browser_session.py', 'default_registry', 0, 1, 0).
python_function('src/vdisplay/control/providers/terminal.py', '_terminal_deps_available', 0, 1, 0).
python_function('src/vdisplay/control/providers/terminal.py', '_parse_ref', 1, 8, 3).
python_function('src/vdisplay/control/providers/terminal.py', '_matches_terminal_node', 2, 14, 2).
python_function('src/vdisplay/control/providers/terminal.py', '_find_terminal_nodes', 2, 3, 2).
python_function('src/vdisplay/control/providers/terminal_screen.py', '_line_node_id', 2, 1, 0).
python_function('src/vdisplay/control/providers/terminal_screen.py', '_cursor_node_id', 1, 1, 0).
python_function('src/vdisplay/control/providers/terminal_screen.py', 'nodes_from_screen', 1, 4, 9).
python_function('src/vdisplay/control/providers/terminal_screen.py', 'new_session_id', 0, 1, 1).
python_function('src/vdisplay/control/providers/terminal_session.py', 'default_registry', 0, 1, 0).
python_function('src/vdisplay/control/providers/uia_impl.py', 'uia_deps_available', 0, 3, 0).
python_function('src/vdisplay/control/providers/uia_impl.py', '_role_from_uia', 1, 3, 3).
python_function('src/vdisplay/control/providers/uia_impl.py', '_rect_to_bounds', 1, 1, 3).
python_function('src/vdisplay/control/providers/uia_impl.py', '_matches_role', 2, 2, 2).
python_function('src/vdisplay/control/providers/uia_impl.py', '_matches_name_fields', 2, 6, 2).
python_function('src/vdisplay/control/providers/uia_impl.py', '_matches_window_fields', 2, 13, 2).
python_function('src/vdisplay/control/providers/uia_impl.py', '_matches_selector', 2, 3, 3).
python_function('src/vdisplay/control/providers/uia_impl.py', '_record_from_uia_element', 1, 13, 9).
python_function('src/vdisplay/control/providers/uia_impl.py', '_passes_uia_filters', 1, 7, 2).
python_function('src/vdisplay/control/providers/uia_impl.py', 'filter_records', 2, 3, 1).
python_function('src/vdisplay/control/providers/uia_impl.py', 'create_uia_backend', 1, 2, 1).
python_function('src/vdisplay/control/providers/x11.py', '_snapshot_hint', 2, 3, 2).
python_function('src/vdisplay/control/providers/x11.py', '_window_to_snapshot', 1, 9, 15).
python_function('src/vdisplay/control/registry.py', '_build_atspi', 0, 1, 1).
python_function('src/vdisplay/control/registry.py', '_build_uia', 0, 1, 1).
python_function('src/vdisplay/control/registry.py', '_build_ax', 0, 1, 1).
python_function('src/vdisplay/control/registry.py', '_build_browser', 0, 1, 1).
python_function('src/vdisplay/control/registry.py', '_build_x11', 0, 1, 1).
python_function('src/vdisplay/control/registry.py', '_build_terminal', 0, 1, 1).
python_function('src/vdisplay/control/registry.py', '_build_vision', 0, 1, 1).
python_function('src/vdisplay/control/registry.py', 'default_provider_registry', 0, 1, 1).
python_function('src/vdisplay/control/router.py', '_eligible_for_profile', 2, 8, 2).
python_function('src/vdisplay/control/router.py', '_select_winner', 2, 9, 7).
python_function('src/vdisplay/control/router.py', 'default_router', 0, 2, 1).
python_function('src/vdisplay/control/routing_semantics.py', 'host_environment_constraints', 1, 1, 2).
python_function('src/vdisplay/control/routing_semantics.py', 'infer_target_environment', 1, 7, 3).
python_function('src/vdisplay/control/routing_semantics.py', 'session_kind_for_target', 1, 1, 1).
python_function('src/vdisplay/control/routing_semantics.py', 'legal_verify_modes_for_target', 1, 2, 2).
python_function('src/vdisplay/control/routing_semantics.py', 'requires_open_session', 1, 1, 0).
python_function('src/vdisplay/control/routing_semantics.py', 'build_routing_semantics', 0, 1, 8).
python_function('src/vdisplay/control/routing_semantics.py', 'host_environment_from_capture_session_type', 1, 1, 1).
python_function('src/vdisplay/control/scoring.py', '_all_provider_names', 0, 3, 4).
python_function('src/vdisplay/control/scoring.py', '_base_score', 1, 2, 1).
python_function('src/vdisplay/control/scoring.py', 'normalize_backend', 1, 4, 3).
python_function('src/vdisplay/control/scoring.py', 'score_to_confidence', 1, 2, 3).
python_function('src/vdisplay/control/scoring.py', '_atspi_ready', 0, 2, 3).
python_function('src/vdisplay/control/scoring.py', '_uia_ready', 0, 2, 2).
python_function('src/vdisplay/control/scoring.py', '_ax_ready', 0, 2, 2).
python_function('src/vdisplay/control/scoring.py', '_browser_ready', 0, 2, 2).
python_function('src/vdisplay/control/scoring.py', '_xdotool_ready', 0, 2, 1).
python_function('src/vdisplay/control/scoring.py', '_xwayland_reachable', 1, 7, 4).
python_function('src/vdisplay/control/scoring.py', '_terminal_ready', 0, 2, 3).
python_function('src/vdisplay/control/scoring.py', '_browser_session_ready', 1, 5, 5).
python_function('src/vdisplay/control/scoring.py', '_vision_ready', 0, 6, 5).
python_function('src/vdisplay/control/scoring.py', '_terminal_session_ready', 1, 4, 4).
python_function('src/vdisplay/control/scoring.py', '_is_terminal_context', 2, 4, 1).
python_function('src/vdisplay/control/scoring.py', '_is_browser_context', 1, 3, 1).
python_function('src/vdisplay/control/scoring.py', '_is_desktop_context', 1, 8, 1).
python_function('src/vdisplay/control/scoring.py', 'selector_context', 2, 6, 5).
python_function('src/vdisplay/control/scoring.py', '_linux_desktop_hosts', 0, 1, 0).
python_function('src/vdisplay/control/scoring.py', '_score_atspi_provider', 1, 10, 4).
python_function('src/vdisplay/control/scoring.py', '_score_uia_provider', 1, 10, 3).
python_function('src/vdisplay/control/scoring.py', '_score_ax_provider', 1, 10, 3).
python_function('src/vdisplay/control/scoring.py', '_score_terminal_provider', 2, 7, 3).
python_function('src/vdisplay/control/scoring.py', '_score_browser_provider', 2, 2, 4).
python_function('src/vdisplay/control/scoring.py', '_browser_context_score', 2, 4, 2).
python_function('src/vdisplay/control/scoring.py', '_browser_session_check', 5, 6, 2).
python_function('src/vdisplay/control/scoring.py', '_x11_linux_eligibility', 2, 4, 2).
python_function('src/vdisplay/control/scoring.py', '_x11_invoke_capabilities', 0, 9, 5).
python_function('src/vdisplay/control/scoring.py', '_x11_context_score', 1, 7, 1).
python_function('src/vdisplay/control/scoring.py', '_score_x11_provider', 2, 1, 4).
python_function('src/vdisplay/control/scoring.py', '_score_vision_provider', 1, 6, 3).
python_function('src/vdisplay/control/scoring.py', '_score_plugin_provider', 2, 11, 2).
python_function('src/vdisplay/control/scoring.py', '_apply_routing_boosts', 3, 7, 4).
python_function('src/vdisplay/control/scoring.py', 'score_provider', 1, 10, 12).
python_function('src/vdisplay/control/scoring.py', 'rank_providers', 0, 8, 11).
python_function('src/vdisplay/control/scoring.py', '_verify_screenshot_only', 2, 4, 0).
python_function('src/vdisplay/control/scoring.py', '_verify_hybrid', 2, 12, 1).
python_function('src/vdisplay/control/scoring.py', 'select_verify_provider', 1, 9, 2).
python_function('src/vdisplay/control/screenshot_verify.py', '_region_from_bounds', 1, 1, 1).
python_function('src/vdisplay/control/screenshot_verify.py', 'enrich_screencast_stream_meta', 1, 4, 3).
python_function('src/vdisplay/control/screenshot_verify.py', '_resolve_screencast_stream_region', 0, 2, 3).
python_function('src/vdisplay/control/screenshot_verify.py', '_region_from_agent_screencast_status', 0, 14, 8).
python_function('src/vdisplay/control/screenshot_verify.py', 'capture_control_screenshot', 0, 3, 7).
python_function('src/vdisplay/control/screenshot_verify.py', '_target_region', 1, 5, 1).
python_function('src/vdisplay/control/screenshot_verify.py', '_maybe_crop_capture', 2, 7, 4).
python_function('src/vdisplay/control/screenshot_verify.py', '_capture_via_agent', 0, 6, 9).
python_function('src/vdisplay/control/screenshot_verify.py', 'diff_png_bytes', 2, 13, 9).
python_function('src/vdisplay/control/screenshot_verify.py', 'verify_screenshot_pair', 2, 1, 2).
python_function('src/vdisplay/control/selector.py', '_infer_selector_environment', 1, 8, 0).
python_function('src/vdisplay/control/selector.py', '_normalize', 1, 2, 2).
python_function('src/vdisplay/control/selector.py', '_role_matches', 2, 3, 1).
python_function('src/vdisplay/control/selector.py', '_app_matches', 2, 4, 1).
python_function('src/vdisplay/control/selector.py', '_window_title_matches', 2, 5, 1).
python_function('src/vdisplay/control/selector.py', '_name_matches', 1, 5, 1).
python_function('src/vdisplay/control/selector.py', '_text_matches', 1, 8, 1).
python_function('src/vdisplay/control/selector.py', '_terminal_line_matches', 2, 3, 2).
python_function('src/vdisplay/control/selector.py', '_terminal_col_matches', 2, 3, 2).
python_function('src/vdisplay/control/selector.py', '_score', 2, 6, 6).
python_function('src/vdisplay/control/selector.py', 'find_matches', 2, 13, 12).
python_function('src/vdisplay/control/selector.py', 'pick_match', 2, 3, 3).
python_function('src/vdisplay/control/selector.py', 'parse_role', 1, 2, 2).
python_function('src/vdisplay/control/selector.py', '_apply_attr', 4, 13, 2).
python_function('src/vdisplay/control/selector.py', 'parse_selector', 1, 14, 9).
python_function('src/vdisplay/control/session.py', 'parse_session_kind', 1, 3, 5).
python_function('src/vdisplay/control/session.py', '_safe_info', 1, 4, 4).
python_function('src/vdisplay/control/session.py', '_safe_capabilities', 1, 4, 4).
python_function('src/vdisplay/control/session.py', 'metadata_from_agent_record', 1, 1, 7).
python_function('src/vdisplay/control/session.py', 'metadata_from_browser_session', 1, 1, 4).
python_function('src/vdisplay/control/session.py', 'metadata_from_terminal_session', 1, 1, 4).
python_function('src/vdisplay/control/session.py', 'build_catalog_from_agent_store', 1, 11, 10).
python_function('src/vdisplay/control/session.py', 'build_catalog_local', 0, 4, 9).
python_function('src/vdisplay/control/session.py', 'merge_catalogs', 0, 5, 5).
python_function('src/vdisplay/control/verifier.py', 'verify_spec_from_flags', 0, 10, 1).
python_function('src/vdisplay/control/verifier.py', '_region_for_verify', 2, 10, 3).
python_function('src/vdisplay/control/verifier.py', '_ocr_text_contains', 2, 8, 5).
python_function('src/vdisplay/control/verifier.py', '_vision_rescue_result', 0, 1, 1).
python_function('src/vdisplay/control/verifier.py', '_aggregate_dual', 2, 6, 2).
python_function('src/vdisplay/control/verifier.py', '_aggregate_screenshot_only', 1, 2, 1).
python_function('src/vdisplay/control/verifier.py', '_aggregate_semantic_only', 3, 5, 1).
python_function('src/vdisplay/control/verifier.py', 'default_verifier', 0, 1, 0).
python_function('src/vdisplay/control/verify.py', '_node_changes', 2, 8, 3).
python_function('src/vdisplay/control/verify.py', '_node_key', 1, 2, 2).
python_function('src/vdisplay/control/verify.py', '_display_text', 1, 5, 0).
python_function('src/vdisplay/control/verify.py', '_subtree_ids', 2, 4, 4).
python_function('src/vdisplay/control/verify.py', '_scope_root_id', 2, 3, 0).
python_function('src/vdisplay/control/verify.py', '_structural_key', 3, 6, 4).
python_function('src/vdisplay/control/verify.py', '_nodes_by_match_key', 2, 5, 3).
python_function('src/vdisplay/control/verify.py', 'diff_snapshots', 2, 6, 8).
python_function('src/vdisplay/control/verify.py', 'snapshot_diff', 2, 1, 1).
python_function('src/vdisplay/control/verify.py', 'collect_changed_nodes', 1, 8, 2).
python_function('src/vdisplay/control/verify.py', '_label_prefix_changes', 2, 9, 8).
python_function('src/vdisplay/control/verify.py', '_label_prefix_changes_by_identity', 2, 11, 5).
python_function('src/vdisplay/control/verify.py', '_selector_change', 3, 4, 2).
python_function('src/vdisplay/control/verify.py', '_handle_selector_verification', 3, 4, 3).
python_function('src/vdisplay/control/verify.py', '_handle_label_verification', 4, 4, 2).
python_function('src/vdisplay/control/verify.py', '_handle_set_value_verification', 4, 7, 4).
python_function('src/vdisplay/control/verify.py', '_handle_focus_verification', 1, 2, 1).
python_function('src/vdisplay/control/verify.py', '_handle_invoke_verification', 4, 8, 3).
python_function('src/vdisplay/control/verify.py', '_add_diff_nodes', 1, 3, 1).
python_function('src/vdisplay/control/verify.py', 'verify_action_result', 0, 9, 13).
python_function('src/vdisplay/control/verify.py', '_is_verified', 2, 12, 3).
python_function('src/vdisplay/control/vision_disambiguate.py', 'item_confidence', 1, 3, 3).
python_function('src/vdisplay/control/vision_disambiguate.py', 'filter_by_confidence', 1, 4, 5).
python_function('src/vdisplay/control/vision_disambiguate.py', 'pick_by_index', 2, 3, 3).
python_function('src/vdisplay/control/vision_disambiguate.py', 'resolve_vision_matches', 2, 1, 4).
python_function('src/vdisplay/control/vision_disambiguate.py', 'vision_threshold', 1, 2, 3).
python_function('src/vdisplay/control/vision_disambiguate.py', 'disambiguation_meta', 0, 3, 0).
python_function('src/vdisplay/control/vision_llm.py', '_truthy', 1, 2, 2).
python_function('src/vdisplay/control/vision_llm.py', '_normalize_model', 1, 2, 3).
python_function('src/vdisplay/control/vision_llm.py', 'vision_llm_settings', 0, 10, 9).
python_function('src/vdisplay/control/vision_llm.py', 'vision_llm_available', 0, 4, 1).
python_function('src/vdisplay/control/vision_llm.py', 'vision_llm_fallback_enabled', 0, 3, 2).
python_function('src/vdisplay/control/vision_llm.py', 'vision_llm_enrich_enabled', 0, 3, 2).
python_function('src/vdisplay/control/vision_llm.py', '_png_to_data_url', 1, 1, 2).
python_function('src/vdisplay/control/vision_llm.py', '_parse_yes_no', 1, 5, 4).
python_function('src/vdisplay/control/vision_llm.py', '_tokenize_expected', 1, 3, 3).
python_function('src/vdisplay/control/vision_llm.py', 'query_vision_llm', 2, 9, 12).
python_function('src/vdisplay/control/vision_llm.py', 'verify_text_in_region', 2, 12, 6).
python_function('src/vdisplay/control/vision_llm.py', 'summarize_region', 1, 3, 2).
python_function('src/vdisplay/control/vision_ocr.py', 'ocr_available', 0, 3, 1).
python_function('src/vdisplay/control/vision_ocr.py', 'ocr_png', 1, 9, 15).
python_function('src/vdisplay/control/vision_ocr.py', '_normalize', 1, 2, 2).
python_function('src/vdisplay/control/vision_ocr.py', '_box_matches', 2, 3, 1).
python_function('src/vdisplay/control/vision_ocr.py', '_match_by_vision_anchor', 2, 7, 5).
python_function('src/vdisplay/control/vision_ocr.py', '_match_by_text_fields', 2, 13, 1).
python_function('src/vdisplay/control/vision_ocr.py', 'match_selector_boxes', 2, 2, 3).
python_function('src/vdisplay/control/vision_ocr.py', 'ocr_find_selector', 2, 1, 2).
python_function('src/vdisplay/control/vision_ocr.py', '_vertical_overlap', 2, 2, 0).
python_function('src/vdisplay/control/vision_ocr.py', '_horizontal_overlap', 2, 2, 0).
python_function('src/vdisplay/control/vision_ocr.py', 'anchor_spatial_relation', 3, 10, 4).
python_function('src/vdisplay/control/vision_ocr.py', '_find_anchor_boxes', 2, 1, 2).
python_function('src/vdisplay/control/vision_ocr.py', 'anchor_spatial_find', 1, 10, 11).
python_function('src/vdisplay/control/vision_ocr.py', 'anchor_based_find', 1, 1, 1).
python_function('src/vdisplay/control/vision_ocr.py', 'ocr_anchor_combined_find', 1, 5, 11).
python_function('src/vdisplay/control/vision_preview.py', 'preview_available', 0, 2, 0).
python_function('src/vdisplay/control/vision_preview.py', 'action_pick_index', 1, 2, 2).
python_function('src/vdisplay/control/vision_preview.py', '_match_kind', 1, 5, 1).
python_function('src/vdisplay/control/vision_preview.py', 'preview_matches_from_nodes', 1, 7, 5).
python_function('src/vdisplay/control/vision_preview.py', 'confidence_color', 1, 5, 0).
python_function('src/vdisplay/control/vision_preview.py', 'render_match_overlay', 2, 10, 21).
python_function('src/vdisplay/control/vision_preview.py', 'build_vision_preview', 2, 10, 10).
python_function('src/vdisplay/control/vision_preview.py', 'write_preview_png', 2, 1, 6).
python_function('src/vdisplay/control/vision_preview.py', 'decode_preview_png', 1, 2, 3).
python_function('src/vdisplay/control/vision_template.py', 'template_available', 0, 2, 0).
python_function('src/vdisplay/control/vision_template.py', 'load_template_png', 1, 7, 9).
python_function('src/vdisplay/control/vision_template.py', '_png_to_gray_array', 1, 1, 5).
python_function('src/vdisplay/control/vision_template.py', 'match_template', 2, 11, 17).
python_function('src/vdisplay/control/vision_template.py', '_dedupe_matches', 1, 5, 3).
python_function('src/vdisplay/control/vision_template.py', '_search_region_for_relation', 2, 8, 5).
python_function('src/vdisplay/control/vision_template.py', 'template_find_selector', 2, 3, 3).
python_function('src/vdisplay/control/vision_template.py', 'match_template_bounds', 4, 3, 4).
python_function('src/vdisplay/control/vision_template.py', 'template_anchor_find', 1, 2, 10).
python_function('src/vdisplay/discovery.py', 'resolve_host_display', 1, 11, 6).
python_function('src/vdisplay/discovery.py', '_display_socket_exists', 1, 2, 5).
python_function('src/vdisplay/discovery.py', '_looks_like_xvfb_only', 1, 4, 4).
python_function('src/vdisplay/discovery.py', 'list_outputs', 1, 8, 15).
python_function('src/vdisplay/discovery.py', '_attach_output_nl', 2, 2, 3).
python_function('src/vdisplay/discovery.py', '_list_monitors', 1, 6, 9).
python_function('src/vdisplay/discovery.py', '_parse_xrandr_query', 1, 8, 8).
python_function('src/vdisplay/discovery.py', '_merge_output_metadata', 2, 3, 3).
python_function('src/vdisplay/discovery.py', 'list_windows', 1, 2, 4).
python_function('src/vdisplay/discovery.py', 'find_window_suggestions', 3, 2, 2).
python_function('src/vdisplay/discovery.py', 'diagnose_display', 1, 10, 15).
python_function('src/vdisplay/discovery.py', '_display_hint', 3, 3, 2).
python_function('src/vdisplay/discovery.py', 'list_monitors', 1, 1, 1).
python_function('src/vdisplay/discovery.py', 'window_discovery_meta', 1, 2, 1).
python_function('src/vdisplay/input/coords.py', 'global_pointer_coords', 3, 10, 8).
python_function('src/vdisplay/input/coords.py', '_global_from_region', 2, 12, 4).
python_function('src/vdisplay/input/coords.py', '_global_from_monitor', 2, 11, 5).
python_function('src/vdisplay/input/coords.py', '_local_to_region_coords', 2, 11, 3).
python_function('src/vdisplay/input/coords.py', '_rotate_local_to_region', 2, 10, 1).
python_function('src/vdisplay/input/coords.py', '_aspect_mismatch', 4, 5, 1).
python_function('src/vdisplay/input/coords.py', '_rotation_for_monitor', 2, 4, 3).
python_function('src/vdisplay/input/coords.py', '_monitor_by_name', 2, 4, 4).
python_function('src/vdisplay/input/linux_ydotool.py', '_ydotool_env', 0, 4, 3).
python_function('src/vdisplay/input/resolve.py', 'resolve_pointer_input', 0, 4, 6).
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
python_function('src/vdisplay/utils.py', 'auto_install_package', 1, 4, 4).
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
python_function('tests/conftest.py', '_isolate_agent_env', 1, 1, 4).
python_function('tests/conftest.py', '_reset_portal_screencast_state', 0, 1, 3).
python_function('tests/conftest.py', '_wait_for_url', 1, 4, 4).
python_function('tests/conftest.py', 'live_agent_url', 0, 1, 14).
python_function('tests/conftest.py', 'agent_client', 0, 1, 4).
python_function('tests/contract/test_contracts.py', 'test_provider_score_contract_maps_confidence', 0, 4, 3).
python_function('tests/contract/test_contracts.py', 'test_control_route_request_from_command', 0, 5, 2).
python_function('tests/contract/test_descriptors.py', 'test_builtin_provider_descriptors_cover_registry', 0, 5, 4).
python_function('tests/contract/test_descriptors.py', 'test_descriptor_for_aliases', 0, 4, 1).
python_function('tests/contract/test_descriptors.py', 'test_terminal_descriptor_declares_session_and_grid', 0, 5, 1).
python_function('tests/contract/test_descriptors.py', 'test_extension_catalog_shape', 0, 11, 2).
python_function('tests/contract/test_descriptors.py', 'test_detect_platform_profile_has_os_family', 0, 5, 3).
python_function('tests/contract/test_descriptors.py', 'test_resolve_host_environment_linux_mapping', 0, 4, 1).
python_function('tests/contract/test_descriptors.py', 'test_resolve_host_environment_other_os', 0, 4, 1).
python_function('tests/contract/test_descriptors.py', 'test_detect_platform_profile_host_environment_matches_display_stack', 1, 3, 4).
python_function('tests/contract/test_providers.py', 'test_registry_lists_builtin_providers', 0, 2, 2).
python_function('tests/contract/test_providers.py', 'test_router_evaluate_without_building_provider', 1, 4, 4).
python_function('tests/contract/test_providers.py', 'test_provider_contract_surface', 1, 7, 10).
python_function('tests/contract/test_providers.py', 'test_rank_providers_returns_contract_scores', 1, 5, 3).
python_function('tests/fixtures/gtk_demo_app.py', 'main', 0, 2, 21).
python_function('tests/test_agent.py', 'test_agent_health', 1, 5, 2).
python_function('tests/test_agent.py', 'test_agent_capabilities', 1, 4, 2).
python_function('tests/test_agent.py', 'test_agent_virtual_session_capture', 2, 7, 7).
python_function('tests/test_agent_api_contract.py', 'test_agent_health_envelope', 1, 5, 2).
python_function('tests/test_agent_api_contract.py', 'test_agent_version_envelope', 1, 5, 2).
python_function('tests/test_agent_api_contract.py', 'test_agent_capabilities_envelope', 1, 5, 2).
python_function('tests/test_agent_api_contract.py', 'test_flatten_envelope_for_sdk', 0, 3, 2).
python_function('tests/test_agent_browser_session.py', 'agent_client_with_browser', 1, 2, 8).
python_function('tests/test_agent_browser_session.py', 'test_agent_browser_open_list_stop', 1, 7, 4).
python_function('tests/test_agent_client.py', 'test_use_agent_false_by_default', 1, 4, 5).
python_function('tests/test_agent_client.py', 'test_resolve_agent_url_auto_detects_live_agent', 2, 2, 6).
python_function('tests/test_agent_client.py', 'test_client_unreachable_raises', 1, 1, 4).
python_function('tests/test_agent_client.py', 'test_probe_retries_after_initial_miss', 1, 3, 6).
python_function('tests/test_agent_client.py', 'test_flatten_agent_envelope_without_vdisplay_agent_package', 0, 3, 1).
python_function('tests/test_agent_client.py', 'test_client_flattens_agent_envelope', 1, 2, 6).
python_function('tests/test_agent_client.py', 'test_virtual_screenshot_routes_local_when_agent_up', 2, 2, 4).
python_function('tests/test_agent_dispatch.py', 'test_dispatch_monitors_via_agent', 1, 4, 5).
python_function('tests/test_agent_dispatch.py', 'test_dsl_bus_uses_executor_when_agent_configured', 1, 3, 5).
python_function('tests/test_agent_integration.py', 'test_agent_client_round_trip_monitors', 2, 3, 4).
python_function('tests/test_agent_integration.py', 'test_dsl_dispatch_round_trip', 2, 6, 2).
python_function('tests/test_agent_integration.py', 'test_rest2vdisplay_round_trip', 2, 5, 7).
python_function('tests/test_agent_integration.py', 'test_virtual_screenshot_round_trip', 3, 4, 7).
python_function('tests/test_agent_sampler.py', 'test_agent_sampler_start_status_stop', 3, 12, 13).
python_function('tests/test_agent_serve_port.py', 'test_parse_ss_pids', 0, 2, 1).
python_function('tests/test_agent_serve_port.py', 'test_ensure_broker_port_free_no_listeners', 1, 1, 2).
python_function('tests/test_agent_serve_port.py', 'test_ensure_broker_port_free_stops_vdisplay_agent', 1, 3, 4).
python_function('tests/test_agent_serve_port.py', 'test_ensure_broker_port_free_rejects_foreign_service', 1, 1, 3).
python_function('tests/test_agent_serve_port.py', 'test_find_listener_pids_excludes_current_pid', 1, 2, 2).
python_function('tests/test_agent_serve_port.py', 'test_stop_pids_ignores_current_pid', 1, 3, 3).
python_function('tests/test_agent_tasks.py', 'agent_client_with_db', 2, 1, 6).
python_function('tests/test_agent_tasks.py', 'test_startup_marks_orphan_tasks_stale', 1, 3, 7).
python_function('tests/test_agent_tasks.py', 'test_sampler_creates_persisted_task', 3, 18, 14).
python_function('tests/test_agent_tasks.py', 'test_virtual_session_registers_task', 1, 8, 3).
python_function('tests/test_agent_terminal_session.py', 'test_agent_open_terminal_session_and_find', 0, 5, 6).
python_function('tests/test_ax_invoke.py', '_submit_button', 0, 1, 2).
python_function('tests/test_ax_invoke.py', '_search_field', 0, 1, 2).
python_function('tests/test_ax_invoke.py', 'test_ax_deps_unavailable_on_linux', 0, 4, 2).
python_function('tests/test_ax_invoke.py', 'test_ax_find_element_by_title', 0, 3, 6).
python_function('tests/test_ax_invoke.py', 'test_ax_click', 0, 3, 6).
python_function('tests/test_ax_invoke.py', 'test_ax_set_value', 0, 3, 6).
python_function('tests/test_ax_invoke.py', 'test_ax_focus', 0, 3, 6).
python_function('tests/test_ax_invoke.py', 'test_ax_fallback_when_unavailable_on_linux', 0, 4, 3).
python_function('tests/test_browser_engine_profiles.py', 'test_normalize_browser_engine_aliases', 0, 5, 1).
python_function('tests/test_browser_engine_profiles.py', 'test_browser_engine_application_profiles_exist', 0, 7, 2).
python_function('tests/test_browser_engine_profiles.py', 'test_browser_session_stores_engine', 1, 4, 7).
python_function('tests/test_browser_engine_profiles.py', 'test_infer_browser_firefox_profile_from_session', 1, 4, 6).
python_function('tests/test_browser_engine_profiles.py', 'test_routing_prefers_browser_with_firefox_session', 1, 8, 9).
python_function('tests/test_browser_engine_profiles.py', 'test_web_spa_fallback_without_engine_session', 0, 3, 2).
python_function('tests/test_browser_engine_profiles.py', 'test_dsl_browser_open_vendor_flag', 0, 3, 2).
python_function('tests/test_browser_engine_profiles.py', 'test_diagnose_control_includes_browser_engine', 1, 4, 6).
python_function('tests/test_browser_engine_profiles.py', 'test_builtin_provider_count_unchanged', 0, 4, 3).
python_function('tests/test_browser_engine_profiles.py', 'test_dispatch_browser_open_passes_engine', 1, 3, 4).
python_function('tests/test_browser_session_detached.py', 'clean_web1', 0, 1, 3).
python_function('tests/test_browser_session_detached.py', 'test_detached_session_survives_registry_reset', 2, 6, 14).
python_function('tests/test_capture_all_monitors.py', '_make_png', 3, 1, 4).
python_function('tests/test_capture_all_monitors.py', 'test_capture_all_monitors_uses_single_screencast_frame', 2, 5, 4).
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
python_function('tests/test_cli_control_args.py', 'test_control_list_accepts_session_id', 0, 4, 2).
python_function('tests/test_cli_control_args.py', 'test_diagnose_control_accepts_selector_and_session_id', 0, 4, 2).
python_function('tests/test_cli_control_args.py', 'test_selector_from_kwargs_merges_session_id_after_css_parse', 0, 4, 1).
python_function('tests/test_cli_control_args.py', 'test_control_browser_open_parser', 0, 5, 2).
python_function('tests/test_cli_control_args.py', 'test_control_click_does_not_duplicate_backend', 1, 4, 5).
python_function('tests/test_cli_control_args.py', 'test_control_list_invokes_service_with_session_id', 1, 4, 5).
python_function('tests/test_cli_session.py', 'test_root_parser_accepts_audit_session_flags', 0, 4, 2).
python_function('tests/test_cli_session.py', 'test_apply_cli_session_args_sets_env', 1, 3, 5).
python_function('tests/test_cli_session.py', 'test_enrich_command_request_uses_env_session_id', 1, 3, 3).
python_function('tests/test_cli_session.py', 'test_artifacts_from_screenshot_paths', 1, 3, 4).
python_function('tests/test_cli_session.py', 'test_artifacts_from_control_preview_and_diff', 1, 3, 3).
python_function('tests/test_cli_session.py', 'test_executor_records_control_cli_step', 2, 5, 9).
python_function('tests/test_cli_session.py', 'test_build_artifacts_for_screenshot_verb', 1, 2, 5).
python_function('tests/test_client_request.py', 'test_route_command_health', 0, 4, 2).
python_function('tests/test_client_request.py', 'test_route_command_windows_query', 0, 7, 3).
python_function('tests/test_client_request.py', 'test_request_delegates_to_http', 1, 4, 5).
python_function('tests/test_command_contract.py', 'test_command_request_from_dsl_monitors', 0, 4, 1).
python_function('tests/test_command_contract.py', 'test_command_request_from_dsl_apps_only', 0, 3, 1).
python_function('tests/test_command_contract.py', 'test_command_result_envelope_success', 0, 5, 2).
python_function('tests/test_command_contract.py', 'test_command_result_envelope_failure', 0, 4, 3).
python_function('tests/test_command_contract.py', 'test_command_request_from_dsl_control_click', 0, 8, 1).
python_function('tests/test_command_contract.py', 'test_command_result_to_dsl_result', 0, 4, 2).
python_function('tests/test_control_agent.py', 'test_agent_control_diagnostics', 2, 7, 4).
python_function('tests/test_control_agent.py', 'test_agent_controls_list', 2, 3, 3).
python_function('tests/test_control_app_matching.py', '_node', 1, 1, 1).
python_function('tests/test_control_app_matching.py', 'test_app_matches_process_name', 0, 2, 4).
python_function('tests/test_control_app_matching.py', 'test_app_matches_window_title', 0, 2, 4).
python_function('tests/test_control_app_matching.py', 'test_window_title_selector', 0, 3, 3).
python_function('tests/test_control_atspi.py', '_probe_atspi_integration', 0, 3, 2).
python_function('tests/test_control_atspi.py', '_atspi_integration_ready', 0, 1, 1).
python_function('tests/test_control_atspi.py', 'atspi_provider', 0, 2, 3).
python_function('tests/test_control_atspi.py', 'test_atspi_snapshot_lists_nodes', 1, 3, 4).
python_function('tests/test_control_atspi.py', 'test_controls_list_cli_integration', 1, 6, 6).
python_function('tests/test_control_browser.py', 'test_browser_provider_snapshot_and_find', 0, 6, 6).
python_function('tests/test_control_browser.py', 'test_browser_provider_actions', 0, 7, 7).
python_function('tests/test_control_browser.py', 'test_resolve_browser_backend_with_injected_page', 0, 2, 3).
python_function('tests/test_control_browser.py', 'test_resolve_browser_backend_without_playwright', 1, 3, 2).
python_function('tests/test_control_browser_session.py', 'registry', 1, 1, 3).
python_function('tests/test_control_browser_session.py', 'test_browser_registry_open_mock_and_close', 1, 4, 4).
python_function('tests/test_control_browser_session.py', 'test_provider_requires_session_without_legacy_page', 1, 1, 3).
python_function('tests/test_control_browser_session.py', 'test_provider_uses_registry_session', 1, 3, 7).
python_function('tests/test_control_browser_session.py', 'test_browser_session_scoring_ineligible_without_open_session', 1, 5, 5).
python_function('tests/test_control_browser_verify.py', 'test_dom_verify_set_value', 0, 5, 10).
python_function('tests/test_control_capabilities.py', 'test_element_capabilities_roundtrip', 0, 2, 3).
python_function('tests/test_control_capabilities.py', 'test_control_node_serializes_capabilities_and_actions', 0, 5, 5).
python_function('tests/test_control_capabilities.py', 'test_atspi_snapshot_deserializes_actions_and_capabilities', 1, 6, 1).
python_function('tests/test_control_executor.py', 'test_executor_control_click_local', 1, 4, 3).
python_function('tests/test_control_executor.py', 'test_executor_controls_find_local', 1, 4, 3).
python_function('tests/test_control_executor.py', 'test_executor_diagnose_control_local', 1, 4, 3).
python_function('tests/test_control_gtk_demo.py', '_atspi_available', 0, 1, 2).
python_function('tests/test_control_gtk_demo.py', '_display_available', 0, 1, 2).
python_function('tests/test_control_gtk_demo.py', '_app_selector', 0, 1, 0).
python_function('tests/test_control_gtk_demo.py', '_find_selector', 0, 1, 0).
python_function('tests/test_control_gtk_demo.py', '_find_increment', 0, 3, 3).
python_function('tests/test_control_gtk_demo.py', '_wait_for_gtk_demo', 0, 4, 4).
python_function('tests/test_control_gtk_demo.py', '_ensure_gtk_demo_ready', 1, 4, 4).
python_function('tests/test_control_gtk_demo.py', 'gtk_demo_session', 0, 6, 13).
python_function('tests/test_control_gtk_demo.py', 'gtk_demo_process', 1, 1, 1).
python_function('tests/test_control_gtk_demo.py', 'gtk_demo_window', 1, 1, 1).
python_function('tests/test_control_gtk_demo.py', 'test_gtk_demo_find_increment_button', 1, 4, 5).
python_function('tests/test_control_gtk_demo.py', 'test_gtk_demo_list_by_window_title', 1, 5, 7).
python_function('tests/test_control_gtk_demo.py', 'test_gtk_demo_click_verify_label', 1, 6, 7).
python_function('tests/test_control_gtk_demo.py', 'test_gtk_demo_set_value_verify', 1, 5, 7).
python_function('tests/test_control_plugins.py', '_reset_plugins', 0, 1, 2).
python_function('tests/test_control_plugins.py', 'test_register_and_list_plugin', 0, 4, 9).
python_function('tests/test_control_plugins.py', 'test_unregister_manual_plugin', 0, 4, 7).
python_function('tests/test_control_plugins.py', 'test_extension_catalog_includes_plugins', 1, 4, 3).
python_function('tests/test_control_policy.py', 'test_assess_control_capability_returns_contract', 1, 4, 3).
python_function('tests/test_control_policy_v2.py', '_mock_ready', 1, 1, 1).
python_function('tests/test_control_policy_v2.py', 'test_auto_prefers_atspi_for_desktop_selector', 1, 5, 3).
python_function('tests/test_control_policy_v2.py', 'test_auto_prefers_terminal_for_terminal_context', 1, 6, 5).
python_function('tests/test_control_policy_v2.py', 'test_auto_prefers_browser_for_dom_selector', 1, 5, 5).
python_function('tests/test_control_policy_v2.py', 'test_terminal_ineligible_without_open_session', 1, 7, 4).
python_function('tests/test_control_policy_v2.py', 'test_explicit_backend_respects_forced_provider', 1, 4, 2).
python_function('tests/test_control_policy_v2.py', 'test_explicit_backend_raises_when_ineligible', 1, 1, 3).
python_function('tests/test_control_policy_v2.py', 'test_rank_providers_orders_by_score', 1, 6, 4).
python_function('tests/test_control_policy_v2.py', 'test_diagnose_control_includes_routing', 1, 8, 3).
python_function('tests/test_control_policy_v2.py', 'test_routing_decision_serializes', 1, 5, 4).
python_function('tests/test_control_screenshot_verify.py', '_png', 1, 1, 4).
python_function('tests/test_control_screenshot_verify.py', 'test_diff_png_detects_change', 0, 3, 2).
python_function('tests/test_control_screenshot_verify.py', 'test_diff_png_identical_is_not_verified', 0, 3, 2).
python_function('tests/test_control_screenshot_verify.py', 'test_diff_png_small_change_on_large_frame', 0, 2, 8).
python_function('tests/test_control_screenshot_verify.py', 'test_verify_screenshot_pair_payload', 0, 3, 2).
python_function('tests/test_control_screenshot_verify.py', 'test_capture_via_agent_when_configured', 1, 4, 5).
python_function('tests/test_control_screenshot_verify.py', 'test_capture_control_screenshot_uses_target_region', 0, 4, 4).
python_function('tests/test_control_screenshot_verify.py', 'test_execute_action_screenshot_verify_only', 1, 5, 10).
python_function('tests/test_control_screenshot_verify.py', 'test_execute_action_dual_verify_requires_both', 1, 4, 9).
python_function('tests/test_control_selector.py', '_node', 1, 1, 2).
python_function('tests/test_control_selector.py', 'test_parse_selector_button_name', 0, 3, 1).
python_function('tests/test_control_selector.py', 'test_find_and_pick_match', 0, 4, 4).
python_function('tests/test_control_selector_v2.py', '_node', 1, 1, 2).
python_function('tests/test_control_selector_v2.py', 'test_selector_roundtrip', 0, 7, 3).
python_function('tests/test_control_selector_v2.py', 'test_parse_css_and_xpath', 0, 5, 1).
python_function('tests/test_control_selector_v2.py', 'test_parse_window_title_and_text_attrs', 0, 4, 1).
python_function('tests/test_control_selector_v2.py', 'test_find_by_accessibility_id_and_text', 0, 3, 3).
python_function('tests/test_control_selector_v2.py', 'test_active_fields_per_environment', 0, 4, 2).
python_function('tests/test_control_set_value_verify.py', 'test_resolve_verify_mode_set_value_uses_ocr_contains_for_vision', 0, 4, 1).
python_function('tests/test_control_set_value_verify.py', 'test_build_action_payload_fails_ok_when_verify_false', 0, 4, 6).
python_function('tests/test_control_set_value_verify.py', 'test_control_set_value_verify_mode_ocr_contains', 1, 4, 9).
python_function('tests/test_control_terminal.py', '_demo_registry', 0, 1, 2).
python_function('tests/test_control_terminal.py', '_seed_default_demo', 0, 1, 3).
python_function('tests/test_control_terminal.py', 'test_terminal_screen_nodes', 0, 7, 7).
python_function('tests/test_control_terminal.py', 'test_terminal_provider_snapshot_and_find', 0, 6, 8).
python_function('tests/test_control_terminal.py', 'test_terminal_provider_actions', 0, 5, 7).
python_function('tests/test_control_terminal.py', 'test_terminal_selector_parse_and_match', 0, 6, 5).
python_function('tests/test_control_terminal.py', 'test_terminal_service_set_value', 0, 4, 6).
python_function('tests/test_control_terminal.py', 'test_terminal_service_verify_text_change', 0, 3, 4).
python_function('tests/test_control_terminal.py', 'test_resolve_provider_terminal_backend', 0, 2, 4).
python_function('tests/test_control_terminal.py', 'test_resolve_provider_auto_routes_terminal_environment', 0, 2, 5).
python_function('tests/test_control_terminal.py', 'test_resolve_provider_unknown_backend', 0, 4, 4).
python_function('tests/test_control_terminal.py', 'test_terminal_service_missing_session_raises', 0, 2, 4).
python_function('tests/test_control_verifier_hybrid.py', '_png', 1, 1, 4).
python_function('tests/test_control_verifier_hybrid.py', 'test_verify_spec_from_dual_flags', 0, 3, 1).
python_function('tests/test_control_verifier_hybrid.py', 'test_hybrid_rescues_failed_semantic_with_visual', 1, 5, 10).
python_function('tests/test_control_verifier_hybrid.py', 'test_strict_dual_verify_still_requires_both', 1, 2, 9).
python_function('tests/test_control_verifier_hybrid.py', 'test_verifier_pipeline_semantic_only', 0, 3, 8).
python_function('tests/test_control_verify.py', '_node', 1, 3, 2).
python_function('tests/test_control_verify.py', '_gtk_demo_snapshots', 0, 1, 2).
python_function('tests/test_control_verify.py', 'test_diff_snapshots_detects_label_change', 0, 5, 3).
python_function('tests/test_control_verify.py', 'test_verify_click_detects_sibling_label_change', 0, 3, 2).
python_function('tests/test_control_verify.py', 'test_verify_click_with_verify_label', 0, 4, 2).
python_function('tests/test_control_verify.py', 'test_verify_label_falls_back_to_identity_when_structure_shifts', 0, 3, 3).
python_function('tests/test_control_verify.py', 'test_verify_click_with_verify_selector', 0, 3, 2).
python_function('tests/test_control_verify.py', 'test_verify_set_value_checks_expected_text', 0, 3, 3).
python_function('tests/test_control_verify.py', 'test_snapshot_diff_alias_matches_diff_snapshots', 0, 2, 3).
python_function('tests/test_control_verify.py', 'test_collect_changed_nodes_flattens_diff', 0, 4, 4).
python_function('tests/test_control_verify.py', 'test_verify_detects_focus_change_without_value_change', 0, 3, 3).
python_function('tests/test_control_verify.py', 'test_verify_fails_when_nothing_changes', 0, 3, 2).
python_function('tests/test_coords_rotation.py', 'test_global_pointer_coords_rotated_left_aspect_mismatch', 0, 4, 1).
python_function('tests/test_coords_rotation.py', 'test_global_pointer_coords_monitor_1to1_on_normal_rotation', 1, 4, 2).
python_function('tests/test_cross_platform_providers.py', '_mock_linux_readiness', 1, 1, 1).
python_function('tests/test_cross_platform_providers.py', '_mock_platform', 1, 1, 2).
python_function('tests/test_cross_platform_providers.py', 'test_builtin_provider_count_includes_cross_platform_stubs', 0, 4, 3).
python_function('tests/test_cross_platform_providers.py', 'test_uia_stub_unavailable_on_linux', 0, 3, 2).
python_function('tests/test_cross_platform_providers.py', 'test_ax_stub_unavailable_on_linux', 0, 3, 2).
python_function('tests/test_cross_platform_providers.py', 'test_linux_desktop_routes_atspi_not_uia_or_ax', 1, 8, 5).
python_function('tests/test_cross_platform_providers.py', 'test_windows_desktop_routes_uia', 1, 6, 6).
python_function('tests/test_cross_platform_providers.py', 'test_macos_desktop_routes_ax', 1, 6, 6).
python_function('tests/test_cross_platform_providers.py', 'test_native_windows_profile_only_on_windows_host', 1, 5, 3).
python_function('tests/test_cross_platform_providers.py', 'test_uia_find_by_accessibility_id', 0, 3, 7).
python_function('tests/test_dsl_browser_open.py', 'test_parse_browser_open_session_alias', 0, 3, 1).
python_function('tests/test_dsl_browser_open.py', 'test_parse_browser_open_line', 0, 6, 1).
python_function('tests/test_dsl_browser_open.py', 'test_browser_open_schema_requires_url', 0, 2, 3).
python_function('tests/test_dsl_browser_open.py', 'test_command_request_from_dsl_browser_open', 0, 8, 2).
python_function('tests/test_dsl_browser_open.py', 'test_to_text_roundtrip_browser_open', 0, 6, 2).
python_function('tests/test_dsl_browser_open.py', 'test_dispatch_browser_open_local', 1, 5, 4).
python_function('tests/test_dsl_browser_open.py', 'test_browser_open_e2e_local', 1, 4, 7).
python_function('tests/test_dsl_browser_open.py', 'test_browser_open_enables_dom_provider_eligibility', 1, 8, 9).
python_function('tests/test_dsl_browser_open.py', 'test_agent_client_browser_open_route', 0, 5, 3).
python_function('tests/test_dsl_browser_open.py', 'test_dispatch_browser_open_via_executor', 1, 3, 3).
python_function('tests/test_dsl_terminal_control.py', 'test_dsl_terminal_set_value_end_to_end', 1, 9, 10).
python_function('tests/test_dsl_terminal_open.py', 'test_parse_terminal_open_line', 0, 6, 1).
python_function('tests/test_dsl_terminal_open.py', 'test_command_request_from_dsl_terminal_open', 0, 5, 2).
python_function('tests/test_dsl_terminal_open.py', 'test_dispatch_terminal_open_local', 1, 4, 4).
python_function('tests/test_dsl_terminal_open.py', 'test_terminal_open_e2e_local', 0, 4, 4).
python_function('tests/test_dsl_terminal_open.py', 'test_dispatch_terminal_open_via_executor', 1, 3, 3).
python_function('tests/test_example_control_plugin.py', '_reset_plugins', 0, 1, 2).
python_function('tests/test_example_control_plugin.py', 'test_echo_provider_contract', 0, 7, 6).
python_function('tests/test_example_control_plugin.py', 'test_register_plugin_via_entry_point_helper', 0, 7, 7).
python_function('tests/test_example_control_plugin.py', 'test_unregister_echo_restores_builtin_count', 0, 4, 6).
python_function('tests/test_example_control_plugin.py', 'test_echo_routing_eligible_with_forced_backend', 1, 5, 5).
python_function('tests/test_example_uia_ax_plugins.py', '_reset_plugins', 0, 1, 2).
python_function('tests/test_example_uia_ax_plugins.py', '_mock_readiness', 1, 1, 1).
python_function('tests/test_example_uia_ax_plugins.py', 'test_example_uia_mock_contract', 0, 7, 7).
python_function('tests/test_example_uia_ax_plugins.py', 'test_example_ax_mock_contract', 0, 7, 7).
python_function('tests/test_example_uia_ax_plugins.py', 'test_register_uia_plugin_via_entry_point', 0, 7, 7).
python_function('tests/test_example_uia_ax_plugins.py', 'test_register_ax_plugin_via_entry_point', 0, 7, 7).
python_function('tests/test_example_uia_ax_plugins.py', 'test_unregister_example_plugins_restores_builtin_count', 0, 5, 6).
python_function('tests/test_example_uia_ax_plugins.py', 'test_example_uia_forced_routing', 1, 5, 5).
python_function('tests/test_example_uia_ax_plugins.py', 'test_example_ax_forced_routing', 1, 5, 5).
python_function('tests/test_execution_policy.py', 'test_execution_policy_routes_to_agent_when_url_set', 1, 2, 5).
python_function('tests/test_execution_policy.py', 'test_execution_policy_routes_local_inside_broker', 1, 2, 4).
python_function('tests/test_execution_policy.py', 'test_execution_policy_routes_local_without_url', 1, 2, 4).
python_function('tests/test_execution_policy.py', 'test_execute_health_local', 1, 4, 3).
python_function('tests/test_execution_policy.py', 'test_execute_monitors_via_agent', 1, 4, 6).
python_function('tests/test_gui_map.py', '_fake_png', 0, 1, 4).
python_function('tests/test_gui_map.py', 'test_action_bounds_expands_narrow_ocr_box', 0, 3, 3).
python_function('tests/test_gui_map.py', 'test_element_from_ocr_box_records_raw_and_action_bounds', 0, 5, 4).
python_function('tests/test_gui_map.py', 'test_build_and_load_gui_map_roundtrip', 2, 6, 10).
python_function('tests/test_gui_map.py', 'test_map_markdown_and_svg_export', 0, 5, 9).
python_function('tests/test_gui_map.py', 'test_verify_hints_from_map_element', 0, 2, 4).
python_function('tests/test_gui_map.py', 'test_resolve_map_verify_mode_prefers_vision_only_paths', 0, 3, 4).
python_function('tests/test_gui_map.py', 'test_map_action_verify_uses_resolved_mode_not_semantic', 2, 4, 14).
python_function('tests/test_gui_map.py', 'test_map_based_control_click_uses_stored_click_point', 2, 8, 18).
python_function('tests/test_gui_map_diff.py', '_fake_png', 0, 1, 4).
python_function('tests/test_gui_map_diff.py', '_sample_pack', 1, 1, 6).
python_function('tests/test_gui_map_diff.py', 'test_match_ocr_box_for_element_prefers_label_and_nearest', 0, 3, 5).
python_function('tests/test_gui_map_diff.py', 'test_diff_gui_map_ok_when_stable', 1, 4, 6).
python_function('tests/test_gui_map_diff.py', 'test_diff_gui_map_detects_bounds_drift', 1, 3, 6).
python_function('tests/test_gui_map_diff.py', 'test_diff_gui_map_detects_missing_anchor', 1, 3, 4).
python_function('tests/test_gui_map_diff.py', 'test_refresh_gui_map_updates_bounds', 2, 4, 8).
python_function('tests/test_gui_map_diff.py', 'test_map_diff_service', 2, 3, 8).
python_function('tests/test_gui_map_diff.py', 'test_assess_map_drift_refresh_required_on_many_missing', 0, 5, 3).
python_function('tests/test_gui_map_diff.py', 'test_build_gui_map_scoped_crop_filters_outside_boxes', 1, 3, 7).
python_function('tests/test_gui_map_diff.py', 'test_map_capture_prefers_agent_screencast', 1, 3, 4).
python_function('tests/test_gui_map_diff.py', 'test_map_capture_requires_screencast_when_agent_running', 1, 1, 3).
python_function('tests/test_host_capture.py', 'test_capture_host_png_prefers_mirror', 1, 4, 7).
python_function('tests/test_host_capture_errors.py', 'test_host_capture_error_mentions_screencast_on_wayland', 1, 3, 2).
python_function('tests/test_host_capture_errors.py', 'test_capture_host_png_records_inactive_screencast', 1, 2, 6).
python_function('tests/test_img2nl_enrich.py', '_make_png', 3, 1, 4).
python_function('tests/test_img2nl_enrich.py', 'test_enrich_screenshot_payload_adds_nl', 2, 3, 5).
python_function('tests/test_img2nl_enrich.py', 'test_execute_screenshot_enriches_when_img2nl_available', 2, 4, 7).
python_function('tests/test_img2nl_enrich.py', 'test_execute_screenshot_skip_img2nl', 2, 3, 8).
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
python_function('tests/test_nlp_pipeline.py', 'test_run_nl_prompt_full_pipeline', 1, 6, 4).
python_function('tests/test_nlp_pipeline.py', 'test_dsl2vdisplay_monitors_matches_payload', 1, 5, 4).
python_function('tests/test_outputs_rotation.py', 'test_rotation_degrees_mapping', 0, 5, 0).
python_function('tests/test_outputs_rotation.py', 'test_parse_xrandr_query_rotation_from_sample', 0, 7, 3).
python_function('tests/test_portal_screencast.py', '_make_png', 3, 1, 4).
python_function('tests/test_portal_screencast.py', 'test_screencast_session_capture_requires_ready', 0, 1, 3).
python_function('tests/test_portal_screencast.py', '_stub_ready_session', 1, 1, 1).
python_function('tests/test_portal_screencast.py', 'test_host_capture_uses_active_screencast', 1, 3, 4).
python_function('tests/test_portal_screencast.py', 'test_agent_screencast_status_endpoint', 1, 3, 2).
python_function('tests/test_portal_screencast.py', 'test_stop_screencast_when_inactive', 0, 3, 1).
python_function('tests/test_portal_screencast.py', 'test_portal_request_path_uses_bus_unique_name', 0, 2, 2).
python_function('tests/test_portal_screencast.py', 'test_stream_target_prefers_pipewire_serial', 0, 5, 2).
python_function('tests/test_portal_screencast.py', 'test_cli_agent_screencast_status', 3, 3, 5).
python_function('tests/test_portal_screencast.py', 'test_agent_capture_uses_store_screencast', 3, 4, 7).
python_function('tests/test_portal_screencast.py', 'test_capture_pipewire_stream_uses_num_buffers', 1, 7, 7).
python_function('tests/test_portal_screencast.py', 'test_agent_client_screencast_status', 2, 3, 3).
python_function('tests/test_profile_inference.py', 'test_infer_web_spa_from_dom_css', 0, 4, 2).
python_function('tests/test_profile_inference.py', 'test_infer_terminal_pty_from_coordinates', 0, 4, 2).
python_function('tests/test_profile_inference.py', 'test_infer_native_gtk_from_role', 0, 3, 2).
python_function('tests/test_profile_inference.py', 'test_infer_vision_from_anchor', 0, 3, 2).
python_function('tests/test_profile_inference.py', 'test_profile_boost_prefers_browser_for_web_spa', 1, 4, 3).
python_function('tests/test_profile_inference.py', 'test_router_includes_application_profile', 1, 4, 4).
python_function('tests/test_profile_inference.py', 'test_profile_for_builtin_ids', 0, 3, 1).
python_function('tests/test_relay_release.py', '_toolbox_states', 0, 1, 1).
python_function('tests/test_relay_release.py', 'test_state_matches_app_jetbrains', 0, 3, 2).
python_function('tests/test_relay_release.py', 'test_select_adopted_for_release_by_app_includes_frame', 0, 2, 3).
python_function('tests/test_relay_release.py', 'test_stash_roundtrip', 2, 4, 5).
python_function('tests/test_relay_window_region.py', '_make_png', 3, 1, 4).
python_function('tests/test_relay_window_region.py', 'test_relay_screenshot_crops_window_region', 2, 4, 7).
python_function('tests/test_relay_window_region.py', 'test_resolve_window_region_requires_match', 1, 1, 3).
python_function('tests/test_routing_semantics.py', 'test_infer_target_environment_mapping', 0, 4, 2).
python_function('tests/test_routing_semantics.py', 'test_build_routing_semantics_browser_requires_session', 0, 6, 2).
python_function('tests/test_routing_semantics.py', 'test_build_routing_semantics_vision_anchor_visible', 0, 4, 2).
python_function('tests/test_routing_semantics.py', 'test_x11_provider_ineligible_on_wayland_host_without_xwayland', 1, 5, 6).
python_function('tests/test_routing_semantics.py', 'test_x11_provider_eligible_on_wayland_host_with_xwayland', 1, 5, 6).
python_function('tests/test_routing_semantics.py', 'test_routing_decision_includes_semantics', 1, 4, 3).
python_function('tests/test_routing_semantics.py', 'test_assess_control_capability_includes_host_environment', 0, 3, 2).
python_function('tests/test_routing_semantics.py', 'test_assess_control_capability_blocks_pointer_on_wayland', 1, 3, 3).
python_function('tests/test_routing_semantics.py', 'test_assess_control_capability_allows_pointer_via_xwayland', 1, 3, 4).
python_function('tests/test_routing_semantics.py', 'test_capture_policy_includes_host_environment', 1, 2, 2).
python_function('tests/test_routing_semantics.py', 'test_diagnose_unattended_includes_host_environment', 1, 3, 2).
python_function('tests/test_routing_semantics.py', 'test_diagnose_control_includes_routing_semantics', 1, 3, 3).
python_function('tests/test_routing_semantics.py', 'test_execution_policy_meta_includes_host_environment', 0, 2, 2).
python_function('tests/test_sampler_policy.py', 'test_assess_unattended_virtual_display', 0, 5, 1).
python_function('tests/test_sampler_policy.py', 'test_assess_unattended_wayland_without_screencast', 1, 4, 2).
python_function('tests/test_sampler_policy.py', 'test_assess_unattended_wayland_with_screencast', 1, 3, 2).
python_function('tests/test_sampler_policy.py', 'test_assess_unattended_uses_in_process_screencast', 1, 2, 3).
python_function('tests/test_sampler_policy.py', 'test_diagnose_unattended_includes_contract', 1, 4, 2).
python_function('tests/test_sampler_policy.py', 'test_sampler_strict_virtual', 2, 4, 7).
python_function('tests/test_sampler_recovery.py', '_stub_contract', 1, 1, 2).
python_function('tests/test_sampler_recovery.py', 'test_is_screencast_recoverable_error', 0, 4, 1).
python_function('tests/test_sampler_recovery.py', 'test_sampler_recovers_from_blank_screencast', 2, 7, 12).
python_function('tests/test_sampler_recovery.py', 'test_sampler_marks_reconsent_when_recovery_fails', 2, 5, 9).
python_function('tests/test_screencast_multiple.py', 'test_screencast_multiple_explicit', 0, 3, 1).
python_function('tests/test_screencast_multiple.py', 'test_screencast_multiple_env', 1, 4, 3).
python_function('tests/test_screenshot_meta.py', 'test_describe_screenshot_nl', 0, 4, 1).
python_function('tests/test_screenshot_meta.py', 'test_build_and_meta_path', 1, 6, 7).
python_function('tests/test_screenshot_routing.py', 'test_resolve_screenshot_routing_host_with_source', 1, 4, 3).
python_function('tests/test_screenshot_routing.py', 'test_resolve_screenshot_routing_explicit_virtual', 1, 4, 3).
python_function('tests/test_screenshot_routing.py', 'test_resolve_screenshot_routing_virtual_display_override', 1, 4, 3).
python_function('tests/test_screenshot_routing.py', 'test_local_screenshot_handler_uses_host_for_source', 1, 4, 5).
python_function('tests/test_screenshot_routing.py', 'test_agent_screenshot_handler_uses_host_for_source', 1, 4, 6).
python_function('tests/test_session_catalog.py', 'test_parse_session_kind_legacy_strings', 0, 4, 1).
python_function('tests/test_session_catalog.py', 'test_build_catalog_from_agent_store', 0, 7, 6).
python_function('tests/test_session_catalog.py', 'test_build_catalog_local_terminal', 0, 3, 6).
python_function('tests/test_session_catalog.py', 'test_merge_catalogs_dedupes_by_id', 0, 3, 4).
python_function('tests/test_session_recorder.py', 'test_session_recording_disabled_by_default', 1, 2, 2).
python_function('tests/test_session_recorder.py', 'test_executor_writes_session_dir', 2, 9, 10).
python_function('tests/test_session_recorder.py', 'test_collect_artifacts_from_explicit_and_data', 1, 4, 6).
python_function('tests/test_session_recorder.py', 'test_render_readme_includes_routing', 0, 3, 3).
python_function('tests/test_uia_invoke.py', '_ok_button', 0, 1, 2).
python_function('tests/test_uia_invoke.py', '_name_field', 0, 1, 2).
python_function('tests/test_uia_invoke.py', 'test_uia_deps_unavailable_on_linux', 0, 4, 2).
python_function('tests/test_uia_invoke.py', 'test_uia_find_element_by_name', 0, 4, 7).
python_function('tests/test_uia_invoke.py', 'test_uia_find_by_accessibility_id', 0, 3, 6).
python_function('tests/test_uia_invoke.py', 'test_uia_click_invoke_pattern', 0, 3, 6).
python_function('tests/test_uia_invoke.py', 'test_uia_set_value', 0, 3, 6).
python_function('tests/test_uia_invoke.py', 'test_uia_focus', 0, 3, 6).
python_function('tests/test_uia_invoke.py', 'test_uia_fallback_when_unavailable_on_linux', 0, 4, 3).
python_function('tests/test_vision_anchor_matching.py', '_boxes', 0, 1, 2).
python_function('tests/test_vision_anchor_matching.py', 'test_anchor_spatial_relation_right_of', 0, 3, 2).
python_function('tests/test_vision_anchor_matching.py', 'test_anchor_spatial_relation_below', 0, 3, 2).
python_function('tests/test_vision_anchor_matching.py', 'test_anchor_spatial_find_right_of_target', 0, 4, 3).
python_function('tests/test_vision_anchor_matching.py', 'test_anchor_spatial_find_below_target', 0, 4, 3).
python_function('tests/test_vision_anchor_matching.py', 'test_anchor_based_find_alias', 0, 3, 3).
python_function('tests/test_vision_anchor_matching.py', 'test_anchor_fallback_when_ocr_misses', 1, 2, 4).
python_function('tests/test_vision_anchor_matching.py', 'test_vision_find_anchor_spatial_integration', 1, 4, 9).
python_function('tests/test_vision_anchor_matching.py', 'test_ocr_anchor_combined_find_without_template', 1, 3, 4).
python_function('tests/test_vision_anchor_visible_verify.py', '_png', 0, 1, 4).
python_function('tests/test_vision_anchor_visible_verify.py', '_template_png', 0, 1, 4).
python_function('tests/test_vision_anchor_visible_verify.py', '_ctx', 0, 1, 6).
python_function('tests/test_vision_anchor_visible_verify.py', 'test_anchor_visible_ocr_anchor_found', 1, 5, 9).
python_function('tests/test_vision_anchor_visible_verify.py', 'test_select_verify_provider_vision_uses_anchor_visible', 0, 3, 2).
python_function('tests/test_vision_anchor_visible_verify.py', 'test_anchor_visible_template_found', 2, 4, 18).
python_function('tests/test_vision_llm.py', '_png', 1, 1, 4).
python_function('tests/test_vision_llm.py', 'test_vision_llm_fallback_enabled_requires_mode_and_key', 1, 4, 3).
python_function('tests/test_vision_llm.py', 'test_verify_text_in_region_parses_yes', 1, 3, 3).
python_function('tests/test_vision_llm.py', 'test_verifier_vision_llm_fallback_only_when_ocr_fails', 1, 5, 13).
python_function('tests/test_vision_llm.py', 'test_verifier_skips_vision_llm_when_ocr_succeeds', 1, 3, 13).
python_function('tests/test_vision_multimatch_disambiguation.py', '_boxes_duplicate_anchors', 0, 1, 2).
python_function('tests/test_vision_multimatch_disambiguation.py', 'test_filter_by_confidence_drops_weak_matches', 0, 3, 4).
python_function('tests/test_vision_multimatch_disambiguation.py', 'test_pick_by_index_selects_nth_match', 0, 3, 3).
python_function('tests/test_vision_multimatch_disambiguation.py', 'test_resolve_vision_matches_applies_threshold_and_sort', 0, 4, 4).
python_function('tests/test_vision_multimatch_disambiguation.py', 'test_anchor_spatial_find_uses_anchor_index', 0, 4, 3).
python_function('tests/test_vision_multimatch_disambiguation.py', 'test_vision_ocr_index_picks_second_submit', 1, 3, 7).
python_function('tests/test_vision_multimatch_disambiguation.py', 'test_resolve_target_spatial_anchor_index_is_anchor_only', 1, 3, 10).
python_function('tests/test_vision_multimatch_disambiguation.py', 'test_vision_template_min_confidence_filters', 2, 3, 17).
python_function('tests/test_vision_ocr_invoke.py', '_fake_png', 0, 1, 4).
python_function('tests/test_vision_ocr_invoke.py', '_mock_ocr_boxes', 2, 1, 1).
python_function('tests/test_vision_ocr_invoke.py', 'test_match_selector_boxes_vision_anchor_fuzzy', 0, 3, 6).
python_function('tests/test_vision_ocr_invoke.py', 'test_match_selector_boxes_text_exact', 0, 3, 5).
python_function('tests/test_vision_ocr_invoke.py', 'test_vision_find_ocr_returns_bounds', 1, 4, 10).
python_function('tests/test_vision_ocr_invoke.py', 'test_vision_invoke_clicks_expanded_ocr_bounds', 1, 3, 10).
python_function('tests/test_vision_ocr_invoke.py', 'test_vision_set_value_types_after_click', 1, 3, 10).
python_function('tests/test_vision_ocr_invoke.py', 'test_vision_set_value_chat_anchor_skips_gnome_hotkey', 1, 4, 11).
python_function('tests/test_vision_ocr_invoke.py', 'test_vision_ocr_miss_returns_empty_find', 1, 2, 5).
python_function('tests/test_vision_ocr_invoke.py', 'test_vision_only_surface_still_routes_x11_when_ocr_ready', 1, 2, 4).
python_function('tests/test_vision_ocr_invoke.py', 'test_ocr_find_selector_with_mocked_ocr_png', 1, 2, 7).
python_function('tests/test_vision_preview.py', '_fake_png', 2, 1, 4).
python_function('tests/test_vision_preview.py', '_vision_node', 0, 1, 2).
python_function('tests/test_vision_preview.py', 'test_render_match_overlay_draws_boxes', 0, 3, 7).
python_function('tests/test_vision_preview.py', 'test_build_vision_preview_json_and_file', 1, 6, 11).
python_function('tests/test_vision_preview.py', 'test_action_pick_index_spatial_anchor_uses_zero_for_highlight', 0, 2, 2).
python_function('tests/test_vision_preview.py', 'test_controls_find_preview_integration', 2, 6, 10).
python_function('tests/test_vision_preview.py', 'test_preview_matches_from_nodes_skips_empty_bounds', 0, 2, 3).
python_function('tests/test_vision_provider_stub.py', '_mock_readiness', 1, 1, 1).
python_function('tests/test_vision_provider_stub.py', 'test_vision_stub_provider_available', 0, 3, 2).
python_function('tests/test_vision_provider_stub.py', 'test_vision_stub_find_by_anchor', 1, 4, 6).
python_function('tests/test_vision_provider_stub.py', 'test_builtin_provider_count_no_per_engine_explosion', 0, 6, 3).
python_function('tests/test_vision_provider_stub.py', 'test_infer_vision_only_surface_profile', 0, 4, 2).
python_function('tests/test_vision_provider_stub.py', 'test_vision_only_surface_routes_to_x11', 1, 7, 7).
python_function('tests/test_vision_provider_stub.py', 'test_vision_provider_stub_anchor_without_ocr', 1, 6, 7).
python_function('tests/test_vision_provider_stub.py', 'test_routing_semantics_vision_requires_no_session', 0, 6, 3).
python_function('tests/test_vision_provider_stub.py', 'test_vision_routing_on_wayland_host', 1, 8, 6).
python_function('tests/test_vision_provider_stub.py', 'test_x11_fallback_boost_for_vision_profile', 1, 8, 7).
python_function('tests/test_vision_template_matching.py', '_template_png', 0, 3, 6).
python_function('tests/test_vision_template_matching.py', '_screen_with_template_at', 2, 1, 7).
python_function('tests/test_vision_template_matching.py', 'test_match_template_finds_embedded_pattern', 0, 5, 5).
python_function('tests/test_vision_template_matching.py', 'test_vision_find_template_returns_bounds', 2, 6, 12).
python_function('tests/test_vision_template_matching.py', 'test_template_match_threshold_tuning', 0, 4, 6).
python_function('tests/test_vision_template_matching.py', 'test_vision_invoke_clicks_template_center', 2, 3, 12).
python_function('tests/test_wayland_capture_fastfail.py', '_black_png', 0, 1, 4).
python_function('tests/test_wayland_capture_fastfail.py', 'test_blank_screencast_invalidates_session', 1, 2, 5).
python_function('tests/test_wayland_capture_fastfail.py', 'test_wayland_host_capture_skips_slow_driver_fallback', 1, 1, 4).
python_function('tests/test_wayland_input.py', 'test_enrich_screencast_stream_meta_from_agent', 1, 3, 2).
python_function('tests/test_wayland_input.py', 'test_global_pointer_coords_screencast_stream', 0, 4, 2).
python_function('tests/test_wayland_input.py', 'test_global_pointer_coords_region_scale', 0, 4, 2).
python_function('tests/test_wayland_input.py', 'test_global_pointer_coords_monitor_1to1_on_rotation', 1, 4, 2).
python_function('tests/test_wayland_input.py', 'test_global_pointer_coords_local_fallback', 0, 3, 1).
python_function('tests/test_wayland_input.py', 'test_resolve_pointer_input_prefers_ydotool_on_wayland', 1, 2, 3).
python_function('tests/test_wayland_input.py', 'test_resolve_pointer_input_xdotool_on_x11', 1, 2, 2).
python_function('tests/test_wayland_input.py', 'test_vision_pointer_click_uses_ydotool_on_wayland', 1, 5, 7).
python_function('tests/test_windows.py', 'test_parse_wm_class', 0, 3, 1).
python_function('tests/test_windows.py', 'test_derive_app_label_prefers_title', 0, 2, 1).
python_function('tests/test_windows.py', 'test_internal_helper_window', 0, 2, 1).
python_function('tests/test_windows.py', 'test_matches_title_on_app_label', 0, 3, 2).
python_function('tests/test_windows_dedupe.py', 'test_dedupe_prefers_application_over_mutter_frame', 0, 3, 2).

% ── Python Classes ───────────────────────────────────────
python_class('examples/control-plugin/src/vdisplay_example_plugin/my_provider.py', 'EchoControlProvider').
python_method('EchoControlProvider', '__init__', 0, 1, 0).
python_method('EchoControlProvider', 'available', 0, 1, 0).
python_method('EchoControlProvider', 'snapshot', 0, 1, 3).
python_method('EchoControlProvider', 'find', 1, 3, 1).
python_method('EchoControlProvider', 'invoke', 1, 1, 0).
python_method('EchoControlProvider', 'focus', 1, 1, 0).
python_method('EchoControlProvider', 'set_value', 2, 1, 0).
python_method('EchoControlProvider', 'bounds', 1, 2, 1).
python_class('examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py', 'ExampleAxProvider').
python_method('ExampleAxProvider', '__init__', 0, 3, 4).
python_method('ExampleAxProvider', 'available', 0, 2, 3).
python_class('examples/control-plugin-uia/src/vdisplay_example_uia_plugin/provider.py', 'ExampleUiaProvider').
python_method('ExampleUiaProvider', '__init__', 0, 3, 4).
python_method('ExampleUiaProvider', 'available', 0, 2, 3).
python_class('packages/dsl2vdisplay/src/dsl2vdisplay/result.py', 'DslResult').
python_method('DslResult', 'to_dict', 0, 1, 0).
python_class('packages/vdisplay-agent/src/vdisplay_agent/runtime.py', 'AgentRuntime').
python_method('AgentRuntime', 'sessions', 0, 1, 0).
python_method('AgentRuntime', 'relay', 0, 1, 0).
python_method('AgentRuntime', 'platform_capabilities', 0, 1, 1).
python_method('AgentRuntime', 'diagnostics', 0, 1, 1).
python_method('AgentRuntime', 'outputs', 0, 1, 1).
python_method('AgentRuntime', 'list_windows', 0, 1, 1).
python_method('AgentRuntime', 'start_virtual', 0, 1, 1).
python_method('AgentRuntime', 'start_mirror', 0, 1, 1).
python_method('AgentRuntime', 'start_relay', 0, 1, 1).
python_method('AgentRuntime', 'start_terminal', 0, 1, 1).
python_method('AgentRuntime', 'start_browser', 0, 1, 1).
python_method('AgentRuntime', 'start_screencast', 0, 1, 1).
python_method('AgentRuntime', 'stop_screencast', 0, 1, 1).
python_method('AgentRuntime', 'screencast_status', 0, 1, 1).
python_method('AgentRuntime', 'stop_session', 1, 1, 1).
python_method('AgentRuntime', 'recover_tasks', 0, 1, 1).
python_method('AgentRuntime', 'list_tasks', 0, 1, 1).
python_method('AgentRuntime', 'get_task', 1, 1, 1).
python_method('AgentRuntime', 'heartbeat_task', 1, 1, 1).
python_method('AgentRuntime', 'stop_task', 1, 1, 1).
python_method('AgentRuntime', 'list_sessions', 0, 1, 1).
python_method('AgentRuntime', 'start_sampler', 1, 1, 1).
python_method('AgentRuntime', 'stop_sampler', 0, 1, 1).
python_method('AgentRuntime', 'sampler_status', 0, 1, 1).
python_method('AgentRuntime', 'capture_frame', 1, 1, 1).
python_method('AgentRuntime', 'list_control_plugins', 0, 1, 1).
python_method('AgentRuntime', 'diagnose_control', 0, 1, 1).
python_method('AgentRuntime', 'list_controls', 1, 1, 1).
python_method('AgentRuntime', 'find_controls', 1, 1, 1).
python_method('AgentRuntime', 'invoke_control', 1, 1, 1).
python_method('AgentRuntime', 'focus_control', 1, 1, 1).
python_method('AgentRuntime', 'set_control_value', 1, 1, 1).
python_method('AgentRuntime', 'adopt_window', 1, 1, 1).
python_method('AgentRuntime', 'release_window', 1, 1, 1).
python_method('AgentRuntime', 'shutdown', 0, 1, 2).
python_class('packages/vdisplay-agent/src/vdisplay_agent/session_store.py', 'SessionRecord').
python_class('packages/vdisplay-agent/src/vdisplay_agent/session_store.py', 'SessionStore').
python_method('SessionStore', 'register', 0, 1, 2).
python_method('SessionStore', 'get', 1, 2, 2).
python_method('SessionStore', 'pop', 1, 2, 2).
python_method('SessionStore', 'relay_session', 1, 5, 5).
python_method('SessionStore', 'clear_relay', 0, 2, 1).
python_class('packages/vdisplay-agent/src/vdisplay_agent/task_store.py', 'TaskStatus').
python_class('packages/vdisplay-agent/src/vdisplay_agent/task_store.py', 'AgentTask').
python_class('packages/vdisplay-agent/src/vdisplay_agent/task_store.py', 'TaskStore').
python_method('TaskStore', '__init__', 1, 2, 5).
python_method('TaskStore', 'create_task', 0, 3, 8).
python_method('TaskStore', 'get_task', 1, 1, 2).
python_method('TaskStore', 'list_tasks', 0, 3, 8).
python_method('TaskStore', 'update_task', 1, 7, 8).
python_method('TaskStore', 'heartbeat', 1, 4, 2).
python_method('TaskStore', 'mark_orphan_running_as_stale', 1, 3, 8).
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
python_class('src/vdisplay/application/commands.py', 'CommandVerb').
python_class('src/vdisplay/application/commands.py', 'ArtifactRef').
python_method('ArtifactRef', 'to_dict', 0, 6, 0).
python_class('src/vdisplay/application/commands.py', 'CommandRequest').
python_method('CommandRequest', 'action', 0, 3, 1).
python_method('CommandRequest', 'from_dsl', 2, 7, 12).
python_class('src/vdisplay/application/commands.py', 'CommandResult').
python_method('CommandResult', 'to_dict', 0, 6, 1).
python_method('CommandResult', 'to_dsl_result', 0, 4, 2).
python_method('CommandResult', 'success', 1, 4, 1).
python_method('CommandResult', 'failure', 1, 5, 1).
python_class('src/vdisplay/application/errors.py', 'ErrorCode').
python_class('src/vdisplay/application/errors.py', 'ApplicationError').
python_method('ApplicationError', 'to_dict', 0, 1, 0).
python_class('src/vdisplay/application/runtime.py', 'ExecutionPolicy').
python_method('ExecutionPolicy', 'route', 1, 6, 4).
python_method('ExecutionPolicy', 'meta_for', 1, 2, 2).
python_class('src/vdisplay/application/services/sampler.py', 'SamplerConfig').
python_method('SamplerConfig', 'to_loop_config', 0, 1, 1).
python_class('src/vdisplay/application/services/sampler_loop.py', 'SamplerLoopConfig').
python_class('src/vdisplay/application/services/sampler_loop.py', 'SamplerLoopState').
python_class('src/vdisplay/application/services/sampler_loop.py', 'SamplerLoop').
python_method('SamplerLoop', '__init__', 2, 1, 3).
python_method('SamplerLoop', 'start', 0, 2, 10).
python_method('SamplerLoop', 'stop', 0, 3, 5).
python_method('SamplerLoop', 'status', 0, 1, 2).
python_method('SamplerLoop', '_run', 0, 10, 9).
python_method('SamplerLoop', '_capture_frame_iteration', 3, 5, 13).
python_method('SamplerLoop', '_handle_capture_error', 1, 4, 2).
python_class('src/vdisplay/application/session_recorder.py', 'StepRecord').
python_class('src/vdisplay/application/session_recorder.py', 'SessionDocument').
python_method('SessionDocument', 'to_dict', 0, 2, 1).
python_class('src/vdisplay/application/session_recorder.py', 'SessionRecorder').
python_method('SessionRecorder', '__init__', 1, 1, 2).
python_method('SessionRecorder', 'session_dir', 0, 1, 0).
python_method('SessionRecorder', '_load_or_create_document', 0, 13, 17).
python_method('SessionRecorder', 'record', 2, 5, 17).
python_method('SessionRecorder', 'flush', 0, 1, 4).
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
python_class('src/vdisplay/capture/policy.py', 'CaptureCapabilityContract').
python_method('CaptureCapabilityContract', 'to_dict', 0, 1, 1).
python_class('src/vdisplay/capture/portal.py', 'PortalProvider').
python_method('PortalProvider', 'available', 0, 1, 0).
python_method('PortalProvider', 'capture_full', 0, 1, 1).
python_method('PortalProvider', 'capture_region', 1, 1, 2).
python_class('src/vdisplay/capture/portal_screencast.py', 'PortalScreenCastSession').
python_method('PortalScreenCastSession', 'is_ready', 0, 3, 1).
python_method('PortalScreenCastSession', 'start', 0, 6, 10).
python_method('PortalScreenCastSession', '_parse_node_ids', 1, 8, 5).
python_method('PortalScreenCastSession', '_parse_stream_targets', 1, 7, 5).
python_method('PortalScreenCastSession', 'status', 0, 1, 1).
python_method('PortalScreenCastSession', 'capture_png', 0, 6, 7).
python_method('PortalScreenCastSession', 'stop', 0, 5, 4).
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
python_method('MssProvider', 'available', 0, 3, 1).
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
python_method('AgentClient', '_request', 2, 2, 5).
python_method('AgentClient', '_send', 2, 3, 6).
python_method('AgentClient', '_build_request', 2, 3, 3).
python_method('AgentClient', '_http_error_message', 1, 5, 5).
python_method('AgentClient', '_raise_on_error', 1, 5, 4).
python_method('AgentClient', '_normalize_payload', 1, 1, 1).
python_method('AgentClient', 'request', 1, 3, 7).
python_method('AgentClient', 'health', 0, 1, 1).
python_method('AgentClient', 'capabilities', 0, 1, 1).
python_method('AgentClient', 'diagnostics', 0, 2, 1).
python_method('AgentClient', 'outputs', 0, 4, 3).
python_method('AgentClient', 'windows', 0, 4, 3).
python_method('AgentClient', 'start_virtual', 0, 1, 1).
python_method('AgentClient', 'start_mirror', 0, 1, 1).
python_method('AgentClient', 'start_relay', 0, 1, 1).
python_method('AgentClient', 'browser_open', 0, 4, 1).
python_method('AgentClient', 'start_screencast', 0, 2, 1).
python_method('AgentClient', 'stop_screencast', 0, 1, 1).
python_method('AgentClient', 'screencast_status', 0, 1, 1).
python_method('AgentClient', 'stop_session', 1, 1, 1).
python_method('AgentClient', 'sampler_start', 0, 1, 1).
python_method('AgentClient', 'sampler_stop', 0, 1, 1).
python_method('AgentClient', 'sampler_status', 0, 1, 1).
python_method('AgentClient', 'diagnose_control', 0, 2, 1).
python_method('AgentClient', 'list_controls', 1, 2, 1).
python_method('AgentClient', 'find_controls', 1, 1, 1).
python_method('AgentClient', 'invoke_control', 1, 1, 1).
python_method('AgentClient', 'focus_control', 1, 1, 1).
python_method('AgentClient', 'set_control_value', 1, 1, 1).
python_method('AgentClient', 'capture_frame', 0, 2, 1).
python_method('AgentClient', 'capture_png_bytes', 0, 2, 6).
python_method('AgentClient', 'adopt_window', 0, 1, 1).
python_method('AgentClient', 'release_window', 0, 1, 1).
python_class('src/vdisplay/control/base.py', 'ControlProvider').
python_method('ControlProvider', 'available', 0, 1, 0).
python_method('ControlProvider', 'snapshot', 0, 1, 0).
python_method('ControlProvider', 'find', 1, 1, 0).
python_method('ControlProvider', 'invoke', 1, 1, 0).
python_method('ControlProvider', 'focus', 1, 1, 0).
python_method('ControlProvider', 'set_value', 2, 1, 0).
python_method('ControlProvider', 'bounds', 1, 1, 0).
python_method('ControlProvider', 'capabilities', 0, 2, 2).
python_method('ControlProvider', 'verify_modes', 0, 2, 2).
python_method('ControlProvider', 'session_kind', 0, 2, 1).
python_class('src/vdisplay/control/browser_engine.py', 'BrowserEngineKind').
python_class('src/vdisplay/control/browser_session_store.py', 'DetachedBrowserMeta').
python_method('DetachedBrowserMeta', 'to_dict', 0, 1, 1).
python_class('src/vdisplay/control/capabilities.py', 'ProviderCapabilities').
python_method('ProviderCapabilities', 'to_dict', 0, 1, 1).
python_class('src/vdisplay/control/contracts.py', 'ProviderScoreContract').
python_method('ProviderScoreContract', 'to_dict', 0, 2, 2).
python_class('src/vdisplay/control/contracts.py', 'ExecutionContext').
python_method('ExecutionContext', 'to_dict', 0, 2, 2).
python_class('src/vdisplay/control/contracts.py', 'VerifySpec').
python_method('VerifySpec', 'to_dict', 0, 2, 2).
python_class('src/vdisplay/control/contracts.py', 'ProviderResult').
python_method('ProviderResult', 'to_dict', 0, 2, 2).
python_class('src/vdisplay/control/contracts.py', 'ControlRouteRequest').
python_method('ControlRouteRequest', 'to_dict', 0, 2, 2).
python_class('src/vdisplay/control/descriptors.py', 'SelectorExtension').
python_method('SelectorExtension', 'to_dict', 0, 4, 1).
python_class('src/vdisplay/control/descriptors.py', 'HostEnvironmentKind').
python_class('src/vdisplay/control/descriptors.py', 'PlatformProfile').
python_method('PlatformProfile', 'to_dict', 0, 4, 1).
python_class('src/vdisplay/control/descriptors.py', 'ApplicationProfile').
python_method('ApplicationProfile', 'to_dict', 0, 4, 1).
python_class('src/vdisplay/control/descriptors.py', 'ProviderDescriptor').
python_method('ProviderDescriptor', 'to_dict', 0, 4, 3).
python_class('src/vdisplay/control/gui_map.py', 'GuiMapBounds').
python_method('GuiMapBounds', 'from_dict', 2, 7, 3).
python_method('GuiMapBounds', 'to_dict', 0, 3, 0).
python_method('GuiMapBounds', 'from_control_bounds', 2, 1, 1).
python_method('GuiMapBounds', 'to_control_bounds', 0, 1, 1).
python_method('GuiMapBounds', 'center', 0, 1, 0).
python_class('src/vdisplay/control/gui_map.py', 'GuiMapPoint').
python_method('GuiMapPoint', 'from_dict', 2, 7, 3).
python_method('GuiMapPoint', 'to_dict', 0, 3, 0).
python_class('src/vdisplay/control/gui_map.py', 'GuiMapIdentity').
python_method('GuiMapIdentity', 'from_dict', 2, 7, 2).
python_method('GuiMapIdentity', 'to_dict', 0, 3, 0).
python_class('src/vdisplay/control/gui_map.py', 'GuiMapElement').
python_method('GuiMapElement', 'from_dict', 2, 7, 6).
python_method('GuiMapElement', 'to_dict', 0, 3, 3).
python_class('src/vdisplay/control/gui_map.py', 'GuiMapRegion').
python_method('GuiMapRegion', 'from_dict', 2, 7, 5).
python_method('GuiMapRegion', 'to_dict', 0, 3, 2).
python_class('src/vdisplay/control/gui_map.py', 'GuiMapPack').
python_method('GuiMapPack', 'from_dict', 2, 7, 7).
python_method('GuiMapPack', 'to_dict', 0, 3, 3).
python_class('src/vdisplay/control/gui_map_diff.py', 'ElementDrift').
python_method('ElementDrift', 'to_dict', 0, 3, 0).
python_class('src/vdisplay/control/gui_map_diff.py', 'RegionDrift').
python_method('RegionDrift', 'to_dict', 0, 3, 0).
python_class('src/vdisplay/control/gui_map_diff.py', 'GuiMapDiff').
python_method('GuiMapDiff', 'to_dict', 0, 3, 3).
python_class('src/vdisplay/control/models.py', 'EnvironmentKind').
python_class('src/vdisplay/control/models.py', 'ControlRole').
python_class('src/vdisplay/control/models.py', 'ControlActionKind').
python_class('src/vdisplay/control/models.py', 'ControlBounds').
python_method('ControlBounds', 'to_dict', 0, 1, 0).
python_method('ControlBounds', 'center', 0, 1, 0).
python_class('src/vdisplay/control/models.py', 'ControlAction').
python_method('ControlAction', 'to_dict', 0, 1, 0).
python_class('src/vdisplay/control/models.py', 'ElementCapabilities').
python_method('ElementCapabilities', 'to_dict', 0, 1, 0).
python_method('ElementCapabilities', 'from_dict', 2, 2, 3).
python_class('src/vdisplay/control/models.py', 'ControlNode').
python_method('ControlNode', 'to_dict', 0, 1, 2).
python_class('src/vdisplay/control/models.py', 'ControlSnapshot').
python_method('ControlSnapshot', 'to_dict', 0, 1, 4).
python_class('src/vdisplay/control/models.py', 'ActionResult').
python_method('ActionResult', 'to_dict', 0, 1, 1).
python_class('src/vdisplay/control/plugins.py', 'RegisteredPlugin').
python_method('RegisteredPlugin', 'to_dict', 0, 2, 1).
python_class('src/vdisplay/control/policy.py', 'ControlCapabilityContract').
python_method('ControlCapabilityContract', 'to_dict', 0, 1, 1).
python_class('src/vdisplay/control/profile_inference.py', 'ProfileInference').
python_method('ProfileInference', 'to_dict', 0, 2, 3).
python_class('src/vdisplay/control/providers/atspi.py', 'AtspiControlProvider').
python_method('AtspiControlProvider', '__init__', 0, 1, 1).
python_method('AtspiControlProvider', 'available', 0, 6, 5).
python_method('AtspiControlProvider', 'probe_integration', 0, 8, 5).
python_method('AtspiControlProvider', 'snapshot', 0, 2, 3).
python_method('AtspiControlProvider', 'find', 1, 2, 2).
python_method('AtspiControlProvider', 'invoke', 1, 2, 2).
python_method('AtspiControlProvider', 'focus', 1, 2, 2).
python_method('AtspiControlProvider', 'set_value', 2, 2, 2).
python_method('AtspiControlProvider', 'bounds', 1, 3, 2).
python_class('src/vdisplay/control/providers/ax.py', 'AxControlProvider').
python_method('AxControlProvider', '__init__', 0, 1, 1).
python_method('AxControlProvider', 'available', 0, 2, 2).
python_method('AxControlProvider', '_records_to_nodes', 1, 2, 3).
python_method('AxControlProvider', 'snapshot', 0, 3, 4).
python_method('AxControlProvider', 'find', 1, 6, 6).
python_method('AxControlProvider', '_record_for', 1, 6, 7).
python_method('AxControlProvider', 'invoke', 1, 2, 3).
python_method('AxControlProvider', 'focus', 1, 2, 3).
python_method('AxControlProvider', 'set_value', 2, 2, 3).
python_method('AxControlProvider', 'bounds', 1, 3, 2).
python_class('src/vdisplay/control/providers/ax_impl.py', 'AxElementRecord').
python_class('src/vdisplay/control/providers/ax_impl.py', 'AxBackend').
python_method('AxBackend', 'connect', 0, 1, 0).
python_method('AxBackend', 'collect_elements', 0, 5, 0).
python_method('AxBackend', 'invoke', 1, 1, 0).
python_method('AxBackend', 'focus', 1, 1, 0).
python_method('AxBackend', 'set_value', 2, 1, 0).
python_class('src/vdisplay/control/providers/ax_impl.py', 'PyobjcAxBackend').
python_method('PyobjcAxBackend', '__init__', 0, 2, 0).
python_method('PyobjcAxBackend', 'connect', 0, 1, 2).
python_method('PyobjcAxBackend', 'collect_elements', 0, 5, 17).
python_method('PyobjcAxBackend', '_require_record', 1, 4, 2).
python_method('PyobjcAxBackend', 'invoke', 1, 1, 3).
python_method('PyobjcAxBackend', 'focus', 1, 1, 3).
python_method('PyobjcAxBackend', 'set_value', 2, 1, 3).
python_class('src/vdisplay/control/providers/ax_impl.py', 'MockAxBackend').
python_method('MockAxBackend', '__init__', 1, 2, 1).
python_method('MockAxBackend', 'connect', 0, 1, 0).
python_method('MockAxBackend', 'collect_elements', 0, 5, 1).
python_method('MockAxBackend', 'invoke', 1, 1, 1).
python_method('MockAxBackend', 'focus', 1, 1, 1).
python_method('MockAxBackend', 'set_value', 2, 1, 0).
python_class('src/vdisplay/control/providers/browser_playwright.py', '_PageLike').
python_method('_PageLike', 'goto', 1, 1, 0).
python_method('_PageLike', 'title', 0, 1, 0).
python_method('_PageLike', 'query_selector_all', 1, 1, 0).
python_method('_PageLike', 'locator', 1, 1, 0).
python_class('src/vdisplay/control/providers/browser_playwright.py', '_ElementLike').
python_method('_ElementLike', 'evaluate', 1, 1, 0).
python_method('_ElementLike', 'bounding_box', 0, 1, 0).
python_method('_ElementLike', 'inner_text', 0, 1, 0).
python_method('_ElementLike', 'get_attribute', 1, 1, 0).
python_method('_ElementLike', 'click', 0, 1, 0).
python_method('_ElementLike', 'fill', 1, 1, 0).
python_method('_ElementLike', 'focus', 0, 1, 0).
python_class('src/vdisplay/control/providers/browser_playwright.py', 'BrowserPlaywrightProvider').
python_method('BrowserPlaywrightProvider', '__init__', 0, 2, 1).
python_method('BrowserPlaywrightProvider', 'available', 0, 2, 1).
python_method('BrowserPlaywrightProvider', '_resolve_session_id', 0, 8, 3).
python_method('BrowserPlaywrightProvider', '_page_for', 0, 14, 7).
python_method('BrowserPlaywrightProvider', 'snapshot', 0, 5, 7).
python_method('BrowserPlaywrightProvider', 'find', 1, 10, 11).
python_method('BrowserPlaywrightProvider', '_resolve_element', 1, 5, 10).
python_method('BrowserPlaywrightProvider', 'invoke', 1, 1, 2).
python_method('BrowserPlaywrightProvider', 'focus', 1, 1, 2).
python_method('BrowserPlaywrightProvider', 'set_value', 2, 1, 2).
python_method('BrowserPlaywrightProvider', 'bounds', 1, 1, 3).
python_method('BrowserPlaywrightProvider', 'close', 0, 2, 1).
python_class('src/vdisplay/control/providers/browser_session.py', 'BrowserSession').
python_method('BrowserSession', 'close', 0, 2, 2).
python_class('src/vdisplay/control/providers/browser_session.py', 'BrowserSessionRegistry').
python_method('BrowserSessionRegistry', '__init__', 0, 1, 0).
python_method('BrowserSessionRegistry', '_tracks_detached_sessions', 0, 1, 0).
python_method('BrowserSessionRegistry', 'list_ids', 0, 6, 8).
python_method('BrowserSessionRegistry', 'get', 1, 3, 2).
python_method('BrowserSessionRegistry', 'require', 1, 2, 2).
python_method('BrowserSessionRegistry', 'open', 1, 14, 17).
python_method('BrowserSessionRegistry', '_attach', 1, 12, 14).
python_method('BrowserSessionRegistry', 'open_mock', 1, 5, 7).
python_method('BrowserSessionRegistry', 'close', 1, 2, 3).
python_method('BrowserSessionRegistry', 'close_all', 0, 2, 2).
python_class('src/vdisplay/control/providers/terminal.py', 'TerminalControlProvider').
python_method('TerminalControlProvider', '__init__', 0, 2, 1).
python_method('TerminalControlProvider', 'available', 0, 1, 1).
python_method('TerminalControlProvider', '_resolve_session_id', 0, 5, 2).
python_method('TerminalControlProvider', 'snapshot', 0, 2, 6).
python_method('TerminalControlProvider', 'find', 1, 5, 3).
python_method('TerminalControlProvider', 'invoke', 1, 2, 4).
python_method('TerminalControlProvider', 'focus', 1, 4, 6).
python_method('TerminalControlProvider', 'set_value', 2, 2, 4).
python_method('TerminalControlProvider', 'bounds', 1, 3, 2).
python_class('src/vdisplay/control/providers/terminal_screen.py', 'ScreenLine').
python_method('ScreenLine', 'stripped', 0, 1, 1).
python_class('src/vdisplay/control/providers/terminal_screen.py', 'ScreenSnapshot').
python_method('ScreenSnapshot', 'line_at', 1, 3, 0).
python_class('src/vdisplay/control/providers/terminal_screen.py', 'ScreenBuffer').
python_method('ScreenBuffer', '__init__', 0, 2, 3).
python_method('ScreenBuffer', '_init_pyte', 0, 2, 2).
python_method('ScreenBuffer', 'resize', 0, 5, 4).
python_method('ScreenBuffer', 'feed', 1, 5, 6).
python_method('ScreenBuffer', '_sync_from_pyte', 0, 4, 4).
python_method('ScreenBuffer', '_feed_simple', 1, 7, 4).
python_method('ScreenBuffer', 'set_lines', 1, 3, 5).
python_method('ScreenBuffer', 'snapshot', 0, 5, 6).
python_class('src/vdisplay/control/providers/terminal_session.py', 'TerminalSession').
python_method('TerminalSession', 'write', 1, 7, 7).
python_method('TerminalSession', 'send_enter', 0, 1, 1).
python_method('TerminalSession', 'sent_text', 0, 1, 1).
python_method('TerminalSession', 'stop', 0, 1, 1).
python_method('TerminalSession', 'close', 0, 2, 2).
python_method('TerminalSession', '_start_reader', 0, 3, 4).
python_class('src/vdisplay/control/providers/terminal_session.py', 'TerminalSessionRegistry').
python_method('TerminalSessionRegistry', '__init__', 0, 1, 0).
python_method('TerminalSessionRegistry', 'list_ids', 0, 1, 1).
python_method('TerminalSessionRegistry', 'get', 1, 1, 1).
python_method('TerminalSessionRegistry', 'require', 1, 2, 2).
python_method('TerminalSessionRegistry', 'open_mock', 0, 5, 4).
python_method('TerminalSessionRegistry', 'open_process', 1, 4, 6).
python_method('TerminalSessionRegistry', 'open_pexpect', 1, 5, 14).
python_method('TerminalSessionRegistry', 'close', 1, 2, 2).
python_method('TerminalSessionRegistry', 'close_all', 0, 2, 2).
python_class('src/vdisplay/control/providers/uia.py', 'UiaControlProvider').
python_method('UiaControlProvider', '__init__', 0, 1, 1).
python_method('UiaControlProvider', 'available', 0, 2, 2).
python_method('UiaControlProvider', '_records_to_nodes', 1, 2, 3).
python_method('UiaControlProvider', 'snapshot', 0, 3, 4).
python_method('UiaControlProvider', 'find', 1, 6, 6).
python_method('UiaControlProvider', '_record_for', 1, 6, 7).
python_method('UiaControlProvider', 'invoke', 1, 2, 3).
python_method('UiaControlProvider', 'focus', 1, 2, 3).
python_method('UiaControlProvider', 'set_value', 2, 2, 3).
python_method('UiaControlProvider', 'bounds', 1, 3, 2).
python_class('src/vdisplay/control/providers/uia_impl.py', 'UiaElementRecord').
python_class('src/vdisplay/control/providers/uia_impl.py', 'UiaBackend').
python_method('UiaBackend', 'connect', 0, 1, 0).
python_method('UiaBackend', 'collect_elements', 0, 9, 0).
python_method('UiaBackend', 'invoke', 1, 1, 0).
python_method('UiaBackend', 'focus', 1, 1, 0).
python_method('UiaBackend', 'set_value', 2, 1, 0).
python_class('src/vdisplay/control/providers/uia_impl.py', 'ComtypesUiaBackend').
python_method('ComtypesUiaBackend', '__init__', 0, 2, 0).
python_method('ComtypesUiaBackend', 'connect', 0, 1, 4).
python_method('ComtypesUiaBackend', 'collect_elements', 0, 9, 13).
python_method('ComtypesUiaBackend', '_require_record', 1, 4, 2).
python_method('ComtypesUiaBackend', 'invoke', 1, 1, 5).
python_method('ComtypesUiaBackend', 'focus', 1, 1, 7).
python_method('ComtypesUiaBackend', 'set_value', 2, 1, 5).
python_class('src/vdisplay/control/providers/uia_impl.py', 'MockUiaBackend').
python_method('MockUiaBackend', '__init__', 1, 2, 1).
python_method('MockUiaBackend', 'connect', 0, 1, 0).
python_method('MockUiaBackend', 'collect_elements', 0, 9, 2).
python_method('MockUiaBackend', 'invoke', 1, 1, 1).
python_method('MockUiaBackend', 'focus', 1, 1, 1).
python_method('MockUiaBackend', 'set_value', 2, 1, 0).
python_class('src/vdisplay/control/providers/vision/provider.py', 'VisionStubProvider').
python_method('VisionStubProvider', '__init__', 0, 1, 0).
python_method('VisionStubProvider', 'available', 0, 5, 2).
python_method('VisionStubProvider', '_capture_png', 0, 2, 2).
python_method('VisionStubProvider', 'last_capture', 0, 1, 0).
python_method('VisionStubProvider', 'last_find_debug', 0, 1, 0).
python_method('VisionStubProvider', 'enable_preview_debug', 1, 1, 0).
python_method('VisionStubProvider', '_box_key', 1, 1, 0).
python_method('VisionStubProvider', '_record_find_debug', 0, 3, 3).
python_method('VisionStubProvider', '_build_rejected_preview', 2, 9, 5).
python_method('VisionStubProvider', '_node_from_ocr', 1, 1, 1).
python_method('VisionStubProvider', '_node_from_template', 1, 5, 1).
python_method('VisionStubProvider', '_node_from_anchor', 1, 2, 1).
python_method('VisionStubProvider', '_selector_wants_ocr', 1, 6, 1).
python_method('VisionStubProvider', '_find_nodes', 1, 6, 5).
python_method('VisionStubProvider', '_try_ocr_nodes', 1, 4, 4).
python_method('VisionStubProvider', '_try_template_nodes', 1, 4, 3).
python_method('VisionStubProvider', '_try_anchor_nodes', 1, 4, 2).
python_method('VisionStubProvider', '_maybe_stub_fast_path', 1, 5, 2).
python_method('VisionStubProvider', '_maybe_stub_fallback', 1, 4, 2).
python_method('VisionStubProvider', '_ensure_png', 2, 2, 1).
python_method('VisionStubProvider', '_template_nodes_from_png', 3, 4, 10).
python_method('VisionStubProvider', '_anchor_nodes_from_png', 3, 10, 11).
python_method('VisionStubProvider', '_ocr_nodes_from_png', 3, 9, 10).
python_method('VisionStubProvider', '_stub_anchor_node', 1, 1, 2).
python_method('VisionStubProvider', 'snapshot', 0, 1, 1).
python_method('VisionStubProvider', 'find', 1, 11, 6).
python_method('VisionStubProvider', '_node_for', 1, 3, 3).
python_method('VisionStubProvider', '_click_node', 1, 7, 4).
python_method('VisionStubProvider', 'invoke_map_node', 1, 1, 1).
python_method('VisionStubProvider', 'focus_map_node', 1, 1, 1).
python_method('VisionStubProvider', 'set_value_map_node', 2, 9, 10).
python_method('VisionStubProvider', '_pointer_click_at', 1, 6, 7).
python_method('VisionStubProvider', 'invoke', 1, 8, 5).
python_method('VisionStubProvider', 'focus', 1, 1, 1).
python_method('VisionStubProvider', 'set_value', 2, 11, 11).
python_method('VisionStubProvider', '_paste_value', 2, 8, 5).
python_method('VisionStubProvider', 'bounds', 1, 1, 1).
python_class('src/vdisplay/control/providers/x11.py', 'X11ControlProvider').
python_method('X11ControlProvider', '__init__', 0, 2, 3).
python_method('X11ControlProvider', 'available', 0, 2, 2).
python_method('X11ControlProvider', 'snapshot', 0, 5, 7).
python_class('src/vdisplay/control/registry.py', 'ProviderRegistry').
python_method('ProviderRegistry', '__init__', 0, 1, 0).
python_method('ProviderRegistry', 'register', 2, 2, 1).
python_method('ProviderRegistry', 'list_names', 0, 1, 1).
python_method('ProviderRegistry', 'list_descriptors', 0, 2, 1).
python_method('ProviderRegistry', 'get_descriptor', 1, 2, 2).
python_method('ProviderRegistry', 'build', 1, 3, 5).
python_class('src/vdisplay/control/router.py', 'RouteResult').
python_method('RouteResult', 'to_dict', 0, 2, 1).
python_class('src/vdisplay/control/router.py', 'ControlRouter').
python_method('ControlRouter', '__init__', 1, 2, 1).
python_method('ControlRouter', '_normalize_request', 1, 8, 2).
python_method('ControlRouter', 'evaluate', 1, 2, 5).
python_method('ControlRouter', 'route', 1, 4, 5).
python_method('ControlRouter', 'route_command', 1, 1, 2).
python_method('ControlRouter', '_build_decision', 0, 7, 9).
python_class('src/vdisplay/control/routing_semantics.py', 'RoutingSemantics').
python_method('RoutingSemantics', 'to_dict', 0, 3, 2).
python_class('src/vdisplay/control/scoring.py', 'ProviderScore').
python_method('ProviderScore', 'to_dict', 0, 5, 1).
python_class('src/vdisplay/control/scoring.py', 'ProviderRoutingDecision').
python_method('ProviderRoutingDecision', 'to_dict', 0, 5, 3).
python_class('src/vdisplay/control/selector.py', 'ControlSelector').
python_method('ControlSelector', 'from_dict', 2, 7, 8).
python_method('ControlSelector', 'to_dict', 0, 6, 3).
python_method('ControlSelector', 'active_fields', 0, 9, 5).
python_class('src/vdisplay/control/session.py', 'SessionMetadata').
python_method('SessionMetadata', 'to_dict', 0, 2, 1).
python_class('src/vdisplay/control/session.py', 'SessionCatalog').
python_method('SessionCatalog', 'to_dict', 0, 2, 2).
python_class('src/vdisplay/control/session.py', 'AgentSessionStore').
python_class('src/vdisplay/control/session_kind.py', 'SessionKind').
python_class('src/vdisplay/control/verifier.py', 'VerifyContext').
python_class('src/vdisplay/control/verifier.py', 'VerificationResult').
python_method('VerificationResult', 'to_dict', 0, 1, 1).
python_class('src/vdisplay/control/verifier.py', 'VerifierPipeline').
python_method('VerifierPipeline', '_run_semantic_if_needed', 1, 2, 3).
python_method('VerifierPipeline', '_run_visual_if_needed', 3, 9, 3).
python_method('VerifierPipeline', '_maybe_ocr_rescue', 4, 7, 2).
python_method('VerifierPipeline', '_evaluate_runs', 2, 1, 3).
python_method('VerifierPipeline', 'verify_after_action', 1, 5, 5).
python_method('VerifierPipeline', '_verify_anchor_visible', 2, 3, 4).
python_method('VerifierPipeline', '_verify_ocr_contains', 2, 3, 4).
python_method('VerifierPipeline', '_verify_with_vision_rescue', 2, 13, 5).
python_method('VerifierPipeline', '_verify_combined', 2, 1, 3).
python_method('VerifierPipeline', '_run_semantic', 1, 11, 5).
python_method('VerifierPipeline', '_run_visual', 2, 7, 5).
python_method('VerifierPipeline', '_run_ocr', 3, 11, 14).
python_method('VerifierPipeline', '_maybe_vision_llm_fallback', 2, 7, 5).
python_method('VerifierPipeline', '_run_anchor_visible', 2, 10, 10).
python_method('VerifierPipeline', '_aggregate', 0, 7, 3).
python_class('src/vdisplay/control/verify_strategy.py', 'VerifyStrategy').
python_class('src/vdisplay/control/vision_disambiguate.py', '_HasConfidence').
python_class('src/vdisplay/control/vision_llm.py', 'VisionLlmSettings').
python_class('src/vdisplay/control/vision_ocr.py', 'OcrTextBox').
python_method('OcrTextBox', 'to_dict', 0, 1, 1).
python_class('src/vdisplay/control/vision_preview.py', 'PreviewMatch').
python_method('PreviewMatch', 'to_dict', 0, 8, 1).
python_class('src/vdisplay/control/vision_preview.py', 'VisionPreviewDebug').
python_method('VisionPreviewDebug', 'to_dict', 0, 8, 2).
python_class('src/vdisplay/control/vision_template.py', 'TemplateMatch').
python_method('TemplateMatch', 'to_dict', 0, 1, 1).
python_class('src/vdisplay/exceptions.py', 'VDisplayError').
python_class('src/vdisplay/exceptions.py', 'BackendNotAvailableError').
python_class('src/vdisplay/exceptions.py', 'CapabilityError').
python_class('src/vdisplay/input/linux_xdotool.py', 'LinuxXdotoolInput').
python_method('LinuxXdotoolInput', '__init__', 1, 1, 0).
python_method('LinuxXdotoolInput', '_env', 0, 2, 0).
python_method('LinuxXdotoolInput', 'available', 0, 2, 1).
python_method('LinuxXdotoolInput', 'can_type', 0, 3, 2).
python_method('LinuxXdotoolInput', 'can_paste', 0, 1, 1).
python_method('LinuxXdotoolInput', 'move', 2, 1, 4).
python_method('LinuxXdotoolInput', 'click', 1, 1, 4).
python_method('LinuxXdotoolInput', 'type_text', 1, 1, 3).
python_method('LinuxXdotoolInput', 'hotkey', 0, 1, 3).
python_class('src/vdisplay/input/linux_ydotool.py', 'LinuxYdotoolInput').
python_method('LinuxYdotoolInput', '__init__', 0, 1, 0).
python_method('LinuxYdotoolInput', 'available', 0, 2, 1).
python_method('LinuxYdotoolInput', 'can_type', 0, 8, 7).
python_method('LinuxYdotoolInput', 'can_paste', 0, 5, 4).
python_method('LinuxYdotoolInput', 'move', 2, 1, 5).
python_method('LinuxYdotoolInput', 'click', 1, 1, 4).
python_method('LinuxYdotoolInput', 'type_text', 1, 1, 4).
python_method('LinuxYdotoolInput', 'hotkey', 0, 1, 3).
python_class('src/vdisplay/input/resolve.py', 'PointerInput').
python_method('PointerInput', 'move', 2, 1, 0).
python_method('PointerInput', 'click', 1, 1, 0).
python_method('PointerInput', 'type_text', 1, 1, 0).
python_class('src/vdisplay/models.py', 'Capabilities').
python_class('src/vdisplay/models.py', 'SessionInfo').
python_class('tests/fixtures/fake_browser.py', 'FakeElement').
python_method('FakeElement', '__init__', 1, 1, 0).
python_method('FakeElement', 'evaluate', 1, 3, 2).
python_method('FakeElement', 'bounding_box', 0, 1, 1).
python_method('FakeElement', 'inner_text', 0, 1, 1).
python_method('FakeElement', 'get_attribute', 1, 1, 1).
python_method('FakeElement', 'click', 0, 1, 0).
python_method('FakeElement', 'fill', 1, 1, 1).
python_method('FakeElement', 'focus', 0, 1, 0).
python_class('tests/fixtures/fake_browser.py', 'FakeLocator').
python_method('FakeLocator', '__init__', 1, 1, 0).
python_method('FakeLocator', 'count', 0, 1, 1).
python_method('FakeLocator', 'nth', 1, 1, 0).
python_method('FakeLocator', 'first', 0, 1, 0).
python_class('tests/fixtures/fake_browser.py', 'FakePage').
python_method('FakePage', '__init__', 0, 1, 1).
python_method('FakePage', 'goto', 1, 1, 0).
python_method('FakePage', 'title', 0, 1, 0).
python_method('FakePage', 'query_selector_all', 1, 1, 1).
python_method('FakePage', 'locator', 1, 3, 1).
python_class('tests/test_capture_providers.py', '_StubProvider').
python_method('_StubProvider', '__init__', 1, 1, 0).
python_method('_StubProvider', 'available', 0, 1, 0).
python_method('_StubProvider', 'capture_full', 0, 1, 0).
python_method('_StubProvider', 'capture_region', 1, 1, 0).
python_class('tests/test_control_gtk_demo.py', 'GtkDemoSession').
python_class('tests/test_control_plugins.py', '_StubPluginProvider').
python_method('_StubPluginProvider', 'available', 0, 1, 0).
python_method('_StubPluginProvider', 'snapshot', 0, 1, 1).
python_method('_StubPluginProvider', 'find', 1, 1, 0).
python_method('_StubPluginProvider', 'invoke', 1, 1, 0).
python_method('_StubPluginProvider', 'focus', 1, 1, 0).
python_method('_StubPluginProvider', 'set_value', 2, 1, 0).
python_method('_StubPluginProvider', 'bounds', 1, 1, 0).
python_class('tests/test_mirror_primary.py', '_FakeResult').
python_method('_FakeResult', '__init__', 2, 1, 0).
python_class('tests/test_session_catalog.py', '_FakeHandle').
python_method('_FakeHandle', 'info', 0, 1, 0).
python_method('_FakeHandle', 'capabilities', 0, 1, 0).
python_class('tests/test_session_catalog.py', '_TerminalHandle').
python_method('_TerminalHandle', 'info', 0, 1, 0).
python_method('_TerminalHandle', 'capabilities', 0, 1, 0).

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

*458 nodes · 500 edges · 112 modules · CC̄=3.5*

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
# generated in 0.23s
# nodes: 458 | edges: 500 | modules: 112
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
  packages.vdisplay-agent.src.vdisplay_agent.routes.health.register_routes
    CC=1  in:0  out:33  total:33
  src.vdisplay.commands.session.command_request_from_control_args
    CC=8  in:1  out:32  total:33
  src.vdisplay.discovery.resolve_host_display
    CC=11  in:26  out:7  total:33
  examples.host-relay.relay_demo.main
    CC=11  in:0  out:33  total:33
  src.vdisplay.commands.agent.handle
    CC=15  in:0  out:32  total:32
  packages.mcp2vdisplay.src.mcp2vdisplay.server.create_server
    CC=1  in:0  out:32  total:32
  examples.host-mirror.mirror_demo.main
    CC=7  in:0  out:31  total:31
  src.vdisplay.control.descriptors.detect_platform_profile
    CC=14  in:8  out:23  total:31
  examples.control-plane.control_demo.run_browser_demo
    CC=6  in:1  out:30  total:31
  src.vdisplay.commands.map.handle
    CC=7  in:0  out:31  total:31
  src.vdisplay.agent_config.resolve_agent_url
    CC=6  in:24  out:5  total:29

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
  src.vdisplay.agent_config  [7 funcs]
    _default_agent_base  CC=3  out:4
    _probe_agent_url  CC=3  out:3
    _probe_default_agent  CC=3  out:3
    agent_auto_enabled  CC=1  out:3
    reset_agent_probe_cache  CC=1  out:0
    resolve_agent_url  CC=6  out:5
    use_agent  CC=2  out:4
  src.vdisplay.agent_dispatch  [2 funcs]
    agent_client  CC=2  out:3
    dispatch_via_agent  CC=1  out:4
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
  src.vdisplay.commands  [1 funcs]
    register_all  CC=2  out:1
  src.vdisplay.commands.agent  [2 funcs]
    _agent_client  CC=2  out:3
    handle  CC=15  out:32
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
  src.vdisplay.control.action_bounds  [2 funcs]
    action_bounds_for_vision  CC=2  out:4
    click_point_for_vision  CC=1  out:1
  src.vdisplay.control.base  [3 funcs]
    capabilities  CC=2  out:2
    session_kind  CC=2  out:1
    verify_modes  CC=2  out:2
  src.vdisplay.control.browser_engine  [4 funcs]
    browser_engine_profile  CC=3  out:1
    engine_profile_id  CC=2  out:3
    normalize_browser_engine  CC=3  out:6
    resolve_session_browser_engine  CC=3  out:4
  src.vdisplay.control.browser_session_store  [8 funcs]
    _chromium_executable  CC=2  out:4
    find_free_port  CC=1  out:4
    launch_detached_chromium  CC=7  out:17
    load_meta  CC=5  out:14
    meta_path  CC=1  out:0
    profile_dir  CC=1  out:0
    remove_meta  CC=2  out:3
    save_meta  CC=1  out:5
  src.vdisplay.control.contracts  [2 funcs]
    control_route_request_from_command  CC=4  out:27
    provider_score_from_dataclass  CC=4  out:4
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
  src.vdisplay.control.gui_map  [11 funcs]
    _boxes_in_scope_for_build  CC=4  out:2
    _prepare_ocr_boxes_for_build  CC=13  out:11
    _slug  CC=2  out:4
    _translate_ocr_boxes  CC=4  out:3
    build_gui_map_from_ocr  CC=7  out:11
    crop_png_bounds  CC=3  out:10
    element_from_ocr_box  CC=9  out:11
    resolve_map_region  CC=2  out:2
    save_gui_map  CC=1  out:4
    scoped_capture_region  CC=2  out:1
  src.vdisplay.control.gui_map_diff  [15 funcs]
    _append_new_elements  CC=14  out:13
    _box_to_bounds  CC=1  out:1
    _boxes_in_scope  CC=5  out:2
    _center  CC=1  out:2
    _classify_element_drift  CC=6  out:14
    _distance  CC=1  out:3
    _labels_match  CC=5  out:2
    _new_ocr_labels  CC=7  out:4
    _normalize_label  CC=1  out:4
    _refresh_known_elements  CC=5  out:6
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
  src.vdisplay.control.profile_inference  [1 funcs]
    profile_for  CC=3  out:2
  src.vdisplay.control.providers.browser_session  [1 funcs]
    open  CC=14  out:21
  src.vdisplay.control.providers.terminal_session  [1 funcs]
    default_registry  CC=1  out:0
  src.vdisplay.control.registry  [4 funcs]
    build  CC=3  out:6
    get_descriptor  CC=2  out:2
    register  CC=2  out:1
    default_provider_registry  CC=1  out:1
  src.vdisplay.control.router  [8 funcs]
    __init__  CC=2  out:1
    _build_decision  CC=7  out:9
    evaluate  CC=2  out:5
    route  CC=4  out:5
    route_command  CC=1  out:2
    _eligible_for_profile  CC=8  out:2
    _select_winner  CC=9  out:9
    default_router  CC=2  out:1
  src.vdisplay.control.routing_semantics  [1 funcs]
    build_routing_semantics  CC=1  out:8
  src.vdisplay.control.scoring  [3 funcs]
    normalize_backend  CC=4  out:3
    rank_providers  CC=8  out:12
    select_verify_provider  CC=9  out:2
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
  src.vdisplay.control.vision_template  [1 funcs]
    template_anchor_find  CC=2  out:11
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

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

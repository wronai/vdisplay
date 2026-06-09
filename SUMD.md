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
- **version**: `0.1.4`
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
  version: 0.1.4;
}

dependencies {
  pillow: Pillow>=10.0;
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
  keys: OPENROUTER_API_KEY, LLM_MODEL, VDISPLAY_AGENT_AUTO, VDISPLAY_AGENT_HOST, VDISPLAY_AGENT_PORT, VDISPLAY_AGENT_URL, VDISPLAY_AGENT_TOKEN, VDISPLAY_AGENT_BROKER, DISPLAY, XDG_SESSION_TYPE, WAYLAND_DISPLAY, VDISPLAY_SCREENCAST_CURSOR, VDISPLAY_IMG2NL, VDISPLAY_IMG2NL_LOCALE, VDISPLAY_CAPTURE_ALLOW_PORTAL, PYTEST_CURRENT_TEST;
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
  version: 0.1.4
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
# vdisplay | 153f 12701L | python:144,shell:8,less:1 | 2026-06-09
# stats: 535 func | 37 cls | 153 mod | CC̄=3.5 | critical:27 | cycles:0
# alerts[5]: CC capture_all_monitors=21; CC describe_screenshot_nl=14; CC capture_host_png=14; CC _route_command=14; CC describe_window_nl=14
# hotspots[5]: create_app fan=33; _start_screencast_impl fan=32; capture_host_png fan=25; create_app fan=22; _portal_impl fan=22
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[153]:
  app.doql.less,48
  examples/agent-broker/broker_demo.py,58
  examples/agent-broker/run.sh,27
  examples/ci-agent/agent.py,74
  examples/common/host_capture.py,30
  examples/common/screenshot_meta.py,163
  examples/common/validate_artifacts.py,85
  examples/headless-virtual/run_virtual.py,64
  examples/host-mirror/mirror_demo.py,98
  examples/host-mirror/run-host.sh,26
  examples/host-mirror/run.sh,54
  examples/host-relay/relay_demo.py,138
  examples/host-relay/run-host.sh,25
  examples/host-relay/run.sh,48
  examples/run_all_examples.sh,153
  packages/cli2vdisplay/src/cli2vdisplay/cli.py,35
  packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py,5
  packages/dsl2vdisplay/src/dsl2vdisplay/bus.py,109
  packages/dsl2vdisplay/src/dsl2vdisplay/cli.py,71
  packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py,161
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py,2
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py,121
  packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py,116
  packages/dsl2vdisplay/src/dsl2vdisplay/result.py,27
  packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py,39
  packages/dsl2vdisplay/tests/test_parity.py,15
  packages/mcp2vdisplay/src/mcp2vdisplay/cli.py,24
  packages/mcp2vdisplay/src/mcp2vdisplay/server.py,96
  packages/nlp2vdisplay/src/nlp2vdisplay/cli.py,42
  packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py,14
  packages/rest2vdisplay/src/rest2vdisplay/app.py,88
  packages/rest2vdisplay/src/rest2vdisplay/cli.py,36
  packages/uri2vdisplay/src/uri2vdisplay/cli.py,31
  packages/uri2vdisplay/src/uri2vdisplay/decode.py,32
  packages/vdisplay-agent/src/vdisplay_agent/__init__.py,6
  packages/vdisplay-agent/src/vdisplay_agent/cli.py,44
  packages/vdisplay-agent/src/vdisplay_agent/envelope.py,86
  packages/vdisplay-agent/src/vdisplay_agent/runtime.py,72
  packages/vdisplay-agent/src/vdisplay_agent/schemas.py,45
  packages/vdisplay-agent/src/vdisplay_agent/serve_port.py,147
  packages/vdisplay-agent/src/vdisplay_agent/server.py,195
  packages/vdisplay-agent/src/vdisplay_agent/services/__init__.py,6
  packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py,52
  packages/vdisplay-agent/src/vdisplay_agent/services/capture.py,77
  packages/vdisplay-agent/src/vdisplay_agent/services/outputs.py,20
  packages/vdisplay-agent/src/vdisplay_agent/services/relay.py,33
  packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py,109
  packages/vdisplay-agent/src/vdisplay_agent/services/windows.py,32
  packages/vdisplay-agent/src/vdisplay_agent/session_store.py,60
  project.sh,59
  src/vdisplay/__init__.py,13
  src/vdisplay/agent_config.py,72
  src/vdisplay/agent_dispatch.py,31
  src/vdisplay/agent_envelope.py,18
  src/vdisplay/api.py,194
  src/vdisplay/application/__init__.py,15
  src/vdisplay/application/commands.py,184
  src/vdisplay/application/errors.py,40
  src/vdisplay/application/executor.py,52
  src/vdisplay/application/handlers/__init__.py,7
  src/vdisplay/application/handlers/agent.py,192
  src/vdisplay/application/handlers/local.py,174
  src/vdisplay/application/runtime.py,83
  src/vdisplay/application/services/__init__.py,4
  src/vdisplay/application/services/capture.py,183
  src/vdisplay/application/services/discovery.py,204
  src/vdisplay/application/services/img2nl_enrich.py,98
  src/vdisplay/application/services/info.py,52
  src/vdisplay/application/services/session.py,199
  src/vdisplay/backends/__init__.py,2
  src/vdisplay/backends/base.py,65
  src/vdisplay/backends/linux_x11_mirror.py,260
  src/vdisplay/backends/linux_x11_relay.py,479
  src/vdisplay/backends/linux_xvfb.py,165
  src/vdisplay/backends/mirror_stub.py,35
  src/vdisplay/capture/__init__.py,16
  src/vdisplay/capture/base.py,10
  src/vdisplay/capture/host.py,485
  src/vdisplay/capture/linux_xwd.py,321
  src/vdisplay/capture/portal.py,222
  src/vdisplay/capture/portal_screencast.py,691
  src/vdisplay/capture/providers/__init__.py,4
  src/vdisplay/capture/providers/base.py,23
  src/vdisplay/capture/providers/drm.py,93
  src/vdisplay/capture/providers/engine.py,100
  src/vdisplay/capture/providers/fbdev.py,78
  src/vdisplay/capture/providers/mss.py,61
  src/vdisplay/capture/providers/x11.py,36
  src/vdisplay/cli.py,33
  src/vdisplay/cli_handlers.py,35
  src/vdisplay/client.py,264
  src/vdisplay/commands/__init__.py,41
  src/vdisplay/commands/agent.py,105
  src/vdisplay/commands/all_cmd.py,47
  src/vdisplay/commands/common.py,36
  src/vdisplay/commands/diagnose.py,19
  src/vdisplay/commands/info.py,17
  src/vdisplay/commands/io.py,8
  src/vdisplay/commands/mirror.py,54
  src/vdisplay/commands/monitors.py,20
  src/vdisplay/commands/nlp.py,24
  src/vdisplay/commands/relay.py,98
  src/vdisplay/commands/screenshot.py,54
  src/vdisplay/commands/virtual.py,82
  src/vdisplay/commands/windows.py,30
  src/vdisplay/discovery.py,353
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
  tests/conftest.py,87
  tests/test_agent.py,44
  tests/test_agent_api_contract.py,32
  tests/test_agent_client.py,119
  tests/test_agent_dispatch.py,53
  tests/test_agent_integration.py,68
  tests/test_agent_serve_port.py,67
  tests/test_capture_all_monitors.py,48
  tests/test_capture_crop.py,50
  tests/test_capture_providers.py,67
  tests/test_capture_xwd.py,53
  tests/test_cli_commands.py,97
  tests/test_client_request.py,43
  tests/test_command_contract.py,50
  tests/test_execution_policy.py,65
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
  tests/test_relay_release.py,66
  tests/test_screenshot_meta.py,54
  tests/test_screenshot_routing.py,105
  tests/test_wayland_capture_fastfail.py,65
  tests/test_windows.py,48
  tests/test_windows_dedupe.py,26
  tree.sh,2
D:
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
  packages/vdisplay-agent/src/vdisplay_agent/runtime.py:
    e: AgentRuntime
    AgentRuntime: sessions(0),relay(0),platform_capabilities(0),diagnostics(0),outputs(0),list_windows(0),start_virtual(0),start_mirror(0),start_relay(0),start_screencast(0),stop_screencast(0),screencast_status(0),stop_session(1),capture_frame(1),adopt_window(1),release_window(1),shutdown(0)  # Privileged runtime: owns session store and broker services.
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
    e: capture_frame,_capture_session,_capture_all_monitors,_capture_host
    capture_frame(store;body)
    _capture_session(store;session_id;body)
    _capture_all_monitors(store;body)
    _capture_host(store;body)
  packages/vdisplay-agent/src/vdisplay_agent/services/outputs.py:
    e: list_outputs_payload
    list_outputs_payload()
  packages/vdisplay-agent/src/vdisplay_agent/services/relay.py:
    e: adopt_window,release_window
    adopt_window(store;body)
    release_window(store;body)
  packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py:
    e: _session_started,start_virtual,start_mirror,start_relay,start_screencast,stop_screencast,screencast_status,stop_session,shutdown
    _session_started(record)
    start_virtual(store)
    start_mirror(store)
    start_relay(store)
    start_screencast(store)
    stop_screencast(store)
    screencast_status(store)
    stop_session(store;session_id)
    shutdown(store)
  packages/vdisplay-agent/src/vdisplay_agent/services/windows.py:
    e: list_windows
    list_windows()
  packages/vdisplay-agent/src/vdisplay_agent/session_store.py:
    e: SessionRecord,SessionStore
    SessionRecord:
    SessionStore: register(0),get(1),pop(1),relay_session(1),clear_relay(0)
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
  src/vdisplay/application/commands.py:
    e: CommandVerb,CommandRequest,CommandResult
    CommandVerb:
    CommandRequest: action(0),from_dsl(2)
    CommandResult: to_dict(0),to_dsl_result(0),success(1),failure(1)
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
    e: _strip_ok,_health,_info,_monitors,_windows,_all,_capabilities,_validate,_screenshot,_virtual_start,_mirror,_adopt,_release,execute_agent
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
    _mirror(client;cmd)
    _adopt(client;cmd)
    _release(client;cmd)
    execute_agent(cmd)
  src/vdisplay/application/handlers/local.py:
    e: _health,_info,_monitors,_windows,_all,_capabilities,_validate,_screenshot,_virtual_start,_mirror,_adopt,_release,execute_local
    _health(_cmd)
    _info(_cmd)
    _monitors(cmd)
    _windows(cmd)
    _all(cmd)
    _capabilities(_cmd)
    _validate(cmd)
    _screenshot(cmd)
    _virtual_start(cmd)
    _mirror(cmd)
    _adopt(cmd)
    _release(cmd)
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
  src/vdisplay/application/services/discovery.py:
    e: _run_discovery,list_monitors,list_monitors_local,list_windows_payload,list_windows_local,list_adopted,list_all,list_all_local,diagnose
    _run_discovery(cmd)
    list_monitors(display)
    list_monitors_local(display)
    list_windows_payload(display)
    list_windows_local(display)
    list_adopted(display)
    list_all(display)
    list_all_local(display)
    diagnose(display)
  src/vdisplay/application/services/img2nl_enrich.py:
    e: img2nl_enabled,img2nl_locale,_image_path,describe_screenshot_image,enrich_screenshot_payload
    img2nl_enabled()
    img2nl_locale()
    _image_path(payload)
    describe_screenshot_image(image_path)
    enrich_screenshot_payload(payload)
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
    e: _wayland_host_session,_monitor_source_name,_monitor_capture_region,_capture_all_from_driver_full,_capture_all_from_screencast,capture_host_png,_host_capture_error,capture_host_to_file,capture_all_monitors
    _wayland_host_session(display)
    _monitor_source_name(display;monitor;source)
    _monitor_capture_region(display;output_name)
    _capture_all_from_driver_full(display;monitors;output_dir)
    _capture_all_from_screencast(display;monitors;output_dir;screencast_session)
    capture_host_png()
    _host_capture_error(display;source;errors)
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
  src/vdisplay/capture/portal_screencast.py:
    e: get_active_screencast,_set_active,_set_active_if_self,start_screencast_session,stop_screencast_session,invalidate_screencast_session,_system_python,_ensure_portal_deps,_open_screencast_pipewire_fd,_start_screencast,_portal_request_path,_stream_properties,_stream_serial,_stream_target,_ensure_fd_inheritable,_dbus_fd,_close_pipewire_fd,_start_screencast_impl,_listen_portal_request,_close_screencast_session,_capture_pipewire_stream,_capture_pipewire_frame_gi_subprocess,_capture_pipewire_frame_gst_launch,_capture_pipewire_node,_vdisplay_src_path,_start_screencast_subprocess,PortalScreenCastSession
    PortalScreenCastSession: is_ready(0),start(0),status(0),capture_png(0),stop(0)  # Hold an open portal ScreenCast session and grab PNG frames f
    get_active_screencast()
    _set_active(session)
    _set_active_if_self(session)
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
    e: _route_command,AgentClient
    AgentClient: __init__(1),_request(2),_send(2),_build_request(2),_http_error_message(1),_raise_on_error(1),_normalize_payload(1),request(1),health(0),capabilities(0),diagnostics(0),outputs(0),windows(0),start_virtual(0),start_mirror(0),start_relay(0),start_screencast(0),stop_screencast(0),screencast_status(0),stop_session(1),capture_frame(0),capture_png_bytes(0),adopt_window(0),release_window(0)  # HTTP client for the local vdisplay-agent broker.
    _route_command(cmd)
  src/vdisplay/commands/__init__.py:
    e: register_all
    register_all(sub)
  src/vdisplay/commands/agent.py:
    e: register,_agent_client,handle
    register(sub)
    _agent_client()
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
    e: _isolate_agent_env,_reset_portal_screencast_state,_wait_for_url,live_agent_url,agent_client
    _isolate_agent_env(monkeypatch)
    _reset_portal_screencast_state()
    _wait_for_url(url)
    live_agent_url()
    agent_client()
  tests/test_agent.py:
    e: test_agent_health,test_agent_capabilities,test_agent_virtual_session_capture
    test_agent_health(agent_client)
    test_agent_capabilities(agent_client)
    test_agent_virtual_session_capture(agent_client;tmp_path)
  tests/test_agent_api_contract.py:
    e: test_agent_health_envelope,test_agent_capabilities_envelope,test_flatten_envelope_for_sdk
    test_agent_health_envelope(agent_client)
    test_agent_capabilities_envelope(agent_client)
    test_flatten_envelope_for_sdk()
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
  tests/test_agent_serve_port.py:
    e: test_parse_ss_pids,test_ensure_broker_port_free_no_listeners,test_ensure_broker_port_free_stops_vdisplay_agent,test_ensure_broker_port_free_rejects_foreign_service,test_find_listener_pids_excludes_current_pid,test_stop_pids_ignores_current_pid
    test_parse_ss_pids()
    test_ensure_broker_port_free_no_listeners(monkeypatch)
    test_ensure_broker_port_free_stops_vdisplay_agent(monkeypatch)
    test_ensure_broker_port_free_rejects_foreign_service(monkeypatch)
    test_find_listener_pids_excludes_current_pid(monkeypatch)
    test_stop_pids_ignores_current_pid(monkeypatch)
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
  tests/test_client_request.py:
    e: test_route_command_health,test_route_command_windows_query,test_request_delegates_to_http
    test_route_command_health()
    test_route_command_windows_query()
    test_request_delegates_to_http(monkeypatch)
  tests/test_command_contract.py:
    e: test_command_request_from_dsl_monitors,test_command_request_from_dsl_apps_only,test_command_result_envelope_success,test_command_result_envelope_failure,test_command_result_to_dsl_result
    test_command_request_from_dsl_monitors()
    test_command_request_from_dsl_apps_only()
    test_command_result_envelope_success()
    test_command_result_envelope_failure()
    test_command_result_to_dsl_result()
  tests/test_execution_policy.py:
    e: test_execution_policy_routes_to_agent_when_url_set,test_execution_policy_routes_local_inside_broker,test_execution_policy_routes_local_without_url,test_execute_health_local,test_execute_monitors_via_agent
    test_execution_policy_routes_to_agent_when_url_set(monkeypatch)
    test_execution_policy_routes_local_inside_broker(monkeypatch)
    test_execution_policy_routes_local_without_url(monkeypatch)
    test_execute_health_local(monkeypatch)
    test_execute_monitors_via_agent(monkeypatch)
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
  tests/test_screenshot_routing.py:
    e: test_resolve_screenshot_routing_host_with_source,test_resolve_screenshot_routing_explicit_virtual,test_resolve_screenshot_routing_virtual_display_override,test_local_screenshot_handler_uses_host_for_source,test_agent_screenshot_handler_uses_host_for_source
    test_resolve_screenshot_routing_host_with_source(monkeypatch)
    test_resolve_screenshot_routing_explicit_virtual(monkeypatch)
    test_resolve_screenshot_routing_virtual_display_override(monkeypatch)
    test_local_screenshot_handler_uses_host_for_source(monkeypatch)
    test_agent_screenshot_handler_uses_host_for_source(monkeypatch)
  tests/test_wayland_capture_fastfail.py:
    e: _black_png,test_blank_screencast_invalidates_session,test_wayland_host_capture_skips_slow_driver_fallback
    _black_png()
    test_blank_screencast_invalidates_session(monkeypatch)
    test_wayland_host_capture_skips_slow_driver_fallback(monkeypatch)
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
project_metadata('vdisplay', '0.1.4', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 48, 'less').
project_file('examples/agent-broker/broker_demo.py', 58, 'python').
project_file('examples/agent-broker/run.sh', 27, 'shell').
project_file('examples/ci-agent/agent.py', 74, 'python').
project_file('examples/common/host_capture.py', 30, 'python').
project_file('examples/common/screenshot_meta.py', 163, 'python').
project_file('examples/common/validate_artifacts.py', 85, 'python').
project_file('examples/headless-virtual/run_virtual.py', 64, 'python').
project_file('examples/host-mirror/mirror_demo.py', 98, 'python').
project_file('examples/host-mirror/run-host.sh', 26, 'shell').
project_file('examples/host-mirror/run.sh', 54, 'shell').
project_file('examples/host-relay/relay_demo.py', 138, 'python').
project_file('examples/host-relay/run-host.sh', 25, 'shell').
project_file('examples/host-relay/run.sh', 48, 'shell').
project_file('examples/run_all_examples.sh', 153, 'shell').
project_file('packages/cli2vdisplay/src/cli2vdisplay/cli.py', 35, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/__init__.py', 5, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 109, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/cli.py', 71, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py', 161, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/__init__.py', 2, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py', 121, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/handlers/query.py', 116, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/result.py', 27, 'python').
project_file('packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py', 39, 'python').
project_file('packages/dsl2vdisplay/tests/test_parity.py', 15, 'python').
project_file('packages/mcp2vdisplay/src/mcp2vdisplay/cli.py', 24, 'python').
project_file('packages/mcp2vdisplay/src/mcp2vdisplay/server.py', 96, 'python').
project_file('packages/nlp2vdisplay/src/nlp2vdisplay/cli.py', 42, 'python').
project_file('packages/nlp2vdisplay/src/nlp2vdisplay/to_dsl.py', 14, 'python').
project_file('packages/rest2vdisplay/src/rest2vdisplay/app.py', 88, 'python').
project_file('packages/rest2vdisplay/src/rest2vdisplay/cli.py', 36, 'python').
project_file('packages/uri2vdisplay/src/uri2vdisplay/cli.py', 31, 'python').
project_file('packages/uri2vdisplay/src/uri2vdisplay/decode.py', 32, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/__init__.py', 6, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/cli.py', 44, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/envelope.py', 86, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/runtime.py', 72, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/schemas.py', 45, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', 147, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/server.py', 195, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/__init__.py', 6, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py', 52, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', 77, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/outputs.py', 20, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/relay.py', 33, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 109, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/services/windows.py', 32, 'python').
project_file('packages/vdisplay-agent/src/vdisplay_agent/session_store.py', 60, 'python').
project_file('project.sh', 59, 'shell').
project_file('src/vdisplay/__init__.py', 13, 'python').
project_file('src/vdisplay/agent_config.py', 72, 'python').
project_file('src/vdisplay/agent_dispatch.py', 31, 'python').
project_file('src/vdisplay/agent_envelope.py', 18, 'python').
project_file('src/vdisplay/api.py', 194, 'python').
project_file('src/vdisplay/application/__init__.py', 15, 'python').
project_file('src/vdisplay/application/commands.py', 184, 'python').
project_file('src/vdisplay/application/errors.py', 40, 'python').
project_file('src/vdisplay/application/executor.py', 52, 'python').
project_file('src/vdisplay/application/handlers/__init__.py', 7, 'python').
project_file('src/vdisplay/application/handlers/agent.py', 192, 'python').
project_file('src/vdisplay/application/handlers/local.py', 174, 'python').
project_file('src/vdisplay/application/runtime.py', 83, 'python').
project_file('src/vdisplay/application/services/__init__.py', 4, 'python').
project_file('src/vdisplay/application/services/capture.py', 183, 'python').
project_file('src/vdisplay/application/services/discovery.py', 204, 'python').
project_file('src/vdisplay/application/services/img2nl_enrich.py', 98, 'python').
project_file('src/vdisplay/application/services/info.py', 52, 'python').
project_file('src/vdisplay/application/services/session.py', 199, 'python').
project_file('src/vdisplay/backends/__init__.py', 2, 'python').
project_file('src/vdisplay/backends/base.py', 65, 'python').
project_file('src/vdisplay/backends/linux_x11_mirror.py', 260, 'python').
project_file('src/vdisplay/backends/linux_x11_relay.py', 479, 'python').
project_file('src/vdisplay/backends/linux_xvfb.py', 165, 'python').
project_file('src/vdisplay/backends/mirror_stub.py', 35, 'python').
project_file('src/vdisplay/capture/__init__.py', 16, 'python').
project_file('src/vdisplay/capture/base.py', 10, 'python').
project_file('src/vdisplay/capture/host.py', 485, 'python').
project_file('src/vdisplay/capture/linux_xwd.py', 321, 'python').
project_file('src/vdisplay/capture/portal.py', 222, 'python').
project_file('src/vdisplay/capture/portal_screencast.py', 691, 'python').
project_file('src/vdisplay/capture/providers/__init__.py', 4, 'python').
project_file('src/vdisplay/capture/providers/base.py', 23, 'python').
project_file('src/vdisplay/capture/providers/drm.py', 93, 'python').
project_file('src/vdisplay/capture/providers/engine.py', 100, 'python').
project_file('src/vdisplay/capture/providers/fbdev.py', 78, 'python').
project_file('src/vdisplay/capture/providers/mss.py', 61, 'python').
project_file('src/vdisplay/capture/providers/x11.py', 36, 'python').
project_file('src/vdisplay/cli.py', 33, 'python').
project_file('src/vdisplay/cli_handlers.py', 35, 'python').
project_file('src/vdisplay/client.py', 264, 'python').
project_file('src/vdisplay/commands/__init__.py', 41, 'python').
project_file('src/vdisplay/commands/agent.py', 105, 'python').
project_file('src/vdisplay/commands/all_cmd.py', 47, 'python').
project_file('src/vdisplay/commands/common.py', 36, 'python').
project_file('src/vdisplay/commands/diagnose.py', 19, 'python').
project_file('src/vdisplay/commands/info.py', 17, 'python').
project_file('src/vdisplay/commands/io.py', 8, 'python').
project_file('src/vdisplay/commands/mirror.py', 54, 'python').
project_file('src/vdisplay/commands/monitors.py', 20, 'python').
project_file('src/vdisplay/commands/nlp.py', 24, 'python').
project_file('src/vdisplay/commands/relay.py', 98, 'python').
project_file('src/vdisplay/commands/screenshot.py', 54, 'python').
project_file('src/vdisplay/commands/virtual.py', 82, 'python').
project_file('src/vdisplay/commands/windows.py', 30, 'python').
project_file('src/vdisplay/discovery.py', 353, 'python').
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
project_file('tests/conftest.py', 87, 'python').
project_file('tests/test_agent.py', 44, 'python').
project_file('tests/test_agent_api_contract.py', 32, 'python').
project_file('tests/test_agent_client.py', 119, 'python').
project_file('tests/test_agent_dispatch.py', 53, 'python').
project_file('tests/test_agent_integration.py', 68, 'python').
project_file('tests/test_agent_serve_port.py', 67, 'python').
project_file('tests/test_capture_all_monitors.py', 48, 'python').
project_file('tests/test_capture_crop.py', 50, 'python').
project_file('tests/test_capture_providers.py', 67, 'python').
project_file('tests/test_capture_xwd.py', 53, 'python').
project_file('tests/test_cli_commands.py', 97, 'python').
project_file('tests/test_client_request.py', 43, 'python').
project_file('tests/test_command_contract.py', 50, 'python').
project_file('tests/test_execution_policy.py', 65, 'python').
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
project_file('tests/test_relay_release.py', 66, 'python').
project_file('tests/test_screenshot_meta.py', 54, 'python').
project_file('tests/test_screenshot_routing.py', 105, 'python').
project_file('tests/test_wayland_capture_fastfail.py', 65, 'python').
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
python_function('examples/headless-virtual/run_virtual.py', '_load_common', 0, 4, 6).
python_function('examples/headless-virtual/run_virtual.py', 'main', 0, 1, 14).
python_function('examples/host-mirror/mirror_demo.py', '_load_common', 0, 4, 6).
python_function('examples/host-mirror/mirror_demo.py', 'main', 0, 7, 19).
python_function('examples/host-relay/relay_demo.py', '_load_common', 0, 4, 6).
python_function('examples/host-relay/relay_demo.py', '_capture_phase', 1, 1, 5).
python_function('examples/host-relay/relay_demo.py', 'main', 0, 11, 17).
python_function('packages/cli2vdisplay/src/cli2vdisplay/cli.py', 'main', 1, 7, 10).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', '_dispatch_legacy', 1, 3, 9).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', 'dispatch', 1, 13, 18).
python_function('packages/dsl2vdisplay/src/dsl2vdisplay/bus.py', '_dispatch_fallback', 1, 4, 6).
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
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_pid_alive', 1, 3, 1).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_parse_ss_pids', 1, 2, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_pids_from_ss', 1, 3, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_pids_from_lsof', 1, 5, 6).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', 'find_listener_pids', 1, 4, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', '_probe_is_vdisplay_agent', 2, 6, 6).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', 'stop_pids', 1, 13, 7).
python_function('packages/vdisplay-agent/src/vdisplay_agent/serve_port.py', 'ensure_broker_port_free', 2, 4, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/server.py', 'create_app', 1, 3, 33).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py', 'platform_capabilities', 0, 5, 9).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capabilities.py', 'diagnostics', 1, 1, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', 'capture_frame', 2, 3, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', '_capture_session', 3, 3, 11).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', '_capture_all_monitors', 2, 2, 5).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/capture.py', '_capture_host', 2, 7, 9).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/outputs.py', 'list_outputs_payload', 0, 2, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/relay.py', 'adopt_window', 2, 6, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/relay.py', 'release_window', 2, 5, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', '_session_started', 1, 1, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_virtual', 1, 1, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_mirror', 1, 1, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_relay', 1, 2, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'start_screencast', 1, 1, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'stop_screencast', 1, 3, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'screencast_status', 1, 3, 2).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'stop_session', 2, 3, 3).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/sessions.py', 'shutdown', 1, 3, 4).
python_function('packages/vdisplay-agent/src/vdisplay_agent/services/windows.py', 'list_windows', 0, 8, 6).
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
python_function('src/vdisplay/application/errors.py', 'error_from_exception', 1, 4, 3).
python_function('src/vdisplay/application/executor.py', '_maybe_enrich_screenshot', 2, 3, 2).
python_function('src/vdisplay/application/executor.py', 'execute', 1, 6, 9).
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
python_function('src/vdisplay/application/handlers/agent.py', '_mirror', 2, 6, 8).
python_function('src/vdisplay/application/handlers/agent.py', '_adopt', 2, 2, 2).
python_function('src/vdisplay/application/handlers/agent.py', '_release', 2, 1, 2).
python_function('src/vdisplay/application/handlers/agent.py', 'execute_agent', 1, 2, 4).
python_function('src/vdisplay/application/handlers/local.py', '_health', 1, 1, 0).
python_function('src/vdisplay/application/handlers/local.py', '_info', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_monitors', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_windows', 1, 2, 1).
python_function('src/vdisplay/application/handlers/local.py', '_all', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_capabilities', 1, 1, 2).
python_function('src/vdisplay/application/handlers/local.py', '_validate', 1, 4, 5).
python_function('src/vdisplay/application/handlers/local.py', '_screenshot', 1, 3, 2).
python_function('src/vdisplay/application/handlers/local.py', '_virtual_start', 1, 1, 1).
python_function('src/vdisplay/application/handlers/local.py', '_mirror', 1, 2, 1).
python_function('src/vdisplay/application/handlers/local.py', '_adopt', 1, 2, 1).
python_function('src/vdisplay/application/handlers/local.py', '_release', 1, 1, 1).
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
python_function('src/vdisplay/application/services/discovery.py', '_run_discovery', 1, 3, 2).
python_function('src/vdisplay/application/services/discovery.py', 'list_monitors', 1, 1, 2).
python_function('src/vdisplay/application/services/discovery.py', 'list_monitors_local', 1, 2, 4).
python_function('src/vdisplay/application/services/discovery.py', 'list_windows_payload', 1, 2, 4).
python_function('src/vdisplay/application/services/discovery.py', 'list_windows_local', 1, 2, 6).
python_function('src/vdisplay/application/services/discovery.py', 'list_adopted', 1, 1, 4).
python_function('src/vdisplay/application/services/discovery.py', 'list_all', 1, 4, 2).
python_function('src/vdisplay/application/services/discovery.py', 'list_all_local', 1, 1, 4).
python_function('src/vdisplay/application/services/discovery.py', 'diagnose', 1, 2, 2).
python_function('src/vdisplay/application/services/img2nl_enrich.py', 'img2nl_enabled', 0, 1, 3).
python_function('src/vdisplay/application/services/img2nl_enrich.py', 'img2nl_locale', 0, 2, 2).
python_function('src/vdisplay/application/services/img2nl_enrich.py', '_image_path', 1, 3, 2).
python_function('src/vdisplay/application/services/img2nl_enrich.py', 'describe_screenshot_image', 1, 9, 8).
python_function('src/vdisplay/application/services/img2nl_enrich.py', 'enrich_screenshot_payload', 1, 9, 7).
python_function('src/vdisplay/application/services/info.py', 'platform_info', 0, 6, 10).
python_function('src/vdisplay/application/services/session.py', 'virtual_start', 0, 1, 4).
python_function('src/vdisplay/application/services/session.py', 'virtual_launch', 1, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'virtual_screenshot', 1, 1, 5).
python_function('src/vdisplay/application/services/session.py', 'mirror_start', 0, 2, 6).
python_function('src/vdisplay/application/services/session.py', 'mirror_screenshot', 1, 2, 4).
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
python_function('src/vdisplay/capture/host.py', '_wayland_host_session', 1, 2, 2).
python_function('src/vdisplay/capture/host.py', '_monitor_source_name', 3, 9, 7).
python_function('src/vdisplay/capture/host.py', '_monitor_capture_region', 2, 4, 3).
python_function('src/vdisplay/capture/host.py', '_capture_all_from_driver_full', 3, 7, 13).
python_function('src/vdisplay/capture/host.py', '_capture_all_from_screencast', 4, 13, 14).
python_function('src/vdisplay/capture/host.py', 'capture_host_png', 0, 14, 25).
python_function('src/vdisplay/capture/host.py', '_host_capture_error', 3, 3, 2).
python_function('src/vdisplay/capture/host.py', 'capture_host_to_file', 1, 3, 9).
python_function('src/vdisplay/capture/host.py', 'capture_all_monitors', 0, 21, 19).
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
python_function('src/vdisplay/capture/portal_screencast.py', 'get_active_screencast', 0, 1, 0).
python_function('src/vdisplay/capture/portal_screencast.py', '_set_active', 1, 1, 0).
python_function('src/vdisplay/capture/portal_screencast.py', '_set_active_if_self', 1, 1, 0).
python_function('src/vdisplay/capture/portal_screencast.py', 'start_screencast_session', 0, 6, 6).
python_function('src/vdisplay/capture/portal_screencast.py', 'stop_screencast_session', 0, 2, 2).
python_function('src/vdisplay/capture/portal_screencast.py', 'invalidate_screencast_session', 1, 4, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_system_python', 0, 4, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_ensure_portal_deps', 0, 5, 2).
python_function('src/vdisplay/capture/portal_screencast.py', '_open_screencast_pipewire_fd', 1, 3, 11).
python_function('src/vdisplay/capture/portal_screencast.py', '_start_screencast', 0, 2, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_portal_request_path', 2, 1, 2).
python_function('src/vdisplay/capture/portal_screencast.py', '_stream_properties', 1, 3, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_stream_serial', 1, 2, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_stream_target', 2, 2, 2).
python_function('src/vdisplay/capture/portal_screencast.py', '_ensure_fd_inheritable', 1, 1, 1).
python_function('src/vdisplay/capture/portal_screencast.py', '_dbus_fd', 1, 5, 5).
python_function('src/vdisplay/capture/portal_screencast.py', '_close_pipewire_fd', 1, 2, 1).
python_function('src/vdisplay/capture/portal_screencast.py', '_start_screencast_impl', 0, 9, 32).
python_function('src/vdisplay/capture/portal_screencast.py', '_listen_portal_request', 3, 1, 3).
python_function('src/vdisplay/capture/portal_screencast.py', '_close_screencast_session', 1, 2, 4).
python_function('src/vdisplay/capture/portal_screencast.py', '_capture_pipewire_stream', 0, 2, 9).
python_function('src/vdisplay/capture/portal_screencast.py', '_capture_pipewire_frame_gi_subprocess', 4, 6, 7).
python_function('src/vdisplay/capture/portal_screencast.py', '_capture_pipewire_frame_gst_launch', 4, 8, 11).
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
python_function('src/vdisplay/cli.py', 'build_parser', 0, 1, 3).
python_function('src/vdisplay/cli.py', 'main', 1, 2, 4).
python_function('src/vdisplay/cli_handlers.py', 'print_json', 1, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'monitors_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'windows_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'all_payload', 0, 1, 1).
python_function('src/vdisplay/cli_handlers.py', 'screenshot_payload', 0, 1, 2).
python_function('src/vdisplay/cli_handlers.py', 'dispatch_cli', 1, 1, 2).
python_function('src/vdisplay/client.py', '_route_command', 1, 14, 6).
python_function('src/vdisplay/commands/__init__.py', 'register_all', 1, 2, 1).
python_function('src/vdisplay/commands/agent.py', 'register', 1, 1, 4).
python_function('src/vdisplay/commands/agent.py', '_agent_client', 0, 2, 3).
python_function('src/vdisplay/commands/agent.py', 'handle', 1, 11, 15).
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
python_function('src/vdisplay/commands/virtual.py', 'handle', 1, 6, 7).
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
python_function('src/vdisplay/discovery.py', 'diagnose_display', 1, 10, 15).
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
python_function('tests/conftest.py', '_isolate_agent_env', 1, 1, 4).
python_function('tests/conftest.py', '_reset_portal_screencast_state', 0, 1, 3).
python_function('tests/conftest.py', '_wait_for_url', 1, 4, 4).
python_function('tests/conftest.py', 'live_agent_url', 0, 1, 14).
python_function('tests/conftest.py', 'agent_client', 0, 1, 4).
python_function('tests/test_agent.py', 'test_agent_health', 1, 5, 2).
python_function('tests/test_agent.py', 'test_agent_capabilities', 1, 4, 2).
python_function('tests/test_agent.py', 'test_agent_virtual_session_capture', 2, 7, 7).
python_function('tests/test_agent_api_contract.py', 'test_agent_health_envelope', 1, 5, 2).
python_function('tests/test_agent_api_contract.py', 'test_agent_capabilities_envelope', 1, 5, 2).
python_function('tests/test_agent_api_contract.py', 'test_flatten_envelope_for_sdk', 0, 3, 2).
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
python_function('tests/test_agent_serve_port.py', 'test_parse_ss_pids', 0, 2, 1).
python_function('tests/test_agent_serve_port.py', 'test_ensure_broker_port_free_no_listeners', 1, 1, 2).
python_function('tests/test_agent_serve_port.py', 'test_ensure_broker_port_free_stops_vdisplay_agent', 1, 3, 4).
python_function('tests/test_agent_serve_port.py', 'test_ensure_broker_port_free_rejects_foreign_service', 1, 1, 3).
python_function('tests/test_agent_serve_port.py', 'test_find_listener_pids_excludes_current_pid', 1, 2, 2).
python_function('tests/test_agent_serve_port.py', 'test_stop_pids_ignores_current_pid', 1, 3, 3).
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
python_function('tests/test_client_request.py', 'test_route_command_health', 0, 4, 2).
python_function('tests/test_client_request.py', 'test_route_command_windows_query', 0, 7, 3).
python_function('tests/test_client_request.py', 'test_request_delegates_to_http', 1, 4, 5).
python_function('tests/test_command_contract.py', 'test_command_request_from_dsl_monitors', 0, 4, 1).
python_function('tests/test_command_contract.py', 'test_command_request_from_dsl_apps_only', 0, 3, 1).
python_function('tests/test_command_contract.py', 'test_command_result_envelope_success', 0, 5, 2).
python_function('tests/test_command_contract.py', 'test_command_result_envelope_failure', 0, 4, 3).
python_function('tests/test_command_contract.py', 'test_command_result_to_dsl_result', 0, 4, 2).
python_function('tests/test_execution_policy.py', 'test_execution_policy_routes_to_agent_when_url_set', 1, 2, 5).
python_function('tests/test_execution_policy.py', 'test_execution_policy_routes_local_inside_broker', 1, 2, 4).
python_function('tests/test_execution_policy.py', 'test_execution_policy_routes_local_without_url', 1, 2, 4).
python_function('tests/test_execution_policy.py', 'test_execute_health_local', 1, 4, 3).
python_function('tests/test_execution_policy.py', 'test_execute_monitors_via_agent', 1, 4, 6).
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
python_function('tests/test_relay_release.py', '_toolbox_states', 0, 1, 1).
python_function('tests/test_relay_release.py', 'test_state_matches_app_jetbrains', 0, 3, 2).
python_function('tests/test_relay_release.py', 'test_select_adopted_for_release_by_app_includes_frame', 0, 2, 3).
python_function('tests/test_relay_release.py', 'test_stash_roundtrip', 2, 4, 5).
python_function('tests/test_screenshot_meta.py', 'test_describe_screenshot_nl', 0, 4, 1).
python_function('tests/test_screenshot_meta.py', 'test_build_and_meta_path', 1, 6, 7).
python_function('tests/test_screenshot_routing.py', 'test_resolve_screenshot_routing_host_with_source', 1, 4, 3).
python_function('tests/test_screenshot_routing.py', 'test_resolve_screenshot_routing_explicit_virtual', 1, 4, 3).
python_function('tests/test_screenshot_routing.py', 'test_resolve_screenshot_routing_virtual_display_override', 1, 4, 3).
python_function('tests/test_screenshot_routing.py', 'test_local_screenshot_handler_uses_host_for_source', 1, 4, 5).
python_function('tests/test_screenshot_routing.py', 'test_agent_screenshot_handler_uses_host_for_source', 1, 4, 6).
python_function('tests/test_wayland_capture_fastfail.py', '_black_png', 0, 1, 4).
python_function('tests/test_wayland_capture_fastfail.py', 'test_blank_screencast_invalidates_session', 1, 2, 5).
python_function('tests/test_wayland_capture_fastfail.py', 'test_wayland_host_capture_skips_slow_driver_fallback', 1, 1, 4).
python_function('tests/test_windows.py', 'test_parse_wm_class', 0, 3, 1).
python_function('tests/test_windows.py', 'test_derive_app_label_prefers_title', 0, 2, 1).
python_function('tests/test_windows.py', 'test_internal_helper_window', 0, 2, 1).
python_function('tests/test_windows.py', 'test_matches_title_on_app_label', 0, 3, 2).
python_function('tests/test_windows_dedupe.py', 'test_dedupe_prefers_application_over_mutter_frame', 0, 3, 2).

% ── Python Classes ───────────────────────────────────────
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
python_method('AgentRuntime', 'start_screencast', 0, 1, 1).
python_method('AgentRuntime', 'stop_screencast', 0, 1, 1).
python_method('AgentRuntime', 'screencast_status', 0, 1, 1).
python_method('AgentRuntime', 'stop_session', 1, 1, 1).
python_method('AgentRuntime', 'capture_frame', 1, 1, 1).
python_method('AgentRuntime', 'adopt_window', 1, 1, 1).
python_method('AgentRuntime', 'release_window', 1, 1, 1).
python_method('AgentRuntime', 'shutdown', 0, 1, 1).
python_class('packages/vdisplay-agent/src/vdisplay_agent/session_store.py', 'SessionRecord').
python_class('packages/vdisplay-agent/src/vdisplay_agent/session_store.py', 'SessionStore').
python_method('SessionStore', 'register', 0, 1, 2).
python_method('SessionStore', 'get', 1, 2, 2).
python_method('SessionStore', 'pop', 1, 2, 2).
python_method('SessionStore', 'relay_session', 1, 5, 5).
python_method('SessionStore', 'clear_relay', 0, 2, 1).
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
python_class('src/vdisplay/application/commands.py', 'CommandRequest').
python_method('CommandRequest', 'action', 0, 2, 1).
python_method('CommandRequest', 'from_dsl', 2, 4, 8).
python_class('src/vdisplay/application/commands.py', 'CommandResult').
python_method('CommandResult', 'to_dict', 0, 3, 1).
python_method('CommandResult', 'to_dsl_result', 0, 4, 2).
python_method('CommandResult', 'success', 1, 2, 1).
python_method('CommandResult', 'failure', 1, 3, 1).
python_class('src/vdisplay/application/errors.py', 'ErrorCode').
python_class('src/vdisplay/application/errors.py', 'ApplicationError').
python_method('ApplicationError', 'to_dict', 0, 1, 0).
python_class('src/vdisplay/application/runtime.py', 'ExecutionPolicy').
python_method('ExecutionPolicy', 'route', 1, 6, 4).
python_method('ExecutionPolicy', 'meta_for', 1, 2, 1).
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
python_class('src/vdisplay/capture/portal_screencast.py', 'PortalScreenCastSession').
python_method('PortalScreenCastSession', 'is_ready', 0, 3, 1).
python_method('PortalScreenCastSession', 'start', 0, 19, 11).
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
python_method('AgentClient', 'start_screencast', 0, 1, 1).
python_method('AgentClient', 'stop_screencast', 0, 1, 1).
python_method('AgentClient', 'screencast_status', 0, 1, 1).
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

*374 nodes · 457 edges · 79 modules · CC̄=3.1*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `_start_screencast_impl` *(in src.vdisplay.capture.portal_screencast)* | 9 | 1 | 71 | **72** |
| `capture_host_png` *(in src.vdisplay.capture.host)* | 14 ⚠ | 2 | 44 | **46** |
| `create_app` *(in packages.rest2vdisplay.src.rest2vdisplay.app)* | 2 | 3 | 38 | **41** |
| `list_outputs` *(in src.vdisplay.discovery)* | 8 | 9 | 27 | **36** |
| `dispatch` *(in packages.dsl2vdisplay.src.dsl2vdisplay.bus)* | 13 ⚠ | 9 | 27 | **36** |
| `main` *(in examples.agent-broker.broker_demo)* | 9 | 0 | 35 | **35** |
| `run_command` *(in src.vdisplay.utils)* | 2 | 29 | 4 | **33** |
| `main` *(in examples.host-relay.relay_demo)* | 11 ⚠ | 0 | 33 | **33** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/wronai/vdisplay
# generated in 0.17s
# nodes: 374 | edges: 457 | modules: 79
# CC̄=3.1

HUBS[20]:
  src.vdisplay.capture.portal_screencast._start_screencast_impl
    CC=9  in:1  out:71  total:72
  src.vdisplay.capture.host.capture_host_png
    CC=14  in:2  out:44  total:46
  packages.rest2vdisplay.src.rest2vdisplay.app.create_app
    CC=2  in:3  out:38  total:41
  src.vdisplay.discovery.list_outputs
    CC=8  in:9  out:27  total:36
  packages.dsl2vdisplay.src.dsl2vdisplay.bus.dispatch
    CC=13  in:9  out:27  total:36
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
  src.vdisplay.capture.portal._portal_impl
    CC=4  in:1  out:28  total:29
  src.vdisplay.backends.linux_x11_relay.LinuxX11RelayBackend.adopt_window
    CC=12  in:0  out:27  total:27
  src.vdisplay.capture.portal_screencast.PortalScreenCastSession.start
    CC=19  in:0  out:26  total:26
  src.vdisplay.capture.host.capture_all_monitors
    CC=21  in:2  out:23  total:25
  packages.dsl2vdisplay.src.dsl2vdisplay.grammar.pick_flag
    CC=3  in:23  out:2  total:25
  src.vdisplay.capture.linux_xwd.is_blank_png
    CC=8  in:10  out:14  total:24
  src.vdisplay.commands.agent.handle
    CC=11  in:0  out:23  total:23
  src.vdisplay.discovery.resolve_host_display
    CC=9  in:17  out:6  total:23
  examples.common.validate_artifacts.validate_image_and_meta
    CC=12  in:1  out:22  total:23
  src.vdisplay.windows.query.inspect_window
    CC=9  in:2  out:21  total:23

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
  packages.vdisplay-agent.src.vdisplay_agent.services.capture  [4 funcs]
    _capture_all_monitors  CC=2  out:8
    _capture_host  CC=7  out:15
    _capture_session  CC=3  out:13
    capture_frame  CC=3  out:6
  packages.vdisplay-agent.src.vdisplay_agent.services.outputs  [1 funcs]
    list_outputs_payload  CC=2  out:4
  packages.vdisplay-agent.src.vdisplay_agent.services.sessions  [9 funcs]
    _session_started  CC=1  out:2
    screencast_status  CC=3  out:2
    shutdown  CC=3  out:4
    start_mirror  CC=1  out:4
    start_relay  CC=2  out:4
    start_screencast  CC=1  out:2
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
  src.vdisplay.application.services.discovery  [9 funcs]
    _run_discovery  CC=3  out:2
    diagnose  CC=2  out:2
    list_adopted  CC=1  out:4
    list_all  CC=4  out:2
    list_all_local  CC=1  out:4
    list_monitors  CC=1  out:2
    list_monitors_local  CC=2  out:4
    list_windows_local  CC=2  out:6
    list_windows_payload  CC=2  out:4
  src.vdisplay.application.services.img2nl_enrich  [5 funcs]
    _image_path  CC=3  out:2
    describe_screenshot_image  CC=9  out:9
    enrich_screenshot_payload  CC=9  out:11
    img2nl_enabled  CC=1  out:3
    img2nl_locale  CC=2  out:2
  src.vdisplay.application.services.info  [1 funcs]
    platform_info  CC=6  out:17
  src.vdisplay.application.services.session  [1 funcs]
    mirror_screenshot  CC=2  out:4
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
  src.vdisplay.capture.host  [9 funcs]
    _capture_all_from_driver_full  CC=7  out:15
    _capture_all_from_screencast  CC=13  out:18
    _host_capture_error  CC=3  out:2
    _monitor_capture_region  CC=4  out:10
    _monitor_source_name  CC=9  out:13
    _wayland_host_session  CC=2  out:2
    capture_all_monitors  CC=21  out:23
    capture_host_png  CC=14  out:44
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
  src.vdisplay.capture.portal_screencast  [28 funcs]
    capture_png  CC=6  out:9
    start  CC=19  out:26
    stop  CC=5  out:4
    _capture_pipewire_frame_gi_subprocess  CC=6  out:10
    _capture_pipewire_frame_gst_launch  CC=8  out:13
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
    handle  CC=11  out:23
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
  packages.vdisplay-agent.src.vdisplay_agent.envelope.success → packages.vdisplay-agent.src.vdisplay_agent.envelope.agent_meta
  packages.vdisplay-agent.src.vdisplay_agent.envelope.failure → packages.vdisplay-agent.src.vdisplay_agent.envelope.agent_meta
  packages.vdisplay-agent.src.vdisplay_agent.envelope.from_runtime → packages.vdisplay-agent.src.vdisplay_agent.envelope.success
  packages.vdisplay-agent.src.vdisplay_agent.envelope.from_runtime → packages.vdisplay-agent.src.vdisplay_agent.envelope.failure
  packages.vdisplay-agent.src.vdisplay_agent.envelope.json_success → packages.vdisplay-agent.src.vdisplay_agent.envelope.from_runtime
  packages.vdisplay-agent.src.vdisplay_agent.envelope.json_from_runtime → packages.vdisplay-agent.src.vdisplay_agent.envelope.from_runtime
  packages.vdisplay-agent.src.vdisplay_agent.envelope.json_error → src.vdisplay.application.errors.error_from_exception
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

## Intent

Cross-platform virtual display orchestration with virtual and mirror sessions

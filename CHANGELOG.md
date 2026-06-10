# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.10] - 2026-06-10

### Fixed
- Fix unused-imports issues (ticket-0c1eb72e)
- Fix magic-numbers issues (ticket-6a84c34d)
- Fix unused-imports issues (ticket-0c0af9db)
- Fix magic-numbers issues (ticket-9869f3ea)
- Fix relative-imports issues (ticket-cf1b1ad1)
- Fix unused-imports issues (ticket-556083c7)
- Fix relative-imports issues (ticket-8396f03d)

## [Unreleased]

### Added
- Map diff `recommendation`, `actionable`, and `key_targets` for drift triage
- Scoped map build: `--crop-bounds`, `--min-text-len` to reduce full-screen OCR noise
- `resolve_map_verify_mode()` — map verify uses `ocr_contains` / `anchor_visible`, not semantic
- Docs: [vision-only-wayland.md](docs/vision-only-wayland.md), updated [gui-map-pack.md](examples/control-plane/gui-map-pack.md)

### Fixed
- `_execute_map_action` no longer hardcodes `verify_mode=semantic` for vision-only maps
- Verifier primary path for `ocr_contains` with region-scoped OCR and hyphen-token matching

### Added (vision LLM cold path)
- `control/vision_llm.py` — OpenRouter vision LLM (`VDISPLAY_VISION_LLM_*`); fallback verify after OCR/anchor fail
- Verifier vision LLM fallback after failed `ocr_contains` / `anchor_visible`
- Optional screenshot enrichment via `img2nl_enrich` when `VDISPLAY_VISION_LLM_MODE=enrich|both`

## [0.1.15] - 2026-06-10

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/rfc/002-cqrs-es-control-feedback.md
- Update project/README.md
- Update project/context.md

### Other
- Update app.doql.less
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 9 more files

## [0.1.14] - 2026-06-10

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/agent-broker.md
- Update docs/architecture.md
- Update docs/control-plane.md
- Update docs/examples.md
- Update docs/guides/README.md
- Update docs/guides/session-report.md
- ... and 8 more files

### Other
- Update app.doql.less
- Update maps/pycharm-chat.json
- Update project/calls.png
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/flow.png
- Update project/index.html
- Update project/logic.pl
- Update project/map.toon.yaml
- Update project/planfile-tickets.yaml
- ... and 2 more files

## [0.1.13] - 2026-06-10

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/guides/README.md
- Update docs/guides/agent-broker.md
- Update docs/guides/browser-control.md
- Update docs/guides/gui-map-pack.md
- Update docs/guides/terminal-control.md
- Update docs/guides/vision-fallback.md
- Update docs/guides/wayland-control.md
- ... and 10 more files

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/map.toon.yaml
- Update project/mermaid.export
- ... and 1 more files

## [0.1.10] - 2026-06-09

### Fixed
- Fix unused-imports issues (ticket-9090e7e1)
- Fix ai-boilerplate issues (ticket-da4b8cab)
- Fix unused-imports issues (ticket-9b868046)
- Fix unused-imports issues (ticket-215d9116)

## [0.1.10] - 2026-06-09

### Fixed
- Fix relative-imports issues (ticket-bc4fbaac)

## [0.1.10] - 2026-06-09

### Fixed
- Fix string-concat issues (ticket-cc7c365d)
- Fix relative-imports issues (ticket-0f4aedb9)
- Fix unused-imports issues (ticket-36a8a2af)
- Fix magic-numbers issues (ticket-20438fcd)
- Fix relative-imports issues (ticket-d5951b18)
- Fix string-concat issues (ticket-10941dcd)
- Fix unused-imports issues (ticket-00e996ed)
- Fix magic-numbers issues (ticket-e37dad70)
- Fix string-concat issues (ticket-d4bc4bb6)
- Fix unused-imports issues (ticket-6aa68d86)
- Fix relative-imports issues (ticket-b8e6fd0e)
- Fix string-concat issues (ticket-f60368ec)
- Fix unused-imports issues (ticket-4c9ad6b9)
- Fix relative-imports issues (ticket-30618d18)
- Fix unused-imports issues (ticket-d9ad4975)
- Fix unused-imports issues (ticket-87773354)
- Fix smart-return-type issues (ticket-966763b1)
- Fix unused-imports issues (ticket-b104c395)
- Fix llm-hallucinations issues (ticket-96ea26a7)
- Fix string-concat issues (ticket-c3ceaaf1)

## [0.1.10] - 2026-06-09

### Fixed
- Fix unused-imports issues (ticket-74fd3f8a)
- Fix ai-boilerplate issues (ticket-82e7f2eb)
- Fix unused-imports issues (ticket-2e96cf60)
- Fix unused-imports issues (ticket-431b795f)
- Fix ai-boilerplate issues (ticket-5bbd3ff7)
- Fix unused-imports issues (ticket-02851731)
- Fix magic-numbers issues (ticket-dbbcee3c)
- Fix string-concat issues (ticket-59a55157)
- Fix unused-imports issues (ticket-38942276)
- Fix unused-imports issues (ticket-f4243602)
- Fix unused-imports issues (ticket-90e9f4ad)
- Fix unused-imports issues (ticket-87bc811c)
- Fix smart-return-type issues (ticket-6bc44888)
- Fix unused-imports issues (ticket-7640f391)
- Fix ai-boilerplate issues (ticket-e1c31d79)
- Fix unused-imports issues (ticket-394961c5)
- Fix ai-boilerplate issues (ticket-1fe3e097)
- Fix unused-imports issues (ticket-2a7ebc5d)
- Fix unused-imports issues (ticket-e655406d)
- Fix magic-numbers issues (ticket-7e7d545f)
- Fix ai-boilerplate issues (ticket-82bb41c8)
- Fix smart-return-type issues (ticket-89f09005)
- Fix unused-imports issues (ticket-65a430e2)
- Fix smart-return-type issues (ticket-1fd06f47)
- Fix unused-imports issues (ticket-9db71dbc)
- Fix magic-numbers issues (ticket-8aa4ce34)
- Fix unused-imports issues (ticket-cc9b0405)
- Fix ai-boilerplate issues (ticket-24602263)
- Fix unused-imports issues (ticket-2bcde290)
- Fix relative-imports issues (ticket-ad4f17c1)
- Fix string-concat issues (ticket-40befefa)
- Fix unused-imports issues (ticket-5e9348d3)
- Fix magic-numbers issues (ticket-e5e80c6a)
- Fix relative-imports issues (ticket-bba442be)
- Fix unused-imports issues (ticket-af5f09b0)
- Fix magic-numbers issues (ticket-f1cb0adf)
- Fix unused-imports issues (ticket-342ce50a)
- Fix smart-return-type issues (ticket-4454330d)
- Fix smart-return-type issues (ticket-7a204181)
- Fix smart-return-type issues (ticket-cd6add99)

## [0.1.10] - 2026-06-09

### Fixed
- Fix relative-imports issues (ticket-61cea448)
- Fix relative-imports issues (ticket-edabd604)
- Fix unused-imports issues (ticket-77784cbb)
- Fix relative-imports issues (ticket-db877e99)
- Fix string-concat issues (ticket-22d13f13)
- Fix unused-imports issues (ticket-a3b0115a)
- Fix relative-imports issues (ticket-52cc5c46)
- Fix smart-return-type issues (ticket-860ccbe9)
- Fix unused-imports issues (ticket-de0a1e6b)
- Fix magic-numbers issues (ticket-73e45fbc)
- Fix relative-imports issues (ticket-bf277a45)
- Fix relative-imports issues (ticket-1f2f39da)
- Fix unused-imports issues (ticket-7daf56aa)
- Fix relative-imports issues (ticket-cadb17a5)
- Fix string-concat issues (ticket-7833339a)
- Fix unused-imports issues (ticket-aaccb586)
- Fix magic-numbers issues (ticket-d528e9a9)
- Fix relative-imports issues (ticket-e1994a6f)
- Fix string-concat issues (ticket-0322dd34)
- Fix unused-imports issues (ticket-18b56f73)
- Fix unused-imports issues (ticket-79e0042c)
- Fix relative-imports issues (ticket-665506df)
- Fix string-concat issues (ticket-35330002)
- Fix unused-imports issues (ticket-d9f64d60)
- Fix magic-numbers issues (ticket-2876fec2)
- Fix relative-imports issues (ticket-eaa65446)
- Fix unused-imports issues (ticket-c0cc5f21)
- Fix magic-numbers issues (ticket-a3429ea5)
- Fix ai-boilerplate issues (ticket-7711c565)
- Fix relative-imports issues (ticket-26a6bac4)
- Fix relative-imports issues (ticket-ccf44daa)
- Fix unused-imports issues (ticket-044f7af5)
- Fix unused-imports issues (ticket-9b933356)
- Fix unused-imports issues (ticket-0e175631)
- Fix magic-numbers issues (ticket-f126120c)
- Fix smart-return-type issues (ticket-73ef63f9)
- Fix string-concat issues (ticket-3f8287b2)
- Fix unused-imports issues (ticket-949b60cc)
- Fix smart-return-type issues (ticket-b75e4e01)
- Fix smart-return-type issues (ticket-c92056bf)

## [Unreleased]

### Added
- `src/vdisplay/application/` — shared use-case layer (`discovery`, `capture`, `session`, `info`) with single agent vs local routing in `application/runtime.py`
- `src/vdisplay/commands/` — CLI command registry; each subcommand uses `set_defaults(func=handle)`
- `src/vdisplay/windows/` package — split into `scan`, `normalize`, `filter`, `rank`, `query` (replaces monolithic `windows.py`)
- README: expanded examples (screenshots, NL/DSL, agent broker), docs/examples cross-links, project layout section

### Added
- `vdisplay_agent/envelope.py` + `schemas.py` — stable agent HTTP envelope and route→action map
- `tests/test_agent_api_contract.py` — envelope shape + SDK flatten tests
- `application/commands.py` — shared `CommandRequest` / `CommandResult` model for CLI, DSL, REST, agent
- `application/errors.py` — stable `ErrorCode` envelope for failures
- `application/executor.py` — single `execute()` entry with agent vs local routing
- `docs/api-contract.md` — frozen command/response contract and agent endpoint map

### Fixed
- `pyproject.toml` — `[dependency-groups] dev` + `tool.uv.default-groups` so `uv sync` / `goal -a` install Pillow, fastapi, dsl2vdisplay, vdisplay-agent, uvicorn for tests
- `is_blank_png` — valid minimal PNGs no longer flagged blank when Pillow is missing
- `test_host_capture` — force mirror fallback path when mocking mirror capture
- `pyproject.toml` — replace `file:packages/...` optional-deps with uv workspace members so `uv sync` / `goal -a` can resolve editable metadata

### Changed
- `client.py` — `AgentClient.request(CommandRequest)` maps verbs to broker HTTP; simple agent handlers delegate to it
- `vdisplay_agent/runtime.py` — thin `AgentRuntime` facade; domain logic in `session_store.py` + `services/{capabilities,outputs,windows,sessions,capture,relay}.py` (fan-out split)
- `application/executor.py` — thin router; per-verb handlers in `application/handlers/{local,agent}.py` (CC split)
- `client.py` — `_request` split into `_send`, `_build_request`, `_http_error_message`, `_raise_on_error`
- `application/runtime.py` — `ExecutionPolicy` is the only agent-vs-local decision point
- `application/services/discovery.py` — local implementations (`*_local`) + routing via executor
- `application/services/capture.py` — `capture_screenshot_local()`; public API routes through executor
- `agent_dispatch.py` — thin deprecated shim over `executor.execute(force_route="agent")`
- `dsl2vdisplay/bus.py` — routes all verbs through `executor.execute()` (legacy handlers only for `LAUNCH`/`VIRTUAL_STOP`)
- `vdisplay_agent/server.py` — all endpoints return `{ok, action, data, meta, error?}` envelope
- `client.py` — flattens agent envelope for backward-compatible SDK dicts
- `cli.py` — thin dispatcher (`args.func(args)`); parser built from command registry
- `payloads.py` — delegates to `application.services.discovery` (backward-compatible shims)
- `cli_handlers.py` — deprecated shim over application services
- `dsl2vdisplay/handlers/query.py` — uses application services instead of direct `payloads` imports
- `vdisplay-agent/runtime.py` — `list_windows` calls `discovery.list_windows_local` (breaks agent↔payloads cycle)
- `nlp.py` — local DSL fallback routes through `discovery` services
- Refactored high-CC functions: `grammar.parse_line`, `nlp.nl_to_dsl`, `linux_x11_mirror.start`, `agent_dispatch.dispatch_via_agent`

### Docs
- Update README.md, CHANGELOG.md, TODO.md with architecture notes and roadmap

## [0.1.12] - 2026-06-10

### Docs
- Update README.md
- Update docs/control-plane.md
- Update docs/rfc/001-extensibility-model.md
- Update docs/rfc/extensibility-model.md
- Update examples/README.md
- Update examples/control-plane/gui-map-pack.md
- Update examples/control-plane/vision-disambiguation.md
- Update examples/control-plane/vision-preview.md
- Update examples/control-plugin-ax/README.md
- Update examples/control-plugin-uia/README.md
- ... and 3 more files

### Test
- Update tests/fixtures/gtk_demo_app.py
- Update tests/test_control_gtk_demo.py
- Update tests/test_control_verify.py
- Update tests/test_coords_rotation.py
- Update tests/test_example_uia_ax_plugins.py
- Update tests/test_gui_map.py
- Update tests/test_gui_map_diff.py
- Update tests/test_routing_semantics.py
- Update tests/test_vision_anchor_visible_verify.py
- Update tests/test_vision_multimatch_disambiguation.py
- ... and 3 more files

### Other
- Update .cursor/mcp.json
- Update .gitignore
- Update .koru/event-store.jsonl
- Update .koru/events/observability.jsonl
- Update .koru/project.json
- Update .planfile/config.yaml
- Update .planfile/sprints/current.yaml
- Update examples/control-plugin-ax/pyproject.toml
- Update examples/control-plugin-ax/src/vdisplay_example_ax_plugin/__init__.py
- Update examples/control-plugin-ax/src/vdisplay_example_ax_plugin/provider.py
- ... and 22 more files

## [0.1.11] - 2026-06-10

### Docs
- Update README.md

### Test
- Update tests/test_vision_anchor_matching.py
- Update tests/test_vision_template_matching.py

### Other
- Update project/duplication.toon.yaml
- Update project/planfile-tickets.yaml

## [0.1.10] - 2026-06-09

### Docs
- Update README.md
- Update docs/rfc/001-extensibility-model.md
- Update docs/rfc/extensibility-model.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_vision_anchor_matching.py
- Update tests/test_vision_template_matching.py

### Other
- Update .code2llm_cache/__init___1781039844393866372_159.pkl
- Update .code2llm_cache/common_1781040205653846463_4359.pkl
- Update .code2llm_cache/control_1781040207076088867_13801.pkl
- Update .code2llm_cache/descriptors_1781040183676855820_15825.pkl
- Update .code2llm_cache/profile_inference_1781040215567220234_9124.pkl
- Update .code2llm_cache/provider_1781040202721045498_13573.pkl
- Update .code2llm_cache/pyproject_1781040184682865842_3441.pkl
- Update .code2llm_cache/scoring_1781040215709388690_25830.pkl
- Update .code2llm_cache/selector_1781040187854897438_12252.pkl
- Update .code2llm_cache/vision_ocr_1781040211854136445_7119.pkl
- ... and 19 more files

## [0.1.9] - 2026-06-09

### Docs
- Update README.md
- Update docs/control-plane.md
- Update docs/rfc/001-extensibility-model.md
- Update docs/rfc/extensibility-model.md
- Update examples/README.md
- Update examples/control-plane/README.md
- Update examples/control-plugin/README.md
- Update project/context.md

### Test
- Update test-screencast.png
- Update tests/contract/test_descriptors.py
- Update tests/contract/test_providers.py
- Update tests/test_agent_api_contract.py
- Update tests/test_ax_invoke.py
- Update tests/test_browser_engine_profiles.py
- Update tests/test_control_agent.py
- Update tests/test_control_browser_session.py
- Update tests/test_control_plugins.py
- Update tests/test_cross_platform_providers.py
- ... and 5 more files

### Other
- Update cursor-dp1.png
- Update cursor-dp2.png
- Update cursor-test.png
- Update examples/control-plugin/pyproject.toml
- Update examples/control-plugin/src/vdisplay_example_plugin/__init__.py
- Update examples/control-plugin/src/vdisplay_example_plugin/my_provider.py
- Update packages/vdisplay-agent/pyproject.toml
- Update packages/vdisplay-agent/src/vdisplay_agent/__init__.py
- Update packages/vdisplay-agent/src/vdisplay_agent/routes/health.py
- Update packages/vdisplay-agent/src/vdisplay_agent/schemas.py
- ... and 13 more files

## [0.1.8] - 2026-06-09

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/agent-broker.md
- Update docs/api-contract.md
- Update docs/architecture.md
- Update docs/control-plane.md
- Update docs/examples.md
- Update docs/index.md
- ... and 7 more files

### Test
- Update tests/contract/test_contracts.py
- Update tests/contract/test_descriptors.py
- Update tests/contract/test_providers.py
- Update tests/fixtures/__init__.py
- Update tests/fixtures/fake_browser.py
- Update tests/test_agent_browser_session.py
- Update tests/test_agent_tasks.py
- Update tests/test_browser_engine_profiles.py
- Update tests/test_browser_session_detached.py
- Update tests/test_cli_control_args.py
- ... and 16 more files

### Other
- Update .gitignore
- Update app.doql.less
- Update brain/scratch_atspi.py
- Update examples/control-plane/control_demo.py
- Update examples/run_all_examples.sh
- Update packages/dsl2vdisplay/src/dsl2vdisplay/bus.py
- Update packages/dsl2vdisplay/src/dsl2vdisplay/grammar.py
- Update packages/dsl2vdisplay/src/dsl2vdisplay/schema/commands/browser_open.schema.json
- Update packages/dsl2vdisplay/src/dsl2vdisplay/schema/commands/terminal_open.schema.json
- Update packages/dsl2vdisplay/src/dsl2vdisplay/schema_registry.py
- ... and 34 more files

## [0.1.7] - 2026-06-09

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/fixtures/run_gtk_demo.sh
- Update tests/test_agent_terminal_session.py
- Update tests/test_command_contract.py
- Update tests/test_control_app_matching.py
- Update tests/test_control_atspi.py
- Update tests/test_control_browser.py
- Update tests/test_control_capabilities.py
- Update tests/test_control_executor.py
- Update tests/test_control_gtk_demo.py
- Update tests/test_control_screenshot_verify.py
- ... and 4 more files

### Other
- Update .code2llm_cache/atspi_1781032229377102546_8329.pkl
- Update .code2llm_cache/atspi_impl_1781031995339782158_12296.pkl
- Update .code2llm_cache/control_1781031644489545337_9454.pkl
- Update .code2llm_cache/control_1781031648783985734_6562.pkl
- Update .code2llm_cache/control_1781032010807402038_2857.pkl
- Update .code2llm_cache/control_click.schema_1781032137548181202_989.pkl
- Update .code2llm_cache/control_focus.schema_1781032138301188705_989.pkl
- Update .code2llm_cache/control_set_value.schema_1781032139169197355_1041.pkl
- Update .code2llm_cache/controls_find.schema_1781032139684202488_817.pkl
- Update .code2llm_cache/controls_list.schema_1781032140121206843_504.pkl
- ... and 64 more files

## [0.1.6] - 2026-06-09

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/control.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/fixtures/gtk_demo_app.py
- Update tests/test_agent_sampler.py
- Update tests/test_control_agent.py
- Update tests/test_control_atspi.py
- Update tests/test_control_policy.py
- Update tests/test_control_selector.py
- Update tests/test_relay_window_region.py
- Update tests/test_sampler_policy.py
- Update tests/test_sampler_recovery.py
- Update tests/test_screencast_multiple.py

### Other
- Update .code2llm_cache/__init___1781026677507577094_830.pkl
- Update .code2llm_cache/__init___1781027803458650394_159.pkl
- Update .code2llm_cache/__init___1781027816848869976_517.pkl
- Update .code2llm_cache/__init___1781027828306058007_865.pkl
- Update .code2llm_cache/agent_1781027199231044175_4125.pkl
- Update .code2llm_cache/atspi_1781027941715925920_6200.pkl
- Update .code2llm_cache/atspi_impl_1781027944939979185_7988.pkl
- Update .code2llm_cache/base_1781027798117562860_1044.pkl
- Update .code2llm_cache/capabilities_1781027841269270912_2118.pkl
- Update .code2llm_cache/capture_1781027391696687734_3292.pkl
- ... and 63 more files

## [0.1.5] - 2026-06-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/agent-broker.md
- Update docs/architecture.md
- Update docs/index.md
- Update docs/installation.md
- Update docs/troubleshooting.md
- ... and 5 more files

### Test
- Update tests/conftest.py
- Update tests/test_agent_client.py
- Update tests/test_agent_dispatch.py
- Update tests/test_agent_integration.py
- Update tests/test_agent_serve_port.py
- Update tests/test_capture_all_monitors.py
- Update tests/test_client_request.py
- Update tests/test_execution_policy.py
- Update tests/test_host_capture.py
- Update tests/test_host_capture_errors.py
- ... and 4 more files

### Other
- Update .code2llm_cache/agent_1781026162305431040_3882.pkl
- Update .code2llm_cache/agent_envelope_1781025998955988430_551.pkl
- Update .code2llm_cache/capture_1781026000963209215_5317.pkl
- Update .code2llm_cache/capture_1781026165730443343_2623.pkl
- Update .code2llm_cache/cli_1781026163053578358_1511.pkl
- Update .code2llm_cache/client_1781025999650000677_9742.pkl
- Update .code2llm_cache/discovery_1781025818419890582_11949.pkl
- Update .code2llm_cache/host_1781026172795469681_16945.pkl
- Update .code2llm_cache/info_1781025815166749058_2019.pkl
- Update .code2llm_cache/policy_1781026667249685781_4114.pkl
- ... and 51 more files

## [0.1.4] - 2026-06-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/agent-broker.md
- Update docs/api-contract.md
- Update docs/docker-guide.md
- Update docs/examples.md
- Update docs/index.md
- ... and 13 more files

### Test
- Update tests/conftest.py
- Update tests/test_agent.py
- Update tests/test_agent_api_contract.py
- Update tests/test_agent_client.py
- Update tests/test_agent_dispatch.py
- Update tests/test_agent_integration.py
- Update tests/test_capture_crop.py
- Update tests/test_capture_providers.py
- Update tests/test_capture_xwd.py
- Update tests/test_cli_commands.py
- ... and 7 more files

### Other
- Update .code2llm_cache/__init___1781006059576366457_262.pkl
- Update .code2llm_cache/agent_dispatch_1781006048535269308_992.pkl
- Update .code2llm_cache/broker_demo_1781005725296511351_1963.pkl
- Update .code2llm_cache/bus_1781006192104554953_4010.pkl
- Update .code2llm_cache/capture_1781006048360267771_4557.pkl
- Update .code2llm_cache/client_1781006188410521314_6703.pkl
- Update .code2llm_cache/commands_1781006029876105852_5006.pkl
- Update .code2llm_cache/discovery_1781006045165239718_5854.pkl
- Update .code2llm_cache/envelope_1781006187047508909_2932.pkl
- Update .code2llm_cache/errors_1781006026272074389_1327.pkl
- ... and 66 more files

## [0.1.3] - 2026-06-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/examples.md
- Update docs/index.md
- Update docs/troubleshooting.md
- Update examples/README.md
- Update packages/README.md
- ... and 2 more files

### Test
- Update tests/test_mirror_primary.py
- Update tests/test_nl.py
- Update tests/test_relay_release.py
- Update tests/test_windows_dedupe.py

### Other
- Update app.doql.less
- Update examples/host-mirror/Dockerfile
- Update packages/dsl2vdisplay/src/dsl2vdisplay/handlers/command.py
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- ... and 12 more files

## [0.1.2] - 2026-06-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/docker-guide.md
- Update docs/examples.md
- Update docs/index.md
- Update docs/installation.md
- Update docs/troubleshooting.md
- ... and 7 more files

### Test
- Update testql-scenarios/generated-cli-tests.testql.toon.yaml
- Update tests/test_outputs_rotation.py
- Update tests/test_windows.py

### Other
- Update app.doql.less
- Update examples/ci-agent/.gitignore
- Update examples/ci-agent/Dockerfile
- Update examples/ci-agent/agent.py
- Update examples/ci-agent/docker-compose.yml
- Update examples/dev-workspace/Dockerfile
- Update examples/dev-workspace/docker-compose.yml
- Update examples/headless-virtual/.gitignore
- Update examples/headless-virtual/Dockerfile
- Update examples/headless-virtual/docker-compose.yml
- ... and 45 more files

## [0.1.1] - 2026-06-09

### Docs
- Update README.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_capture_xwd.py
- Update tests/test_import.py
- Update tests/test_linux_xvfb_integration.py

### Other
- Update .code2llm_cache/__init___1780992527463967589_116.pkl
- Update .code2llm_cache/__init___1780992538625526451_78.pkl
- Update .code2llm_cache/__init___1780992568582641857_364.pkl
- Update .code2llm_cache/__init___1780992586447498704_42.pkl
- Update .code2llm_cache/api_1780992568263130899_5520.pkl
- Update .code2llm_cache/base_1780992527651301007_225.pkl
- Update .code2llm_cache/base_1780992561887161891_1597.pkl
- Update .code2llm_cache/cli_1780992577423316461_6733.pkl
- Update .code2llm_cache/exceptions_1780992406000000000_148.pkl
- Update .code2llm_cache/goal_1780992565350071766_12249.pkl
- ... and 32 more files


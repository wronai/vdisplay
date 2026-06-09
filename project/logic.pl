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


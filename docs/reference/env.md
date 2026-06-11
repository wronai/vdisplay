# Environment variables

Consolidated reference. Package-specific vars may also appear in [agent-broker.md](../agent-broker.md).

## Agent broker

| Variable | Where | Purpose |
|----------|-------|---------|
| `VDISPLAY_AGENT_URL` | clients | Broker base URL (e.g. `http://127.0.0.1:8765`) |
| `VDISPLAY_AGENT_TOKEN` | clients + agent | Optional Bearer auth |
| `VDISPLAY_AGENT_HOST` | agent | Bind address (default `127.0.0.1`) |
| `VDISPLAY_AGENT_PORT` | agent | Listen port (default `8765`) |
| `VDISPLAY_AGENT_BROKER` | agent only | Set to `1` inside broker — **never on clients** |
| `VDISPLAY_AGENT_DB` | agent | Task persistence DB (default `~/.cache/vdisplay/agent-tasks.db`) |
| `VDISPLAY_CAPTURE_ALLOW_PORTAL` | agent | Set `1` to opt in to xdg-desktop-portal capture |

## Screencast / keeper (GNOME Wayland)

| Variable | Default | Purpose |
|----------|---------|---------|
| `VDISPLAY_SCREENCAST_MULTIPLE` | `1` | Multi-stream portal session (All Screens) |
| `VDISPLAY_SCREENCAST_GNOME_FALLBACK` | `1` | Portal screenshot + crop when PipeWire gst fails |
| `VDISPLAY_KEEPER_CAPTURE_TIMEOUT_S` | `130` | Keeper IPC capture timeout (seconds) |
| `VDISPLAY_SCREENCAST_LOCAL_START_COOLDOWN_S` | — | Cooldown between screencast starts |
| `VDISPLAY_SCREENCAST_RECOVERY_COOLDOWN_S` | — | Auto-recovery cooldown after failed capture |
| `VDISPLAY_SCREENCAST_CURSOR` | — | Include cursor in screencast capture |

Guide: [guides/gnome-wayland-screencast.md](../guides/gnome-wayland-screencast.md)
| `DISPLAY` | agent / local | X display (auto-resolves to `:0` on host) |
| `VDISPLAY_SESSION_BASE` | web replay | Root directory for audit sessions (default `.vdisplay` in cwd / home) |
| `VDISPLAY_REPLAY_DELAY_S` | replay | Pause between replayed CONTROL_* steps (default `0.25`) |

## Vision / map (Wayland)

| Variable | Purpose |
|----------|---------|
| `YDOTOOL_SOCKET` | ydotool daemon socket (e.g. `/tmp/.ydotool_socket`) |
| `VDISPLAY_IMG2NL` | `1` — optional img2nl enrichment for VQL |
| `VDISPLAY_DESCRIBE_BACKEND` | `auto` \| `imgl` \| `img2vql` \| `img2nl` — screenshot NL describe path |
| `VDISPLAY_OBSERVE` | `1` — build `ScreenContext` sidecar after screenshot (auto when imgl/vql installed) |
| `VDISPLAY_IMGL` | `1` — run IMGL scene analysis in observe pipeline |
| `VDISPLAY_VQL` | `1` — export VQL program JSON (+ SVG with `--svg`) |
| `VDISPLAY_VISION_BACKEND` | `auto` \| `local` \| `imgl` — OCR/template/diff/preview backend (`local` = built-in; `imgl` = IMGL `vision_ops`; `auto` = IMGL when installed) |
| `VDISPLAY_VISION_PREVIEW` | `auto` \| `local` \| `imgl` — preview overlay renderer (`imgl` = IMGL `annotate_export`; `auto` = IMGL when installed) |
| `VDISPLAY_OBSERVE_CACHE` | `1` — reuse IMGL/VQL from session `artifacts/observe/` when fingerprint matches |
| `VDISPLAY_OCR_CACHE` | `1` — use OCR boxes from `VDISPLAY_SCREEN_CONTEXT_PATH` sidecar before full-screen OCR |
| `VDISPLAY_SCREEN_CONTEXT_PATH` | Path to `.context.json` sidecar for verify OCR cache |
| `VDISPLAY_VISION_LLM` | OpenRouter model id for cold-path vision (separate from `LLM_MODEL`) |
| `VDISPLAY_VISION_LLM_ENABLED` | `0` \| `1` |
| `VDISPLAY_VISION_LLM_MODE` | `off` \| `fallback` \| `enrich` \| `both` |
| `OPENROUTER_API_KEY` | Required when vision LLM enabled |

Example:

```bash
LLM_MODEL=openrouter/qwen/qwen3-coder-next
VDISPLAY_VISION_LLM=openrouter/google/gemini-3.1-flash-image-preview
VDISPLAY_VISION_LLM_ENABLED=1
VDISPLAY_VISION_LLM_MODE=fallback
OPENROUTER_API_KEY=sk-or-v1-...
```

Guide: [guides/vision-fallback.md](../guides/vision-fallback.md)

## Accessibility (Linux desktop)

| Variable | Purpose |
|----------|---------|
| `GTK_A11Y` | `1` — enable GTK accessibility |
| `QT_ACCESSIBILITY` | `1` — enable Qt accessibility |
| `GDK_BACKEND` | `x11` — force XWayland for GTK apps (AT-SPI path) |

## koru / coru integration (external)

Used by `koru.integrations.vdisplay_client` when koru drives IDE chat via vdisplay instead of the autopilot plugin socket.

| Variable | Default | Purpose |
|----------|---------|---------|
| `KORU_VDISPLAY_CONTROL_FALLBACK` | `auto` | `auto` — enable on Wayland when plugin disconnected; `0` — disable |
| `KORU_VDISPLAY_AGENT_URL` | from vdisplay | Broker URL when vdisplay is not imported in-process |
| `KORU_VDISPLAY_DRY_RUN` | off | Log drive payload without actuating |

vdisplay fallback **does not** replace the koru IDE plugin for Cursor/Glass UI chat (Electron webview is not matched by generic AT-SPI selectors). See [guides/desktop-control-today.md](../guides/desktop-control-today.md).

## Orchestration (external)

| Variable | Purpose |
|----------|---------|
| `LLM_MODEL` | General text LLM for agents — **not** used for vision verify |

## Session recorder

| Variable | Purpose |
|----------|---------|
| `VDISPLAY_SESSION` | `1` — auto-create `.vdisplay/<timestamp>__.../` per process |
| `VDISPLAY_SESSION_DIR` | Explicit session directory (overrides auto path) |
| `VDISPLAY_SESSION_ID` | Slug suffix for auto-created session dir |
| `VDISPLAY_AGENT_AUDIT_DELEGATE` | `1` (default) — agent-routed commands record on broker via `X-VDisplay-*` headers |
| `VDISPLAY_EVENT_STORE` | `1` by default when session recording is on; writes `index.jsonl` |
| `VDISPLAY_EVENT_FORMAT` | `json` (default) \| `protobuf` — also append length-delimited records to `index.pb` |
| `VDISPLAY_PROJECTIONS` | `1` (default) — rebuild `projections/*.json` after each event |
| `VDISPLAY_SESSION_EMBED_IMAGES` | Embed PNG thumbnails in README (future) |

CLI: `vdisplay --session [--session-id SLUG] …` — root audit slug. Control `--session-id` is the **terminal/browser** session id (different field).

See [session-report.md](../guides/session-report.md) and [RFC 002](rfc/002-cqrs-es-control-feedback.md).

## Control actuation (Wayland / verify)

| Variable | Purpose |
|----------|---------|
| `VDISPLAY_CONTROL_RETRY` | `auto` \| `0` \| `1` — retry failed verify (`auto` = on when `--verify`) |
| `VDISPLAY_CONTROL_MAX_ATTEMPTS` | Max retry attempts (default `3`) |
| `VDISPLAY_CONTROL_RETRY_DELAY_MS` | Pause between retries (default `150`) |
| `VDISPLAY_CONTROL_RETRY_STRATEGIES` | Comma list: `retry_scope,fallback_backend,refresh_map` |
| `VDISPLAY_CONTROL_FOCUS_MS` | Pause after click-to-focus before keystrokes (default `350`) |
| `VDISPLAY_CONTROL_POINTER_SETTLE_MS` | Pause after pointer click before typing (default `50`) |
| `VDISPLAY_ALLOW_YDOTOOL_TYPING` | `1` — allow ydotool keystrokes on Wayland (default off on GNOME) |
| `YDOTOOL_SOCKET` | ydotoold socket path |

See also: [vision-only-wayland.md](../vision-only-wayland.md) · [troubleshooting.md](../troubleshooting.md)

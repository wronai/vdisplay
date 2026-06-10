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
| `DISPLAY` | agent / local | X display (auto-resolves to `:0` on host) |

## Vision / map (Wayland)

| Variable | Purpose |
|----------|---------|
| `YDOTOOL_SOCKET` | ydotool daemon socket (e.g. `/tmp/.ydotool_socket`) |
| `VDISPLAY_IMG2NL` | `1` — optional img2nl enrichment for VQL |
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

CLI equivalents: `vdisplay --session --session-id pycharm-chat monitors` (root `--session-id` is the **audit** slug; control `--session-id` is terminal/browser session).
| `VDISPLAY_SESSION_EMBED_IMAGES` | Embed PNG thumbnails in README (phase 2) |

See [session-report.md](../guides/session-report.md).

See also: [vision-only-wayland.md](../vision-only-wayland.md) · [troubleshooting.md](../troubleshooting.md)

# vdisplay-agent broker

> **Navigation:** Quick guide [guides/agent-broker.md](guides/agent-broker.md) · Architecture [architecture.md](architecture.md)

Back to [documentation index](index.md) · [packages/README.md](../packages/README.md)

Install **vdisplay-agent once** on the host. All clients (CLI, DSL, REST, MCP) talk to it over localhost HTTP instead of opening capture backends, portals, or DRM devices directly.

## Architecture

```mermaid
flowchart TB
  subgraph clients [Clients — no direct capture]
    CLI[vdisplay CLI]
    DSL[dsl2vdisplay]
    REST[rest2vdisplay]
    MCP[mcp2vdisplay]
  end
  subgraph control [Control layer]
    REQ[CommandRequest]
    EXEC[application.executor]
  end
  subgraph broker [vdisplay-agent 127.0.0.1:8765]
    RT[AgentRuntime]
    CAP[capture providers + ScreenCast]
    DISC[discovery / sessions]
  end
  CLI --> DSL
  DSL --> REQ
  REQ --> EXEC
  REST --> DSL
  MCP --> DSL
  EXEC -->|VDISPLAY_AGENT_URL| RT
  EXEC -->|no URL| LOCAL[vdisplay in-process]
  RT --> CAP
  RT --> DISC
```

When `VDISPLAY_AGENT_URL` is set, `dsl2vdisplay.dispatch()` builds a `CommandRequest` and `application.executor.execute()` routes to the broker via `AgentClient`. The agent sets `VDISPLAY_AGENT_BROKER=1` internally so it never calls itself recursively.

Legacy `vdisplay.agent_dispatch` still works but is **deprecated** — use `application.executor.execute` for new code.

## Install and run

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay

# terminal 1 — broker (localhost only)
vdisplay-agent serve
# or: vdisplay agent serve
# default: http://127.0.0.1:8765

# terminal 2 — clients
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
```

Optional auth:

```bash
export VDISPLAY_AGENT_TOKEN=your-secret
# clients send: Authorization: Bearer your-secret
```

## Environment variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `VDISPLAY_AGENT_URL` | clients | Broker base URL (e.g. `http://127.0.0.1:8765`) |
| `VDISPLAY_AGENT_TOKEN` | clients + agent | Optional Bearer token |
| `VDISPLAY_AGENT_HOST` | agent | Bind address (default `127.0.0.1`) |
| `VDISPLAY_AGENT_PORT` | agent | Listen port (default `8765`) |
| `VDISPLAY_AGENT_BROKER` | agent only | Set to `1` inside broker — do not set on clients |
| `VDISPLAY_AGENT_DB` | agent | Task persistence DB path (default `~/.cache/vdisplay/agent-tasks.db`) |
| `VDISPLAY_CAPTURE_ALLOW_PORTAL` | agent | Set to `1` to opt in to xdg-desktop-portal capture |
| `DISPLAY` | agent | Host X display (default auto-resolves to `:0`) |

## Agent HTTP API

### Health and discovery

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| GET | `/capabilities` | Platform + control + task persistence capabilities |
| GET | `/diagnostics` | DISPLAY / session diagnostics |
| GET | `/outputs` | Connected monitors (fast; no window enrichment) |
| GET | `/windows` | Application windows (query params as CLI filters) |

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sessions` | Unified session catalog (virtual, mirror, relay, terminal, screencast, sampler) |
| POST | `/session/virtual/start` | Start Xvfb session |
| POST | `/session/mirror/start` | Start mirror session |
| POST | `/session/relay/start` | Start relay session |
| POST | `/session/terminal/open` | Open controllable terminal PTY session |
| POST | `/session/browser/open` | Open Playwright browser session (`url`, `session_id`, `headless`) |
| POST | `/session/screencast/start` | Start persistent portal ScreenCast (Wayland; one consent) |
| POST | `/session/screencast/stop` | Stop ScreenCast session |
| GET | `/session/screencast/status` | ScreenCast session state |
| POST | `/session/{id}/stop` | Stop session |

### Tasks (durable broker work)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tasks` | List persisted tasks (`?status=`, `?kind=`) |
| GET | `/tasks/{task_id}` | Task detail with `config` and `state` |
| POST | `/tasks/{task_id}/heartbeat` | Refresh lease; optional `state` body |
| POST | `/tasks/{task_id}/stop` | Mark task stopped |

Tasks survive broker introspection across restarts. Orphan `running` tasks from a previous broker process are marked `stale` on startup.

### Sampler and capture

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sampler/start` | Background frame sampler (returns `task_id`) |
| POST | `/sampler/stop` | Stop sampler |
| GET | `/sampler/status` | Sampler state + heartbeat refresh |
| POST | `/capture/frame` | Screenshot (PNG path or base64 in body) |

### Control plane

| Method | Path | Description |
|--------|------|-------------|
| GET | `/control/plugins` | Registered control provider plugins |
| GET | `/diagnostics/control` | Control readiness + routing + extension catalog |
| POST | `/controls/list` | List control tree |
| POST | `/controls/find` | Find nodes by selector |
| POST | `/control/invoke` | Invoke / click |
| POST | `/control/focus` | Focus element |
| POST | `/control/set-value` | Set value / fill |

### Window relay

| Method | Path | Description |
|--------|------|-------------|
| POST | `/window/adopt` | Relay adopt window |
| POST | `/window/release` | Relay release window |

### Web console

Browser dashboard for multi-monitor supervision and capture control. Guide: [guides/web-console.md](guides/web-console.md).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/web` | HTML console (monitors, tasks, windows, replay) |
| GET | `/api/web/overview` | Aggregated broker state for dashboard |
| GET | `/api/web/frame/{monitor_name}` | PNG frame for one monitor |
| GET | `/api/web/frames` | All monitor frames (JSON) |
| POST | `/api/web/screencast/start` | Start ScreenCast from console (`multiple: true` default) |
| POST | `/api/web/sampler/start` | Start sampler from console (`all_monitors: true` default) |
| GET | `/api/web/replay/sessions` | List `.vdisplay` audit sessions |
| POST | `/api/web/replay/start` | Queue session replay (runs CONTROL_* steps in background) |
| GET | `/api/web/replay/status/{job_id}` | Replay job status |

```bash
xdg-open http://127.0.0.1:8765/web
curl -s http://127.0.0.1:8765/api/web/overview | jq '.data.monitors.monitor_count'
```

Quick checks:

```bash
curl -s http://127.0.0.1:8765/health | jq .
curl -s http://127.0.0.1:8765/outputs | jq '{monitor_count, monitors: [.monitors[].name]}'
```

## Client workflows

### CLI

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent health
vdisplay agent screencast status
vdisplay agent screencast start
vdisplay agent screencast stop
vdisplay monitors
vdisplay virtual screenshot -o /tmp/vd.png
```

### DSL

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
dsl2vdisplay -c 'HEALTH'
dsl2vdisplay -c 'MONITORS'
dsl2vdisplay -c 'SCREENSHOT OUT /tmp/out.png MODE virtual DISPLAY :99'
```

### REST (`rest2vdisplay`)

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
rest2vdisplay serve --port 8216 --agent-url http://127.0.0.1:8765

curl -s http://127.0.0.1:8216/health | jq .
curl -s -X POST http://127.0.0.1:8216/v1/dsl \
  -H 'content-type: application/json' \
  -d '{"verb":"MONITORS"}' | jq '.data.monitor_count'
curl -s -X POST http://127.0.0.1:8216/v1/dsl \
  -H 'content-type: text/plain' \
  -d 'HEALTH'
```

REST routes:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Adapter health + broker status |
| GET | `/capabilities` | Proxy to agent capabilities |
| GET | `/v1/schema` | DSL schema list |
| GET | `/v1/schema/{verb}` | Schema for one verb |
| POST | `/v1/dsl` | Execute DSL (JSON or plain text) |
| POST | `/v1/commands` | Alias for `/v1/dsl` |

### MCP (`mcp2vdisplay`)

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
mcp2vdisplay serve
```

Tools:

| Tool | Description |
|------|-------------|
| `vdisplay_agent_status` | Broker connectivity + capabilities |
| `vdisplay_run_command` | Single DSL line |
| `vdisplay_run_dsl` | Multi-line DSL script |
| `vdisplay_to_dsl` | NL → DSL (no side effects) |
| `vdisplay_screencast_start` | Start portal ScreenCast on agent (Wayland) |
| `vdisplay_screencast_stop` | Stop portal ScreenCast session |
| `vdisplay_screencast_status` | ScreenCast session state |

## Capture providers (host)

The agent tries driver-level providers in order:

- **Xvfb / owned display:** X11 → MSS (XCB) → DRM → fbdev
- **Wayland host:** DRM → fbdev → MSS → X11
- **Portal:** only when `VDISPLAY_CAPTURE_ALLOW_PORTAL=1`

Virtual display screenshots (`MODE virtual`, Xvfb `:99`) work without portal prompts. Host mirror screenshots on **GNOME Wayland + NVIDIA** often fail until a persistent ScreenCast session is started in the agent, or until the user has DRM access (e.g. `video` group for `/dev/fb0`).

### Etap 2 — persistent ScreenCast (Wayland)

Start once (interactive source picker + Screen Recording consent), then capture many frames without new prompts:

```bash
curl -s -X POST http://127.0.0.1:8765/session/screencast/start \
  -H 'content-type: application/json' \
  -d '{"interactive": true}' | jq .

# or via CLI (requires VDISPLAY_AGENT_URL)
vdisplay agent screencast start

curl -s http://127.0.0.1:8765/session/screencast/status | jq .
vdisplay agent screencast status

# host capture now uses the open PipeWire stream
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay screenshot -o /tmp/host.png --source DP-1

curl -s -X POST http://127.0.0.1:8765/session/screencast/stop | jq .
vdisplay agent screencast stop
```

Requirements on the agent host:

- `python3-dbus`, `python3-gi` (GNOME session bus)
- `ffmpeg` built with PipeWire input **or** GStreamer `pipewiresrc`
- Screen Recording permission for `vdisplay-agent` in GNOME Settings

## Typical multi-terminal setup

```bash
# 1 — broker
vdisplay-agent serve --port 8765

# 2 — export once per shell / systemd user unit
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

# optional: install broker as user service (Linux)
mkdir -p ~/.config/systemd/user
cp packaging/systemd/vdisplay-agent.user.service ~/.config/systemd/user/
# edit ExecStart if vdisplay-agent is not in ~/.local/bin
systemctl --user daemon-reload
systemctl --user enable --now vdisplay-agent.service
```

Environment file (optional):

```bash
mkdir -p ~/.config/vdisplay
printf 'VDISPLAY_AGENT_URL=http://127.0.0.1:8765\n' > ~/.config/vdisplay/agent.env
# add to shell: set -a; source ~/.config/vdisplay/agent.env; set +a
```

```bash
# 3 — any combination of adapters
rest2vdisplay serve --port 8216
mcp2vdisplay serve
dsl2vdisplay -c 'MONITORS'
vdisplay screenshot --all-monitors --out-dir /tmp/shots --mode mirror
```

## Related

- [Control plane](control-plane.md)
- [RFC 001 — extensibility model](rfc/001-extensibility-model.md)
- [Troubleshooting — agent and capture](troubleshooting.md#vdisplay-agent-and-capture)
- [Installation — control layer](installation.md#control-layer-and-agent)
- [Example: agent-broker](../examples/agent-broker/)
- [Architecture](architecture.md)
- [packages/vdisplay-agent/README.md](../packages/vdisplay-agent/README.md)

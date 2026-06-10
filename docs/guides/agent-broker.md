# Guide: agent broker

**Question:** Should I run `vdisplay-agent serve` or call vdisplay in-process?

## Use the broker when

- You are on a **desktop host** (GNOME Wayland or X11 with portal/screencast).
- Multiple clients (CLI, DSL, REST, MCP) should share one capture runtime.
- You need **ScreenCast** for Wayland screenshots (portal consent).

## Use in-process when

- **CI / Docker** with Xvfb (`:99`) — no host display.
- **Unit tests** — `unset VDISPLAY_AGENT_URL`.
- Single-shot scripts that do not need portal persistence.

## Quick setup

```bash
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
```

Inside the broker process, `VDISPLAY_AGENT_BROKER=1` prevents recursive self-calls. **Do not set that on clients.**

## Wayland screencast order

```bash
vdisplay-agent serve &          # 1 — agent must be running
sleep 2
vdisplay agent screencast start # 2 — portal picker
vdisplay screenshot -o out.png --source DP-1
```

Starting screencast before the agent is up loses the session.

## Routing rule

| `VDISPLAY_AGENT_URL` | Route |
|----------------------|-------|
| set (client) | HTTP → broker |
| unset | `application.services.*` in-process |

Broker process always runs local handlers (`VDISPLAY_AGENT_BROKER=1`).

## Full reference

- HTTP API, tasks DB, auth: [agent-broker.md](../agent-broker.md)
- Executor flow: [architecture.md](../architecture.md)
- Example: [examples/agent-broker](../../examples/agent-broker/)

# vdisplay-agent broker

Install the broker **once** on a desktop host; point CLI, DSL, REST, and MCP at it with `VDISPLAY_AGENT_URL`. Clients never open DRM, portal, or capture backends directly.

- Docs: [docs/agent-broker.md](../../docs/agent-broker.md)
- Examples: [docs/examples.md](../../docs/examples.md)

## Run

```bash
cd examples/agent-broker
chmod +x run.sh
./run.sh
```

The script starts a temporary agent on port **8777** (override with `VD_AGENT_PORT`), runs [broker_demo.py](broker_demo.py), then exits.

## With a persistent agent (recommended)

```bash
# terminal 1 — systemd or manual
vdisplay-agent serve --port 8765

# terminal 2
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
python3 examples/agent-broker/broker_demo.py
```

Systemd user unit: [packaging/systemd/vdisplay-agent.user.service](../../packaging/systemd/vdisplay-agent.user.service)

## Wayland host screenshots (ScreenCast)

On GNOME Wayland, driver capture (DRM/fbdev) often fails. Start a **persistent ScreenCast session** in the agent once:

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

curl -X POST http://127.0.0.1:8765/session/screencast/start \
  -H 'content-type: application/json' \
  -d '{"interactive": true}'

vdisplay screenshot -o output/host.png --source DP-1
vdisplay mirror screenshot -o output/mirror.png --source primary

curl -X POST http://127.0.0.1:8765/session/screencast/stop
```

Requirements: `python3-dbus`, `python3-gi`, `ffmpeg` with PipeWire (or GStreamer `pipewiresrc`), Screen Recording permission for `vdisplay-agent`.

## REST + DSL

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
rest2vdisplay serve --port 8216 --agent-url $VDISPLAY_AGENT_URL

curl -s http://127.0.0.1:8216/health | jq .
curl -s -X POST http://127.0.0.1:8216/v1/dsl -H 'content-type: text/plain' -d 'MONITORS' | jq .
dsl2vdisplay -c 'MONITORS'
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VDISPLAY_AGENT_URL` | — | Broker base URL for all clients |
| `VDISPLAY_AGENT_TOKEN` | — | Optional Bearer auth |
| `VDISPLAY_AGENT_PORT` | `8765` | Agent listen port |
| `VD_AGENT_PORT` | `8777` | Port used by `run.sh` demo only |

See [docs/agent-broker.md](../../docs/agent-broker.md) for the full HTTP API.

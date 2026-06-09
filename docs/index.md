# vdisplay documentation

Cross-platform virtual display orchestration for Python agents, CI pipelines, and headless automation.

## Quick links

| Resource | Description |
|----------|-------------|
| [README.md](../README.md) | Project overview, API summary, CLI reference |
| [Installation](installation.md) | System dependencies and Python setup |
| [Agent broker](agent-broker.md) | **vdisplay-agent** — install once, REST/MCP/DSL, ScreenCast |
| [Architecture](architecture.md) | CommandRequest + executor (local vs agent routing) |
| [Docker guide](docker-guide.md) | Running vdisplay in containers |
| [Examples index](examples.md) | All usage examples by environment |
| [Troubleshooting](troubleshooting.md) | Common CLI errors and fixes |
| [packages/README.md](../packages/README.md) | Control layer (DSL, MCP, REST, NL) |

## Recommended desktop setup

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
```

Try: [examples/agent-broker](../examples/agent-broker/) · [agent-broker.md](agent-broker.md) · [architecture.md](architecture.md)

## Modes

| Mode | Class / API | Use when |
|------|-------------|----------|
| `virtual` | `VirtualDisplaySession` | Isolated headless display (Xvfb) |
| `mirror` | `MirrorSession` | Duplicate an existing screen output |
| `relay` | `WindowRelaySession` | Hide/restore a window on the same session |
| `screencast` | Agent `POST /session/screencast/start` | Wayland host capture after one portal consent |

See [README.md — Modes](../README.md#modes) for the capability matrix.

## Output objects (`nl`)

Monitors and windows returned by the API, CLI, and control layer include **`nl`** — a natural-language description of their contents.

| Object | Source | `nl` describes |
|--------|--------|----------------|
| Monitor | `vdisplay monitors`, `vdisplay all`, DSL `MONITORS` | resolution, rotation, primary, visible apps |
| Window | `vdisplay windows`, `vdisplay all`, DSL `WINDOWS` | app label, size, monitor, process |
| Adopted window | `vdisplay relay list`, `vdisplay all` | off-screen stashed windows |

Example:

```bash
vdisplay all | jq '{monitors: .monitors[].nl, windows: .windows[].nl}'
```

## Examples by environment

| Environment | Path | Docker | Host desktop |
|-------------|------|--------|--------------|
| **Agent broker** | [examples/agent-broker](../examples/agent-broker/) | No | Yes |
| Headless virtual display | [examples/headless-virtual](../examples/headless-virtual/) | Yes | No |
| CI / agent screenshot | [examples/ci-agent](../examples/ci-agent/) | Yes | No |
| Dev workspace (mounted) | [examples/dev-workspace](../examples/dev-workspace/) | Yes | No |
| Mirror host desktop | [examples/host-mirror](../examples/host-mirror/) | Optional | Yes |
| Relay host windows | [examples/host-relay](../examples/host-relay/) | Optional | Yes |

Details: [examples.md](examples.md)

## Python API (minimal)

```python
from vdisplay import VirtualDisplaySession
from vdisplay.client import AgentClient

# In-process virtual display
vd = VirtualDisplaySession.create(width=1920, height=1080)
vd.start()
vd.save_screenshot("screen.png")
vd.stop()

# Via broker (when VDISPLAY_AGENT_URL is set)
client = AgentClient("http://127.0.0.1:8765")
client.outputs()
client.start_virtual(width=1280, height=720, display=":99")
```

Full API: [README.md](../README.md#python-api)

## CLI (minimal)

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765   # optional broker
vdisplay monitors
vdisplay virtual screenshot -o screen.png --display :99
```

Full CLI: [README.md](../README.md)

## Control layer

With broker (recommended on a desktop host):

```bash
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
dsl2vdisplay -c 'MONITORS'    # CommandRequest → executor → agent
rest2vdisplay serve --port 8216 --agent-url $VDISPLAY_AGENT_URL
mcp2vdisplay serve
```

Without broker (in-process, tests, containers):

```bash
dsl2vdisplay -c 'MONITORS DISPLAY :0'
nlp2vdisplay to-dsl "show windows on the primary monitor"
```

See [architecture.md](architecture.md), [packages/README.md](../packages/README.md), and [agent-broker.md](agent-broker.md).

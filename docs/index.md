# vdisplay documentation

Cross-platform virtual display orchestration for Python agents, CI pipelines, and headless automation.

## Quick links

| Resource | Description |
|----------|-------------|
| [README.md](../README.md) | Project overview, API summary, CLI reference |
| [Installation](installation.md) | System dependencies and Python setup |
| [Docker guide](docker-guide.md) | Running vdisplay in containers |
| [Examples index](examples.md) | All usage examples by environment |
| [Troubleshooting](troubleshooting.md) | Common CLI errors and fixes |
| [packages/README.md](../packages/README.md) | Control layer (DSL, MCP, REST) |

## Modes

| Mode | Class | Use when |
|------|-------|----------|
| `virtual` | `VirtualDisplaySession` | You need an isolated headless display (Xvfb) |
| `mirror` | `MirrorSession` | You want to duplicate an existing screen output |
| `relay` | `WindowRelaySession` | You want to hide/restore a window on the same X11 session |

See [README.md — Modes](../README.md#modes) for the capability matrix.

## Examples by environment

| Environment | Path | Docker | Host X11 required |
|-------------|------|--------|-------------------|
| Headless virtual display | [examples/headless-virtual](../examples/headless-virtual/) | Yes | No |
| CI / agent screenshot | [examples/ci-agent](../examples/ci-agent/) | Yes | No |
| Dev workspace (mounted) | [examples/dev-workspace](../examples/dev-workspace/) | Yes | No |
| Mirror host desktop | [examples/host-mirror](../examples/host-mirror/) | Yes | Yes |
| Relay host windows | [examples/host-relay](../examples/host-relay/) | Yes | Yes |

## Python API (minimal)

```python
from vdisplay import VirtualDisplaySession, MirrorSession, WindowRelaySession

vd = VirtualDisplaySession.create(width=1920, height=1080)
vd.start()
vd.launch(["xterm"])
vd.save_screenshot("screen.png")
vd.stop()
```

Full API details: [README.md](../README.md#python-api)

## CLI (minimal)

```bash
vdisplay info
vdisplay virtual screenshot -o screen.png --display :99
```

Full CLI reference: [README.md](../README.md#cli)

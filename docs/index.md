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
| [packages/README.md](../packages/README.md) | Control layer (DSL, MCP, REST, NL) |

## Modes

| Mode | Class | Use when |
|------|-------|----------|
| `virtual` | `VirtualDisplaySession` | You need an isolated headless display (Xvfb) |
| `mirror` | `MirrorSession` | You want to duplicate an existing screen output |
| `relay` | `WindowRelaySession` | You want to hide/restore a window on the same X11 session |

See [README.md — Modes](../README.md#modes) for the capability matrix.

## Output objects (`nl`)

Monitors and windows returned by the API, CLI, and control layer include **`nl`** — a natural-language description of their contents.

| Object | Source | `nl` describes |
|--------|--------|----------------|
| Monitor | `vdisplay outputs`, DSL `OUTPUTS` | Resolution, rotation, primary flag, visible app names on that output |
| Window | `vdisplay relay list-windows`, DSL `WINDOWS` | App label, role, size, position, process, WM class |
| Adopted window | `vdisplay relay list`, `adopt-window` | Same as window, for stashed off-screen windows |

Example:

```bash
vdisplay outputs | jq '.outputs[].nl'
vdisplay relay list-windows --apps-only | jq '.windows[].nl'
```

## Examples by environment

| Environment | Path | Docker | Host X11 required |
|-------------|------|--------|-------------------|
| Headless virtual display | [examples/headless-virtual](../examples/headless-virtual/) | Yes | No |
| CI / agent screenshot | [examples/ci-agent](../examples/ci-agent/) | Yes | No |
| Dev workspace (mounted) | [examples/dev-workspace](../examples/dev-workspace/) | Yes | No |
| Mirror host desktop | [examples/host-mirror](../examples/host-mirror/) | Yes | Yes |
| Relay host windows | [examples/host-relay](../examples/host-relay/) | Yes | Yes |

Details: [examples.md](examples.md)

## Python API (minimal)

```python
from vdisplay import VirtualDisplaySession, MirrorSession, WindowRelaySession
from vdisplay.discovery import list_outputs, list_windows

for monitor in list_outputs():
    print(monitor["name"], monitor["nl"])

for window in list_windows(apps_only=True):
    print(window["app_label"], window["nl"])

vd = VirtualDisplaySession.create(width=1920, height=1080)
vd.start()
vd.launch(["xterm"])
vd.save_screenshot("screen.png")
vd.stop()
```

Full API: [README.md](../README.md#python-api)

## CLI (minimal)

```bash
vdisplay info
vdisplay outputs
vdisplay relay list-windows --apps-only
vdisplay virtual screenshot -o screen.png --display :99
```

Full CLI: [README.md](../README.md#cli)

## Control layer

```bash
dsl2vdisplay -c 'OUTPUTS DISPLAY :0'
dsl2vdisplay -c 'WINDOWS DISPLAY :0'
nlp2vdisplay to-dsl "show windows on the primary monitor"
```

See [packages/README.md](../packages/README.md).

# vdisplay documentation

**Start here:** [start-here.md](start-here.md) — install, local vs broker, first commands.

## Navigation

### Getting started

| Doc | Description |
|-----|-------------|
| [start-here.md](start-here.md) | **Entry point** — install, routing, choose your path |
| [installation.md](installation.md) | System and Python dependencies |
| [troubleshooting.md](troubleshooting.md) | Common errors and fixes |

### Guides (how do I…?)

| Guide | Question |
|-------|----------|
| [guides/agent-broker.md](guides/agent-broker.md) | Local vs broker? Screencast order? |
| [guides/wayland-control.md](guides/wayland-control.md) | Native Wayland / PyCharm / canvas? |
| [guides/gui-map-pack.md](guides/gui-map-pack.md) | Build and refresh GUI map? |
| [guides/vision-fallback.md](guides/vision-fallback.md) | OCR verify + vision LLM? |
| [guides/browser-control.md](guides/browser-control.md) | Playwright DOM control? |
| [guides/terminal-control.md](guides/terminal-control.md) | PTY grid control? |
| [guides/session-report.md](guides/session-report.md) | Session audit trail / recorder (implemented) |

### Reference (lookup)

| Doc | Description |
|-----|-------------|
| [reference/env.md](reference/env.md) | Environment variables |
| [reference/cli.md](reference/cli.md) | CLI command index |
| [reference/api.md](reference/api.md) | CommandRequest / SDK |
| [reference/dsl.md](reference/dsl.md) | DSL verbs |
| [reference/rest.md](reference/rest.md) | REST adapter |
| [reference/mcp.md](reference/mcp.md) | MCP tools |

### Architecture & control

| Doc | Description |
|-----|-------------|
| [architecture.md](architecture.md) | Executor routing, modules, extensibility |
| [control-plane.md](control-plane.md) | Providers, selector, verifier, plugins |
| [agent-broker.md](agent-broker.md) | Full broker HTTP API |
| [vision-only-wayland.md](vision-only-wayland.md) | Vision-only profile deep dive |
| [api-contract.md](api-contract.md) | Stable command/response contract |
| [rfc/001-extensibility-model.md](rfc/001-extensibility-model.md) | Control extension model |

### Examples & adapters

| Doc | Description |
|-----|-------------|
| [examples.md](examples.md) | Example project index |
| [docker-guide.md](docker-guide.md) | Containers |
| [packages/README.md](../packages/README.md) | DSL, MCP, REST, NL packages |

## Quick start (desktop)

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay

vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay monitors
```

## Modes

| Mode | Class / API | Use when |
|------|-------------|----------|
| `virtual` | `VirtualDisplaySession` | Isolated headless display (Xvfb) |
| `mirror` | `MirrorSession` | Duplicate an existing screen output |
| `relay` | `WindowRelaySession` | Hide/restore a window on the same session |
| `screencast` | Agent `POST /session/screencast/start` | Wayland host capture after portal consent |

## Output objects (`nl`)

Monitors and windows include **`nl`** — a natural-language description. See [README.md](../README.md#output-objects-nl) for examples.

## Python API (minimal)

```python
from vdisplay import VirtualDisplaySession
from vdisplay.client import AgentClient
from vdisplay.application.executor import execute
from vdisplay.application.commands import CommandRequest

vd = VirtualDisplaySession.create(width=1920, height=1080)
vd.start()
vd.save_screenshot("screen.png")
vd.stop()

client = AgentClient("http://127.0.0.1:8765")
client.outputs()
```

Full API: [reference/api.md](reference/api.md) · [README.md](../README.md)

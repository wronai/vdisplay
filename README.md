# vdisplay


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.13-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$7.69-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-9.7h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $7.6889 (16 commits)
- 👤 **Human dev:** ~$968 (9.7h @ $100/h, 30min dedup)

Generated on 2026-06-10 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Cross-platform **virtual display orchestration API** for Python.

One unified API, multiple OS backends with different capabilities. Monitors and windows include an **`nl`** field — a natural-language description of what they contain.

CLI, DSL, REST, MCP, and the local **vdisplay-agent** broker all route through **`application.executor`** and shared **application services** (`src/vdisplay/application/`).

## Quick start

```bash
pip install "vdisplay[pillow]"
# or from source (recommended for development):
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
```

```bash
unset DISPLAY   # optional: auto-resolves host display to :0
vdisplay all
vdisplay monitors
vdisplay windows --apps-only
```

## Documentation

| Start | Description |
|-------|-------------|
| **[docs/start-here.md](docs/start-here.md)** | **Entry point** — install, local vs broker, choose your path |

| Guides | Reference |
|--------|-----------|
| [Wayland control](docs/guides/wayland-control.md) | [Environment vars](docs/reference/env.md) |
| [GUI Map Pack](docs/guides/gui-map-pack.md) | [CLI index](docs/reference/cli.md) |
| [Vision fallback](docs/guides/vision-fallback.md) | [API / SDK](docs/reference/api.md) |
| [Agent broker](docs/guides/agent-broker.md) | [DSL](docs/reference/dsl.md) · [REST](docs/reference/rest.md) · [MCP](docs/reference/mcp.md) |
| [Browser](docs/guides/browser-control.md) · [Terminal](docs/guides/terminal-control.md) | |

| Architecture | Other |
|--------------|-------|
| [docs/architecture.md](docs/architecture.md) | [Installation](docs/installation.md) |
| [Control plane](docs/control-plane.md) | [Examples index](docs/examples.md) |
| [Agent broker (full API)](docs/agent-broker.md) | [Troubleshooting](docs/troubleshooting.md) |
| [Vision-only Wayland](docs/vision-only-wayland.md) | [packages/README.md](packages/README.md) |

Full index: [docs/index.md](docs/index.md)

## Examples

| Example | Mode | Host X11 | Run |
|---------|------|----------|-----|
| [headless-virtual](examples/headless-virtual/) | virtual | No | `cd examples/headless-virtual && docker compose up --build` |
| [agent-broker](examples/agent-broker/) | broker | No | `cd examples/agent-broker && ./run.sh` |
| [ci-agent](examples/ci-agent/) | virtual | No | `cd examples/ci-agent && docker compose run --rm ci-agent` |
| [dev-workspace](examples/dev-workspace/) | dev | No | `cd examples/dev-workspace && docker compose run --rm dev` |
| [host-mirror](examples/host-mirror/) | mirror | Yes | `cd examples/host-mirror && ./run.sh` |
| [host-relay](examples/host-relay/) | relay | Yes | `cd examples/host-relay && ./run.sh` |
| [run_all_examples.sh](examples/run_all_examples.sh) | mixed | varies | `./examples/run_all_examples.sh` |

Details: [docs/examples.md](docs/examples.md) · per-example READMEs in each folder above.

## Use cases

| Goal | Start here |
|------|------------|
| Desktop automation on GNOME Wayland | [docs/guides/wayland-control.md](docs/guides/wayland-control.md) |
| Persistent vision click targets | [docs/guides/gui-map-pack.md](docs/guides/gui-map-pack.md) |
| Broker + REST/MCP for agents | [docs/guides/agent-broker.md](docs/guides/agent-broker.md) |
| Headless CI screenshot | [examples/headless-virtual](examples/headless-virtual/) |
| Semantic browser/terminal control | [docs/control-plane.md](docs/control-plane.md) |

## Common commands

```bash
vdisplay all
vdisplay monitors
vdisplay windows --apps-only
vdisplay diagnose
vdisplay screenshot -o out.png --source DP-1    # Wayland: agent + screencast first
vdisplay diagnose control
vdisplay control click --backend vision --map maps/chat.json --target chat
```

CLI index: [docs/reference/cli.md](docs/reference/cli.md)

## Output objects (`nl`)

Monitors and windows include **`nl`** — a natural-language summary of contents.

```bash
vdisplay all | jq '{monitors: .monitors[].nl, windows: .windows[].nl}'
```

## Desktop workflows

Long-form GNOME / JetBrains / Firefox / screenshot workflows moved to guides:

- [docs/guides/wayland-control.md](docs/guides/wayland-control.md)
- [docs/guides/gui-map-pack.md](docs/guides/gui-map-pack.md)
- [docs/start-here.md](docs/start-here.md)

> **Legacy detail:** extended README sections (desktop workflows, control plane examples, screenshot recipes) remain in git history; prefer guides for maintenance.

## Control plane

Unified AT-SPI, browser, terminal, vision, and map backends. See [docs/control-plane.md](docs/control-plane.md) and task guides above.

```bash
vdisplay diagnose control
vdisplay control list --backend auto
vdisplay control click --role button --name Save --verify
```

## vdisplay-agent broker

```bash
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent screencast start   # Wayland portal — once per session
```

Full API: [docs/agent-broker.md](docs/agent-broker.md) · Guide: [docs/guides/agent-broker.md](docs/guides/agent-broker.md)

## Control layer equivalents

| Intent | CLI | DSL |
|--------|-----|-----|
| Full state | `vdisplay all` | `ALL DISPLAY :0` |
| Monitors | `vdisplay monitors` | `MONITORS DISPLAY :0` |
| Windows | `vdisplay windows --apps-only` | `WINDOWS DISPLAY :0` |
| Adopt window | `vdisplay relay adopt-window --app X` | `ADOPT APP X` |
| Screenshot | `vdisplay screenshot -o out.png` | `SCREENSHOT OUT out.png DISPLAY :99` |
| Validate tools | `vdisplay diagnose` | `VALIDATE DISPLAY :0` |

## Modes

| Mode | Purpose | Isolation | Screenshot | Window move |
|------|---------|-----------|------------|-------------|
| `virtual` | Private Xvfb session for agents | Yes | Yes | No (use `launch()`) |
| `mirror` | Duplicate existing display output | No | Yes | N/A |
| `relay` | Move window within same X11 session | Partial | Yes (`relay screenshot`) | Yes |
| `screencast` | Portal ScreenCast in agent (Wayland) | No | Yes (after consent) | N/A |

## Requirements (Linux v0.1)

| Component | Used by |
|-----------|---------|
| `Xvfb`, `xwd`, `scrot` | virtual / X11 capture |
| `xrandr` | mirror mode |
| `xdotool` | relay + input |
| `python3-dbus`, `python3-gi` | portal ScreenCast (Wayland host) |
| `ffmpeg` (PipeWire) or GStreamer `pipewiresrc` | ScreenCast frame grab |
| `Pillow` (optional) | faster PNG encoding |

```bash
sudo apt install xvfb x11-apps x11-utils xdotool scrot x11-xserver-utils
sudo apt install python3-dbus python3-gi   # Wayland ScreenCast in agent
pip install "vdisplay[pillow]"
```

Full setup: [docs/installation.md](docs/installation.md)

## Python API

### Sessions (backends)

```python
from vdisplay import VirtualDisplaySession, MirrorSession, WindowRelaySession
from vdisplay.discovery import list_monitors, list_windows

# Inspect monitors and windows with nl descriptions
for monitor in list_monitors():
    print(monitor["nl"])

for window in list_windows(apps_only=True):
    print(window["nl"])

# Virtual isolated display
vd = VirtualDisplaySession.create(width=1920, height=1080)
vd.start()
vd.launch(["xterm"])
vd.save_screenshot("screen.png")
vd.stop()

# Mirror existing desktop (same session, no isolation)
# On GNOME Wayland: start agent screencast before save_screenshot, or use capture_host_to_file()
m = MirrorSession.create(source="primary", target="DP-1")
m.start()
m.save_screenshot("mirror.png")   # needs ScreenCast on Wayland
m.stop()

# Relay window off-screen and restore (persists across CLI calls)
r = WindowRelaySession.create()
r.start()
r.adopt_window(match_app="JetBrains")
r.release_window(match_app="JetBrains")
r.stop()
```

### Application layer (shared by CLI / DSL / REST / MCP / agent)

```python
from vdisplay.application.commands import CommandRequest
from vdisplay.application.executor import execute
from vdisplay.application.services import discovery, capture, session, info

# Single execution entry (routes to agent when VDISPLAY_AGENT_URL is set)
result = execute(CommandRequest.from_dsl({"verb": "MONITORS"}, line="MONITORS"))
print(result.data)

# Direct service use-cases (always in-process)
monitors = discovery.list_monitors(display=":0")
meta = capture.capture_screenshot(output="screen.png", monitor=1)
session.virtual_start(width=1280, height=720, display=":99")
caps = info.platform_info()
```

Via broker SDK:

```python
from vdisplay.client import AgentClient

client = AgentClient("http://127.0.0.1:8765")
client.outputs()
client.start_screencast(interactive=True)
```

### Window heuristics (testable submodules)

```python
from vdisplay.windows import list_windows_enriched, find_windows, pick_best_window
from vdisplay.windows.rank import dedupe_app_windows
from vdisplay.windows.filter import is_internal_window
```

## Project layout

```
src/vdisplay/
├── application/
│   ├── commands.py         # CommandRequest / CommandResult / CommandVerb
│   ├── executor.py         # single entry: execute() → local or agent
│   ├── handlers/           # local + agent command handlers
│   └── services/           # discovery, capture, session, info
├── commands/               # CLI registry (set_defaults per subcommand)
├── windows/                # scan → normalize → filter → rank → query
├── capture/
│   ├── providers/          # drm, fbdev, mss, x11, portal (opt-in)
│   └── portal_screencast.py  # persistent ScreenCast (Wayland)
├── backends/               # virtual, mirror, relay
├── client.py               # AgentClient SDK
└── cli.py                  # thin entry: register_all + args.func(args)

packages/
├── dsl2vdisplay/           # grammar + CQRS bus → executor
├── vdisplay-agent/         # localhost broker (privileged runtime)
├── rest2vdisplay/          # HTTP → DSL
├── mcp2vdisplay/           # MCP tools
└── nlp2vdisplay/           # NL → DSL
```

## Control layer (DSL / MCP / REST / NL)

Programmatic interfaces on top of the same application services. All query results include `nl` on monitors and windows.

| Package | Role |
|---------|------|
| [dsl2vdisplay](packages/dsl2vdisplay/) | Grammar + CQRS bus (`MONITORS`, `WINDOWS`, `ADOPT`, …) |
| [nlp2vdisplay](packages/nlp2vdisplay/) | Natural language → DSL |
| [uri2vdisplay](packages/uri2vdisplay/) | `vdisplay://cmd/...` → DSL |
| [cli2vdisplay](packages/cli2vdisplay/) | REPL over DSL |
| [mcp2vdisplay](packages/mcp2vdisplay/) | MCP server tools |
| [rest2vdisplay](packages/rest2vdisplay/) | REST API on port 8216 |
| [vdisplay-agent](packages/vdisplay-agent/) | Local broker — sessions, capture, relay |

```bash
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
rest2vdisplay serve --port 8216 --agent-url $VDISPLAY_AGENT_URL
mcp2vdisplay serve
curl -s http://127.0.0.1:8216/health | jq .
curl -s -X POST http://127.0.0.1:8216/v1/dsl -H 'content-type: text/plain' -d 'MONITORS' | jq .
```

Full reference: [packages/README.md](packages/README.md)

## Limitations

- Existing windows on `DISPLAY=:0` **cannot** move into Xvfb `:99` — different X servers.
- Use `VirtualDisplaySession.launch()` for apps on the virtual display.
- Use `WindowRelaySession` to hide/show windows on the current session.
- `mirror` controls the same desktop through a duplicated output, not an isolated copy.
- `nl` on monitors lists apps whose window center falls on that output geometry.
- On **GNOME Wayland**, Docker X11 forwarding often produces black screenshots — use [vdisplay-agent](docs/agent-broker.md) on the host instead.
- Windows/macOS backends are planned; Linux/X11 + Wayland (via agent) supported in v0.1.

Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)

## Development

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
pytest tests/ -q
./examples/agent-broker/run.sh
./examples/run_all_examples.sh   # where host X11 is available
```

Architecture: [docs/architecture.md](docs/architecture.md)

## License

Licensed under Apache-2.0.

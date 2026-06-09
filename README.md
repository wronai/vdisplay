# vdisplay


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.3-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.60-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-2.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.5974 (2 commits)
- 👤 **Human dev:** ~$200 (2.0h @ $100/h, 30min dedup)

Generated on 2026-06-09 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Cross-platform **virtual display orchestration API** for Python.

One unified API, multiple OS backends with different capabilities. Monitors and windows include an **`nl`** field — a natural-language description of what they contain.

## Quick start

```bash
pip install "vdisplay[pillow]"
# or from source: pip install -e ".[dev]"
```

## List monitors, windows, and display info

Each monitor and window includes **`nl`** — a human-readable summary of what it contains.

```bash
unset DISPLAY                         # optional: auto-resolves host display to :0

# monitors (xrandr) — name, geometry, rotation, primary, nl
vdisplay outputs
vdisplay outputs | jq '.outputs[] | {name, primary, nl}'

# windows on the current display — title, app, pid, class, nl
vdisplay relay list-windows --apps-only
vdisplay relay list-windows --app "Firefox"
vdisplay relay list-windows --class jetbrains-toolbox --pid 32977

# platform capabilities + outputs
vdisplay info

# diagnose DISPLAY, socket, output count
vdisplay diagnose

# adopted (off-screen) windows — persisted in ~/.cache/vdisplay/
vdisplay relay list
```

Filter windows with `--title`, `--app`, `--class`, `--pid`, or `--window-id`. Use `--all` to include internal/helper windows.

### Example output

Monitor:

```json
{
  "name": "DP-2",
  "primary": true,
  "width": 4320,
  "height": 7680,
  "rotation": "left",
  "rotation_degrees": 90,
  "nl": "Primary monitor DP-2 (4320×7680, rotated left (90°)). Visible apps: Toolbox."
}
```

Window:

```json
{
  "window_id": "8388615",
  "app_label": "Toolbox",
  "title": "Toolbox",
  "type": "application",
  "wm_class": "jetbrains-toolbox",
  "pid": 32977,
  "nl": "Toolbox application window (880×1326 at (4470,298)), process jetbrains-toolb, class jetbrains-toolbox."
}
```

## Actions — virtual, mirror, relay

```bash
# virtual display (isolated Xvfb)
vdisplay virtual screenshot -o screen.png --display :99

# mirror — needs two outputs; list names first with: vdisplay outputs
vdisplay mirror start --source primary --target DP-1 -o mirror.png
VD_SOURCE=DP-2 VD_TARGET=HDMI-1 ./examples/host-mirror/run.sh

# relay — hide window off-screen, restore later (separate CLI calls OK)
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay release-window --app "JetBrains"
```

Control layer equivalents:

```bash
dsl2vdisplay -c 'OUTPUTS DISPLAY :0'
dsl2vdisplay -c 'WINDOWS DISPLAY :0'
nlp2vdisplay to-dsl "list monitors on display zero"
```

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/index.md](docs/index.md) | Documentation hub |
| [docs/installation.md](docs/installation.md) | System and Python setup |
| [docs/docker-guide.md](docs/docker-guide.md) | Running in Docker |
| [docs/examples.md](docs/examples.md) | All usage examples |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common errors and fixes |
| [packages/README.md](packages/README.md) | Control layer — DSL, MCP, REST, NL |

## Examples

| Example | Mode | Host X11 | Run |
|---------|------|----------|-----|
| [headless-virtual](examples/headless-virtual/) | virtual | No | `cd examples/headless-virtual && docker compose up --build` |
| [ci-agent](examples/ci-agent/) | virtual | No | `cd examples/ci-agent && docker compose run --rm ci-agent` |
| [dev-workspace](examples/dev-workspace/) | dev | No | `cd examples/dev-workspace && docker compose run --rm dev` |
| [host-mirror](examples/host-mirror/) | mirror | Yes | `cd examples/host-mirror && ./run.sh` |
| [host-relay](examples/host-relay/) | relay | Yes | `cd examples/host-relay && ./run.sh` |

See [docs/examples.md](docs/examples.md) for details on each example.

## Modes

| Mode | Purpose | Isolation | Screenshot | Window move |
|------|---------|-----------|------------|-------------|
| `virtual` | Private Xvfb session for agents | Yes | Yes | No (use `launch()`) |
| `mirror` | Duplicate existing display output | No | Yes | N/A |
| `relay` | Move window within same X11 session | Partial | No | Yes |

## Requirements (Linux v0.1)

- `Xvfb` — virtual display
- `xwd` / `scrot` — screen capture (scrot fallback on multi-monitor XWayland)
- `xrandr` — mirror configuration
- `xdotool` — window relay and input
- `Pillow` (optional) — faster PNG encoding; pure-Python PNG fallback included

```bash
sudo apt install xvfb x11-apps x11-utils xdotool scrot
pip install "vdisplay[pillow]"
```

## Python API

```python
from vdisplay import VirtualDisplaySession, MirrorSession, WindowRelaySession
from vdisplay.discovery import list_outputs, list_windows

# Inspect monitors and windows with nl descriptions
for monitor in list_outputs():
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
m = MirrorSession.create(source="primary", target="DP-1")
m.start()
m.save_screenshot("mirror.png")
m.stop()

# Relay window off-screen and restore (persists across CLI calls)
r = WindowRelaySession.create()
r.start()
r.adopt_window(match_app="JetBrains")
r.release_window(match_app="JetBrains")
r.stop()
```

## Control layer (DSL / MCP / REST / NL)

Programmatic interfaces on top of the same API. All query results include `nl` on monitors and windows.

| Package | Role |
|---------|------|
| [dsl2vdisplay](packages/dsl2vdisplay/) | Grammar + CQRS bus (`OUTPUTS`, `WINDOWS`, `ADOPT`, …) |
| [nlp2vdisplay](packages/nlp2vdisplay/) | Natural language → DSL |
| [uri2vdisplay](packages/uri2vdisplay/) | `vdisplay://cmd/...` → DSL |
| [cli2vdisplay](packages/cli2vdisplay/) | REPL over DSL |
| [mcp2vdisplay](packages/mcp2vdisplay/) | MCP server tools |
| [rest2vdisplay](packages/rest2vdisplay/) | REST API on port 8216 |

```bash
pip install -e packages/dsl2vdisplay
rest2vdisplay serve --port 8216
mcp2vdisplay serve
```

Full reference: [packages/README.md](packages/README.md)

## Limitations

- Existing windows on `DISPLAY=:0` **cannot** move into Xvfb `:99` — different X servers.
- Use `VirtualDisplaySession.launch()` for apps on the virtual display.
- Use `WindowRelaySession` to hide/show windows on the current session.
- `mirror` controls the same desktop through a duplicated output, not an isolated copy.
- `nl` on monitors lists apps whose window center falls on that output geometry.
- Windows/macOS backends are planned; Linux/X11 is fully supported in v0.1.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

Licensed under Apache-2.0.

# vdisplay


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.5-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$2.18-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-3.1h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $2.1795 (4 commits)
- 👤 **Human dev:** ~$306 (3.1h @ $100/h, 30min dedup)

Generated on 2026-06-09 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

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

| Doc | Description |
|-----|-------------|
| [docs/index.md](docs/index.md) | Documentation hub — start here |
| [docs/installation.md](docs/installation.md) | System and Python setup |
| [docs/docker-guide.md](docs/docker-guide.md) | Running in Docker |
| [docs/examples.md](docs/examples.md) | All usage examples by environment |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common errors and fixes |
| [docs/agent-broker.md](docs/agent-broker.md) | **vdisplay-agent** — install-once broker, env vars, REST/MCP |
| [docs/architecture.md](docs/architecture.md) | CommandRequest + executor routing (local vs agent) |
| [examples/README.md](examples/README.md) | Runnable example projects |
| [packages/README.md](packages/README.md) | Control layer — DSL, MCP, REST, NL, agent |

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

## List monitors, windows, and display state

Each monitor and window includes **`nl`** — a human-readable summary of what it contains.

```bash
# everything — monitors + application windows + adopted (off-screen)
vdisplay all
vdisplay all | jq '{monitors: .monitor_count, windows: .window_count, adopted: .adopted_count}'

# monitors only (xrandr) — name, geometry, rotation, primary, nl
vdisplay monitors
vdisplay monitors | jq '.monitors[] | {name, primary, nl}'

# application windows only — title, app, pid, class, nl
vdisplay windows --apps-only
vdisplay windows --app "Firefox"
vdisplay windows --class jetbrains-toolbox --pid 32977
vdisplay windows --min-width 400 --min-height 300

# platform capabilities + monitors
vdisplay info

# diagnose DISPLAY, socket, monitor count
vdisplay diagnose

# adopted (off-screen) windows — persisted in ~/.cache/vdisplay/
vdisplay relay list
```

| Command | Shows |
|---------|--------|
| `vdisplay all` | monitors + windows + adopted |
| `vdisplay monitors` | connected displays only |
| `vdisplay windows` | visible application windows only |
| `vdisplay relay list` | windows moved off-screen by relay |
| `vdisplay info` | platform capabilities |
| `vdisplay diagnose` | DISPLAY diagnostics |

`vdisplay outputs` still works but is **deprecated** — use `vdisplay all` or `vdisplay monitors`.
`vdisplay relay list-windows` is deprecated — use `vdisplay windows`.

Filter windows with `--app`, `--class`, `--pid`, `--min-width`, `--min-height`. Use `--all` (default) to include internal/helper windows; `--apps-only` excludes them.

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
  "monitor_id": 0,
  "nl": "Primary monitor DP-2 (4320×7680, rotated left (90°)). Visible apps: Toolbox."
}
```

Window:

```json
{
  "window_id": "8388615",
  "app_label": "Toolbox",
  "monitor_id": 0,
  "monitor_name": "DP-2",
  "monitor_index": 0,
  "pid": 32977,
  "nl": "Toolbox application window (880×1326 at (4470,298)) on monitor DP-2, process jetbrains-toolb, class jetbrains-toolbox."
}
```

## Screenshots

### Quick reference

| Goal | Command |
|------|---------|
| One monitor (host) | `vdisplay screenshot -o screen.png --source DP-2` |
| All monitors | `vdisplay screenshot --all-monitors --out-dir ./captures` |
| Virtual Xvfb (no portal) | `vdisplay virtual screenshot -o screen.png --display :99` |
| Mirror + capture | `vdisplay mirror screenshot -o mirror.png --source primary --target DP-1` |
| Describe saved PNG (`img2nl`) | `vdisplay screenshot -o screen.png` → JSON field `nl` |
| Loop every 1s (after screencast) | see [Continuous capture](#continuous-capture-wayland) below |

With **`VDISPLAY_AGENT_URL`** set, screenshots route through the broker (same providers, one runtime).

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

# single monitor — use output name from: vdisplay monitors
vdisplay screenshot -o screen.png --monitor 1
vdisplay screenshot -o screen.png --source DP-2

# all connected monitors (DP-2.png, DP-1.png, HDMI-1.png, …)
vdisplay screenshot --all-monitors --out-dir ./captures

# isolated Xvfb session (works without portal / on headless CI)
vdisplay virtual screenshot -o screen.png --display :99
vdisplay screenshot -o vd.png --mode virtual --vd-display :99

# mirror: prefer mirror screenshot on Wayland (uses ScreenCast when active)
vdisplay mirror screenshot -o mirror.png --source primary --target DP-1
```

### Wayland host (GNOME) — start here

On **GNOME Wayland**, `DISPLAY=:0` is XWayland — direct X11/DRM capture often yields **black PNGs** (especially with NVIDIA).

**One-time setup** — needs **two terminals** (broker must stay running):

```bash
# terminal 1 — leave this running (blocks the shell)
vdisplay agent serve
# same as: vdisplay-agent serve
```

```bash
# terminal 2 — all capture commands go here
vdisplay agent health                    # should return {"status":"ok",...}
vdisplay agent screencast start          # pick monitor in portal dialog (once)
# GNOME: Settings → Privacy → Screen Recording → allow vdisplay-agent / terminal
```

> **Common mistake:** running `vdisplay agent screencast start` before `vdisplay agent serve`
> gives `Set VDISPLAY_AGENT_URL … or start: vdisplay-agent serve`. Start the broker first.

`VDISPLAY_AGENT_URL` is optional when the broker listens on `127.0.0.1:8765` (auto-detect).
Explicit export still works: `export VDISPLAY_AGENT_URL=http://127.0.0.1:8765`

**Then capture as often as you like** (no new prompts):

```bash
vdisplay screenshot -o host.png --source DP-2
vdisplay screenshot -o host.png --source primary
vdisplay mirror screenshot -o mirror.png --source primary --target DP-1
vdisplay relay screenshot -o relay.png --source DP-2
```

REST equivalent:

```bash
curl -X POST http://127.0.0.1:8765/session/screencast/start \
  -H 'content-type: application/json' -d '{"interactive": true}'
vdisplay screenshot -o host.png --source DP-1
```

> **Note:** `vdisplay mirror start -o mirror.png` runs xrandr mirror then tries driver-level capture directly.
> On Wayland use **`vdisplay mirror screenshot`** (or `vdisplay screenshot`) after screencast is active.

### Continuous capture (Wayland)

After `vdisplay agent screencast start`, grab frames every second without portal prompts:

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
mkdir -p ./captures
i=0
while true; do
  vdisplay screenshot -o "./captures/frame-$(printf '%04d' "$i").png" --source DP-2
  i=$((i + 1))
  sleep 1
done
```

Python (virtual display — no portal needed):

```python
import time
from pathlib import Path
from vdisplay import VirtualDisplaySession

vd = VirtualDisplaySession.create(display=":99")
vd.start()
try:
    for i in range(60):
        vd.save_screenshot(f"frame-{i:04d}.png")
        time.sleep(1)
finally:
    vd.stop()
```

See also [examples/ci-agent/](examples/ci-agent/) (`VD_FRAMES=60` in Docker).

### Describe a screenshot (`img2nl`)

By default, `vdisplay screenshot` enriches JSON with an **`nl`** field — a natural-language description of the saved PNG (Polish locale by default):

```bash
vdisplay screenshot -o screen.png --source DP-2 | jq '{path, nl, img2nl}'
```

Requires optional package: `pip install img2nl[analyze]`. Disable with `VDISPLAY_IMG2NL=0` or `vdisplay screenshot --no-img2nl`.

To describe an **existing** image file:

```python
from vdisplay.application.services.img2nl_enrich import describe_screenshot_image
print(describe_screenshot_image("screen.png")["text"])
```

## Actions — virtual, mirror, relay

```bash
# virtual display (isolated Xvfb)
vdisplay virtual start --width 1920 --height 1080 --display :99
vdisplay virtual launch xterm -hold          # flags after the command name are OK
vdisplay virtual screenshot -o screen.png --display :99

# mirror — needs two monitors; list names first with: vdisplay monitors
vdisplay mirror start --source primary --target DP-1          # xrandr only (no PNG)
vdisplay mirror screenshot -o mirror.png --source primary --target DP-1   # Wayland: screencast first
VD_SOURCE=DP-2 VD_TARGET=HDMI-1 ./examples/host-mirror/run.sh   # Docker; black PNGs on Wayland

# relay — hide window off-screen, restore later (separate CLI calls OK)
# 1) find a window to move
vdisplay windows --apps-only
vdisplay windows --app "JetBrains" | jq '.windows[] | {window_id, app_label, nl}'

# 2) adopt (move off-screen) — match by app, title, class, pid, or window-id
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay adopt-window --title "Firefox"
vdisplay relay adopt-window --class jetbrains-toolbox --pid 32977
vdisplay relay adopt-window --window-id 8388615

# 3) move to another monitor instead of off-screen
vdisplay relay adopt-window --app "Firefox" --target HDMI-1

# 4) list adopted windows (persisted in ~/.cache/vdisplay/)
vdisplay relay list
vdisplay relay list | jq '.adopted[] | {window_id, app_label, title, nl}'

# 5) restore — separate CLI call works (geometry saved on adopt)
vdisplay relay release-window --app "JetBrains"
vdisplay relay release-window --window-id 8388615

# 6) screenshot while relaying (Wayland: agent serve + screencast first)
# terminal 1: vdisplay agent serve
vdisplay agent screencast start
vdisplay relay screenshot -o before.png --source DP-2
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay screenshot -o after-hide.png --source DP-2
vdisplay relay release-window --app "JetBrains"
vdisplay relay screenshot -o after-restore.png --source DP-2

# 7) full host demo (before / after adopt / after release PNGs)
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent screencast start
WINDOW_APP=JetBrains ./examples/host-relay/run-host.sh
# output: examples/host-relay/output/before_automation.png, after_adopt.png, after_release.png
```

**Relay tips**

- Adopted window positions **persist** across CLI calls (`~/.cache/vdisplay/__vdisplay_stash__-*.json`).
- Relay moves windows within the **same X11 session** — it does not move apps into Xvfb `:99`.
- On **Wayland**, window move uses XWayland; screenshots need **agent + screencast** (Docker `./run.sh` often yields black PNGs — use `./run-host.sh` instead).
- Filter windows first: `vdisplay windows --app "Toolbox"` → use `--app`, `--title`, or `--window-id` from JSON.

## Natural language and DSL

```bash
# NL → DSL → JSON (built into vdisplay)
vdisplay nlp "list monitors on display zero"
vdisplay nlp "show application windows" --dsl-only

# DSL bus (same semantics as CLI query verbs)
dsl2vdisplay -c 'MONITORS DISPLAY :0'
dsl2vdisplay -c 'WINDOWS DISPLAY :0 APPS_ONLY'
dsl2vdisplay -c 'ALL DISPLAY :0'

# NL package (thin wrapper; pip install -e packages/nlp2vdisplay)
nlp2vdisplay to-dsl "list monitors on display zero"
nlp2vdisplay apply "show application windows on display zero"
# shorthand — bare prompt defaults to apply:
nlp2vdisplay "show application windows on display zero"
```

Legacy DSL verbs still work: `OUTPUTS` maps to `MONITORS`, `WINDOWS` unchanged.

## vdisplay-agent broker

Install **once** on the host. CLI, DSL, REST, and MCP set `VDISPLAY_AGENT_URL` and route capture, sessions, and discovery through the broker — no per-app portal prompts or direct DRM access from adapters.

```bash
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay

# terminal 1 — broker (localhost)
vdisplay-agent serve
# or: vdisplay agent serve

# terminal 2 — clients
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent health
vdisplay monitors                    # 3 monitors in ~50 ms via agent /outputs
dsl2vdisplay -c 'MONITORS'
rest2vdisplay serve --port 8216 --agent-url $VDISPLAY_AGENT_URL
mcp2vdisplay serve                   # tool: vdisplay_agent_status
```

| Env var | Role |
|---------|------|
| `VDISPLAY_AGENT_URL` | Client → broker URL |
| `VDISPLAY_AGENT_TOKEN` | Optional Bearer auth |
| `VDISPLAY_CAPTURE_ALLOW_PORTAL` | Opt-in portal screenshot (agent only) |

**Wayland host capture:** start ScreenCast once in the agent (`POST /session/screencast/start`), then use normal screenshot commands. See [docs/agent-broker.md](docs/agent-broker.md) and [examples/agent-broker](examples/agent-broker/).

Virtual display screenshots work without portal. DRM/fbdev capture requires `video` group on some setups.

Full reference: [docs/agent-broker.md](docs/agent-broker.md) · [packages/vdisplay-agent](packages/vdisplay-agent/)

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

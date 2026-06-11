# CLI reference

Command index. Full examples and platform notes live in [guides/](../guides/) and the legacy [README.md](../../README.md) (being trimmed).

Install: `pip install -e ".[pillow,dev]"` · Broker: [guides/agent-broker.md](../guides/agent-broker.md)

## Discovery

| Command | Description |
|---------|-------------|
| `vdisplay all` | Monitors + windows + adopted |
| `vdisplay monitors` | Connected displays |
| `vdisplay windows` | Application windows (XWayland on Wayland hosts) |
| `vdisplay info` | Platform capabilities |
| `vdisplay diagnose` | DISPLAY / dependency diagnostics |
| `vdisplay capabilities` | Feature flags |

Window filters: `--app`, `--class`, `--pid`, `--min-width`, `--min-height`, `--apps-only`

## Capture & sessions

| Command | Description |
|---------|-------------|
| `vdisplay screenshot -o PATH` | Capture frame |
| `vdisplay virtual start` | Start Xvfb session |
| `vdisplay mirror start` | Mirror monitor output |
| `vdisplay relay adopt-window` | Move window off-screen |
| `vdisplay relay release-window` | Restore window |
| `vdisplay agent screencast start` | Wayland portal screencast (via broker) |

Screenshot options: `--source`, `--monitor`, `--display`, `--prefer-mirror`

## Control

| Command | Description |
|---------|-------------|
| `vdisplay diagnose control` | Backend readiness + routing explain |
| `vdisplay control list` | List controls (AT-SPI / browser / terminal) |
| `vdisplay control find` | Find by selector |
| `vdisplay control click` | Invoke / click |
| `vdisplay control focus` | Focus control |
| `vdisplay control set-value` | Type / paste value |
| `vdisplay control browser-open` | Open Playwright session |

Common flags: `--backend auto|atspi|browser|terminal|vision|x11`, `--verify`, `--screenshot-verify`, `--map`, `--target`, `--scope`

Session audit: `--session`, `--session-id` (root flags — see [session-report.md](../guides/session-report.md))

## Session recording

```bash
vdisplay --session --session-id demo control click --role button --name OK --verify
# → .vdisplay/<ts>__demo/README.md with routing + verify per step
```

## Map (GUI Map Pack)

| Command | Description |
|---------|-------------|
| `vdisplay map build` | OCR → map JSON (+ optional md/svg) |
| `vdisplay map show` | Inspect map elements |
| `vdisplay map diff` | Compare map vs live OCR |
| `vdisplay map refresh` | Update bounds from live capture |

Guide: [guides/gui-map-pack.md](../guides/gui-map-pack.md)

## Agent subcommands

| Command | Description |
|---------|-------------|
| `vdisplay-agent serve` | Start broker |
| `vdisplay agent serve` | Alias |
| `vdisplay agent preflight` | Agent + portal + keeper readiness check |
| `vdisplay agent health` | Broker health via HTTP |
| `vdisplay agent screencast start` | Start keeper + portal screencast (All Screens) |
| `vdisplay agent screencast start --force` | Bypass cooldown / refresh stale session |
| `vdisplay agent screencast start --single-monitor` | Single-monitor portal picker |
| `vdisplay agent screencast stop` | Stop screencast session |
| `vdisplay agent screencast status` | Active session + streams + keeper PID |
| `vdisplay agent screencast probe --source DP-1` | Test keeper capture for monitor |
| `vdisplay agent screencast probe --via-agent` | Probe through agent `/capture/frame` |
| `vdisplay agent screencast clear-cooldown` | Reset screencast start cooldown |

## App registry

| Command | Description |
|---------|-------------|
| `vdisplay app list` | IDE/app registry (cursor, pycharm, vscode, …) |
| `vdisplay app show <id>` | Show app variants and map targets |
| `vdisplay app open <id> [--variant default-xwayland]` | Launch registered app |

## Automation

| Command | Description |
|---------|-------------|
| `vdisplay auto list` | List planfile automation tasks |
| `vdisplay auto once` | Run next pending task |
| `vdisplay auto run` | Run task loop |

Example: [examples/dev-workflow](../examples/dev-workflow/) · Guide: [guides/gnome-wayland-screencast.md](../guides/gnome-wayland-screencast.md)

## DSL equivalent

```bash
dsl2vdisplay -c 'MONITORS DISPLAY :0'
dsl2vdisplay -c 'WINDOWS DISPLAY :0 APPS_ONLY true'
```

See [dsl.md](dsl.md)

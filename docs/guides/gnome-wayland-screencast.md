# Guide: GNOME Wayland multi-monitor screencast

**Question:** How do I capture and automate on a GNOME Wayland desktop with 3 monitors (DP-1, DP-2, HDMI-1)?

Related: [agent-broker.md](agent-broker.md) · [wayland-control.md](wayland-control.md) · [troubleshooting.md](../troubleshooting.md)

## Architecture (keeper + agent)

On GNOME Wayland, portal ScreenCast consent must live in a **GUI session process**. vdisplay splits capture into two parts:

| Component | Role |
|-----------|------|
| **`vdisplay-agent serve`** | Local REST broker on `127.0.0.1:8765` — routes screenshot, control, sessions |
| **screencast keeper** | Subprocess spawned by CLI in your GNOME terminal — holds portal session + PipeWire FD |
| **`POST /session/screencast/adopt`** | Agent adopts keeper state (session path, node IDs, socket path) |
| **Keeper socket** | `$XDG_RUNTIME_DIR/vdisplay-screencast.sock` — agent delegates capture here |

The agent **must not** call `OpenPipeWireRemote` directly (GNOME returns `Invalid session`). Capture goes through the keeper IPC socket.

State files:

- `$XDG_RUNTIME_DIR/vdisplay-screencast-keeper.json` — keeper PID, streams, session path
- `$XDG_RUNTIME_DIR/vdisplay-screencast.sock` — capture requests
- `~/.cache/vdisplay/agent-tasks.db` — task persistence (screencast:active)

## Two-terminal workflow

Both terminals must be in the **same GNOME session** (not SSH without X/Wayland forwarding).

```bash
# Terminal 1 — leave running
cd ~/github/wronai/vdisplay
source .venv/bin/activate
export PYTHONPATH=src:packages/vdisplay-agent/src
vdisplay-agent serve
```

```bash
# Terminal 2
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export PYTHONPATH=src:packages/vdisplay-agent/src

vdisplay agent preflight                    # agent + portal + keeper readiness
vdisplay agent screencast start --force       # portal picker → choose All Screens
vdisplay agent screencast probe --source DP-1 # validate keeper capture
vdisplay screenshot -o /tmp/dp1.png --source DP-1
```

### When to restart screencast

Run `vdisplay agent screencast start --force` again after:

- Agent restart (`Ctrl+C` on Terminal 1)
- Reboot or portal session timeout
- Keeper crash (`keeper_pid` dead in status)
- Wrong monitor content in PNG (stale stream mapping)

While agent + keeper stay up, repeat screenshots freely:

```bash
vdisplay screenshot -o /tmp/dp1.png --source DP-1
vdisplay screenshot -o /tmp/dp2.png --source DP-2
vdisplay screenshot -o /tmp/hdmi1.png --source HDMI-1
```

## Monitor ↔ portal stream mapping

Portal streams use **logical coordinates** (often half of xrandr pixel geometry). vdisplay matches monitors to streams by position + orientation, not by stream index order.

Example layout (nvidia dev workstation):

| Monitor | xrandr geometry | Rotation | Portal stream | Region (logical) | PNG size |
|---------|-----------------|----------|---------------|------------------|----------|
| **DP-1** | 4096×2560 @ (0,1304) | normal | index 0, id `"2"` | `[0,652] 2048×1280` | 2048×1280 |
| **HDMI-1** | 4096×2560 @ (0,3864) | normal | index 1, id `"1"` | `[0,1932] 2048×1280` | 2048×1280 |
| **DP-2** (primary) | 4320×7680 @ (4096,0) | left 90° | index 2, id `"0"` | `[2048,0] 2160×3840` | 2160×3840 portrait |

Verify mapping before building GUI maps:

```bash
vdisplay agent screencast status | jq '.streams[] | {node_id, position: .properties.position, size: .properties.size}'
vdisplay agent screencast probe --source DP-1
vdisplay agent screencast probe --source DP-2
vdisplay agent screencast probe --source HDMI-1
vdisplay monitors | jq '.monitors[] | {name, geometry, rotation, nl}'
```

Implementation: `src/vdisplay/capture/screencast_stream_matching.py`

## Discovery commands

```bash
vdisplay monitors                          # xrandr + NL summaries
vdisplay windows --apps-only               # XWayland only (Toolbox, etc.)
vdisplay agent screencast status           # keeper + streams
vdisplay app list                          # IDE registry (cursor, pycharm, …)
vdisplay all                               # monitors + windows + relay state
```

Native Wayland apps (Cursor, Firefox, GNOME Terminal) **do not** appear in `vdisplay windows`. Use screencast + vision/map for those.

## Automation (planfile)

Dev workflow for this machine:

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export PYTHONPATH=src:packages/vdisplay-agent/src

# Agent must be running first (Terminal 1)
bash examples/dev-workflow/run-dev-automation.sh
# or run tasks individually:
vdisplay auto list --project . --planfile examples/dev-workflow/planfile.yaml
vdisplay auto once --project . --planfile examples/dev-workflow/planfile.yaml
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `VDISPLAY_AGENT_URL` | — | Broker URL (required for host capture) |
| `VDISPLAY_SCREENCAST_MULTIPLE` | `1` | Multi-stream portal session (All Screens) |
| `VDISPLAY_SCREENCAST_GNOME_FALLBACK` | `1` | Portal screenshot + crop when PipeWire gst fails |
| `VDISPLAY_KEEPER_CAPTURE_TIMEOUT_S` | `130` | Keeper IPC timeout for slow captures |
| `VDISPLAY_SCREENCAST_LOCAL_START_COOLDOWN_S` | — | Cooldown between screencast starts; `--force` bypasses |
| `VDISPLAY_SCREENCAST_RECOVERY_COOLDOWN_S` | — | Auto-recovery cooldown after failed capture |
| `VDISPLAY_AGENT_DB` | `~/.cache/vdisplay/agent-tasks.db` | Task store path |

Full list: [reference/env.md](../reference/env.md)

## Troubleshooting quick reference

| Symptom | Fix |
|---------|-----|
| `vdisplay-agent unreachable` | Start Terminal 1: `vdisplay-agent serve` |
| Black / blank PNG | `vdisplay agent screencast start --force` |
| Wrong monitor in PNG | `pkill -f screencast_keeper; vdisplay agent screencast start --force` |
| `POST /capture/frame` 400/500 | Check `vdisplay agent screencast status`; restart keeper |
| Shutdown crash `file is not a database` | Remove corrupt DB: `file ~/.cache/vdisplay/agent-tasks.db` must say SQLite; restart agent |
| PyCharm / Cursor not in windows | Expected — use `--source DP-N` screenshot + map |

Details: [troubleshooting.md](../troubleshooting.md)

## Developing vdisplay on this PC

Use vdisplay to observe and test the desktop you develop on:

1. **Preflight** — `vdisplay agent preflight`
2. **Capture regression** — `examples/dev-workflow/run-dev-automation.sh`
3. **Map build** — `vdisplay map build --monitor DP-2 --crop-bounds …` (after probe confirms stream)
4. **Control** — `vdisplay control click --map maps/… --target …` (ydotool + vision)
5. **Web console** — `http://127.0.0.1:8765/web` (live tiles per monitor)

Example: [examples/dev-workflow](../../examples/dev-workflow/)

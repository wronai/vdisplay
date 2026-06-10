# Installation

Back to [documentation index](index.md) · [start-here.md](start-here.md)

## Python package

```bash
pip install vdisplay

# recommended on Linux (faster PNG encoding)
pip install "vdisplay[pillow]"

# from source — install core + adapters together (editable)
git clone https://github.com/wronai/vdisplay.git
cd vdisplay
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
```

Requires **Python ≥ 3.10**.

## Linux system dependencies (v0.1)

| Tool | Used by | Debian/Ubuntu |
|------|---------|---------------|
| `Xvfb` | virtual display | `xvfb` |
| `xwd` | screenshots | `x11-apps` |
| `xrandr` | mirror mode | `x11-xserver-utils` |
| `xdotool` | relay + input | `xdotool` |
| `scrot` | screenshots (multi-monitor fallback) | `scrot` |
| `python3-dbus`, `python3-gi` | portal ScreenCast (Wayland) | `python3-dbus`, `python3-gi` |
| `ffmpeg` | PipeWire frame capture | `ffmpeg` (with PipeWire enabled) |

```bash
sudo apt install xvfb x11-apps x11-utils x11-xserver-utils xdotool scrot
sudo apt install python3-dbus python3-gi ffmpeg
```

`Pillow` is optional — vdisplay includes a pure-Python PNG fallback when Pillow is not installed.

## Verify installation

```bash
vdisplay all
vdisplay monitors
vdisplay windows --apps-only
pytest tests/ -v   # when installed from source with [dev]
```

## Control layer and agent

For desktop hosts where multiple apps (CLI, REST, MCP, Koru) share one capture/runtime:

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay

vdisplay-agent serve
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent health
dsl2vdisplay -c 'MONITORS'
```

Try the runnable demo: [examples/agent-broker](../examples/agent-broker/)

Optional systemd user service: [packaging/systemd/vdisplay-agent.user.service](../packaging/systemd/vdisplay-agent.user.service)

See [agent-broker.md](agent-broker.md), [architecture.md](architecture.md).

## Platform support

| Platform | virtual | mirror | relay | host capture (Wayland) |
|----------|---------|--------|-------|-------------------------|
| Linux / X11 | Full | Full | Full | DRM/X11 providers |
| Linux / Wayland | Full | Full | Full | Agent + ScreenCast |
| Windows | Planned | Planned | Planned | Planned |
| macOS | Planned | Best-effort | Best-effort | Planned |

See [README.md — Limitations](../README.md#limitations) and [troubleshooting.md](troubleshooting.md).

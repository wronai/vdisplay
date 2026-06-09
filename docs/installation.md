# Installation

Back to [documentation index](index.md) · [README.md](../README.md)

## Python package

```bash
pip install vdisplay

# recommended on Linux (faster PNG encoding)
pip install "vdisplay[pillow]"

# from source
git clone https://github.com/wronai/vdisplay.git
cd vdisplay
pip install -e ".[pillow,dev]"
```

Requires **Python ≥ 3.10**.

## Linux system dependencies (v0.1)

| Tool | Used by | Debian/Ubuntu |
|------|---------|---------------|
| `Xvfb` | virtual display | `xvfb` |
| `xwd` | screenshots | `x11-apps` |
| `xrandr` | mirror mode | `x11-xserver-utils` |
| `xdotool` | relay + input | `xdotool` |

```bash
sudo apt install xvfb x11-apps x11-utils x11-xserver-utils xdotool
```

`Pillow` is optional — vdisplay includes a pure-Python PNG fallback when Pillow is not installed.

## Verify installation

```bash
vdisplay info
pytest tests/ -v   # when installed from source with [dev]
```

## Platform support

| Platform | virtual | mirror | relay |
|----------|---------|--------|-------|
| Linux / X11 | Full | Full | Full |
| Windows | Planned | Planned | Planned |
| macOS | Planned | Best-effort | Best-effort |

See [README.md — Limitations](../README.md#limitations).

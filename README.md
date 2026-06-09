# vdisplay


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.1-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.15-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-1.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.1500 (1 commits)
- 👤 **Human dev:** ~$100 (1.0h @ $100/h, 30min dedup)

Generated on 2026-06-09 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---



Cross-platform **virtual display orchestration API** for Python.

One unified API, multiple OS backends with different capabilities.

## Modes

| Mode | Purpose | Isolation | Screenshot | Window move |
|------|---------|-----------|------------|-------------|
| `virtual` | Private Xvfb session for agents | Yes | Yes | No (use `launch()`) |
| `mirror` | Duplicate existing display output | No | Yes | N/A |
| `relay` | Move window within same X11 session | Partial | No | Yes |

## Requirements (Linux v0.1)

- `Xvfb` — virtual display
- `xwd` — screen capture
- `xrandr` — mirror configuration
- `xdotool` — window relay and input
- `Pillow` (optional) — faster PNG encoding; pure-Python PNG fallback included

```bash
sudo apt install xvfb x11-utils xdotool
pip install "vdisplay[pillow]"
```

## Python API

```python
from vdisplay import VirtualDisplaySession, MirrorSession, WindowRelaySession

# Virtual isolated display
vd = VirtualDisplaySession.create(width=1920, height=1080)
vd.start()
vd.launch(["xterm"])
png = vd.screenshot_bytes()
vd.save_screenshot("screen.png")
vd.stop()

# Mirror existing desktop (same session, no isolation)
m = MirrorSession.create(source="primary", target="HDMI-1")
m.start()
frame = m.screenshot_bytes()
m.pointer.move(400, 300)
m.pointer.click()
m.stop()

# Relay window off-screen and restore (same X server only)
r = WindowRelaySession.create()
r.start()
r.adopt_window(match_title="Firefox")
r.release_window(match_title="Firefox")
r.stop()
```

## CLI

```bash
vdisplay info
vdisplay virtual start --width 1920 --height 1080 --display :99
vdisplay virtual screenshot -o screen.png --display :99
vdisplay mirror start --source primary --target HDMI-1 -o mirror.png
vdisplay relay adopt-window --title Firefox
vdisplay relay release-window --title Firefox
```

## Limitations

- Existing windows on `DISPLAY=:0` **cannot** move into Xvfb `:99` — different X servers.
- Use `VirtualDisplaySession.launch()` for apps on the virtual display.
- Use `WindowRelaySession` to hide/show windows on the current session.
- `mirror` controls the same desktop through a duplicated output, not an isolated copy.
- Windows/macOS backends are planned; Linux/X11 is fully supported in v0.1.

## Development

```bash
pip install -e ".[pillow]"
pytest tests/ -v
```


## License

Licensed under Apache-2.0.

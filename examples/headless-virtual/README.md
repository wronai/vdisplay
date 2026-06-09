# Headless virtual display

Fully isolated Xvfb session inside Docker — no host display required.

- Docs: [docs/examples.md](../../docs/examples.md)
- Docker guide: [docs/docker-guide.md](../../docs/docker-guide.md)

## Run

```bash
cd examples/headless-virtual
docker compose up --build
```

Screenshot is saved to `output/screen.png`.

Does not require `vdisplay-agent` — runs in-process inside the container. For desktop hosts with multiple clients, see [agent-broker](../agent-broker/).

## What it does

1. Starts `VirtualDisplaySession` on `DISPLAY=:99`
2. Captures a PNG screenshot
3. Writes result to `/output/screen.png` (mounted volume)

## Python equivalent

```python
from vdisplay import VirtualDisplaySession

vd = VirtualDisplaySession.create(width=1280, height=720, display=":99")
vd.start()
vd.save_screenshot("screen.png")
vd.stop()
```

See [run_virtual.py](run_virtual.py).

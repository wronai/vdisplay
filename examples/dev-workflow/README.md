# Dev workflow — develop vdisplay using vdisplay on this PC

Automated smoke test for the **GNOME Wayland 3-monitor** setup (DP-1, DP-2, HDMI-1).

## PL — rozwój vdisplay przez interfejs PC

Ten komputer (nvidia, GNOME Wayland, 3 monitory) jest docelową maszyną dev. vdisplay obserwuje pulpit przez broker + keeper screencast, a planfile uruchamia regresję capture i testy.

```bash
# Terminal 1 — broker (ta sama sesja GNOME)
export PYTHONPATH=src:packages/vdisplay-agent/src
vdisplay-agent serve

# Terminal 2 — automatyzacja dev
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export PYTHONPATH=src:packages/vdisplay-agent/src
bash examples/dev-workflow/run-dev-automation.sh
```

Dokumentacja: [docs/guides/gnome-wayland-screencast.md](../../docs/guides/gnome-wayland-screencast.md)

## Prerequisites

```bash
cd ~/github/wronai/vdisplay
source .venv/bin/activate
pip install -e ".[pillow,dev,auto]" -e "packages/vdisplay-agent[serve]"
```

## Run

```bash
# Terminal 1 — broker (same GNOME session)
export PYTHONPATH=src:packages/vdisplay-agent/src
vdisplay-agent serve

# Terminal 2 — automation
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export PYTHONPATH=src:packages/vdisplay-agent/src
bash examples/dev-workflow/run-dev-automation.sh
```

The script checks agent health, ensures screencast is ready, then runs all tasks in `planfile.yaml`:

- preflight, screencast status, monitors, windows, app list
- probe + screenshot for DP-1, DP-2, HDMI-1
- agent health via HTTP API

Output PNGs: `/tmp/vdisplay-dev-dp1.png`, `dp2`, `hdmi1`.

## Manual commands

```bash
vdisplay auto --project . --planfile examples/dev-workflow/planfile.yaml list
vdisplay auto --project . --planfile examples/dev-workflow/planfile.yaml once
vdisplay auto --project . --planfile examples/dev-workflow/planfile.yaml run --max 3
```

## Documentation

Full guide: [docs/guides/gnome-wayland-screencast.md](../../docs/guides/gnome-wayland-screencast.md)

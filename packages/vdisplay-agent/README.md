# vdisplay-agent

Localhost broker for vdisplay — sessions, discovery, and capture on the host.

Clients set `VDISPLAY_AGENT_URL` and never touch DRM, portal, or X11 capture directly. The agent handles Wayland screencast (via xdg-desktop-portal + keeper daemon for persistent "All Screens" sessions), multi-monitor source selection, and AT-SPI/UI control.

## Key Features (recent)

- **Keeper-managed screencast**: Use `vdisplay agent screencast start --force` to create a persistent portal session (GUI consent once, then delegated via unix socket to avoid "Invalid session"/AccessDenied on multi-stream "All Screens").
- **Specific monitor capture**: `vdisplay screenshot --source DP-1` (or HDMI-1 etc.) uses stream matching to select the correct PipeWire stream from the "All Screens" capture. Region metadata now correctly reflects the assigned stream (fix for mismatch with tall/rotated monitors).
- **Delegation for reliability**: Capture requests go to the keeper process (which owns the fd) instead of the agent proxy. Supports fallback to index 0 + client-side crop for complex layouts.
- **Status & probe**: `vdisplay agent screencast status` and `probe --source DP-1` report keeper_managed, streams with positions/sizes, tried_indices for fallbacks.
- **App registry & control**: Launch registered apps (Cursor, PyCharm, VSCode, Zed, Windsurf, VSCodium) with rich selectors for chat/AI panels. Control via AT-SPI (list/find/click/focus/set-value) or vision. Browser sessions via Playwright.
- **Multi-monitor aware**: Works with rotated (90°), offset, mixed-DPI setups (e.g. DP-2 tall primary, DP-1/HDMI-1 landscape). Capture uses portal streams + xrandr for correct cropping.

## Install

```bash
pip install -e "packages/vdisplay-agent[serve]"
```

## Run

```bash
vdisplay-agent serve
# default http://127.0.0.1:8765

vdisplay agent serve   # same, via main vdisplay CLI
```

**For reliable desktop capture/control (multi-monitor):**
```bash
# Terminal 1 (agent + keeper)
export PYTHONPATH=src:packages/vdisplay-agent/src
export VDISPLAY_ATSPI_TIMEOUT_S=30   # for robust AT-SPI on complex desktops
vdisplay-agent serve

# Terminal 2 (client)
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export PYTHONPATH=src:packages/vdisplay-agent/src

vdisplay agent screencast start --force   # one-time GUI "All Screens" consent
vdisplay agent screencast status
vdisplay agent screencast probe --source DP-1
vdisplay screenshot -o /tmp/dp1.png --source DP-1
vdisplay windows --apps-only
vdisplay app open cursor   # or pycharm, code, zed, etc.
vdisplay control list
vdisplay control find --role entry --text-contains "Chat"
```

## Client env

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
export VDISPLAY_AGENT_TOKEN=...   # optional
```

## Endpoints

See [docs/agent-broker.md](../../docs/agent-broker.md) for the full HTTP API, capture notes, adapter examples, and systemd user unit (`packaging/systemd/vdisplay-agent.user.service`).

**Web console:** [docs/guides/web-console.md](../../docs/guides/web-console.md) — open `http://127.0.0.1:8765/web` for multi-monitor preview and automation controls.

Quick test:

```bash
curl -s http://127.0.0.1:8765/health
curl -s http://127.0.0.1:8765/outputs | jq .monitor_count
```

## Developing vdisplay using vdisplay (self-hosting the dev loop)

Use the PC GUI via vdisplay to develop vdisplay itself:
- Observe: `vdisplay monitors`, `screenshot --source DP-1`, `windows`, `observe`, `control list`.
- Automate: `vdisplay app open cursor` (or code), `control find/click/set-value` on chat or editor, `screenshot` to verify.
- Run tests/automation: launch terminal/IDE, run `pytest tests/test_portal_screencast.py -q`, build, etc.
- Edit docs/code: open in Cursor/VSCode via app open + control to focus/edit (or direct + verify via screenshot/NL).

See history of fixes for keeper delegation, stream matching, region metadata, AT-SPI robustness, and Wayland limitations.

For full automation (planfiles, DSL, koru integration) see the main koru docs and `vdisplay auto`, `control`, `nlp`.

## Limitations & Tips

- Wayland: x11/windows shows only XWayland + helpers. Use `--source` capture + vision/img2nl for native apps. AT-SPI can timeout on complex desktops (use `VDISPLAY_ATSPI_TIMEOUT_S=30`, lower `--max-depth` for list).
- Keeper: Restart with `--force` if streams stale. Probe to verify per-source assignment.
- Control: Prefers AT-SPI; falls back to vision for Wayland chat (see app registry selectors for Cursor/PyCharm/etc.).
- Multi-monitor: "All Screens" via keeper gives virtual streams; matching + crop handles DP-1 etc. correctly now.

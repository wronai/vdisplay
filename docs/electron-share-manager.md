# Electron Share Manager

`packages/vdisplay-electron-share` is an optional Electron manager for GNOME
Wayland capture. It is designed for automation workflows where each agent
targets one concrete application window.

This is the single Electron implementation in the repository. Browser-bridge
push mode (`/capture/ingest`) is implemented in this same package, not as a
second app under `examples/`.

Package README: [../packages/vdisplay-electron-share/README.md](../packages/vdisplay-electron-share/README.md).  
Packages overview: [../packages/README.md](../packages/README.md).  
Main README: [../README.md](../README.md).

## Why it exists

The existing Python PipeWire keeper can start a portal session, but GNOME
permissions may still prevent frame delivery. The current recommended path is
`vdisplay services up`: it starts `vdisplay-agent`, starts the Electron manager
for tray/status/preview UI, and opens the agent browser bridge in
Chrome/Chromium. Browser bridge frames are pushed to `/capture/ingest` and are
served by the agent before any PipeWire fallback.

This does not bypass Wayland security: the user still chooses the shared
window/screen in the browser's screen-share dialog.

## UI modes

Full mode is the default. It opens a manager window optimized for 1920x1080,
capped to the current work area. It shows target label, status, controls,
display/window lists, and preview.

Compact mode is always on top and sized around 20% of a FullHD workspace,
showing only a live preview and small controls. This is meant to stay visible
while automation runs.

The tray menu can show the manager, switch compact/full mode, toggle
always-on-top, open the browser bridge, or quit.

## Recommended one-command stack

```bash
cd ~/github/wronai/vdisplay
source .venv/bin/activate

vdisplay services up --install \
  --instance jetbrains \
  --target jetbrains \
  --source HDMI-1 \
  --open-browser-bridge
```

Then, in the browser bridge tab:

1. Click `Share screen`.
2. Select the IDE monitor.
3. Keep the tab open.

Check readiness:

```bash
vdisplay services status --source HDMI-1
vdisplay screenshot -o /tmp/ide.png --source HDMI-1
```

Stop manager and portal state:

```bash
vdisplay services down --port 8799
```

## HTTP API

Default URL: `http://127.0.0.1:8799`

- `GET /health`: status payload
- `GET /status`: same as health
- `GET /displays`: Electron display list
- `GET /sources`: monitor/window source list
- `GET /frame.png`: latest shared PNG
- `GET /web`: browser preview page
- `GET /window/full`: switch to full manager and show window
- `GET /window/compact`: switch to compact preview and show window
- `GET /window/tray`: hide window to tray
- `GET /window/show`: restore window
- `GET /quit`: stop this manager instance

`vdisplay` can use this API when `VDISPLAY_ELECTRON_SHARE_URL` is set.
The recommended `services up` path instead routes screenshots through
`vdisplay-agent` and browser bridge frames.

If `VDISPLAY_AGENT_URL` is set, the process that needs
`VDISPLAY_ELECTRON_SHARE_URL` is `vdisplay-agent`, because the agent performs
the capture. If the agent is not running, direct local CLI capture can be used
by unsetting `VDISPLAY_AGENT_URL`.

When `VDISPLAY_ELECTRON_AGENT_URL` or `VDISPLAY_AGENT_URL` is set for the
Electron process, the manager also uses the push bridge:
`/session/browser-bridge/register`, `/session/browser-bridge/heartbeat`, and
`/capture/ingest`. `vdisplay-agent` then serves fresh frames directly from its
TTL store before falling back to PipeWire/keeper.

On this GNOME Wayland/NVIDIA class of setup, Electron's own renderer
`getDisplayMedia` and `desktopCapturer` can fail or hang. In that case the
Electron manager still provides UI, tray, display/window metadata and status,
while the Chrome/Chromium browser bridge provides the actual frames.

Ingested frames include source metadata when available: Electron display id,
display label, source id/name, display bounds, frame width/height and scale
factor. This lets downstream clients distinguish multiple manager instances and
prepare monitor/window crop logic without relying only on a PNG filename.

## Multiple targets

Run one manager per target app/window. Each instance needs a unique port.

```bash
vdisplay services up --install --instance pycharm --target "PyCharm chat" --source HDMI-1 --port 8799 --open-browser-bridge
vdisplay services up --instance cursor --target "Cursor" --source DP-1 --port 8800 --open-browser-bridge
```

Then route each automation process to the correct broker:

```bash
VDISPLAY_AGENT_URL=http://127.0.0.1:8766 vdisplay screenshot -o /tmp/pycharm.png --source HDMI-1
VDISPLAY_AGENT_URL=http://127.0.0.1:8766 vdisplay screenshot -o /tmp/cursor.png --source DP-1
```

Manage one instance without touching the tray:

```bash
vdisplay electron-share status --port 8799
vdisplay electron-share window full --port 8799
vdisplay electron-share window tray --port 8799
vdisplay electron-share stop --port 8799
```

## Limitations

On Wayland, the user must still approve screen sharing. Neither Electron nor
vdisplay can click the portal Share button or grant Screen Recording
permissions by itself.

On Linux/PipeWire, Chromium/Electron may expose a single chosen stream rather
than independent per-monitor streams. For multi-monitor workflows, choose All
Screens and let `vdisplay` crop the selected monitor from the composite frame.

## CLI

```bash
vdisplay services up --install --instance pycharm --target "PyCharm chat" --source HDMI-1 --open-browser-bridge
vdisplay electron-share install
vdisplay electron-share up --install --instance pycharm --target "PyCharm chat" --port 8799
vdisplay electron-share status --port 8799
vdisplay electron-share window full --port 8799
vdisplay electron-share stop --port 8799
vdisplay electron-share build --install
vdisplay electron-share path
```

`services up --install --open-browser-bridge` is the one-command first run for
automation. `electron-share up --install` launches only the manager in the
background; `electron-share start --install` is foreground/debug mode.
`build --install` installs npm dependencies and runs the Electron package build.

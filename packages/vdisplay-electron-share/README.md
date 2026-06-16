# vdisplay-electron-share

Small Electron share manager/tray UI for GNOME Wayland automation.

Full solution guide: [../../docs/electron-share-manager.md](../../docs/electron-share-manager.md).

This package is the canonical Electron implementation for vdisplay. It supports
both pull broker mode (`GET /frame.png`) and push bridge mode
(`/capture/ingest` into `vdisplay-agent`).

It provides the manager window, tray, display/window lists, logs, and local HTTP
control API. On GNOME Wayland systems where Electron capture is unreliable, use
the agent browser bridge as the actual frame source.

The default window mode is the full manager, optimized for a FullHD workspace.
It can be reduced to a compact always-on-top preview, hidden to tray, or opened
as a browser bridge/web view.

## Run

Recommended one-command automation stack:

```bash
cd ~/github/wronai/vdisplay
source .venv/bin/activate

vdisplay services up --install \
  --instance jetbrains \
  --target jetbrains \
  --source HDMI-1 \
  --open-browser-bridge
```

In the opened browser bridge tab, click `Share screen`, select the IDE monitor,
and keep the tab open. `vdisplay-agent` receives frames through
`POST /capture/ingest`.

Direct manager-only run:

```bash
vdisplay electron-share start --install \
  --instance pycharm \
  --target "PyCharm chat" \
  --source HDMI-1 \
  --port 8799
```

Direct run from the Electron app directory:

```bash
cd ~/github/wronai/vdisplay/packages/vdisplay-electron-share
npm install
npm start
```

The start script unsets `ELECTRON_RUN_AS_NODE`; if you launch the built binary
directly from an environment that has this variable, unset it first.

In the Electron window use `Browser bridge` for the agent-hosted Chrome bridge.
`Share target`/Electron capture can still be used where the Electron runtime
supports it, but on GNOME Wayland/NVIDIA it may return no stream or time out.

## Use from vdisplay

```bash
cd ~/github/wronai/vdisplay
source .venv/bin/activate
export VDISPLAY_ELECTRON_SHARE_URL=http://127.0.0.1:8799

vdisplay screenshot -o /tmp/test-hdmi1.png --source HDMI-1
```

The direct Electron provider is opt-in. If `VDISPLAY_ELECTRON_SHARE_URL` and
`VDISPLAY_ELECTRON_SHARE=1` are unset, `vdisplay` uses the existing capture
pipeline. The recommended browser bridge path uses `VDISPLAY_AGENT_URL` and
does not require direct `VDISPLAY_ELECTRON_SHARE_URL` for screenshots.

If `VDISPLAY_AGENT_URL` is set, the agent process performs the capture. In that
case start the agent with the same Electron URL:

```bash
VDISPLAY_AGENT_URL=http://127.0.0.1:8766 \
VDISPLAY_ELECTRON_SHARE_URL=http://127.0.0.1:8799 \
vdisplay-agent serve
```

For direct local CLI capture without the agent, unset `VDISPLAY_AGENT_URL`.

## Notes

On Wayland this does not bypass the portal. The user still must approve screen
sharing. Electron helps because GNOME sees one stable application identity, and
the browser/WebRTC capture path can be more reliable than a Python PipeWire
pipeline.

## Manager controls

- `Share target`: opens the browser/system picker.
- `Compact 20%`: small always-on-top preview for watching whether automation is
  doing anything.
- `Full manager`: expands to up to 1920x1080 or the current work area.
- `Tray`: hides the window while keeping capture and HTTP alive.
- `Browser bridge`: opens the agent browser bridge page for frame ingest.
- `Always on top`: enabled by default; can be changed in the manager or tray.

Closing the window hides it to tray by default. Set
`VDISPLAY_ELECTRON_CLOSE_QUITS=1` if close should quit the process.

## Multiple instances

Run one instance per automation target. Use a unique port and instance name:

```bash
vdisplay services up --instance pycharm --target "PyCharm chat" --source HDMI-1 --port 8799 --open-browser-bridge
vdisplay services up --instance chrome --target "Chrome" --source DP-1 --port 8800 --open-browser-bridge
```

Point each automation process at the right broker:

```bash
VDISPLAY_AGENT_URL=http://127.0.0.1:8766 vdisplay screenshot -o /tmp/pycharm.png --source HDMI-1
VDISPLAY_AGENT_URL=http://127.0.0.1:8766 vdisplay screenshot -o /tmp/chrome.png --source DP-1
```

## Environment

- `VDISPLAY_ELECTRON_SHARE_HOST`: default `127.0.0.1`
- `VDISPLAY_ELECTRON_SHARE_PORT`: default `8799`
- `VDISPLAY_ELECTRON_SHARE_INSTANCE`: display name for tray/web/status
- `VDISPLAY_ELECTRON_TARGET_LABEL`: initial target label
- `VDISPLAY_ELECTRON_BRIDGE_SOURCE`: source name registered in `vdisplay-agent`, default `HDMI-1`
- `VDISPLAY_ELECTRON_AGENT_URL`: agent URL for push bridge; falls back to `VDISPLAY_AGENT_URL`
- `VDISPLAY_ELECTRON_BRIDGE_PUSH=0`: disable push bridge to agent
- `VDISPLAY_ELECTRON_DISABLE_GPU=0`: keep GPU acceleration enabled (disabled by default for NVIDIA/Wayland stability)
- `VDISPLAY_ELECTRON_OZONE_PLATFORM`: Chromium Ozone platform, default `wayland` on Wayland sessions
- `VDISPLAY_ELECTRON_MAIN_CAPTURE_FALLBACK=0`: disable Electron `desktopCapturer` fallback on non-Wayland sessions; Wayland forces the fallback because this Electron runtime does not expose a usable renderer `getDisplayMedia`
- Linux enables Chromium `WebRTCPipeWireCapturer` automatically so `getDisplayMedia` can use the GNOME/PipeWire Screen Share portal.
- `VDISPLAY_ELECTRON_NO_SANDBOX=0`: keep Chromium sandbox enabled
- `VDISPLAY_ELECTRON_ALWAYS_ON_TOP=0`: disable default always-on-top
- `VDISPLAY_ELECTRON_SHARE_MODE=full`: start expanded
- `VDISPLAY_ELECTRON_CLOSE_QUITS=1`: make window close quit instead of tray-hide

## CLI

```bash
vdisplay services up --install --instance pycharm --target "PyCharm chat" --source HDMI-1 --open-browser-bridge
vdisplay electron-share install
vdisplay electron-share start --install --instance pycharm --target "PyCharm chat" --source HDMI-1 --port 8799
vdisplay electron-share status --port 8799
vdisplay electron-share window full --port 8799
vdisplay electron-share window tray --port 8799
vdisplay electron-share stop --port 8799
vdisplay electron-share build --install
vdisplay electron-share path
```

`services up --install --open-browser-bridge` is the recommended first command
for automation. `electron-share start --install` only launches the manager.
`build --install` installs npm dependencies if needed and runs
`electron-builder`.

## Local HTTP manager API

- `GET /status`: capture, window, bridge and display status.
- `GET /sources`: available monitor/window sources.
- `GET /window/full`: show and switch to full manager mode.
- `GET /window/compact`: show and switch to compact preview mode.
- `GET /window/tray`: hide the window to tray.
- `GET /window/show`: restore the manager window.
- `GET /quit`: stop this manager instance.

When `VDISPLAY_ELECTRON_AGENT_URL` or `VDISPLAY_AGENT_URL` is set, the manager
registers a browser bridge in `vdisplay-agent`, sends heartbeats every 2s, and
pushes PNG frames to `/capture/ingest`.

Frame ingest includes display/source metadata when Electron can provide it:
display id/label, source id/name, display bounds, frame size and scale factor.

# Vision-only automation on Linux Wayland

> **Navigation:** Task guide [guides/wayland-control.md](guides/wayland-control.md) · Map workflow [guides/gui-map-pack.md](guides/gui-map-pack.md) · Env vars [reference/env.md](reference/env.md)

Back to [documentation index](index.md) · [GUI Map Pack](../examples/control-plane/gui-map-pack.md)

For apps without a usable accessibility tree (PyCharm native Wayland, canvas, game surfaces), vdisplay uses profile **`vision_only_surface`**: screencast capture + OCR/map bounds + ydotool pointer injection.

## Backend eligibility

| Backend | Wayland host | Role |
|---------|--------------|------|
| `map` / direct bounds | yes | **Primary** — click/set-value from stored coordinates |
| `vision` (OCR) | yes | find by anchor/token; verify after action |
| `ydotool` | yes | pointer + paste (typing often blocked on GNOME) |
| `atspi` | partial | only XWayland apps with `GDK_BACKEND=x11` |
| `x11` / xdotool | **no** | ineligible on `linux_wayland` |
| `uia` | **no** | Windows only |
| `ax` | **no** | macOS only |

## Workflow

```bash
export YDOTOOL_SOCKET=/tmp/.ydotool_socket
vdisplay-agent serve &
sleep 2
vdisplay agent screencast start

# build scoped map (not full monitor) — crop-bounds = x,y,width,height in screencast pixels
vdisplay control find --backend vision --text-contains "Ask" --preview --preview-output /tmp/preview.png
vdisplay map build --monitor DP-2 --crop-bounds 1507,1027,800,1200 \
  --output maps/chat.json --region-id pycharm.ai_chat

# act via map (prefer stable target id from map show, e.g. ask — not status-bar "message")
vdisplay control click --map maps/chat.json --target ask
vdisplay control set-value --map maps/chat.json --target ask --value "test" --verify

# verify with tokens
vdisplay control find --backend vision --text-contains "test"

# before stale automation
vdisplay map diff --map maps/chat.json --scope pycharm.ai_chat
vdisplay map refresh --map maps/chat.json --scope pycharm.ai_chat
```

## Verify vs action

- **Action**: always prefer `--map --target` (uses `action_bounds` / `click_point`).
- **Verify**: `identity+region` from map → `ocr_contains` / `anchor_visible` / `screenshot_diff` — never semantic tree on this profile.

## Common failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `map diff` many `missing` | full-screen OCR map, UI scrolled/changed | rebuild with `--crop-bounds`; `map refresh --scope` |
| `set-value` fail, map OK | OCR path without map | use `--map --target message` (paste path) |
| `set-value` / paste hangs | `wl-copy`/`xclip` hanging on pipe descriptors | Ensure `wl-clipboard` / `xclip` are installed. Subprocess calls are now protected with timeouts and DEVNULL redirection to avoid hangs. |
| `find --text "long-string"` miss | OCR tokenization | `--text-contains "token"` |
| capture 400 / black PNG | screencast not in agent | agent serve → screencast start (correct order) |
| click wrong monitor | rotation / index drift | `map refresh`; check `--monitor DP-2` |

## img2nl / VQL (cold path)

Screenshot enrichment via `VDISPLAY_IMG2NL=1` adds NL metadata to VQL programs. Optional image LLM (`VDISPLAY_VISION_LLM_*`) is a **cold path** for diagnosis, region description, and verify fallback — not the control hot path.

```bash
# Keep orchestration on a text model:
LLM_MODEL=openrouter/qwen/qwen3-coder-next

# Vision LLM (separate from LLM_MODEL):
VDISPLAY_VISION_LLM=openrouter/google/gemini-3.1-flash-image-preview
VDISPLAY_VISION_LLM_ENABLED=1
VDISPLAY_VISION_LLM_MODE=fallback   # off | fallback | enrich | both
OPENROUTER_API_KEY=sk-or-v1-...
```

See [img2nl VQL integration](https://github.com/wronai/img2nl/blob/main/docs/vql-integration.md).

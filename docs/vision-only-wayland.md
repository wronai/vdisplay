# Vision-only automation on Linux Wayland

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

# build scoped map (not full monitor)
vdisplay map build --monitor DP-2 --crop-bounds X,Y,W,H \
  --output maps/chat.json --region-id pycharm.ai_chat

# act via map
vdisplay control click --map maps/chat.json --target chat
vdisplay control set-value --map maps/chat.json --target message --value "test"

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
| `find --text "long-string"` miss | OCR tokenization | `--text-contains "token"` |
| capture 400 / black PNG | screencast not in agent | agent serve → screencast start (correct order) |
| click wrong monitor | rotation / index drift | `map refresh`; check `--monitor DP-2` |

## img2nl / VQL (cold path)

Screenshot enrichment via `VDISPLAY_IMG2NL=1` adds NL metadata to VQL programs. See [img2nl VQL integration](https://github.com/wronai/img2nl/blob/main/docs/vql-integration.md).

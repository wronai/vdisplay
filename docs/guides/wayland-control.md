# Guide: Wayland control

**Question:** How do I automate native Wayland apps (PyCharm, Firefox Wayland, canvas)?

## Constraints on GNOME Wayland

| Tool | Native Wayland app | XWayland app |
|------|-------------------|--------------|
| `vdisplay windows` | **Not listed** | Listed |
| AT-SPI semantic tree | Often empty / partial | Works if `GDK_BACKEND=x11` |
| xdotool / x11 backend | **Blocked** | Works |
| Portal screencast | **Yes** (via agent) | Yes |
| Vision OCR + map + ydotool | **Yes** (primary path) | Yes |

## Recommended stack (`vision_only_surface`)

1. `vdisplay-agent serve` + `screencast start`
2. Build **scoped** GUI map (`--crop-bounds`) — not full monitor
3. Act with `--map --target` (action bounds, not full-screen OCR)
4. Verify with OCR crop or map hints; optional vision LLM on fail

Full workflow: [vision-only-wayland.md](../vision-only-wayland.md) · Map details: [gui-map-pack.md](gui-map-pack.md)

## PyCharm / JetBrains

Native Wayland PyCharm is invisible to X11 window lists. Options:

**A — Vision + map (current default on Wayland)**

```bash
export YDOTOOL_SOCKET=/tmp/.ydotool_socket
vdisplay control click --map maps/chat.json --target chat
vdisplay control set-value --map maps/chat.json --target message --value "hello" --verify
```

**B — Force XWayland (better AT-SPI, worse HiDPI)**

```bash
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 pycharm
```

JetBrains on XWayland may accept paste where native Wayland ignores uinput.

## Prerequisites

```bash
export YDOTOOL_SOCKET=/tmp/.ydotool_socket   # ydotool daemon socket
vdisplay-agent serve &
vdisplay agent screencast start
```

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Black screenshot | Start screencast after agent serve |
| `find --text "long string"` misses | Use `--text-contains token` or map verify |
| `set-value ok: true` but field empty | Enable `--verify`; see [vision-fallback.md](vision-fallback.md) |
| Full-monitor map drift | Rebuild with `--crop-bounds` |

Troubleshooting: [troubleshooting.md](../troubleshooting.md)

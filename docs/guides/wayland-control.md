# Guide: Wayland control

**Question:** How do I automate native Wayland apps (PyCharm, Firefox Wayland, canvas)?

Related: [desktop-control-today.md](desktop-control-today.md) (status & gaps) · [vision-only-wayland.md](../vision-only-wayland.md) · [gui-map-pack.md](gui-map-pack.md) · [reference/env.md](../reference/env.md)

## Constraints on GNOME Wayland

| Tool | Native Wayland app | XWayland app (e.g. JetBrains Toolbox) |
|------|-------------------|----------------------------------------|
| `vdisplay windows` / `vdisplay all` | **Not listed** (X11 enumeration only) | Listed with `nl` summary |
| AT-SPI semantic tree | Often empty / partial | Works if app runs under XWayland (`GDK_BACKEND=x11`) |
| x11 / xdotool backend | **Ineligible** on `linux_wayland` | Works for listed XWayland windows |
| Portal screencast | **Yes** (via agent) | Yes |
| Vision OCR + **GUI map** + ydotool | **Yes** (primary path) | Yes |

Native Wayland PyCharm does **not** appear in `vdisplay windows`. That is expected — use **screencast + map**, not window title matching.

## Recommended stack (`vision_only_surface`)

1. `vdisplay-agent serve` + `vdisplay agent screencast start` (capture on Wayland host)
2. Build a **scoped** GUI map (`vdisplay map build --crop-bounds …`) — not full monitor OCR
3. Act with `--map --target` (uses `action_bounds` / `click_point`, not raw OCR box)
4. Verify with `--verify` (map `verify_mode` → `ocr_contains` / screenshot hybrid)

Full workflow: [vision-only-wayland.md](../vision-only-wayland.md) · Map details: [gui-map-pack.md](gui-map-pack.md)

## Quick start (map-based control)

```bash
export YDOTOOL_SOCKET=/tmp/.ydotool_socket   # ydotoold socket
# optional — allow keystrokes instead of paste-only on GNOME:
# export VDISPLAY_ALLOW_YDOTOOL_TYPING=1

vdisplay-agent serve &
sleep 2
vdisplay agent screencast start

# Inspect map targets first (ids vary per map):
vdisplay map show maps/chat.json

vdisplay control click --map maps/chat.json --target chat
vdisplay control set-value --map maps/chat.json --target message --value "hello" --verify
```

Use target ids from `map show` (e.g. `ask`, `message`, `chat`) — do not guess names from OCR labels.

## PyCharm / JetBrains

**A — Vision + map (default on Wayland host)**

Build a scoped map for the chat/editor panel, then click/set-value via `--map --target` as above.

**B — Force XWayland (better AT-SPI, worse HiDPI)**

```bash
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 pycharm
```

JetBrains on XWayland may accept paste where native Wayland ignores uinput.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `YDOTOOL_SOCKET` | ydotool daemon socket (required for pointer on Wayland) |
| `VDISPLAY_ALLOW_YDOTOOL_TYPING` | `1` — allow ydotool keystrokes (default: paste fallback) |
| `VDISPLAY_CONTROL_POINTER_SETTLE_MS` | Pause after click before type (default `50`) |
| `VDISPLAY_CONTROL_FOCUS_MS` | Pause after focus before keystrokes (default `350`) |
| `VDISPLAY_CONTROL_SETTLE_MS` | Pause before verify snapshot (default `150`) |
| `VDISPLAY_AGENT_URL` | When set, discovery/control may route via broker |

See [reference/env.md](../reference/env.md).

## Inspecting the desktop

```bash
# Human-readable window summaries (XWayland / X11 only):
vdisplay all | jq '{monitor: .monitors[]?.nl, window: .windows[]?.nl}'

# Or separately:
vdisplay monitors | jq '.monitors[].nl'
vdisplay windows --apps-only | jq '.windows[].nl'
```

If `monitors[].nl` is `null`, ensure you are on a current build (agent broker must enrich monitor NL). Windows always carry `nl`; native Wayland apps simply will not be in the list.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| `NameError: _REASON_DESKTOP_CONTEXT` on CLI start | Broken/partial `scoring.py` — use current tree; reinstall: `pip install -e .` |
| Black screenshot | Start agent, then `vdisplay agent screencast start` |
| `find --text "long string"` misses | Use `--text-contains token` or map targets |
| `set-value ok: true` but field empty | Add `--verify`; prefer map + paste path — [vision-fallback.md](vision-fallback.md) |
| Full-monitor map drift | Rebuild with `--crop-bounds`; `map diff` / `map refresh --scope` |
| Click wrong monitor | Match `--monitor DP-N` in map build to screencast geometry |
| Expect PyCharm in `vdisplay windows` | Native Wayland apps are invisible to X11 — use map path |

Troubleshooting: [troubleshooting.md](../troubleshooting.md)

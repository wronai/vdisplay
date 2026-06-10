# Guide: GUI Map Pack

**Question:** How do I build and maintain persistent click targets for vision-only apps?

## When to use a map

- App has **no usable AT-SPI tree** (PyCharm native Wayland, canvas, games).
- You need **stable coordinates** across sessions (action bounds + click points).
- Full-screen OCR on every action is too slow or noisy.

## Workflow (5 steps)

```bash
# 1) Agent + screencast
export YDOTOOL_SOCKET=/tmp/.ydotool_socket
vdisplay-agent serve & && sleep 2 && vdisplay agent screencast start

# 2) Build scoped map (prefer crop over full monitor)
vdisplay map build --monitor DP-2 \
  --crop-bounds 1200,200,800,1400 \
  --output maps/chat.json --region-id pycharm.ai_chat

# 3) Act via map targets (hot path — no full OCR)
vdisplay control click --map maps/chat.json --target chat
vdisplay control set-value --map maps/chat.json --target message --value "test" --verify

# 4) Check drift before long runs
vdisplay map diff --map maps/chat.json --scope pycharm.ai_chat

# 5) Refresh bounds when UI moved cosmetically
vdisplay map refresh --map maps/chat.json --scope pycharm.ai_chat
```

## Key concepts

| Concept | Role |
|---------|------|
| `raw_bounds` | OCR detection box |
| `action_bounds` | Safe click/type region (padded) |
| `click_point` | Center used for ydotool |
| `verify_mode` | How post-action verify runs (`ocr_contains`, `anchor_visible`, …) |
| `scope` / `region_id` | Sub-panel for diff/refresh |

## Verify vs action

- **Action:** always `--map --target` (uses stored bounds).
- **Verify:** map element `verify_mode` → OCR/anchor/screenshot — never semantic tree on this profile.

## Full spec + CLI reference

Detailed PR-26/27/28 doc with export formats and verify modes:

[examples/control-plane/gui-map-pack.md](../../examples/control-plane/gui-map-pack.md)

Platform context: [wayland-control.md](wayland-control.md) · [vision-only-wayland.md](../vision-only-wayland.md)

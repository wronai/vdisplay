# GUI Map Pack (PR-26/27/28)

Persistent vision regions and elements with **raw bounds**, **action bounds**, and **click points** — for `vision_only_surface` apps (PyCharm native Wayland, canvas, streams) where AT-SPI/x11 are unavailable.

## Prerequisites (Wayland / GNOME)

```bash
export YDOTOOL_SOCKET=/tmp/.ydotool_socket
vdisplay-agent serve & && sleep 2
vdisplay agent screencast start   # before map/control — agent capture lives in agent process
```

Order matters: starting screencast **before** `vdisplay-agent serve` kills the previous agent session.

## Build a map

**Prefer scoped OCR** — full-monitor maps (~460 elements) produce noisy diff and false missing anchors.

```bash
# 1) Full monitor (legacy — noisy)
vdisplay map build \
  --monitor DP-2 \
  --output maps/pycharm-dp2-full.json \
  --region-id pycharm.ai_chat \
  --region-label "PyCharm AI Chat"

# 2) Recommended — crop to chat panel (x,y,width,height from map show or vision preview)
vdisplay map build \
  --monitor DP-2 \
  --output maps/pycharm-chat.json \
  --region-id pycharm.ai_chat \
  --region-label "PyCharm AI Chat" \
  --crop-bounds 1200,200,800,1400 \
  --min-text-len 3 \
  --md maps/pycharm-chat.md \
  --svg maps/pycharm-chat.svg
```

| Artifact | Purpose |
|----------|---------|
| `map.json` | Source of truth for automation |
| `map.md` | Operator index (regions, elements, verify hints) |
| `map.svg` | Visual atlas (raw dashed boxes, action solid boxes, click points) |

## Scoped control (hot path)

Use stored **action bounds** and **click_point** — no full-desktop OCR on each action:

```bash
vdisplay control click --backend vision --map maps/pycharm-chat.json --target chat
vdisplay control set-value --backend vision --map maps/pycharm-chat.json --target message \
  --value "test-message-from-vdisplay"
vdisplay control find --backend vision --text-contains "message-from"   # tokens, not full string
```

On GNOME Wayland, `set-value` via map uses **ydotool-paste** (typing via uinput is often blocked).

## Element schema (map.json)

Each element records:

- `raw_bounds` — OCR detection box
- `action_bounds` — expanded target used for click/set-value (see `action_bounds.py`)
- `click_point` — center of action bounds sent to ydotool
- `identity` — `{role, name, name_prefix, anchor_text}` for verify fallback
- `verify_mode` — default `identity+region` → resolved at runtime (see below)
- `monitor`, `rotation`, `region_id`, `tile_fingerprint`

## Verify modes (`vision_only_surface`)

Actions and verify use **separate paths**. Map actions never use semantic tree verify.

| Stored `verify_mode` | Resolved at runtime | When |
|---------------------|---------------------|------|
| `identity+region` | `ocr_contains` | `set-value` with text to check |
| `identity+region` | `anchor_visible` | click/focus when `anchor_text` set |
| `identity+region` | `screenshot_diff` | fallback when no anchor/label |

Legal verify for vision-only: `screenshot`, `ocr`, `anchor_visible` — not `semantic`.

Long hyphenated strings (`test-message-from-vdisplay`) fail exact OCR — verify with **token** `text-contains` or map-region `ocr_contains`.

## Drift detection (PR-27)

```bash
vdisplay map diff --map maps/pycharm-chat.json --scope pycharm.ai_chat
# exit code 1 when drift detected

vdisplay map refresh --map maps/pycharm-chat.json --scope pycharm.ai_chat --output maps/pycharm-chat.json
vdisplay map refresh --map maps/pycharm-chat.json --add-new   # append new OCR labels
```

### Per-element status

| Status | Meaning | Action |
|--------|---------|--------|
| `ok` | anchor, bounds, fingerprint stable | none |
| `bounds` | OCR anchor found but moved > 12px | `map refresh --scope …` |
| `fingerprint` | tile hash changed at same bounds | cosmetic; refresh optional |
| `missing` | anchor not found near stored bounds | refresh or rebuild scoped map |

### Diff recommendation (PR-28)

JSON includes:

- `recommendation`: `stable` | `stable_with_cosmetic_drift` | `refresh_recommended` | `refresh_required`
- `actionable`: true when automation should not trust stale bounds
- `key_targets`: status for `chat`, `message`, `ask_anything` when present

Example interpretation (many `missing` + region fingerprint change):

```json
"recommendation": "refresh_required",
"actionable": true,
"key_targets": { "chat": "bounds", "message": "missing" }
```

→ run `map refresh --scope pycharm.ai_chat` before map-target clicks.

## Rotation (DP-2 / left)

Pointer mapping in `input/coords.py` applies rotation when monitor metadata and PNG aspect diverge — typical for rotated Wayland screencast.

## Optional: vision LLM layer (enhancer, not hot path)

For semantic diagnosis when OCR/map diff is ambiguous, use a **separate** image model (not global `LLM_MODEL`):

```bash
# orchestration / code — keep text model
LLM_MODEL=openrouter/qwen/qwen3-coder-next

# image analysis / drift summary — optional
VDISPLAY_VISION_LLM=openrouter/google/gemini-3.1-flash-image-preview
VDISPLAY_VISION_LLM_ENABLED=0   # 1 for diagnose/enrich only
```

Gemini image is for: region description, drift summary, mockups — **not** click coordinates (use map bounds + ydotool).

## See also

- [Vision preview](./vision-preview.md) — overlay debug, find crop bounds (PR-25)
- [Vision disambiguation](./vision-disambiguation.md) — index/confidence (PR-24)
- [Control plane README](./README.md) — backend matrix for Wayland

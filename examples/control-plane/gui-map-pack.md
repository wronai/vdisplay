# GUI Map Pack (PR-26)

Persistent vision regions and elements with **raw bounds**, **action bounds**, and **click points** — aligned with runtime click expansion and identity-based verify.

## Build a map

```bash
vdisplay agent screencast start
vdisplay map build \
  --monitor DP-2 \
  --output dp2-map.json \
  --md dp2-map.md \
  --svg dp2-map.svg \
  --region-id pycharm.ai_chat \
  --region-label "PyCharm AI Chat"
```

Produces:

| Artifact | Purpose |
|----------|---------|
| `map.json` | Source of truth for automation |
| `map.md` | Operator index (regions, elements, verify hints) |
| `map.svg` | Visual atlas (raw dashed boxes, action solid boxes, click points) |

## Scoped control

Use stored **action bounds** and **click_point** — no full-desktop OCR on each action:

```bash
vdisplay control find --backend vision --map dp2-map.json --scope pycharm.ai_chat
vdisplay control click --backend vision --map dp2-map.json --target ask_anything
vdisplay control set-value --backend vision --map dp2-map.json --target ask_anything --value "test"
```

## Element schema (map.json)

Each element records:

- `raw_bounds` — OCR/template detection box
- `action_bounds` — expanded target used for click/set-value (see `action_bounds.py`)
- `click_point` — center of action bounds sent to ydotool
- `identity` — `{role, name, name_prefix, anchor_text}` for verify fallback
- `monitor`, `rotation`, `region_id`, `tile_fingerprint`

## Scoped verify

When `--map --target` is used with `--verify`:

1. Semantic verify uses map `identity.name_prefix` as `verify_label` when not overridden
2. Screenshot verify compares within element `action_bounds` region
3. Identity fallback `(role, name)` matches unstable AT-SPI trees (same as `verify.py`)

## Rotation (DP-2 / left)

Pointer mapping in `input/coords.py` applies a rotation transform when monitor metadata and PNG aspect ratio diverge — typical for rotated outputs on Wayland screencast.

Capture meta should include `rotation` (map build sets this from `xrandr` when `--monitor` is passed).

## Drift detection (PR-27)

Compare a stored map against the live desktop:

```bash
vdisplay map diff --map dp2-map.json --scope pycharm.ai_chat
# exit code 1 when drift detected (bounds/fingerprint/missing)

vdisplay map refresh --map dp2-map.json --output dp2-map.json --svg dp2-map.svg
vdisplay map refresh --map dp2-map.json --add-new   # append new OCR labels
```

Drift report includes per-element status:

| Status | Meaning |
|--------|---------|
| `ok` | anchor, bounds, and fingerprint stable |
| `bounds` | OCR anchor found but moved > 12px |
| `fingerprint` | tile hash changed at same bounds |
| `missing` | anchor not found near stored bounds |

## See also

- [Vision preview](./vision-preview.md) — overlay debug (PR-25)
- [Vision disambiguation](./vision-disambiguation.md) — index/confidence (PR-24)

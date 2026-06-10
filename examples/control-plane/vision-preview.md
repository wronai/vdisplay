# Vision match preview overlay (PR-25)

Visual debug for vision control — see **all** OCR/template matches on the screencast
frame, with numbers, confidence colors, and the selected click target highlighted.

## Quick start

```bash
pip install "vdisplay[vision]"   # Pillow + tesseract + opencv

# Wayland: capture source for vision
vdisplay agent serve
vdisplay agent screencast start

# Find + write overlay PNG
vdisplay control find --backend vision --vision-anchor "Submit" \
  --preview --preview-output preview.png

# Open preview.png — green box = match that would be clicked (--index 0)
```

## CLI flags

| Flag | Purpose |
|------|---------|
| `--preview` | Render overlay; JSON includes `preview.preview_png_base64` |
| `-o` / `--preview-output PATH` | Also write PNG to disk |
| `--preview-debug` | Gray boxes for confidence-rejected matches + `debug` metadata |

Works on:

- `vdisplay control find ...`
- `vdisplay diagnose control ...` (runs vision find + attaches `preview` + `vision_find`)

## Examples

```bash
# Second "Submit" button — preview shows both boxes, #1 highlighted
vdisplay control find --backend vision --vision-anchor "Submit" \
  --index 1 --preview -o preview.png

# Spatial anchor — preview highlights spatial target (anchor index via --index)
vdisplay control find --backend vision \
  --vision-anchor "Email" --vision-anchor-rel right_of --vision-target "Submit" \
  --preview --preview-debug -o preview.png

# Extract PNG from JSON without -o
vdisplay control find --backend vision --vision-anchor "Submit" --preview \
  | jq -r '.preview.preview_png_base64' | base64 -d > preview.png
```

## JSON shape

```json
{
  "preview": {
    "preview_available": true,
    "selected_index": 1,
    "preview_path": "/tmp/preview.png",
    "preview_size_bytes": 8421,
    "matches": [
      {"index": 0, "label": "Submit", "confidence": 0.95, "selected": false, "kind": "ocr", "bounds": {...}},
      {"index": 1, "label": "Submit", "confidence": 0.88, "selected": true, "kind": "ocr", "bounds": {...}}
    ],
    "debug": {
      "raw_match_count": 3,
      "filtered_match_count": 2,
      "rejected": [{"index": 0, "label": "Submit", "confidence": 0.55, "rejected": true, ...}],
      "vision_anchor": "Submit",
      "vision_min_confidence": 0.85
    }
  }
}
```

## Overlay colors

| Color | Meaning |
|-------|---------|
| Green (thick) | Selected match (`--index` / click target) |
| Cyan | Confidence ≥ 0.90 |
| Orange | Confidence ≥ 0.75 |
| Red | Confidence < 0.75 |
| Gray `#R…` | Rejected by `--vision-min-confidence` (`--preview-debug`) |

## Agent API

```bash
curl -s -X POST http://127.0.0.1:8765/controls/find \
  -H 'content-type: application/json' \
  -d '{
    "backend": "vision",
    "vision_anchor": "Submit",
    "preview": true,
    "preview_debug": true,
    "preview_output": "/tmp/preview.png"
  }' | jq '.data.preview.preview_path'
```

## PyCharm / Wayland workflow

When AT-SPI and x11-fallback cannot see PyCharm (native Wayland Electron):

```bash
vdisplay agent serve
vdisplay agent screencast start

# See what OCR actually detects before clicking
vdisplay control find --backend vision --vision-anchor "Run" \
  --preview -o pycharm-vision-preview.png

# Tune index/confidence from the overlay
vdisplay control click --backend vision --vision-anchor "Run" \
  --index 0 --vision-min-confidence 0.80 --verify
```

## Module map

| File | Role |
|------|------|
| `src/vdisplay/control/vision_preview.py` | Overlay render + JSON payload |
| `src/vdisplay/control/vision_disambiguate.py` | Confidence/index (PR-24) |
| `src/vdisplay/control/providers/vision/provider.py` | `last_capture()`, debug metadata |
| `src/vdisplay/application/services/control.py` | `controls_find` / `diagnose_control` preview |

## Tests

```bash
pytest tests/test_vision_preview.py -q
```

## Related

- [PR-24 disambiguation](vision-disambiguation.md)
- [Control plane](../../docs/control-plane.md)
- [RFC 001](../../docs/rfc/001-extensibility-model.md)

# Vision control — multi-match disambiguation (PR-24)

When screenshot OCR or template matching finds **multiple** controls (duplicate labels,
repeated icons), use selector disambiguation before click/invoke.

## CLI

```bash
pip install "vdisplay[vision]"

# Click the second "Submit" button (0-based --index)
vdisplay control click --backend vision --vision-anchor "Submit" --index 1

# Require stronger template/OCR confidence (0.0–1.0)
vdisplay control click --backend vision \
  --vision-template ./templates/icon.png \
  --vision-min-confidence 0.92

# Two "Email" labels — use the lower row's adjacent Submit
vdisplay control click --backend vision \
  --vision-anchor "Email" \
  --vision-anchor-rel right_of \
  --vision-target "Submit" \
  --index 1

# Preview matches before acting
vdisplay control find --backend vision --vision-anchor "Submit" \
  | jq '.matches[] | {name, y: .bounds.y, confidence: .state.confidence, match_count: .state.match_count}'
```

## Semantics

| Input | Meaning |
|-------|---------|
| `--index 0` | First match after filtering (default) |
| `--index N` | Nth match among OCR/template hits |
| `--index N` + spatial anchor | Nth duplicate **anchor** label (`Email`, `Password`, …) |
| `--vision-min-confidence` | Drop matches below threshold; also used as template `matchTemplate` floor when set |

Default thresholds when `--vision-min-confidence` is omitted:

- **Template**: OpenCV normalized score ≥ `0.85`
- **OCR**: Tesseract per-word confidence ≥ `30` (stored as 0.0–1.0 in nodes)

## Node metadata

Vision `find()` nodes include disambiguation fields in `state`:

```json
{
  "confidence": 0.93,
  "match_count": 2,
  "selected_index": 1,
  "min_confidence": 0.85
}
```

## Python API

```python
from vdisplay.application.services import control as control_svc

result = control_svc.control_click(
    backend="vision",
    vision_anchor="Submit",
    index=1,
    vision_min_confidence=0.9,
    verify=True,
)
print(result["target"]["state"]["match_count"])
```

## Module map

| File | Role |
|------|------|
| `src/vdisplay/control/vision_disambiguate.py` | Filter/sort/pick helpers |
| `src/vdisplay/control/vision_ocr.py` | `anchor_index` for duplicate anchors |
| `src/vdisplay/control/vision_template.py` | Threshold from `vision_min_confidence` |
| `src/vdisplay/control/providers/vision/provider.py` | Applies disambiguation in find paths |

## Tests

```bash
pytest tests/test_vision_multimatch_disambiguation.py -q
```

## Related

- [PR-22 vision template/anchor](../README.md#vision-template--spatial-anchor-pr-22) — README section
- [Control plane](../docs/control-plane.md)
- [RFC 001](../docs/rfc/001-extensibility-model.md)

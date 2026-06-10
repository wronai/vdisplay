# Guide: browser control

**Question:** How do I open a browser session and click DOM elements?

## Open session first

Browser control requires an active Playwright session (`browser_open` / DSL `BROWSER_OPEN`):

```bash
vdisplay control browser-open \
  --url https://example.com \
  --session-id web-1 \
  --headed

# or DSL
dsl2vdisplay -c 'BROWSER_OPEN URL https://example.com SESSION_ID web-1 HEADLESS false'
```

## Find and act

```bash
vdisplay control list --backend browser --session-id web-1
vdisplay control click --backend browser --session-id web-1 \
  --dom-css "#submit" --verify
vdisplay control set-value --backend browser --session-id web-1 \
  --dom-css "#email" --value "user@example.com" --verify
```

## Routing

`--backend auto` ranks `browser` when selector has `dom_css`, `dom_xpath`, or `session_id` with browser kind.

Diagnostics:

```bash
vdisplay diagnose control --backend browser --session-id web-1 --dom-css "#go"
```

## Examples

- [examples/control-plane/control_demo.py](../../examples/control-plane/control_demo.py)
- [control-plane.md](../control-plane.md) — provider matrix

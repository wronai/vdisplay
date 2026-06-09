# Control plane

Back to [documentation index](index.md) · [RFC 001 — extensibility](rfc/001-extensibility-model.md)

Unified GUI control for browsers, terminals, and native desktop apps. Vision (screenshot/screencast) is used for verification and fallback — not as the primary actuation path.

## Architecture

```
Selector → Policy/Router → Provider adapter → VerifierPipeline
                ↑
         Application profile inference
```

| Layer | Module | Role |
|-------|--------|------|
| Selector | `control/selector.py` | Core + extension fields (`dom_css`, `terminal_line`, …) |
| Router | `control/router.py`, `scoring.py` | Capability-driven provider ranking |
| Registry | `control/registry.py`, `control/plugins.py` | Builtin + registered adapters |
| Providers | `control/providers/*` | AT-SPI, Playwright, terminal, X11 |
| Verify | `control/verifier.py` | Semantic, screenshot, hybrid |
| Sessions | `control/session.py` | Portable session catalog |

## Builtin providers

| `provider_id` | Surface | Session kind |
|---------------|---------|--------------|
| `atspi` | Linux desktop a11y | — |
| `browser` | Playwright DOM | `browser` (requires `browser_open` / `POST /session/browser/open`) |
| `terminal` | PTY / TUI grid | `terminal` |
| `x11` | xdotool fallback | — |

## Diagnostics

```bash
vdisplay diagnose control
# or via agent:
curl -s 'http://127.0.0.1:8765/diagnostics/control?dom_css=button' | jq .
```

Response includes:

- `control` — readiness contract (backends, deps, reasons)
- `routing` — explainable provider decision for the selector
- `application_profile` — inferred class-of-app (`web_spa`, `terminal_pty`, …)
- `extensions` — platform profile, descriptors, plugins, session kinds

## Plugin registration (PR-12)

Register adapters at runtime without modifying core:

```python
from vdisplay.control import register_control_provider, ProviderDescriptor
from vdisplay.control.capabilities import POINTER_FALLBACK

register_control_provider(
    ProviderDescriptor(
        provider_id="my-adapter",
        adapter_kind="custom",
        environments=frozenset({"desktop"}),
        session_kind=None,
        capabilities=POINTER_FALLBACK,
        base_score=60,
    ),
    lambda display=None, session_id=None: MyControlProvider(),
)
```

### Entry points (optional wheel packaging)

In your package `pyproject.toml`:

```toml
[project.entry-points."vdisplay.control_providers"]
my_adapter = "my_package.vdisplay_plugin:register"
```

Loader convention — either:

1. Callable `register(registry: ProviderRegistry) -> None`, or
2. Object with `.descriptor` and `.factory` attributes.

List registered plugins:

```bash
curl -s http://127.0.0.1:8765/control/plugins | jq .
```

## Browser sessions

```bash
curl -s -X POST http://127.0.0.1:8765/session/browser/open \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com","session_id":"web-1","headless":true}' | jq .

curl -s 'http://127.0.0.1:8765/diagnostics/control?session_id=web-1&dom_css=button' | jq .
```

DOM verify runs automatically for browser actions when `--verify` is set (mode `dom`).

## CLI / DSL

```bash
# List all accessible controls for Firefox
vdisplay control list --app firefox --backend auto

# Click a button with role "button" and name "Save"
vdisplay control click --role button --name Save --verify

# Set input value and verify change
vdisplay control set-value --role input --name "Search" --value "hello" --verify

# Diagnose control plane capabilities
vdisplay diagnose control
```

DSL verbs: `CONTROLS`, `CLICK`, `FOCUS`, `SET_VALUE`, `DIAGNOSE_CONTROL`, `TERMINAL_OPEN`, `BROWSER_OPEN`.

Open a **browser session** (canonical: `session_id`, `SessionKind.browser`) before DOM control — the browser provider is ineligible without it:

```bash
browser open --url https://example.com --session web-1
# optional: --headed, --title "...", --vendor firefox
```

`--session-id` is accepted as an alias. DOM verify mode applies after the session is open.

## Routing semantics (PR-15)

Four axes — do not conflate:

| Axis | Type | Example |
|------|------|---------|
| Host | `HostEnvironmentKind` | `linux_wayland`, `linux_x11` |
| Target | `EnvironmentKind` | `browser`, `terminal`, `desktop` |
| Session | `SessionKind` | `browser`, `terminal` (open before DOM/TUI control) |
| Verify | `VerifyStrategy` | `dom` (browser), `text` (terminal) |

`diagnose control` and routing decisions expose `routing_semantics` with host constraints (e.g. xdotool blocked on `linux_wayland`).


## Controlling JetBrains IDEs / Java Swing Apps

Java Swing applications, including JetBrains IDEs like PyCharm, can be controlled in two ways depending on the backend provider used.

### 1. ATSPI Control (Accessible Widget Tree)

To allow the `atspi` provider to inspect PyCharm's UI components (buttons, text inputs, trees) and interact with them semantically:

1. **Install the Java ATK Wrapper** on the host machine to bridge Java accessibility events to the system D-Bus/AT-SPI bus:
   ```bash
   sudo apt install libatk-wrapper-java
   ```
2. **Enable screen reader support** in PyCharm by starting it with the VM option:
   `-Dide.support.screenreaders.enabled=true`
   *Alternatively, add `ide.support.screenreaders.enabled=true` directly to PyCharm's custom VM options file (`~/.config/JetBrains/PyCharm2026.1/pycharm64.vmoptions`).*

### 2. X11 Pointer/Keyboard Injection Fallback

If semantic AT-SPI control is not fully configured, the `x11-fallback` provider can adopt PyCharm's window and inject clicks/types at coordinates.

1. **Force X11/XWayland Mode**: On Wayland sessions (such as Ubuntu 22.04+), JetBrains IDEs run natively under Wayland by default. This makes their windows invisible to X11-based tools (`xdotool`, `x11-fallback`, `adopt-window`). Force X11 mode by unsetting Wayland-related variables:
   ```bash
   env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 /snap/bin/pycharm-professional
   ```
2. **Adopt and Relay**: Once running in X11 mode, adopt PyCharm's window using the relay system:
   ```bash
   vdisplay relay adopt-window --app "JetBrains"
   ```

## Related

- [Agent broker — control + task APIs](agent-broker.md)
- [RFC 001 — full extensibility model](rfc/001-extensibility-model.md)
- [API contract](api-contract.md)


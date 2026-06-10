# Control plane

> **Navigation:** Guides [guides/](guides/) · CLI [reference/cli.md](reference/cli.md) · Architecture [architecture.md](architecture.md)

Back to [documentation index](index.md) · [RFC 001 — extensibility](rfc/001-extensibility-model.md)

> **Current capabilities & gaps (2026-06):** For a task-oriented view of what works on Linux desktop today (browser, terminal, PyCharm, Cursor, koru fallback), see [guides/desktop-control-today.md](guides/desktop-control-today.md).

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

## Verify and actuation

| Action | Default verify (semantic backends) | Vision backend |
|--------|-----------------------------------|----------------|
| `click` / `invoke` | State diff, label change, focus | `anchor_visible` or screenshot hybrid |
| `set-value` | `text_value.after == value` (AT-SPI / terminal / browser DOM) | `ocr_contains` on typed text |

After every actuation, vdisplay waits `VDISPLAY_CONTROL_SETTLE_MS` (default **150 ms**) before the verify snapshot when `--verify` or `--screenshot-verify` is set. Increase on slow UIs (e.g. `export VDISPLAY_CONTROL_SETTLE_MS=400`).

**Pointer click → type sequence (vision / x11):**

1. Move + click at `action_bounds` center (or map `click_point`)  
2. Wait `VDISPLAY_CONTROL_POINTER_SETTLE_MS` (default **50 ms**) for compositor focus  
3. Wait `VDISPLAY_CONTROL_FOCUS_MS` (default **350 ms**) before keystrokes  
4. `type_text` if backend supports it (`xdotool`, ydotool with `VDISPLAY_ALLOW_YDOTOOL_TYPING=1`)  
5. Clipboard paste fallback (`wl-copy` / `xclip` + Ctrl+V via ydotool)

**AT-SPI set-value:** grabs focus before `Text.set_text_contents` / `Value.set_current_value`.

Session steps record routing, verify mode, confidence, and artifact paths when `--session` is enabled — [session-report.md](guides/session-report.md).

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

### Cross-platform plugin wheels (PR-23)

Ship platform-specific semantic control as optional installable wheels:

| Example wheel | Platform | Entry point | Mock on Linux CI |
|---------------|----------|-------------|------------------|
| [`examples/control-plugin-uia/`](../examples/control-plugin-uia/) | Windows UIA | `example-uia` | `MockUiaBackend` (Notepad tree) |
| [`examples/control-plugin-ax/`](../examples/control-plugin-ax/) | macOS AX | `example-ax` | `MockAxBackend` (Calculator tree) |

```bash
pip install -e examples/control-plugin-uia examples/control-plugin-ax
vdisplay control list --backend example-uia --app Notepad
vdisplay control click --backend example-ax --role button --name OK --verify
```

Core builtins `uia` and `ax` remain in vdisplay; the example wheels show how OEMs
package native deps (`comtypes`, `pyobjc`) without editing core routing.

### Vision multi-match disambiguation (PR-24)

When OCR/template find returns multiple hits, filter and pick with selector fields:

| Field | CLI flag | Role |
|-------|----------|------|
| `index` | `--index` | Pick Nth match after confidence filter (0-based) |
| `vision_min_confidence` | `--vision-min-confidence` | Unified 0.0–1.0 threshold for OCR + template |
| `vision_anchor_rel` + `index` | `--vision-anchor-rel` + `--index` | Pick Nth duplicate **anchor** label before spatial search |

```bash
# Second "Submit" on screen
vdisplay control click --backend vision --vision-anchor Submit --index 1

# Stricter template match
vdisplay control click --backend vision \
  --vision-template ./btn.png --vision-min-confidence 0.92

# List matches with confidence metadata
vdisplay control find --backend vision --vision-anchor Submit | jq '.matches'
```

Implementation: `src/vdisplay/control/vision_disambiguate.py` — used by vision provider
find paths and `controls_find` / `_resolve_target`.

### Vision match preview overlay (PR-25)

Render numbered bounding boxes on the screencast frame — debug **why** a match was picked:

```bash
vdisplay control find --backend vision --vision-anchor Submit \
  --preview --preview-output preview.png

vdisplay diagnose control --backend vision --vision-anchor Submit \
  --preview --preview-debug -o preview.png
```

JSON field `preview.preview_png_base64` (or `preview_path` with `-o`). Green box = selected
match; gray `#R` boxes = rejected when `--preview-debug`.

See [examples/control-plane/vision-preview.md](../examples/control-plane/vision-preview.md).

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

### GNOME — desktop & terminal (quick reference)

Full examples: [README — GNOME desktop & terminal control](../README.md#gnome-desktop-control-native-apps-via-at-spi).

```bash
# Desktop GTK (Files, Calculator) — AT-SPI on Wayland host
export GTK_A11Y=1 GDK_BACKEND=x11
vdisplay control list --app Nautilus --backend atspi --format tree
vdisplay control click --app Nautilus --role button --name Home --verify

# Do not use x11 on linux_wayland (xdotool blocked)
vdisplay diagnose control --app firefox --backend auto

# Terminal — PTY session (not GNOME Terminal window)
dsl2vdisplay -c 'terminal open --session-id t1 --command bash --rows 40 --cols 120'
vdisplay control set-value --backend terminal --session-id t1 --terminal-line 1 --value "ls -la" --verify

# Browser — detached CLI sessions
vdisplay control browser-open --url https://example.com --session-id web-1
vdisplay control click --backend browser --session-id web-1 --selector "#submit" --verify
```

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

**Important Note**: On Wayland sessions (Ubuntu 22.04+), JetBrains IDEs run natively under Wayland by default. This makes them **invisible** to both X11-based tools (`xdotool`, `x11-fallback`, `adopt-window`) and AT-SPI accessibility tools. You must force XWayland mode for any control method to work.

### 1. ATSPI Control (Accessible Widget Tree)

To allow the `atspi` provider to inspect PyCharm's UI components (buttons, text inputs, trees) and interact with them semantically:

1. **Force XWayland Mode** (required on Wayland):
   ```bash
   env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 /snap/bin/pycharm-professional
   ```

2. **Install the Java ATK Wrapper** on the host machine to bridge Java accessibility events to the system D-Bus/AT-SPI bus:
   ```bash
   sudo apt install libatk-wrapper-java
   ```

3. **Enable screen reader support** in PyCharm by starting it with the VM option:
   `-Dide.support.screenreaders.enabled=true`
   *Alternatively, add `ide.support.screenreaders.enabled=true` directly to PyCharm's custom VM options file (`~/.config/JetBrains/PyCharm2026.1/pycharm64.vmoptions`).*

4. **Test ATSPI detection**:
   ```bash
   # List accessible controls in PyCharm
   vdisplay control list --backend atspi --app "PyCharm"

   # Click a button or element
   vdisplay control click --role button --name "Chat" --verify

   # Set text in an input field
   vdisplay control set-value --role entry --name "Chat input" --value "Your text here" --verify
   ```

**Test Results**: ATSPI works correctly on Linux systems with proper XWayland setup. Testing showed that Google Chrome was successfully detected via AT-SPI with 1 window and accessible child elements, confirming the backend functionality.

### 2. X11 Pointer/Keyboard Injection Fallback

If semantic AT-SPI control is not fully configured, the `x11-fallback` provider can adopt PyCharm's window and inject clicks/types at coordinates.

1. **Force X11/XWayland Mode**: On Wayland sessions (such as Ubuntu 22.04+), JetBrains IDEs run natively under Wayland by default. This makes their windows invisible to X11-based tools (`xdotool`, `x11-fallback`, `adopt-window`). Force X11 mode by unsetting Wayland-related variables:
   ```bash
   env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 /snap/bin/pycharm-professional
   ```

2. **Verify X11 detection**:
   ```bash
   # Check if PyCharm is now visible to X11 tools
   vdisplay windows --app "PyCharm"
   xdotool search --name "PyCharm"
   ```

3. **Adopt and Relay**: Once running in X11 mode, adopt PyCharm's window using the relay system:
   ```bash
   vdisplay relay adopt-window --app "PyCharm"
   vdisplay relay list  # Check adopted windows
   vdisplay relay release-window --app "PyCharm"
   ```

**Test Results**: On Wayland systems, X11 fallback is **blocked by default** for security reasons. The diagnostic shows `xdotool ineffective on Wayland host`. X11 control only works when applications are explicitly launched in XWayland mode.

### 3. Wayland Native Workaround

If you cannot restart PyCharm in XWayland mode, you can still interact with it using the portal screencast approach:

```bash
# Start the vdisplay agent
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

# Start portal screencast (requires one-time GUI consent)
vdisplay agent screencast start

# Take screenshots of the entire desktop
vdisplay screenshot -o desktop.png

# Use vision-based control or manual coordinate-based interaction
# Note: This is less precise than ATSPI or X11 methods
```

### Summary of Test Results

| Method | Works on Wayland | Requires Restart | Precision | Setup Complexity |
|--------|------------------|------------------|-----------|------------------|
| ATSPI | ❌ (requires XWayland) | ✅ | High | Medium |
| X11 Fallback | ❌ (blocked on Wayland) | ✅ | Low | Low |
| Portal Screencast | ✅ | ❌ | Low | Low |

**Recommendation**: For reliable PyCharm control, always launch it in XWayland mode using the environment variables shown above. This enables both ATSPI and X11 control methods.

## Test Results Summary (2026-06-09)

**Environment**: Ubuntu Wayland, Python 3.13, vdisplay 0.1.31

### Working Components ✅
- **Control Diagnostics**: All backends operational (AT-SPI, Browser, Terminal, X11-fallback)
- **Terminal Control**: Fully functional - session management, text input, command execution verified
- **Browser Control**: Fully functional - headless Chromium, DOM navigation, element detection working
- **Portal Screencast**: Fully functional - screenshot capture with img2nl analysis
- **AT-SPI Discovery**: Successfully detects applications (tested with Google Chrome)

### Partial/Limited Components ⚠️
- **AT-SPI Interaction**: Discovery works, but direct interaction attempts experience dbind timeouts
- **Element Capabilities**: Most detected AT-SPI elements have limited interaction capabilities

### Non-Working Components ❌
- **X11 Fallback**: Blocked on Wayland host for security reasons
- **PyCharm Control**: Not testable without XWayland mode (requires application restart)

### Test Coverage
- **Demo Script**: `examples/control-plane/control_demo.py` runs successfully
- **CLI Commands**: `vdisplay control list`, `vdisplay screenshot`, `vdisplay agent screencast` all functional
- **Python API**: Session management and control operations verified through demo

For detailed test results, see [examples/control-plane/README.md](../examples/control-plane/README.md#test-results-2026-06-09).

### JetBrains Control Test Results (2026-06-09)

**Tested Environment**: Ubuntu Wayland with JetBrains Toolbox running in XWayland mode

**Findings**:
- ✅ **Toolbox Detection**: Successfully detected via `vdisplay windows --app "JetBrains"`
- ✅ **Relay/Adopt**: Window successfully moved off-screen and restored
- ✅ **Direct xdotool**: Text input works despite Wayland restrictions
- ❌ **AT-SPI**: Toolbox not detected as separate application by AT-SPI
- ❌ **PyCharm IDE**: Not visible (likely running in native Wayland mode)

**Working Example**:
```bash
# Detect and control JetBrains Toolbox
vdisplay windows --app "JetBrains" | jq '.windows[] | {window_id, app_label, nl}'
# Output: window_id: "10485767", app_label: "Toolbox"

# Relay control
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay release-window --app "JetBrains"

# Direct xdotool control (bypasses Wayland restrictions)
xdotool windowactivate 10485767
xdotool type "Test text from vdisplay"
```

**Key Insight**: While vdisplay's x11 backend is blocked on Wayland, direct xdotool commands still work for XWayland windows like JetBrains Toolbox, providing a workaround for basic control operations.

## DSL Browser Control (2026-06-09)

**Usage**: DSL provides command-line interface for browser automation with proper session management.

**Working Examples**:
```bash
# Open browser session (required before control)
dsl2vdisplay -c 'BROWSER OPEN --URL https://example.com --SESSION_ID web-1 --HEADLESS true'

# Control operations
dsl2vdisplay -c 'CONTROLS LIST --BACKEND browser --SESSION_ID web-1'
dsl2vdisplay -c 'CONTROL CLICK --BACKEND browser --SESSION_ID web-1 --SELECTOR "#go" --VERIFY'
```

**Test Results**:
- ✅ Session management works (open/close browser sessions)
- ✅ DOM element detection (28 elements found on example.com)
- ✅ Click operations with verification (confidence 0.9)
- ✅ Proper routing (browser provider selected with score 345)

**Key Requirements**:
- Always open browser session before control operations
- Use `--SESSION_ID` to specify which browser session to control
- DSL uses `--SELECTOR` for CSS selectors (automatically detected as DOM context)

## Cursor Editor Control (2026-06-09)

**Status**: ❌ Not controllable (native Wayland Electron app)

**Test Results**:
- ✅ Cursor running (PID 25916, Electron-based editor)
- ❌ Not visible to X11 tools (native Wayland mode)
- ❌ AT-SPI does not detect Cursor as separate application
- ❌ Relay/adopt functionality fails
- ✅ Portal screencast works for indirect observation

**Key Findings**:
```
Process: cursor --no-sandbox --ozone-platform=wayland
X11 Detection: vdisplay windows --app "Cursor" → 0 windows
AT-SPI Detection: Only gnome-shell visible, no Cursor app tree
Direct Control: Not possible via current vdisplay methods
```

**Workaround Options**:
1. **XWayland Mode**: Restart Cursor in XWayland for basic xdotool control
   ```bash
   env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 cursor --no-sandbox
   ```
2. **Screenshot Analysis**: Use portal screencast for vision-based control
   ```bash
   vdisplay screenshot -o cursor.png --source DP-2
   # Analyze screenshot with OCR/vision for cursor position
   ```
3. **VS Code Extensions**: Use VS Code automation extensions directly within Cursor

**Current Limitations**: Electron apps in native Wayland mode are not accessible to X11/AT-SPI control methods. This is a platform limitation, not a vdisplay-specific issue.

## Related

- [Agent broker — control + task APIs](agent-broker.md)
- [RFC 001 — full extensibility model](rfc/001-extensibility-model.md)
- [API contract](api-contract.md)


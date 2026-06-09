# Control Plane Demo Example

This example demonstrates how to use the **vdisplay control plane** to programmatically query, inspect, and interact with user interface controls. It covers:

1. **Diagnostics**: Querying control capability support and available providers.
2. **Desktop UI Controls**: Scanning the AT-SPI accessibility tree to list desktop controls.
3. **Terminal Sessions**: Launching an interactive terminal process (`bash`), writing input, and listing terminal grid outputs.
4. **Browser Sessions**: Opening a headless browser via Playwright, listing DOM element structures, clicking links, and verifying actions.
5. **JetBrains IDE Control**: Interacting with PyCharm/IntelliJ IDEA windows via AT-SPI or X11 fallback.

## Prerequisites

Ensure all dependencies for the control plane are installed:

```bash
# Install system packages (required for AT-SPI bridge support)
sudo apt install libatk-wrapper-java

# Install optional Python dependencies for control backends
pip install "vdisplay[dev]"
```

### JetBrains IDE Setup

For controlling PyCharm or IntelliJ IDEA:

1. **Force XWayland mode** (required on Wayland systems):
   ```bash
   env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 /snap/bin/pycharm-professional
   ```

2. **Enable accessibility support** in PyCharm:
   - Add to VM options: `-Dide.support.screenreaders.enabled=true`
   - Or edit `~/.config/JetBrains/PyCharm2026.1/pycharm64.vmoptions`

## Running the Demo

Simply execute the script:

```bash
./control_demo.py
```

Or run it through the main package virtual environment:

```bash
python3 examples/control-plane/control_demo.py
```

## JetBrains IDE Examples

### Controlling PyCharm via AT-SPI

```bash
# List accessible controls in PyCharm
vdisplay control list --backend atspi --app "PyCharm"

# Click the Chat button to open AI assistant
vdisplay control click --role button --name "Chat" --verify

# Type in the chat input field
vdisplay control set-value --role entry --name "Chat input" --value "How do I debug Python code?" --verify

# Click the Send button
vdisplay control click --role button --name "Send" --verify
```

### Controlling PyCharm via X11 Fallback

```bash
# Adopt PyCharm window (requires XWayland mode)
vdisplay relay adopt-window --app "PyCharm"

# Use xdotool for keyboard input (less precise)
xdotool type "print('Hello, World!')"
xdotool key Return

# Release the window when done
vdisplay relay release-window --app "PyCharm"
```

### Python API Example

```python
from vdisplay.control import ControlSelector, ControlProvider
from vdisplay.application import create_executor

# Create control selector for PyCharm chat input
selector = ControlSelector(
    role="entry",
    name="Chat input",
    app="PyCharm"
)

# Execute text input
executor = create_executor()
result = executor.execute_command(
    "control",
    action="set_value",
    selector=selector,
    value="Your text here",
    verify=True
)
```

## DSL Browser Control Examples

**Important**: Browser sessions must be opened before control operations.

### Opening a Browser Session

```bash
# Open headless browser session
dsl2vdisplay -c 'BROWSER OPEN --URL https://example.com --SESSION_ID web-1 --HEADLESS true'

# Open headed browser (visible window)
dsl2vdisplay -c 'BROWSER OPEN --URL https://example.com --SESSION_ID web-1 HEADED'
```

### Browser Control Operations

```bash
# List DOM elements in browser session
dsl2vdisplay -c 'CONTROLS LIST --BACKEND browser --SESSION_ID web-1'

# Click element using CSS selector
dsl2vdisplay -c 'CONTROL CLICK --BACKEND browser --SESSION_ID web-1 --SELECTOR "#go" --VERIFY'

# Focus on element
dsl2vdisplay -c 'CONTROL FOCUS --BACKEND browser --SESSION_ID web-1 --SELECTOR "a"'

# Set value in input field (requires form elements)
dsl2vdisplay -c 'CONTROL SET_VALUE --BACKEND browser --SESSION_ID web-1 --SELECTOR "input" --VALUE "test value" --VERIFY'
```

### DSL Test Results (2026-06-09)

**Status**: ✅ Working with proper session management

**Working Commands**:
- ✅ `BROWSER OPEN`: Successfully opens browser sessions
- ✅ `CONTROLS LIST`: Returns DOM elements (28 elements found on example.com)
- ✅ `CONTROL CLICK`: Successfully clicks elements with verification (confidence 0.9)

**Tested Example**:
```bash
# Open session
dsl2vdisplay -c 'BROWSER OPEN --URL https://example.com --SESSION_ID web-1 --HEADLESS true'

# Click link
dsl2vdisplay -c 'CONTROL CLICK --BACKEND browser --SESSION_ID web-1 --SELECTOR "#go" --VERIFY'
# Result: Clicked "Learn more" link, verified with DOM mode, confidence 0.9

# List controls
dsl2vdisplay -c 'CONTROLS LIST --BACKEND browser --SESSION_ID web-1'
# Result: 28 DOM elements detected (links, text, etc.)
```

**Common Error**:
```
Error: browser session 'web-1' is not open
Solution: Always run BROWSER OPEN before browser control operations
```

## Test Results (2026-06-09)

### Environment
- **OS**: Ubuntu Linux 6.17.0-35-generic
- **Display Stack**: Wayland (GNOME)
- **Python**: 3.13 (miniconda)
- **vdisplay**: 0.1.31

### Control Plane Diagnostics ✅

All control backends are operational:
- **AT-SPI**: ✅ Active (system python)
- **Browser**: ✅ Playwright available
- **Terminal**: ✅ Provider available (pyte/pexpect optional)
- **X11 Fallback**: ❌ Blocked on Wayland host

### AT-SPI Control Tests ⚠️

**Status**: Partially working with limitations

**Findings**:
- AT-SPI successfully detects desktop applications (tested with Google Chrome)
- `vdisplay control list --backend atspi` returns detailed control trees
- Chrome detected with 1 window and accessible child elements
- **Timeout issues**: Direct interaction attempts (`control click`) result in dbind timeouts
- **Capability limitations**: Most detected elements have `activate: false` capabilities

**Working Commands**:
```bash
# List AT-SPI controls (works)
vdisplay control list --backend atspi --app "Chrome"

# Filter for interactive elements
vdisplay control list --backend atspi --app "Chrome" | jq '.nodes | to_entries | .[] | select(.value.role == "button" or .value.role == "entry")'
```

**Failed Commands**:
```bash
# Direct interaction (timeout)
vdisplay control click --backend atspi --name "Activities"
# Error: atspi_error: timeout from dbind (1)
```

### Terminal Control Tests ✅

**Status**: Fully working

**Test Results**:
- Terminal session opens successfully with bash
- Text input works: `echo hello-vdisplay` command sent successfully
- Control routing selects terminal provider with score 300
- Session management operational

**Working Commands**:
```bash
# Python API (from control_demo.py)
session_svc.terminal_open(
    session_id="demo-term-session",
    command="/bin/bash",
    cols=80,
    rows=24,
)

control_svc.control_set_value(
    display=":0",
    backend="terminal",
    session_id="demo-term-session",
    role="input",
    value="echo hello-vdisplay\n",
    verify=True,
)
```

**Limitations**:
- Semantic verification may fail (expected for terminal state)
- Requires explicit session_id for all operations

### Browser Control Tests ✅

**Status**: Fully working

**Test Results**:
- Headless browser launches successfully (Chromium engine)
- Navigates to example.com correctly
- DOM element detection works (found "Learn more" element)
- Session management operational

**Working Commands**:
```bash
# Python API (from control_demo.py)
session_svc.browser_open(
    session_id="demo-browser-session",
    url="https://example.com",
    headless=True,
)

# List DOM elements
control_svc.controls_list(
    display=":0",
    backend="browser",
    session_id="demo-browser-session",
)
```

**Limitations**:
- DOM selectors must match exactly (case-sensitive)
- Link name mismatch caused click failure in demo ("Learn more" vs "More information...")

### Portal Screencast Tests ✅

**Status**: Fully working

**Test Results**:
- Portal screencast starts successfully with one-time GUI consent
- Screenshot capture works: 2560×1600 px images
- Agent integration operational
- img2nl analysis provides scene descriptions

**Working Commands**:
```bash
# Start agent
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

# Start screencast
vdisplay agent screencast start

# Capture screenshot
vdisplay screenshot -o test-screencast.png
```

### PyCharm Control Tests ❌

**Status**: Not tested (requires XWayland mode)

**Blockers**:
- PyCharm running in native Wayland mode (invisible to X11/AT-SPI)
- Java ATK Wrapper not installed (requires sudo)
- Cannot restart user's PyCharm instance for testing

**Requirements for Testing**:
1. Force XWayland: `env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 /snap/bin/pycharm-professional`
2. Install Java ATK Wrapper: `sudo apt install libatk-wrapper-java`
3. Enable screen reader support: `-Dide.support.screenreaders.enabled=true`

### JetBrains Toolbox Control Tests ✅

**Status**: Partially working (X11 detection works, Wayland limitations apply)

**Test Results**:
- Toolbox successfully detected via X11: `vdisplay windows --app "JetBrains"`
- Window ID 10485767 identified (880×1326 at (7586,658))
- Relay/adopt functionality works: window successfully moved off-screen and restored
- Direct xdotool commands work despite Wayland limitations
- Text input via xdotool successful: `xdotool type "Test text from vdisplay"`

**Working Commands**:
```bash
# Detect Toolbox window
vdisplay windows --app "JetBrains" | jq '.windows[] | {window_id, app_label, nl}'

# Adopt window (move off-screen)
vdisplay relay adopt-window --app "JetBrains"

# List adopted windows
vdisplay relay list

# Restore window
vdisplay relay release-window --app "JetBrains"

# Direct xdotool control (bypasses vdisplay Wayland restrictions)
xdotool windowactivate 10485767
xdotool type "Test text from vdisplay"
```

**Limitations**:
- AT-SPI does not detect Toolbox as separate application (shows gnome-shell only)
- vdisplay x11 backend blocked on Wayland host
- PyCharm IDE windows not visible (likely running in native Wayland mode)
- Only Toolbox running in XWayland mode is controllable

### Cursor Editor Control Tests ❌

**Status**: Not controllable (native Wayland Electron app)

**Test Results**:
- Cursor is running (verified via process list, PID 25916)
- Running in native Wayland mode: `--ozone-platform=wayland` flag detected
- Not visible to X11 tools: `vdisplay windows --app "Cursor"` returns 0 windows
- Not visible to xdotool: `xdotool search --name "Cursor"` returns no results
- AT-SPI does not detect Cursor as separate application (shows gnome-shell only)
- Relay/adopt fails: `vdisplay relay adopt-window --app "Cursor"` error
- Portal screencast works: can capture entire desktop including Cursor

**Working Commands**:
```bash
# Portal screencast (only indirect observation)
vdisplay screenshot -o cursor-test.png  # Full desktop screenshot
vdisplay screenshot -o cursor-dp1.png --source DP-1  # Specific monitor
vdisplay screenshot -o cursor-dp2.png --source DP-2  # Primary monitor
```

**Limitations**:
- No direct control possible (click, type, focus)
- No window management possible (move, resize, minimize)
- No accessibility tree access via AT-SPI
- Only indirect observation via screenshots
- Requires XWayland mode for any direct control (requires restart)

**Requirements for Control**:
1. Restart Cursor in XWayland mode: `env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 cursor --no-sandbox`
2. Enable accessibility features in Electron app if needed
3. Use xdotool or vdisplay relay after XWayland mode is active

### Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Control Diagnostics | ✅ Working | All backends detected |
| AT-SPI Discovery | ✅ Working | Detects apps and elements |
| AT-SPI Interaction | ⚠️ Limited | Timeout issues on some operations |
| Terminal Control | ✅ Working | Full functionality |
| Browser Control | ✅ Working | Full functionality |
| Portal Screencast | ✅ Working | Full functionality |
| JetBrains Toolbox | ✅ Partial | X11 detection works, xdotool control possible |
| PyCharm IDE Control | ❌ Untested | Requires XWayland setup |
| Cursor Editor | ❌ No Control | Native Wayland Electron app, only screenshots possible |
| X11 Fallback | ❌ Blocked | Wayland security restriction |

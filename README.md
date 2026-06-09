# vdisplay


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.9-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$5.73-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-6.1h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $5.7266 (8 commits)
- 👤 **Human dev:** ~$615 (6.1h @ $100/h, 30min dedup)

Generated on 2026-06-09 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Cross-platform **virtual display orchestration API** for Python.

One unified API, multiple OS backends with different capabilities. Monitors and windows include an **`nl`** field — a natural-language description of what they contain.

CLI, DSL, REST, MCP, and the local **vdisplay-agent** broker all route through **`application.executor`** and shared **application services** (`src/vdisplay/application/`).

## Quick start

```bash
pip install "vdisplay[pillow]"
# or from source (recommended for development):
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
```

```bash
unset DISPLAY   # optional: auto-resolves host display to :0
vdisplay all
vdisplay monitors
vdisplay windows --apps-only
```

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/index.md](docs/index.md) | Documentation hub — start here |
| [docs/installation.md](docs/installation.md) | System and Python setup |
| [docs/docker-guide.md](docs/docker-guide.md) | Running in Docker |
| [docs/examples.md](docs/examples.md) | All usage examples by environment |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common errors and fixes |
| [docs/agent-broker.md](docs/agent-broker.md) | **vdisplay-agent** — install-once broker, env vars, REST/MCP |
| [docs/architecture.md](docs/architecture.md) | CommandRequest + executor routing (local vs agent) |
| [examples/README.md](examples/README.md) | Runnable example projects |
| [packages/README.md](packages/README.md) | Control layer — DSL, MCP, REST, NL, agent |

## Examples

| Example | Mode | Host X11 | Run |
|---------|------|----------|-----|
| [headless-virtual](examples/headless-virtual/) | virtual | No | `cd examples/headless-virtual && docker compose up --build` |
| [agent-broker](examples/agent-broker/) | broker | No | `cd examples/agent-broker && ./run.sh` |
| [ci-agent](examples/ci-agent/) | virtual | No | `cd examples/ci-agent && docker compose run --rm ci-agent` |
| [dev-workspace](examples/dev-workspace/) | dev | No | `cd examples/dev-workspace && docker compose run --rm dev` |
| [host-mirror](examples/host-mirror/) | mirror | Yes | `cd examples/host-mirror && ./run.sh` |
| [host-relay](examples/host-relay/) | relay | Yes | `cd examples/host-relay && ./run.sh` |
| [run_all_examples.sh](examples/run_all_examples.sh) | mixed | varies | `./examples/run_all_examples.sh` |

Details: [docs/examples.md](docs/examples.md) · per-example READMEs in each folder above.

## List monitors, windows, and display state

Each monitor and window includes **`nl`** — a human-readable summary of what it contains.

```bash
# everything — monitors + application windows + adopted (off-screen)
vdisplay all
vdisplay all | jq '{monitors: .monitor_count, windows: .window_count, adopted: .adopted_count}'

# monitors only (xrandr) — name, geometry, rotation, primary, nl
vdisplay monitors
vdisplay monitors | jq '.monitors[] | {name, primary, nl}'

# application windows only — title, app, pid, class, nl
vdisplay windows --apps-only
vdisplay windows --app "Firefox"
vdisplay windows --class jetbrains-toolbox --pid 32977
vdisplay windows --min-width 400 --min-height 300

# platform capabilities + monitors
vdisplay info

# diagnose DISPLAY, socket, monitor count
vdisplay diagnose

# adopted (off-screen) windows — persisted in ~/.cache/vdisplay/
vdisplay relay list
```

| Command | Shows |
|---------|--------|
| `vdisplay all` | monitors + windows + adopted |
| `vdisplay monitors` | connected displays only |
| `vdisplay windows` | visible application windows only |
| `vdisplay relay list` | windows moved off-screen by relay |
| `vdisplay info` | platform capabilities |
| `vdisplay diagnose` | DISPLAY diagnostics |

`vdisplay outputs` still works but is **deprecated** — use `vdisplay all` or `vdisplay monitors`.
`vdisplay relay list-windows` is deprecated — use `vdisplay windows`.

Filter windows with `--app`, `--class`, `--pid`, `--min-width`, `--min-height`. Use `--all` (default) to include internal/helper windows; `--apps-only` excludes them.

## Desktop workflows (GNOME, multi-monitor)

Examples for a typical Linux desktop session (`DISPLAY=:0`, Wayland + XWayland). Replace monitor names (`DP-2`, `DP-1`, `HDMI-1`) with output from `vdisplay monitors`.

> **Wayland note:** vdisplay lists **XWayland** windows via `xdotool`. Native Wayland apps (Firefox Wayland, Cursor, GNOME Terminal) may not appear in `vdisplay windows` — use **portal screencast** for screenshots of the full desktop or a chosen monitor.

### JetBrains Toolbox / IDE

**⚠️ Wayland Users**: JetBrains IDEs run natively on Wayland by default and are **invisible** to X11 tools. Force XWayland mode for control:
```bash
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE DISPLAY=:0 /snap/bin/pycharm-professional
```

Toolbox usually runs on XWayland and shows up in window lists:

```bash
# find Toolbox on the primary monitor
vdisplay windows --app "JetBrains"
vdisplay windows --class jetbrains-toolbox | jq '.windows[] | {window_id, app_label, monitor_name, nl}'

# hide Toolbox off-screen (automation / clean screenshot)
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay list

# move Toolbox to another physical monitor
vdisplay relay adopt-window --app "JetBrains" --target HDMI-1
vdisplay relay release-window --app "JetBrains"

# before/after screenshots (Wayland: agent + screencast first — see below)
vdisplay agent serve                              # terminal 1
vdisplay agent screencast start                   # terminal 2 — pick monitor in portal
vdisplay relay screenshot -o before.png --source DP-2
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay screenshot -o toolbox-hidden.png --source DP-2
vdisplay relay release-window --app "JetBrains"
vdisplay relay screenshot -o after-restore.png --source DP-2
```

IntelliJ / PyCharm (when launched via Toolbox, often XWayland):

```bash
# Find PyCharm windows
vdisplay windows --app "PyCharm"
vdisplay windows --class idea | jq '.windows[] | {title, pid, nl}'
vdisplay relay adopt-window --title "vdisplay"   # partial title match

# Control PyCharm via AT-SPI (requires Java ATK Wrapper + screen reader support)
# Install: sudo apt install libatk-wrapper-java
# VM option: -Dide.support.screenreaders.enabled=true
vdisplay control list --backend atspi --app "PyCharm"
vdisplay control click --role button --name "Chat" --verify
vdisplay control set-value --role entry --name "Chat input" --value "Your text" --verify
```

**Note**: For comprehensive test results of control plane functionality, see [examples/control-plane/README.md](examples/control-plane/README.md#test-results-2026-06-09). Testing shows Terminal and Browser control working fully, AT-SPI discovery working but with interaction limitations on Wayland. JetBrains Toolbox successfully controlled via xdotool workaround despite Wayland restrictions. DSL browser control requires session opening before operations. Cursor editor not controllable in native Wayland mode (only screenshot observation possible).
```

### Firefox (XWayland)

If Firefox runs on XWayland (`about:support` → Window Protocol: X11):

```bash
vdisplay windows --app "Firefox"
vdisplay windows --class firefox | jq '.windows[] | {window_id, title, nl}'
vdisplay relay adopt-window --app "Firefox"
vdisplay relay adopt-window --title "Mozilla Firefox"
vdisplay relay release-window --app "Firefox"
```

Native Wayland Firefox is **not** listed by `vdisplay windows` — capture the monitor instead:

```bash
vdisplay agent screencast start
vdisplay screenshot -o firefox-monitor.png --source DP-2
```

### Chromium / Chrome / Edge

Same as Firefox — only visible when running on XWayland:

```bash
vdisplay windows --class google-chrome
vdisplay windows --class chromium
vdisplay windows --app "Chrome" | jq '.windows[].nl'
```

### GNOME Terminal, Cursor, native Wayland apps

These often **do not** appear in `vdisplay windows`. Workflow:

```bash
# 1) see which monitors exist and what XWayland apps are visible
vdisplay all | jq '{monitors: [.monitors[].name], x11_windows: [.windows[].app_label]}'

# 2) screenshot the monitor where the app is shown
vdisplay agent screencast start
vdisplay screenshot -o terminal.png --source DP-1
vdisplay screenshot -o primary.png --source primary
```

### LibreOffice, GIMP, Steam (XWayland)

```bash
vdisplay windows --app "LibreOffice"
vdisplay windows --class soffice
vdisplay windows --app "GIMP"
vdisplay relay adopt-window --class steam
vdisplay relay release-window --class steam
```

### VS Code / Cursor / Slack / Discord (Electron)

Electron apps often expose a partial AT-SPI tree when launched with accessibility enabled. Window listing still depends on XWayland:

```bash
# list visible Electron windows (when on XWayland)
vdisplay windows --app "Cursor"
vdisplay windows --app "code"
vdisplay windows --class slack | jq '.windows[] | {title, app_label, nl}'

# semantic control — AT-SPI backend (GTK_A11Y / Java ATK wrapper may be required for some builds)
export GTK_A11Y=1
vdisplay diagnose control
vdisplay control list --app "Cursor" --backend atspi --max-depth 4
vdisplay control click --app "Cursor" --role button --name "Run" --verify

# if native Wayland build — window not in list; capture monitor instead
vdisplay agent screencast start
vdisplay screenshot -o cursor.png --source DP-2
```

### Thunderbird, Nautilus, GNOME Calculator

```bash
vdisplay windows --app "Thunderbird"
vdisplay windows --class org.gnome.Nautilus
vdisplay windows --class org.gnome.Calculator

# hide file manager off-screen before a clean desktop shot
vdisplay relay adopt-window --class org.gnome.Nautilus
vdisplay relay screenshot -o desk-clean.png --source DP-2
vdisplay relay release-window --class org.gnome.Nautilus
```

### Spotify, OBS, Blender (mixed X11 / Wayland)

```bash
vdisplay windows --app "Spotify"
vdisplay windows --class obs
vdisplay windows --class blender | jq '.windows[] | {title, monitor_name, nl}'

# move Blender to second monitor (XWayland only)
vdisplay relay adopt-window --class blender --target HDMI-1
```

### Messaging & video calls (Telegram, Signal, Zoom, Teams)

Electron and Qt wrappers — window listing depends on XWayland; capture the monitor for native Wayland builds:

```bash
vdisplay windows --app "Telegram"
vdisplay windows --class signal
vdisplay windows --app "zoom"
vdisplay windows --class teams | jq '.windows[] | {title, app_label, nl}'

# hide chat window before desktop recording
vdisplay relay adopt-window --app "Telegram"
vdisplay agent screencast start
vdisplay screenshot -o desk-no-telegram.png --source DP-2
vdisplay relay release-window --app "Telegram"

# Zoom/Teams on Wayland — usually not in window list; full-monitor capture
vdisplay screenshot -o meeting.png --source primary
```

### Developer tools (DBeaver, Android Studio, Docker Desktop, Wireshark)

Java/Electron apps — often XWayland; Java ATK helps AT-SPI:

```bash
vdisplay windows --app "DBeaver"
vdisplay windows --class android-studio
vdisplay windows --class Docker
vdisplay windows --class wireshark | jq '.windows[] | {title, pid, nl}'

# semantic click in DBeaver SQL editor toolbar (AT-SPI)
export GTK_A11Y=1
vdisplay control list --app DBeaver --backend atspi --max-depth 5
vdisplay control click --app DBeaver --role button --name Execute --verify

# hide Android Studio emulator window off-screen during screenshot
vdisplay relay adopt-window --title "Android Emulator"
vdisplay relay screenshot -o ci-screen.png --source DP-2
vdisplay relay release-window --title "Android Emulator"
```

### Media players & creative (VLC, Audacity, Krita, Inkscape)

GTK/Qt apps — GTK tools benefit from `GDK_BACKEND=x11` on Wayland for AT-SPI:

```bash
vdisplay windows --class vlc
vdisplay windows --app "Audacity"
vdisplay windows --class krita
vdisplay windows --class inkscape

# pause VLC via AT-SPI (when tree is exposed)
GDK_BACKEND=x11 GTK_A11Y=1 vdisplay control click --app vlc --role button --name Pause --verify

# move Inkscape to second monitor before export
vdisplay relay adopt-window --class inkscape --target HDMI-1
vdisplay relay release-window --class inkscape
```

### Terminals beyond GNOME Terminal (Tilix, Alacritty, kitty)

Native Wayland terminals rarely appear in `vdisplay windows`. Prefer a **terminal session** or monitor capture:

```bash
# if running on XWayland
vdisplay windows --class Tilix
vdisplay windows --class Alacritty
vdisplay windows --class kitty

# reliable TUI control — open PTY instead of chasing desktop window
dsl2vdisplay -c 'terminal open --session-id dev-1 --command bash'
vdisplay control list --backend terminal --session-id dev-1
vdisplay control click --backend terminal --session-id dev-1 --terminal-line 1 --terminal-col 0

# screenshot where the terminal is visible (Wayland)
vdisplay agent screencast start
vdisplay screenshot -o alacritty.png --source DP-1
```

### System apps (Settings, Software, Files, Calculator, virt-manager)

GNOME shell apps are often native Wayland — use monitor capture or AT-SPI with X11 backend:

```bash
vdisplay windows --class gnome-control-center    # Settings (XWayland only)
vdisplay windows --class org.gnome.Software
vdisplay windows --class virt-manager
vdisplay windows --class VirtualBox

# virt-manager VM window on second monitor
vdisplay relay adopt-window --class virt-manager --target DP-1

# Settings on Wayland — not listed; capture primary
vdisplay screenshot -o settings.png --source primary
```

### Password managers & notes (Bitwarden, Obsidian, 1Password)

Electron apps — partial AT-SPI when accessibility is enabled:

```bash
vdisplay windows --app "Bitwarden"
vdisplay windows --class obsidian
vdisplay windows --app "1Password"

export GTK_A11Y=1
vdisplay control list --app obsidian --backend atspi --format tree
vdisplay control click --app Bitwarden --role button --name Unlock --verify
```

### AT-SPI control on native GTK apps (GNOME Wayland)

On Wayland, force GTK apps onto X11 for a reliable accessibility tree:

```bash
export DISPLAY=:0
export GDK_BACKEND=x11
export GTK_A11Y=1
export NO_AT_BRIDGE=0

# demo fixture used in tests — or any GTK3 app you start the same way
./tests/fixtures/run_gtk_demo.sh &
sleep 2

vdisplay control list --app vdisplay-gtk-demo --backend atspi
vdisplay control click --app vdisplay-gtk-demo --role button --name Increment --verify
vdisplay control set-value --app vdisplay-gtk-demo --role input --index 0 --value hello --verify
```

### Browser sessions (Playwright DOM — any site)

Open a **browser session** first, then control via DOM selectors (not the desktop Firefox window):

```bash
# DSL
dsl2vdisplay -c 'browser open --url https://example.com --session web-1'
dsl2vdisplay -c 'browser open --url https://example.com --session web-ff --vendor firefox --headed'

# CLI equivalent via agent (terminal 1: vdisplay agent serve)
vdisplay agent browser-open --url https://example.com --session-id web-1

# control the open session
vdisplay control list --backend browser --session-id web-1
vdisplay control click --backend browser --session-id web-1 --selector "#submit" --verify
vdisplay diagnose control --selector "#go" --session-id web-1   # routing + profile inference
```

### GNOME desktop control (native apps via AT-SPI)

On **GNOME Wayland**, prefer `atspi` over `x11` — `xdotool` is blocked (`linux_wayland`). Enable accessibility where needed:

```bash
# one-time / per-shell — GTK/Java/Electron trees
export GTK_A11Y=1
export QT_ACCESSIBILITY=1
export JAVA_TOOL_OPTIONS="-Djavax.accessibility.assistive_technologies=org.GNOME.Accessibility.AtkWrapper"

# diagnose before clicking — shows eligible providers on your host
vdisplay diagnose control --app firefox --role button --name Reload --backend auto
```

#### Files (Nautilus)

```bash
# launch on X11 stack for a fuller tree on Wayland host
GDK_BACKEND=x11 GTK_A11Y=1 nautilus ~ &
sleep 2

vdisplay control list --app Nautilus --backend atspi --format tree
vdisplay control click --app Nautilus --role button --name Home --verify
vdisplay control click --app Nautilus --role menu item --name Documents --verify
```

#### Calculator

```bash
GDK_BACKEND=x11 GTK_A11Y=1 gnome-calculator &
sleep 1

vdisplay control list --app Calculator --backend atspi
vdisplay control click --app Calculator --role push button --name 7 --verify
vdisplay control click --app Calculator --role push button --name equals --verify
```

#### Text Editor / gedit

```bash
GDK_BACKEND=x11 GTK_A11Y=1 gnome-text-editor ~/notes.txt &
sleep 1

vdisplay control set-value --app "Text Editor" --role text --index 0 --value "hello from vdisplay" --verify
vdisplay control click --role button --name Save --verify
```

#### Settings (limited tree on Wayland)

```bash
# Settings is often native Wayland — tree may be shallow; use browser/terminal sessions for automation instead
vdisplay control list --app Settings --backend atspi --max-depth 3
vdisplay screenshot -o settings.png --source primary   # visual fallback
```

#### Firefox desktop window (not browser session)

```bash
# native Wayland Firefox: AT-SPI partial, x11 blocked — prefer browser session for web UI
# force X11 window for desktop-window control:
MOZ_ENABLE_WAYLAND=0 firefox &
sleep 3

vdisplay control list --app firefox --backend atspi --format tree
vdisplay control click --backend atspi --app firefox --role button --name Reload --verify
# do NOT use on Wayland host:
# vdisplay control click --backend x11 --app firefox --role button --name Reload
```

#### PyCharm / IntelliJ (Java AT-SPI)

```bash
vdisplay control list --backend atspi --app "PyCharm"
vdisplay control click --role button --name "Chat" --verify
vdisplay control set-value --role entry --name "Chat input" --value "Explain this stack trace" --verify
```

### GNOME terminal control (PTY sessions)

**GNOME Terminal** on Wayland usually has **no** usable desktop window for control — open a **PTY session** instead (works headless, in CI, and across CLI invocations):

```bash
# open session (DSL — same semantics as agent POST /session/terminal/open)
dsl2vdisplay -c 'terminal open --session-id term-1 --command bash --rows 40 --cols 120'

# inspect TUI grid
vdisplay control list --backend terminal --session-id term-1
vdisplay diagnose control --backend terminal --session-id term-1

# send keys at grid coordinates (1-based line/col)
vdisplay control click --backend terminal --session-id term-1 --terminal-line 1 --terminal-col 0
vdisplay control set-value --backend terminal --session-id term-1 --terminal-line 2 --value "ls -la" --verify
```

#### Interactive shell workflow

```bash
dsl2vdisplay -c 'terminal open --session-id shell-1 --command bash'
vdisplay control set-value --backend terminal --session-id shell-1 --terminal-line 1 --value "cd ~/github/wronai/vdisplay" --verify
vdisplay control set-value --backend terminal --session-id shell-1 --terminal-line 2 --value "git status" --verify
vdisplay control list --backend terminal --session-id shell-1
```

#### Python REPL

```bash
dsl2vdisplay -c 'terminal open --session-id py-1 --command python3 --rows 30 --cols 100'
vdisplay control set-value --backend terminal --session-id py-1 --terminal-line 1 --value "import vdisplay; print(vdisplay.__file__)" --verify
```

#### htop / ncurses (coordinate + text match)

```bash
dsl2vdisplay -c 'terminal open --session-id htop-1 --command htop'
sleep 2
vdisplay control find --backend terminal --session-id htop-1 --text-contains "Tasks"
vdisplay control click --backend terminal --session-id htop-1 --terminal-line 5 --terminal-col 0
```

#### vim / less (read-only navigation)

```bash
dsl2vdisplay -c 'terminal open --session-id vim-1 --command "vim /tmp/notes.txt"'
sleep 1
vdisplay control click --backend terminal --session-id vim-1 --terminal-line 1 --terminal-col 0
# prefer terminal session over chasing GNOME Terminal / Tilix / kitty desktop windows
```

#### Long-running terminal with agent broker

```bash
# terminal 1
vdisplay agent serve

# terminal 2 — session lives in broker process
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
dsl2vdisplay -c 'terminal open --session-id agent-term --command bash'
vdisplay control list --backend terminal --session-id agent-term
```

#### Terminal vs desktop terminal apps (GNOME)

| App | Desktop `control` | Recommended |
|-----|-------------------|-------------|
| GNOME Terminal | rarely works (Wayland) | `terminal open` + `--session-id` |
| Tilix / Terminator | XWayland only | PTY session or `--class Tilix` + screenshot |
| Alacritty / kitty | native Wayland hidden | PTY session |
| `ssh` in PTY | N/A | `terminal open --command "ssh host"` |

### Browser + terminal combined (typical dev loop)

```bash
# web UI in Playwright session (detached across CLI calls)
vdisplay control browser-open --url http://localhost:3000 --session-id web-1 --headed
vdisplay control click --backend browser --session-id web-1 --selector "#submit" --verify

# build/logs in PTY
dsl2vdisplay -c 'terminal open --session-id build-1 --command "npm run dev"'
vdisplay control set-value --backend terminal --session-id build-1 --terminal-line 1 --value "r" --verify
```

### Desktop app cheat sheet

| App | `vdisplay windows` | Control backend | Notes |
|-----|-------------------|-----------------|-------|
| JetBrains Toolbox / IDE | `--app JetBrains` | `atspi` (X11) | Often XWayland; Java ATK wrapper helps |
| Firefox (native Wayland) | usually hidden | monitor screenshot | Use screencast + `--source` |
| Firefox (X11) | `--class firefox` | `atspi` or relay | Check `about:support` → Window Protocol |
| Chromium / Chrome | `--class google-chrome` | `atspi` / relay | XWayland only in window list |
| Cursor / VS Code / Slack | `--app Cursor` / `code` | `atspi` (partial) | Wayland build → screenshot fallback |
| GNOME Terminal / Tilix | often hidden | `terminal` session | Open PTY session instead of desktop window |
| Alacritty / kitty | `--class` (X11 only) | `terminal` or screenshot | Native Wayland → monitor capture |
| Telegram / Signal / Discord | `--app` / `--class` | relay / screenshot | Electron; hide with `relay adopt-window` |
| Zoom / Teams / Meet | often hidden | monitor screenshot | Video UI rarely in XWayland list |
| DBeaver / Android Studio | `--app` / `--class` | `atspi` (Java) | `GTK_A11Y=1`; emulator via `--title` |
| Docker Desktop / Wireshark | `--class Docker` | relay / `atspi` | Mixed Electron/Qt |
| VLC / Audacity / Krita | `--class vlc` etc. | `atspi` (GTK/Qt) | `GDK_BACKEND=x11` on Wayland host |
| GIMP / Blender / OBS | `--class` / `--app` | `atspi` / relay | Move with `--target HDMI-1` |
| Thunderbird / Evolution | `--app Thunderbird` | `atspi` / relay | Mail clients on XWayland |
| Nautilus / Calculator | `--class org.gnome.*` | relay / `atspi` | Hide file manager before clean shot |
| virt-manager / VirtualBox | `--class virt-manager` | relay | VM window on second monitor |
| Bitwarden / Obsidian | `--app` | `atspi` (partial) | Electron; unlock via `--role button` |
| GTK demo / native GTK | `--app` / title | `atspi` | `GDK_BACKEND=x11` on Wayland host |
| Web app (any URL) | N/A | `browser` + session | `browser open` then DOM selectors |

### Typical desktop session (discover → hide → capture → control)

Copy-paste workflow when several apps are open on a GNOME desktop:

```bash
# 0) broker + portal (once per session)
vdisplay agent serve                              # terminal 1
vdisplay agent screencast start                   # terminal 2

# 1) inventory — what XWayland exposes vs monitors only
vdisplay all | jq '{
  monitors: [.monitors[] | {name, primary, nl}],
  windows: [.windows[] | {app_label, title, monitor_name}]
}'

# 2) hide noisy windows before a clean screenshot
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay adopt-window --class slack
vdisplay relay adopt-window --class org.gnome.Nautilus
vdisplay relay screenshot -o desk-clean.png --source DP-2

# 3) semantic control on an app that exposes AT-SPI (GTK/Java on X11)
export GDK_BACKEND=x11 GTK_A11Y=1
vdisplay control list --app DBeaver --backend atspi --format tree
vdisplay control click --app DBeaver --role button --name Execute --verify

# 4) web workflow — separate from desktop Firefox
dsl2vdisplay -c 'browser open --url https://example.com --session web-1 --headed'
vdisplay control click --backend browser --session-id web-1 --selector "a" --verify

# 5) restore hidden windows
vdisplay relay release-window --app "JetBrains"
vdisplay relay release-window --class slack
vdisplay relay release-window --class org.gnome.Nautilus
```

### Multi-monitor layout (3 outputs)

Inspect geometry, then capture or move windows per output:

```bash
vdisplay monitors | jq '.monitors[] | {name, primary, x, y, width, height, nl}'

# one PNG per connected output (Wayland: screencast + Entire Screen in portal for all)
vdisplay agent screencast start
vdisplay screenshot --all-monitors --out-dir ./captures
ls ./captures/    # DP-2.png, DP-1.png, HDMI-1.png

# single monitor by name
vdisplay screenshot -o dp1.png --source DP-1
vdisplay screenshot -o hdmi.png --source HDMI-1

# mirror primary onto second output (X11 multi-head only; Wayland → use screencast screenshot)
vdisplay mirror screenshot -o mirrored.png --source primary --target DP-1
```

### Isolated virtual desktop (any app, no portal)

Run apps on owned Xvfb `:99` — works headless and in CI:

```bash
sudo apt install xterm   # or firefox, etc.

vdisplay virtual start --width 1920 --height 1080 --display :99
vdisplay virtual launch xterm -hold
vdisplay virtual launch --display :99 xterm -e 'sleep 5; echo hello'

# separate session: launch spins up its own Xvfb, runs command, stops
vdisplay virtual launch xterm -hold
vdisplay virtual screenshot -o vd-xterm.png --display :99

# Python API — long-running agent on :99
python3 - <<'PY'
from vdisplay import VirtualDisplaySession
vd = VirtualDisplaySession.create(width=1280, height=720, display=":99")
vd.start()
vd.launch(["xterm", "-hold"])
vd.save_screenshot("agent-screen.png")
input("Press Enter to stop…")
vd.stop()
PY
```

### Quick agent setup (copy-paste for desktop capture)

```bash
# terminal 1 — leave running
vdisplay agent serve

# terminal 2
vdisplay agent health
vdisplay agent screencast start          # once per session; pick monitor or Entire Screen
vdisplay screenshot -o desk.png --source DP-2
vdisplay relay screenshot -o desk.png --source DP-2
vdisplay mirror screenshot -o desk.png --source primary
vdisplay agent screencast status
vdisplay agent screencast stop
```

If capture is **blank**, the portal shared a different monitor than `--source` — use `vdisplay monitors` + match the name, or restart screencast and choose **Entire Screen**.

### Example output

Monitor:

```json
{
  "name": "DP-2",
  "primary": true,
  "width": 4320,
  "height": 7680,
  "rotation": "left",
  "rotation_degrees": 90,
  "monitor_id": 0,
  "nl": "Primary monitor DP-2 (4320×7680, rotated left (90°)). Visible apps: Toolbox."
}
```

Window:

```json
{
  "window_id": "8388615",
  "app_label": "Toolbox",
  "monitor_id": 0,
  "monitor_name": "DP-2",
  "monitor_index": 0,
  "pid": 32977,
  "nl": "Toolbox application window (880×1326 at (4470,298)) on monitor DP-2, process jetbrains-toolb, class jetbrains-toolbox."
}
```

## Screenshots

### Quick reference

| Goal | Command |
|------|---------|
| One monitor (host) | `vdisplay screenshot -o screen.png --source DP-2` |
| All monitors | `vdisplay screenshot --all-monitors --out-dir ./captures` |
| Virtual Xvfb (no portal) | `vdisplay virtual screenshot -o screen.png --display :99` |
| Mirror + capture | `vdisplay mirror screenshot -o mirror.png --source primary --target DP-1` |
| Describe saved PNG (`img2nl`) | `vdisplay screenshot -o screen.png` → JSON field `nl` |
| Loop every 1s (after screencast) | see [Continuous capture](#continuous-capture-wayland) below |

With **`VDISPLAY_AGENT_URL`** set, screenshots route through the broker (same providers, one runtime).

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

# single monitor — use output name from: vdisplay monitors
vdisplay screenshot -o screen.png --monitor 1
vdisplay screenshot -o screen.png --source DP-2

# all connected monitors (DP-2.png, DP-1.png, HDMI-1.png, …)
vdisplay screenshot --all-monitors --out-dir ./captures

# isolated Xvfb session (works without portal / on headless CI)
vdisplay virtual screenshot -o screen.png --display :99
vdisplay screenshot -o vd.png --mode virtual --vd-display :99

# mirror: prefer mirror screenshot on Wayland (uses ScreenCast when active)
vdisplay mirror screenshot -o mirror.png --source primary --target DP-1
```

### Wayland host (GNOME) — start here

On **GNOME Wayland**, `DISPLAY=:0` is XWayland — direct X11/DRM capture often yields **black PNGs** (especially with NVIDIA).

**One-time setup** — needs **two terminals** (broker must stay running):

```bash
# terminal 1 — leave this running (blocks the shell)
vdisplay agent serve
# same as: vdisplay-agent serve
```

```bash
# terminal 2 — all capture commands go here
vdisplay agent health                    # should return {"status":"ok",...}
vdisplay agent screencast start          # pick monitor in portal dialog (once)
# GNOME: Settings → Privacy → Screen Recording → allow vdisplay-agent / terminal
```

> **Common mistake:** running `vdisplay agent screencast start` before `vdisplay agent serve`
> gives `Set VDISPLAY_AGENT_URL … or start: vdisplay-agent serve`. Start the broker first.

`VDISPLAY_AGENT_URL` is optional when the broker listens on `127.0.0.1:8765` (auto-detect).
Explicit export still works: `export VDISPLAY_AGENT_URL=http://127.0.0.1:8765`

**Then capture as often as you like** (no new prompts):

```bash
vdisplay screenshot -o host.png --source DP-2
vdisplay screenshot -o host.png --source primary
vdisplay mirror screenshot -o mirror.png --source primary --target DP-1
vdisplay relay screenshot -o relay.png --source DP-2
```

REST equivalent:

```bash
curl -X POST http://127.0.0.1:8765/session/screencast/start \
  -H 'content-type: application/json' -d '{"interactive": true}'
vdisplay screenshot -o host.png --source DP-1
```

> **Note:** `vdisplay mirror start -o mirror.png` runs xrandr mirror then tries driver-level capture directly.
> On Wayland use **`vdisplay mirror screenshot`** (or `vdisplay screenshot`) after screencast is active.

### Continuous capture (Wayland)

After `vdisplay agent screencast start`, grab frames every second without portal prompts:

```bash
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
mkdir -p ./captures
i=0
while true; do
  vdisplay screenshot -o "./captures/frame-$(printf '%04d' "$i").png" --source DP-2
  i=$((i + 1))
  sleep 1
done
```

Python (virtual display — no portal needed):

```python
import time
from pathlib import Path
from vdisplay import VirtualDisplaySession

vd = VirtualDisplaySession.create(display=":99")
vd.start()
try:
    for i in range(60):
        vd.save_screenshot(f"frame-{i:04d}.png")
        time.sleep(1)
finally:
    vd.stop()
```

See also [examples/ci-agent/](examples/ci-agent/) (`VD_FRAMES=60` in Docker).

### Describe a screenshot (`img2nl`)

By default, `vdisplay screenshot` enriches JSON with an **`nl`** field — a natural-language description of the saved PNG (Polish locale by default):

```bash
vdisplay screenshot -o screen.png --source DP-2 | jq '{path, nl, img2nl}'
```

Requires optional package: `pip install img2nl[analyze]`. Disable with `VDISPLAY_IMG2NL=0` or `vdisplay screenshot --no-img2nl`.

To describe an **existing** image file:

```python
from vdisplay.application.services.img2nl_enrich import describe_screenshot_image
print(describe_screenshot_image("screen.png")["text"])
```

## Actions — virtual, mirror, relay

```bash
# virtual display (isolated Xvfb)
vdisplay virtual start --width 1920 --height 1080 --display :99
vdisplay virtual launch xterm -hold          # flags after the command name are OK
vdisplay virtual screenshot -o screen.png --display :99

# mirror — needs two monitors; list names first with: vdisplay monitors
vdisplay mirror start --source primary --target DP-1          # xrandr only (no PNG)
vdisplay mirror screenshot -o mirror.png --source primary --target DP-1   # Wayland: screencast first
VD_SOURCE=DP-2 VD_TARGET=HDMI-1 ./examples/host-mirror/run.sh   # Docker; black PNGs on Wayland

# relay — hide window off-screen, restore later (separate CLI calls OK)
# 1) find a window to move
vdisplay windows --apps-only
vdisplay windows --app "JetBrains" | jq '.windows[] | {window_id, app_label, nl}'

# 2) adopt (move off-screen) — match by app, title, class, pid, or window-id
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay adopt-window --title "Firefox"
vdisplay relay adopt-window --class jetbrains-toolbox --pid 32977
vdisplay relay adopt-window --window-id 8388615

# 3) move to another monitor instead of off-screen
vdisplay relay adopt-window --app "Firefox" --target HDMI-1

# 4) list adopted windows (persisted in ~/.cache/vdisplay/)
vdisplay relay list
vdisplay relay list | jq '.adopted[] | {window_id, app_label, title, nl}'

# 5) restore — separate CLI call works (geometry saved on adopt)
vdisplay relay release-window --app "JetBrains"
vdisplay relay release-window --window-id 8388615

# 6) screenshot while relaying (Wayland: agent serve + screencast first)
# terminal 1: vdisplay agent serve
vdisplay agent screencast start
vdisplay relay screenshot -o before.png --source DP-2
vdisplay relay adopt-window --app "JetBrains"
vdisplay relay screenshot -o after-hide.png --source DP-2
vdisplay relay release-window --app "JetBrains"
vdisplay relay screenshot -o after-restore.png --source DP-2

# 7) full host demo (before / after adopt / after release PNGs)
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent screencast start
WINDOW_APP=JetBrains ./examples/host-relay/run-host.sh
# output: examples/host-relay/output/before_automation.png, after_adopt.png, after_release.png
```

**Relay tips**

- Adopted window positions **persist** across CLI calls (`~/.cache/vdisplay/__vdisplay_stash__-*.json`).
- Relay moves windows within the **same X11 session** — it does not move apps into Xvfb `:99`.
- On **Wayland**, window move uses XWayland; screenshots need **agent + screencast** (Docker `./run.sh` often yields black PNGs — use `./run-host.sh` instead).
- Filter windows first: `vdisplay windows --app "Toolbox"` → use `--app`, `--title`, or `--window-id` from JSON.

## Control plane (Semantic UI control)

The control plane provides a unified API for accessibility-first, semantic control of native applications, web browsers, and terminals, using computer vision (`img2nl` / screenshot diffs) to verify action execution.

Supported backends:
- `atspi` — Linux Desktop AT-SPI2 accessibility tree
- `browser` — Playwright headless/headed browser DOM
- `terminal` — Terminal session emulation and cursor positioning
- `x11` — `xdotool` keyboard/mouse pointer injection fallback

### CLI Examples

```bash
# 1) Diagnose control backends and readiness
vdisplay diagnose control

# 2) List all interactive controls (buttons, inputs, links)
vdisplay control list --backend auto

# 3) Filter controls by application (e.g. Firefox) in tree format
vdisplay control list --app firefox --backend auto --format tree

# 4) Click a button by name and verify state change semantically
vdisplay control click --role button --name "Save" --verify

# 5) Type text into an input field and verify value change
vdisplay control set-value --role input --name "Username" --value "admin" --verify

# 6) Click a control using CSS selectors in browser environment
vdisplay control click --backend browser --selector "#submit-btn" --session-id "web-1" --verify

# 7) Open browser session then route automatically (DSL)
dsl2vdisplay -c 'browser open --url https://example.com --session web-1 --vendor firefox'
dsl2vdisplay -c 'control click --backend browser --session-id web-1 --selector "#go" --verify'

# 8) Desktop GTK app on Wayland host (X11 backend for AT-SPI)
GDK_BACKEND=x11 GTK_A11Y=1 vdisplay control list --app vdisplay-gtk-demo --backend atspi

# 9) Java IDE toolbar (DBeaver / IntelliJ on XWayland)
vdisplay control click --app DBeaver --role button --name "Execute SQL" --verify

# 10) Electron app — unlock dialog (Bitwarden / Obsidian)
vdisplay control click --app Bitwarden --role button --name Unlock --verify

# 11) xdotool fallback — **X11 host only** (blocked on GNOME Wayland)
# vdisplay control click --backend x11 --app firefox --role button --name Reload

# 12) GNOME Files — navigate sidebar
GDK_BACKEND=x11 GTK_A11Y=1 vdisplay control click --app Nautilus --role button --name Home --verify

# 13) GNOME Calculator — press keys
vdisplay control click --app Calculator --role push button --name 5 --verify

# 14) PTY terminal — type command and verify grid
dsl2vdisplay -c 'terminal open --session-id t1 --command bash'
vdisplay control set-value --backend terminal --session-id t1 --terminal-line 1 --value "echo ok" --verify

# 15) Routing check with selector (browser engine + profile)
vdisplay diagnose control --selector "#go" --session-id web-1 --backend auto
```

### GNOME backend picker

| Goal | Backend | Example |
|------|---------|---------|
| GTK app (Files, Calculator) | `atspi` + `GDK_BACKEND=x11` | `control click --app Nautilus --role button --name Home` |
| Java IDE | `atspi` | `control click --app PyCharm --role button --name Run` |
| Web app / form | `browser` + session | `control browser-open` then `--selector "#id"` |
| Shell / TUI / CI | `terminal` + session | `terminal open` then `--terminal-line N` |
| Canvas / no a11y tree | `vision` (stub) | `diagnose control --vision-anchor btn` |
| Pointer injection | `x11` | **ineligible on Wayland** — use `atspi` or sessions |

### Python API Example

```python
from vdisplay.application.services import control as control_svc

# List controls from the active accessibility tree
controls = control_svc.controls_list(display=":0", app="Firefox", format="flat")
for c in controls:
    print(f"[{c['role']}] {c['name']} (at {c['x']},{c['y']})")

# Programmatically click a button and verify success
result = control_svc.control_click(
    display=":0",
    role="button",
    name="Log In",
    verify=True,
    screenshot_verify=True
)
print("Action OK:", result["ok"])
```

## Natural language and DSL

```bash
# NL → DSL → JSON (built into vdisplay)
vdisplay nlp "list monitors on display zero"
vdisplay nlp "show application windows" --dsl-only

# DSL bus (same semantics as CLI query verbs)
dsl2vdisplay -c 'MONITORS DISPLAY :0'
dsl2vdisplay -c 'WINDOWS DISPLAY :0 APPS_ONLY'
dsl2vdisplay -c 'ALL DISPLAY :0'

# NL package (thin wrapper; pip install -e packages/nlp2vdisplay)
nlp2vdisplay to-dsl "list monitors on display zero"
nlp2vdisplay apply "show application windows on display zero"
# shorthand — bare prompt defaults to apply:
nlp2vdisplay "show application windows on display zero"
```

Legacy DSL verbs still work: `OUTPUTS` maps to `MONITORS`, `WINDOWS` unchanged.

## vdisplay-agent broker

Install **once** on the host. CLI, DSL, REST, and MCP set `VDISPLAY_AGENT_URL` and route capture, sessions, and discovery through the broker — no per-app portal prompts or direct DRM access from adapters.

```bash
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay

# terminal 1 — broker (localhost)
vdisplay-agent serve
# or: vdisplay agent serve

# terminal 2 — clients
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765
vdisplay agent health
vdisplay monitors                    # 3 monitors in ~50 ms via agent /outputs
dsl2vdisplay -c 'MONITORS'
rest2vdisplay serve --port 8216 --agent-url $VDISPLAY_AGENT_URL
mcp2vdisplay serve                   # tool: vdisplay_agent_status
```

| Env var | Role |
|---------|------|
| `VDISPLAY_AGENT_URL` | Client → broker URL |
| `VDISPLAY_AGENT_TOKEN` | Optional Bearer auth |
| `VDISPLAY_CAPTURE_ALLOW_PORTAL` | Opt-in portal screenshot (agent only) |

**Wayland host capture:** start ScreenCast once in the agent (`POST /session/screencast/start`), then use normal screenshot commands. See [docs/agent-broker.md](docs/agent-broker.md) and [examples/agent-broker](examples/agent-broker/).

Virtual display screenshots work without portal. DRM/fbdev capture requires `video` group on some setups.

Full reference: [docs/agent-broker.md](docs/agent-broker.md) · [packages/vdisplay-agent](packages/vdisplay-agent/)

## Control layer equivalents

| Intent | CLI | DSL |
|--------|-----|-----|
| Full state | `vdisplay all` | `ALL DISPLAY :0` |
| Monitors | `vdisplay monitors` | `MONITORS DISPLAY :0` |
| Windows | `vdisplay windows --apps-only` | `WINDOWS DISPLAY :0` |
| Adopt window | `vdisplay relay adopt-window --app X` | `ADOPT APP X` |
| Screenshot | `vdisplay screenshot -o out.png` | `SCREENSHOT OUT out.png DISPLAY :99` |
| Validate tools | `vdisplay diagnose` | `VALIDATE DISPLAY :0` |

## Modes

| Mode | Purpose | Isolation | Screenshot | Window move |
|------|---------|-----------|------------|-------------|
| `virtual` | Private Xvfb session for agents | Yes | Yes | No (use `launch()`) |
| `mirror` | Duplicate existing display output | No | Yes | N/A |
| `relay` | Move window within same X11 session | Partial | Yes (`relay screenshot`) | Yes |
| `screencast` | Portal ScreenCast in agent (Wayland) | No | Yes (after consent) | N/A |

## Requirements (Linux v0.1)

| Component | Used by |
|-----------|---------|
| `Xvfb`, `xwd`, `scrot` | virtual / X11 capture |
| `xrandr` | mirror mode |
| `xdotool` | relay + input |
| `python3-dbus`, `python3-gi` | portal ScreenCast (Wayland host) |
| `ffmpeg` (PipeWire) or GStreamer `pipewiresrc` | ScreenCast frame grab |
| `Pillow` (optional) | faster PNG encoding |

```bash
sudo apt install xvfb x11-apps x11-utils xdotool scrot x11-xserver-utils
sudo apt install python3-dbus python3-gi   # Wayland ScreenCast in agent
pip install "vdisplay[pillow]"
```

Full setup: [docs/installation.md](docs/installation.md)

## Python API

### Sessions (backends)

```python
from vdisplay import VirtualDisplaySession, MirrorSession, WindowRelaySession
from vdisplay.discovery import list_monitors, list_windows

# Inspect monitors and windows with nl descriptions
for monitor in list_monitors():
    print(monitor["nl"])

for window in list_windows(apps_only=True):
    print(window["nl"])

# Virtual isolated display
vd = VirtualDisplaySession.create(width=1920, height=1080)
vd.start()
vd.launch(["xterm"])
vd.save_screenshot("screen.png")
vd.stop()

# Mirror existing desktop (same session, no isolation)
# On GNOME Wayland: start agent screencast before save_screenshot, or use capture_host_to_file()
m = MirrorSession.create(source="primary", target="DP-1")
m.start()
m.save_screenshot("mirror.png")   # needs ScreenCast on Wayland
m.stop()

# Relay window off-screen and restore (persists across CLI calls)
r = WindowRelaySession.create()
r.start()
r.adopt_window(match_app="JetBrains")
r.release_window(match_app="JetBrains")
r.stop()
```

### Application layer (shared by CLI / DSL / REST / MCP / agent)

```python
from vdisplay.application.commands import CommandRequest
from vdisplay.application.executor import execute
from vdisplay.application.services import discovery, capture, session, info

# Single execution entry (routes to agent when VDISPLAY_AGENT_URL is set)
result = execute(CommandRequest.from_dsl({"verb": "MONITORS"}, line="MONITORS"))
print(result.data)

# Direct service use-cases (always in-process)
monitors = discovery.list_monitors(display=":0")
meta = capture.capture_screenshot(output="screen.png", monitor=1)
session.virtual_start(width=1280, height=720, display=":99")
caps = info.platform_info()
```

Via broker SDK:

```python
from vdisplay.client import AgentClient

client = AgentClient("http://127.0.0.1:8765")
client.outputs()
client.start_screencast(interactive=True)
```

### Window heuristics (testable submodules)

```python
from vdisplay.windows import list_windows_enriched, find_windows, pick_best_window
from vdisplay.windows.rank import dedupe_app_windows
from vdisplay.windows.filter import is_internal_window
```

## Project layout

```
src/vdisplay/
├── application/
│   ├── commands.py         # CommandRequest / CommandResult / CommandVerb
│   ├── executor.py         # single entry: execute() → local or agent
│   ├── handlers/           # local + agent command handlers
│   └── services/           # discovery, capture, session, info
├── commands/               # CLI registry (set_defaults per subcommand)
├── windows/                # scan → normalize → filter → rank → query
├── capture/
│   ├── providers/          # drm, fbdev, mss, x11, portal (opt-in)
│   └── portal_screencast.py  # persistent ScreenCast (Wayland)
├── backends/               # virtual, mirror, relay
├── client.py               # AgentClient SDK
└── cli.py                  # thin entry: register_all + args.func(args)

packages/
├── dsl2vdisplay/           # grammar + CQRS bus → executor
├── vdisplay-agent/         # localhost broker (privileged runtime)
├── rest2vdisplay/          # HTTP → DSL
├── mcp2vdisplay/           # MCP tools
└── nlp2vdisplay/           # NL → DSL
```

## Control layer (DSL / MCP / REST / NL)

Programmatic interfaces on top of the same application services. All query results include `nl` on monitors and windows.

| Package | Role |
|---------|------|
| [dsl2vdisplay](packages/dsl2vdisplay/) | Grammar + CQRS bus (`MONITORS`, `WINDOWS`, `ADOPT`, …) |
| [nlp2vdisplay](packages/nlp2vdisplay/) | Natural language → DSL |
| [uri2vdisplay](packages/uri2vdisplay/) | `vdisplay://cmd/...` → DSL |
| [cli2vdisplay](packages/cli2vdisplay/) | REPL over DSL |
| [mcp2vdisplay](packages/mcp2vdisplay/) | MCP server tools |
| [rest2vdisplay](packages/rest2vdisplay/) | REST API on port 8216 |
| [vdisplay-agent](packages/vdisplay-agent/) | Local broker — sessions, capture, relay |

```bash
vdisplay-agent serve --port 8765
export VDISPLAY_AGENT_URL=http://127.0.0.1:8765

pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
rest2vdisplay serve --port 8216 --agent-url $VDISPLAY_AGENT_URL
mcp2vdisplay serve
curl -s http://127.0.0.1:8216/health | jq .
curl -s -X POST http://127.0.0.1:8216/v1/dsl -H 'content-type: text/plain' -d 'MONITORS' | jq .
```

Full reference: [packages/README.md](packages/README.md)

## Limitations

- Existing windows on `DISPLAY=:0` **cannot** move into Xvfb `:99` — different X servers.
- Use `VirtualDisplaySession.launch()` for apps on the virtual display.
- Use `WindowRelaySession` to hide/show windows on the current session.
- `mirror` controls the same desktop through a duplicated output, not an isolated copy.
- `nl` on monitors lists apps whose window center falls on that output geometry.
- On **GNOME Wayland**, Docker X11 forwarding often produces black screenshots — use [vdisplay-agent](docs/agent-broker.md) on the host instead.
- Windows/macOS backends are planned; Linux/X11 + Wayland (via agent) supported in v0.1.

Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)

## Development

```bash
pip install -e ".[pillow,dev]"
pip install -e "packages/vdisplay-agent[serve]"
pip install -e packages/dsl2vdisplay packages/rest2vdisplay packages/mcp2vdisplay
pytest tests/ -q
./examples/agent-broker/run.sh
./examples/run_all_examples.sh   # where host X11 is available
```

Architecture: [docs/architecture.md](docs/architecture.md)

## License

Licensed under Apache-2.0.

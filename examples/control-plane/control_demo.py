#!/usr/bin/env python3
"""Control Plane Demo — showcase semantic control via AT-SPI, terminal, and browser."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path to allow running from within the examples directory
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from vdisplay.application.services import control as control_svc
from vdisplay.application.services import session as session_svc
from vdisplay.discovery import resolve_host_display
from vdisplay.exceptions import VDisplayError


def run_diagnostics(display: str) -> None:
    print("==> 1. Control Plane Diagnostics")
    diag = control_svc.diagnose_control(display=display)
    print(json.dumps(diag, indent=2))
    print("-" * 60)


def show_active_controls(display: str) -> None:
    print("==> 2. Listing Active Desktop UI Controls (AT-SPI / X11)")
    try:
        # List flat controls up to depth 3
        result = control_svc.controls_list(
            display=display,
            backend="auto",
            max_depth=3,
            format="flat"
        )
        nodes = list(result.get("nodes", {}).values())
        print(f"Found {len(nodes)} visible controls on display {display}:")
        for i, c in enumerate(nodes[:15]):
            app_str = f" in {c.get('app_label')}" if c.get("app_label") else ""
            bounds = c.get("bounds") or {}
            x, y = bounds.get("x", 0), bounds.get("y", 0)
            print(f"  [{i}] Role: {c.get('role')}, Name: '{c.get('name')}'{app_str} at ({x}, {y})")
        if len(nodes) > 15:
            print(f"  ... and {len(nodes) - 15} more controls.")
    except Exception as exc:
        print(f"Could not read AT-SPI controls: {exc}")
    print("-" * 60)


def run_terminal_demo(display: str) -> None:
    print("==> 3. Terminal Control Session Demo")
    try:
        # Check if terminal session dependencies (pyte, pexpect) are available
        diag = control_svc.diagnose_control(display=display)
        if "terminal" not in diag.get("control", {}).get("backends", []):
            print("Terminal backend is not supported/ready (requires pyte and pexpect). Skipping.")
            return

        # Start a local bash shell session
        print("Opening terminal session (running 'bash')...")
        session_id = "demo-term-session"
        
        open_res = session_svc.terminal_open(
            session_id=session_id,
            command="/bin/bash",
            cols=80,
            rows=24,
        )
        print("Terminal opened:", json.dumps(open_res, indent=2))

        # Send command (e.g. ls -la) to terminal
        print("Sending command 'echo hello-vdisplay' to terminal...")
        set_res = control_svc.control_set_value(
            display=display,
            backend="terminal",
            session_id=session_id,
            role="input",
            value="echo hello-vdisplay\n",
            verify=True,
        )
        print("Set-value result:", json.dumps(set_res, indent=2))

        # Wait a moment for bash to execute and print
        time.sleep(0.5)

        # Read terminal output controls
        result = control_svc.controls_list(
            display=display,
            backend="terminal",
            session_id=session_id,
        )
        nodes = list(result.get("nodes", {}).values())
        print("Terminal screen lines:")
        for line in nodes:
            if line.get("role") == "terminal_line":
                state = line.get("state") or {}
                print(f"  Line {state.get('terminal_line')}: '{line.get('name')}'")

    except Exception as exc:
        print(f"Terminal demo encountered an error: {exc}")
    print("-" * 60)


def run_browser_demo(display: str) -> None:
    print("==> 4. Headless Browser Control Demo")
    try:
        # Check if browser backend (playwright) is available
        diag = control_svc.diagnose_control(display=display)
        if "browser" not in diag.get("control", {}).get("backends", []):
            print("Browser backend is not supported/ready (requires playwright). Skipping.")
            return

        session_id = "demo-browser-session"
        print("Launching headless browser to example.com...")
        
        open_res = session_svc.browser_open(
            session_id=session_id,
            url="https://example.com",
            headless=True,
        )
        print("Browser opened:", json.dumps(open_res, indent=2))

        # List DOM elements (links, headings, etc.)
        result = control_svc.controls_list(
            display=display,
            backend="browser",
            session_id=session_id,
        )
        nodes = list(result.get("nodes", {}).values())
        print(f"Found {len(nodes)} DOM elements:")
        for c in nodes[:15]:
            # DOM selectors might be inside state or separate fields
            selector = c.get("state", {}).get("dom_css") or c.get("provider_ref")
            print(f"  Role: {c.get('role')}, Name: '{c.get('name')}', Selector: {selector}")
        if len(nodes) > 15:
            print(f"  ... and {len(nodes) - 15} more elements.")

        # Click the 'More information...' link
        print("Clicking the 'More information...' link...")
        click_res = control_svc.control_click(
            display=display,
            backend="browser",
            session_id=session_id,
            role="link",
            name="More information...",
            verify=True,
        )
        print("Click result:", json.dumps(click_res, indent=2))

    except Exception as exc:
        print(f"Browser demo encountered an error: {exc}")
    print("-" * 60)


def main() -> int:
    display = resolve_host_display(os.environ.get("DISPLAY"))
    print(f"Initializing Control Plane Demo on DISPLAY={display}...\n")
    
    run_diagnostics(display)
    show_active_controls(display)
    run_terminal_demo(display)
    run_browser_demo(display)
    
    print("Demo completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

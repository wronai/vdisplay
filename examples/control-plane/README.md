# Control Plane Demo Example

This example demonstrates how to use the **vdisplay control plane** to programmatically query, inspect, and interact with user interface controls. It covers:

1. **Diagnostics**: Querying control capability support and available providers.
2. **Desktop UI Controls**: Scanning the AT-SPI accessibility tree to list desktop controls.
3. **Terminal Sessions**: Launching an interactive terminal process (`bash`), writing input, and listing terminal grid outputs.
4. **Browser Sessions**: Opening a headless browser via Playwright, listing DOM element structures, clicking links, and verifying actions.

## Prerequisites

Ensure all dependencies for the control plane are installed:

```bash
# Install system packages (required for AT-SPI bridge support)
sudo apt install libatk-wrapper-java

# Install optional Python dependencies for control backends
pip install "vdisplay[dev]"
```

## Running the Demo

Simply execute the script:

```bash
./control_demo.py
```

Or run it through the main package virtual environment:

```bash
python3 examples/control-plane/control_demo.py
```

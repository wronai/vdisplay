# macOS AX control plugin example (PR-23)

Installable wheel that registers an **`example-ax`** provider via the
`vdisplay.control_providers` entry-point group. It wraps the core
`AxControlProvider` and shows how to ship **macOS-only semantic control**
as an optional package with platform deps (`pyobjc-framework-ApplicationServices`).

On non-macOS hosts (CI, Linux dev machines) the plugin uses
`MockAxBackend` with a synthetic Calculator tree so tests and docs run everywhere.

## Layout

```
examples/control-plugin-ax/
├── README.md
├── pyproject.toml
└── src/vdisplay_example_ax_plugin/
    ├── __init__.py      # register_plugin() entry point
    └── provider.py      # ExampleAxProvider + ProviderDescriptor
```

## Install

```bash
cd ~/github/wronai/vdisplay
source venv/bin/activate
pip install -e ".[dev]"
pip install -e examples/control-plugin-ax

# macOS native AX (optional)
pip install -e "examples/control-plugin-ax[macos]"
export VDISPLAY_AX_MOCK=0   # use ApplicationServices on darwin
```

## Verify registration

```bash
vdisplay diagnose control | jq '.extensions.plugins[] | select(.provider_id=="example-ax")'

# Forced routing (mock tree on Linux)
vdisplay control list --backend example-ax --app Calculator
vdisplay control click --backend example-ax --role button --name OK --verify
```

## Mock vs native

| Host | Default backend | Override |
|------|-----------------|----------|
| Linux / CI | `MockAxBackend` (Calculator demo tree) | `VDISPLAY_AX_MOCK=1` |
| macOS | Native `PyobjcAxBackend` | `VDISPLAY_AX_MOCK=1` forces mock |
| macOS (native) | ApplicationServices AX | `VDISPLAY_AX_MOCK=0` |

## Production pattern

vdisplay core already ships builtin `ax` with host-gated scoring. For a
**third-party or OEM wheel**, reuse this layout but:

1. Set `provider_id="ax"` (or your vendor id) in `ProviderDescriptor`
2. Declare `pyobjc-framework-ApplicationServices` with `sys_platform == 'darwin'`
3. Keep invoke/find logic in the wheel — do **not** patch `scoring.py`

See also: [control-plugin-uia](../control-plugin-uia/) (Windows), [control-plugin](../control-plugin/) (minimal echo stub).

## Tests

```bash
pytest tests/test_example_uia_ax_plugins.py -q
```

## References

- RFC: [`docs/rfc/001-extensibility-model.md`](../../docs/rfc/001-extensibility-model.md)
- Core AX: `src/vdisplay/control/providers/ax.py`
- Plugin API: `src/vdisplay/control/plugins.py`

"""Portal dependency bootstrap from system dist-packages."""

from __future__ import annotations

import pytest


def test_ensure_portal_deps_loads_system_dbus_from_venv(monkeypatch) -> None:
    import sys

    from vdisplay.capture import portal_screencast as ps

    # Simulate a clean venv without dbus on path
    monkeypatch.setattr(sys, "path", [p for p in sys.path if "dist-packages" not in p])
    ps._ensure_portal_deps()
    try:
        import dbus
    except ImportError as exc:
        # System python3-dbus missing, or its C extension was built for a
        # different interpreter version than this venv (ABI mismatch).
        pytest.skip(f"system dbus bindings unavailable for this interpreter: {exc}")

    assert "dist-packages" in str(dbus.__file__)

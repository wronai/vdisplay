"""xdg-desktop-portal screenshot (GNOME/Wayland). Uses system python3 when venv lacks dbus."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..exceptions import VDisplayError


def _portal_impl(out: Path, *, interactive: bool, timeout_s: float) -> dict:
    try:
        import dbus
        from dbus.mainloop.glib import DBusGMainLoop
        from gi.repository import GLib
    except ImportError as exc:
        return {
            "ok": False,
            "error": f"portal capture needs python3-dbus and python3-gi: {exc}",
        }

    from urllib.parse import unquote, urlparse

    result: dict = {"ok": False, "response": -1, "uri": ""}

    def on_response(response, results) -> None:
        result["response"] = int(response)
        if int(response) == 0:
            result["uri"] = str(results.get("uri", ""))
            result["ok"] = True
        elif int(response) == 1:
            result["error"] = "user cancelled portal screenshot"
        elif int(response) == 2:
            result["error"] = (
                "portal screenshot denied (Screen Recording permission missing). "
                "GNOME: Settings → Privacy → Screen Recording → enable your terminal/IDE, "
                "or run once with portal interactive=True to grant access."
            )
        else:
            result["error"] = f"portal screenshot failed with response={response}"
        loop.quit()

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    token = "vdisplay_capture"
    unique = bus.get_unique_name()[1:].replace(".", "_")
    request_path = f"/org/freedesktop/portal/desktop/request/{unique}/{token}"
    bus.add_signal_receiver(
        on_response,
        dbus_interface="org.freedesktop.portal.Request",
        path=request_path,
    )
    proxy = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    iface = dbus.Interface(proxy, dbus_interface="org.freedesktop.portal.Screenshot")
    iface.Screenshot(
        "",
        {
            "interactive": dbus.Boolean(interactive),
            "handle_token": token,
        },
    )

    loop = GLib.MainLoop()
    GLib.timeout_add_seconds(max(1, int(timeout_s)), loop.quit)
    loop.run()

    if not result.get("ok"):
        return result

    src = Path(unquote(urlparse(result["uri"]).path))
    if not src.is_file():
        return {"ok": False, "error": f"portal uri missing file: {result['uri']}"}

    shutil.copy2(src, out)
    return {"ok": True, "path": str(out), "source": "xdg-portal"}


def _system_python() -> str:
    for candidate in ("/usr/bin/python3", shutil.which("python3")):
        if candidate and Path(candidate).is_file():
            return candidate
    return sys.executable


def capture_portal_png(*, interactive: bool = False, timeout_s: float = 25.0) -> bytes:
    """Capture full desktop PNG via xdg-desktop-portal."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        out = Path(tmp.name)
    try:
        payload = _capture_portal_to_file(out, interactive=interactive, timeout_s=timeout_s)
        if not payload.get("ok"):
            raise VDisplayError(str(payload.get("error") or "portal capture failed"))
        data = out.read_bytes()
        if len(data) < 64:
            raise VDisplayError("portal capture returned empty PNG")
        return data
    finally:
        out.unlink(missing_ok=True)


def _capture_portal_to_file(
    out: Path,
    *,
    interactive: bool,
    timeout_s: float,
) -> dict:
    try:
        import dbus  # noqa: F401

        return _portal_impl(out, interactive=interactive, timeout_s=timeout_s)
    except ImportError:
        pass

    system_py = _system_python()
    script = r'''
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

def portal_impl(out, interactive, timeout_s):
    try:
        import dbus
        from dbus.mainloop.glib import DBusGMainLoop
        from gi.repository import GLib
    except ImportError as exc:
        return {"ok": False, "error": f"portal capture needs python3-dbus and python3-gi: {exc}"}

    result = {"ok": False, "response": -1, "uri": ""}

    def on_response(response, results):
        result["response"] = int(response)
        if int(response) == 0:
            result["uri"] = str(results.get("uri", ""))
            result["ok"] = True
        elif int(response) == 1:
            result["error"] = "user cancelled portal screenshot"
        elif int(response) == 2:
            result["error"] = (
                "portal screenshot denied (Screen Recording permission missing). "
                "GNOME: Settings → Privacy → Screen Recording → enable your terminal/IDE."
            )
        else:
            result["error"] = f"portal screenshot failed with response={response}"
        loop.quit()

    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    token = "vdisplay_capture"
    unique = bus.get_unique_name()[1:].replace(".", "_")
    request_path = f"/org/freedesktop/portal/desktop/request/{unique}/{token}"
    bus.add_signal_receiver(
        on_response,
        dbus_interface="org.freedesktop.portal.Request",
        path=request_path,
    )
    proxy = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    iface = dbus.Interface(proxy, dbus_interface="org.freedesktop.portal.Screenshot")
    iface.Screenshot("", {"interactive": dbus.Boolean(interactive), "handle_token": token})
    loop = GLib.MainLoop()
    GLib.timeout_add_seconds(max(1, int(timeout_s)), loop.quit)
    loop.run()
    if not result.get("ok"):
        return result
    src = Path(unquote(urlparse(result["uri"]).path))
    if not src.is_file():
        return {"ok": False, "error": f"portal uri missing file: {result['uri']}"}
    shutil.copy2(src, out)
    return {"ok": True, "path": str(out), "source": "xdg-portal"}

out = Path(sys.argv[1])
interactive = sys.argv[2].lower() in {"1", "true", "yes"}
timeout_s = float(sys.argv[3])
print(json.dumps(portal_impl(out, interactive, timeout_s)))
'''
    try:
        completed = subprocess.run(
            [system_py, "-c", script, str(out), str(interactive).lower(), str(timeout_s)],
            capture_output=True,
            text=True,
            timeout=timeout_s + 5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"portal capture timed out after {timeout_s}s"}

    if completed.returncode != 0 and not completed.stdout.strip():
        err = (completed.stderr or completed.stdout or "portal subprocess failed").strip()
        return {"ok": False, "error": err}

    try:
        import json

        payload = json.loads(completed.stdout.strip() or "{}")
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass
    return {"ok": False, "error": completed.stderr.strip() or "portal subprocess returned invalid JSON"}


class PortalProvider:
    """Opt-in portal capture (VDISPLAY_CAPTURE_ALLOW_PORTAL=1). Not used by default."""

    name = "portal"

    def available(self) -> tuple[bool, str]:
        return True, "xdg-desktop-portal (requires Screen Recording consent)"

    def capture_full(self) -> bytes:
        return capture_portal_png(interactive=False, timeout_s=20.0)

    def capture_region(self, region: tuple[int, int, int, int]) -> bytes:
        from .linux_xwd import _crop_png

        return _crop_png(self.capture_full(), region)


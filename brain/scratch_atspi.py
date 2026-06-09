import sys
import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi, GLib

Atspi.init()
desktop = Atspi.get_desktop(0)
print(f"Desktop child count: {desktop.get_child_count()}")

for i in range(desktop.get_child_count()):
    try:
        app = desktop.get_child_at_index(i)
        if app is None:
            print(f"[{i}]: None")
            continue
        print(f"[{i}]: Role: {app.get_role_name()}, Name: {app.name}")
    except Exception as exc:
        print(f"[{i}]: Error: {exc}")

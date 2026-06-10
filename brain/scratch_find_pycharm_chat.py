import sys
import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi

Atspi.init()
desktop = Atspi.get_desktop(0)

def dump_tree(accessible, path, depth=0):
    if depth > 12:  # Prevent infinite recursion / deep nest hangs
        return
    try:
        role = accessible.get_role_name() or "unknown"
    except Exception:
        role = "error"
    try:
        name = accessible.name or ""
    except Exception:
        name = "error"
    try:
        desc = accessible.description or ""
    except Exception:
        desc = "error"
        
    text_val = ""
    try:
        text_iface = accessible.get_text_iface()
        if text_iface:
            count = Atspi.Text.get_character_count(text_iface)
            if count > 0:
                text_val = Atspi.Text.get_text(text_iface, 0, count).strip()
    except Exception:
        pass
        
    role_lower = role.lower()
    name_lower = name.lower()
    desc_lower = desc.lower()
    
    # We want to find editable text elements, or elements that look like chat input/boxes
    is_interesting = (
        "entry" in role_lower or 
        "text" in role_lower or 
        "chat" in name_lower or 
        "chat" in desc_lower or
        "chat" in role_lower or
        "editor" in role_lower or
        "input" in name_lower
    )
    
    if is_interesting:
        print(f"{'  ' * depth}[{path}] Role: {role}, Name: '{name}', Desc: '{desc}', TextVal: '{text_val}'")
        
    try:
        child_count = accessible.get_child_count()
    except Exception:
        child_count = 0
        
    for i in range(child_count):
        try:
            child = accessible.get_child_at_index(i)
            if child:
                dump_tree(child, f"{path}/{i}", depth + 1)
        except Exception:
            continue

print(f"Desktop child count: {desktop.get_child_count()}")
for i in range(desktop.get_child_count()):
    try:
        app = desktop.get_child_at_index(i)
        if app is None:
            print(f"[{i}]: None")
            continue
        try:
            name = app.name
        except Exception as e:
            name = f"Error getting name: {e}"
        print(f"[{i}] App Name: '{name}'")
        dump_tree(app, str(i))
    except Exception as exc:
        print(f"[{i}] Root error: {exc}")

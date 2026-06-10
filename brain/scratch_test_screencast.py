import sys
import uuid
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

def test_screencast():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    screencast = dbus.Interface(proxy, dbus_interface="org.freedesktop.portal.ScreenCast")

    loop = GLib.MainLoop()

    def on_create(response, results):
        print(f"on_create response={response} results={results}")
        if response != 0:
            print("CreateSession failed")
            loop.quit()
            return
        
        session_handle = results.get("session_handle")
        print(f"Created session: {session_handle}")
        
        # Now try SelectSources twice to simulate "Sources already selected"
        select_token = "vdisplay_select_test_1"
        select_path = f"/org/freedesktop/portal/desktop/request/{bus.get_unique_name()[1:].replace('.', '_')}/{select_token}"
        
        def on_select(resp, res):
            print(f"on_select response={resp} results={res}")
            
            # Now trigger Start
            start_token = "vdisplay_start_test"
            start_path = f"/org/freedesktop/portal/desktop/request/{bus.get_unique_name()[1:].replace('.', '_')}/{start_token}"
            
            def on_start(resp_st, res_st):
                print(f"on_start response={resp_st} results={res_st}")
                loop.quit()

            bus.add_signal_receiver(
                on_start,
                dbus_interface="org.freedesktop.portal.Request",
                signal_name="Response",
                path=str(start_path),
            )
            
            try:
                print("Calling Start...")
                screencast.Start(session_handle, "", {"handle_token": start_token})
                print("Start call completed")
            except Exception as e:
                print(f"Start exception: {e}")
                loop.quit()

        bus.add_signal_receiver(
            on_select,
            dbus_interface="org.freedesktop.portal.Request",
            signal_name="Response",
            path=str(select_path),
        )
        
        try:
            print("Calling SelectSources 1...")
            screencast.SelectSources(
                session_handle,
                {
                    "handle_token": select_token,
                    "types": dbus.UInt32(1),
                    "multiple": dbus.Boolean(False),
                    "cursor_mode": dbus.UInt32(2),
                    "interactive": dbus.Boolean(True),
                }
            )
            print("SelectSources 1 completed")
        except Exception as e:
            print(f"SelectSources 1 exception: {e}")

        # Try calling it again to force "Sources already selected"
        try:
            print("Calling SelectSources 2 (expecting failure/already selected)...")
            screencast.SelectSources(
                session_handle,
                {
                    "handle_token": select_token,
                    "types": dbus.UInt32(1),
                    "multiple": dbus.Boolean(False),
                    "cursor_mode": dbus.UInt32(2),
                    "interactive": dbus.Boolean(True),
                }
            )
            print("SelectSources 2 completed")
        except Exception as e:
            print(f"SelectSources 2 exception: {e}")
            if "Sources already selected" in str(e):
                print("Caught expected exception. Attempting to proceed to on_select...")
                # Manually trigger on_select to proceed to Start
                on_select(0, {})

    create_token = "vdisplay_create_test_2"
    unique = bus.get_unique_name()[1:].replace(".", "_")
    create_path = f"/org/freedesktop/portal/desktop/request/{unique}/{create_token}"
    
    bus.add_signal_receiver(
        on_create,
        dbus_interface="org.freedesktop.portal.Request",
        signal_name="Response",
        path=str(create_path),
    )
    
    session_token = f"vdisplay_sess_{uuid.uuid4().hex[:8]}"
    print(f"Calling CreateSession...")
    screencast.CreateSession(
        {
            "handle_token": create_token,
            "session_handle_token": session_token,
        }
    )
    
    GLib.timeout_add_seconds(10, lambda: loop.quit() or False)
    loop.run()

if __name__ == "__main__":
    test_screencast()

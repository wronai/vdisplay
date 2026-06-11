"""Keep a portal ScreenCast session alive in a user-GUI process for the agent broker."""

from __future__ import annotations

import base64
import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

from ..exceptions import VDisplayError
from .portal_screencast import (
    ensure_portal_session_env,
    portal_session_env_status,
    screencast_adopt_payload,
    start_screencast_session,
    stop_screencast_session,
)

_STATE_NAME = "vdisplay-screencast-keeper.json"
_STOP_NAME = "vdisplay-screencast-keeper.stop"
_SOCKET_NAME = "vdisplay-screencast.sock"
_DEFAULT_CAPTURE_TIMEOUT_S = 30.0
_CAPTURE_SERVER: dict[str, Any] = {}


def keeper_state_path() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(runtime) / _STATE_NAME


def keeper_stop_path() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(runtime) / _STOP_NAME


def keeper_socket_path() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(runtime) / _SOCKET_NAME


def _keeper_runtime_dir() -> str:
    return os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"


def session_uses_keeper(session: Any) -> bool:
    if bool(getattr(session, "keeper_managed", False)):
        sock = str(getattr(session, "keeper_socket_path", "") or "").strip()
        if sock:
            return True
        pid = int(getattr(session, "keeper_pid", 0) or 0)
        if pid > 0 and _pid_alive(pid):
            return True
    return keeper_manages_session(str(getattr(session, "session_path", "") or ""))


def keeper_manages_session(session_path: str) -> bool:
    path = str(session_path or "").strip()
    if not path:
        return False
    state = read_keeper_state()
    return state is not None and str(state.get("session_path") or "") == path


def _resolve_keeper_socket_path(
    *,
    socket_path: str | None = None,
    state: dict[str, Any] | None = None,
) -> Path:
    explicit = str(socket_path or "").strip()
    if explicit:
        return Path(explicit)
    if state is not None:
        from_state = str(state.get("socket_path") or "").strip()
        if from_state:
            return Path(from_state)
    return keeper_socket_path()


def ping_keeper_socket(
    socket_path: str | Path,
    *,
    timeout_s: float = 2.0,
) -> bool:
    path = Path(socket_path)
    if not path.is_socket():
        return False
    payload = {"op": "ping"}
    request = (json.dumps(payload) + "\n").encode("utf-8")
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        conn.settimeout(timeout_s)
        conn.connect(str(path))
        conn.sendall(request)
        data = b""
        while b"\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
    except OSError:
        return False
    finally:
        conn.close()
    line = data.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
    if not line:
        return False
    try:
        response = json.loads(line)
    except json.JSONDecodeError:
        return False
    return isinstance(response, dict) and bool(response.get("ok"))


def keeper_capture_ready(
    state: dict[str, Any] | None = None,
    *,
    socket_path: str | None = None,
    timeout_s: float = 2.0,
) -> bool:
    path = _resolve_keeper_socket_path(socket_path=socket_path, state=state)
    if not path.is_socket():
        return False
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if ping_keeper_socket(path, timeout_s=min(1.0, timeout_s)):
            return True
        if not path.is_socket():
            return False
        time.sleep(0.05)
    return False


def _capture_server_running() -> bool:
    thread = _CAPTURE_SERVER.get("thread")
    return (
        thread is not None
        and thread.is_alive()
        and keeper_socket_path().is_socket()
    )


def _ensure_capture_server(session: Any, *, pid: int) -> None:
    if _capture_server_running():
        return
    _CAPTURE_SERVER["thread"] = _start_capture_server(session, pid=pid)


def request_keeper_capture(
    *,
    node_index: int = 0,
    session_path: str | None = None,
    socket_path: str | None = None,
    timeout_s: float = _DEFAULT_CAPTURE_TIMEOUT_S,
) -> bytes:
    """Capture a PNG frame from the keeper-owned portal session."""
    state = read_keeper_state()
    expected_path = str(session_path or (state or {}).get("session_path") or "").strip()
    if state is not None and session_path and str(state.get("session_path") or "") != session_path:
        # Adopted metadata may outlive keeper state; still try explicit socket_path.
        if not socket_path:
            raise VDisplayError("screencast keeper session mismatch")
        state = None
    sock_path = _resolve_keeper_socket_path(socket_path=socket_path, state=state)
    if not sock_path.is_socket():
        raise VDisplayError(
            f"screencast keeper capture socket unavailable ({sock_path})"
        )

    payload = {"op": "capture", "node_index": int(node_index)}
    if expected_path:
        payload["session_path"] = expected_path
    request = (json.dumps(payload) + "\n").encode("utf-8")

    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        conn.settimeout(timeout_s)
        conn.connect(str(sock_path))
        conn.sendall(request)
        data = b""
        while b"\n" not in data:
            chunk = conn.recv(65536)
            if not chunk:
                break
            data += chunk
    finally:
        conn.close()

    line = data.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
    if not line:
        raise VDisplayError("screencast keeper capture returned no response")
    try:
        response = json.loads(line)
    except json.JSONDecodeError as exc:
        raise VDisplayError(f"screencast keeper capture invalid response: {exc}") from exc
    if not isinstance(response, dict):
        raise VDisplayError("screencast keeper capture invalid response type")
    if not response.get("ok"):
        raise VDisplayError(str(response.get("error") or "screencast keeper capture failed"))
    raw = response.get("png_base64")
    if not isinstance(raw, str) or not raw:
        raise VDisplayError("screencast keeper capture missing png_base64")
    try:
        return base64.b64decode(raw.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise VDisplayError(f"screencast keeper capture decode failed: {exc}") from exc


def read_keeper_state() -> dict[str, Any] | None:
    path = keeper_state_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    pid = int(payload.get("pid") or 0)
    if pid > 0 and not _pid_alive(pid):
        return None
    return payload


def stop_keeper() -> dict[str, Any]:
    state = read_keeper_state()
    keeper_socket_path().unlink(missing_ok=True)
    if state is None:
        keeper_stop_path().unlink(missing_ok=True)
        return {"ok": True, "stopped": False}
    pid = int(state.get("pid") or 0)
    try:
        keeper_stop_path().write_text("stop", encoding="utf-8")
    except OSError:
        pass
    if pid > 0:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.time() + 3.0
    while time.time() < deadline:
        if read_keeper_state() is None:
            break
        time.sleep(0.1)
    keeper_state_path().unlink(missing_ok=True)
    keeper_stop_path().unlink(missing_ok=True)
    stop_screencast_session()
    return {"ok": True, "stopped": True, "pid": pid}


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _write_state(session, *, pid: int, socket_ready: bool = False) -> dict[str, Any]:
    runtime = _keeper_runtime_dir()
    sock = str(Path(runtime) / _SOCKET_NAME)
    payload = {
        "pid": pid,
        "ready": True,
        "runtime_dir": runtime,
        "socket_path": sock,
        "keeper_managed": True,
        "socket_ready": socket_ready,
        **screencast_adopt_payload(session),
    }
    keeper_state_path().write_text(json.dumps(payload), encoding="utf-8")
    return payload


def _mark_socket_ready(session: Any, *, pid: int) -> None:
    _write_state(session, pid=pid, socket_ready=True)


def _dispatch_capture_request(session: Any, request: dict[str, Any]) -> dict[str, Any]:
    op = str(request.get("op") or "").strip().lower()
    if op == "ping":
        return {
            "ok": True,
            "session_path": session.session_path,
            "node_ids": session.node_ids,
        }
    if op != "capture":
        return {"ok": False, "error": f"unknown op: {op or 'missing'}"}

    expected = str(request.get("session_path") or "").strip()
    if expected and expected != str(session.session_path or ""):
        return {"ok": False, "error": "session_path mismatch"}

    try:
        node_index = int(request.get("node_index") or 0)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid node_index"}

    try:
        png = session.capture_png_local(node_index=node_index)
    except VDisplayError as exc:
        return {"ok": False, "error": f"capture failed: {exc}"}
    return {
        "ok": True,
        "png_base64": base64.b64encode(png).decode("ascii"),
        "bytes": len(png),
    }


def _handle_capture_connection(session: Any, conn: socket.socket) -> None:
    data = b""
    while b"\n" not in data:
        chunk = conn.recv(65536)
        if not chunk:
            return
        data += chunk
    line = data.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
    if not line:
        response = {"ok": False, "error": "empty request"}
    else:
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = {"ok": False, "error": "invalid json"}
        else:
            if not isinstance(request, dict):
                response = {"ok": False, "error": "request must be a json object"}
            else:
                op = str(request.get("op") or "").strip().lower()
                if op == "ping":
                    response = _dispatch_capture_request(session, request)
                else:
                    result_holder: dict[str, Any] = {}
                    done = threading.Event()

                    def _worker() -> None:
                        try:
                            result_holder["response"] = _dispatch_capture_request(session, request)
                        except Exception as exc:
                            result_holder["response"] = {
                                "ok": False,
                                "error": f"capture failed: {exc}",
                            }
                        finally:
                            done.set()

                    threading.Thread(
                        target=_worker,
                        daemon=True,
                        name="vdisplay-screencast-capture-worker",
                    ).start()
                    if not done.wait(timeout=_DEFAULT_CAPTURE_TIMEOUT_S * 4):
                        response = {
                            "ok": False,
                            "error": f"keeper capture timed out after {_DEFAULT_CAPTURE_TIMEOUT_S * 4:.0f}s",
                        }
                    else:
                        response = result_holder.get("response") or {
                            "ok": False,
                            "error": "keeper capture returned no response",
                        }
    try:
        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
    except OSError:
        return


def _start_capture_server(session: Any, *, pid: int) -> threading.Thread:
    sock_path = keeper_socket_path()

    def _serve() -> None:
        sock_path.unlink(missing_ok=True)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(str(sock_path))
            os.chmod(sock_path, 0o600)
            server.listen(8)
            server.settimeout(1.0)
            _mark_socket_ready(session, pid=pid)
            while session.active and session.is_ready and not keeper_stop_path().is_file():
                try:
                    conn, _addr = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if (
                        keeper_stop_path().is_file()
                        or not session.active
                        or not session.is_ready
                    ):
                        break
                    time.sleep(0.1)
                    continue
                with conn:
                    try:
                        conn.settimeout(_DEFAULT_CAPTURE_TIMEOUT_S)
                        _handle_capture_connection(session, conn)
                    except Exception as exc:
                        try:
                            with open("/tmp/vdisplay-keeper-error.log", "a", encoding="utf-8") as f:
                                f.write(f"--- Connection Error: {exc} ---\n")
                        except Exception:
                            pass
                        continue
        finally:
            server.close()
            sock_path.unlink(missing_ok=True)
            if session.active and session.is_ready and not keeper_stop_path().is_file():
                _write_state(session, pid=pid, socket_ready=False)

    thread = threading.Thread(target=_serve, daemon=True, name="vdisplay-screencast-capture")
    thread.start()
    return thread


def run_keeper_daemon(
    *,
    interactive: bool = True,
    timeout_s: float = 120.0,
    multiple: bool | None = None,
) -> int:
    """Run portal ScreenCast and hold the session until SIGTERM or stop file."""
    ensure_portal_session_env()
    ok, hint = portal_session_env_status()
    if not ok:
        print(hint, file=sys.stderr)
        return 1

    stop_keeper()
    keeper_stop_path().unlink(missing_ok=True)
    session = start_screencast_session(
        interactive=interactive,
        timeout_s=timeout_s,
        multiple=multiple,
    )
    _write_state(session, pid=os.getpid(), socket_ready=False)
    _ensure_capture_server(session, pid=os.getpid())

    def _shutdown(*_args: object) -> None:
        try:
            session.stop()
        except Exception:
            pass
        keeper_state_path().unlink(missing_ok=True)
        keeper_stop_path().unlink(missing_ok=True)
        keeper_socket_path().unlink(missing_ok=True)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    while True:
        if keeper_stop_path().is_file():
            _shutdown()
        if not session.is_ready:
            break
        _ensure_capture_server(session, pid=os.getpid())
        if not _capture_server_running():
            _write_state(session, pid=os.getpid(), socket_ready=False)
        time.sleep(1.0)
    return 0


def spawn_keeper(
    *,
    interactive: bool = True,
    timeout_s: float = 120.0,
    multiple: bool | None = None,
) -> dict[str, Any]:
    """Start keeper subprocess in the user's GUI session; return adopt payload when ready."""
    import subprocess

    ensure_portal_session_env()
    ok, hint = portal_session_env_status()
    if not ok:
        raise VDisplayError(hint)

    stop_keeper()
    src = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.update(ensure_portal_session_env())
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [
        sys.executable,
        "-m",
        "vdisplay.capture.screencast_keeper",
        "daemon",
        "--timeout",
        str(timeout_s),
        "--multiple",
        "true" if multiple is not False else "false",
    ]
    if not interactive:
        cmd.append("--no-interactive")

    subprocess.Popen(
        cmd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    deadline = time.time() + timeout_s + 15.0
    while time.time() < deadline:
        state = read_keeper_state()
        if state is not None and state.get("session_path"):
            if keeper_capture_ready(state, timeout_s=2.0):
                return state
        time.sleep(0.25)

    stop_keeper()
    raise VDisplayError(
        f"screencast keeper timed out after {timeout_s}s — "
        "complete the GNOME Screen Recording dialog (All Screens) or check "
        "Settings → Privacy → Screen Recording for python3."
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="vdisplay-screencast-keeper")
    sub = parser.add_subparsers(dest="command", required=True)

    daemon = sub.add_parser("daemon", help="Hold portal ScreenCast session open")
    daemon.add_argument("--timeout", type=float, default=120.0)
    daemon.add_argument("--multiple", default="true")
    daemon.add_argument("--no-interactive", action="store_true")
    daemon.set_defaults(func=lambda a: run_keeper_daemon(
        interactive=not a.no_interactive,
        timeout_s=a.timeout,
        multiple=a.multiple.lower() in {"1", "true", "yes"},
    ))

    stop = sub.add_parser("stop")
    stop.set_defaults(func=lambda _a: (print(json.dumps(stop_keeper())), 0)[1])

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

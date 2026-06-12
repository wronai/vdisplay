"""Web console — multi-monitor view and automation controls."""

from __future__ import annotations

from collections.abc import Callable
from importlib import resources
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from .. import schemas as S
from ..envelope import json_error, json_from_runtime, strip_ok, success
from ..runtime import AgentRuntime
from ..services import web_console


def _console_html() -> str:
    path = Path(__file__).resolve().parent.parent / "static" / "console.html"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    try:
        return resources.files("vdisplay_agent.static").joinpath("console.html").read_text(encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"console.html missing: {exc}") from exc


def _browser_bridge_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>vdisplay browser bridge</title>
  <style>
    :root { color-scheme: dark; font-family: ui-sans-serif, system-ui, sans-serif; }
    body { margin: 0; background: #101820; color: #f6f1e7; }
    main { box-sizing: border-box; display: grid; gap: 16px; min-height: 100vh; padding: 20px; }
    header, section { border: 1px solid rgba(255,255,255,.14); border-radius: 20px; background: rgba(255,255,255,.08); padding: 16px; }
    header { align-items: center; display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; }
    h1 { font-size: 20px; margin: 0; }
    button { border: 0; border-radius: 12px; background: #f6c85f; color: #101820; cursor: pointer; font-weight: 800; padding: 10px 14px; }
    button.secondary { background: rgba(255,255,255,.14); color: #f6f1e7; }
    input { border: 1px solid rgba(255,255,255,.18); border-radius: 10px; background: rgba(0,0,0,.25); color: #f6f1e7; padding: 10px; }
    label { display: grid; gap: 6px; font-size: 12px; font-weight: 800; }
    video { background: #050708; border-radius: 16px; max-height: 72vh; object-fit: contain; width: 100%; }
    pre { color: #d7ffe0; max-height: 220px; overflow: auto; white-space: pre-wrap; }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>vdisplay browser bridge</h1>
        <p>Chrome/Chromium getDisplayMedia fallback for GNOME Wayland.</p>
      </div>
      <label>Source <input id="source" value="HDMI-1" /></label>
      <button id="start">Share screen</button>
      <button id="stop" class="secondary">Stop</button>
    </header>
    <section>
      <video id="preview" autoplay muted playsinline></video>
    </section>
    <section>
      <pre id="status">idle</pre>
    </section>
    <canvas id="canvas" hidden></canvas>
  </main>
  <script>
    const params = new URLSearchParams(location.search);
    const sourceInput = document.getElementById("source");
    const statusEl = document.getElementById("status");
    const video = document.getElementById("preview");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    sourceInput.value = params.get("source") || params.get("monitor") || "HDMI-1";
    let stream = null;
    let bridgeId = "";
    let seq = 0;
    let heartbeatTimer = null;
    let frameTimer = null;

    function log(payload) {
      statusEl.textContent = JSON.stringify(payload, null, 2);
    }

    async function postJson(path, payload) {
      const response = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.ok === false) {
        throw new Error((data.error && data.error.message) || data.detail || response.statusText);
      }
      return data.data || data;
    }

    async function registerBridge() {
      const source = sourceInput.value.trim() || "HDMI-1";
      const payload = await postJson("/session/browser-bridge/register", {
        client: "vdisplay-browser-bridge",
        version: "0.1.0",
        sources: [source],
        monitors: [source],
      });
      bridgeId = payload.bridge_id;
      return bridgeId;
    }

    async function heartbeat() {
      if (!bridgeId) return;
      const source = sourceInput.value.trim() || "HDMI-1";
      await postJson("/session/browser-bridge/heartbeat", {
        bridge_id: bridgeId,
        sharing: Boolean(stream),
        sources: [source],
        monitors: [source],
        fps: 2,
      });
    }

    async function pushFrame() {
      if (!stream || !bridgeId) {
        log({ ok: false, phase: "pushFrame", error: "stream or bridge missing", bridge_id: bridgeId, has_stream: Boolean(stream) });
        return;
      }
      if (video.videoWidth <= 0 || video.videoHeight <= 0) {
        log({ ok: false, phase: "pushFrame", error: "video has no dimensions yet", bridge_id: bridgeId, videoWidth: video.videoWidth, videoHeight: video.videoHeight });
        return;
      }
      const source = sourceInput.value.trim() || "HDMI-1";
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/png");
      if (!dataUrl || dataUrl.length < 100) {
        log({ ok: false, phase: "pushFrame", error: "canvas produced an empty frame", width: canvas.width, height: canvas.height });
        return;
      }
      await postJson("/capture/ingest", {
        bridge_id: bridgeId,
        source,
        seq: ++seq,
        mime: "image/png",
        data_url: dataUrl,
        width: canvas.width,
        height: canvas.height,
        captured_at_ms: Date.now(),
        source_name: document.title,
      });
      log({ ok: true, bridge_id: bridgeId, source, seq, width: canvas.width, height: canvas.height });
    }

    function stop() {
      clearInterval(heartbeatTimer);
      clearInterval(frameTimer);
      heartbeatTimer = null;
      frameTimer = null;
      if (stream) {
        for (const track of stream.getTracks()) track.stop();
      }
      stream = null;
      video.srcObject = null;
      log({ ok: true, stopped: true, bridge_id: bridgeId });
    }

    async function start() {
      stop();
      await registerBridge();
      stream = await navigator.mediaDevices.getDisplayMedia({
        audio: false,
        video: { cursor: "always", frameRate: { ideal: 5, max: 15 } },
      });
      video.srcObject = stream;
      for (const track of stream.getVideoTracks()) track.addEventListener("ended", stop);
      await new Promise((resolve) => {
        if (video.readyState >= 2) { resolve(); return; }
        video.addEventListener("loadeddata", () => resolve(), { once: true });
        setTimeout(resolve, 3000);
      });
      try { await video.play(); } catch (e) {
        if (e.name !== "AbortError") throw e;
        /* autoplay already started playback — safe to ignore */
      }
      await new Promise((resolve) => {
        if (video.videoWidth > 0 && video.videoHeight > 0) {
          resolve();
          return;
        }
        video.onloadedmetadata = () => resolve();
        setTimeout(resolve, 1500);
      });
      await heartbeat();
      await pushFrame();
      heartbeatTimer = setInterval(() => heartbeat().catch((error) => log({ ok: false, error: String(error) })), 2000);
      frameTimer = setInterval(() => pushFrame().catch((error) => log({ ok: false, error: String(error) })), 500);
    }

    document.getElementById("start").addEventListener("click", () => start().catch((error) => log({ ok: false, error: String(error) })));
    document.getElementById("stop").addEventListener("click", stop);
    log({ ok: true, url: location.href, source: sourceInput.value, hint: "Click Share screen, choose the IDE monitor, then keep this tab open." });
  </script>
</body>
</html>"""


def register_routes(
    app: FastAPI,
    broker: AgentRuntime,
    check_auth: Callable[[str | None], None],
) -> None:
    @app.get("/web", response_class=HTMLResponse, include_in_schema=False)
    def web_console_page() -> HTMLResponse:
        return HTMLResponse(_console_html())

    @app.get("/api/web/browser-bridge", response_class=HTMLResponse, include_in_schema=False)
    def web_browser_bridge_page() -> HTMLResponse:
        return HTMLResponse(_browser_bridge_html())

    @app.get("/api/web/overview")
    def web_overview(
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        payload = web_console.build_overview(broker, display=display)
        return success(S.ACTION_WEB_OVERVIEW, payload)

    @app.get("/api/web/frame/{monitor_name}")
    def web_frame(
        monitor_name: str,
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> FileResponse:
        check_auth(authorization)
        try:
            path = web_console.capture_monitor_frame(
                broker,
                monitor_name,
                display=display,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return FileResponse(path, media_type="image/png", filename=f"{monitor_name}.png")

    @app.get("/api/web/frames")
    def web_frames(
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        try:
            frames = web_console.capture_all_monitor_frames(broker, display=display)
        except Exception as exc:
            return json_error(S.ACTION_WEB_FRAMES, exc)
        payload = {
            "count": len(frames),
            "frames": [
                {
                    "monitor_name": item["monitor_name"],
                    "url": f"/api/web/frame/{item['monitor_name']}",
                    "meta": item.get("meta"),
                }
                for item in frames
            ],
        }
        return json_from_runtime(S.ACTION_WEB_FRAMES, payload)

    @app.post("/api/web/screencast/start")
    async def web_screencast_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        payload = dict(body or {})
        payload.setdefault("multiple", True)
        payload.setdefault("interactive", True)
        try:
            return json_from_runtime(
                S.ACTION_SCREENCAST_START,
                broker.start_screencast(
                    interactive=bool(payload.get("interactive", True)),
                    timeout_s=float(payload.get("timeout_s", 120.0)),
                    multiple=payload.get("multiple"),
                ),
            )
        except Exception as exc:
            return json_error(S.ACTION_SCREENCAST_START, exc)

    @app.post("/api/web/sampler/start")
    async def web_sampler_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        payload = dict(body or {})
        payload.setdefault("mode", "desktop")
        payload.setdefault("all_monitors", True)
        payload.setdefault("interval_s", 5.0)
        try:
            return json_from_runtime(S.ACTION_SAMPLER_START, broker.start_sampler(payload))
        except Exception as exc:
            return json_error(S.ACTION_SAMPLER_START, exc)

    @app.get("/api/web/replay/sessions")
    def web_replay_sessions(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        return success(S.ACTION_WEB_REPLAY_SESSIONS, {"sessions": web_console.list_replay_sessions()})

    @app.post("/api/web/replay/start")
    async def web_replay_start(
        body: dict[str, Any],
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        session_id = str((body or {}).get("session_id") or "").strip()
        if not session_id:
            return json_error(S.ACTION_WEB_REPLAY_START, ValueError("session_id required"))
        try:
            return json_from_runtime(S.ACTION_WEB_REPLAY_START, web_console.queue_replay(session_id))
        except Exception as exc:
            return json_error(S.ACTION_WEB_REPLAY_START, exc)

    @app.get("/api/web/replay/status/{job_id}")
    def web_replay_status(
        job_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        check_auth(authorization)
        from vdisplay.application.replay import replay_job_status

        payload = replay_job_status(job_id)
        if payload is None:
            raise HTTPException(status_code=404, detail=f"replay job not found: {job_id}")
        return success(S.ACTION_WEB_REPLAY_STATUS, payload)

    @app.post("/api/web/pointer/click")
    async def web_pointer_click(
        body: dict[str, Any],
        display: str | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        check_auth(authorization)
        payload = dict(body or {})
        monitor_name = str(payload.get("monitor_name") or payload.get("monitor") or "").strip()
        if not monitor_name:
            return json_error(S.ACTION_WEB_POINTER_CLICK, ValueError("monitor_name required"))
        try:
            x = float(payload.get("x"))
            y = float(payload.get("y"))
        except (TypeError, ValueError):
            return json_error(S.ACTION_WEB_POINTER_CLICK, ValueError("x and y required"))
        coord_space = str(payload.get("coord_space") or "png")
        button = int(payload.get("button") or 1)
        try:
            return json_from_runtime(
                S.ACTION_WEB_POINTER_CLICK,
                web_console.click_monitor_pointer(
                    broker,
                    monitor_name=monitor_name,
                    x=x,
                    y=y,
                    coord_space=coord_space,
                    button=button,
                    display=display,
                ),
            )
        except Exception as exc:
            return json_error(S.ACTION_WEB_POINTER_CLICK, exc)

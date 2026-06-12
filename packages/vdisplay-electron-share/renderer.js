"use strict";

const startButton = document.getElementById("start");
const stopButton = document.getElementById("stop");
const compactButton = document.getElementById("compact");
const fullButton = document.getElementById("full");
const trayButton = document.getElementById("tray");
const webButton = document.getElementById("web");
const exportLogsButton = document.getElementById("exportLogs");
const targetInput = document.getElementById("target");
const alwaysOnTopInput = document.getElementById("alwaysOnTop");
const statusEl = document.getElementById("status");
const badgeEl = document.getElementById("badge");
const video = document.getElementById("preview");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d", { alpha: false });
const screenPicker = document.getElementById("screenPicker");
const previewWrap = document.getElementById("previewWrap");
const screenGrid = document.getElementById("screenGrid");
const refreshScreensButton = document.getElementById("refreshScreens");
const windowSidebar = document.getElementById("windowSidebar");
const windowList = document.getElementById("windowList");
const windowEmpty = document.getElementById("windowEmpty");
const sidebarMeta = document.getElementById("sidebarMeta");
const refreshWindowsButton = document.getElementById("refreshWindows");

let config = {};
let stream = null;
let frameTimer = null;
let mainPreviewTimer = null;
let captureGeneration = 0;
let sharedDisplayId = "";
let sharedDisplayLabel = "";
let activeSourceId = "";
let activeSourceName = "";
let windowRefreshTimer = null;

function logRenderer(level, message, details = null) {
  if (window.vdisplayShare && typeof window.vdisplayShare.log === "function") {
    window.vdisplayShare.log(level, message, details);
  }
}

window.addEventListener("error", (event) => {
  logRenderer("renderer-error", event.message || "renderer error", {
    filename: event.filename || "",
    lineno: event.lineno || 0,
    colno: event.colno || 0,
    error: event.error ? String(event.error.stack || event.error.message || event.error) : "",
  });
});

window.addEventListener("unhandledrejection", (event) => {
  logRenderer("renderer-error", "unhandled promise rejection", {
    reason: event.reason ? String(event.reason.stack || event.reason.message || event.reason) : "",
  });
});

function waitForVideoReady(videoEl) {
  if (videoEl.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
    return Promise.resolve();
  }
  return new Promise((resolve, reject) => {
    const onReady = () => {
      cleanup();
      resolve();
    };
    const onError = () => {
      cleanup();
      reject(videoEl.error || new Error("video failed to load stream"));
    };
    const cleanup = () => {
      videoEl.removeEventListener("loadedmetadata", onReady);
      videoEl.removeEventListener("canplay", onReady);
      videoEl.removeEventListener("error", onError);
    };
    videoEl.addEventListener("loadedmetadata", onReady, { once: true });
    videoEl.addEventListener("canplay", onReady, { once: true });
    videoEl.addEventListener("error", onError, { once: true });
  });
}

async function safePlay(videoEl) {
  const initialSource = videoEl.srcObject;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      await videoEl.play();
      return true;
    } catch (error) {
      const message = String(error && error.message ? error.message : error);
      const interrupted =
        Boolean(error && error.name === "AbortError") ||
        message.includes("interrupted by a new load request") ||
        message.includes("interrupted by a call to pause");
      if (!interrupted) {
        throw error;
      }
      if (videoEl.srcObject !== initialSource) {
        return false;
      }
      await new Promise((resolve) => setTimeout(resolve, 80));
    }
  }
  return false;
}

function applyMode(mode) {
  const nextMode = mode === "full" ? "full" : "compact";
  document.body.classList.toggle("full", nextMode === "full");
  document.body.classList.toggle("compact", nextMode === "compact");
}

function setStatus(payload) {
  const next = {
    sharing: Boolean(stream),
    targetLabel: targetInput.value || config.targetLabel,
    sharedDisplayId,
    sharedDisplayLabel,
    activeSourceId,
    activeSourceName,
    ...payload,
  };
  window.vdisplayShare.status(next);
  badgeEl.textContent = `${next.sharing ? "sharing" : "idle"}: ${next.targetLabel || "target"}`;
  statusEl.textContent = JSON.stringify(
    {
      broker: config.url,
      agent: config.agentUrl || null,
      ozonePlatform: config.ozonePlatform || "",
      useSystemPicker: Boolean(config.useSystemPicker),
      bridgePush: Boolean(config.bridgePush),
      bridgeSource: config.bridgeSource || "",
      ...next,
    },
    null,
    2,
  );
}

function showScreenPicker() {
  screenPicker.classList.remove("hidden");
  previewWrap.classList.add("hidden");
}

function showPreview() {
  screenPicker.classList.add("hidden");
  previewWrap.classList.remove("hidden");
}

function showWindowSidebar(visible) {
  windowSidebar.classList.toggle("hidden", !visible);
}

function thumbnailMarkup(thumbnail, label) {
  if (thumbnail) {
    return `<img alt="${label}" src="${thumbnail}" />`;
  }
  return `<div class="placeholder">No preview</div>`;
}

function displaysToScreenCards(displays) {
  return (displays || []).map((display) => ({
    id: `display:${display.id}`,
    name: display.label || `Display ${display.id}`,
    display_id: String(display.id),
    display_label: display.label || `Display ${display.id}`,
    thumbnail: null,
    primary: Boolean(display.primary),
    fallback: true,
    size: display.size,
  }));
}

function displayIdOf(display) {
  if (!display) {
    return "";
  }
  const value = display.display_id || display.id;
  return value === undefined || value === null ? "" : String(value);
}

function displayLabelOf(display) {
  if (!display) {
    return "";
  }
  const id = displayIdOf(display);
  return display.display_label || display.label || display.name || (id ? `Display ${id}` : "");
}

function selectDisplay(display) {
  const id = displayIdOf(display);
  if (!id) {
    return "";
  }
  sharedDisplayId = id;
  sharedDisplayLabel = displayLabelOf(display);
  return sharedDisplayId;
}

async function getDisplayMediaWithTimeout(constraints, generation, timeoutMs = 12000) {
  let timedOut = false;
  const mediaPromise = navigator.mediaDevices.getDisplayMedia(constraints);
  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => {
      timedOut = true;
      reject(new Error(`GNOME Screen Share picker timed out after ${timeoutMs}ms`));
    }, timeoutMs);
  });
  mediaPromise
    .then((lateMedia) => {
      if (timedOut || generation !== captureGeneration) {
        for (const track of lateMedia.getTracks()) {
          track.stop();
        }
      }
    })
    .catch(() => {});
  return Promise.race([mediaPromise, timeoutPromise]);
}

function displayMatchesPreferred(display, preferred) {
  if (!preferred || !preferred.width || !display || !display.bounds) {
    return false;
  }
  const scale = preferred.width / Math.max(1, display.bounds.width);
  const expectedX = preferred.x / scale;
  const expectedY = preferred.y / scale;
  return (
    Math.abs(display.bounds.x - expectedX) <= 16 &&
    Math.abs(display.bounds.y - expectedY) <= 16
  );
}

function findPreferredDisplay(displays, preferred) {
  if (!preferred || !preferred.width) {
    return null;
  }
  return (displays || []).find((display) => displayMatchesPreferred(display, preferred)) || null;
}

function ensureDisplaySelection(displays) {
  const list = displays || config.displays || [];
  const preferredDisplay = findPreferredDisplay(list, config.preferredBounds);
  if (preferredDisplay) {
    if (String(preferredDisplay.id) !== sharedDisplayId) {
      return selectDisplay(preferredDisplay);
    }
    return sharedDisplayId;
  }
  if (sharedDisplayId) {
    return sharedDisplayId;
  }
  const selected = list.find((display) => display && display.primary) || list[0];
  return selectDisplay(selected);
}

function renderScreenGrid(screens) {
  screenGrid.innerHTML = "";
  if (!screens.length) {
    screenGrid.innerHTML =
      `<p class="empty-state">No monitors found. Check GNOME Screen Recording permission for Electron, then click Refresh.</p>`;
    return;
  }
  for (const screenSource of screens) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "source-card";
    if (screenSource.id === activeSourceId || String(screenSource.display_id || "") === sharedDisplayId) {
      card.classList.add("active");
    }
    const meta = [
      screenSource.display_label || `Display ${screenSource.display_id || "?"}`,
      screenSource.primary ? "primary" : "",
      screenSource.size ? `${screenSource.size.width}×${screenSource.size.height}` : "",
      screenSource.fallback ? "no preview yet" : "",
    ]
      .filter(Boolean)
      .join(" · ");
    card.innerHTML = `
      ${thumbnailMarkup(screenSource.thumbnail, screenSource.name)}
      <strong>${screenSource.name}</strong>
      <span>${meta}</span>
    `;
    card.addEventListener("click", () => {
      selectDisplay(screenSource);
      renderScreenGrid(screens);
      refreshWindowSidebar().catch((error) => {
        setStatus({ error: String(error) });
      });
      if (screenSource.fallback) {
        startCaptureWithSystemPicker().catch((error) => {
          setStatus({ sharing: false, error: String(error && error.message ? error.message : error) });
        });
        return;
      }
      startCaptureFromSource({
        sourceId: screenSource.id,
        sourceName: screenSource.name,
        displayId: screenSource.display_id,
        displayLabel: screenSource.display_label || screenSource.name,
        kind: "screen",
      });
    });
    screenGrid.appendChild(card);
  }
}

function renderWindowList(windows, filtered, fallback = "") {
  windowList.innerHTML = "";
  const visible = windows.length > 0;
  windowEmpty.classList.toggle("hidden", visible);
  if (!visible) {
    sidebarMeta.textContent = sharedDisplayId
      ? `No windows detected on ${sharedDisplayLabel || sharedDisplayId}. Click Refresh windows after moving or opening the target app.`
      : "Choose a monitor to list window previews.";
    return;
  }
  for (const windowSource of windows) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "window-item";
    if (windowSource.id === activeSourceId) {
      item.classList.add("active");
    }
    item.innerHTML = `
      ${thumbnailMarkup(windowSource.thumbnail, windowSource.name)}
      <div>
        <strong>${windowSource.name}</strong>
        <span>${
          windowSource.source === "agent-windows"
            ? `agent list · ${windowSource.display_label || windowSource.display_id || "display unknown"}`
            : windowSource.display_id
              ? `display ${windowSource.display_id}`
              : "display unknown"
        }</span>
      </div>
    `;
    item.addEventListener("click", () => {
      if (windowSource.source === "agent-windows") {
        setStatus({
          sharing: false,
          error:
            "This window is visible via agent metadata only; use the Chrome browser bridge or share the whole monitor for live preview.",
        });
        return;
      }
      startCaptureFromSource({
        sourceId: windowSource.id,
        sourceName: windowSource.name,
        displayId: sharedDisplayId,
        displayLabel: sharedDisplayLabel,
        kind: "window",
      });
    });
    windowList.appendChild(item);
  }
  sidebarMeta.textContent = fallback === "agent-windows"
    ? `${windows.length} XWayland window(s) from agent metadata; live previews unavailable in Electron on this Wayland session`
    : filtered
      ? `${windows.length} window(s) on ${sharedDisplayLabel || sharedDisplayId || "shared screen"}`
      : `${windows.length} window(s) shown (display filter unavailable on this platform)`;
}

async function refreshScreenPicker() {
  const payload = await window.vdisplayShare.listSources(null, false);
  const screens = payload.screens || displaysToScreenCards(payload.displays);
  const displays = payload.displays && payload.displays.length ? payload.displays : screens;
  ensureDisplaySelection(displays);
  renderScreenGrid(screens);
  return payload;
}

async function refreshWindowSidebar() {
  ensureDisplaySelection(config.displays);
  showWindowSidebar(true);
  const payload = await window.vdisplayShare.listSources(sharedDisplayId || null);
  ensureDisplaySelection(payload.displays);
  renderWindowList(payload.windows || [], Boolean(payload.filtered), payload.windowsFallback || "");
  return payload;
}

function stopWindowRefresh() {
  if (windowRefreshTimer) {
    clearInterval(windowRefreshTimer);
    windowRefreshTimer = null;
  }
}

function startWindowRefresh() {
  stopWindowRefresh();
  windowRefreshTimer = setInterval(() => {
    refreshWindowSidebar().catch(() => {});
  }, 4000);
}

function stopMainPreviewPolling() {
  if (mainPreviewTimer) {
    clearInterval(mainPreviewTimer);
    mainPreviewTimer = null;
  }
  video.classList.remove("hidden");
  const previewFrame = document.getElementById("previewFrame");
  if (previewFrame) {
    previewFrame.classList.add("hidden");
    previewFrame.removeAttribute("src");
  }
}

function startMainPreviewPolling() {
  stopMainPreviewPolling();
  let previewFrame = document.getElementById("previewFrame");
  if (!previewFrame) {
    previewFrame = document.createElement("img");
    previewFrame.id = "previewFrame";
    previewFrame.alt = "shared screen";
    previewWrap.appendChild(previewFrame);
  }
  video.classList.add("hidden");
  previewFrame.classList.remove("hidden");
  const base = (config && config.url) || "http://127.0.0.1:8799";
  const refresh = () => {
    previewFrame.src = `${base}/frame.png?t=${Date.now()}`;
  };
  refresh();
  mainPreviewTimer = setInterval(refresh, 500);
}

function stopCapture() {
  captureGeneration += 1;
  stopWindowRefresh();
  stopMainPreviewPolling();
  window.vdisplayShare.stopMainCapture().catch(() => {});
  if (frameTimer) {
    clearInterval(frameTimer);
    frameTimer = null;
  }
  if (stream) {
    for (const track of stream.getTracks()) {
      track.stop();
    }
  }
  stream = null;
  video.srcObject = null;
  activeSourceId = "";
  activeSourceName = "";
  showScreenPicker();
  showWindowSidebar(Boolean(sharedDisplayId));
  setStatus({ sharing: false, error: "" });
}

function isWaylandRuntime() {
  return Boolean(config && config.ozonePlatform === "wayland");
}

async function tryMainCaptureFallback(generation) {
  setStatus({
    sharing: false,
    error:
      "requesting screen capture — keep this Electron window focused (approve GNOME dialog if shown, up to 15s)",
  });
  await window.vdisplayShare.ensureCaptureFocus().catch(() => {});
  const result = await window.vdisplayShare.startMainCapture({
    displayId: sharedDisplayId,
    displayLabel: sharedDisplayLabel,
    sourceId: activeSourceId,
    sourceName: activeSourceName,
  });
  if (generation !== captureGeneration) {
    return { ok: false, cancelled: true };
  }
  if (result && result.ok) {
    showPreview();
    showWindowSidebar(true);
    startMainPreviewPolling();
    setStatus({
      sharing: true,
      error: "",
      captureMode: result.captureMode || "main-desktopCapturer",
    });
    return result;
  }
  return result || { ok: false, error: "main-process capture failed" };
}

async function beginDisplayMediaCapture(generation, { statusHint = "" } = {}) {
  if (isWaylandRuntime()) {
    if (statusHint) {
      setStatus({ sharing: false, error: statusHint });
    }
    return tryMainCaptureFallback(generation);
  }
  if (statusHint) {
    setStatus({ sharing: false, error: statusHint });
  }
  showPreview();
  showWindowSidebar(true);
  await window.vdisplayShare.ensureCaptureFocus().catch(() => {});
  try {
    if (!navigator.mediaDevices || typeof navigator.mediaDevices.getDisplayMedia !== "function") {
      throw new Error(
        "getDisplayMedia unavailable in this Electron runtime; try restarting with VDISPLAY_ELECTRON_OZONE_PLATFORM=wayland or use the grid source picker",
      );
    }
    const media = await getDisplayMediaWithTimeout(
      {
        audio: false,
        video: {
          cursor: "always",
          frameRate: { ideal: 5, max: 15 },
        },
      },
      generation,
    );
    if (generation !== captureGeneration) {
      for (const track of media.getTracks()) {
        track.stop();
      }
      return null;
    }
    stream = media;
    video.srcObject = stream;
    await waitForVideoReady(video);
    if (generation !== captureGeneration) {
      return null;
    }
    if (!(await safePlay(video))) {
      return;
    }
    if (generation !== captureGeneration) {
      return null;
    }
    for (const track of stream.getVideoTracks()) {
      track.addEventListener("ended", stopCapture);
    }
    frameTimer = setInterval(publishFrame, 500);
    publishFrame();
    await refreshWindowSidebar();
    startWindowRefresh();
    setStatus({ sharing: true, error: "" });
    return stream;
  } catch (error) {
    const message = String(error && error.message ? error.message : error);
    const fallback =
      config.mainCaptureFallbackEnabled || isWaylandRuntime()
        ? await tryMainCaptureFallback(generation)
        : {
            ok: false,
            error:
              "desktopCapturer fallback is disabled; keep this Electron window focused and approve the GNOME Screen Share dialog.",
          };
    if (fallback && fallback.ok) {
      return { mainCapture: true };
    }
    if (message.includes("timed out")) {
      const detail =
        (fallback && fallback.error) ||
        "Click this Electron window so it has focus, then retry Share.";
      throw new Error(`${message}. ${detail}`);
    }
    if (message === "Not supported" || message.includes("Not supported")) {
      const detail =
        (fallback && fallback.error) ||
        "Click this Electron window so it has focus, enable GNOME Settings → Privacy → Screen Recording for Electron, then retry Share.";
      throw new Error(
        `getDisplayMedia is not supported (ozone-platform=${(config && config.ozonePlatform) || "unknown"}). ${detail}`,
      );
    }
    throw error;
  } finally {
    await window.vdisplayShare.restoreCaptureHandler();
  }
}

async function startCaptureFromSource(source) {
  stopCapture();
  const generation = captureGeneration;
  try {
    if (source.displayId) {
      sharedDisplayId = String(source.displayId);
      sharedDisplayLabel = source.displayLabel || source.sourceName;
      refreshWindowSidebar().catch(() => {});
    }
    setStatus({ sharing: false, error: `starting ${source.kind}: ${source.sourceName}` });
    const selected = await window.vdisplayShare.selectSource({
      sourceId: source.sourceId,
      sourceName: source.sourceName,
      displayId: source.displayId || "",
      displayLabel: source.displayLabel || source.sourceName,
    });
    if (!selected || !selected.ok) {
      throw new Error((selected && selected.error) || "source selection failed");
    }
    sharedDisplayId = selected.sharedDisplayId || sharedDisplayId;
    sharedDisplayLabel = selected.sharedDisplayLabel || sharedDisplayLabel;
    activeSourceId = selected.sourceId || source.sourceId;
    activeSourceName = source.sourceName || selected.sourceId || "";
    const started = await beginDisplayMediaCapture(generation, {
      statusHint: selected.hint || "",
    });
    if (!started) {
      const fallback = await tryMainCaptureFallback(generation);
      if (fallback && fallback.ok) {
        return;
      }
      return;
    }
  } catch (error) {
    await window.vdisplayShare.restoreCaptureHandler().catch(() => {});
    if (generation !== captureGeneration) {
      return;
    }
    stream = null;
    activeSourceId = "";
    showScreenPicker();
    setStatus({ sharing: false, error: String(error && error.message ? error.message : error) });
  }
}

async function startCaptureWithSystemPicker() {
  stopCapture();
  const generation = captureGeneration;
  try {
    // On x11, open the GNOME picker immediately — do not block on a 15s desktopCapturer timeout first.
    if (!isWaylandRuntime()) {
      await window.vdisplayShare.prepareSystemPicker();
      try {
        const started = await beginDisplayMediaCapture(generation, {
          statusHint: "waiting for GNOME Screen Share dialog — keep this window focused",
        });
        if (started) {
          return;
        }
      } catch (pickerError) {
        if (generation !== captureGeneration) {
          return;
        }
      }
    }
    const mainFirst = await tryMainCaptureFallback(generation);
    if (mainFirst && mainFirst.ok) {
      return;
    }
    if (isWaylandRuntime()) {
      throw new Error(
        (mainFirst && mainFirst.error) ||
          "Wayland capture failed. Enable Settings → Privacy → Screen Recording for Electron/vdisplay share, keep this window focused, wait up to 15s, then retry. Or restart with VDISPLAY_ELECTRON_OZONE_PLATFORM=x11.",
      );
    }
    throw new Error(
      (mainFirst && mainFirst.error) ||
        "capture failed — enable Settings → Privacy → Screen Recording for Electron/vdisplay share, keep this window focused, then retry Share",
    );
  } catch (error) {
    await window.vdisplayShare.restoreCaptureHandler().catch(() => {});
    if (generation !== captureGeneration) {
      return;
    }
    stream = null;
    showScreenPicker();
    setStatus({ sharing: false, error: String(error && error.message ? error.message : error) });
  }
}

function publishFrame() {
  if (!stream || !video.videoWidth || !video.videoHeight) {
    return;
  }
  if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  }
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const [track] = stream.getVideoTracks();
  const settings = track ? track.getSettings() : {};
  window.vdisplayShare.frame({
    dataUrl: canvas.toDataURL("image/png"),
    width: canvas.width,
    height: canvas.height,
    ts: Date.now(),
    displaySurface: settings.displaySurface || "",
    displayId: sharedDisplayId,
    displayLabel: sharedDisplayLabel,
    sourceId: activeSourceId,
    sourceName: activeSourceName,
  });
}

async function autoStartPreferredCapture(screens) {
  if (!config.autoStartCapture || stream) {
    return false;
  }
  if (!sharedDisplayId && !config.preferredBounds) {
    return false;
  }
  const screenSource = (screens || []).find(
    (item) => String(item.display_id || "") === String(sharedDisplayId),
  );
  setStatus({
    sharing: false,
    error: `auto-starting capture on ${sharedDisplayLabel || sharedDisplayId || config.bridgeSource || "bridge"} — approve GNOME Share`,
  });
  if (screenSource && screenSource.fallback) {
    await startCaptureWithSystemPicker();
    return true;
  }
  if (screenSource) {
    await startCaptureFromSource({
      sourceId: screenSource.id,
      sourceName: screenSource.name,
      displayId: screenSource.display_id,
      displayLabel: screenSource.display_label || screenSource.name,
      kind: "screen",
    });
    return true;
  }
  await startCaptureWithSystemPicker();
  return true;
}

async function handleShareClick() {
  if (config.useSystemPicker || !sharedDisplayId) {
    await startCaptureWithSystemPicker();
    return;
  }
  showScreenPicker();
  await refreshScreenPicker();
  await refreshWindowSidebar();
  setStatus({ sharing: false, error: "choose a monitor from the grid, or click Share target for GNOME picker" });
}

startButton.addEventListener("click", handleShareClick);
stopButton.addEventListener("click", stopCapture);
refreshScreensButton.addEventListener("click", () => {
  refreshScreenPicker().catch((error) => {
    setStatus({ sharing: false, error: String(error) });
  });
});
refreshWindowsButton.addEventListener("click", () => {
  refreshWindowSidebar().catch((error) => {
    setStatus({ error: String(error) });
  });
});
compactButton.addEventListener("click", async () => {
  const payload = await window.vdisplayShare.setMode("compact");
  applyMode(payload.mode);
});
fullButton.addEventListener("click", async () => {
  const payload = await window.vdisplayShare.setMode("full");
  applyMode(payload.mode);
});
trayButton.addEventListener("click", () => window.vdisplayShare.minimizeToTray());
webButton.addEventListener("click", () => window.vdisplayShare.openWeb());
exportLogsButton.addEventListener("click", async () => {
  try {
    const payload = await window.vdisplayShare.exportLogs();
    setStatus({ error: `debug logs exported: ${payload.path}` });
  } catch (error) {
    setStatus({ error: `debug log export failed: ${String(error && error.message ? error.message : error)}` });
  }
});
alwaysOnTopInput.addEventListener("change", async () => {
  const payload = await window.vdisplayShare.setAlwaysOnTop(alwaysOnTopInput.checked);
  alwaysOnTopInput.checked = payload.alwaysOnTop;
});
targetInput.addEventListener("change", async () => {
  const payload = await window.vdisplayShare.setTarget(targetInput.value);
  targetInput.value = payload.targetLabel;
  setStatus({ targetLabel: payload.targetLabel });
});

window.vdisplayShare.onMainCaptureFrame(() => {
  const previewFrame = document.getElementById("previewFrame");
  if (!previewFrame || previewFrame.classList.contains("hidden")) {
    return;
  }
  const base = (config && config.url) || "http://127.0.0.1:8799";
  previewFrame.src = `${base}/frame.png?t=${Date.now()}`;
});

window.vdisplayShare.onMode((payload) => {
  if (payload && payload.mode) {
    applyMode(payload.mode);
  }
  if (payload && typeof payload.alwaysOnTop === "boolean") {
    alwaysOnTopInput.checked = payload.alwaysOnTop;
  }
});

window.vdisplayShare.config().then(async (payload) => {
  config = payload;
  targetInput.value = payload.targetLabel || "";
  alwaysOnTopInput.checked = Boolean(payload.alwaysOnTop);
  sharedDisplayId = payload.sharedDisplayId || "";
  sharedDisplayLabel = payload.sharedDisplayLabel || "";
  applyMode(payload.mode);
  if (payload.mode !== "compact") {
    await window.vdisplayShare.setMode("full");
    applyMode("full");
  }
  showScreenPicker();
  showWindowSidebar(true);
  ensureDisplaySelection(payload.displays);
  renderScreenGrid(displaysToScreenCards(payload.displays));
  setStatus({
    sharing: false,
    error: `found ${(payload.displays || []).length} monitor(s); loading previews...`,
  });
  try {
    const listed = await refreshScreenPicker();
    await refreshWindowSidebar();
    startWindowRefresh();
    let hint = "click KEB 15.6\" below or Share target — keep this Electron window focused";
    if (config.preferredBounds && sharedDisplayLabel) {
      hint = `auto-selected ${sharedDisplayLabel} for ${config.bridgeSource || "bridge"} — click it, approve GNOME Share, keep Electron focused`;
    } else if (listed.usingFallback) {
      hint =
        "click a monitor — the GNOME share dialog will open (choose the same screen and click Share)";
    } else if (listed.sourcesError) {
      hint = `previews partial: ${listed.sourcesError}. ${hint}`;
    }
    setStatus({ sharing: false, error: hint });
    if (config.autoStartCapture) {
      await autoStartPreferredCapture(listed.screens || displaysToScreenCards(listed.displays));
    }
  } catch (error) {
    setStatus({
      sharing: false,
      error: `${error}. Monitors are listed without previews — click one to try capture.`,
    });
  }
}).catch((error) => {
  setStatus({ sharing: false, error: `startup failed: ${error}` });
});

window.vdisplayShare.onAutoStartCapture(async () => {
  try {
    const listed = await refreshScreenPicker();
    await autoStartPreferredCapture(listed.screens || displaysToScreenCards(listed.displays));
  } catch (error) {
    setStatus({ sharing: false, error: `auto-start failed: ${String(error && error.message ? error.message : error)}` });
  }
});

"use strict";

const startButton = document.getElementById("start");
const stopButton = document.getElementById("stop");
const compactButton = document.getElementById("compact");
const fullButton = document.getElementById("full");
const trayButton = document.getElementById("tray");
const webButton = document.getElementById("web");
const exportLogsButton = document.getElementById("exportLogs");
const copyStatusButton = document.getElementById("copyStatus");
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
const openSettingsButton = document.getElementById("openSettings");
const grantAccessButton = document.getElementById("grantAccess");

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
let captureActive = false;
let captureInFlight = false;
let lastStatusJson = "";
let lastStatusHint = "";
let lastCaptureFailureAt = 0;
let lastCaptureFailureMessage = "";

function captureRetryCooldownMs() {
  const value = Number((config && config.captureRetryCooldownMs) || 60000);
  return Number.isFinite(value) ? Math.max(0, Math.min(300000, value)) : 60000;
}

function captureRetryWaitMs() {
  if (!lastCaptureFailureAt) {
    return 0;
  }
  return Math.max(0, captureRetryCooldownMs() - (Date.now() - lastCaptureFailureAt));
}

function markCaptureFailure(message) {
  lastCaptureFailureAt = Date.now();
  lastCaptureFailureMessage = String(message || "Monitor capture failed");
}

function clearCaptureFailure() {
  lastCaptureFailureAt = 0;
  lastCaptureFailureMessage = "";
}

function logRenderer(level, message, details = null) {
  if (window.vdisplayShare && typeof window.vdisplayShare.log === "function") {
    window.vdisplayShare.log(level, message, details);
  }
}

function truncateText(value, limit = 160) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  return text.length > limit ? `${text.slice(0, limit)}...` : text;
}

function describeElement(element) {
  if (!element || element === document || element === window) {
    return {};
  }
  const rect = typeof element.getBoundingClientRect === "function"
    ? element.getBoundingClientRect()
    : null;
  return {
    tag: String(element.tagName || "").toLowerCase(),
    id: element.id || "",
    className: typeof element.className === "string" ? truncateText(element.className, 120) : "",
    role: element.getAttribute ? element.getAttribute("role") || "" : "",
    type: element.getAttribute ? element.getAttribute("type") || "" : "",
    ariaLabel: element.getAttribute ? element.getAttribute("aria-label") || "" : "",
    title: element.getAttribute ? element.getAttribute("title") || "" : "",
    text: truncateText(element.innerText || element.textContent || "", 160),
    bounds: rect
      ? {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        }
      : null,
  };
}

function userActionContext(extra = {}) {
  return {
    at_ms: Date.now(),
    window: {
      width: window.innerWidth,
      height: window.innerHeight,
      devicePixelRatio: window.devicePixelRatio || 1,
    },
    state: {
      sharing: currentSharingState(),
      targetLabel: targetInput ? targetInput.value || "" : "",
      sharedDisplayId,
      sharedDisplayLabel,
      activeSourceId,
      activeSourceName,
      captureInFlight,
    },
    ...extra,
  };
}

function logUserAction(action, details = {}) {
  logRenderer("user-action", action, userActionContext(details));
}

document.addEventListener(
  "click",
  (event) => {
    logUserAction("ui.click", {
      pointer: {
        clientX: Math.round(event.clientX),
        clientY: Math.round(event.clientY),
        pageX: Math.round(event.pageX),
        pageY: Math.round(event.pageY),
        button: event.button,
        buttons: event.buttons,
        altKey: event.altKey,
        ctrlKey: event.ctrlKey,
        metaKey: event.metaKey,
        shiftKey: event.shiftKey,
      },
      target: describeElement(event.target),
    });
  },
  true,
);

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

function currentSharingState() {
  return captureActive || Boolean(stream);
}

function buildStatusDocument(payload = {}) {
  const next = {
    sharing: currentSharingState(),
    targetLabel: targetInput.value || config.targetLabel,
    sharedDisplayId,
    sharedDisplayLabel,
    activeSourceId,
    activeSourceName,
    ...payload,
  };
  const doc = {
    broker: config.url,
    agent: config.agentUrl || null,
    ozonePlatform: config.ozonePlatform || "",
    useSystemPicker: Boolean(config.useSystemPicker),
    bridgePush: Boolean(config.bridgePush),
    bridgeSource: config.bridgeSource || "",
    sharing: next.sharing,
    targetLabel: next.targetLabel,
    sharedDisplayId: next.sharedDisplayId,
    sharedDisplayLabel: next.sharedDisplayLabel,
    activeSourceId: next.activeSourceId,
    activeSourceName: next.activeSourceName,
  };
  if (next.hint) {
    doc.hint = String(next.hint);
  } else if (lastStatusHint && !next.error && !next.notice) {
    doc.hint = lastStatusHint;
  }
  if (next.error) {
    doc.error = String(next.error);
  }
  if (next.notice) {
    doc.notice = String(next.notice);
  }
  return doc;
}

function setStatus(payload) {
  const normalizedPayload = { ...(payload || {}) };
  if (
    !Object.prototype.hasOwnProperty.call(normalizedPayload, "error") &&
    (Object.prototype.hasOwnProperty.call(normalizedPayload, "hint") ||
      Object.prototype.hasOwnProperty.call(normalizedPayload, "notice"))
  ) {
    normalizedPayload.error = "";
  }
  const next = {
    sharing: currentSharingState(),
    targetLabel: targetInput.value || config.targetLabel,
    sharedDisplayId,
    sharedDisplayLabel,
    activeSourceId,
    activeSourceName,
    ...normalizedPayload,
  };
  if (typeof normalizedPayload.sharing === "boolean") {
    captureActive = normalizedPayload.sharing;
  }
  if (next.hint) {
    lastStatusHint = String(next.hint);
  } else if (typeof next.error === "string" && next.error && !next.notice) {
    lastStatusHint = String(next.error);
  }
  window.vdisplayShare.status(next);
  badgeEl.textContent = `${next.sharing ? "sharing" : "idle"}: ${next.targetLabel || "target"}`;
  if (startButton) {
    startButton.disabled = Boolean(captureInFlight || next.sharing);
    startButton.textContent = next.sharing
      ? "Sharing active"
      : captureInFlight
        ? "Starting..."
        : "Share monitor";
  }
  lastStatusJson = JSON.stringify(buildStatusDocument(next), null, 2);
  statusEl.textContent = lastStatusJson;
}

async function copyStatusJson() {
  const text = lastStatusJson || statusEl.textContent || "";
  if (!text.trim()) {
    setStatus({ error: "nothing to copy yet" });
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    setStatus({ notice: "status JSON copied to clipboard", hint: lastStatusHint || undefined });
  } catch (error) {
    setStatus({
      error: `clipboard copy failed: ${String(error && error.message ? error.message : error)}`,
      hint: lastStatusHint || undefined,
    });
  }
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

function selectDisplay(display, reason = "auto") {
  const id = displayIdOf(display);
  if (!id) {
    return "";
  }
  sharedDisplayId = id;
  sharedDisplayLabel = displayLabelOf(display);
  logUserAction(reason === "user" ? "monitor.user_select" : "monitor.auto_select", {
    reason,
    displayId: sharedDisplayId,
    displayLabel: sharedDisplayLabel,
    sourceId: display.id || "",
    sourceName: display.name || "",
    primary: Boolean(display.primary),
    fallback: Boolean(display.fallback),
    size: display.size || null,
  });
  return sharedDisplayId;
}

function sourcePreviewsEnabled() {
  return Boolean(config && config.allowSourcePreviews);
}

function normalizedText(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function automationTargetMatchesDesired(sourceName, targetLabel) {
  const source = normalizedText(sourceName);
  const target = normalizedText(targetLabel);
  if (!target || target === "automation target") {
    return true;
  }
  if (!source) {
    return false;
  }
  if (target.includes("jetbrains") || target.includes("pycharm") || target.includes("idea")) {
    if (source.includes("toolbox")) {
      return false;
    }
    return [
      "pycharm",
      "intellij",
      "idea",
      "webstorm",
      "goland",
      "clion",
      "rider",
      "rubymine",
      "phpstorm",
      "datagrip",
      "dataspell",
      "android studio",
    ].some((token) => source.includes(token));
  }
  return source.includes(target);
}

async function selectAutomationTarget(source) {
  const sourceId = String(source.sourceId || source.id || "");
  const sourceName = String(source.sourceName || source.name || sourceId || "");
  if (!sourceId && !sourceName) {
    return null;
  }
  const desiredTargetLabel = String((targetInput && targetInput.value) || config.targetLabel || "").trim();
  if (!automationTargetMatchesDesired(sourceName, desiredTargetLabel)) {
    const message = `window "${sourceName || sourceId}" does not match automation target "${desiredTargetLabel || "target"}"`;
    setStatus({
      sharing: captureActive || Boolean(stream),
      targetLabel: desiredTargetLabel,
      error: message,
      hint: "Change the target label first if you really want to automate this window.",
    });
    logUserAction("automation_target.reject", {
      sourceId,
      sourceName,
      targetLabel: desiredTargetLabel,
      reason: "target_mismatch",
    });
    return { ok: false, rejected: true, error: message };
  }
  const payload = await window.vdisplayShare.selectAutomationTarget({
    sourceId,
    sourceName,
    displayId: source.displayId || sharedDisplayId,
    displayLabel: source.displayLabel || sharedDisplayLabel,
    targetLabel: desiredTargetLabel,
  });
  logUserAction("automation_target.select", {
    sourceId,
    sourceName,
    displayId: source.displayId || sharedDisplayId,
    displayLabel: source.displayLabel || sharedDisplayLabel,
    result: payload,
  });
  activeSourceId = payload.activeSourceId || sourceId;
  activeSourceName = payload.activeSourceName || sourceName;
  if (payload.targetLabel) {
    targetInput.value = payload.targetLabel;
  }
  setStatus({
    sharing: captureActive || Boolean(stream),
    targetLabel: payload.targetLabel || desiredTargetLabel,
    error: captureActive || stream
      ? `automation target selected: ${activeSourceName || activeSourceId}`
      : `automation target selected: ${activeSourceName || activeSourceId}; share the monitor to enable capture`,
  });
  refreshWindowSidebar().catch(() => {});
  return payload;
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
      return selectDisplay(preferredDisplay, "preferred");
    }
    return sharedDisplayId;
  }
  if (sharedDisplayId) {
    return sharedDisplayId;
  }
  const selected = list.find((display) => display && display.primary) || list[0];
  return selectDisplay(selected, "default");
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
      selectDisplay(screenSource, "user");
      renderScreenGrid(screens);
      refreshWindowSidebar().catch((error) => {
        setStatus({ error: String(error) });
      });
      setStatus({
        sharing: captureActive || Boolean(stream),
        hint: `Monitor ${sharedDisplayLabel || sharedDisplayId} selected. Click Share monitor once to request whole-screen access.`,
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
      if (!captureActive && !stream) {
        setStatus({
          sharing: false,
          error:
            "Window selected as automation target. Share the monitor first (grid or Share monitor) to enable live capture.",
        });
      }
      selectAutomationTarget({
        sourceId: windowSource.id,
        sourceName: windowSource.name,
        displayId: sharedDisplayId,
        displayLabel: sharedDisplayLabel,
      }).catch((error) => {
        setStatus({ sharing: captureActive || Boolean(stream), error: String(error && error.message ? error.message : error) });
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
  if (!sourcePreviewsEnabled()) {
    const screens = displaysToScreenCards(config.displays || []);
    const displays = config.displays || screens;
    ensureDisplaySelection(displays);
    renderScreenGrid(screens);
    return {
      ok: true,
      passive: true,
      usingFallback: true,
      screens,
      displays,
      sourcesError: "",
    };
  }
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
  if (!sourcePreviewsEnabled()) {
    renderWindowList([], true);
    sidebarMeta.textContent = sharedDisplayId
      ? `Monitor ${sharedDisplayLabel || sharedDisplayId} selected. Window previews disabled (passive mode) to avoid GNOME permission prompts.`
      : "Choose a monitor, then share it. Window previews stay disabled unless VDISPLAY_ELECTRON_ALLOW_SOURCE_PREVIEWS=1.";
    return {
      ok: true,
      passive: true,
      skipped: true,
      windows: [],
    };
  }
  if (!captureActive && !stream) {
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
  if (!sourcePreviewsEnabled()) {
    return;
  }
  if (!captureActive && !stream) {
    return;
  }
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
  logUserAction("capture.stop", {
    hadStream: Boolean(stream),
    captureActive,
  });
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
  captureActive = false;
  showScreenPicker();
  showWindowSidebar(Boolean(sharedDisplayId));
  setStatus({ sharing: false, error: "" });
}

function isWaylandRuntime() {
  return Boolean(config && config.ozonePlatform === "wayland");
}

function prefersMainProcessMonitorCapture() {
  return Boolean(config.mainCaptureFallbackEnabled) && !config.useSystemPicker;
}

async function tryMainCaptureFallback(generation, { monitorOnly = false, force = false } = {}) {
  logUserAction("capture.main_process.request", {
    generation,
    monitorOnly,
    force,
    displayId: sharedDisplayId,
    displayLabel: sharedDisplayLabel,
    activeSourceId,
    activeSourceName,
  });
  setStatus({
    sharing: false,
    hint:
      "Requesting monitor capture — approve GNOME once if prompted (whole screen, not an app). Keep Electron focused.",
  });
  const result = await window.vdisplayShare.startMainCapture({
    displayId: sharedDisplayId,
    displayLabel: sharedDisplayLabel,
    sourceId: monitorOnly ? "" : activeSourceId,
    sourceName: monitorOnly ? "" : activeSourceName,
    monitorOnly,
    force: Boolean(force),
  });
  logUserAction(result && result.ok ? "capture.main_process.ok" : "capture.main_process.failed", {
    generation,
    monitorOnly,
    force,
    result,
  });
  if (generation !== captureGeneration) {
    return { ok: false, cancelled: true };
  }
  if (result && result.ok) {
    showPreview();
    showWindowSidebar(true);
    startMainPreviewPolling();
    startWindowRefresh();
    setStatus({
      sharing: true,
      error: "",
      captureMode: result.captureMode || "main-desktopCapturer",
    });
    return result;
  }
  return result || { ok: false, error: "main-process capture failed" };
}

async function beginDisplayMediaCapture(generation, { statusHint = "", monitorOnly = false } = {}) {
  logUserAction("capture.display_media.begin", {
    generation,
    monitorOnly,
    statusHint,
    ozonePlatform: config.ozonePlatform || "",
    useSystemPicker: Boolean(config.useSystemPicker),
  });
  if (isWaylandRuntime() || monitorOnly || prefersMainProcessMonitorCapture()) {
    if (statusHint) {
      setStatus({ sharing: false, hint: statusHint });
    }
    return tryMainCaptureFallback(generation, { monitorOnly: true });
  }
  if (statusHint) {
    setStatus({ sharing: false, hint: statusHint });
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
          displaySurface: "monitor",
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
    if (prefersMainProcessMonitorCapture()) {
      throw error;
    }
    const fallback =
      config.mainCaptureFallbackEnabled || isWaylandRuntime()
        ? await tryMainCaptureFallback(generation, { monitorOnly })
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
  logUserAction("capture.source.start", { source });
  if (source.kind && source.kind !== "screen") {
    await selectAutomationTarget(source);
    return;
  }
  if (prefersMainProcessMonitorCapture()) {
    if (source.displayId) {
      sharedDisplayId = String(source.displayId);
      sharedDisplayLabel = source.displayLabel || source.sourceName;
      refreshWindowSidebar().catch(() => {});
    }
    const generation = captureGeneration;
    await tryMainCaptureFallback(generation, { monitorOnly: true });
    return;
  }
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
      monitorOnly: true,
    });
    if (!started) {
      const fallback = await tryMainCaptureFallback(generation, { monitorOnly: true });
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
  logUserAction("capture.system_picker.start", {
    displayId: sharedDisplayId,
    displayLabel: sharedDisplayLabel,
  });
  stopCapture();
  const generation = captureGeneration;
  try {
    // On x11, open the GNOME picker immediately — do not block on a 15s desktopCapturer timeout first.
    if (!isWaylandRuntime()) {
      await window.vdisplayShare.prepareSystemPicker();
      try {
        const started = await beginDisplayMediaCapture(generation, {
          statusHint: "waiting for GNOME Screen Share dialog — keep this window focused",
          monitorOnly: true,
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
    const mainFirst = await tryMainCaptureFallback(generation, { monitorOnly: true, force: true });
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

async function startMonitorCaptureForSelectedDisplay() {
  logUserAction("capture.monitor.start_click", {
    displayId: sharedDisplayId,
    displayLabel: sharedDisplayLabel,
    captureInFlight,
    captureActive,
    hasStream: Boolean(stream),
    retryWaitMs: captureRetryWaitMs(),
  });
  if (captureInFlight) {
    setStatus({
      notice: "Monitor capture request already in progress; ignoring duplicate click",
      hint: lastStatusHint || undefined,
    });
    return;
  }
  if (captureActive || stream) {
    setStatus({ notice: "Monitor capture already active", hint: lastStatusHint || undefined });
    return;
  }
  const waitMs = captureRetryWaitMs();
  if (waitMs > 0) {
    setStatus({
      sharing: false,
      notice: `Capture retry blocked for ${Math.ceil(waitMs / 1000)}s to avoid repeated GNOME permission prompts`,
      hint:
        lastCaptureFailureMessage ||
        "Grant Screen Recording for Electron/vdisplay share once, then retry Share monitor.",
    });
    return;
  }
  captureInFlight = true;
  try {
    stopCapture();
    const generation = captureGeneration;
    if (!sharedDisplayId) {
      showScreenPicker();
      await refreshScreenPicker().catch(() => {});
      setStatus({
        sharing: false,
        hint: "Choose a monitor from the grid first, then click Share monitor.",
      });
      return;
    }
    setStatus({
      sharing: false,
      hint: `Sharing monitor ${sharedDisplayLabel || sharedDisplayId} (whole screen) — one GNOME prompt at most; keep Electron focused`,
    });
    if (prefersMainProcessMonitorCapture()) {
      const mainFirst = await tryMainCaptureFallback(generation, { monitorOnly: true, force: true });
      if (mainFirst && mainFirst.ok) {
        clearCaptureFailure();
        await refreshWindowSidebar().catch(() => {});
      } else if (!(mainFirst && mainFirst.cooldown)) {
        markCaptureFailure(
          (mainFirst && mainFirst.error) ||
            "Monitor capture failed — grant GNOME Screen Recording for vdisplay share or Electron, then retry Share monitor",
        );
        setStatus({
          sharing: false,
          error: lastCaptureFailureMessage,
          hint:
            "Use Screen Recording settings or Grant via GNOME once, then click Share monitor again (whole screen, not an app).",
        });
      }
      return;
    }
    let screenSource = null;
    if (sourcePreviewsEnabled()) {
      try {
        const listed = await window.vdisplayShare.listSources(null, false);
        screenSource = (listed.screens || []).find(
          (item) => String(item.display_id || "") === String(sharedDisplayId),
        );
      } catch {
        screenSource = null;
      }
    }
    if (screenSource && !screenSource.fallback) {
      await startCaptureFromSource({
        sourceId: screenSource.id,
        sourceName: screenSource.name,
        displayId: screenSource.display_id,
        displayLabel: screenSource.display_label || screenSource.name,
        kind: "screen",
      });
      clearCaptureFailure();
      return;
    }
    const mainFirst = await tryMainCaptureFallback(generation, { monitorOnly: true, force: true });
    if (mainFirst && mainFirst.ok) {
      clearCaptureFailure();
      await refreshWindowSidebar().catch(() => {});
      return;
    }
    if (mainFirst && mainFirst.cooldown) {
      setStatus({
        sharing: false,
        error: mainFirst.error || "Capture cooldown active",
        hint: lastStatusHint || undefined,
      });
      return;
    }
    if (config.useSystemPicker) {
      await startCaptureWithSystemPicker();
      return;
    }
    const failureMessage =
      (mainFirst && mainFirst.error) ||
      "Monitor capture failed — grant GNOME Screen Recording for Electron once, then retry Share monitor";
    markCaptureFailure(failureMessage);
    setStatus({
      sharing: false,
      error: failureMessage,
      hint: lastStatusHint || undefined,
    });
  } catch (error) {
    const message = String(error && error.message ? error.message : error);
    markCaptureFailure(message);
    setStatus({
      sharing: false,
      error: message,
      hint: lastStatusHint || undefined,
    });
  } finally {
    captureInFlight = false;
  }
}

async function autoStartPreferredCapture(screens) {
  if (!config.autoStartCapture || stream || captureActive) {
    return false;
  }
  if (!sharedDisplayId && !config.preferredBounds) {
    return false;
  }
  setStatus({
    sharing: false,
    hint: `Auto-starting monitor ${sharedDisplayLabel || sharedDisplayId || config.bridgeSource || "bridge"} — whole screen only`,
  });
  await startMonitorCaptureForSelectedDisplay();
  return captureActive || Boolean(stream);
}

async function handleShareClick() {
  logUserAction("button.share_monitor");
  await startMonitorCaptureForSelectedDisplay();
}

async function handleGrantAccessClick() {
  logUserAction("button.grant_via_gnome");
  if (captureInFlight) {
    return;
  }
  captureInFlight = true;
  try {
    setStatus({
      sharing: false,
      hint: "Opening GNOME screen-share dialog — choose the whole monitor, not a single app",
    });
    await startCaptureWithSystemPicker();
  } finally {
    captureInFlight = false;
  }
}

async function handleOpenSettingsClick() {
  logUserAction("button.open_screen_recording_settings");
  const payload = await window.vdisplayShare.openScreenRecordingSettings();
  setStatus({
    sharing: currentSharingState(),
    notice: payload && payload.ok ? "Opened Screen Recording settings" : "Could not open settings",
    hint:
      (payload && payload.hint) ||
      "Enable vdisplay share and/or Electron under Privacy → Screen Recording, then click Share monitor",
    error: payload && payload.ok ? "" : (payload && payload.error) || "settings open failed",
  });
}

startButton.addEventListener("click", handleShareClick);
if (openSettingsButton) {
  openSettingsButton.addEventListener("click", () => {
    handleOpenSettingsClick().catch((error) => {
      setStatus({ error: String(error && error.message ? error.message : error) });
    });
  });
}
if (grantAccessButton) {
  grantAccessButton.addEventListener("click", () => {
    handleGrantAccessClick().catch((error) => {
      setStatus({ error: String(error && error.message ? error.message : error) });
    });
  });
}
stopButton.addEventListener("click", () => {
  logUserAction("button.stop");
  stopCapture();
});
refreshScreensButton.addEventListener("click", () => {
  logUserAction("button.refresh_monitors");
  refreshScreenPicker().catch((error) => {
    setStatus({ sharing: false, error: String(error) });
  });
});
refreshWindowsButton.addEventListener("click", () => {
  logUserAction("button.refresh_windows");
  refreshWindowSidebar().catch((error) => {
    setStatus({ error: String(error) });
  });
});
compactButton.addEventListener("click", async () => {
  logUserAction("button.compact_mode");
  const payload = await window.vdisplayShare.setMode("compact");
  applyMode(payload.mode);
});
fullButton.addEventListener("click", async () => {
  logUserAction("button.full_mode");
  const payload = await window.vdisplayShare.setMode("full");
  applyMode(payload.mode);
});
trayButton.addEventListener("click", () => {
  logUserAction("button.tray");
  window.vdisplayShare.minimizeToTray();
});
webButton.addEventListener("click", () => {
  logUserAction("button.web");
  window.vdisplayShare.openWeb();
});
exportLogsButton.addEventListener("click", async () => {
  logUserAction("button.export_logs");
  try {
    const payload = await window.vdisplayShare.exportLogs();
    setStatus({
      notice: `debug logs exported: ${payload.path}`,
      hint: lastStatusHint || undefined,
    });
  } catch (error) {
    setStatus({
      error: `debug log export failed: ${String(error && error.message ? error.message : error)}`,
      hint: lastStatusHint || undefined,
    });
  }
});
copyStatusButton.addEventListener("click", () => {
  logUserAction("button.copy_status");
  copyStatusJson().catch((error) => {
    setStatus({
      error: `copy failed: ${String(error && error.message ? error.message : error)}`,
      hint: lastStatusHint || undefined,
    });
  });
});
alwaysOnTopInput.addEventListener("change", async () => {
  logUserAction("toggle.always_on_top", { checked: Boolean(alwaysOnTopInput.checked) });
  const payload = await window.vdisplayShare.setAlwaysOnTop(alwaysOnTopInput.checked);
  alwaysOnTopInput.checked = payload.alwaysOnTop;
});
targetInput.addEventListener("change", async () => {
  logUserAction("target_label.change", { targetLabel: targetInput.value || "" });
  const payload = await window.vdisplayShare.setTarget(targetInput.value);
  targetInput.value = payload.targetLabel;
  setStatus({ targetLabel: payload.targetLabel });
});

window.vdisplayShare.onCaptureActive((payload) => {
  if (!payload || !payload.sharing) {
    return;
  }
  showPreview();
  showWindowSidebar(true);
  startMainPreviewPolling();
  startWindowRefresh();
  clearCaptureFailure();
  setStatus({
    sharing: true,
    error: "",
    captureMode: payload.captureMode || "main-desktopCapturer",
    hint: payload.autoResume
      ? `Monitor capture active for ${config.bridgeSource || "bridge"} — auto-resumed`
      : `Monitor capture active for ${config.bridgeSource || sharedDisplayLabel || "selected monitor"} — do not click Share monitor again unless you press Stop first`,
  });
});

window.vdisplayShare.onMainCaptureFrame((payload) => {
  if (payload && payload.ok && !captureActive && !stream) {
    showPreview();
    showWindowSidebar(true);
    startMainPreviewPolling();
    startWindowRefresh();
    clearCaptureFailure();
    setStatus({
      sharing: true,
      error: "",
      hint: `Monitor capture active for ${config.bridgeSource || sharedDisplayLabel || "selected monitor"} — do not click Share monitor again unless you press Stop first`,
    });
  }
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
    hint: sourcePreviewsEnabled()
      ? `found ${(payload.displays || []).length} monitor(s); loading previews...`
      : `found ${(payload.displays || []).length} monitor(s); passive mode — select monitor, then click Share monitor once`,
  });
  try {
    const listed = await refreshScreenPicker();
    await refreshWindowSidebar();
    let hint = "click a monitor below, then Share monitor — whole screen first; pick an app on the right after";
    if (config.preferredBounds && sharedDisplayLabel) {
      hint = `Monitor ${sharedDisplayLabel} selected for ${config.bridgeSource || "bridge"} — click Share monitor (whole screen), then optionally pick an app on the right`;
    } else if (listed.usingFallback) {
      hint =
        "Previews unavailable — click the monitor tile or Share monitor; GNOME may ask once for screen access (not a specific app)";
    } else if (listed.sourcesError) {
      hint = `Previews partial: ${listed.sourcesError}. ${hint}`;
    }
    setStatus({ sharing: false, hint });
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
  if (captureActive || stream) {
    return;
  }
  try {
    const listed = await refreshScreenPicker();
    await autoStartPreferredCapture(listed.screens || displaysToScreenCards(listed.displays));
  } catch (error) {
    setStatus({ sharing: false, error: `auto-start failed: ${String(error && error.message ? error.message : error)}` });
  }
});

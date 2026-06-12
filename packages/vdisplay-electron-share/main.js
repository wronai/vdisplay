"use strict";

const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const {
  app,
  BrowserWindow,
  clipboard,
  Menu,
  Tray,
  desktopCapturer,
  ipcMain,
  nativeImage,
  screen,
  session,
  shell,
} = require("electron");

if (process.platform === "linux") {
  app.setName("vdisplay share");
}

if (process.platform === "linux" && process.env.VDISPLAY_ELECTRON_DISABLE_GPU !== "0") {
  app.disableHardwareAcceleration();
  app.commandLine.appendSwitch("disable-gpu");
  app.commandLine.appendSwitch("disable-gpu-compositing");
  app.commandLine.appendSwitch("disable-gpu-sandbox");
}

const HOST = process.env.VDISPLAY_ELECTRON_SHARE_HOST || "127.0.0.1";
const PORT = Number(process.env.VDISPLAY_ELECTRON_SHARE_PORT || "8799");
const MANAGER_ORIGIN = `http://${HOST}:${PORT}`;
const INSTANCE_ID = process.env.VDISPLAY_ELECTRON_SHARE_INSTANCE || `share-${PORT}`;
const INITIAL_TARGET_LABEL = process.env.VDISPLAY_ELECTRON_TARGET_LABEL || "automation target";
const USE_SYSTEM_PICKER = process.env.VDISPLAY_ELECTRON_SHARE_USE_SYSTEM_PICKER === "1";
const CLOSE_QUITS = process.env.VDISPLAY_ELECTRON_CLOSE_QUITS === "1";
const AGENT_URL = (process.env.VDISPLAY_ELECTRON_AGENT_URL || process.env.VDISPLAY_AGENT_URL || "").replace(/\/+$/, "");
const AGENT_TOKEN = process.env.VDISPLAY_AGENT_TOKEN || "";
const BRIDGE_SOURCE = process.env.VDISPLAY_ELECTRON_BRIDGE_SOURCE || process.env.VDISPLAY_ELECTRON_SHARE_SOURCE || "HDMI-1";
const BRIDGE_PUSH = Boolean(AGENT_URL) && process.env.VDISPLAY_ELECTRON_BRIDGE_PUSH !== "0";
const AUTO_START_CAPTURE = process.env.VDISPLAY_ELECTRON_AUTO_START_CAPTURE !== "0";

function requestRendererAutoStartCapture() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return false;
  }
  mainWindow.webContents.send("share:auto-start-capture", {
    sharedDisplayId: rendererStatus.sharedDisplayId || "",
    bridgeSource: BRIDGE_SOURCE,
  });
  return true;
}

function handleShareStartRequest() {
  openManager();
  return ensureCaptureFocus({ lock: true }).then(() => {
    const sent = requestRendererAutoStartCapture();
    return {
      ok: true,
      triggered: sent,
      sharedDisplayId: rendererStatus.sharedDisplayId || "",
      sharedDisplayLabel: rendererStatus.sharedDisplayLabel || "",
      hint: sent
        ? "GNOME Screen Share dialog should open — approve the KEB/HDMI-1 monitor and keep Electron focused"
        : "Electron window not ready yet — open the manager and click the IDE monitor",
    };
  });
}

function preferredBoundsFromEnv() {
  const width = Number(process.env.VDISPLAY_ELECTRON_PREFERRED_DISPLAY_WIDTH || 0);
  const height = Number(process.env.VDISPLAY_ELECTRON_PREFERRED_DISPLAY_HEIGHT || 0);
  if (!width || !height) {
    return null;
  }
  return {
    x: Number(process.env.VDISPLAY_ELECTRON_PREFERRED_DISPLAY_X || 0),
    y: Number(process.env.VDISPLAY_ELECTRON_PREFERRED_DISPLAY_Y || 0),
    width,
    height,
    diagonal: Number(process.env.VDISPLAY_ELECTRON_PREFERRED_DISPLAY_DIAGONAL || 0),
  };
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

function resolvePreferredDisplay(displays = screen.getAllDisplays()) {
  const preferred = preferredBoundsFromEnv();
  if (!preferred) {
    return null;
  }
  return displays.find((item) => displayMatchesPreferred(item, preferred)) || null;
}
const OZONE_PLATFORM =
  process.env.VDISPLAY_ELECTRON_OZONE_PLATFORM ||
  (process.platform === "linux"
    ? process.env.WAYLAND_DISPLAY || String(process.env.XDG_SESSION_TYPE || "").toLowerCase() === "wayland"
      ? "wayland"
      : "x11"
    : "");
const IS_WAYLAND =
  Boolean(process.env.WAYLAND_DISPLAY) ||
  String(process.env.XDG_SESSION_TYPE || "").toLowerCase() === "wayland" ||
  OZONE_PLATFORM === "wayland";
const MAIN_CAPTURE_FALLBACK_ENABLED =
  IS_WAYLAND || process.env.VDISPLAY_ELECTRON_MAIN_CAPTURE_FALLBACK !== "0";

function mainCaptureAllowed() {
  if (MAIN_CAPTURE_FALLBACK_ENABLED) {
    return true;
  }
  // Renderer getDisplayMedia is unavailable on Electron+Wayland; desktopCapturer is the only path.
  return IS_WAYLAND;
}

if (process.env.VDISPLAY_ELECTRON_NO_SANDBOX !== "0") {
  app.commandLine.appendSwitch("no-sandbox");
}

if (OZONE_PLATFORM) {
  app.commandLine.appendSwitch("ozone-platform", OZONE_PLATFORM);
}

if (["127.0.0.1", "localhost", "::1"].includes(HOST)) {
  app.commandLine.appendSwitch("unsafely-treat-insecure-origin-as-secure", MANAGER_ORIGIN);
}

if (process.platform === "linux") {
  app.commandLine.appendSwitch("enable-features", "WebRTCPipeWireCapturer");
  app.commandLine.appendSwitch("enable-usermedia-screen-capturing");
}

if (process.env.VDISPLAY_ELECTRON_DISABLE_GPU !== "0") {
  app.disableHardwareAcceleration();
  app.commandLine.appendSwitch("disable-gpu");
  app.commandLine.appendSwitch("disable-gpu-compositing");
  app.commandLine.appendSwitch("disable-accelerated-video-decode");
  app.commandLine.appendSwitch("disable-accelerated-video-encode");
  app.commandLine.appendSwitch(
    "disable-features",
    "VaapiVideoDecoder,VaapiVideoEncoder,CanvasOopRasterization,UseChromeOSDirectVideoDecoder",
  );
}

let mainWindow = null;
let tray = null;
let lastFrame = null;
let lastFrameMeta = {};
let frameSeq = 0;
let bridgeId = null;
let bridgeLastOk = "";
let bridgeLastError = "";
let bridgeHeartbeatTimer = null;
let windowMode = process.env.VDISPLAY_ELECTRON_SHARE_MODE === "compact" ? "compact" : "full";
let alwaysOnTop = process.env.VDISPLAY_ELECTRON_ALWAYS_ON_TOP !== "0";
let rendererStatus = {
  sharing: false,
  error: "",
  targetLabel: INITIAL_TARGET_LABEL,
  sharedDisplayId: "",
  sharedDisplayLabel: "",
  activeSourceId: "",
  activeSourceName: "",
};

let pendingCaptureSourceId = null;
let mainCaptureTimer = null;
let mainCaptureState = null;
let captureFocusLock = false;

const THUMBNAIL_SIZE = { width: 320, height: 180 };
const MAIN_CAPTURE_THUMBNAIL_SIZE = {
  width: Number(process.env.VDISPLAY_ELECTRON_MAIN_CAPTURE_WIDTH || "2048"),
  height: Number(process.env.VDISPLAY_ELECTRON_MAIN_CAPTURE_HEIGHT || "1280"),
};
const GET_SOURCES_TIMEOUT_MS = Number(process.env.VDISPLAY_ELECTRON_GET_SOURCES_TIMEOUT_MS || "5000");
const MAIN_CAPTURE_TIMEOUT_MS = Number(process.env.VDISPLAY_ELECTRON_MAIN_CAPTURE_TIMEOUT_MS || "15000");
const APP_ICON_PATH = path.join(__dirname, "assets", "vdisplay-share.svg");
const SESSION_STARTED_AT = new Date();
const SESSION_LOG_LIMIT = Number(process.env.VDISPLAY_ELECTRON_SESSION_LOG_LIMIT || "2000");
const originalConsole = {
  log: console.log.bind(console),
  warn: console.warn.bind(console),
  error: console.error.bind(console),
};
let sessionLog = [];
let lastStatusLogKey = "";

function formatLogArg(value) {
  if (value instanceof Error) {
    return `${value.name}: ${value.message}${value.stack ? `\n${value.stack}` : ""}`;
  }
  if (typeof value === "string") {
    return value;
  }
  try {
    return JSON.stringify(redactDebugValue(value));
  } catch {
    return String(value);
  }
}

function redactDebugValue(value, depth = 0) {
  if (value == null || typeof value === "number" || typeof value === "boolean") {
    return value;
  }
  if (Buffer.isBuffer(value)) {
    return `<Buffer length=${value.length}>`;
  }
  if (value instanceof Error) {
    return { name: value.name, message: value.message, stack: value.stack || "" };
  }
  if (typeof value === "string") {
    if (value.startsWith("data:image/")) {
      return `<image data url omitted; chars=${value.length}>`;
    }
    return value.length > 4000 ? `${value.slice(0, 4000)}…<truncated chars=${value.length}>` : value;
  }
  if (depth > 6) {
    return "<max depth>";
  }
  if (Array.isArray(value)) {
    return value.map((item) => redactDebugValue(item, depth + 1));
  }
  if (typeof value === "object") {
    const output = {};
    for (const [key, item] of Object.entries(value)) {
      if (/token|secret|password|authorization|api[_-]?key/i.test(key)) {
        output[key] = item ? "<redacted>" : item;
      } else {
        output[key] = redactDebugValue(item, depth + 1);
      }
    }
    return output;
  }
  return String(value);
}

function logSession(level, message, details = null) {
  sessionLog.push({
    ts: new Date().toISOString(),
    level,
    message: String(message || ""),
    details: details == null ? null : redactDebugValue(details),
  });
  if (sessionLog.length > SESSION_LOG_LIMIT) {
    sessionLog = sessionLog.slice(sessionLog.length - SESSION_LOG_LIMIT);
  }
}

for (const level of ["log", "warn", "error"]) {
  console[level] = (...args) => {
    logSession(level, args.map(formatLogArg).join(" "));
    originalConsole[level](...args);
  };
}

function withTimeout(promise, ms, label = "operation") {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`${label} timed out after ${ms}ms`));
    }, ms);
    Promise.resolve(promise)
      .then((value) => {
        clearTimeout(timer);
        resolve(value);
      })
      .catch((error) => {
        clearTimeout(timer);
        reject(error);
      });
  });
}

function fallbackScreensFromDisplays(displays) {
  return displays.map((display) => ({
    id: `display:${display.id}`,
    name: display.label || `Display ${display.id}`,
    display_id: String(display.id),
    display_label: display.label || `Display ${display.id}`,
    thumbnail: null,
    primary: Boolean(display.primary),
    fallback: true,
    size: display.size,
    bounds: display.bounds,
  }));
}

async function getDesktopSources(options, label, timeoutMs = GET_SOURCES_TIMEOUT_MS) {
  return await withTimeout(
    desktopCapturer.getSources(options),
    timeoutMs,
    label,
  );
}

async function resolveScreenSourceForDisplay(displayId) {
  const sources = await getDesktopSources(
    {
      types: ["screen"],
      thumbnailSize: { width: 0, height: 0 },
      fetchWindowIcons: false,
    },
    "desktopCapturer.getSources(screen)",
  );
  const displayKey = String(displayId);
  return (
    sources.find((source) => String(source.display_id) === displayKey) ||
    sources.find((source) => source.id.includes(displayKey)) ||
    null
  );
}

function serializeDisplay(display) {
  return {
    id: display.id,
    label: display.label || `Display ${display.id}`,
    bounds: display.bounds,
    workArea: display.workArea,
    size: display.size,
    scaleFactor: display.scaleFactor,
    rotation: display.rotation,
    internal: display.internal,
    primary: display.id === screen.getPrimaryDisplay().id,
  };
}

function serializeSource(source) {
  return {
    id: source.id,
    name: source.name,
    display_id: source.display_id || "",
    thumbnail:
      source.thumbnail && !source.thumbnail.isEmpty()
        ? source.thumbnail.toDataURL()
        : null,
    appIcon:
      source.appIcon && !source.appIcon.isEmpty() ? source.appIcon.toDataURL() : null,
  };
}

async function listCaptureSources({ displayId = null, includeWindows = true } = {}) {
  const displays = screen.getAllDisplays().map(serializeDisplay);
  let screenSources = [];
  let windowSources = [];
  let agentWindowSources = [];
  let sourcesError = "";

  try {
    screenSources = await getDesktopSources(
      {
        types: ["screen"],
        thumbnailSize: THUMBNAIL_SIZE,
        fetchWindowIcons: false,
      },
      "desktopCapturer.getSources(screen)",
    );
  } catch (error) {
    sourcesError = capturePermissionHint(error && error.message ? error.message : error);
  }

  if (includeWindows) {
    try {
      windowSources = await getDesktopSources(
        {
          types: ["window"],
          thumbnailSize: THUMBNAIL_SIZE,
          fetchWindowIcons: true,
        },
        "desktopCapturer.getSources(window)",
      );
    } catch (error) {
      if (!sourcesError) {
        sourcesError = capturePermissionHint(error && error.message ? error.message : error);
      }
    }
  }

  let screens = screenSources.map((source) => {
    const serialized = serializeSource(source);
    const display = displays.find((item) => String(item.id) === String(serialized.display_id));
    return {
      ...serialized,
      display_label: display ? display.label : "",
      primary: Boolean(display && display.primary),
      fallback: false,
    };
  });

  if (!screens.length) {
    screens = fallbackScreensFromDisplays(displays);
  }

  let windows = windowSources
    .filter((source) => source.name && !source.name.startsWith("vdisplay share"))
    .map(serializeSource);

  if (includeWindows && windows.length === 0) {
    agentWindowSources = await listAgentWindowSources(displayId).catch((error) => {
      if (!sourcesError) {
        sourcesError = `agent windows fallback: ${String(error && error.message ? error.message : error)}`;
      }
      return [];
    });
    if (agentWindowSources.length > 0) {
      windows = agentWindowSources;
    }
  }

  const displayKey = displayId != null ? String(displayId) : "";
  let filtered = false;
  if (displayKey) {
    const onDisplay = windows.filter((item) => item.display_id === displayKey);
    if (onDisplay.length > 0) {
      windows = onDisplay;
      filtered = true;
    }
  }

  return {
    displays,
    screens,
    windows,
    filtered,
    sourcesError,
    windowsFallback: agentWindowSources.length > 0 ? "agent-windows" : "",
    usingFallback: screenSources.length === 0,
    sharedDisplayId: rendererStatus.sharedDisplayId || "",
  };
}

async function listAgentWindowSources(displayId = null) {
  if (!AGENT_URL) {
    return [];
  }
  const url = `${AGENT_URL}/windows?apps_only=true`;
  const response = await fetch(url, { headers: agentHeaders() });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.detail || (payload.error && payload.error.message) || response.statusText);
  }
  const data = payload.data || payload;
  const source = String(BRIDGE_SOURCE || "").trim();
  const selectedDisplayId = displayId != null ? String(displayId) : "";
  const rows = Array.isArray(data.windows) ? data.windows : [];
  return rows
    .filter((item) => {
      const monitorName = String(item.monitor_name || "").trim();
      return !source || !monitorName || monitorName === source;
    })
    .map((item) => {
      const title = String(item.title || item.name || item.app_label || item.window_id || "window");
      const monitorName = String(item.monitor_name || source || "");
      const width = Number(item.width || 0);
      const height = Number(item.height || 0);
      const x = Number(item.x || 0);
      const y = Number(item.y || 0);
      return {
        id: `agent-window:${item.window_id || title}`,
        name: title,
        thumbnail: "",
        display_id: selectedDisplayId || monitorName,
        display_label: monitorName,
        source: "agent-windows",
        window_id: item.window_id || "",
        app_label: item.app_label || "",
        wm_class: item.wm_class || "",
        bounds: { x, y, width, height },
      };
    });
}

function json(res, statusCode, payload) {
  const body = Buffer.from(JSON.stringify(payload, null, 2));
  res.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "content-length": body.length,
    "access-control-allow-origin": "http://127.0.0.1",
  });
  res.end(body);
}

function png(res, data) {
  res.writeHead(200, {
    "content-type": "image/png",
    "content-length": data.length,
    "cache-control": "no-store",
    "access-control-allow-origin": "http://127.0.0.1",
  });
  res.end(data);
}

function frameAgeMs() {
  if (!lastFrameMeta.ts) {
    return null;
  }
  return Math.max(0, Date.now() - Number(lastFrameMeta.ts));
}

function appIconSvg() {
  try {
    return fs.readFileSync(APP_ICON_PATH, "utf8");
  } catch {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
      <rect width="512" height="512" rx="108" fill="#101820"/>
      <rect x="96" y="112" width="320" height="224" rx="40" fill="#f6c85f"/>
      <path d="M172 164h168v112H172z" fill="#101820"/>
      <path d="M196 190h88l-35 58h76L188 338l39-70h-61l30-78z" fill="#4ab7ff"/>
      <circle cx="380" cy="144" r="48" fill="#ff6b4a"/>
    </svg>`;
  }
}

function appIconImage() {
  return nativeImage.createFromDataURL(
    `data:image/svg+xml;base64,${Buffer.from(appIconSvg()).toString("base64")}`,
  );
}

function statusPayload() {
  return {
    ok: true,
    service: "vdisplay-electron-share",
    instance: INSTANCE_ID,
    url: `http://${HOST}:${PORT}`,
    targetLabel: rendererStatus.targetLabel || INITIAL_TARGET_LABEL,
    mode: windowMode,
    alwaysOnTop,
    mainCaptureFallbackEnabled: mainCaptureAllowed(),
    sharing: Boolean(rendererStatus.sharing && lastFrame),
    sharedDisplayId: rendererStatus.sharedDisplayId || "",
    sharedDisplayLabel: rendererStatus.sharedDisplayLabel || "",
    activeSourceId: rendererStatus.activeSourceId || "",
    activeSourceName: rendererStatus.activeSourceName || "",
    renderer_status: rendererStatus,
    browser_bridge: {
      enabled: BRIDGE_PUSH,
      agent_url: AGENT_URL || null,
      bridge_id: bridgeId,
      source: BRIDGE_SOURCE,
      last_ok: bridgeLastOk,
      last_error: bridgeLastError,
    },
    frame: lastFrame
      ? {
          bytes: lastFrame.length,
          age_ms: frameAgeMs(),
          ...lastFrameMeta,
        }
      : null,
    displays: screen.getAllDisplays(),
  };
}

function debugEnvironment() {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (
      key.startsWith("VDISPLAY_") ||
      key.startsWith("ELECTRON_") ||
      [
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XDG_SESSION_TYPE",
        "XDG_CURRENT_DESKTOP",
        "DESKTOP_SESSION",
        "GDK_BACKEND",
        "LIBVA_DRIVER_NAME",
        "PATH",
      ].includes(key)
    ) {
      env[key] = redactDebugValue(value);
    }
  }
  return env;
}

function debugLogDir() {
  return path.join(os.homedir(), ".local", "state", "vdisplay", "electron-share", "debug");
}

function safeFilePart(value) {
  return String(value || "session")
    .replace(/[^a-zA-Z0-9_.-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "session";
}

function jsonBlock(value) {
  return `\n\`\`\`json\n${JSON.stringify(redactDebugValue(value), null, 2)}\n\`\`\`\n`;
}

function buildDebugMarkdown(bundle) {
  return [
    `# vdisplay Electron Share debug bundle`,
    ``,
    `Generated: ${bundle.generated_at}`,
    `Session started: ${bundle.session_started_at}`,
    `Instance: ${bundle.instance}`,
    `Target: ${bundle.target_label}`,
    ``,
    `## Summary`,
    jsonBlock(bundle.summary),
    `## Status`,
    jsonBlock(bundle.status),
    `## Capture sources`,
    jsonBlock(bundle.sources),
    `## Environment`,
    jsonBlock(bundle.environment),
    `## Session log`,
    jsonBlock(bundle.session_log),
  ].join("\n");
}

async function exportSessionLogsMarkdown() {
  const generatedAt = new Date().toISOString();
  let sources = null;
  try {
    sources = await withTimeout(
      listCaptureSources({
        displayId: rendererStatus.sharedDisplayId || null,
        includeWindows: true,
      }),
      1500,
      "debug source enumeration",
    );
  } catch (error) {
    sources = { ok: false, error: String(error && error.message ? error.message : error) };
  }
  const status = statusPayload();
  const bundle = {
    generated_at: generatedAt,
    session_started_at: SESSION_STARTED_AT.toISOString(),
    instance: INSTANCE_ID,
    target_label: rendererStatus.targetLabel || INITIAL_TARGET_LABEL,
    summary: {
      service: "vdisplay-electron-share",
      host: HOST,
      port: PORT,
      mode: windowMode,
      alwaysOnTop,
      closeQuits: CLOSE_QUITS,
      useSystemPicker: USE_SYSTEM_PICKER,
      ozonePlatform: OZONE_PLATFORM,
      mainCaptureFallbackEnabled: mainCaptureAllowed(),
      bridgePush: BRIDGE_PUSH,
      bridgeSource: BRIDGE_SOURCE,
      agentUrl: AGENT_URL || null,
      pid: process.pid,
      platform: process.platform,
      arch: process.arch,
      node: process.versions.node,
      electron: process.versions.electron,
      chrome: process.versions.chrome,
    },
    status,
    sources,
    environment: debugEnvironment(),
    session_log: sessionLog,
  };
  const markdown = buildDebugMarkdown(bundle);
  const dir = debugLogDir();
  fs.mkdirSync(dir, { recursive: true });
  const fileName = `${generatedAt.replace(/[:.]/g, "-")}__${safeFilePart(INSTANCE_ID)}.md`;
  const filePath = path.join(dir, fileName);
  fs.writeFileSync(filePath, markdown, "utf8");
  clipboard.writeText(filePath);
  logSession("info", "exported session debug markdown", {
    path: filePath,
    bytes: Buffer.byteLength(markdown),
  });
  return {
    ok: true,
    path: filePath,
    bytes: Buffer.byteLength(markdown),
    copiedToClipboard: "path",
  };
}

function agentHeaders() {
  const headers = { "content-type": "application/json" };
  if (AGENT_TOKEN) {
    headers.authorization = `Bearer ${AGENT_TOKEN}`;
  }
  return headers;
}

async function postAgent(pathname, payload) {
  if (!BRIDGE_PUSH) {
    return null;
  }
  const response = await fetch(`${AGENT_URL}${pathname}`, {
    method: "POST",
    headers: agentHeaders(),
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) {
    const message = data.error && data.error.message ? data.error.message : response.statusText;
    throw new Error(`${pathname}: ${message}`);
  }
  return data.data || data;
}

async function ensureBridge() {
  if (!BRIDGE_PUSH) {
    return null;
  }
  if (bridgeId) {
    return bridgeId;
  }
  const payload = await postAgent("/session/browser-bridge/register", {
    client: "vdisplay-electron-share",
    version: app.getVersion(),
    sources: [BRIDGE_SOURCE],
    monitors: [BRIDGE_SOURCE],
  });
  bridgeId = payload.bridge_id;
  bridgeLastOk = "registered";
  bridgeLastError = "";
  return bridgeId;
}

function resetBridgeRegistration() {
  bridgeId = null;
}

async function heartbeatBridge() {
  if (!BRIDGE_PUSH) {
    return;
  }
  try {
    const id = await ensureBridge();
    await postAgent("/session/browser-bridge/heartbeat", {
      bridge_id: id,
      sharing: Boolean(rendererStatus.sharing && lastFrame),
      sources: [BRIDGE_SOURCE],
      monitors: [BRIDGE_SOURCE],
      fps: 2,
    });
    bridgeLastOk = "heartbeat";
    bridgeLastError = "";
  } catch (error) {
    const message = String(error && error.message ? error.message : error);
    if (/not registered/i.test(message)) {
      resetBridgeRegistration();
      try {
        const id = await ensureBridge();
        await postAgent("/session/browser-bridge/heartbeat", {
          bridge_id: id,
          sharing: Boolean(rendererStatus.sharing && lastFrame),
          sources: [BRIDGE_SOURCE],
          monitors: [BRIDGE_SOURCE],
          fps: 2,
        });
        bridgeLastOk = "heartbeat";
        bridgeLastError = "";
        return;
      } catch (retryError) {
        bridgeLastError = String(retryError && retryError.message ? retryError.message : retryError);
        return;
      }
    }
    bridgeLastError = message;
  }
}

function stopMainProcessCapture() {
  if (mainCaptureTimer) {
    clearInterval(mainCaptureTimer);
    mainCaptureTimer = null;
  }
  mainCaptureState = null;
  lastCaptureDisplayMoveId = "";
  releaseCaptureFocusLock();
}

async function captureMainProcessFrame() {
  if (!mainCaptureState) {
    return false;
  }
  const { displayId, displayLabel, sourceName } = mainCaptureState;
  let screenSources = [];
  try {
    screenSources = await getDesktopSources(
      {
        types: ["screen"],
        thumbnailSize: MAIN_CAPTURE_THUMBNAIL_SIZE,
        fetchWindowIcons: false,
      },
      "desktopCapturer.getSources(screen-main-capture)",
      MAIN_CAPTURE_TIMEOUT_MS,
    );
  } catch (error) {
    bridgeLastError = capturePermissionHint(error && error.message ? error.message : error);
    return false;
  }
  const displayKey = String(displayId || "");
  const picked =
    (displayKey &&
      (screenSources.find((source) => String(source.display_id) === displayKey) ||
        screenSources.find((source) => source.id.includes(displayKey)))) ||
    screenSources[0];
  if (!picked || !picked.thumbnail || picked.thumbnail.isEmpty()) {
    bridgeLastError = "desktopCapturer returned no screen thumbnail";
    return false;
  }
  const size = picked.thumbnail.getSize();
  lastFrame = picked.thumbnail.toPNG();
  lastFrameMeta = {
    width: size.width,
    height: size.height,
    ts: Date.now(),
    displayId: displayId || picked.display_id || "",
    displayLabel: displayLabel || picked.name || "",
    sourceId: picked.id || "",
    sourceName: sourceName || picked.name || "",
    captureMode: "main-desktopCapturer",
  };
  rendererStatus = {
    ...rendererStatus,
    sharing: true,
    error: "",
    activeSourceId: picked.id,
    activeSourceName: picked.name || sourceName || "",
  };
  createTray();
  if (mainWindow) {
    mainWindow.webContents.send("share:main-capture-frame", {
      ok: true,
      width: size.width,
      height: size.height,
      captureMode: "main-desktopCapturer",
    });
  }
  await ingestBridgeFrame();
  return true;
}

async function startMainProcessCapture(payload = {}) {
  stopMainProcessCapture();
  if (!mainCaptureAllowed()) {
    return {
      ok: false,
      error:
        "desktopCapturer is disabled (VDISPLAY_ELECTRON_MAIN_CAPTURE_FALLBACK=0). On Wayland use x11 ozone or re-enable desktopCapturer.",
      captureMode: "main-desktopCapturer-disabled",
    };
  }
  captureFocusLock = true;
  const focus = await ensureCaptureFocus({ lock: true });
  mainCaptureState = {
    displayId: String(payload.displayId || rendererStatus.sharedDisplayId || ""),
    displayLabel: String(payload.displayLabel || rendererStatus.sharedDisplayLabel || ""),
    sourceId: String(payload.sourceId || rendererStatus.activeSourceId || ""),
    sourceName: String(payload.sourceName || rendererStatus.activeSourceName || ""),
  };
  const ok = await captureMainProcessFrame();
  if (!ok) {
    stopMainProcessCapture();
    let hint = capturePermissionHint(bridgeLastError || "");
    if (IS_WAYLAND && /timed out/i.test(String(bridgeLastError || hint))) {
      hint = `${hint} Restart without native Wayland: VDISPLAY_ELECTRON_OZONE_PLATFORM=x11 vdisplay electron-share start --instance ${INSTANCE_ID} --source ${BRIDGE_SOURCE} --port ${PORT}`;
    }
    return {
      ok: false,
      error: hint || "desktopCapturer could not capture the screen.",
      sourcesError: bridgeLastError || "",
      focused: Boolean(focus && focus.focused),
    };
  }
  mainCaptureTimer = setInterval(() => {
    captureMainProcessFrame().catch((error) => {
      bridgeLastError = String(error && error.message ? error.message : error);
    });
  }, 500);
  return { ok: true, captureMode: "main-desktopCapturer" };
}

async function ingestBridgeFrame() {
  if (!BRIDGE_PUSH || !lastFrame) {
    return;
  }
  const display = screen
    .getAllDisplays()
    .map(serializeDisplay)
    .find((item) => String(item.id) === String(lastFrameMeta.displayId || rendererStatus.sharedDisplayId));
  const payload = {
    source: BRIDGE_SOURCE,
    mime: "image/png",
    png_base64: lastFrame.toString("base64"),
    width: lastFrameMeta.width,
    height: lastFrameMeta.height,
    captured_at_ms: lastFrameMeta.ts || Date.now(),
    display_id: lastFrameMeta.displayId || rendererStatus.sharedDisplayId || "",
    display_label: lastFrameMeta.displayLabel || rendererStatus.sharedDisplayLabel || "",
    source_id: lastFrameMeta.sourceId || rendererStatus.activeSourceId || "",
    source_name: lastFrameMeta.sourceName || rendererStatus.activeSourceName || "",
    display_bounds: display ? display.bounds : null,
    scale_factor: display ? display.scaleFactor : null,
  };
  try {
    const id = await ensureBridge();
    await postAgent("/capture/ingest", {
      bridge_id: id,
      seq: ++frameSeq,
      ...payload,
    });
    bridgeLastOk = `ingest ${frameSeq}`;
    bridgeLastError = "";
  } catch (error) {
    const message = String(error && error.message ? error.message : error);
    if (/not registered/i.test(message)) {
      resetBridgeRegistration();
      try {
        const id = await ensureBridge();
        await postAgent("/capture/ingest", {
          bridge_id: id,
          seq: ++frameSeq,
          ...payload,
        });
        bridgeLastOk = `ingest ${frameSeq}`;
        bridgeLastError = "";
        return;
      } catch (retryError) {
        bridgeLastError = String(retryError && retryError.message ? retryError.message : retryError);
        return;
      }
    }
    bridgeLastError = message;
  }
}

function webPage() {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>vdisplay ${INSTANCE_ID}</title>
  <style>
    body { margin: 0; background: #101820; color: #f6f1e7; font-family: system-ui, sans-serif; }
    header { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 18px; background: #18242b; }
    h1 { font-size: 16px; margin: 0; }
    img { display: block; width: 100vw; height: calc(100vh - 58px); object-fit: contain; background: #050708; }
    code { color: #d7ffe0; }
  </style>
</head>
<body>
  <header>
    <h1>${INSTANCE_ID}: ${rendererStatus.targetLabel || INITIAL_TARGET_LABEL}</h1>
    <code id="status">loading...</code>
  </header>
  <img id="frame" src="/frame.png?t=${Date.now()}" />
  <script>
    const frame = document.getElementById("frame");
    const status = document.getElementById("status");
    async function tick() {
      frame.src = "/frame.png?t=" + Date.now();
      try {
        const res = await fetch("/status");
        const data = await res.json();
        status.textContent = data.sharing ? "sharing" : (data.renderer_status?.error || "idle");
      } catch (error) {
        status.textContent = String(error);
      }
    }
    setInterval(tick, 1000);
    tick();
  </script>
</body>
</html>`;
}

function startHttpServer() {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url || "/", `http://${HOST}:${PORT}`);
    if (url.pathname === "/" || url.pathname === "/manager") {
      const body = fs.readFileSync(path.join(__dirname, "renderer.html"));
      res.writeHead(200, {
        "content-type": "text/html; charset=utf-8",
        "content-length": body.length,
      });
      res.end(body);
      return;
    }
    if (url.pathname === "/renderer.js") {
      const body = fs.readFileSync(path.join(__dirname, "renderer.js"));
      res.writeHead(200, {
        "content-type": "application/javascript; charset=utf-8",
        "content-length": body.length,
      });
      res.end(body);
      return;
    }
    if (url.pathname === "/health" || url.pathname === "/status") {
      json(res, 200, statusPayload());
      return;
    }
    if (url.pathname === "/web") {
      const body = Buffer.from(webPage());
      res.writeHead(200, {
        "content-type": "text/html; charset=utf-8",
        "content-length": body.length,
      });
      res.end(body);
      return;
    }
    if (url.pathname === "/displays") {
      json(res, 200, { ok: true, displays: screen.getAllDisplays().map(serializeDisplay) });
      return;
    }
    if (url.pathname === "/sources") {
      const displayId = url.searchParams.get("displayId") || rendererStatus.sharedDisplayId || null;
      const includeWindows = url.searchParams.get("includeWindows") !== "0";
      listCaptureSources({ displayId, includeWindows })
        .then((payload) => json(res, 200, { ok: true, ...payload }))
        .catch((error) => json(res, 500, { ok: false, error: String(error) }));
      return;
    }
    if (url.pathname === "/share/start" && (req.method === "POST" || req.method === "GET")) {
      handleShareStartRequest()
        .then((payload) => json(res, 200, payload))
        .catch((error) => json(res, 500, { ok: false, error: String(error) }));
      return;
    }
    if (url.pathname === "/share/main-capture" && (req.method === "POST" || req.method === "GET")) {
      openManager();
      ensureCaptureFocus({ lock: true })
        .then(() =>
          startMainProcessCapture({
            displayId: url.searchParams.get("displayId") || rendererStatus.sharedDisplayId || "",
            displayLabel: url.searchParams.get("displayLabel") || rendererStatus.sharedDisplayLabel || "",
          }),
        )
        .then((payload) => json(res, payload && payload.ok ? 200 : 503, payload))
        .catch((error) => json(res, 500, { ok: false, error: String(error) }));
      return;
    }
    if (url.pathname === "/window/full") {
      applyWindowMode("full");
      openManager();
      json(res, 200, statusPayload());
      return;
    }
    if (url.pathname === "/window/compact") {
      applyWindowMode("compact");
      openManager();
      json(res, 200, statusPayload());
      return;
    }
    if (url.pathname === "/window/tray") {
      if (mainWindow) {
        mainWindow.hide();
      }
      json(res, 200, statusPayload());
      return;
    }
    if (url.pathname === "/window/show") {
      openManager();
      json(res, 200, statusPayload());
      return;
    }
    if (url.pathname === "/logs/export") {
      exportSessionLogsMarkdown()
        .then((payload) => json(res, 200, payload))
        .catch((error) =>
          json(res, 500, {
            ok: false,
            error: String(error && error.message ? error.message : error),
          }),
        );
      return;
    }
    if (url.pathname === "/quit" || url.pathname === "/shutdown") {
      stopMainProcessCapture();
      const payload = statusPayload();
      payload.exiting = true;
      json(res, 200, payload);
      setTimeout(() => app.exit(0), 50);
      return;
    }
    if (url.pathname === "/frame.png" || url.pathname === "/frame/all.png") {
      if (!lastFrame) {
        json(res, 503, {
          ok: false,
          error: "no shared frame yet; open the Electron window and click Share screens",
          status: rendererStatus,
        });
        return;
      }
      png(res, lastFrame);
      return;
    }
    json(res, 404, { ok: false, error: `unknown route: ${url.pathname}` });
  });
  server.listen(PORT, HOST, () => {
    console.log(`vdisplay-electron-share ${INSTANCE_ID} listening on http://${HOST}:${PORT}`);
  });
  server.on("error", (error) => {
    console.error(`vdisplay-electron-share ${INSTANCE_ID} failed to listen on ${HOST}:${PORT}:`, error);
  });
}

function installDisplayMediaHandler(forceSystemPicker) {
  const useSystemPicker =
    forceSystemPicker === undefined ? USE_SYSTEM_PICKER : Boolean(forceSystemPicker);

  // Native Wayland ozone: renderer getDisplayMedia + portal parent-window fail on GNOME.
  // Main-process desktopCapturer is the only supported path (see renderer.js).
  if (OZONE_PLATFORM === "wayland" && IS_WAYLAND) {
    session.defaultSession.setDisplayMediaRequestHandler(null);
    return;
  }

  // System picker: let Chromium/GNOME handle source selection (no custom handler).
  if (useSystemPicker) {
    session.defaultSession.setDisplayMediaRequestHandler(null);
    return;
  }

  if (!mainCaptureAllowed()) {
    session.defaultSession.setDisplayMediaRequestHandler(null);
    return;
  }

  session.defaultSession.setDisplayMediaRequestHandler(
    async (_request, callback) => {
      let finished = false;
      const finish = (payload) => {
        if (finished) {
          return;
        }
        finished = true;
        callback(payload);
      };
      try {
        const sourceId = pendingCaptureSourceId;
        pendingCaptureSourceId = null;
        await ensureCaptureFocus({ lock: true });
        const sources = await getDesktopSources(
          {
            types: ["screen", "window"],
            thumbnailSize: { width: 0, height: 0 },
            fetchWindowIcons: false,
          },
          "desktopCapturer.getSources(display-media-handler)",
          MAIN_CAPTURE_TIMEOUT_MS,
        );
        const displayId = String(rendererStatus.sharedDisplayId || screen.getPrimaryDisplay().id || "");
        const picked =
          (sourceId ? sources.find((source) => source.id === sourceId) : null) ||
          (displayId
            ? sources.find((source) => String(source.display_id || "") === displayId) ||
              sources.find((source) => String(source.id || "").includes(displayId))
            : null) ||
          sources.find((source) => String(source.id || "").startsWith("screen:")) ||
          sources[0] ||
          null;
        if (!picked) {
          throw new Error("desktopCapturer returned no video sources");
        }
        if (!rendererStatus.sharedDisplayId && picked.display_id) {
          rendererStatus.sharedDisplayId = String(picked.display_id);
          rendererStatus.sharedDisplayLabel = `Display ${picked.display_id}`;
        }
        rendererStatus.activeSourceId = picked.id;
        rendererStatus.activeSourceName = picked.name || rendererStatus.activeSourceName || "screen";
        createTray();
        finish({ video: picked });
      } catch (error) {
        console.warn("display media request handler failed:", error);
        pendingCaptureSourceId = null;
        releaseCaptureFocusLock();
        rendererStatus = {
          ...rendererStatus,
          sharing: false,
          error: capturePermissionHint(error && error.message ? error.message : error),
        };
        createTray();
      }
    },
    { useSystemPicker: false },
  );
}

function createWindow() {
  const initial = managerBounds(windowMode);
  mainWindow = new BrowserWindow({
    width: initial.width,
    height: initial.height,
    x: initial.x,
    y: initial.y,
    title: `vdisplay share: ${INSTANCE_ID}`,
    alwaysOnTop,
    autoHideMenuBar: true,
    icon: appIconImage(),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.setMenu(null);
  mainWindow.setAlwaysOnTop(alwaysOnTop, "floating");
  mainWindow.on("close", (event) => {
    if (CLOSE_QUITS) {
      return;
    }
    event.preventDefault();
    mainWindow.hide();
  });
  mainWindow.loadURL(`${MANAGER_ORIGIN}/manager`);
}

function managerBounds(mode) {
  const display = screen.getPrimaryDisplay();
  const area = display.workArea;
  if (mode === "full") {
    const width = Math.min(1680, area.width);
    const height = Math.min(980, area.height);
    return {
      width,
      height,
      x: area.x + Math.max(0, Math.round((area.width - width) / 2)),
      y: area.y + Math.max(0, Math.round((area.height - height) / 2)),
    };
  }
  const width = Math.min(420, Math.max(320, Math.round(1920 * 0.2)));
  const height = Math.min(270, Math.max(216, Math.round(1080 * 0.2) + 54));
  return {
    width,
    height,
    x: area.x + Math.max(0, area.width - width - 20),
    y: area.y + 20,
  };
}

function applyWindowMode(mode) {
  windowMode = mode === "full" ? "full" : "compact";
  if (!mainWindow) {
    return;
  }
  const bounds = managerBounds(windowMode);
  mainWindow.setBounds(bounds, true);
  mainWindow.setAlwaysOnTop(alwaysOnTop, "floating");
  mainWindow.webContents.send("share:mode", { mode: windowMode, alwaysOnTop });
}

function setAlwaysOnTop(value) {
  alwaysOnTop = Boolean(value);
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(alwaysOnTop, "floating");
    mainWindow.webContents.send("share:mode", { mode: windowMode, alwaysOnTop });
  }
  createTray();
}

function openManager() {
  if (!mainWindow) {
    createWindow();
  }
  mainWindow.show();
  mainWindow.focus();
}

function capturePermissionHint(errorMessage) {
  const base = String(errorMessage || "").trim();
  const focusHint =
    "Click the Electron Share window so it has focus, then retry Share — GNOME only shows the Screen Recording dialog for the focused app.";
  const settingsHint =
    "If no GNOME dialog appeared, open Settings → Privacy → Screen Recording and enable Electron or vdisplay share.";
  const x11Hint =
    "If capture keeps timing out on Wayland, restart with: VDISPLAY_ELECTRON_OZONE_PLATFORM=x11 vdisplay electron-share start ...";
  if (/timed out|access dialog|Only the focused app|fetch failed|associate portal window/i.test(base)) {
    let msg = base || focusHint;
    if (!msg.includes("GNOME only shows")) {
      msg = `${msg}. ${focusHint}`;
    }
    if (!msg.includes("Screen Recording")) {
      msg = `${msg} ${settingsHint}`;
    }
    if (IS_WAYLAND && !msg.includes("OZONE_PLATFORM=x11")) {
      msg = `${msg} ${x11Hint}`;
    }
    return msg;
  }
  return base || settingsHint;
}

function displayById(displayId) {
  const key = String(displayId || "").trim();
  if (!key) {
    return null;
  }
  return screen.getAllDisplays().find((display) => String(display.id) === key) || null;
}

let lastCaptureDisplayMoveId = "";

function moveWindowToSharedDisplay() {
  if (!mainWindow) {
    return null;
  }
  const display =
    displayById(rendererStatus.sharedDisplayId) ||
    displayById(lastFrameMeta.displayId) ||
    null;
  if (!display) {
    return null;
  }
  const displayId = String(display.id);
  if (lastCaptureDisplayMoveId === displayId) {
    return {
      displayId,
      displayLabel: display.label || `Display ${display.id}`,
      bounds: display.bounds,
      skipped: true,
    };
  }
  const size = managerBounds(windowMode);
  const x =
    display.bounds.x +
    Math.max(0, Math.round((display.bounds.width - size.width) / 2));
  const y =
    display.bounds.y +
    Math.max(0, Math.round((display.bounds.height - size.height) / 2));
  mainWindow.setBounds(
    {
      x,
      y,
      width: size.width,
      height: size.height,
    },
    true,
  );
  lastCaptureDisplayMoveId = displayId;
  return {
    displayId,
    displayLabel: display.label || `Display ${display.id}`,
    bounds: display.bounds,
    skipped: false,
  };
}

async function ensureCaptureFocus({ lock = false } = {}) {
  if (!mainWindow) {
    createWindow();
  }
  if (mainWindow.isMinimized()) {
    mainWindow.restore();
  }
  if (lock) {
    captureFocusLock = true;
  }
  const moved = moveWindowToSharedDisplay();
  if (moved && !moved.skipped) {
    logSession("info", "moved share window to target display before capture", moved);
  }
  mainWindow.setAlwaysOnTop(true, "screen-saver");
  mainWindow.show();
  mainWindow.focus();
  if (typeof app.focus === "function") {
    app.focus({ steal: true });
  }
  await new Promise((resolve) => setTimeout(resolve, IS_WAYLAND ? 900 : 350));
  if (!captureFocusLock && alwaysOnTop) {
    mainWindow.setAlwaysOnTop(true, "floating");
  } else if (!captureFocusLock && !alwaysOnTop) {
    mainWindow.setAlwaysOnTop(false);
  }
  return { ok: true, focused: mainWindow.isFocused(), locked: captureFocusLock };
}

function releaseCaptureFocusLock() {
  if (!captureFocusLock) {
    return;
  }
  captureFocusLock = false;
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(alwaysOnTop, "floating");
  }
}

function openWebView() {
  const url = AGENT_URL
    ? `${AGENT_URL}/api/web/browser-bridge?source=${encodeURIComponent(BRIDGE_SOURCE)}`
    : `${MANAGER_ORIGIN}/web`;
  shell.openExternal(url);
}

function trayIcon() {
  return appIconImage();
}

function createTray() {
  if (!tray) {
    tray = new Tray(trayIcon());
    tray.setToolTip(`vdisplay share ${INSTANCE_ID}`);
    tray.on("click", openManager);
  }
  tray.setContextMenu(
    Menu.buildFromTemplate([
      { label: `vdisplay share: ${INSTANCE_ID}`, enabled: false },
      { label: rendererStatus.targetLabel || INITIAL_TARGET_LABEL, enabled: false },
      { type: "separator" },
      { label: "Show manager", click: openManager },
      { label: "Compact preview", click: () => applyWindowMode("compact") },
      { label: "Full manager", click: () => applyWindowMode("full") },
      {
        label: "Always on top",
        type: "checkbox",
        checked: alwaysOnTop,
        click: (item) => setAlwaysOnTop(item.checked),
      },
      { label: "Open web view", click: openWebView },
      {
        label: "Export debug logs",
        click: () => {
          exportSessionLogsMarkdown().catch((error) => {
            console.error("debug log export failed:", error);
          });
        },
      },
      { type: "separator" },
      { label: "Quit", click: () => app.exit(0) },
    ]),
  );
}

ipcMain.handle("share:list-sources", async (_event, arg) => {
  const displayId =
    arg && typeof arg === "object" ? arg.displayId || null : arg || null;
  const includeWindows =
    !(arg && typeof arg === "object" && arg.includeWindows === false);
  return listCaptureSources({
    displayId: displayId || rendererStatus.sharedDisplayId || null,
    includeWindows,
  });
});

ipcMain.handle("share:select-source", async (_event, payload) => {
  let sourceId = payload && payload.sourceId ? String(payload.sourceId) : "";
  if (!sourceId) {
    return { ok: false, error: "sourceId required" };
  }
  if (sourceId.startsWith("display:")) {
    const displayId = sourceId.slice("display:".length);
    rendererStatus.sharedDisplayId = String(payload.displayId || displayId);
    rendererStatus.sharedDisplayLabel = String(
      payload.displayLabel || `Display ${displayId}`,
    );
    if (!mainCaptureAllowed()) {
      pendingCaptureSourceId = null;
      installDisplayMediaHandler(true);
      rendererStatus.activeSourceId = sourceId;
      rendererStatus.activeSourceName = String(payload.sourceName || rendererStatus.sharedDisplayLabel);
      createTray();
      return {
        ok: true,
        useSystemPicker: true,
        captureMode: "system",
        sourceId,
        sharedDisplayId: rendererStatus.sharedDisplayId,
        sharedDisplayLabel: rendererStatus.sharedDisplayLabel,
        hint: `In the GNOME dialog, choose "${rendererStatus.sharedDisplayLabel}" and click Share`,
      };
    }
    try {
      const resolved = await resolveScreenSourceForDisplay(displayId);
      if (resolved) {
        sourceId = resolved.id;
        pendingCaptureSourceId = sourceId;
        installDisplayMediaHandler(false);
        rendererStatus.activeSourceId = sourceId;
        rendererStatus.activeSourceName = String(payload.sourceName || resolved.name || "");
        createTray();
        return {
          ok: true,
          sourceId,
          captureMode: "programmatic",
          sharedDisplayId: rendererStatus.sharedDisplayId,
          sharedDisplayLabel: rendererStatus.sharedDisplayLabel,
        };
      }
    } catch {
      // Fall back to the GNOME portal picker below.
    }
    pendingCaptureSourceId = null;
    installDisplayMediaHandler(true);
    rendererStatus.activeSourceId = sourceId;
    rendererStatus.activeSourceName = String(payload.sourceName || rendererStatus.sharedDisplayLabel);
    createTray();
    return {
      ok: true,
      useSystemPicker: true,
      captureMode: "system",
      sourceId,
      sharedDisplayId: rendererStatus.sharedDisplayId,
      sharedDisplayLabel: rendererStatus.sharedDisplayLabel,
      hint: `In the GNOME dialog, choose "${rendererStatus.sharedDisplayLabel}" and click Share`,
    };
  }
  pendingCaptureSourceId = sourceId;
  if (payload && payload.displayId) {
    rendererStatus.sharedDisplayId = String(payload.displayId);
  }
  if (payload && payload.displayLabel) {
    rendererStatus.sharedDisplayLabel = String(payload.displayLabel);
  }
  if (payload && payload.sourceName) {
    rendererStatus.activeSourceId = sourceId;
    rendererStatus.activeSourceName = String(payload.sourceName);
  }
  if (!mainCaptureAllowed()) {
    pendingCaptureSourceId = null;
    installDisplayMediaHandler(true);
    createTray();
    return {
      ok: true,
      useSystemPicker: true,
      captureMode: "system",
      sourceId,
      sharedDisplayId: rendererStatus.sharedDisplayId,
      sharedDisplayLabel: rendererStatus.sharedDisplayLabel,
      hint: `In the GNOME dialog, choose "${rendererStatus.activeSourceName || rendererStatus.sharedDisplayLabel || "the target window"}" and click Share`,
    };
  }
  installDisplayMediaHandler(false);
  createTray();
  return {
    ok: true,
    sourceId,
    captureMode: "programmatic",
    sharedDisplayId: rendererStatus.sharedDisplayId,
    sharedDisplayLabel: rendererStatus.sharedDisplayLabel,
  };
});

ipcMain.handle("share:start-main-capture", async (_event, payload) => startMainProcessCapture(payload || {}));

ipcMain.handle("share:stop-main-capture", () => {
  stopMainProcessCapture();
  return { ok: true };
});

ipcMain.handle("share:ensure-capture-focus", async () => ensureCaptureFocus());

ipcMain.handle("share:prepare-system-picker", async () => {
  await ensureCaptureFocus();
  pendingCaptureSourceId = null;
  installDisplayMediaHandler(true);
  return { ok: true };
});

ipcMain.handle("share:restore-capture-handler", () => {
  installDisplayMediaHandler(USE_SYSTEM_PICKER);
  return { ok: true };
});

ipcMain.handle("share:config", () => ({
  instance: INSTANCE_ID,
  host: HOST,
  port: PORT,
  url: `http://${HOST}:${PORT}`,
  targetLabel: rendererStatus.targetLabel || INITIAL_TARGET_LABEL,
  bridgeSource: BRIDGE_SOURCE,
  preferredBounds: preferredBoundsFromEnv(),
  autoStartCapture: AUTO_START_CAPTURE,
  bridgePush: BRIDGE_PUSH,
  agentUrl: AGENT_URL,
  ozonePlatform: OZONE_PLATFORM,
    mainCaptureFallbackEnabled: mainCaptureAllowed(),
  mode: windowMode,
  alwaysOnTop,
  displays: screen.getAllDisplays().map(serializeDisplay),
  useSystemPicker: USE_SYSTEM_PICKER,
  sharedDisplayId: rendererStatus.sharedDisplayId,
  sharedDisplayLabel: rendererStatus.sharedDisplayLabel,
}));

ipcMain.handle("share:set-mode", (_event, mode) => {
  applyWindowMode(mode);
  return { mode: windowMode, alwaysOnTop };
});

ipcMain.handle("share:set-always-on-top", (_event, value) => {
  setAlwaysOnTop(value);
  return { mode: windowMode, alwaysOnTop };
});

ipcMain.handle("share:minimize-to-tray", () => {
  if (mainWindow) {
    mainWindow.hide();
  }
  return { ok: true };
});

ipcMain.handle("share:open-web", () => {
  openWebView();
  return { ok: true };
});

ipcMain.handle("share:set-target", (_event, targetLabel) => {
  rendererStatus.targetLabel = String(targetLabel || INITIAL_TARGET_LABEL).trim() || INITIAL_TARGET_LABEL;
  if (mainWindow) {
    mainWindow.setTitle(`vdisplay share: ${INSTANCE_ID} - ${rendererStatus.targetLabel}`);
  }
  createTray();
  return { targetLabel: rendererStatus.targetLabel };
});

ipcMain.handle("share:export-logs", () => exportSessionLogsMarkdown());

ipcMain.on("share:renderer-log", (_event, payload) => {
  logSession(
    payload && payload.level ? String(payload.level) : "renderer",
    payload && payload.message ? String(payload.message) : "",
    payload && payload.details ? payload.details : null,
  );
});

ipcMain.on("share:status", (_event, payload) => {
  const previousDisplayId = rendererStatus.sharedDisplayId || "";
  rendererStatus = {
    ...rendererStatus,
    ...(payload || {}),
  };
  const nextDisplayId = rendererStatus.sharedDisplayId || "";
  if (nextDisplayId && nextDisplayId !== previousDisplayId) {
    lastCaptureDisplayMoveId = "";
  }
  const statusLogKey = JSON.stringify({
    sharing: rendererStatus.sharing,
    error: rendererStatus.error || "",
    targetLabel: rendererStatus.targetLabel || "",
    sharedDisplayId: rendererStatus.sharedDisplayId || "",
    activeSourceId: rendererStatus.activeSourceId || "",
  });
  if (statusLogKey !== lastStatusLogKey) {
    lastStatusLogKey = statusLogKey;
    logSession("renderer-status", rendererStatus.error || (rendererStatus.sharing ? "sharing" : "idle"), rendererStatus);
  }
  createTray();
  heartbeatBridge();
});

ipcMain.on("share:frame", (_event, payload) => {
  if (!payload || typeof payload.dataUrl !== "string") {
    return;
  }
  const marker = "base64,";
  const index = payload.dataUrl.indexOf(marker);
  if (index < 0) {
    return;
  }
  lastFrame = Buffer.from(payload.dataUrl.slice(index + marker.length), "base64");
  lastFrameMeta = {
    width: Number(payload.width || 0),
    height: Number(payload.height || 0),
    ts: Number(payload.ts || Date.now()),
    displaySurface: payload.displaySurface || "",
    displayId: payload.displayId || rendererStatus.sharedDisplayId || "",
    displayLabel: payload.displayLabel || rendererStatus.sharedDisplayLabel || "",
    sourceId: payload.sourceId || rendererStatus.activeSourceId || "",
    sourceName: payload.sourceName || rendererStatus.activeSourceName || "",
  };
  ingestBridgeFrame();
});

app.whenReady().then(() => {
  const preferredDisplay = resolvePreferredDisplay();
  if (preferredDisplay) {
    rendererStatus.sharedDisplayId = String(preferredDisplay.id);
    rendererStatus.sharedDisplayLabel = preferredDisplay.label || `Display ${preferredDisplay.id}`;
  }
  Menu.setApplicationMenu(null);
  installDisplayMediaHandler();
  startHttpServer();
  createWindow();
  createTray();
  if (BRIDGE_PUSH) {
    heartbeatBridge();
    bridgeHeartbeatTimer = setInterval(heartbeatBridge, 2000);
  }
});

app.on("before-quit", () => {
  if (bridgeHeartbeatTimer) {
    clearInterval(bridgeHeartbeatTimer);
    bridgeHeartbeatTimer = null;
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

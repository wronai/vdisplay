"use strict";

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("vdisplayShare", {
  startMainCapture: (payload) => ipcRenderer.invoke("share:start-main-capture", payload || {}),
  stopMainCapture: () => ipcRenderer.invoke("share:stop-main-capture"),
  ensureCaptureFocus: () => ipcRenderer.invoke("share:ensure-capture-focus"),
  onMainCaptureFrame: (handler) =>
    ipcRenderer.on("share:main-capture-frame", (_event, payload) => handler(payload)),
  config: () => ipcRenderer.invoke("share:config"),
  listSources: (displayId, includeWindows = true) =>
    ipcRenderer.invoke("share:list-sources", { displayId, includeWindows }),
  selectSource: (payload) => ipcRenderer.invoke("share:select-source", payload),
  restoreCaptureHandler: () => ipcRenderer.invoke("share:restore-capture-handler"),
  prepareSystemPicker: () => ipcRenderer.invoke("share:prepare-system-picker"),
  setMode: (mode) => ipcRenderer.invoke("share:set-mode", mode),
  setAlwaysOnTop: (value) => ipcRenderer.invoke("share:set-always-on-top", value),
  minimizeToTray: () => ipcRenderer.invoke("share:minimize-to-tray"),
  openWeb: () => ipcRenderer.invoke("share:open-web"),
  setTarget: (targetLabel) => ipcRenderer.invoke("share:set-target", targetLabel),
  exportLogs: () => ipcRenderer.invoke("share:export-logs"),
  log: (level, message, details = null) =>
    ipcRenderer.send("share:renderer-log", { level, message, details }),
  status: (payload) => ipcRenderer.send("share:status", payload),
  frame: (payload) => ipcRenderer.send("share:frame", payload),
  onMode: (handler) => ipcRenderer.on("share:mode", (_event, payload) => handler(payload)),
  onAutoStartCapture: (handler) =>
    ipcRenderer.on("share:auto-start-capture", (_event, payload) => handler(payload)),
});

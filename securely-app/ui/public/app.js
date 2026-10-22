/* Securely compact island — status + colored scan pill + drag */

const LOOK_KEY = "securely-look";
const SETTINGS_KEY = "securely-settings";
const MODE_KEY = "securely-scan-mode";
const SHELL_WIDTH = 360;

const MODES = [
  { id: "quick", label: "Quick", startLabel: "Quick Scan" },
  { id: "timed", label: "Timed", startLabel: "Timed Scan" },
  { id: "continuous", label: "24/7", startLabel: "24/7 Monitor" },
];

const frameEl = document.querySelector("#frame");
const shellEl = document.querySelector("#shell");
const sendEl = document.querySelector("#send");
const statusLine = document.querySelector("#status-line");
const statusText = document.querySelector("#status-text");
const scanLabel = document.querySelector(".scan-label");
const dragEl = document.querySelector("#drag");

let running = false;
let scanMode = loadMode();
let settings = loadSettings();
let fitTimer = 0;
let fitInstant = false;
let fittedFrame = "";
let fitFlight = false;
let fitQueued = false;
let timedTimer = 0;

function hostPost(payload) {
  try {
    if (window.chrome?.webview?.postMessage) {
      window.chrome.webview.postMessage(JSON.stringify(payload));
    }
  } catch { /* browser preview */ }
}

function loadSettings() {
  try {
    return {
      testMode: false,
      opacity: 50,
      light: false,
      timedMins: 5,
      ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}"),
    };
  } catch {
    return { testMode: false, opacity: 50, light: false, timedMins: 5 };
  }
}

function loadMode() {
  const raw = localStorage.getItem(MODE_KEY) || "quick";
  return MODES.some((m) => m.id === raw) ? raw : "quick";
}

function modeMeta(id = scanMode) {
  return MODES.find((m) => m.id === id) || MODES[0];
}

function applyLook() {
  const opacity = Math.min(100, Math.max(10, Number(settings.opacity) || 50));
  settings.opacity = opacity;
  const light = !!settings.light;
  document.documentElement.dataset.widget = light ? "light" : "dark";
  const wash = opacity / 100;
  document.documentElement.style.setProperty("--glass", light ? `rgba(255,255,255,${wash})` : `rgba(0,0,0,${wash})`);
  localStorage.setItem(LOOK_KEY, JSON.stringify({ opacity, light }));
}

function setStatus(text, state = "idle") {
  if (statusText) statusText.textContent = text;
  else if (statusLine) statusLine.textContent = text;
  if (statusLine) statusLine.dataset.state = state;
  const live = document.querySelector("#status");
  if (live) live.textContent = text;
}

function setScanMode(next) {
  if (running) return;
  const id = MODES.some((m) => m.id === next) ? next : "quick";
  scanMode = id;
  localStorage.setItem(MODE_KEY, id);
  sendEl.dataset.mode = id;
  if (scanLabel) scanLabel.textContent = modeMeta(id).label;
  syncRunningChrome();
}

function cycleScanMode() {
  if (running) return;
  const i = MODES.findIndex((m) => m.id === scanMode);
  setScanMode(MODES[(i + 1) % MODES.length].id);
}

function syncRunningChrome() {
  const meta = modeMeta();
  sendEl.classList.toggle("is-send", !running);
  sendEl.classList.toggle("is-stop", running);
  sendEl.setAttribute("aria-pressed", String(running));
  if (running) {
    sendEl.setAttribute("aria-label", "Stop");
    sendEl.title = "Stop";
    if (scanLabel) scanLabel.textContent = "Stop";
  } else {
    sendEl.setAttribute("aria-label", meta.startLabel);
    sendEl.title = `${meta.startLabel} · right-click to change mode`;
    if (scanLabel) scanLabel.textContent = meta.label;
  }
}

function setRunning(on) {
  running = on;
  if (!on && timedTimer) {
    clearTimeout(timedTimer);
    timedTimer = 0;
  }
  syncRunningChrome();
}

function syncShellShape() {
  shellEl.classList.add("is-pill");
  shellEl.classList.remove("is-open");
}

function frameWidth() {
  return SHELL_WIDTH + 8;
}

function measureFrame() {
  return 48;
}

function scheduleFit(instant = false) {
  if (instant) fitInstant = true;
  clearTimeout(fitTimer);
  fitTimer = setTimeout(() => {
    const snap = fitInstant;
    fitInstant = false;
    fitWindow(snap);
  }, 16);
}

async function fitWindow(instant = false) {
  if (fitFlight) {
    fitQueued = true;
    if (instant) fitInstant = true;
    return;
  }
  fitFlight = true;
  try {
    const width = frameWidth();
    const height = measureFrame();
    const next = `${width}x${height}`;
    if (next === fittedFrame && !instant) return;
    hostPost({ cmd: "fit", cssWidth: width, cssHeight: height, instant: !!instant });
    fittedFrame = next;
  } finally {
    fitFlight = false;
    if (fitQueued) {
      fitQueued = false;
      const snap = fitInstant;
      fitInstant = false;
      fitWindow(snap);
    }
  }
}

function fitTrace() {
  const svg = document.querySelector("#trace");
  const rects = svg ? [...svg.querySelectorAll("rect")] : [];
  if (!svg || !rects.length) return;
  const width = Math.max(1, frameEl.clientWidth);
  const height = Math.max(1, frameEl.clientHeight);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const inset = 2.5;
  const w = Math.max(4, width - inset * 2);
  const h = Math.max(4, height - inset * 2);
  const radius = h / 2;
  for (const rect of rects) {
    rect.setAttribute("x", String(inset));
    rect.setAttribute("y", String(inset));
    rect.setAttribute("width", String(w));
    rect.setAttribute("height", String(h));
    rect.setAttribute("rx", String(radius));
    rect.setAttribute("ry", String(radius));
  }
}

function appendAudit(kind, text) {
  const rows = JSON.parse(localStorage.getItem("securely-audit") || "[]");
  rows.unshift({ t: Date.now(), kind, text });
  localStorage.setItem("securely-audit", JSON.stringify(rows.slice(0, 200)));
}

function finishQuickLike(kind, text) {
  appendAudit(kind, text);
  setStatus(settings.testMode ? "Threat (test)" : "Securely idle", settings.testMode ? "alert" : "idle");
  setRunning(false);
}

function startScan() {
  if (scanMode === "continuous") {
    const ok = window.confirm(
      "Enable 24/7 continuous monitoring?\n\nSecurely will capture your primary screen and send OCR text for analysis.",
    );
    if (!ok) return;
  }

  setRunning(true);
  if (scanMode === "quick") {
    setStatus("Scanning…", "scan");
    setTimeout(() => {
      if (!running) return;
      const kind = settings.testMode ? "SUSPICIOUS" : "SAFE";
      const text = settings.testMode
        ? "Test Mode: fake phishing cue."
        : "Quick Scan complete.";
      finishQuickLike(kind, text);
    }, 800);
    return;
  }

  if (scanMode === "timed") {
    const mins = Math.max(1, Number(settings.timedMins) || 5);
    setStatus(`Timed ${mins}m`, "scan");
    appendAudit("SCAN", `Timed scan started (${mins} min).`);
    timedTimer = setTimeout(() => {
      if (!running) return;
      appendAudit("SCAN", "Timed scan finished.");
      setStatus("Securely idle", "idle");
      setRunning(false);
    }, mins * 60 * 1000);
    return;
  }

  setStatus("24/7 active", "scan");
  appendAudit("SCAN", "24/7 monitoring started.");
}

function stopScan() {
  setRunning(false);
  setStatus("Securely idle", "idle");
  appendAudit("SCAN", "Scan stopped.");
}

sendEl.addEventListener("click", () => {
  if (running) stopScan();
  else startScan();
});

sendEl.addEventListener("contextmenu", (e) => {
  e.preventDefault();
  cycleScanMode();
});

document.querySelector("#home-btn")?.addEventListener("click", () => {
  hostPost({ cmd: "dashboard", tab: "dashboard" });
});
document.querySelector("#settings-btn")?.addEventListener("click", () => {
  hostPost({ cmd: "dashboard", tab: "settings" });
});
document.querySelector("#audit-btn")?.addEventListener("click", () => {
  hostPost({ cmd: "dashboard", tab: "audit" });
});
document.querySelector("#minimize-btn")?.addEventListener("click", () => {
  hostPost({ cmd: "visible", shown: false });
});
document.querySelector("#exit-btn")?.addEventListener("click", () => hostPost({ cmd: "quit" }));

/* Drag uses host cursor-follow (GetCursorPos), not WebView move deltas. */
function endDragFollow() {
  hostPost({ cmd: "follow", active: false });
}
dragEl.addEventListener("pointerdown", (e) => {
  if (e.button !== 0) return;
  e.preventDefault();
  dragEl.setPointerCapture(e.pointerId);
  hostPost({ cmd: "follow", active: true });
});
dragEl.addEventListener("pointerup", endDragFollow);
dragEl.addEventListener("pointercancel", endDragFollow);
dragEl.addEventListener("lostpointercapture", endDragFollow);

window.addEventListener("storage", (e) => {
  if (e.key === MODE_KEY && e.newValue) setScanMode(e.newValue);
  if (e.key === SETTINGS_KEY) settings = loadSettings();
});

try {
  const look = JSON.parse(localStorage.getItem(LOOK_KEY) || "null");
  if (look) {
    settings.opacity = look.opacity ?? settings.opacity;
    settings.light = !!look.light;
  }
} catch { /* ignore */ }

localStorage.setItem("securely-setup-done", "1");
applyLook();
syncShellShape();
setScanMode(scanMode);
setStatus("Securely idle", "idle");
setRunning(false);
if (typeof ResizeObserver === "function") new ResizeObserver(() => fitTrace()).observe(frameEl);
fitTrace();
scheduleFit(true);
requestAnimationFrame(() => {
  scheduleFit(true);
  hostPost({ cmd: "home" });
});

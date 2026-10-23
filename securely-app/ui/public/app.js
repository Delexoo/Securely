/* Securely compact island — status + colored scan pill + drag */

const LOOK_KEY = "securely-look";
const SETTINGS_KEY = "securely-settings";
const MODE_KEY = "securely-scan-mode";
const LAYOUT_KEY = "securely-widget-layout";
const LICENSE_KEY = "securely-license";
const SITE_ORIGIN = "https://trysecurely.vercel.app";
const OCR_TEXT_ONLY_MIN = 160;

const MODES = [
  { id: "quick", label: "Quick", startLabel: "Quick Scan" },
  { id: "timed", label: "Timed", startLabel: "Timed Scan" },
  { id: "continuous", label: "24/7", startLabel: "24/7 Monitor" },
];

/** Widget reshape cycle — each form has its own chrome in securely.css */
const LAYOUTS = [
  { id: "normal", label: "Normal pill", width: 340, height: 64, privacyH: 140, radius: "pill" },
  { id: "square", label: "Small square", width: 148, height: 168, privacyH: 220, radius: 28 },
  { id: "vertical", label: "Vertical", width: 168, height: 340, privacyH: 400, radius: 32 },
  { id: "big", label: "Big square", width: 268, height: 292, privacyH: 360, radius: 36 },
];

const LAYOUT_ICONS = {
  normal: '<rect x="3.5" y="7" width="17" height="10" rx="5"/>',
  square: '<rect x="6" y="6" width="12" height="12" rx="3"/>',
  vertical: '<rect x="8" y="3.5" width="8" height="17" rx="3.5"/>',
  big: '<rect x="4" y="4" width="16" height="16" rx="4"/>',
};

const frameEl = document.querySelector("#frame");
const shellEl = document.querySelector("#shell");
const sendEl = document.querySelector("#send");
const statusLine = document.querySelector("#status-line");
const statusText = document.querySelector("#status-text");
const statusSub = document.querySelector("#status-sub");
const scanLabel = document.querySelector(".scan-label");
const dragEl = document.querySelector("#drag");
const layoutBtn = document.querySelector("#layout-btn");
const privacyGate = document.querySelector("#privacy-gate");
const privacyKinds = document.querySelector("#privacy-kinds");
const privacyStop = document.querySelector("#privacy-stop");
const privacyContinue = document.querySelector("#privacy-continue");

let running = false;
let scanMode = loadMode();
let settings = loadSettings();
let widgetLayout = loadLayout();
let fitTimer = 0;
let fitInstant = false;
let fittedFrame = "";
let fitFlight = false;
let fitQueued = false;
let timedTimer = 0;
let privacyOpen = false;
let privacyResolver = null;

function hostPost(payload) {
  try {
    if (window.chrome?.webview?.postMessage) {
      window.chrome.webview.postMessage(JSON.stringify(payload));
    }
  } catch { /* browser preview */ }
}

const hostPending = new Map();
let hostReqSeq = 0;

function hostRequest(cmd, extra = {}, timeoutMs = 45000) {
  return new Promise((resolve, reject) => {
    if (!window.chrome?.webview) {
      reject(new Error("Securely host is not available."));
      return;
    }
    const id = `r${++hostReqSeq}`;
    const timer = setTimeout(() => {
      hostPending.delete(id);
      reject(new Error("Screen capture timed out."));
    }, timeoutMs);
    hostPending.set(id, { resolve, reject, timer });
    hostPost({ cmd, id, ...extra });
  });
}

if (window.chrome?.webview) {
  window.chrome.webview.addEventListener("message", (event) => {
    let data = event.data;
    if (typeof data === "string") {
      try {
        data = JSON.parse(data);
      } catch {
        return;
      }
    }
    if (!data || typeof data !== "object" || !data.id || !hostPending.has(data.id)) return;
    const entry = hostPending.get(data.id);
    hostPending.delete(data.id);
    clearTimeout(entry.timer);
    if (data.ok === false) entry.reject(new Error(data.error || "Host request failed."));
    else entry.resolve(data);
  });
}

function loadSettings() {
  try {
    return {
      testMode: false,
      opacity: 100,
      light: false,
      timedMins: 5,
      sound: true,
      notifications: true,
      ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}"),
    };
  } catch {
    return { testMode: false, opacity: 100, light: false, timedMins: 5, sound: true, notifications: true };
  }
}

function loadLayout() {
  const raw = localStorage.getItem(LAYOUT_KEY) || settings.layout || "normal";
  return LAYOUTS.some((l) => l.id === raw) ? raw : "normal";
}

function layoutMeta(id = widgetLayout) {
  return LAYOUTS.find((l) => l.id === id) || LAYOUTS[0];
}

/* Securely sound pack (/sounds) */
const SOUNDS = {
  start: "menu-open.mp3",
  done: "notification-pluck-off.mp3",
  alert: "notification-alert.mp3",
  ping: "new-notification.mp3",
  soft: "notification-2.mp3",
};
const soundUrls = new Map();
const soundLoads = new Map();
let liveAudio = null;

function loadSound(file) {
  const ready = soundLoads.get(file);
  if (ready) return ready;
  const pending = fetch(`/sounds/${file}`)
    .then((response) => {
      if (!response.ok) throw new Error("missing sound");
      return response.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      soundUrls.set(file, url);
      return url;
    })
    .catch(() => "");
  soundLoads.set(file, pending);
  return pending;
}

function playSound(kind) {
  if (settings.sound === false) return;
  const file = SOUNDS[kind] || SOUNDS.ping;
  // Host NAudio — WebView Audio() only works inside the click gesture (Quick start).
  if (window.chrome?.webview) {
    hostPost({ cmd: "play", file });
    return;
  }
  void (async () => {
    try {
      const src = soundUrls.get(file) || (await loadSound(file));
      if (!src) return;
      if (liveAudio) {
        liveAudio.pause();
        liveAudio = null;
      }
      const audio = new Audio(src);
      liveAudio = audio;
      await audio.play();
    } catch { /* autoplay / missing file */ }
  })();
}

function preloadSounds() {
  for (const file of Object.values(SOUNDS)) loadSound(file);
}

function loadMode() {
  const raw = localStorage.getItem(MODE_KEY) || "quick";
  return MODES.some((m) => m.id === raw) ? raw : "quick";
}

function modeMeta(id = scanMode) {
  return MODES.find((m) => m.id === id) || MODES[0];
}

function applyLook() {
  // Bold solid shell — opacity only nudges charcoal brightness, never goes translucent.
  const opacity = Math.min(100, Math.max(40, Number(settings.opacity) || 100));
  settings.opacity = opacity;
  const light = !!settings.light;
  document.documentElement.dataset.widget = light ? "light" : "dark";
  if (light) {
    document.documentElement.style.setProperty("--pill", "#f4f5f7");
    document.documentElement.style.setProperty("--glass", "#f4f5f7");
  } else {
    const t = opacity / 100;
    const r = Math.round(22 * t);
    const g = Math.round(26 * t);
    const b = Math.round(34 * t);
    const pill = `rgb(${r}, ${g}, ${b})`;
    document.documentElement.style.setProperty("--pill", pill);
    document.documentElement.style.setProperty("--glass", pill);
  }
  localStorage.setItem(LOOK_KEY, JSON.stringify({ opacity, light }));
}

function applyLayout(id = widgetLayout, { fit = true } = {}) {
  const meta = layoutMeta(id);
  widgetLayout = meta.id;
  settings.layout = meta.id;
  localStorage.setItem(LAYOUT_KEY, meta.id);
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch { /* ignore */ }

  if (frameEl) frameEl.dataset.layout = meta.id;
  if (shellEl) {
    shellEl.dataset.layout = meta.id;
    shellEl.classList.toggle("is-pill", meta.id === "normal");
    shellEl.classList.toggle("is-open", meta.id !== "normal");
  }
  if (layoutBtn) {
    layoutBtn.title = `Reshape · now ${meta.label}. Click for next shape.`;
    layoutBtn.setAttribute("aria-label", `Reshape widget (current: ${meta.label})`);
    const icon = layoutBtn.querySelector(".layout-icon");
    if (icon) icon.innerHTML = LAYOUT_ICONS[meta.id] || LAYOUT_ICONS.normal;
  }
  if (statusSub) {
    statusSub.textContent = meta.id === "normal" ? "Securely" : meta.label;
  }
  applyFrameSize();
  if (fit) scheduleFit(true);
  fitTrace();
}

function cycleLayout() {
  const idx = LAYOUTS.findIndex((l) => l.id === widgetLayout);
  const next = LAYOUTS[(idx + 1) % LAYOUTS.length];
  applyLayout(next.id);
  playSound("soft");
}

const STATUS = {
  idle: { label: "Idle", state: "idle" },
  scanning: { label: "Scanning", state: "scanning" },
  safe: { label: "Safe", state: "safe" },
  warning: { label: "Warning", state: "warning" },
  phishing: { label: "Phishing", state: "phishing" },
  active: { label: "Monitoring", state: "scanning" },
};

function setStatus(keyOrText, state) {
  const preset = STATUS[keyOrText];
  const label = preset ? preset.label : keyOrText;
  const nextState = preset ? preset.state : (state || "idle");
  if (statusText) statusText.textContent = label;
  else if (statusLine) statusLine.textContent = label;
  if (statusLine) {
    statusLine.dataset.state = nextState;
    statusLine.title = label;
  }
  const live = document.querySelector("#status");
  if (live) live.textContent = label;
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
  applyLayout(widgetLayout, { fit: false });
}

function applyFrameSize() {
  const meta = layoutMeta();
  const w = privacyOpen ? Math.max(meta.width, 320) : meta.width;
  if (frameEl) {
    frameEl.style.width = `${w}px`;
    frameEl.style.maxWidth = `${w}px`;
    frameEl.classList.toggle("is-privacy", privacyOpen);
  }
  if (shellEl) {
    shellEl.style.width = "100%";
  }
}

function frameWidth() {
  const meta = layoutMeta();
  return privacyOpen ? Math.max(meta.width, 320) : meta.width;
}

function measureFrame() {
  const meta = layoutMeta();
  const floor = privacyOpen ? meta.privacyH : meta.height;
  // Prefer live shell height so tools are never clipped by a too-short fit.
  const live = shellEl ? Math.ceil(shellEl.getBoundingClientRect().height) : 0;
  const pad = 2; // tiny safety so WinForms region does not bite anti-aliased edges
  return Math.max(floor, live + pad);
}

function setPrivacyOpen(on) {
  privacyOpen = !!on;
  if (privacyGate) privacyGate.hidden = !privacyOpen;
  shellEl.classList.toggle("is-privacy", privacyOpen);
  applyFrameSize();
  scheduleFit(true);
}

function askPrivacyContinue(summary) {
  return new Promise((resolve) => {
    if (privacyResolver) {
      privacyResolver(false);
      privacyResolver = null;
    }
    if (privacyKinds) {
      privacyKinds.textContent = summary
        ? `Detected: ${summary}. Continue only if you accept AI may see redacted screen text.`
        : "Sensitive details may be visible. Continue only if you accept AI analysis.";
    }
    privacyResolver = resolve;
    setPrivacyOpen(true);
    playSound("alert");
    setStatus("warning");
  });
}

function settlePrivacy(allow) {
  if (!privacyResolver) {
    setPrivacyOpen(false);
    return;
  }
  const done = privacyResolver;
  privacyResolver = null;
  setPrivacyOpen(false);
  done(!!allow);
}

privacyStop?.addEventListener("click", () => settlePrivacy(false));
privacyContinue?.addEventListener("click", () => settlePrivacy(true));

function scheduleFit(instant = false) {
  if (instant) fitInstant = true;
  clearTimeout(fitTimer);
  fitTimer = setTimeout(() => {
    const snap = fitInstant;
    fitInstant = false;
    fitWindow(snap);
  }, instant ? 0 : 48);
}

async function fitWindow(instant = false) {
  if (fitFlight) {
    fitQueued = true;
    if (instant) fitInstant = true;
    return;
  }
  fitFlight = true;
  try {
    applyFrameSize();
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
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
  const meta = layoutMeta();
  const radius = meta.radius === "pill" ? h / 2 : Math.min(Number(meta.radius) || 22, Math.min(w, h) / 2);
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
  let statusKey = "safe";
  if (kind === "PHISHING" || kind === "DANGER" || kind === "MALICIOUS") statusKey = "phishing";
  else if (kind === "SUSPICIOUS" || kind === "UNSURE" || kind === "WARNING") statusKey = "warning";
  else if (kind === "SAFE" || kind === "LEGITIMATE_LOGIN" || kind === "LEGITIMATE_PAYMENT") statusKey = "safe";
  playSound(statusKey === "safe" ? "done" : "alert");
  setStatus(statusKey);
  setRunning(false);
}

function parseAnalysis(analysis) {
  const raw = String(analysis || "").trim();
  const line = raw.split(/\r?\n/).map((s) => s.trim()).find(Boolean) || raw;
  const upper = line.toUpperCase();
  if (upper.startsWith("LEGITIMATE_LOGIN")) return { kind: "LEGITIMATE_LOGIN", text: line };
  if (upper.startsWith("LEGITIMATE_PAYMENT")) return { kind: "LEGITIMATE_PAYMENT", text: line };
  if (upper.startsWith("PHISHING") || upper.startsWith("MALICIOUS")) return { kind: "PHISHING", text: line };
  if (upper.startsWith("SUSPICIOUS")) return { kind: "SUSPICIOUS", text: line };
  if (upper.startsWith("UNSURE")) return { kind: "UNSURE", text: line };
  if (upper.startsWith("SAFE") || upper === "SAFE") return { kind: "SAFE", text: line || "SAFE" };
  if (upper.includes("PHISH")) return { kind: "PHISHING", text: line };
  if (upper.includes("SUSPICIOUS")) return { kind: "SUSPICIOUS", text: line };
  return { kind: "UNSURE", text: line || "UNSURE: Could not classify this screen." };
}

async function captureScreen() {
  const shot = await hostRequest("capture");
  if (!shot?.image) throw new Error("The screen could not be captured.");
  return {
    image: shot.image,
    text: typeof shot.text === "string" ? shot.text : "",
    mimeType: shot.mimeType || "image/jpeg",
  };
}

async function analyzeScreen(shot, { allowImage = true } = {}) {
  const text = String(shot.text || "");
  const payload = { text };
  // Prefer OCR text when rich enough — smaller, faster, less accidental PII in pixels.
  const sendImage = allowImage && (!!shot.image) && text.trim().length < OCR_TEXT_ONLY_MIN;
  if (sendImage) {
    payload.image = shot.image;
    payload.mimeType = shot.mimeType || "image/jpeg";
  }
  const attempt = async () => {
    const res = await fetch(`${SITE_ORIGIN}/api/analyze`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Analysis unavailable.");
    return parseAnalysis(data.analysis);
  };
  try {
    return await attempt();
  } catch (err) {
    await new Promise((r) => setTimeout(r, 450));
    return attempt();
  }
}

function mergeLocalHint(aiResult, localHint) {
  if (!localHint) return aiResult;
  if (!aiResult || aiResult.kind === "SAFE" || aiResult.kind === "UNSURE") {
    return { kind: localHint.kind, text: `${localHint.text} AI: ${aiResult?.text || "n/a"}` };
  }
  if (localHint.kind === "PHISHING" && aiResult.kind !== "PHISHING") {
    return { kind: "PHISHING", text: `${localHint.text} AI: ${aiResult.text}` };
  }
  return aiResult;
}

async function runQuickScan() {
  setStatus("scanning");
  if (settings.testMode) {
    await new Promise((r) => setTimeout(r, 500));
    if (!running) return;
    finishQuickLike("SUSPICIOUS", "Test Mode: fake phishing cue.");
    return;
  }
  try {
    const shot = await captureScreen();
    if (!running) return;

    const detector = window.SecurelySensitive;
    const sensitive = detector?.detectSensitive?.(shot.text) || { found: false };
    let allowImage = true;
    let textForAi = shot.text || "";

    if (sensitive.found) {
      appendAudit("PRIVACY", `Sensitive details held back from AI: ${sensitive.summary || "detected"}.`);
      const ok = await askPrivacyContinue(sensitive.summary);
      if (!running) return;
      if (!ok) {
        appendAudit("PRIVACY", "User stopped before AI — sensitive screen was not uploaded.");
        playSound("soft");
        setStatus("idle");
        setRunning(false);
        return;
      }
      // Continue: redact OCR and never upload the raw screenshot.
      textForAi = detector.redactSensitive(shot.text, sensitive.hits);
      allowImage = false;
      appendAudit("PRIVACY", "User continued after sensitive warning — AI received redacted text only.");
    }

    const localHint = detector?.localThreatHints?.(textForAi) || null;
    let result = await analyzeScreen(
      { ...shot, text: textForAi },
      { allowImage },
    );
    result = mergeLocalHint(result, localHint);
    if (!running) return;
    finishQuickLike(result.kind, result.text);
  } catch (err) {
    if (!running) return;
    const message = err instanceof Error ? err.message : "Quick Scan failed.";
    finishQuickLike("UNSURE", `UNSURE: ${message}`);
  }
}

function loadLicense() {
  try {
    return JSON.parse(localStorage.getItem(LICENSE_KEY) || "null");
  } catch {
    return null;
  }
}

function saveLicense(data) {
  localStorage.setItem(LICENSE_KEY, JSON.stringify(data));
}

function isLicensed() {
  const lic = loadLicense();
  return !!(lic && lic.active && lic.email);
}

function openBilling() {
  hostPost({ cmd: "dashboard", tab: "billing" });
}

async function refreshLicense(email) {
  const clean = String(email || "").trim().toLowerCase();
  if (!clean || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(clean)) {
    throw new Error("Enter the email you used at Stripe checkout.");
  }
  const res = await fetch(`${SITE_ORIGIN}/api/license`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: clean }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Could not verify subscription.");
  const next = {
    email: clean,
    active: !!data.active,
    status: data.status || (data.active ? "active" : "inactive"),
    checkedAt: Date.now(),
  };
  saveLicense(next);
  return next;
}

function syncLicenseChrome() {
  document.documentElement.dataset.licensed = isLicensed() ? "1" : "0";
}

function startScan() {
  // Never use window.confirm/alert — WebView2 script dialogs freeze the shaped pill.
  // Dashboard opens only for subscription / activation — never for a normal scan.
  if (!isLicensed()) {
    setStatus("idle");
    openBilling();
    return;
  }

  setRunning(true);
  void playSound("start");
  if (scanMode === "quick") {
    void runQuickScan();
    return;
  }

  if (scanMode === "timed") {
    const mins = Math.max(1, Number(settings.timedMins) || 5);
    setStatus("scanning");
    appendAudit("SCAN", `Timed scan started (${mins} min).`);
    timedTimer = setTimeout(() => {
      if (!running) return;
      appendAudit("SCAN", "Timed scan finished.");
      void playSound("done");
      setStatus("idle");
      setRunning(false);
    }, mins * 60 * 1000);
    return;
  }

  setStatus("active");
  appendAudit("SCAN", "24/7 monitoring started (screen OCR while active).");
  if (!localStorage.getItem("securely-continuous-ok")) {
    localStorage.setItem("securely-continuous-ok", "1");
  }
}

function stopScan() {
  if (privacyResolver) settlePrivacy(false);
  setRunning(false);
  playSound("soft");
  setStatus("idle");
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
layoutBtn?.addEventListener("click", () => cycleLayout());
/* Exit = hide the pill (same as minimize). Full quit lives in the dashboard. */
document.querySelector("#exit-btn")?.addEventListener("click", () => {
  playSound("soft");
  hostPost({ cmd: "visible", shown: false });
});

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
  if (e.key === SETTINGS_KEY) {
    settings = loadSettings();
    applyLook();
    if (settings.layout && settings.layout !== widgetLayout) applyLayout(settings.layout);
  }
  if (e.key === LAYOUT_KEY && e.newValue && e.newValue !== widgetLayout) applyLayout(e.newValue);
  if (e.key === LICENSE_KEY) syncLicenseChrome();
  if (e.key === LOOK_KEY) applyLook();
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
applyLayout(widgetLayout, { fit: false });
setScanMode(scanMode);
setStatus("idle");
setRunning(false);
syncLicenseChrome();
window.refreshSecurelyLicense = refreshLicense;
window.isSecurelyLicensed = isLicensed;
window.playSecurelySound = playSound;
window.setSecurelyStatus = setStatus;
window.cycleSecurelyLayout = cycleLayout;
preloadSounds();
if (typeof ResizeObserver === "function") new ResizeObserver(() => fitTrace()).observe(frameEl);
fitTrace();
scheduleFit(true);
requestAnimationFrame(() => {
  scheduleFit(true);
  hostPost({ cmd: "home" });
});

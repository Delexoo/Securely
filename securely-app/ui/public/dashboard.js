const SETTINGS_KEY = "securely-settings";
const AUDIT_KEY = "securely-audit";
const LOOK_KEY = "securely-look";
const APPEAR_KEY = "securely-dash-appearance";

const SITE_ORIGIN = "https://trysecurely.vercel.app";

function hostPost(payload) {
  try {
    if (window.chrome?.webview?.postMessage) {
      window.chrome.webview.postMessage(JSON.stringify(payload));
    }
  } catch { /* preview */ }
}

const hostPending = new Map();
let hostReqSeq = 0;

function hostRequest(cmd, extra = {}, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    if (!window.chrome?.webview) {
      reject(new Error("Securely host is not available."));
      return;
    }
    const id = `d${++hostReqSeq}`;
    const timer = setTimeout(() => {
      hostPending.delete(id);
      reject(new Error("Host request timed out."));
    }, timeoutMs);
    hostPending.set(id, { resolve, reject, timer });
    hostPost({ cmd, id, ...extra });
  });
}

if (window.chrome?.webview) {
  window.chrome.webview.addEventListener("message", (event) => {
    let data = event.data;
    if (typeof data === "string") {
      try { data = JSON.parse(data); } catch { return; }
    }
    if (!data || typeof data !== "object") return;
    // Host-shared license (pill + dashboard WebViews).
    if (data.type === "license" && data.license) {
      saveLicenseLocal(data.license);
      paintBilling();
      return;
    }
    if (!data.id) return;
    const pending = hostPending.get(data.id);
    if (!pending) return;
    clearTimeout(pending.timer);
    hostPending.delete(data.id);
    pending.resolve(data);
  });
}

function loadSettings() {
  try {
    return {
      hitboxes: false,
      strict: false,
      testMode: false,
      notifications: true,
      sound: true,
      opacity: 100,
      light: false,
      timedMins: 5,
      ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}"),
    };
  } catch {
    return { hitboxes: false, strict: false, testMode: false, notifications: true, sound: true, opacity: 100, light: false, timedMins: 5, layout: "normal" };
  }
}

let settings = loadSettings();
let mode = "quick";
let pillShown = true;

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  localStorage.setItem(LOOK_KEY, JSON.stringify({ opacity: settings.opacity, light: settings.light }));
  hostPost({ cmd: "notify-pill", type: "look" });
}

function setAppearance(modeName) {
  document.documentElement.dataset.appearance = modeName === "dark" ? "dark" : "light";
  localStorage.setItem(APPEAR_KEY, document.documentElement.dataset.appearance);
  document.querySelectorAll("[data-dashboard-mode]").forEach((btn) => {
    btn.setAttribute("aria-checked", String(btn.dataset.dashboardMode === document.documentElement.dataset.appearance));
  });
}

function syncWidgetModes() {
  document.querySelectorAll("[data-widget-mode]").forEach((btn) => {
    const light = btn.dataset.widgetMode === "light";
    btn.setAttribute("aria-checked", String(Boolean(settings.light) === light));
  });
}

const EDUCATION = {
  PHISHING: {
    explain:
      "This screen looked like a phishing or scam page — something designed to steal passwords, codes, or money by pretending to be a trusted site or person.",
    tips: [
      "Do not type passwords, codes, or card numbers on that screen.",
      "Check the real address bar (https + exact domain). Close the tab and reopen the site from a bookmark you trust.",
      "If you already entered a password, change it on the real site and turn on two-factor authentication.",
      "Never approve unexpected authenticator or bank prompts.",
    ],
  },
  SUSPICIOUS: {
    explain:
      "Securely saw warning signs that are common in scams or unsafe pages, but it is not 100% sure. Treat the screen carefully until you verify it.",
    tips: [
      "Pause before clicking download, “verify account,” or payment buttons.",
      "Compare the URL and branding with the official site or app.",
      "If someone messaged you the link, contact them through a channel you already trust — not by replying in that chat.",
      "When unsure, navigate to the service yourself instead of using the link on screen.",
    ],
  },
  UNSURE: {
    explain:
      "Securely could not confidently classify this screen (weak OCR, blocked upload, or unclear content). That does not mean it is safe.",
    tips: [
      "If anything asks for money, secrets, or remote access, stop and verify out-of-band.",
      "Run another Quick Scan after the page fully loads.",
      "Keep Windows and your browser updated.",
    ],
  },
  WARNING: {
    explain: "Securely flagged a warning on this activity. Review the summary and avoid rushing into logins or payments.",
    tips: [
      "Double-check who you are interacting with before sharing personal data.",
      "Prefer official apps and bookmarked sites over links from ads or messages.",
    ],
  },
  SAFE: {
    explain: "No strong phishing or scam signals were found on this capture. Stay alert — AI assist is not a guarantee.",
    tips: [
      "Still use unique passwords and two-factor authentication.",
      "Be careful with unexpected pop-ups even on familiar sites.",
    ],
  },
  PRIVACY: {
    explain: "Sensitive details were detected on screen. Securely held them back from AI until you chose what to do.",
    tips: [
      "Hide or blur secrets before scanning when you can.",
      "Prefer Continue only when you accept redacted text may still be analyzed.",
    ],
  },
  SCAN: {
    explain: "This is a scan lifecycle note (start, finish, or stop), not a threat verdict.",
    tips: ["Use Quick for a one-shot check; Timed or 24/7 for longer watching from the pill."],
  },
  DEFAULT: {
    explain: "Review this entry’s summary. When Securely marks Suspicious or Phishing, treat the screen as untrusted until verified.",
    tips: [
      "Verify domains yourself.",
      "Never share one-time codes with callers or chat pop-ups.",
      "Keep Securely updated and Windows Security enabled.",
    ],
  },
};

function educationFor(kind) {
  const key = String(kind || "").toUpperCase();
  if (key.includes("PHISH") || key === "MALICIOUS" || key === "DANGER") return EDUCATION.PHISHING;
  if (key.includes("SUSPICIOUS")) return EDUCATION.SUSPICIOUS;
  if (key.includes("UNSURE")) return EDUCATION.UNSURE;
  if (key.includes("WARN")) return EDUCATION.WARNING;
  if (key === "SAFE" || key.startsWith("LEGITIMATE")) return EDUCATION.SAFE;
  if (key === "PRIVACY") return EDUCATION.PRIVACY;
  if (key === "SCAN") return EDUCATION.SCAN;
  return EDUCATION.DEFAULT;
}

const LICENSE_KEY = "securely-license";
const PENDING_CHECKOUT_KEY = "securely-pending-checkout";
let licenseWatchTimer = 0;
let sessionWatchTimer = 0;

function openSection(name) {
  const allowed = [
    "monitor",
    "analyze",
    "antivirus",
    "vpn",
    "settings",
    "billing",
    "audit",
    "releases",
    "credits",
  ];
  const tabMap = {
    dashboard: "monitor",
    settings: "settings",
    billing: "billing",
    audit: "audit",
    releases: "releases",
    credits: "credits",
    monitor: "monitor",
    analyze: "analyze",
    antivirus: "antivirus",
    protect: "antivirus",
    vpn: "vpn",
  };
  const id = tabMap[name] || (allowed.includes(name) ? name : "monitor");
  document.querySelectorAll(".side-nav [data-open]").forEach((btn) => {
    btn.setAttribute("aria-current", String(btn.dataset.open === id));
  });
  document.querySelectorAll("main > section[data-section]").forEach((sec) => {
    sec.hidden = sec.dataset.section !== id;
  });
  history.replaceState(null, "", `${location.pathname}?tab=${id === "monitor" ? "dashboard" : id}`);
  if (id === "audit" || id === "monitor") syncAlerts();
  if (id === "releases") paintReleaseNotes();
  if (id === "billing") {
    paintBilling();
    void hydrateLicenseFromHost().then(() => {
      paintBilling();
      try {
        const pending = JSON.parse(localStorage.getItem(PENDING_CHECKOUT_KEY) || "null");
        if (!loadLicense()?.active && pending?.sessionId) startSessionWatch(pending.sessionId);
      } catch { /* ignore */ }
    });
  }
  if (id === "antivirus") paintAv();
  if (id === "vpn") paintVpn();
}

window.openSecurelySection = openSection;

function setMode(next) {
  mode = next;
  localStorage.setItem("securely-scan-mode", mode);
  document.querySelectorAll("[data-mode]").forEach((btn) => {
    btn.setAttribute("aria-checked", String(btn.dataset.mode === mode));
  });
  const durationRow = document.querySelector("#duration-row");
  if (durationRow) durationRow.hidden = mode !== "timed";
  hostPost({ cmd: "notify-pill", type: "mode" });
}

function syncDashStatus() {
  const status = document.querySelector("#dash-status");
  const countdown = document.querySelector("#dash-countdown");
  try {
    const runtime = JSON.parse(localStorage.getItem("securely-runtime") || "null");
    if (status && runtime?.label) status.textContent = runtime.label;
    if (countdown) {
      countdown.textContent =
        mode === "timed"
          ? `Timed mode · ${settings.timedMins || 5} min duration · start/stop from the pill`
          : mode === "continuous"
            ? "24/7 mode · start/stop from the pill"
            : "Quick mode · start/stop from the pill";
    }
  } catch {
    if (status) status.textContent = "Idle";
  }
}

function openAuditDetail(row) {
  const dialog = document.querySelector("#audit-detail");
  if (!dialog || !row) return;
  const kind = String(row.kind || "EVENT");
  const edu = educationFor(kind);
  const kindEl = document.querySelector("#audit-detail-kind");
  const whenEl = document.querySelector("#audit-detail-when");
  const summaryEl = document.querySelector("#audit-detail-summary");
  const explainEl = document.querySelector("#audit-detail-explain");
  const tipsEl = document.querySelector("#audit-detail-tips");
  const shotWrap = document.querySelector("#audit-detail-shot");
  const img = document.querySelector("#audit-detail-img");
  const ocrEl = document.querySelector("#audit-detail-ocr");
  if (kindEl) kindEl.textContent = kind;
  if (whenEl) whenEl.textContent = new Date(row.t).toLocaleString();
  if (summaryEl) {
    summaryEl.textContent =
      row.summary ||
      row.text ||
      "No detailed summary was stored for this entry.";
  }
  if (explainEl) explainEl.textContent = row.explain || edu.explain;
  if (tipsEl) {
    tipsEl.replaceChildren();
    const tips = Array.isArray(row.tips) && row.tips.length ? row.tips : edu.tips;
    for (const tip of tips) {
      const li = document.createElement("li");
      li.textContent = tip;
      tipsEl.append(li);
    }
  }
  const hasShot = !!(row.image && String(row.image).length > 32);
  if (shotWrap && img) {
    shotWrap.hidden = !hasShot;
    if (hasShot) {
      const mime = row.mimeType && String(row.mimeType).startsWith("image/") ? row.mimeType : "image/jpeg";
      img.src = `data:${mime};base64,${row.image}`;
    } else {
      img.removeAttribute("src");
    }
  }
  if (ocrEl) {
    const snippet = row.ocrSnippet ? String(row.ocrSnippet).trim() : "";
    ocrEl.hidden = !snippet;
    ocrEl.textContent = snippet ? `OCR excerpt: ${snippet}` : "";
  }
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
}

function renderAudit(target) {
  const rows = JSON.parse(localStorage.getItem(AUDIT_KEY) || "[]");
  if (!rows.length) {
    target.innerHTML = `<p class="empty-state">No threats logged yet. Run a Quick Scan from the pill to start.</p>`;
    return;
  }
  target.replaceChildren();
  for (const row of rows.slice(0, 80)) {
    const el = document.createElement("button");
    el.type = "button";
    el.className = "threat-row";
    if (row.image) el.classList.add("has-shot");
    const kind = document.createElement("span");
    kind.className = "kind";
    kind.textContent = row.kind || "EVENT";
    const body = document.createElement("span");
    body.textContent = row.text || "";
    const when = document.createElement("div");
    when.className = "muted";
    when.textContent = new Date(row.t).toLocaleString();
    el.append(kind, body, when);
    el.addEventListener("click", () => openAuditDetail(row));
    target.appendChild(el);
  }
}

function syncAlerts() {
  const alerts = document.querySelector("#dash-alerts");
  const audit = document.querySelector("#audit-list");
  if (alerts) renderAudit(alerts);
  if (audit) renderAudit(audit);
}

function appendReleaseGroups(card, sections) {
  for (const [label, key] of [["Added", "added"], ["Bug fixes", "fixes"]]) {
    const filled = (sections || []).filter((section) => (section[key] || []).length);
    if (!filled.length) continue;
    const heading = document.createElement("h3");
    heading.textContent = label;
    card.append(heading);
    for (const section of filled) {
      const area = document.createElement("h4");
      area.textContent = section.heading;
      const list = document.createElement("ul");
      for (const note of section[key]) {
        const item = document.createElement("li");
        item.textContent = note;
        list.append(item);
      }
      card.append(area, list);
    }
  }
}

let releaseNotesLoaded = false;
function paintReleaseNotes(force = false) {
  const root = document.querySelector("#release-notes");
  if (!root) return;
  if (releaseNotesLoaded && !force && root.querySelector(".release")) return;
  root.innerHTML = `<p class="empty-state">Loading release notes…</p>`;
  fetch("/releases.json")
    .then((response) => {
      if (!response.ok) throw new Error("missing");
      return response.json();
    })
    .then((log) => {
      root.replaceChildren();
      const updates = log.updates || [];
      if (!updates.length) {
        root.innerHTML = `<p class="empty-state">No release notes yet.</p>`;
        return;
      }
      updates.forEach((update, index) => {
        const article = document.createElement("article");
        article.className = "release";
        article.id = `v${update.version}`;
        const mark = document.createElement("div");
        mark.className = "release-mark";
        mark.setAttribute("aria-hidden", "true");
        const body = document.createElement("div");
        body.className = "release-body";
        const meta = document.createElement("header");
        meta.className = "release-meta";
        const tag = document.createElement("a");
        tag.className = "release-tag";
        tag.href = update.url || `https://github.com/Delexoo/Securely/releases/tag/v${update.version}`;
        tag.target = "_blank";
        tag.rel = "noopener";
        tag.textContent = update.tag || `v${update.version}`;
        meta.append(tag);
        if (index === 0) {
          const latest = document.createElement("span");
          latest.className = "release-latest";
          latest.textContent = "Latest";
          meta.append(latest);
        }
        const [year, month, day] = String(update.date).split("-").map(Number);
        const time = document.createElement("time");
        time.dateTime = update.date;
        time.textContent = new Date(Date.UTC(year, month - 1, day)).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
          timeZone: "UTC",
        });
        meta.append(time);
        const card = document.createElement("div");
        card.className = "release-card";
        const title = document.createElement("h2");
        title.textContent = update.title || update.version;
        card.append(title);
        appendReleaseGroups(card, update.sections);
        body.append(meta, card);
        article.append(mark, body);
        root.append(article);
      });
      releaseNotesLoaded = true;
    })
    .catch(() => {
      root.innerHTML = `<p class="empty-state">Release notes could not be loaded.</p>`;
    });
}

function bindSettings() {
  const map = {
    "set-hitboxes": "hitboxes",
    "set-strict": "strict",
    "set-test": "testMode",
    "set-notify": "notifications",
    "set-sound": "sound",
  };
  for (const [id, key] of Object.entries(map)) {
    const el = document.querySelector(`#${id}`);
    if (!el) continue;
    el.checked = !!settings[key];
    el.addEventListener("change", () => {
      settings[key] = el.checked;
      saveSettings();
    });
  }
  const opacity = document.querySelector("#opacity");
  const opacityValue = document.querySelector("#opacity-value");
  if (opacity) {
    opacity.value = String(Math.max(40, settings.opacity ?? 100));
    if (opacityValue) opacityValue.textContent = `${opacity.value}%`;
    opacity.addEventListener("input", () => {
      settings.opacity = Math.max(40, Number(opacity.value) || 100);
      if (opacityValue) opacityValue.textContent = `${settings.opacity}%`;
      saveSettings();
    });
  }
}

document.querySelector("#side-collapse")?.addEventListener("click", () => {
  const dash = document.querySelector(".dash");
  const collapsed = dash.classList.toggle("is-collapsed");
  document.querySelector("#side-collapse")?.setAttribute("aria-expanded", String(!collapsed));
});

document.querySelectorAll(".side-nav [data-open]").forEach((btn) => {
  btn.addEventListener("click", () => openSection(btn.dataset.open));
});

document.querySelectorAll("[data-mode]").forEach((btn) => {
  btn.addEventListener("click", () => {
    setMode(btn.dataset.mode);
    syncDashStatus();
  });
});

document.querySelector("#dash-timed-mins")?.addEventListener("change", (e) => {
  settings.timedMins = Number(e.target.value) || 5;
  saveSettings();
  syncDashStatus();
  hostPost({ cmd: "notify-pill", type: "settings" });
});

document.querySelectorAll("[data-dashboard-mode]").forEach((btn) => {
  btn.addEventListener("click", () => setAppearance(btn.dataset.dashboardMode));
});

document.querySelectorAll("[data-widget-mode]").forEach((btn) => {
  btn.addEventListener("click", () => {
    settings.light = btn.dataset.widgetMode === "light";
    saveSettings();
    syncWidgetModes();
  });
});

window.addEventListener("storage", (e) => {
  if (e.key === "securely-scan-mode" && e.newValue) {
    if (["quick", "timed", "continuous"].includes(e.newValue)) {
      mode = e.newValue;
      document.querySelectorAll("[data-mode]").forEach((btn) => {
        btn.setAttribute("aria-checked", String(btn.dataset.mode === mode));
      });
      const durationRow = document.querySelector("#duration-row");
      if (durationRow) durationRow.hidden = mode !== "timed";
      syncDashStatus();
    }
  }
  if (e.key === SETTINGS_KEY || e.key === LOOK_KEY) {
    settings = loadSettings();
    syncWidgetModes();
    const map = {
      "set-hitboxes": "hitboxes",
      "set-strict": "strict",
      "set-test": "testMode",
      "set-notify": "notifications",
      "set-sound": "sound",
    };
    for (const [id, key] of Object.entries(map)) {
      const el = document.querySelector(`#${id}`);
      if (el) el.checked = !!settings[key];
    }
    const opacity = document.querySelector("#opacity");
    const opacityValue = document.querySelector("#opacity-value");
    if (opacity) {
      opacity.value = String(Math.max(40, settings.opacity ?? 100));
      if (opacityValue) opacityValue.textContent = `${opacity.value}%`;
    }
    const timedSel = document.querySelector("#dash-timed-mins");
    if (timedSel && settings.timedMins) timedSel.value = String(settings.timedMins);
    syncDashStatus();
  }
  if (e.key === "securely-runtime" || e.key === AUDIT_KEY) {
    syncDashStatus();
    syncAlerts();
  }
});

function loadLicense() {
  try {
    return JSON.parse(localStorage.getItem(LICENSE_KEY) || "null");
  } catch {
    return null;
  }
}

function saveLicenseLocal(next) {
  localStorage.setItem(LICENSE_KEY, JSON.stringify(next));
  try {
    window.dispatchEvent(new StorageEvent("storage", { key: LICENSE_KEY, newValue: JSON.stringify(next) }));
  } catch { /* ignore */ }
}

async function persistLicenseToHost(next) {
  saveLicenseLocal(next);
  try {
    await hostRequest(
      "license-set",
      {
        email: next.email || "",
        active: !!next.active,
        status: next.status || "",
        sessionId: next.sessionId || "",
      },
      8000,
    );
  } catch { /* preview / host busy — local still set */ }
}

function isSuiteLicensed() {
  return !!(loadLicense()?.active);
}

function paintBilling() {
  const lic = loadLicense();
  const active = !!lic?.active;
  const tag = document.querySelector("#license-status");
  const copy = document.querySelector("#license-status-copy");
  const btn = document.querySelector("#license-stripe");
  if (tag) {
    tag.textContent = active ? "Active" : "Inactive";
    tag.dataset.state = active ? "active" : "inactive";
    tag.classList.toggle("is-active", active);
    tag.classList.toggle("is-inactive", !active);
  }
  if (copy) {
    copy.textContent = active
      ? `Licensed to ${lic.email || "your Stripe email"}. Analyze, Protect, VPN, and scans are unlocked.`
      : "No active subscription on this computer yet.";
  }
  if (btn) {
    btn.textContent = active ? "Manage on Stripe" : "Subscribe with Stripe — $3/mo";
  }
  document.documentElement.dataset.licensed = active ? "1" : "0";
  document.querySelectorAll("[data-needs-license]").forEach((el) => {
    el.toggleAttribute("disabled", !active);
  });
}

function requireSuiteLicense(feature) {
  if (isSuiteLicensed()) return true;
  openSection("billing");
  const msg = document.querySelector("#license-message");
  if (msg) {
    msg.textContent = `Subscribe to unlock ${feature || "Securely"}. Status becomes Active right after Stripe confirms.`;
  }
  return false;
}

async function applyLicense(email, active, status, message, sessionId) {
  const clean = String(email || "").trim().toLowerCase();
  // Promo / 100% off can complete before email lands — still unlock when active.
  if (!clean && !active) return;
  const next = {
    email: clean || loadLicense()?.email || "",
    active: !!active,
    status: status || (active ? "active" : "inactive"),
    checkedAt: Date.now(),
    sessionId: sessionId || loadLicense()?.sessionId || "",
  };
  await persistLicenseToHost(next);
  paintBilling();
  const msg = document.querySelector("#license-message");
  if (msg && message) msg.textContent = message;
}

function stopLicenseWatch() {
  if (licenseWatchTimer) {
    clearInterval(licenseWatchTimer);
    licenseWatchTimer = 0;
  }
}

function stopSessionWatch() {
  if (sessionWatchTimer) {
    clearInterval(sessionWatchTimer);
    sessionWatchTimer = 0;
  }
}

async function checkLicenseEmail(email) {
  const clean = String(email || "").trim().toLowerCase();
  if (!clean) return null;
  const res = await fetch(`${SITE_ORIGIN}/api/license`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: clean }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Could not verify subscription.");
  return { email: clean, active: !!data.active, status: data.status || "" };
}

async function checkCheckoutSession(sessionId) {
  const id = String(sessionId || "").trim();
  if (!id || !/^cs_[A-Za-z0-9_]+$/.test(id)) return null;
  const res = await fetch(`${SITE_ORIGIN}/api/checkout-status`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ sessionId: id }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Could not confirm checkout.");
  return {
    email: String(data.email || "").trim().toLowerCase(),
    active: !!data.active,
    status: data.status || "",
    sessionId: id,
  };
}

function startLicenseWatch(email) {
  const clean = String(email || "").trim().toLowerCase();
  if (!clean) return;
  const prev = (() => {
    try {
      return JSON.parse(localStorage.getItem(PENDING_CHECKOUT_KEY) || "null") || {};
    } catch {
      return {};
    }
  })();
  localStorage.setItem(
    PENDING_CHECKOUT_KEY,
    JSON.stringify({ ...prev, email: clean, startedAt: prev.startedAt || Date.now() }),
  );
  stopLicenseWatch();
  let tries = 0;
  const tick = async () => {
    tries += 1;
    if (tries > 60) {
      stopLicenseWatch();
      const msg = document.querySelector("#license-message");
      if (msg) msg.textContent = "Still waiting on Stripe. Finish checkout in the browser tab, then return here.";
      return;
    }
    try {
      const result = await checkLicenseEmail(clean);
      if (result?.active) {
        stopLicenseWatch();
        stopSessionWatch();
        localStorage.removeItem(PENDING_CHECKOUT_KEY);
        await applyLicense(
          result.email,
          true,
          result.status,
          "Subscription active — payment connected. You can run scans now.",
        );
      }
    } catch { /* keep polling */ }
  };
  void tick();
  licenseWatchTimer = setInterval(tick, 2500);
}

function startSessionWatch(sessionId) {
  const id = String(sessionId || "").trim();
  if (!id || !/^cs_[A-Za-z0-9_]+$/.test(id)) return;
  localStorage.setItem(
    PENDING_CHECKOUT_KEY,
    JSON.stringify({ sessionId: id, startedAt: Date.now() }),
  );
  stopSessionWatch();
  let tries = 0;
  const tick = async () => {
    tries += 1;
    if (tries > 72) {
      stopSessionWatch();
      const msg = document.querySelector("#license-message");
      if (msg) {
        msg.textContent =
          "Still confirming Stripe. Finish checkout (promo codes work on Stripe’s page), then return here.";
      }
      return;
    }
    try {
      const result = await checkCheckoutSession(id);
      if (result?.active) {
        stopSessionWatch();
        stopLicenseWatch();
        localStorage.removeItem(PENDING_CHECKOUT_KEY);
        await applyLicense(
          result.email,
          true,
          result.status || "active",
          "Subscription active — promo or payment connected. You can run scans now.",
          result.sessionId,
        );
        return;
      }
      if (result?.email && !loadLicense()?.active) {
        startLicenseWatch(result.email);
      }
    } catch { /* keep polling */ }
  };
  void tick();
  sessionWatchTimer = setInterval(tick, 2000);
}

async function openStripeCheckout() {
  const msg = document.querySelector("#license-message");
  if (msg) msg.textContent = "Starting Stripe checkout…";
  try {
    const res = await fetch(`${SITE_ORIGIN}/api/checkout`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.url) throw new Error(data.error || "Checkout unavailable.");
    // Prefer system browser via host — WebView2 window.open often drops opener/postMessage.
    hostPost({ cmd: "open-url", url: data.url });
    try {
      window.open(data.url, "securely-checkout");
    } catch { /* host open is enough */ }
    if (data.sessionId) {
      startSessionWatch(data.sessionId);
    } else {
      localStorage.setItem(PENDING_CHECKOUT_KEY, JSON.stringify({ startedAt: Date.now() }));
    }
    if (msg) {
      msg.textContent =
        "Checkout opened in Stripe. Enter a promo code if you have one — status flips to Active when it clears.";
    }
  } catch (err) {
    if (msg) msg.textContent = err.message || "Could not start checkout.";
  }
}

async function openStripePortal() {
  const msg = document.querySelector("#license-message");
  const email = loadLicense()?.email || "";
  if (!email) {
    if (msg) msg.textContent = "No saved subscription email yet — subscribe with Stripe first.";
    return;
  }
  if (msg) msg.textContent = "Opening Stripe portal…";
  try {
    const res = await fetch(`${SITE_ORIGIN}/api/portal`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.url) throw new Error(data.error || "Portal unavailable.");
    hostPost({ cmd: "open-url", url: data.url });
    if (msg) msg.textContent = "Stripe portal opened in your browser.";
  } catch (err) {
    if (msg) msg.textContent = err.message || "Could not open the portal.";
  }
}

document.querySelector("#license-stripe")?.addEventListener("click", () => {
  if (loadLicense()?.active) {
    void openStripePortal();
  } else {
    void openStripeCheckout();
  }
});

window.addEventListener("message", (event) => {
  const data = event.data;
  if (!data || data.type !== "securely-checkout-done") return;
  if (data.sessionId) startSessionWatch(data.sessionId);
  if (data.active) {
    stopLicenseWatch();
    localStorage.removeItem(PENDING_CHECKOUT_KEY);
    void applyLicense(
      data.email,
      true,
      data.status || "active",
      "Subscription active — payment connected. You can run scans now.",
      data.sessionId || "",
    );
    return;
  }
  if (data.email) startLicenseWatch(data.email);
});

window.addEventListener("focus", () => {
  try {
    const pending = JSON.parse(localStorage.getItem(PENDING_CHECKOUT_KEY) || "null");
    if (loadLicense()?.active) return;
    if (pending?.sessionId) startSessionWatch(pending.sessionId);
    else if (pending?.email) startLicenseWatch(pending.email);
  } catch { /* ignore */ }
});

async function hydrateLicenseFromHost() {
  try {
    const res = await hostRequest("license-get", {}, 5000);
    if (res?.license && typeof res.license === "object") {
      saveLicenseLocal({
        email: res.license.email || "",
        active: !!res.license.active,
        status: res.license.status || "",
        checkedAt: res.license.checkedAt || Date.now(),
        sessionId: res.license.sessionId || "",
      });
      paintBilling();
    }
  } catch { /* preview */ }
}

document.querySelector("#audit-refresh")?.addEventListener("click", syncAlerts);
document.querySelector("#audit-clear")?.addEventListener("click", () => {
  localStorage.setItem(AUDIT_KEY, "[]");
  syncAlerts();
});
async function playDashSound(file) {
  if (settings.sound === false) return;
  try {
    const audio = new Audio(`/sounds/${file}`);
    await audio.play();
  } catch { /* ignore */ }
}

document.querySelector("#set-test-notify")?.addEventListener("click", () => {
  const rows = JSON.parse(localStorage.getItem(AUDIT_KEY) || "[]");
  rows.unshift({ t: Date.now(), kind: "UNSURE", text: "Test notification — desktop toast wires through core next." });
  localStorage.setItem(AUDIT_KEY, JSON.stringify(rows.slice(0, 200)));
  playDashSound("notification-alert.mp3");
  syncAlerts();
  openSection("audit");
});

document.querySelector("#set-sound")?.addEventListener("change", (e) => {
  if (e.target.checked) playDashSound("new-notification.mp3");
});

document.querySelector("#toggle-pill")?.addEventListener("click", () => {
  pillShown = !pillShown;
  hostPost({ cmd: "visible", shown: pillShown });
});
document.querySelector("#quit-securely")?.addEventListener("click", () => hostPost({ cmd: "quit" }));

/* ——— Analyze / Antivirus / VPN suite ——— */
const AV_KEY = "securely-av";
const VPN_KEY = "securely-vpn";
const AV_EVENTS_KEY = "securely-av-events";

let analyzeFile = null;

function loadAv() {
  try {
    return {
      profile: "balanced",
      watchDownloads: true,
      ...JSON.parse(localStorage.getItem(AV_KEY) || "{}"),
    };
  } catch {
    return { profile: "balanced", watchDownloads: true };
  }
}

function saveAv(next) {
  localStorage.setItem(AV_KEY, JSON.stringify(next));
}

function loadVpn() {
  try {
    return {
      connected: false,
      region: "us-la",
      killSwitch: true,
      splitTunnel: false,
      config: "",
      connectedAt: 0,
      wireguard: false,
      ...JSON.parse(localStorage.getItem(VPN_KEY) || "{}"),
    };
  } catch {
    return { connected: false, region: "us-la", killSwitch: true, splitTunnel: false, config: "", connectedAt: 0, wireguard: false };
  }
}

function saveVpn(next) {
  localStorage.setItem(VPN_KEY, JSON.stringify(next));
}

function pushAvEvent(text, kind = "PROTECT") {
  const rows = JSON.parse(localStorage.getItem(AV_EVENTS_KEY) || "[]");
  rows.unshift({ t: Date.now(), kind, text });
  localStorage.setItem(AV_EVENTS_KEY, JSON.stringify(rows.slice(0, 40)));
  const audit = JSON.parse(localStorage.getItem(AUDIT_KEY) || "[]");
  audit.unshift({ t: Date.now(), kind, text, summary: text });
  localStorage.setItem(AUDIT_KEY, JSON.stringify(audit.slice(0, 200)));
}

async function sha256File(file) {
  const buf = await file.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", buf);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function paintAnalyzeResult(data, fallbackSubject = "") {
  const card = document.querySelector("#analyze-result");
  const verdictEl = document.querySelector("#analyze-verdict");
  const summaryEl = document.querySelector("#analyze-summary");
  const evidenceEl = document.querySelector("#analyze-evidence");
  const tipsEl = document.querySelector("#analyze-tips");
  if (!card) return;
  const verdict = data?.verdict || "unknown";
  card.dataset.verdict = verdict;
  if (verdictEl) verdictEl.textContent = verdict;
  if (summaryEl) {
    summaryEl.textContent =
      data?.summary ||
      (data?.error ? data.error : `Checked ${fallbackSubject || "item"}.`);
  }
  if (evidenceEl) {
    evidenceEl.replaceChildren();
    for (const row of data?.evidence || []) {
      const li = document.createElement("li");
      li.textContent = `${row.source}: ${row.detail}`;
      evidenceEl.append(li);
    }
  }
  if (tipsEl) {
    const tips = data?.tips || [];
    tipsEl.hidden = !tips.length;
    tipsEl.replaceChildren();
    for (const tip of tips) {
      const li = document.createElement("li");
      li.textContent = tip;
      tipsEl.append(li);
    }
  }
}

async function runThreatAnalyze(payload) {
  const res = await fetch(`${SITE_ORIGIN}/api/analyze-threat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Analysis failed.");
  return data;
}

function setAnalyzeBusy(on) {
  document.querySelector("#analyze-url-btn")?.toggleAttribute("disabled", !!on);
  document.querySelector("#analyze-file-btn")?.toggleAttribute("disabled", !!on || !analyzeFile);
}

function bindAnalyze() {
  const drop = document.querySelector("#analyze-drop");
  const fileInput = document.querySelector("#analyze-file");
  const meta = document.querySelector("#analyze-file-meta");
  const fileBtn = document.querySelector("#analyze-file-btn");

  function takeFile(file) {
    if (!file) return;
    if (file.size > 32 * 1024 * 1024) {
      paintAnalyzeResult({ verdict: "unknown", summary: "File is over 32 MB — pick a smaller sample or hash it elsewhere.", evidence: [], tips: [] });
      return;
    }
    analyzeFile = file;
    if (meta) {
      meta.hidden = false;
      meta.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
    }
    if (fileBtn) fileBtn.disabled = false;
  }

  document.querySelector("#analyze-pick")?.addEventListener("click", () => fileInput?.click());
  drop?.addEventListener("click", () => fileInput?.click());
  fileInput?.addEventListener("change", () => takeFile(fileInput.files?.[0]));
  drop?.addEventListener("dragover", (e) => {
    e.preventDefault();
    drop.classList.add("is-drag");
  });
  drop?.addEventListener("dragleave", () => drop.classList.remove("is-drag"));
  drop?.addEventListener("drop", (e) => {
    e.preventDefault();
    drop.classList.remove("is-drag");
    takeFile(e.dataTransfer?.files?.[0]);
  });

  document.querySelector("#analyze-url-btn")?.addEventListener("click", async () => {
    if (!requireSuiteLicense("Analyze")) return;
    const url = document.querySelector("#analyze-url")?.value?.trim() || "";
    if (!url) {
      paintAnalyzeResult({ verdict: "unknown", summary: "Paste a link first.", evidence: [], tips: [] });
      return;
    }
    setAnalyzeBusy(true);
    paintAnalyzeResult({ verdict: "unknown", summary: "Checking link…", evidence: [], tips: [] });
    try {
      const data = await runThreatAnalyze({ type: "url", url });
      paintAnalyzeResult(data, url);
      pushAvEvent(`URL ${data.verdict}: ${url}`, data.verdict === "malicious" ? "PHISHING" : data.verdict === "suspicious" ? "SUSPICIOUS" : "ANALYZE");
    } catch (err) {
      paintAnalyzeResult({ verdict: "unknown", summary: err.message || "Link check failed.", evidence: [], tips: [] });
    } finally {
      setAnalyzeBusy(false);
    }
  });

  fileBtn?.addEventListener("click", async () => {
    if (!requireSuiteLicense("Analyze")) return;
    if (!analyzeFile) return;
    setAnalyzeBusy(true);
    paintAnalyzeResult({ verdict: "unknown", summary: "Hashing on this PC…", evidence: [], tips: [] });
    try {
      const hash = await sha256File(analyzeFile);
      paintAnalyzeResult({
        verdict: "unknown",
        summary: `SHA-256 ${hash.slice(0, 16)}… — looking up reputation…`,
        evidence: [{ source: "local", detail: "Hash computed locally; file bytes are not uploaded by default." }],
        tips: [],
      });
      const data = await runThreatAnalyze({
        type: "file",
        hash,
        fileName: analyzeFile.name,
        fileSize: analyzeFile.size,
        mimeType: analyzeFile.type || "",
      });
      paintAnalyzeResult(data, analyzeFile.name);
      pushAvEvent(
        `File ${data.verdict}: ${analyzeFile.name}`,
        data.verdict === "malicious" ? "PHISHING" : data.verdict === "suspicious" ? "SUSPICIOUS" : "ANALYZE",
      );
      paintAv();
    } catch (err) {
      paintAnalyzeResult({ verdict: "unknown", summary: err.message || "File analysis failed.", evidence: [], tips: [] });
    } finally {
      setAnalyzeBusy(false);
    }
  });
}

function paintAv() {
  const av = loadAv();
  document.querySelectorAll("[data-av-profile]").forEach((btn) => {
    btn.setAttribute("aria-checked", String(btn.dataset.avProfile === av.profile));
  });
  const watch = document.querySelector("#av-watch-downloads");
  if (watch) watch.checked = !!av.watchDownloads;
  const status = document.querySelector("#av-status");
  if (status) {
    status.textContent = `Ready — ${av.profile[0].toUpperCase()}${av.profile.slice(1)} profile${
      av.watchDownloads ? " · Downloads watch on" : ""
    }.`;
  }
  const list = document.querySelector("#av-events");
  if (!list) return;
  const rows = JSON.parse(localStorage.getItem(AV_EVENTS_KEY) || "[]");
  if (!rows.length) {
    list.innerHTML = `<p class="empty-state">No protect events yet. Scan a file to see results here.</p>`;
    return;
  }
  list.replaceChildren();
  for (const row of rows.slice(0, 20)) {
    const el = document.createElement("div");
    el.className = "threat-row";
    el.innerHTML = `<span class="kind">${row.kind || "PROTECT"}</span><span>${row.text || ""}</span><div class="muted">${new Date(row.t).toLocaleString()}</div>`;
    list.append(el);
  }
}

function bindAv() {
  document.querySelectorAll("[data-av-profile]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const av = loadAv();
      av.profile = btn.dataset.avProfile || "balanced";
      saveAv(av);
      paintAv();
    });
  });
  document.querySelector("#av-watch-downloads")?.addEventListener("change", (e) => {
    const av = loadAv();
    av.watchDownloads = !!e.target.checked;
    saveAv(av);
    paintAv();
  });
  document.querySelector("#av-open-defender")?.addEventListener("click", () => {
    hostPost({ cmd: "open-url", url: "ms-settings:windowsdefender" });
    window.open("ms-settings:windowsdefender", "_blank");
  });
  document.querySelector("#av-open-analyze")?.addEventListener("click", () => openSection("analyze"));
  document.querySelector("#av-scan-files")?.addEventListener("click", async () => {
    if (!requireSuiteLicense("Protect")) return;
    const status = document.querySelector("#av-status");
    try {
      // Prefer host dialog + Defender MpCmdRun (ClamAV/Jackal-style local first, then cloud hash).
      const picked = await hostRequest("av-scan", { action: "pick" }, 120000);
      const paths = JSON.parse(picked.pathsJson || "[]").slice(0, 12);
      if (!paths.length) return;
      if (status) status.textContent = `Defender + hash scanning ${paths.length} file(s)…`;
      const hostScan = await hostRequest("av-scan", { action: "scan", paths }, 180000);
      const rows = hostScan.result?.results || [];
      for (const row of rows) {
        if (row.threat) {
          pushAvEvent(`Defender threat: ${row.name}`, "PHISHING");
          continue;
        }
        try {
          const data = await runThreatAnalyze({
            type: "file",
            hash: row.sha256,
            fileName: row.name,
            fileSize: 0,
            mimeType: "",
          });
          pushAvEvent(
            `Scan ${data.verdict}: ${row.name} (Defender ${row.defender})`,
            data.verdict === "malicious" ? "PHISHING" : "PROTECT",
          );
        } catch (err) {
          pushAvEvent(`Hash OK · cloud lookup failed: ${row.name}`, "UNSURE");
        }
      }
      paintAv();
      if (status) status.textContent = "Scan finished — Defender + reputation.";
      playDashSound("notification-pluck-off.mp3");
    } catch {
      // Browser preview fallback
      const input = document.createElement("input");
      input.type = "file";
      input.multiple = true;
      input.addEventListener("change", async () => {
        const files = [...(input.files || [])].slice(0, 8);
        if (!files.length) return;
        if (status) status.textContent = `Scanning ${files.length} file(s)…`;
        for (const file of files) {
          try {
            const hash = await sha256File(file);
            const data = await runThreatAnalyze({
              type: "file",
              hash,
              fileName: file.name,
              fileSize: file.size,
              mimeType: file.type || "",
            });
            pushAvEvent(`Scan ${data.verdict}: ${file.name}`, data.verdict === "malicious" ? "PHISHING" : "PROTECT");
          } catch (err) {
            pushAvEvent(`Scan failed: ${file.name} — ${err.message || "error"}`, "UNSURE");
          }
        }
        paintAv();
        if (status) status.textContent = "Scan finished — see recent protect events.";
      });
      input.click();
    }
  });

  hostRequest("av-scan", { action: "status" })
    .then((res) => {
      const copy = document.querySelector("#av-defender-copy");
      if (copy && res.defender?.hint) copy.textContent = res.defender.hint;
    })
    .catch(() => {});
}

const VPN_LOCATIONS = [
  { id: "us-la", name: "United States", city: "Los Angeles", tag: "Fastest", flag: "🇺🇸", x: 18, y: 48, lat: 34.05, lon: -118.24 },
  { id: "us-ny", name: "United States", city: "New York", tag: "Double VPN", flag: "🇺🇸", x: 28, y: 42, lat: 40.71, lon: -74.0 },
  { id: "ca", name: "Canada", city: "Toronto", tag: "Fastest", flag: "🇨🇦", x: 24, y: 36, lat: 43.65, lon: -79.38 },
  { id: "nl", name: "Netherlands", city: "Amsterdam", tag: "Onion over VPN", flag: "🇳🇱", x: 50, y: 38, lat: 52.37, lon: 4.9 },
  { id: "de", name: "Germany", city: "Frankfurt", tag: "Fastest", flag: "🇩🇪", x: 52, y: 40, lat: 50.11, lon: 8.68 },
  { id: "uk", name: "United Kingdom", city: "London", tag: "Fastest", flag: "🇬🇧", x: 47, y: 36, lat: 51.5, lon: -0.12 },
  { id: "jp", name: "Japan", city: "Tokyo", tag: "Fastest", flag: "🇯🇵", x: 82, y: 44, lat: 35.68, lon: 139.69 },
];

let vpnGeo = null;
let vpnMapZoom = 1;
let vpnBusy = false;

function projectLatLon(lat, lon) {
  const x = ((lon + 180) / 360) * 100;
  const y = ((90 - lat) / 180) * 100;
  return { x: Math.min(96, Math.max(4, x)), y: Math.min(90, Math.max(10, y)) };
}

async function fetchVpnGeo() {
  try {
    const res = await fetch(`${SITE_ORIGIN}/api/ip-geo`);
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "lookup failed");
    vpnGeo = data;
    return data;
  } catch (err) {
    vpnGeo = { ok: false, ip: "—", label: "Location unavailable", error: err.message };
    return vpnGeo;
  }
}

function paintVpn() {
  const vpn = loadVpn();
  const shell = document.querySelector("#vpn-map-shell");
  const btn = document.querySelector("#vpn-connect");
  const kill = document.querySelector("#vpn-kill");
  const split = document.querySelector("#vpn-split");
  const config = document.querySelector("#vpn-config");
  const region = document.querySelector("#vpn-region");
  const ipEl = document.querySelector("#vpn-map-ip");
  const title = document.querySelector("#vpn-loc-title");
  const state = document.querySelector("#vpn-loc-state");
  const flag = document.querySelector("#vpn-flag");
  const hint = document.querySelector("#vpn-engine-hint");

  if (region) region.value = vpn.region || "auto";
  if (kill) kill.checked = vpn.killSwitch !== false;
  if (split) split.checked = !!vpn.splitTunnel;
  if (config && document.activeElement !== config) config.value = vpn.config || "";

  shell?.classList.toggle("is-on", !!vpn.connected);
  if (btn) {
    btn.textContent = vpnBusy ? "Working…" : vpn.connected ? "Disconnect" : "Quick Connect";
    btn.disabled = !!vpnBusy;
  }

  const loc = VPN_LOCATIONS.find((l) => l.id === vpn.region) || VPN_LOCATIONS[0];
  const geoLabel = vpnGeo?.label || (vpn.connected ? `${loc.city}, ${loc.name}` : "Detecting…");
  const ip = vpnGeo?.ip || "—";
  const elapsed = vpn.connected && vpn.connectedAt
    ? Math.max(0, Math.floor((Date.now() - vpn.connectedAt) / 1000))
    : 0;
  if (ipEl) {
    ipEl.textContent = vpn.connected
      ? `IP ${ip} · ${vpnGeo?.country || loc.name} · ${elapsed}s`
      : `IP ${ip} · ${vpnGeo?.country || "—"}`;
  }
  if (title) title.textContent = vpn.connected ? `${loc.city}, ${loc.name}` : geoLabel;
  if (state) state.textContent = vpn.connected ? "Secured" : "Unsecured";
  if (flag) flag.textContent = vpn.connected ? loc.flag : vpnGeo?.countryCode ? flagFor(vpnGeo.countryCode) : "🌐";
  if (hint) {
    hint.textContent = String(vpn.config || "").trim()
      ? "BYO WireGuard profile saved."
      : "Paste a .conf to enable a real location change.";
  }

  const pins = document.querySelector("#vpn-pins");
  if (pins) {
    pins.replaceChildren();
    for (const spot of VPN_LOCATIONS) {
      const pin = document.createElement("button");
      pin.type = "button";
      pin.className = "vpn-pin" + (vpn.region === spot.id || (vpn.connected && vpn.region === spot.id) ? " is-active" : "");
      if (vpn.connected && vpn.region === spot.id) pin.classList.add("is-active");
      pin.style.left = `${spot.x}%`;
      pin.style.top = `${spot.y}%`;
      pin.title = `${spot.city}, ${spot.name}`;
      pin.addEventListener("click", () => {
        const next = loadVpn();
        next.region = spot.id;
        saveVpn(next);
        paintVpn();
      });
      pins.append(pin);
    }
    if (vpnGeo?.lat != null && vpnGeo?.lon != null) {
      const p = projectLatLon(vpnGeo.lat, vpnGeo.lon);
      const here = document.createElement("button");
      here.type = "button";
      here.className = "vpn-pin is-active";
      here.style.left = `${p.x}%`;
      here.style.top = `${p.y}%`;
      here.title = `Current exit · ${vpnGeo.label}`;
      pins.append(here);
    }
  }

  const recents = document.querySelector("#vpn-recents");
  if (recents) {
    recents.replaceChildren();
    for (const spot of VPN_LOCATIONS.slice(0, 5)) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "vpn-recent" + (vpn.region === spot.id ? " is-active" : "");
      card.innerHTML = `<div class="vpn-recent-flag">${spot.flag}</div><strong>${spot.name}</strong><span>${spot.tag}</span>`;
      card.addEventListener("click", () => {
        const next = loadVpn();
        next.region = spot.id;
        saveVpn(next);
        paintVpn();
      });
      recents.append(card);
    }
  }
}

function flagFor(code) {
  const c = String(code || "").toUpperCase();
  if (c.length !== 2) return "🌐";
  return String.fromCodePoint(...[...c].map((ch) => 127397 + ch.charCodeAt(0)));
}

function bindVpn() {
  const persist = () => {
    const vpn = loadVpn();
    vpn.region = document.querySelector("#vpn-region")?.value || vpn.region || "us-la";
    vpn.killSwitch = !!document.querySelector("#vpn-kill")?.checked;
    vpn.splitTunnel = !!document.querySelector("#vpn-split")?.checked;
    vpn.config = document.querySelector("#vpn-config")?.value || "";
    saveVpn(vpn);
    paintVpn();
  };

  document.querySelector("#vpn-kill")?.addEventListener("change", persist);
  document.querySelector("#vpn-split")?.addEventListener("change", persist);
  document.querySelector("#vpn-save-config")?.addEventListener("click", () => {
    persist();
    playDashSound("new-notification.mp3");
  });
  document.querySelector("#vpn-map-refresh")?.addEventListener("click", async () => {
    await fetchVpnGeo();
    paintVpn();
  });
  document.querySelector("#vpn-wg-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    hostPost({ cmd: "open-url", url: "https://www.wireguard.com/install/" });
  });
  document.querySelector("#vpn-all-locations")?.addEventListener("click", () => {
    document.querySelector("#vpn-config")?.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  let zoom = 1;
  document.querySelector("#vpn-zoom-in")?.addEventListener("click", () => {
    zoom = Math.min(1.6, zoom + 0.15);
    const canvas = document.querySelector("#vpn-map-canvas");
    if (canvas) canvas.style.transform = `scale(${zoom})`;
  });
  document.querySelector("#vpn-zoom-out")?.addEventListener("click", () => {
    zoom = Math.max(1, zoom - 0.15);
    const canvas = document.querySelector("#vpn-map-canvas");
    if (canvas) canvas.style.transform = `scale(${zoom})`;
  });

  document.querySelector("#vpn-connect")?.addEventListener("click", async () => {
    if (!requireSuiteLicense("VPN")) return;
    const vpn = loadVpn();
    vpn.region = document.querySelector("#vpn-region")?.value || vpn.region || "us-la";
    vpn.killSwitch = !!document.querySelector("#vpn-kill")?.checked;
    vpn.splitTunnel = !!document.querySelector("#vpn-split")?.checked;
    vpn.config = document.querySelector("#vpn-config")?.value || vpn.config || "";
    const connecting = !vpn.connected;
    if (connecting && !String(vpn.config || "").trim()) {
      const state = document.querySelector("#vpn-loc-state");
      if (state) {
        state.textContent = "Need WireGuard .conf";
        state.style.color = "#fbbf24";
      }
      document.querySelector("#vpn-config")?.focus();
      return;
    }

    vpnBusy = true;
    paintVpn();
    try {
      const res = await hostRequest("vpn", {
        action: connecting ? "connect" : "disconnect",
        config: vpn.config,
        killSwitch: vpn.killSwitch,
        splitTunnel: vpn.splitTunnel,
        region: vpn.region,
      });
      if (!res.ok && connecting) {
        vpn.connected = false;
        saveVpn(vpn);
        const state = document.querySelector("#vpn-loc-state");
        if (state) {
          state.textContent = res.message || "Connect failed";
          state.style.color = "#f87171";
        }
        playDashSound("notification-alert.mp3");
        return;
      }
      vpn.connected = connecting ? !!res.connected || !!res.ok : false;
      vpn.connectedAt = vpn.connected ? Date.now() : 0;
      vpn.wireguard = !!res.wireguard;
      saveVpn(vpn);
      await new Promise((r) => setTimeout(r, connecting ? 1800 : 400));
      await fetchVpnGeo();
      paintVpn();
      playDashSound(vpn.connected ? "notification-pluck-off.mp3" : "menu-open.mp3");
    } catch (err) {
      vpn.connected = false;
      saveVpn(vpn);
      const state = document.querySelector("#vpn-loc-state");
      if (state) state.textContent = err.message || "Host VPN error";
    } finally {
      vpnBusy = false;
      paintVpn();
    }
  });

  fetchVpnGeo().then(() => paintVpn());
  hostRequest("vpn", { action: "status" })
    .then((res) => {
      const vpn = loadVpn();
      if (res.connected) {
        vpn.connected = true;
        vpn.connectedAt = vpn.connectedAt || Date.now();
      }
      vpn.wireguard = !!res.wireguard;
      saveVpn(vpn);
      paintVpn();
    })
    .catch(() => {});
}

function bindSuiteChannels() {
  bindAnalyze();
  bindAv();
  bindVpn();
  paintAv();
  paintVpn();
}

const savedAppear = localStorage.getItem(APPEAR_KEY) || "light";
setAppearance(savedAppear);
syncWidgetModes();
bindSettings();
bindSuiteChannels();

const tab = new URLSearchParams(location.search).get("tab") || "dashboard";
openSection(tab);
const savedMode = localStorage.getItem("securely-scan-mode") || "quick";
setMode(["quick", "timed", "continuous"].includes(savedMode) ? savedMode : "quick");
const timedSelect = document.querySelector("#dash-timed-mins");
if (timedSelect && settings.timedMins) timedSelect.value = String(settings.timedMins);
syncDashStatus();
syncAlerts();
paintBilling();
void hydrateLicenseFromHost().then(() => {
  try {
    const pending = JSON.parse(localStorage.getItem(PENDING_CHECKOUT_KEY) || "null");
    if (loadLicense()?.active) return;
    if (pending?.sessionId) {
      startSessionWatch(pending.sessionId);
      const msg = document.querySelector("#license-message");
      if (msg) msg.textContent = "Watching Stripe checkout — promo codes unlock as soon as Stripe confirms.";
    } else if (pending?.email) {
      startLicenseWatch(pending.email);
      const msg = document.querySelector("#license-message");
      if (msg) msg.textContent = "Watching Stripe for your payment — status updates automatically.";
    }
  } catch { /* ignore */ }
});

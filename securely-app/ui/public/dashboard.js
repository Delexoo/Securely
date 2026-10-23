const SETTINGS_KEY = "securely-settings";
const AUDIT_KEY = "securely-audit";
const LOOK_KEY = "securely-look";
const APPEAR_KEY = "securely-dash-appearance";

function hostPost(payload) {
  try {
    if (window.chrome?.webview?.postMessage) {
      window.chrome.webview.postMessage(JSON.stringify(payload));
    }
  } catch { /* preview */ }
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

const SITE_ORIGIN = "https://trysecurely.vercel.app";
const LICENSE_KEY = "securely-license";

function openSection(name) {
  const allowed = ["monitor", "settings", "billing", "audit", "releases", "credits"];
  const tabMap = {
    dashboard: "monitor",
    settings: "settings",
    billing: "billing",
    audit: "audit",
    releases: "releases",
    credits: "credits",
    monitor: "monitor",
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
  if (id === "billing") paintBilling();
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

const PENDING_CHECKOUT_KEY = "securely-pending-checkout";
let licenseWatchTimer = 0;

function saveLicenseLocal(next) {
  localStorage.setItem(LICENSE_KEY, JSON.stringify(next));
  try {
    window.dispatchEvent(new StorageEvent("storage", { key: LICENSE_KEY, newValue: JSON.stringify(next) }));
  } catch { /* ignore */ }
}

function paintBilling() {
  const lic = loadLicense();
  const tag = document.querySelector("#license-status");
  const copy = document.querySelector("#license-status-copy");
  const btn = document.querySelector("#license-stripe");
  if (tag) {
    tag.textContent = lic?.active ? "Active" : "Inactive";
    tag.dataset.state = lic?.active ? "active" : "inactive";
  }
  if (copy) {
    copy.textContent = lic?.active
      ? `Licensed to ${lic.email}. Scans are unlocked.`
      : "No active subscription on this computer yet.";
  }
  if (btn) {
    btn.textContent = lic?.active ? "Manage on Stripe" : "Subscribe with Stripe — $3/mo";
  }
}

function applyLicense(email, active, status, message) {
  const clean = String(email || "").trim().toLowerCase();
  if (!clean) return;
  saveLicenseLocal({
    email: clean,
    active: !!active,
    status: status || (active ? "active" : "inactive"),
    checkedAt: Date.now(),
  });
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

function startLicenseWatch(email) {
  const clean = String(email || "").trim().toLowerCase();
  if (!clean) return;
  localStorage.setItem(PENDING_CHECKOUT_KEY, JSON.stringify({ email: clean, startedAt: Date.now() }));
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
        localStorage.removeItem(PENDING_CHECKOUT_KEY);
        applyLicense(
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
    // Keep opener so billing-success can postMessage back (do not use noopener).
    window.open(data.url, "securely-checkout");
    localStorage.setItem(PENDING_CHECKOUT_KEY, JSON.stringify({ startedAt: Date.now() }));
    if (msg) {
      msg.textContent = "Checkout opened in Stripe. Status flips to Active when payment clears.";
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
    window.open(data.url, "_blank", "noopener");
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
  if (data.active && data.email) {
    stopLicenseWatch();
    localStorage.removeItem(PENDING_CHECKOUT_KEY);
    applyLicense(
      data.email,
      true,
      data.status || "active",
      "Subscription active — payment connected. You can run scans now.",
    );
    return;
  }
  if (data.email) startLicenseWatch(data.email);
});

window.addEventListener("focus", () => {
  try {
    const pending = JSON.parse(localStorage.getItem(PENDING_CHECKOUT_KEY) || "null");
    if (pending?.email && !loadLicense()?.active) startLicenseWatch(pending.email);
  } catch { /* ignore */ }
});

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

const savedAppear = localStorage.getItem(APPEAR_KEY) || "light";
setAppearance(savedAppear);
syncWidgetModes();
bindSettings();

const tab = new URLSearchParams(location.search).get("tab") || "dashboard";
openSection(tab);
const savedMode = localStorage.getItem("securely-scan-mode") || "quick";
setMode(["quick", "timed", "continuous"].includes(savedMode) ? savedMode : "quick");
const timedSelect = document.querySelector("#dash-timed-mins");
if (timedSelect && settings.timedMins) timedSelect.value = String(settings.timedMins);
syncDashStatus();
syncAlerts();
paintBilling();
try {
  const pending = JSON.parse(localStorage.getItem(PENDING_CHECKOUT_KEY) || "null");
  if (pending?.email && !loadLicense()?.active) {
    startLicenseWatch(pending.email);
    const msg = document.querySelector("#license-message");
    if (msg) msg.textContent = "Watching Stripe for your payment — status updates automatically.";
  }
} catch { /* ignore */ }

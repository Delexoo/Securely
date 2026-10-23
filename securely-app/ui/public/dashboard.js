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
      opacity: 50,
      light: false,
      timedMins: 5,
      ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}"),
    };
  } catch {
    return { hitboxes: false, strict: false, testMode: false, notifications: true, sound: true, opacity: 50, light: false, timedMins: 5 };
  }
}

let settings = loadSettings();
let mode = "quick";
let pillShown = true;

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  localStorage.setItem(LOOK_KEY, JSON.stringify({ opacity: settings.opacity, light: settings.light }));
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
    btn.setAttribute("aria-checked", String(!!settings.light === light));
  });
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
}

function renderAudit(target) {
  const rows = JSON.parse(localStorage.getItem(AUDIT_KEY) || "[]");
  if (!rows.length) {
    target.innerHTML = `<p class="empty-state">No threats logged yet. Run a Quick Scan to start.</p>`;
    return;
  }
  target.replaceChildren();
  for (const row of rows.slice(0, 80)) {
    const el = document.createElement("div");
    el.className = "threat-row";
    const kind = document.createElement("span");
    kind.className = "kind";
    kind.textContent = row.kind || "EVENT";
    const body = document.createElement("span");
    body.textContent = row.text || "";
    const when = document.createElement("div");
    when.className = "muted";
    when.textContent = new Date(row.t).toLocaleString();
    el.append(kind, body, when);
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
    opacity.value = String(settings.opacity ?? 50);
    if (opacityValue) opacityValue.textContent = `${opacity.value}%`;
    opacity.addEventListener("input", () => {
      settings.opacity = Number(opacity.value) || 50;
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
  btn.addEventListener("click", () => setMode(btn.dataset.mode));
});

document.querySelector("#dash-timed-mins")?.addEventListener("change", (e) => {
  settings.timedMins = Number(e.target.value) || 5;
  saveSettings();
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

function loadLicense() {
  try {
    return JSON.parse(localStorage.getItem(LICENSE_KEY) || "null");
  } catch {
    return null;
  }
}

function paintBilling() {
  const lic = loadLicense();
  const tag = document.querySelector("#license-status");
  const copy = document.querySelector("#license-status-copy");
  const emailEl = document.querySelector("#license-email");
  if (emailEl && lic?.email && !emailEl.value) emailEl.value = lic.email;
  if (tag) tag.textContent = lic?.active ? "Active" : "Inactive";
  if (copy) {
    copy.textContent = lic?.active
      ? `Licensed to ${lic.email}. Scans are unlocked.`
      : "No active subscription on this computer yet.";
  }
}

async function activateLicense() {
  const msg = document.querySelector("#license-message");
  const email = document.querySelector("#license-email")?.value?.trim() || "";
  if (msg) msg.textContent = "Checking Stripe…";
  try {
    const res = await fetch(`${SITE_ORIGIN}/api/license`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Could not verify subscription.");
    localStorage.setItem(
      LICENSE_KEY,
      JSON.stringify({
        email: email.toLowerCase(),
        active: !!data.active,
        status: data.status || "",
        checkedAt: Date.now(),
      }),
    );
    paintBilling();
    if (msg) {
      msg.textContent = data.active
        ? "Subscription active. You can run scans from the pill."
        : "No active $3/month subscription for that email. Subscribe first, then Activate again.";
    }
  } catch (err) {
    if (msg) msg.textContent = err.message || "Activation failed.";
  }
}

document.querySelector("#license-activate")?.addEventListener("click", () => activateLicense());
document.querySelector("#license-subscribe")?.addEventListener("click", async () => {
  const msg = document.querySelector("#license-message");
  const email = document.querySelector("#license-email")?.value?.trim() || "";
  const promo = document.querySelector("#license-promo")?.value?.trim() || "";
  if (!email) {
    if (msg) msg.textContent = "Enter your Stripe email before Subscribe.";
    return;
  }
  if (msg) msg.textContent = "Starting Stripe checkout…";
  try {
    const res = await fetch(`${SITE_ORIGIN}/api/checkout`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, promo }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.url) throw new Error(data.error || "Checkout unavailable.");
    window.open(data.url, "_blank", "noopener");
    if (msg) {
      msg.textContent = promo
        ? "Checkout opened. Complete payment (promo applied if valid), then Activate."
        : "Checkout opened. Complete payment, then Activate with the same email.";
    }
  } catch (err) {
    if (msg) msg.textContent = err.message || "Could not start checkout.";
  }
});
document.querySelector("#license-portal")?.addEventListener("click", async () => {
  const msg = document.querySelector("#license-message");
  const email = document.querySelector("#license-email")?.value?.trim() || loadLicense()?.email || "";
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
});

document.querySelector("#dash-start")?.addEventListener("click", () => {
  const lic = loadLicense();
  if (!lic?.active) {
    openSection("billing");
    const msg = document.querySelector("#license-message");
    if (msg) msg.textContent = "Subscribe or Activate with your Stripe email before scanning.";
    return;
  }
  if (mode === "continuous") {
    localStorage.setItem("securely-continuous-ok", "1");
  }
  const mins = Number(document.querySelector("#dash-timed-mins")?.value) || 5;
  const status = document.querySelector("#dash-status");
  if (status) {
    status.textContent = mode === "timed" ? `Timed ${mins}m` : mode === "continuous" ? "Active" : "Scanning…";
  }
  if (mode === "quick") {
    const kind = settings.testMode ? "SUSPICIOUS" : "SAFE";
    const text = settings.testMode ? "Test Mode: fake phishing cue." : "Dashboard Quick Scan complete.";
    const rows = JSON.parse(localStorage.getItem(AUDIT_KEY) || "[]");
    rows.unshift({ t: Date.now(), kind, text });
    localStorage.setItem(AUDIT_KEY, JSON.stringify(rows.slice(0, 200)));
    syncAlerts();
    setTimeout(() => {
      if (status) status.textContent = "Idle";
    }, 700);
  }
});

document.querySelector("#dash-stop")?.addEventListener("click", () => {
  const status = document.querySelector("#dash-status");
  if (status) status.textContent = "Idle";
});

document.querySelector("#audit-quick")?.addEventListener("click", () => {
  setMode("quick");
  openSection("monitor");
  document.querySelector("#dash-start")?.click();
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
syncAlerts();

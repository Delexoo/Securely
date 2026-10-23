/**
 * File / URL / hash threat analysis (VirusTotal-like).
 * Patterns aligned with VirusTotal API v3 / vt-py / vt-cli:
 *   lookup → submit when unknown → poll analysis → engine stats.
 * POST { type: "url"|"hash"|"file", url?, hash?, fileName?, fileSize?, mimeType? }
 * Keys stay server-side: VIRUSTOTAL_API_KEY (optional), OPENROUTER_API_KEY (optional).
 */
import { setCors, rateLimit, requireAnalyzeKey, originAllowed } from "./_limits.js";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const DEFAULT_MODEL = "meta-llama/llama-3.3-8b-instruct";
const VT_API = "https://www.virustotal.com/api/v3";
const MAX_URL = 2048;
const MAX_NAME = 260;
const VT_POLL_MS = 1800;
const VT_POLL_TRIES = 8;


function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function isPrivateHost(hostname) {
  const h = String(hostname || "").toLowerCase();
  if (!h || h === "localhost" || h.endsWith(".local") || h.endsWith(".internal")) return true;
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(h)) {
    const p = h.split(".").map(Number);
    if (p[0] === 10 || p[0] === 127 || p[0] === 0) return true;
    if (p[0] === 192 && p[1] === 168) return true;
    if (p[0] === 172 && p[1] >= 16 && p[1] <= 31) return true;
  }
  return false;
}

function normalizeUrl(raw) {
  let s = String(raw || "").trim().slice(0, MAX_URL);
  if (!s) return null;
  if (!/^https?:\/\//i.test(s)) s = `https://${s}`;
  let u;
  try {
    u = new URL(s);
  } catch {
    return null;
  }
  if (!/^https?:$/i.test(u.protocol)) return null;
  if (isPrivateHost(u.hostname)) return null;
  return u.toString();
}

function normalizeHash(raw) {
  const h = String(raw || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-f0-9]/g, "");
  if ([32, 40, 64].includes(h.length)) return h;
  return "";
}

function scoreToVerdict(score) {
  if (score >= 70) return "malicious";
  if (score >= 35) return "suspicious";
  if (score <= 5) return "clean";
  return "unknown";
}

function urlId(url) {
  return Buffer.from(url).toString("base64url");
}

function vtHeaders(key) {
  return { "x-apikey": key, accept: "application/json" };
}

function parseVtObject(data) {
  const attrs = data?.data?.attributes || {};
  const stats = attrs.last_analysis_stats || attrs.stats || {};
  const results = attrs.last_analysis_results || {};
  const engines = Object.entries(results)
    .map(([name, v]) => ({
      name,
      category: v?.category || "undetected",
      result: v?.result || v?.category || "undetected",
    }))
    .sort((a, b) => {
      const rank = { malicious: 0, suspicious: 1, phishing: 0, malware: 0, spam: 2, malwareware: 2 };
      return (rank[a.category] ?? 9) - (rank[b.category] ?? 9) || a.name.localeCompare(b.name);
    })
    .slice(0, 32);
  const malicious = Number(stats.malicious) || 0;
  const suspicious = Number(stats.suspicious) || 0;
  const harmless = Number(stats.harmless) || 0;
  const undetected = Number(stats.undetected) || 0;
  const timeout = Number(stats.timeout) || 0;
  const typeUnsupported = Number(stats["type-unsupported"]) || 0;
  const total = malicious + suspicious + harmless + undetected + timeout + typeUnsupported;
  return {
    found: true,
    status: attrs.status || "completed",
    engines,
    malicious,
    suspicious,
    harmless,
    undetected,
    timeout,
    typeUnsupported,
    total,
    reputation: typeof attrs.reputation === "number" ? attrs.reputation : null,
    tags: Array.isArray(attrs.tags) ? attrs.tags.slice(0, 12) : [],
    analysisId: data?.data?.id || "",
  };
}

async function vtFetch(path, key, init = {}) {
  const res = await fetch(`${VT_API}${path}`, {
    ...init,
    headers: { ...vtHeaders(key), ...(init.headers || {}) },
  });
  if (res.status === 429) {
    await sleep(2500);
    return vtFetch(path, key, init);
  }
  return res;
}

async function vtGetReport(kind, id, key) {
  const path =
    kind === "url" ? `/urls/${urlId(id)}` : `/files/${encodeURIComponent(id)}`;
  const res = await vtFetch(path, key);
  if (res.status === 404) return { found: false };
  if (!res.ok) return null;
  return parseVtObject(await res.json());
}

async function vtPollAnalysis(analysisId, key) {
  if (!analysisId) return null;
  for (let i = 0; i < VT_POLL_TRIES; i++) {
    const res = await vtFetch(`/analyses/${encodeURIComponent(analysisId)}`, key);
    if (!res.ok) return null;
    const data = await res.json();
    const status = data?.data?.attributes?.status || "";
    if (status === "completed") return parseVtObject(data);
    await sleep(VT_POLL_MS);
  }
  return null;
}

/** Submit URL for fresh analysis (vt scan url / POST /urls). */
async function vtSubmitUrl(url, key) {
  const body = new URLSearchParams({ url });
  const res = await vtFetch("/urls", key, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) return null;
  const data = await res.json();
  const analysisId = data?.data?.id || "";
  const polled = await vtPollAnalysis(analysisId, key);
  if (polled) return polled;
  // Fall back to report after submit (analysis may still be queued).
  await sleep(1200);
  return vtGetReport("url", url, key);
}

/** Request re-analysis of a known hash (vt rescan). */
async function vtRescanFile(hash, key) {
  const res = await vtFetch(`/files/${encodeURIComponent(hash)}/analyse`, key, {
    method: "POST",
  });
  if (!res.ok) return null;
  const data = await res.json();
  return vtPollAnalysis(data?.data?.id || "", key);
}

async function vtLookup(kind, id, { submitIfMissing = true } = {}) {
  const key = process.env.VIRUSTOTAL_API_KEY || "";
  if (!key) return null;
  try {
    let report = await vtGetReport(kind, id, key);
    if (report?.found) return report;
    if (report && report.found === false && submitIfMissing && kind === "url") {
      const submitted = await vtSubmitUrl(id, key);
      if (submitted?.found) return { ...submitted, submitted: true };
      return { found: false, submitted: !!submitted };
    }
    if (report && report.found === false) return report;
    return report;
  } catch {
    return null;
  }
}

async function urlhausLookup(url) {
  try {
    const body = new URLSearchParams({ url });
    const res = await fetch("https://urlhaus-api.abuse.ch/v1/url/", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (data?.query_status === "ok") {
      return {
        listed: true,
        threat: data.threat || "malware_download",
        tags: Array.isArray(data.tags) ? data.tags.slice(0, 8) : [],
      };
    }
    return { listed: false };
  } catch {
    return null;
  }
}

function localUrlHeuristics(url) {
  const u = new URL(url);
  const host = u.hostname.toLowerCase();
  const path = `${u.pathname}${u.search}`.toLowerCase();
  const evidence = [];
  let score = 0;
  if (host.split(".").length > 4) {
    score += 15;
    evidence.push({ source: "heuristic", detail: "Unusually deep subdomain chain." });
  }
  if (/\d{1,3}(\.\d{1,3}){3}/.test(host)) {
    score += 25;
    evidence.push({ source: "heuristic", detail: "Raw IP used as host — common in phishing kits." });
  }
  if (/(login|verify|secure|account|wallet|seed|crypto|invoice|urgent)/.test(path + host)) {
    score += 12;
    evidence.push({ source: "heuristic", detail: "Path/host uses high-risk scam keywords." });
  }
  if (/\.(zip|exe|scr|js|vbs|msi|bat|cmd)(\?|$)/i.test(path)) {
    score += 30;
    evidence.push({ source: "heuristic", detail: "URL points at an executable or script download." });
  }
  if (u.protocol === "http:") {
    score += 8;
    evidence.push({ source: "heuristic", detail: "Plain HTTP (no TLS)." });
  }
  return { score, evidence };
}

function localFileHeuristics(fileName, fileSize, mimeType) {
  const name = String(fileName || "").slice(0, MAX_NAME);
  const lower = name.toLowerCase();
  const evidence = [];
  let score = 0;
  const risky = /\.(exe|scr|js|vbs|bat|cmd|ps1|msi|dll|com|pif|hta|wsf|jar|apk)$/i;
  const double = /\.(pdf|doc|docx|jpg|png|txt)\.(exe|scr|js|bat|cmd)$/i;
  if (double.test(lower)) {
    score += 55;
    evidence.push({ source: "heuristic", detail: "Double extension — classic malware disguise." });
  } else if (risky.test(lower)) {
    score += 28;
    evidence.push({ source: "heuristic", detail: `Executable-class file type (${lower.split(".").pop()}).` });
  }
  if (/(crack|keygen|warez|nulled|activation|patcher|cheat)/i.test(lower)) {
    score += 35;
    evidence.push({ source: "heuristic", detail: "Filename matches common piracy/malware lure words." });
  }
  if (/(wallet\.dat|seed|mnemonic|private.?key|id_rsa)/i.test(lower)) {
    score += 20;
    evidence.push({ source: "heuristic", detail: "Name suggests secrets — treat as sensitive, not just malware." });
  }
  const size = Number(fileSize) || 0;
  if (size > 0 && size < 800 && risky.test(lower)) {
    score += 10;
    evidence.push({ source: "heuristic", detail: "Very small executable — often a downloader stub." });
  }
  if (mimeType && /javascript|vbscript|x-msdownload|x-dosexec/i.test(mimeType)) {
    score += 18;
    evidence.push({ source: "heuristic", detail: `MIME type ${mimeType} is high-risk.` });
  }
  return { score, evidence };
}

async function aiSummary(prompt) {
  const key = process.env.OPENROUTER_API_KEY || "";
  if (!key) return "";
  try {
    const res = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://trysecurely.vercel.app",
        "X-Title": "Securely Analyze",
      },
      body: JSON.stringify({
        model: process.env.OPENROUTER_MODEL || DEFAULT_MODEL,
        max_tokens: 220,
        messages: [
          {
            role: "system",
            content:
              "You are Securely’s threat analyst. Given evidence about a file or URL, write 2 short sentences: (1) what the risk is, (2) one concrete protection tip. No markdown. Do not invent engines or scores.",
          },
          { role: "user", content: prompt.slice(0, 3500) },
        ],
      }),
    });
    if (!res.ok) return "";
    const data = await res.json();
    return String(data?.choices?.[0]?.message?.content || "").trim().slice(0, 600);
  } catch {
    return "";
  }
}

function tipsFor(verdict) {
  if (verdict === "malicious") {
    return [
      "Do not open or run this file/link.",
      "Delete the download and empty Recycle Bin.",
      "If you already ran it, disconnect from the network and scan with Windows Security.",
    ];
  }
  if (verdict === "suspicious") {
    return [
      "Verify the sender and open the official site yourself instead of this link.",
      "Prefer hashing and reputation checks before running unknown executables.",
      "Keep Securely screen monitoring on while browsing unfamiliar sites.",
    ];
  }
  if (verdict === "clean") {
    return [
      "No strong signals found — still avoid running unexpected attachments.",
      "Keep Windows Security real-time protection enabled.",
    ];
  }
  return [
    "Reputation is incomplete — treat as untrusted until verified.",
    "Upload hashes (not secrets) to a trusted multi-engine service if you need a second opinion.",
  ];
}

function applyVtEvidence(vt, evidence, engines) {
  if (!vt) return 0;
  let score = 0;
  if (vt.found) {
    score += Math.min(85, vt.malicious * 12 + vt.suspicious * 6);
    const parts = [
      `${vt.malicious} malicious`,
      `${vt.suspicious} suspicious`,
      `${vt.harmless} harmless`,
      `${vt.undetected} undetected`,
    ];
    if (vt.timeout) parts.push(`${vt.timeout} timeout`);
    if (vt.typeUnsupported) parts.push(`${vt.typeUnsupported} unsupported`);
    if (vt.submitted) parts.push("fresh submit");
    evidence.push({
      source: "VirusTotal",
      detail: parts.join(" · ") + (vt.total ? ` (${vt.total} engines)` : ""),
    });
    if (vt.reputation != null) {
      evidence.push({ source: "VirusTotal", detail: `Community reputation score: ${vt.reputation}.` });
    }
    if (vt.tags?.length) {
      evidence.push({ source: "VirusTotal", detail: `Tags: ${vt.tags.join(", ")}.` });
    }
    engines.push(
      ...vt.engines
        .filter((e) => e.category === "malicious" || e.category === "suspicious")
        .slice(0, 16)
        .map((e) => ({ name: e.name, result: e.result || e.category })),
    );
    if (engines.length < 8) {
      engines.push(
        ...vt.engines
          .filter((e) => e.category === "harmless" || e.category === "undetected")
          .slice(0, 8 - engines.length)
          .map((e) => ({ name: e.name, result: e.category })),
      );
    }
  } else if (vt.found === false) {
    evidence.push({
      source: "VirusTotal",
      detail: vt.submitted
        ? "Submitted for analysis — no completed report yet."
        : "No prior report for this indicator.",
    });
  }
  return score;
}

export default async function handler(req, res) {
  setCors(req, res);
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed." });
    return;
  }
  if (!originAllowed(req)) {
    res.status(403).json({ error: "Origin not allowed." });
    return;
  }
  if (!requireAnalyzeKey(req)) {
    res.status(401).json({ error: "Missing or invalid Securely API key." });
    return;
  }
  const limited = rateLimit(req, "analyze-threat", { limit: 60, windowMs: 60 * 60 * 1000 });
  if (limited) {
    res.setHeader("Retry-After", String(limited.retryAfterSec));
    res.status(429).json({ error: "Analyze rate limit reached. Try again later." });
    return;
  }

  try {
    const body = typeof req.body === "object" && req.body ? req.body : {};
    const type = String(body.type || "").toLowerCase();
    const evidence = [];
    const engines = [];
    let score = 0;
    let subject = "";
    let vtMeta = null;

    if (type === "url") {
      const url = normalizeUrl(body.url);
      if (!url) {
        res.status(400).json({ error: "Enter a valid public http(s) URL." });
        return;
      }
      subject = url;
      const local = localUrlHeuristics(url);
      score += local.score;
      evidence.push(...local.evidence);

      const uh = await urlhausLookup(url);
      if (uh?.listed) {
        score += 70;
        evidence.push({
          source: "URLhaus",
          detail: `Listed as ${uh.threat || "malicious"}${uh.tags?.length ? ` (${uh.tags.join(", ")})` : ""}.`,
        });
        engines.push({ name: "URLhaus", result: "malicious" });
      } else if (uh && uh.listed === false) {
        evidence.push({ source: "URLhaus", detail: "Not currently listed." });
        engines.push({ name: "URLhaus", result: "clean" });
      }

      const vt = await vtLookup("url", url, { submitIfMissing: true });
      vtMeta = vt;
      score += applyVtEvidence(vt, evidence, engines);
    } else if (type === "hash" || type === "file") {
      const hash = normalizeHash(body.hash);
      if (!hash) {
        res.status(400).json({ error: "Provide a valid MD5, SHA-1, or SHA-256 hash." });
        return;
      }
      subject = hash;
      if (type === "file") {
        const local = localFileHeuristics(body.fileName, body.fileSize, body.mimeType);
        score += local.score;
        evidence.push(...local.evidence);
        if (body.fileName) {
          evidence.push({
            source: "local",
            detail: `File ${String(body.fileName).slice(0, MAX_NAME)} · ${Number(body.fileSize) || 0} bytes`,
          });
        }
      }

      let vt = await vtLookup("hash", hash, { submitIfMissing: false });
      // Optional fresher verdict when client asks and hash is already known.
      if (vt?.found && body.rescan && process.env.VIRUSTOTAL_API_KEY) {
        const rescanned = await vtRescanFile(hash, process.env.VIRUSTOTAL_API_KEY);
        if (rescanned?.found) vt = { ...rescanned, submitted: true };
      }
      vtMeta = vt;
      score += applyVtEvidence(vt, evidence, engines);
      if (vt && vt.found === false && score < 10) score = 8;
      if (!vt && !process.env.VIRUSTOTAL_API_KEY) {
        evidence.push({
          source: "Securely",
          detail: "Cloud multi-engine key not configured — using local heuristics + AI summary only.",
        });
      }
    } else {
      res.status(400).json({ error: "type must be url, hash, or file." });
      return;
    }

    const verdict = scoreToVerdict(score);
    const ai = await aiSummary(
      `Subject: ${subject}\nVerdict so far: ${verdict}\nScore: ${score}\nEvidence:\n${evidence
        .map((e) => `- ${e.source}: ${e.detail}`)
        .join("\n")}`,
    );

    const summary =
      ai ||
      (verdict === "malicious"
        ? "Strong malicious signals were found. Do not open this item."
        : verdict === "suspicious"
          ? "Mixed or heuristic risk signals — verify before trusting this item."
          : verdict === "clean"
            ? "No strong malicious signals from available checks."
            : "Not enough reputation data yet — treat as unknown.");

    res.status(200).json({
      verdict,
      score,
      subject,
      summary,
      evidence,
      engines: engines.slice(0, 24),
      tips: tipsFor(verdict),
      stats: vtMeta?.found
        ? {
            malicious: vtMeta.malicious,
            suspicious: vtMeta.suspicious,
            harmless: vtMeta.harmless,
            undetected: vtMeta.undetected,
            timeout: vtMeta.timeout,
            typeUnsupported: vtMeta.typeUnsupported,
            total: vtMeta.total,
          }
        : null,
      providers: {
        virustotal: Boolean(process.env.VIRUSTOTAL_API_KEY),
        openrouter: Boolean(process.env.OPENROUTER_API_KEY),
        urlhaus: true,
      },
      links: {
        virustotalOrg: "https://github.com/VirusTotal",
        vtPy: "https://github.com/VirusTotal/vt-py",
        vtCli: "https://virustotal.github.io/vt-cli/",
      },
    });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Analysis failed." });
  }
}

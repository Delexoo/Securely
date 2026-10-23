/** Shared CORS allow-list + per-IP rate limits for Securely APIs. */

const ALLOWED_ORIGINS = new Set([
  "https://trysecurely.com",
  "https://www.trysecurely.com",
  "https://trysecurely.vercel.app",
]);

const buckets = new Map();

function clientIp(req) {
  const xf = String(req.headers["x-forwarded-for"] || "")
    .split(",")[0]
    .trim();
  return xf || String(req.headers["x-real-ip"] || req.socket?.remoteAddress || "unknown").slice(0, 64);
}

export function setCors(req, res, { credentials = false } = {}) {
  const origin = String(req.headers.origin || "");
  // Desktop WebView2 mapped UI often sends no Origin or "null".
  let allow = "*";
  if (!origin || origin === "null") {
    allow = "*";
  } else {
    try {
      const host = new URL(origin).host;
      if (ALLOWED_ORIGINS.has(origin) || /\.vercel\.app$/i.test(host)) allow = origin;
      else allow = "https://trysecurely.com";
    } catch {
      allow = "https://trysecurely.com";
    }
    res.setHeader("Vary", "Origin");
  }
  res.setHeader("Access-Control-Allow-Origin", allow);
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Securely-Client, X-Securely-Key");
}

export function originAllowed(req) {
  const origin = String(req.headers.origin || "");
  if (!origin || origin === "null") return true;
  try {
    const host = new URL(origin).host;
    if (ALLOWED_ORIGINS.has(origin)) return true;
    if (/\.vercel\.app$/i.test(host)) return true;
  } catch {
    return false;
  }
  return false;
}

/**
 * Sliding window limiter. Returns null if OK, or { retryAfterSec }.
 * @param {import('http').IncomingMessage} req
 * @param {string} bucket
 * @param {{ limit: number, windowMs: number }} opts
 */
export function rateLimit(req, bucket, { limit, windowMs }) {
  const ip = clientIp(req);
  const key = `${bucket}:${ip}`;
  const now = Date.now();
  let entry = buckets.get(key);
  if (!entry || now - entry.start >= windowMs) {
    entry = { start: now, count: 0 };
    buckets.set(key, entry);
  }
  entry.count += 1;
  if (entry.count > limit) {
    const retryAfterSec = Math.max(1, Math.ceil((entry.start + windowMs - now) / 1000));
    return { retryAfterSec };
  }
  // Opportunistic cleanup
  if (buckets.size > 4000) {
    for (const [k, v] of buckets) {
      if (now - v.start > windowMs * 2) buckets.delete(k);
    }
  }
  return null;
}

export function requireAnalyzeKey(req) {
  const expected = process.env.SECURELY_ANALYZE_KEY || "";
  if (!expected) return true; // unset = desktop-friendly open (still rate-limited)
  const got =
    String(req.headers["x-securely-key"] || "") ||
    String(req.headers.authorization || "").replace(/^Bearer\s+/i, "");
  return got === expected;
}

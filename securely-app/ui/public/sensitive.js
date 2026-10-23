/**
 * Local (no-network) sensitive-detail detector for Securely.
 * Runs on OCR text before any AI call so secrets are not uploaded unless the user continues.
 */
(function (global) {
  function luhnOk(digits) {
    let sum = 0;
    let alt = false;
    for (let i = digits.length - 1; i >= 0; i -= 1) {
      let n = digits.charCodeAt(i) - 48;
      if (n < 0 || n > 9) return false;
      if (alt) {
        n *= 2;
        if (n > 9) n -= 9;
      }
      sum += n;
      alt = !alt;
    }
    return sum % 10 === 0;
  }

  function findCards(text) {
    const hits = [];
    const re = /(?:^|[^\d])(\d(?:[\s-]?\d){12,18})(?=[^\d]|$)/g;
    let m;
    while ((m = re.exec(text))) {
      const digits = m[1].replace(/\D/g, "");
      if (digits.length < 13 || digits.length > 19) continue;
      if (!luhnOk(digits)) continue;
      // Skip long pure serial-looking runs that fail common BIN ranges lightly:
      if (/^0+$/.test(digits)) continue;
      hits.push({ kind: "payment", label: "payment card number", start: m.index, end: m.index + m[0].length, value: m[1] });
    }
    return hits;
  }

  function findSsns(text) {
    const hits = [];
    const re = /\b(?!000|666|9\d\d)(\d{3})-?(?!00)(\d{2})-?(?!0000)(\d{4})\b/g;
    let m;
    while ((m = re.exec(text))) {
      const area = Number(m[1]);
      if (area === 0 || area === 666 || area >= 900) continue;
      hits.push({ kind: "ssn", label: "Social Security number", start: m.index, end: m.index + m[0].length, value: m[0] });
    }
    return hits;
  }

  function findPasswords(text) {
    const hits = [];
    const patterns = [
      /\b(?:password|passwd|pwd|passcode|pin)\s*[=:]\s*(\S{4,64})/gi,
      /\b(?:current|new|confirm)\s+password\s*[=:]\s*(\S{4,64})/gi,
      /\b(?:secret|api[_ -]?key|access[_ -]?token|private[_ -]?key)\s*[=:]\s*(\S{8,128})/gi,
    ];
    for (const re of patterns) {
      let m;
      while ((m = re.exec(text))) {
        hits.push({ kind: "password", label: "password or secret", start: m.index, end: m.index + m[0].length, value: m[0] });
      }
    }
    // Password field UI cues + nearby masked dots / value-looking tokens
    if (/\bpassword\b/i.test(text) && /[•●*]{4,}|\bshow password\b|\bhide password\b/i.test(text)) {
      hits.push({ kind: "password", label: "password field", start: 0, end: 0, value: "" });
    }
    return hits;
  }

  function findPaymentExtras(text) {
    const hits = [];
    const cvv = /\b(?:cvv|cvc|cid|security code)\s*[=:]?\s*(\d{3,4})\b/gi;
    let m;
    while ((m = cvv.exec(text))) {
      hits.push({ kind: "payment", label: "card security code", start: m.index, end: m.index + m[0].length, value: m[0] });
    }
    if (/\b(?:exp(?:iry|iration)?|valid thru)\b/i.test(text) && /\b(0[1-9]|1[0-2])\s*[\/\-]\s*(\d{2}|\d{4})\b/.test(text)) {
      const exp = text.match(/\b(0[1-9]|1[0-2])\s*[\/\-]\s*(\d{2}|\d{4})\b/);
      if (exp) hits.push({ kind: "payment", label: "card expiry", start: exp.index, end: exp.index + exp[0].length, value: exp[0] });
    }
    const routing = /\b(?:routing|aba)\s*(?:number|#)?\s*[=:]?\s*(\d{9})\b/gi;
    while ((m = routing.exec(text))) {
      hits.push({ kind: "payment", label: "bank routing number", start: m.index, end: m.index + m[0].length, value: m[0] });
    }
    const acct = /\b(?:account)\s*(?:number|#)?\s*[=:]?\s*(\d{8,17})\b/gi;
    while ((m = acct.exec(text))) {
      hits.push({ kind: "payment", label: "bank account number", start: m.index, end: m.index + m[0].length, value: m[0] });
    }
    return hits;
  }

  function findAddresses(text) {
    const hits = [];
    const street = /\b\d{1,5}\s+[A-Za-z0-9.'\-]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)\b\.?/gi;
    let m;
    while ((m = street.exec(text))) {
      hits.push({ kind: "address", label: "street address", start: m.index, end: m.index + m[0].length, value: m[0] });
    }
    const zip = /\b(?:[A-Z]{2}|[A-Za-z][a-z]+,?\s+[A-Z]{2})\s+\d{5}(?:-\d{4})?\b/g;
    while ((m = zip.exec(text))) {
      hits.push({ kind: "address", label: "mailing address / ZIP", start: m.index, end: m.index + m[0].length, value: m[0] });
    }
    return hits;
  }

  function uniqueKinds(hits) {
    const order = ["password", "ssn", "payment", "address"];
    const labels = {
      password: "passwords / secrets",
      ssn: "Social Security numbers",
      payment: "payment details",
      address: "addresses",
    };
    const seen = new Set();
    const kinds = [];
    for (const h of hits) {
      if (seen.has(h.kind)) continue;
      seen.add(h.kind);
      kinds.push(h.kind);
    }
    kinds.sort((a, b) => order.indexOf(a) - order.indexOf(b));
    return { kinds, labels: kinds.map((k) => labels[k] || k) };
  }

  function detectSensitive(text) {
    const raw = String(text || "");
    if (!raw.trim()) return { found: false, hits: [], kinds: [], labels: [], summary: "" };
    const hits = [
      ...findPasswords(raw),
      ...findSsns(raw),
      ...findCards(raw),
      ...findPaymentExtras(raw),
      ...findAddresses(raw),
    ];
    const { kinds, labels } = uniqueKinds(hits);
    return {
      found: hits.length > 0,
      hits,
      kinds,
      labels,
      summary: labels.length ? labels.join(", ") : "",
    };
  }

  function redactSensitive(text, hits) {
    let out = String(text || "");
    if (!hits?.length) return out;
    const sorted = [...hits].filter((h) => h.end > h.start && h.value).sort((a, b) => b.start - a.start);
    for (const h of sorted) {
      const token = h.kind === "ssn" ? "[SSN]" : h.kind === "payment" ? "[PAYMENT]" : h.kind === "password" ? "[SECRET]" : "[ADDRESS]";
      // Replace the concrete value occurrence, not only the slice (OCR offsets can drift).
      if (h.value) out = out.split(h.value).join(token);
    }
    return out;
  }

  /** Lightweight local phishing cues — complements AI, never replaces the sensitive gate. */
  function localThreatHints(text) {
    const t = String(text || "").toLowerCase();
    if (!t.trim()) return null;
    const cues = [
      { re: /\bhttps?:\/\/(?!localhost|127\.0\.0\.1)/i, kind: "SUSPICIOUS", note: "Insecure or raw URL visible on screen" },
      { re: /\b(urgent|act now|account (will be )?(suspended|closed|locked)|verify (your )?account|confirm (your )?identity)\b/i, kind: "SUSPICIOUS", note: "Urgency / account-threat language" },
      { re: /\b(you('ve| have) won|claim (your )?prize|lottery|inheritance)\b/i, kind: "SUSPICIOUS", note: "Prize / lottery scam language" },
      { re: /\b(tech support|computer (is )?infected|call (this )?number|microsoft support|apple support)\b/i, kind: "SUSPICIOUS", note: "Tech-support scam language" },
      { re: /\b(g00gle|micr0soft|faceb00k|paypa1|appleid-?secure)\b/i, kind: "PHISHING", note: "Possible typosquat brand" },
    ];
    for (const c of cues) {
      if (c.re.test(t)) return { kind: c.kind, text: `${c.kind}: ${c.note} (local check).` };
    }
    if (/\bhttp:\/\//i.test(text) && !/\bhttps:\/\//i.test(text)) {
      return { kind: "SUSPICIOUS", text: "SUSPICIOUS: Insecure HTTP URL on screen (local check)." };
    }
    return null;
  }

  global.SecurelySensitive = { detectSensitive, redactSensitive, localThreatHints };
})(typeof window !== "undefined" ? window : globalThis);

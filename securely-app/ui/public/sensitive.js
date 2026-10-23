/**
 * Local (no-network) sensitive-detail detector for Securely.
 * Runs on OCR text before any AI call so secrets are not uploaded unless the user continues.
 */
(function (global) {
  const KIND_LABELS = {
    password: "passwords / secrets",
    ssn: "Social Security numbers",
    payment: "payment details",
    address: "addresses",
    email: "email addresses",
    phone: "phone numbers",
    dob: "dates of birth",
    government_id: "government IDs",
    medical: "medical / insurance IDs",
    tax: "tax IDs",
    crypto: "crypto wallets / seed phrases",
    auth: "one-time codes / recovery codes",
    network: "private network identifiers",
    biometric: "biometric data cues",
  };

  const KIND_ORDER = Object.keys(KIND_LABELS);

  const REDACT = {
    password: "[SECRET]",
    ssn: "[SSN]",
    payment: "[PAYMENT]",
    address: "[ADDRESS]",
    email: "[EMAIL]",
    phone: "[PHONE]",
    dob: "[DOB]",
    government_id: "[GOV_ID]",
    medical: "[MEDICAL_ID]",
    tax: "[TAX_ID]",
    crypto: "[CRYPTO]",
    auth: "[AUTH_CODE]",
    network: "[NETWORK]",
    biometric: "[BIOMETRIC]",
  };

  function pushHit(hits, kind, label, start, end, value) {
    hits.push({ kind, label, start: start || 0, end: end || 0, value: value || "" });
  }

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
      if (!luhnOk(digits) || /^0+$/.test(digits)) continue;
      pushHit(hits, "payment", "payment card number", m.index, m.index + m[0].length, m[1]);
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
      pushHit(hits, "ssn", "Social Security number", m.index, m.index + m[0].length, m[0]);
    }
    return hits;
  }

  function findPasswords(text) {
    const hits = [];
    const patterns = [
      /\b(?:password|passwd|pwd|passcode|pin)\s*[=:]\s*(\S{4,64})/gi,
      /\b(?:current|new|confirm)\s+password\s*[=:]\s*(\S{4,64})/gi,
      /\b(?:secret|api[_ -]?key|access[_ -]?token|refresh[_ -]?token|private[_ -]?key|client[_ -]?secret)\s*[=:]\s*(\S{8,200})/gi,
      /\b(?:bearer)\s+[A-Za-z0-9\-._~+/]+=*/gi,
      /\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,
      /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g,
      /\bghp_[A-Za-z0-9]{36,}\b/g,
      /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/g,
      /\bsk-(?:live|test)?[A-Za-z0-9]{20,}\b/g,
    ];
    for (const re of patterns) {
      let m;
      while ((m = re.exec(text))) {
        pushHit(hits, "password", "password or secret", m.index, m.index + m[0].length, m[0]);
      }
    }
    if (/\bpassword\b/i.test(text) && /[•●*]{4,}|\bshow password\b|\bhide password\b/i.test(text)) {
      pushHit(hits, "password", "password field", 0, 0, "");
    }
    return hits;
  }

  function findPaymentExtras(text) {
    const hits = [];
    const cvv = /\b(?:cvv|cvc|cid|security code)\s*[=:]?\s*(\d{3,4})\b/gi;
    let m;
    while ((m = cvv.exec(text))) {
      pushHit(hits, "payment", "card security code", m.index, m.index + m[0].length, m[0]);
    }
    if (/\b(?:exp(?:iry|iration)?|valid thru)\b/i.test(text)) {
      const exp = text.match(/\b(0[1-9]|1[0-2])\s*[\/\-]\s*(\d{2}|\d{4})\b/);
      if (exp) pushHit(hits, "payment", "card expiry", exp.index, exp.index + exp[0].length, exp[0]);
    }
    const routing = /\b(?:routing|aba)\s*(?:number|#)?\s*[=:]?\s*(\d{9})\b/gi;
    while ((m = routing.exec(text))) {
      pushHit(hits, "payment", "bank routing number", m.index, m.index + m[0].length, m[0]);
    }
    const acct = /\b(?:account)\s*(?:number|#)?\s*[=:]?\s*(\d{8,17})\b/gi;
    while ((m = acct.exec(text))) {
      pushHit(hits, "payment", "bank account number", m.index, m.index + m[0].length, m[0]);
    }
    const iban = /\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/g;
    while ((m = iban.exec(text))) {
      if (m[0].length >= 15) pushHit(hits, "payment", "IBAN", m.index, m.index + m[0].length, m[0]);
    }
    const swift = /\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b/g;
    while ((m = swift.exec(text))) {
      if (/\b(?:swift|bic)\b/i.test(text.slice(Math.max(0, m.index - 12), m.index + m[0].length + 4))) {
        pushHit(hits, "payment", "SWIFT / BIC", m.index, m.index + m[0].length, m[0]);
      }
    }
    return hits;
  }

  function findAddresses(text) {
    const hits = [];
    const street =
      /\b\d{1,5}\s+[A-Za-z0-9.'\-]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl|Circle|Cir|Terrace|Ter)\b\.?/gi;
    let m;
    while ((m = street.exec(text))) {
      pushHit(hits, "address", "street address", m.index, m.index + m[0].length, m[0]);
    }
    const zip = /\b(?:[A-Z]{2}|[A-Za-z][a-z]+,?\s+[A-Z]{2})\s+\d{5}(?:-\d{4})?\b/g;
    while ((m = zip.exec(text))) {
      pushHit(hits, "address", "mailing address / ZIP", m.index, m.index + m[0].length, m[0]);
    }
    const po = /\bP\.?\s*O\.?\s*Box\s+\d+\b/gi;
    while ((m = po.exec(text))) {
      pushHit(hits, "address", "P.O. Box", m.index, m.index + m[0].length, m[0]);
    }
    return hits;
  }

  function findEmails(text) {
    const hits = [];
    const re = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
    let m;
    while ((m = re.exec(text))) {
      // Skip obvious product/support domains used as labels only when alone — still redact real emails.
      pushHit(hits, "email", "email address", m.index, m.index + m[0].length, m[0]);
    }
    return hits;
  }

  function findPhones(text) {
    const hits = [];
    const re =
      /(?:(?:\+?1[\s\-.]?)?(?:\(?\d{3}\)?[\s\-.]?)\d{3}[\s\-.]?\d{4}|\+\d{1,3}[\s\-.]?\d{6,14})\b/g;
    let m;
    while ((m = re.exec(text))) {
      const digits = m[0].replace(/\D/g, "");
      if (digits.length < 10 || digits.length > 15) continue;
      // Avoid matching pure SSN-like already handled / short extensions
      if (/^\d{3}-\d{2}-\d{4}$/.test(m[0])) continue;
      pushHit(hits, "phone", "phone number", m.index, m.index + m[0].length, m[0]);
    }
    return hits;
  }

  function findDob(text) {
    const hits = [];
    const labeled =
      /\b(?:d\.?o\.?b\.?|date of birth|birth\s*date|born)\s*[=:]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})/gi;
    let m;
    while ((m = labeled.exec(text))) {
      pushHit(hits, "dob", "date of birth", m.index, m.index + m[0].length, m[0]);
    }
    return hits;
  }

  function findGovernmentIds(text) {
    const hits = [];
    const patterns = [
      { re: /\b(?:passport|pass\s*#|passport\s*(?:no|number|#))\s*[=:]?\s*([A-Z0-9]{6,12})\b/gi, label: "passport number" },
      { re: /\b(?:driver'?s?\s*license|dl\s*(?:no|number|#)|licence\s*no)\s*[=:]?\s*([A-Z0-9\-]{5,20})\b/gi, label: "driver's license" },
      { re: /\b(?:national\s*id|nid|citizen\s*id|aadhaar|aadhar)\s*[=:]?\s*([A-Z0-9\s\-]{6,16})\b/gi, label: "national ID" },
      { re: /\b(?:alien\s*registration|uscis|green\s*card)\s*[=:]?\s*([A-Z0-9\-]{6,16})\b/gi, label: "immigration ID" },
    ];
    for (const { re, label } of patterns) {
      let m;
      while ((m = re.exec(text))) {
        pushHit(hits, "government_id", label, m.index, m.index + m[0].length, m[0]);
      }
    }
    return hits;
  }

  function findMedical(text) {
    const hits = [];
    const patterns = [
      { re: /\b(?:MRN|medical\s*record\s*(?:no|number|#))\s*[=:]?\s*([A-Z0-9\-]{5,20})\b/gi, label: "medical record number" },
      { re: /\b(?:Medicare|Medicaid)\s*(?:ID|#|number)?\s*[=:]?\s*([A-Z0-9\-]{6,15})\b/gi, label: "health insurance ID" },
      { re: /\b(?:member\s*id|subscriber\s*id|policy\s*(?:no|number))\s*[=:]?\s*([A-Z0-9\-]{6,20})\b/gi, label: "insurance member ID" },
      { re: /\b(?:NPI)\s*[=:]?\s*(\d{10})\b/gi, label: "NPI" },
    ];
    for (const { re, label } of patterns) {
      let m;
      while ((m = re.exec(text))) {
        pushHit(hits, "medical", label, m.index, m.index + m[0].length, m[0]);
      }
    }
    if (/\bHIPAA\b/i.test(text) && /\b(?:patient|diagnosis|prescription)\b/i.test(text)) {
      pushHit(hits, "medical", "health record cues", 0, 0, "");
    }
    return hits;
  }

  function findTax(text) {
    const hits = [];
    const ein = /\b(?:EIN|employer\s*id(?:entification)?)\s*[=:]?\s*(\d{2}-?\d{7})\b/gi;
    let m;
    while ((m = ein.exec(text))) {
      pushHit(hits, "tax", "EIN / tax ID", m.index, m.index + m[0].length, m[0]);
    }
    const itin = /\b(?:ITIN)\s*[=:]?\s*(9\d{2}-?\d{2}-?\d{4})\b/gi;
    while ((m = itin.exec(text))) {
      pushHit(hits, "tax", "ITIN", m.index, m.index + m[0].length, m[0]);
    }
    return hits;
  }

  function findCrypto(text) {
    const hits = [];
    const btc = /\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b/g;
    let m;
    while ((m = btc.exec(text))) {
      if (m[0].length >= 26) pushHit(hits, "crypto", "Bitcoin address", m.index, m.index + m[0].length, m[0]);
    }
    const eth = /\b0x[a-fA-F0-9]{40}\b/g;
    while ((m = eth.exec(text))) {
      pushHit(hits, "crypto", "Ethereum address", m.index, m.index + m[0].length, m[0]);
    }
    if (/\b(?:seed\s*phrase|recovery\s*phrase|mnemonic)\b/i.test(text)) {
      // 12/24 word-ish runs are hard; flag the cue and nearby long word sequences
      pushHit(hits, "crypto", "wallet seed / recovery phrase", 0, 0, "");
      const words = text.match(/\b(?:[a-z]{3,12}\s+){11,23}[a-z]{3,12}\b/i);
      if (words) pushHit(hits, "crypto", "possible mnemonic word list", words.index, words.index + words[0].length, words[0]);
    }
    return hits;
  }

  function findAuthCodes(text) {
    const hits = [];
    const otp =
      /\b(?:otp|one[-\s]?time\s*(?:code|password|passcode)|verification\s*code|auth(?:entication)?\s*code|2fa|mfa)\s*[=:]?\s*(\d{4,8})\b/gi;
    let m;
    while ((m = otp.exec(text))) {
      pushHit(hits, "auth", "one-time / 2FA code", m.index, m.index + m[0].length, m[0]);
    }
    const recovery = /\b(?:recovery|backup)\s*codes?\s*[=:]?\s*([A-Z0-9\-\s]{10,80})/gi;
    while ((m = recovery.exec(text))) {
      pushHit(hits, "auth", "recovery codes", m.index, m.index + m[0].length, m[0]);
    }
    return hits;
  }

  function findNetwork(text) {
    const hits = [];
    const ipv4 = /\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b/g;
    let m;
    while ((m = ipv4.exec(text))) {
      pushHit(hits, "network", "private IP address", m.index, m.index + m[0].length, m[0]);
    }
    const mac = /\b(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}\b/gi;
    while ((m = mac.exec(text))) {
      pushHit(hits, "network", "MAC address", m.index, m.index + m[0].length, m[0]);
    }
    return hits;
  }

  function findBiometric(text) {
    const hits = [];
    if (/\b(?:fingerprint|face\s*id|touch\s*id|iris\s*scan|biometric)\b/i.test(text) &&
      /\b(?:scan|enroll|template|match|unlock)\b/i.test(text)) {
      pushHit(hits, "biometric", "biometric data cues", 0, 0, "");
    }
    return hits;
  }

  function uniqueKinds(hits) {
    const seen = new Set();
    const kinds = [];
    for (const h of hits) {
      if (seen.has(h.kind)) continue;
      seen.add(h.kind);
      kinds.push(h.kind);
    }
    kinds.sort((a, b) => KIND_ORDER.indexOf(a) - KIND_ORDER.indexOf(b));
    return { kinds, labels: kinds.map((k) => KIND_LABELS[k] || k) };
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
      ...findEmails(raw),
      ...findPhones(raw),
      ...findDob(raw),
      ...findGovernmentIds(raw),
      ...findMedical(raw),
      ...findTax(raw),
      ...findCrypto(raw),
      ...findAuthCodes(raw),
      ...findNetwork(raw),
      ...findBiometric(raw),
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
    const sorted = [...hits].filter((h) => h.value).sort((a, b) => b.value.length - a.value.length);
    for (const h of sorted) {
      const token = REDACT[h.kind] || "[REDACTED]";
      if (h.value) out = out.split(h.value).join(token);
    }
    return out;
  }

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

  global.SecurelySensitive = { detectSensitive, redactSensitive, localThreatHints, KIND_LABELS };
})(typeof window !== "undefined" ? window : globalThis);

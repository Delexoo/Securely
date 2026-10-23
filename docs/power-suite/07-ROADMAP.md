# Roadmap

Effort is rough (engineer-weeks for a small team). Risks are explicit.

## v0.2 — Analyze MVP + policy foundation (~3–5 weeks)

| Deliverable | Effort | Risk |
|-------------|--------|------|
| Dashboard Analyze tab (hash, URL, file ≤32MB) | M | UX polish |
| Server `/api/analyze-hash` + `/api/analyze-url` (+ one licensed multi-engine) | M | API keys/quota |
| Sensitive gate on uploads | S | FP blockages |
| Quiet / Balanced / Paranoid toggles (settings JSON) | S | Scope creep |
| Pill: “Analyze clipboard URL” | S | — |

**Exit criteria:** Paying user can paste a URL or drop an EXE and see Clean/Suspicious/Malicious/Unknown with evidence list.

## v0.3 — Protect companion + proactive loops (~4–6 weeks)

| Deliverable | Effort | Risk |
|-------------|--------|------|
| Downloads watcher → Analyze prompt | M | Noise |
| Quarantine + restore | M | ACL bugs |
| On-demand folder scan (YARA + hash) | M | Perf |
| Defender health tile | S | Detection reliability |
| Timed/24·7 + hitboxes hardening | M | OCR cost/privacy |

**Exit criteria:** New download can be quarantined; Defender still primary; screen modes trustworthy.

## v1.0 — VPN + suite cohesion (~8–12 weeks)

| Deliverable | Effort | Risk |
|-------------|--------|------|
| WireGuard BYO + partner list | L | Elevation, WFP |
| Kill switch + split presets | M | Leak edge cases |
| Cross-feature policies | M | Complexity |
| Honest marketing + threat model refresh | S | Legal review |
| Signed installer | M | Cert ops |

**Exit criteria:** Connect VPN with kill switch; suite feels coherent; claims match SECURITY.md.

## Later / skip

Password vault, dark web, parental, kernel AV, Meshnet clones, macOS/iOS.

## Risks register

| Risk | Mitigation |
|------|------------|
| Looking like a fake “Norton killer” | Companion framing; never disable Defender |
| Malware sample liability | Short retention; isolated storage; abuse limits |
| VPN no-logs overclaim | BYO first; partner audit before claim |
| AI false Safe | Heuristics + Unsure on failure |
| Scope explosion | Phase 1 prompt below — Analyze only |

---

## Cursor implementation prompt — Phase 1 only

Copy into a **new** agent chat when ready to build (not research):

```
Workspace: E:\MasterVault\Securely

Build ONLY Power Suite Phase 1 from docs/power-suite/:
- Read 00-EXECUTIVE-BRIEF.md, 02-ANALYZE-ANYTHING.md, 06-ARCHITECTURE.md, 07-ROADMAP.md (v0.2 section).
- Do NOT implement VPN, kernel AV, Defender replacement, or RE of commercial products.

Implement:
1. Dashboard side-nav "Analyze" page: drag-drop file, paste URL, paste hash.
2. Host: compute SHA-256 for local files; never send VT/OpenRouter keys in the client.
3. Website APIs: POST /api/analyze-hash and /api/analyze-url (and optional signed upload for small files). Use env keys for one legitimate threat API (VirusTotal v3 or MetaDefender) + URL feed if configured; return normalized { verdict, engines[], evidence[] }.
4. Reuse sensitive.js / similar checks to warn or block sensitive uploads.
5. Settings: profile enum quiet|balanced|paranoid stored with existing dashboard settings.
6. Pill: optional action to Analyze clipboard when it looks like a URL.
7. Update docs/THREAT_MODEL.md data-flow for Analyze; add brain/log notes only if asked to ship.

Constraints:
- Match existing glass UI / postMessage patterns.
- Rate-limit APIs; CORS as existing analyze.js.
- No scraping VirusTotal HTML; no commit of .env; no version bump unless I ask to commit/update.

Start by sketching the UI + API contract, then implement end-to-end with a mock provider fallback when keys are missing (verdict Unknown + local hash only).
```

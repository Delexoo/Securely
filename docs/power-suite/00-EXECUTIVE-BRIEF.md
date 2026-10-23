# Securely Power Suite — Executive Brief

**Date:** 2026-10-22  
**Status:** Research (no code shipped under this plan yet)  
**Audience:** Product + engineering agents building the next Securely milestones

## Vision

Securely becomes a **proactive, lightweight Windows security suite** that feels as useful as top consumer tools (Norton / Bitdefender / NordVPN class *outcomes*), without cloning them and without reverse-engineering their closed products.

The suite rests on five pillars:

1. **Screen-aware threat monitoring** (already shipping) — OCR + local sensitive gate + AI classification  
2. **Analyze Anything** — VirusTotal-*like* UX for files, hashes, and links via legitimate multi-signal APIs  
3. **Lightweight AV companion** — on-demand + selective real-time signals; **complement Defender**, do not replace it in v1  
4. **Lightweight VPN** — WireGuard-based tunnel with kill switch / split tunnel / profiles  
5. **Securely-unique wedge** — continuous screen phishing protection + local PII gate before any cloud AI

## What makes Securely unique

Most suite vendors own **disk + network**. Almost none own **what is on the user’s screen right now** with an explicit privacy gate before remote AI.

| Competitor strength | Securely counter |
|---------------------|------------------|
| Kernel AV / huge signature DBs | Prefer Defender coexistence + Analyze multi-signal + heuristics |
| Global VPN PoPs | Partner or self-host WireGuard; honest no-logs claims |
| Multi-engine cloud scan (VT) | Aggregate **licensed** providers + local static; never scrape VT |
| Password vault / dark web | Later / skip for v1 — not the wedge |

**Wedge sentence for marketing (honest):**  
*Securely watches the screen for phishing and scams, keeps sensitive text off the AI by default, and adds Analyze / AV companion / VPN when you need them — without turning off Windows Defender.*

## Non-goals (v1–v1.0)

- Replacing Microsoft Defender as the primary AV  
- Kernel mini-filters / HVCI attestation / driver signing programs (phase 3+)  
- Scraping VirusTotal or cloning Norton/Bitdefender/NordVPN binaries or branding  
- Claiming “100% virus protection” or audited no-logs before those are true  
- Full password manager, parental controls, dark-web monitoring, cloud backup (later or skip)

## Current baseline (repo)

| Area | Today |
|------|--------|
| Host | WinForms + WebView2 (`securely-app/host`) |
| UI | Glass pill + dashboard (`securely-app/ui/public`) |
| Core | Quick Scan OCR → local `sensitive.js` gate → OpenRouter via `Securely-Website/api/analyze` |
| Biz | Stripe checkout / license / installer |
| Version | `0.1.4` (package.json); unshipped privacy/billing polish may exist locally |

## Recommended product shape

```
Pill (always-on widget)
  └─ Quick / Timed / 24·7 screen protection

Dashboard
  ├─ Monitoring (existing)
  ├─ Analyze   ← Phase 1 MVP
  ├─ Protect   ← AV companion + policy profiles (Phase 2)
  ├─ VPN       ← WireGuard client (Phase 2–3)
  ├─ Audit / Settings / Credits (existing+)
```

## Quality bar

- **Proactive:** clear warnings, one-click actions, Quiet / Balanced / Paranoid profiles  
- **Lightweight:** no second full AV stack fighting Defender in v1  
- **Honest:** SECURITY.md and threat model state limits; marketing matches code  
- **Legal:** public competitive research + open architectures only; REA only on own/open targets  

## Decision that unlocks shipping speed

**Ship as a Defender companion + Analyze + screen wedge first.** Full “Norton replacement” marketing waits until real-time AV and VPN meet the quality bar. This is the path that ships premium UX without lying.

Next: [01-COMPETITIVE-MAP](./01-COMPETITIVE-MAP.md) → architecture docs → [07-ROADMAP](./07-ROADMAP.md) Phase 1 prompt.

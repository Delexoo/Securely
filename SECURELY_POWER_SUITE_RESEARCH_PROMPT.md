# Securely Power Suite — Cursor Research Agent Prompt

Copy everything below the line into a **new Cursor agent chat** with workspace access to `E:\MasterVault\Securely\`.

---

## Mission

You are a senior product + systems research agent. Your job is to turn **Securely** from a screen-threat overlay into a **unique, proactive, lightweight security suite** that feels as capable as top consumer tools (feature *parity of outcomes*, not a clone), while staying **legal, shippable, and Windows-first**.

Deliver a research-backed architecture and phased build plan. Prefer **evidence from public sources and open systems**. Do **not** reverse-engineer, decompile, crack, bypass, or unpack proprietary Norton, Bitdefender, NordVPN, VirusTotal, or similar closed binaries.

### What “powerful + unique” means for Securely

Securely already does primary-monitor OCR + local sensitive-data gate + AI threat classification + Stripe subscription. Expand it into a **coherent suite** with:

1. **Proactive protection** — real-time signals, clear warnings, one-click actions, low false-alarm UX  
2. **Built-in “analyze anything”** — paste/upload **files or links**, multi-engine / multi-signal verdict (VirusTotal-*like* UX, not a VirusTotal scrape/clone)  
3. **Lightweight antivirus layer** — on-demand + real-time hooks where Windows allows, customizable policies  
4. **Lightweight VPN layer** — WireGuard-class tunnel, kill switch, split tunnel, profiles (NordVPN-*like* UX)  
5. **Securely-unique wedge** — screen-aware phishing + local PII gate before AI (what Norton-class tools do not own)

---

## Hard rules (do not violate)

| Allowed | Not allowed |
|---------|-------------|
| Public docs, help centers, pricing pages, whitepapers, patents as *ideas only* | Decompiling Norton / Bitdefender / NordVPN / closed AV-VPN installers |
| Open-source AV/VPN/scanner architectures (ClamAV, Windows Defender APIs, WireGuard, OpenVPN, YARA, Sigma, etc.) | License-key generators, signature DB theft, API key scraping, ToS-breaking automation |
| Feature inventories & UX pattern notes from marketing demos | Circumventing DRM, license checks, or update channels of third-party products |
| Using [REA](https://rea.tools/) / [`morluto/rea`](https://github.com/morluto/rea) on **Securely’s own builds**, open samples, or **explicitly permitted** teaching targets | Using REA (or any RE stack) against commercial security vendors’ closed apps |
| Curated learning lists like [`morluto/awesome-reverse-engineering`](https://github.com/morluto/awesome-reverse-engineering) for **method literacy** on open/own targets | “Replicate Norton by dumping its binaries” |

If a step would require closed-product RE, **stop**, document the *capability goal* instead, and propose an **open/legal equivalent**.

---

## Workspace context (read first)

| Path | Role |
|------|------|
| `E:\MasterVault\Securely\` | Product source of truth |
| `securely-app/host/` | WinForms + WebView2 shell |
| `securely-app/ui/public/` | Pill + dashboard |
| `Securely-Website/` | Marketing + APIs (Stripe, analyze, license) |
| `brain/log.json` | Release notes source |
| `RECREATE_SECURELY_PROMPT.md` | Original rebuild charter |
| Current strengths | Quick Scan OCR→AI, local sensitive gate, billing, installer |

---

## Research workstreams (extensive — do all)

### A. Competitive capability map (public sources only)

For **Norton**, **Bitdefender**, **Malwarebytes**, **Windows Defender**, **NordVPN / Mullvad / Proton VPN**, and **VirusTotal / Hybrid Analysis / URLhaus**:

1. List **user-visible features** (real-time scan, web shield, ransomware, firewall, VPN kill switch, password vault, dark web, etc.).  
2. Tag each: `must-have` / `later` / `skip for v1`.  
3. Note **Windows integration surface** (drivers, WFP, ETW, AMSI, SmartScreen, filter drivers — at concept level).  
4. Output a gap matrix: *Top suite capability → Securely today → proposed Securely approach*.

### B. “Analyze anything” (VirusTotal-like) — architecture research

Design a Securely **Analyze** surface (dashboard + optional website):

- Inputs: file upload, drag-drop, URL/link paste, hash lookup  
- Pipeline: local static checks → optional sandbox → multi-signal reputation (own DB + **legitimate** provider APIs with keys in server env — never client)  
- Verdict UX: clean / suspicious / malicious / unknown + evidence timeline  
- Privacy: hash-first, opt-in upload, sensitive-file blocklist (reuse Securely sensitive detector)  
- Rate limits, malware retention policy, abuse controls  

Research open patterns: YARA, ClamAV, PE parsing, URL reputation lists, sandbox designs (concept), how VT-style multi-engine UIs are composed **without** scraping VT.

### C. Lightweight antivirus — architecture research

Propose a **Windows-first, customizable, lightweight** AV layer:

- On-demand scan (paths, extensions, archives)  
- Real-time: which hooks are realistic for a small team (AMSI consumer, Defender coexistence, filesystem mini-filter vs user-mode watchers)  
- Quarantine, exclusions, schedules, “Securely mode” profiles (Quiet / Balanced / Paranoid)  
- Coexistence with Windows Defender (prefer complement, not replace, for v1)  
- Signature + heuristic + behavior signals; update channel design  

Cite open projects and Microsoft public docs. Flag anything that needs kernel signing / HVCI / attestation as **phase 3+**.

### D. Lightweight VPN — architecture research

Propose a **customizable VPN** that feels Nord-class without cloning branding:

- Protocol choice (prefer WireGuard)  
- Kill switch, split tunnel, Always-On, per-app rules (Windows capabilities)  
- Server list UX, obfuscation as optional later  
- Trust model: who runs servers (self-host vs partner), no-logs claims that are *honest*  
- Integration with Securely UI (glass dashboard already exists)

### E. Proactive + real-time Securely-unique core

Deepen what only Securely owns:

- Continuous screen monitoring with consent  
- Local sensitive-data gate (already started — expand categories & false-positive control)  
- Phishing hitboxes, audit log, timed/24-7 modes  
- Cross-feature actions: “suspicious download → Analyze tab”; “login page → pause AI upload”; “VPN off on bank domain” (policy ideas)

### F. REA / reverse-engineering literacy (bounded)

Using public materials from [rea.tools](https://rea.tools/), [`morluto/rea`](https://github.com/morluto/rea), and [`morluto/awesome-reverse-engineering`](https://github.com/morluto/awesome-reverse-engineering):

1. Summarize how agent-assisted RE workflows work (inspect → explain → rebuild).  
2. Propose **allowed REA targets** for this project: SecurelyShell.exe, open malware *samples in a lab*, open-source AV/VPN demos — **never** commercial AV/VPN vendors.  
3. If REA is not installed, output the exact setup prompt from rea.tools for the human to approve (`npx rea-agents@latest setup`) — do not silently install without approval.  
4. Produce a short “how we’d use REA to harden Securely” checklist (e.g. understand our own capture/OCR path, not competitor apps).

### G. Threat model & honest marketing

Update/extend `docs/THREAT_MODEL.md` and draft claim language that stays true:

- What Securely **will** and **will not** claim vs Norton-class suites  
- Data flows for Analyze / AV / VPN / screen OCR  
- Abuse cases and mitigations  

---

## Deliverables (required artifacts)

Write these into the repo (create folders as needed):

1. `docs/power-suite/00-EXECUTIVE-BRIEF.md` — 1–2 pages: vision, uniqueness, non-goals  
2. `docs/power-suite/01-COMPETITIVE-MAP.md` — feature matrix + sources  
3. `docs/power-suite/02-ANALYZE-ANYTHING.md` — VT-like design + APIs  
4. `docs/power-suite/03-LIGHTWEIGHT-AV.md` — architecture + phases  
5. `docs/power-suite/04-LIGHTWEIGHT-VPN.md` — architecture + phases  
6. `docs/power-suite/05-REALTIME-PROACTIVE.md` — Securely-unique real-time design  
7. `docs/power-suite/06-ARCHITECTURE.md` — one system diagram (mermaid) tying pill, dashboard, host, APIs, VPN, AV, Analyze  
8. `docs/power-suite/07-ROADMAP.md` — v0.2 / v0.3 / v1.0 milestones, effort, risks  
9. `docs/power-suite/08-REA-BOUNDED-USE.md` — allowed REA usage policy for this team  
10. Append a short `brain/log.json`-ready note list under a draft heading (do not bump version unless the human asks to ship)

Also produce a **Cursor implementation prompt** at the end of `07-ROADMAP.md` for the next agent to build **only Phase 1** (Analyze tab MVP + policy toggles), not the entire suite at once.

---

## Method

1. Explore current Securely code before proposing greenfield.  
2. Prefer multiple reputable public sources per claim; link them.  
3. Separate **UX inspiration** from **implementation**.  
4. Call out legal/compliance (export crypto, VPN jurisdiction, malware sample handling).  
5. When stuck between “full AV” vs “Defender companion,” recommend the path that ships quality fastest without lying in marketing.  
6. Do not commit or deploy unless the human explicitly asks.

---

## Success criteria

- A credible plan for a **proactive multi-feature Securely** that feels premium and unique  
- Clear **Phase 1** that can start in the existing WinForms + WebView2 + website stack  
- Zero instructions that require reverse-engineering closed commercial security products  
- Explicit reuse of Securely’s screen + sensitive-gate advantage as the product wedge  

Begin with a short plan, then execute the workstreams and write the docs.

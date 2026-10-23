# Competitive capability map (public sources only)

Sources consulted: vendor marketing/help pages, Microsoft Learn, VirusTotal public docs, WireGuard Windows docs. **No closed-binary reverse engineering.**

## Tag legend

- `must-have` — needed for Securely to feel like a suite by v1.0  
- `later` — valuable after core wedge ships  
- `skip` — out of scope or poor fit for a small team  

## Feature inventory

### Norton 360 (public feature hub / datasheet)

| Feature | Tag | Windows surface (concept) | Securely approach |
|---------|-----|---------------------------|-------------------|
| Real-time malware / ransomware | must-have (outcome) | Filter drivers, behavior, cloud intel | Companion: on-demand + download watch + Defender status; not replace Defender v1 |
| Safe Web / phishing sites | must-have | Browser / DNS / URL reputation | Screen OCR phishing + URL Analyze + optional DNS blocklist later |
| Scam / AI scam protection | must-have | Content classification | **Own:** screen OCR + AI (already) |
| VPN | must-have | Tunnel + WFP | WireGuard client (04) |
| Password manager | later | Extension / vault | Skip until after VPN/AV |
| Dark web monitoring | skip | Identity APIs | Partner or skip |
| SafeCam | later | Device access monitoring | Optional later |
| Cloud backup / parental | skip | — | Skip |
| Smart Firewall | later | WFP | Prefer Windows Firewall + VPN kill switch first |

Refs: [Norton features](https://us.norton.com/features), [Norton 360 comparison](https://us.norton.com/feature/norton-360-features-comparison)

### Bitdefender Total Security

| Feature | Tag | Notes for Securely |
|---------|-----|-------------------|
| Real-time AV + Advanced Threat Defense | must-have (outcome) | Behavior monitoring is hard; phase 2+ heuristics / AMSI consumer research |
| Multi-layer ransomware | later | Prefer Defender Controlled Folder Access coexistence messaging |
| Firewall | later | Don’t replace Windows Firewall early |
| Network threat prevention | later | URL/DNS reputation in Analyze |
| VPN (capped on suite plans) | must-have | Full WireGuard profiles; honest traffic policy |
| Safepay / password vault | skip / later | Screen pause on login already covers part of Safepay intent |
| Webcam/mic protection | later | Optional |

Refs: [Bitdefender Total Security](https://www.bitdefender.com/en-us/consumer/total-security)

### Malwarebytes (public positioning)

| Feature | Tag | Securely approach |
|---------|-----|-------------------|
| On-demand / real-time malware | must-have | On-demand first; real-time via user-mode watchers then AMSI |
| Web protection | must-have | Analyze URLs + screen cues |
| Lightweight / remediation focus | must-have | Match “lightweight” brand; quarantine UX |

### Windows Defender (Microsoft Learn)

| Capability | Tag | Securely approach |
|------------|-----|-------------------|
| Real-time protection | must-have (keep on) | **Do not register as primary AV in v1** — avoids forcing Defender passive/off |
| AMSI | must-have (integrate) | Call AMSI from Analyze / script paths; optional provider later |
| Cloud-delivered protection | later | Surface Defender health in dashboard |
| Controlled folder access | later | Deep-link to Windows Security settings |

Refs: [AMSI](https://learn.microsoft.com/en-us/windows/win32/amsi/antimalware-scan-interface-portal), [Defender compatibility](https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-antivirus-compatibility)

### NordVPN / Mullvad / Proton (public)

| Feature | Tag | Securely approach |
|---------|-----|-------------------|
| WireGuard / NordLynx-class speed | must-have | Prefer open WireGuard |
| Kill switch (system / app) | must-have | WFP patterns from wireguard-windows |
| Split tunnel | must-have | AllowedIPs + app rules where feasible |
| Always-On | later | Profile + reconnect |
| Threat Protection (DNS/URL) | later | Fold into Analyze / Protect policies |
| Meshnet / double VPN / obfuscation | skip / later | After basic tunnel quality |
| Audited no-logs | must-have (claim honesty) | Only claim after jurisdiction + audit plan |

Refs: [NordVPN kill switch](https://nordvpn.com/features/vpn-kill-switch/), [WireGuard Windows netquirk](https://git.zx2c4.com/wireguard-windows/about/docs/netquirk.md), Mullvad/Proton public WireGuard docs

### VirusTotal / Hybrid Analysis / URLhaus

| Feature | Tag | Securely approach |
|---------|-----|-------------------|
| Multi-engine file verdict | must-have (UX) | Licensed APIs (VT official, MetaDefender, etc.) server-side — **no scrape** |
| URL / domain / IP report | must-have | Same + free feeds (URLhaus) where ToS allows |
| Hash lookup first | must-have | Privacy: hash before upload |
| Sandbox behavior | later | Hybrid Analysis API or defer |
| Community comments | skip | Skip |

Refs: [VirusTotal how it works](https://docs.virustotal.com/docs/how-it-works), [VT API v3](https://docs.virustotal.com/reference/api-v2-v3-migration-guide)

## Gap matrix

| Top-suite capability | Securely today | Proposed Securely |
|----------------------|----------------|-------------------|
| Real-time disk AV | None | Defender companion + download folder watch → Analyze |
| Web / phishing shield | Screen OCR + AI | + URL Analyze + optional DNS |
| Multi-engine file scan | None | Analyze tab + server fan-out APIs |
| VPN | None | WireGuard UI in dashboard |
| Password vault | None | Later |
| Screen phishing | **Strong start** | Deepen Timed/24·7, hitboxes, proactive actions |
| Local PII gate | **Shipping** (`sensitive.js`) | Expand FP control; reuse in Analyze uploads |
| Suite dashboard | Monitoring / Settings / Audit / Credits | + Analyze / Protect / VPN |

## Windows integration surface (concept-level)

| Layer | Use in Securely | Phase |
|-------|-----------------|-------|
| User-mode file watchers | New downloads → Analyze prompt | 1–2 |
| AMSI (caller) | Scan scripts/content buffers | 2 |
| Windows Security Center registration | Only if becoming primary AV | 3+ (avoid early) |
| WFP | VPN kill switch | 2–3 |
| ETW / Sysmon-like | Behavior signals | 3+ |
| Mini-filter / ELAM | Full AV | 3+ / partner |

## UX inspiration vs implementation

**Inspiration (allowed):** clean verdict cards, one-tap connect VPN, Quiet/Balanced/Paranoid profiles, drag-drop Analyze.

**Implementation (required):** open protocols, Microsoft public APIs, licensed threat APIs, Securely’s own OCR/PII stack — never dumped competitor binaries.

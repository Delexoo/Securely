# Threat model (baseline + power suite research)

Securely assists users by OCR + remote LLM classification of primary-monitor content, and (planned) Analyze / Protect / VPN layers. It is **not** a guarantee against all phishing, a full EDR, or a replacement for Windows Defender in v1.

Research plan: `docs/power-suite/`.

## Assets

- User screenshots / OCR text (may contain passwords, messages, financial data)
- Uploaded files / hashes / URLs submitted to Analyze (planned)
- Quarantine store (planned)
- VPN configs and tunnel state (planned)
- Provider API keys (OpenRouter, Stripe, threat-intel APIs)
- Installer integrity / update channel
- Entitlements (Stripe license)

## What Securely will claim vs will not

| Will claim (when true) | Will not claim |
|------------------------|----------------|
| Assists with on-screen phishing/scam cues | Stops all malware / “100% virus protection” |
| Local sensitive gate before AI upload | Perfect PII detection |
| Multi-signal Analyze via licensed APIs | “Same engines as VirusTotal scraped” |
| Companion protection beside Defender | Replaces antivirus |
| WireGuard VPN with kill switch (when shipped) | Audited no-logs before an audit exists |

## Data flows

| Flow | Data | Trust notes |
|------|------|-------------|
| Screen OCR → AI | Redacted text (preferred); image only if user continues after sensitive warning | Server OpenRouter key; failed → Unsure |
| Analyze hash | Hash only | Prefer before any upload |
| Analyze file | Bytes opt-in | Retention policy; sensitive blocklist |
| Analyze URL | URL string | Server-side fetch carefully; no SSRF to internal nets |
| Protect watcher | Paths + hashes | Local first |
| VPN | Keys/config | Host helper; not in WebView storage plaintext long-term |

## Priority threats

| Threat | Path | Mitigation now | Residual |
|--------|------|----------------|----------|
| Embedded provider keys | Repo / binary | Keys scrubbed; Edge uses env secret | Git history may still contain old keys — **rotate** |
| Unrestricted AI proxy | Public Edge URL | Optional `REQUIRE_AUTH`; text size + timeout caps | CORS `*`; no per-user quota yet |
| Prompt injection via OCR | Malicious page text | System prompt treats OCR as evidence; failed calls ≠ Safe | Model can still be manipulated — layer heuristics |
| False Safe | Model error / outage | Empty/failed → Unsure/503 | Need local heuristics + tests |
| Stripe entitlement fraud | Fake webhook / client “success” | Checkout-status + webhook path improving | Do not grant paid features client-side only |
| Local secret theft | Malware on user PC | N/A beyond least privilege | DPAPI planned for any future local keys |
| Tampered installer | Supply chain | Not signed in this workspace | Code signing required for release |
| Analyze malware retention / abuse | Upload API | Planned: rate limits, short retention, auth | Until shipped, do not accept public uploads |
| VPN trust overclaim | Marketing | BYO WireGuard first; partner audit before no-logs | Jurisdiction risk if self-hosting |
| Disabling Defender accidentally | AV registration | v1 = companion only | User may still turn Defender off manually |

## Abuse cases & mitigations (suite)

| Abuse | Mitigation |
|-------|------------|
| Using Analyze as free malware distribution CDN | Auth + retention + no public download of samples |
| SSRF via URL analyze | Block private IP ranges; timeouts; size caps |
| Flooding OpenRouter / VT quota | Per-license rate limits |
| REA / research misuse against third-party AV | Policy in `docs/power-suite/08-REA-BOUNDED-USE.md` |

Full architecture notes: `docs/OPENROUTER_CONFIGURATION.md`, `docs/INTEGRATION_STATUS.md`, `docs/power-suite/06-ARCHITECTURE.md`.

# Threat model (baseline)

Securely assists users by OCR + remote LLM classification of primary-monitor content. It is **not** a guarantee against all phishing or a hardened EDR.

## Assets

- User screenshots / OCR text (may contain passwords, messages, financial data)
- Provider API keys (OpenRouter, Stripe)
- Installer integrity / update channel
- Entitlements (future Stripe license)

## Priority threats

| Threat | Path | Mitigation now | Residual |
|--------|------|----------------|----------|
| Embedded provider keys | Repo / binary | Keys scrubbed; Edge uses env secret | Git history may still contain old keys — **rotate** |
| Unrestricted AI proxy | Public Edge URL | Optional `REQUIRE_AUTH`; text size + timeout caps | CORS `*`; no per-user quota yet |
| Prompt injection via OCR | Malicious page text | System prompt treats OCR as evidence; failed calls ≠ Safe | Model can still be manipulated — layer heuristics |
| False Safe | Model error / outage | Empty/failed → Unsure/503 | Need local heuristics + tests |
| Stripe entitlement fraud | Fake webhook / client “success” | Not implemented | Do not grant paid features client-side |
| Local secret theft | Malware on user PC | N/A beyond least privilege | DPAPI planned for any future local keys |
| Tampered installer | Supply chain | Not signed in this workspace | Code signing required for release |

Full architecture notes: `docs/OPENROUTER_CONFIGURATION.md`, `docs/INTEGRATION_STATUS.md`.

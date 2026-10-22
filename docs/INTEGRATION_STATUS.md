# Integration status

Classification: **Verified** | **Implemented, not fully verified** | **Partially mitigated** | **Not implemented** | **Not applicable**

| Service | Status | Notes |
|---------|--------|-------|
| OpenRouter (Edge analyze) | Implemented, not fully verified | Code in `supabase/functions/analyze/index.ts` uses OpenRouter. No local `OPENROUTER_API_KEY`; deploy + live call not verified here. |
| Groq | Partially mitigated | Active Edge path migrated away. Legacy client code may still *mention* Groq URLs; hardcoded `gsk_` keys scrubbed from workspace source. Rotate any keys that ever leaked. |
| Supabase Auth / DB / RLS | Not implemented | Edge function only; no migrations or RLS policies in-repo. |
| Stripe Checkout / webhooks | Not implemented | Docs and CLI present; no working `api/checkout` + signed webhook in Securely trees yet. Pricing page CTAs do not charge. |
| Website hosting / HTTPS | Not implemented | No production URL or security-header host config found. |
| Desktop → analyze proxy | Partially mitigated | `SECURELY_API_URL` pattern in Securely Project; rewrite `securely-app` core not fully wired. |

Update this file when a live test succeeds.

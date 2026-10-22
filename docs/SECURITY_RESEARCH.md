# Security research notes

Last updated: 2026-10-22. Sources consulted (primary where linked):

- OWASP ASVS / Top 10 (application risks: injection, broken access, SSRF, XSS)
- OpenRouter API docs: https://openrouter.ai/docs/api-reference/overview
- OpenRouter cost routing guidance: https://openrouter.ai/blog/tutorials/how-to-get-the-lowest-cost-llm-inference-on-openrouter/
- OpenRouter Meta Llama model listing / pricing comparisons (Oct 2026 reads via third-party price tables citing OpenRouter)
- Stripe webhook signing (official docs — implementation still pending)
- Supabase RLS guidance (official docs — schema still pending)
- Microsoft DPAPI / WebView2 security notes (for future desktop secret storage)

## Decisions taken from research

1. **Server-side LLM only** — shared provider keys must not ship in installers (obfuscation ≠ secrecy).
2. **OpenRouter exclusive** — single OpenAI-compatible schema; model swappable via env.
3. **Default model `meta-llama/llama-3.3-8b-instruct`** — cost/quality trade for short threat labels; not free-tier (quota/reliability) and not frontier (cost).
4. **Failed assessments ≠ Safe** — Edge returns 503 or Unsure on upstream failure.
5. **OCR text, not full screenshots, as default remote payload** — reduces image retention risk (OCR can still contain secrets).

## Not yet verified live

- Deployed Edge secrets
- Stripe test-mode checkout + webhook idempotency
- Supabase RLS on any user tables
- Production HTTPS headers

# OpenRouter configuration

**Status:** Implemented in Edge Function code; live deployment not verified in this environment (no `OPENROUTER_API_KEY` present in local `.env`).

## Exclusive provider

Securely uses **OpenRouter only** for LLM threat classification.

- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Auth: `Authorization: Bearer <OPENROUTER_API_KEY>`
- App headers: `HTTP-Referer`, `X-OpenRouter-Title: Securely`

## Default model

| Setting | Value |
|--------|--------|
| Primary | `meta-llama/llama-3.3-8b-instruct` |
| Fallback list | same + `meta-llama/llama-3.1-8b-instruct` |
| Why | Low cost (~$0.05–0.08 / M tokens class on OpenRouter as of Oct 2026 research), strong enough for short classification labels, large context, widely available. Not the absolute cheapest free tier (free tiers are rate-limited and variable). |
| Not chosen | Frontier GPT/Claude (cost); vision models (product sends OCR **text**, not screenshots, by default); Groq-hosted IDs (Groq is removed as a provider). |

Override with Edge secret / env `OPENROUTER_MODEL`.

## Cost controls (server)

- OCR text truncated to 12 000 characters
- `max_tokens` capped at 512
- 45 s request timeout
- Failed / empty upstream responses → **Unsure** or HTTP 503 — never **Safe**

## Credential architecture

| Layer | Holds OpenRouter key? |
|-------|------------------------|
| Desktop client / installer | **No** |
| Website JS | **No** |
| Supabase Edge `analyze` secrets | **Yes** |
| User-supplied BYOK | Not implemented |

Clients call `SECURELY_API_URL` with optional JWT. Rotate any keys that were previously committed in source.

## Configure

1. Create an OpenRouter key at openrouter.ai
2. Supabase → Edge Functions → Secrets: `OPENROUTER_API_KEY`, optional `OPENROUTER_MODEL`, `REQUIRE_AUTH`
3. Redeploy `supabase/functions/analyze`
4. Point clients at the function URL via `SECURELY_API_URL`

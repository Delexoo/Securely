# Securely API (Vercel serverless)

`POST /api/analyze` — Threat analysis using **Groq**. Stack: **Supabase**, **Vercel**, **Stripe**, **Groq**.

**Important for distribution:** Do **not** put your Groq API key in the desktop app. Store it in **Supabase Vault**; the API reads it server-side. The desktop app only needs `SECURELY_API_URL` (your Vercel URL) and optionally `SECURELY_API_JWT` (Supabase JWT).

## Request

- **Body:** `{ "text": "OCR text from screen" }`
- **Optional:** `Authorization: Bearer <Supabase JWT>`
- **Optional:** `license_key` in body (when using Stripe)

## Storing the API key (Supabase — recommended for selling)

1. In **Supabase** (your project): use **Vault** or a secure storage method to store a secret named `GROQ_API_KEY` with your Groq key value. (If your Supabase plan supports Vault / `get_secret` RPC, use that; otherwise store in a table with restricted access and read it in your backend.)
2. On **Vercel**: set **only** `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. Do **not** set `GROQ_API_KEY` in Vercel — the API will fetch it from Supabase so the key never lives in the app or in Vercel env if you prefer.
3. **Desktop app:** Set `SECURELY_API_URL=https://your-project.vercel.app/api/analyze` (env or config). The app sends OCR text to your API; no key in the app.

## Vercel environment variables

Set these in your Vercel project (**Settings → Environment Variables**):

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes* | Supabase project URL (API fetches Groq key from Vault here) |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes* | For Supabase Vault `get_secret("GROQ_API_KEY")` |
| `GROQ_API_KEY` | No** | Groq key (optional if using Supabase Vault only) |
| `GROQ_MODEL` | No | Default: `llama-3.1-8b-instant` |
| `SUPABASE_JWT_SECRET` | No*** | To verify `Authorization: Bearer` Supabase JWT |
| `REQUIRE_AUTH` | No | Set `1` to require Supabase JWT on every request |
| `STRIPE_SECRET_KEY` | No | For Stripe subscription/license checks |
| `REQUIRE_STRIPE` | No | Set `1` to require valid Stripe access |

\* For **key in Supabase only**: set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`; store `GROQ_API_KEY` in Supabase Vault.  
\** Set in Vercel only if you prefer not to use Vault; otherwise the API gets the key from Supabase.  
\*** Required when `REQUIRE_AUTH=1`.

## Responses

- **200** — `{ "analysis": "Safe|Suspicious: ...|Malicious: ...|Unsure: ..." }`
- **401** — Missing or invalid Supabase JWT (when `REQUIRE_AUTH=1`)
- **402** — Valid subscription/license required (when `REQUIRE_STRIPE=1`)
- **503** — Groq key missing or analysis failed

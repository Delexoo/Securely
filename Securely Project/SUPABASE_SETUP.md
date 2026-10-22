# Securely + Supabase API Setup

This guide gets the **Securely** desktop app using your **Supabase Edge Function** for AI threat analysis, so your Groq API key stays on Supabase and never in the app.

## What you get

- **Supabase Edge Function** `analyze`: runs the same threat-analysis logic as Securely, using Groq.
- **Securely.py** calls `SECURELY_API_URL` (your Supabase function URL) and optionally sends `SECURELY_API_JWT` for auth.

## 1. Supabase project

1. Go to [supabase.com](https://supabase.com) and sign in.
2. Create a new project (or use an existing one).
3. Note your **Project URL**: `https://<project-ref>.supabase.co`.

## 2. Store your Groq API key in Supabase (do not put it in code)

Your Edge Function reads the key from **Edge Function Secrets** (so the key never lives in your repo or desktop app).

1. In Supabase Dashboard: **Project Settings** (gear) → **Edge Functions**.
2. Under **Secrets** (or **Vault** depending on your plan), add:
   - **Name:** `GROQ_API_KEY`
   - **Value:** your Groq API key (from [console.groq.com](https://console.groq.com)).
3. Optional: add `GROQ_MODEL` (e.g. `llama-3.1-8b-instant`) and/or `REQUIRE_AUTH` = `1` to require a Bearer token on every request.

## 3. Deploy the Edge Function

You need the Supabase CLI and to be logged in.

```bash
# Install Supabase CLI if needed (Windows: scoop install supabase, or download from GitHub)
npm install -g supabase

# Log in
supabase login

# From your project root (where supabase/functions/analyze exists)
cd "d:\Securely Project"
supabase link --project-ref YOUR_PROJECT_REF
supabase functions deploy analyze
```

Replace `YOUR_PROJECT_REF` with the ref from your project URL (e.g. `abcdefghij` from `https://abcdefghij.supabase.co`).

If you haven’t linked the project yet, create it with `supabase init` in this folder first, then `supabase link`.

After deploy, your function URL is:

```text
https://<project-ref>.supabase.co/functions/v1/analyze
```

## 4. Connect Securely.py to the API

Securely reads these environment variables (you can use the aliases in the second column):

| Variable | Alias | Required | Description |
|----------|--------|----------|-------------|
| `SECURELY_API_URL` | `GROQ_API_URL` | Yes | Full URL of your analyze function, e.g. `https://YOUR_REF.supabase.co/functions/v1/analyze` |
| `SECURELY_API_JWT` | `SUPABASE_KEY` | No | Supabase anon key or JWT for `Authorization: Bearer` (if you set `REQUIRE_AUTH=1` on the function) |

### Option A: Use a `.env` file (recommended)

In the same folder as `Securely.py` create a file named `.env`:

```env
SECURELY_API_URL=https://YOUR_PROJECT_REF.supabase.co/functions/v1/analyze
# Or use: GROQ_API_URL=https://YOUR_PROJECT_REF.supabase.co/functions/v1/analyze

# Optional (if your Edge Function has REQUIRE_AUTH=1):
# SECURELY_API_JWT=your-supabase-anon-key-or-jwt
# Or: SUPABASE_KEY=your-supabase-anon-key-or-jwt
```

Install the optional dependency so Securely can load `.env`:

```bash
pip install python-dotenv
```

Then run Securely as usual; it will use the Supabase API.

### Option B: Set environment variables in the shell

**Windows (PowerShell):**

```powershell
$env:SECURELY_API_URL = "https://YOUR_PROJECT_REF.supabase.co/functions/v1/analyze"
python Securely.py
```

**Windows (Command Prompt):**

```cmd
set SECURELY_API_URL=https://YOUR_PROJECT_REF.supabase.co/functions/v1/analyze
python Securely.py
```

Replace `YOUR_PROJECT_REF` with your actual Supabase project reference.

## 5. Optional: Require auth (JWT)

If you set the secret `REQUIRE_AUTH=1` for the Edge Function, every request must include a valid Supabase JWT:

```env
SECURELY_API_JWT=<your-supabase-anon-key-or-user-jwt>
```

For a desktop app you can use the **anon** key for simple auth, or implement Supabase Auth and use a user’s JWT.

## 6. Verify it works

1. Set `SECURELY_API_URL` (and `SECURELY_API_JWT` if using auth).
2. Run `python Securely.py`.
3. Trigger a scan that uses AI (e.g. let it capture a screen and analyze). In the log you should see something like “Calling server API: …” and “Server API returned 200 OK”.

If you see **401**, check `SECURELY_API_JWT` and that `REQUIRE_AUTH` matches. If you see **503**, check that `GROQ_API_KEY` is set in Supabase Edge Function secrets and that the Groq key is valid.

## Summary

- **Supabase:** Store `GROQ_API_KEY` (and optionally `GROQ_MODEL`, `REQUIRE_AUTH`) in Edge Function secrets. Deploy `supabase/functions/analyze`.
- **Securely:** Set `SECURELY_API_URL` to `https://<project-ref>.supabase.co/functions/v1/analyze` (and `SECURELY_API_JWT` if you require auth). Use a `.env` file and `python-dotenv` for convenience.

Your Groq API key stays in Supabase; the desktop app only talks to your Supabase Edge Function.

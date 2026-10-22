# Security policy

## Supported surfaces

- `securely-app/` — current Windows rewrite (host + WebView UI + core)
- `Securely Project/supabase/functions/analyze` — server-side OpenRouter proxy
- `Securely-Website/` — marketing site

Legacy trees (`sSecurely/`, `Securely C#/`) are historical; do not ship them with embedded provider keys.

## Reporting a vulnerability

Email the project operator (add a public contact once published). Do not file public issues that include secrets, screenshots of user desktops, or live API keys.

Please include: affected component, impact, and steps to reproduce without sending real user screen data.

## Secrets

- Never commit `.env` files (see root `.gitignore`).
- Never embed OpenRouter or Stripe secret keys in desktop binaries or website JS.
- If a key was ever committed, **rotate it** at the provider immediately.

## Limitations

Securely is an assistive monitor. It does not guarantee detection of every phishing attempt, does not replace antivirus, and cannot protect a fully compromised OS.

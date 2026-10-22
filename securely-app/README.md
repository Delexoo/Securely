# Securely (rewrite)

Hooxie-style glass pill + Securely threat monitoring. Built under `securely-app/` so old Python/WPF trees stay untouched.

## Run (scaffold)

```powershell
cd E:\MasterVault\Securely\securely-app\host
dotnet run
```

Loads `https://securely.local/index.html` from `ui/public` via WebView2 virtual host mapping.

- **Ctrl+\** — hide/show (Hooxie-matched)
- Quick Scan / More / Look work as UI stubs; OCR/AI pipeline wires next via `core/`

## Layout

- `host/` — WinForms + WebView2 shell
- `ui/public/` — pill UI (Hooxie tokens)
- `core/` — capture / OCR / analyze (evolving from SecurelyCore)
- `docs/PLAN.md` — stack + chrome map
- `docs/FEATURE_CHECKLIST.md` — must-preserve features

## Config (later)

- `SECURELY_API_URL` — analyze proxy
- Optional JWT for license
- Settings JSON under `%AppData%\Securely\`

# Securely rewrite — plan

## Stack (decision)

| Layer | Choice | Why |
|-------|--------|-----|
| **Host** | .NET WinForms + WebView2 (`host/`) | Match Hooxie shell: transparent, topmost, region radius, fit/hide |
| **UI** | HTML/CSS/JS forked from Hooxie `public/` (`ui/public/`) | Literal glass/pill/circles — no CustomTkinter / old WPF island look |
| **Core** | C# library evolved from `SecurelyCore` (`core/`) | Already has ScreenMonitor, OCR, analyzer, audit, education; stays in-process with host |
| **API** | Keep Supabase Edge `analyze` + `SECURELY_API_URL` client | No Groq keys in client; 401/402 handling from Securely Project |

Node bridge (Hooxie `widget.ts`) is **not** required: host maps `https://securely.local` → `ui/public` and accepts `chrome.webview.postMessage` for fit/move/visible/quit.

## Folder layout

```
securely-app/
  host/           SecurelyShell (WinForms + WebView2)
  ui/public/      Pill widget (Hooxie chrome → Securely jobs)
  ui/dashboard/   Optional Settings/Audit/Education (Hooxie dash style later)
  core/           Capture, OCR, analyze, hitboxes, audit, settings JSON
  docs/           PLAN + feature checklist
```

Old trees under `sSecurely/`, `Securely Project/`, `Securely C#/` stay until Kelly says delete.

## Chrome mapping

| Hooxie | Securely |
|--------|----------|
| Prompt / send | Status line + Quick Scan / Stop |
| Chat toggle / band | Threat event stream |
| Presets | Scan modes + duration |
| More menu | Test Mode, Look, hide, exit |
| Usage ring | Scan progress / threat level |
| Dashboard | Settings + Audit + Education |
| Drag | Move overlay |
| Setup | OCR tip, consent, hotkey, disclosure |

## Defaults for open questions

1. **Hotkey:** `Ctrl+\` (match Hooxie slide-hide). Documented in setup + More.
2. **Response classes:** Prefer Project/API dialect (`Safe` / `Suspicious` / `Malicious` / `Unsure`) plus `LEGITIMATE_LOGIN` / `LEGITIMATE_PAYMENT` for auto-pause. Unify in core.
3. **HWND window target:** Keep in core; wire UI as advanced later (Python capture existed, UI was unwired).
4. **Timed presets:** 5 / 15 / 30 / 60 (+ allow 1–60 custom in settings).
5. **Credential pre-flight** (Project only): keep as optional gate before sending OCR text.

## Implementation order

1. ~~Inventory~~ → ~~Plan~~ → ~~Scaffold shell~~ (this)
2. Port Look / light-dark polish; dashboard window stub
3. Wire `core`: Quick / Timed / 24/7, OCR, proxy analyze, auto-pause
4. Hitboxes overlay, toasts, sound, cooldown, settings JSON
5. Audit, instant analysis, education, Test Mode
6. Checklist verify

## Not porting

LockIn chat, Ask-me-anything, lock-in message rotation, TaskFlow naming, hardcoded Groq keys, backdrop-filter blur, purple AI-slop themes.

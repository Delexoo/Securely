# Recreate Securely — Agent Prompt

Copy everything below the line into a new Cursor agent chat (with workspace access to both folders).

---

## Mission

Rebuild **Securely** as a clean, optimized Windows desktop app. Keep **all current Securely product features**. Replace the UI chrome with a near-literal copy of the **Hooxie** overlay widget (glass pill + expandable panels), adapted to Securely’s threat-monitoring domain — not Hooxie’s Cursor-agent domain.

Do **not** invent a new visual language. Open Hooxie’s UI files and port structure, tokens, and interaction patterns. Do **not** ship LockIn/TaskFlow leftover branding or chat.

---

## Workspaces (read before writing code)

| Path | Role |
|------|------|
| `E:\MasterVault\Securely\` | Source of truth for **features** |
| `E:\MasterVault\hooxie\` | Source of truth for **UI look & shell architecture** |

### Securely — read these first (feature inventory)

1. `E:\MasterVault\Securely\sSecurely\Securely.py` — full Python product (monolith, ~7k lines)
2. `E:\MasterVault\Securely\Securely Project\Securely.py` — same + API/Supabase/JWT path
3. `E:\MasterVault\Securely\Securely C#\SecurelyCore\` — ported core (`ScreenMonitor`, `GroqThreatAnalyzer`, OCR, audit, education)
4. `E:\MasterVault\Securely\Securely C#\lockinnigga\` — partial WPF island UI (reference behavior only; **do not copy its look**)
5. `E:\MasterVault\Securely\Securely Project\api\`, `supabase\functions\analyze\` — server analyze + license pattern
6. Marketing only (features/pricing context): `Securely-Website\`

Ignore: `bin/`, `obj/`, `publish/`, `node_modules/`, `CS50/`, `LockInNigga2/`, PyInstaller `dist/`.

### Hooxie — copy UI from these (do not redesign)

**Widget (primary):**
- `E:\MasterVault\hooxie\public\app.css` — design tokens & components
- `E:\MasterVault\hooxie\public\index.html` — DOM chrome hierarchy
- `E:\MasterVault\hooxie\public\app.js` — look/opacity/pill shape/fold behavior
- `E:\MasterVault\hooxie\public\reply-format.js` — only if you need rich text bubbles

**Host shell (architecture to mirror):**
- `E:\MasterVault\hooxie\src\widget-shell\Program.cs` — WinForms + WebView2, transparent, topmost, region radius
- `E:\MasterVault\hooxie\src\widget.ts` — fit sizes, host protocol

**Optional settings surface:**
- `E:\MasterVault\hooxie\site\dashboard.html` + `site\dash.css` — separate dashboard look (Manrope / light card). Use only for a Settings/Dashboard window, not the pill.

---

## What Securely is

Windows real-time **AI + OCR screen threat monitor**: capture primary display → OCR → LLM analysis → flag phishing/scams/malicious UI → notify, log, optional hitboxes. Auto-pause on legitimate login/payment pages. Consumer security overlay, not antivirus.

---

## Feature checklist (must preserve)

Track every item. Mark done in your plan as you implement. Do not drop features for “MVP” unless Kelly explicitly says so.

### Monitoring
- [ ] **Quick Scan** — one-shot capture → OCR → AI → stop (no auto-pause)
- [ ] **Timed scan** — run for chosen duration (support 1m–1h; presets 5/15/30/60), countdown UI, then stop
- [ ] **24/7 continuous** — loop with consent gate before enable
- [ ] **Primary monitor only** (multi-monitor: ignore secondary)
- [ ] Optional **window target** (HWND must be fully on primary) — Python has this; keep it

### Pipeline
- [ ] Screenshot (mss / GDI equivalent)
- [ ] Mask notification tray region (~bottom-right 15%×25%) before analysis
- [ ] OCR (Tesseract) with filters for Securely’s own UI / IDE noise
- [ ] LLM analysis (prefer **server proxy** `SECURELY_API_URL` + optional JWT; no hardcoded Groq keys in client)
- [ ] Heuristics: suspicious URLs/domains, login vs payment detection, soft-ignore for clear dev environments
- [ ] Response classes: `SAFE`, `SUSPICIOUS`, `UNSURE`, `LEGITIMATE_LOGIN`, `LEGITIMATE_PAYMENT`
- [ ] Analysis cache / debounce to cut API cost
- [ ] Multi-key / rate-limit handling on server side

### Safety UX
- [ ] **Auto-pause ~180s** on legitimate login/payment with countdown; auto-resume (skip during Quick Scan)
- [ ] Explicit **consent** before continuous monitoring
- [ ] Clear disclosure that screen content is analyzed

### Overlays & alerts
- [ ] **Hitboxes** — fullscreen click-through topmost overlay; red translucent boxes on OCR matches
- [ ] Desktop **toasts** + optional **sound**
- [ ] Cooldown so the same threat doesn’t spam
- [ ] Test notification control

### Modes / settings
- [ ] Hitboxes on/off
- [ ] Strict / keyword local scan on/off
- [ ] Test Mode (fake threats without live AI)
- [ ] Notifications on/off
- [ ] Sound on/off
- [ ] Timed-scan duration
- [ ] Widget opacity (map to Hooxie Look/opacity → `--glass`)
- [ ] Hide/show hotkey (Hooxie uses Ctrl+\; Securely C# used Alt+\ — pick one, document it, match Hooxie slide-hide feel)

### Analysis & education
- [ ] Audit log file + in-UI list (`securely_log.txt` or equivalent)
- [ ] Instant analysis view (screenshot + explanation)
- [ ] Threat education database / window (phishing, malware, ransomware, etc.)
- [ ] Training screenshot capture path (feature exists; default off — keep as optional/advanced)

### Product / backend
- [ ] Server-side analyze API pattern (Supabase Edge / Vercel) — keys never in client
- [ ] Auth/license awareness (`401` / `402`) without breaking offline Test Mode
- [ ] Do **not** port LockIn chat, “Ask me anything”, lock-in message rotation, or TaskFlow naming

---

## UI requirements (Hooxie copy)

### Architecture
Mirror Hooxie, not CustomTkinter or the old WPF island:

1. **Borderless topmost host** (WinForms or equivalent) + **WebView2**
2. Transparent WebView background; glass = semi-transparent `#shell` over desktop
3. **No `backdrop-filter` blur** on the widget — opacity wash only (Hooxie rule)
4. Window region: **pill (`border-radius: 999`)** when compact/short; **~22px** when expanded
5. Fit/resize protocol similar to Hooxie `fit` / shell shape sync

### Visual system (port from `public/app.css`)
- Tokens: `--glass`, `--accent`, `--text`, `--muted`, `--fill`, `--fill-hover`, `--line`, `--ink`, `--button`, `--button-ink`
- Font: Segoe UI Variable Text / Segoe UI stack (widget); Manrope only if cloning dashboard
- Dark default glass `rgba(0,0,0,0.5)`; light mode via `data-widget="light"`
- Circles ~30×30, hover scale 1.1 / active 0.94, cubic-bezier `(0.2, 0.8, 0.2, 1)`
- Panel enter: ~280ms fade + slight translateY
- Optional color swatches + opacity slider like Hooxie Look

### Chrome mapping (Securely content in Hooxie layout)

Adapt Hooxie’s `#shell` hierarchy — same structure, Securely jobs:

| Hooxie piece | Securely equivalent |
|--------------|---------------------|
| Toolbar / prompt row | Compact status + primary actions (Quick Scan / Stop / status text) |
| Tool circles | Home/Audit, Settings, Hitboxes toggle, Drag, Exit |
| Chat band | Threat event stream / audit snippets (bubbles or reply rows) |
| More menu | Scan modes, duration, Test Mode, Exit |
| Usage panel | API/license or scan status (optional) |
| Dashboard window | Full Settings + Audit Log + Education (Hooxie dash style OK) |
| Stealth/undetectable ring | Optional “hide from capture” if you implement it; otherwise omit — don’t fake it |
| Setup flow | First-run: OCR/Tesseract check, consent, API/license, hotkey tip |

**Collapsed state:** capsule status pill (Securely status + minimal controls).  
**Expanded state:** scan controls, countdown, threat list, settings drawers.

Brand the product **Securely** everywhere (title, icons, strings). Keep Securely logo assets from the Securely tree where useful.

---

## Optimization goals (why rewrite)

1. Split monolith: `core` (capture/OCR/analyze/audit) vs `ui` (WebView) vs `host` (shell)
2. No hardcoded API keys — env + server proxy only
3. Debounce / cache / cheaper local prefilter before LLM
4. Persist settings (JSON) — C# port largely didn’t
5. Single codebase (don’t leave 3 diverging Securely.py copies)
6. Rename away from `TaskFlow` / `LockInNigga`
7. Graceful OCR missing state (clear UI, don’t silent-fail)
8. Keep continuous-capture consent + auto-pause as first-class

Suggested stack (align with Hooxie unless Kelly prefers otherwise):
- **Host:** .NET WinForms + WebView2 (like Hooxie)
- **UI:** HTML/CSS/JS ported from Hooxie `public/`
- **Core:** C# library evolved from `SecurelyCore`, or Node bridge if that fits the host — pick one and justify briefly
- **API:** keep Supabase/Vercel analyze path from `Securely Project`

---

## Working process

1. **Inventory pass** — walk Securely + Hooxie files above; note any feature you find that this prompt missed; add it to the checklist before coding.
2. **Plan** — propose folder layout, host/UI/core split, and which Securely behaviors map to which Hooxie panels. Wait for approval if ambiguous.
3. **Scaffold** — empty Securely host + WebView loading a forked `public/` with Securely branding.
4. **Port UI chrome** — match Hooxie glass/pill/circles/menus first (static shell).
5. **Wire core** — monitoring modes, OCR, analyze, pause, hitboxes, audit, notifications.
6. **Settings persistence + hotkey hide**.
7. **Polish** — opacity/look, light/dark, toasts, education, instant analysis.
8. **Verify** against the feature checklist; call out anything still missing.

### Rules
- Prefer reading real files over assumptions — both trees exist on disk.
- When unsure about a Securely behavior, open `Securely.py` / `ScreenMonitor.cs` and match it.
- When unsure about UI, open Hooxie `app.css` / `index.html` and match it.
- Do not mix Hooxie dashboard tokens into the pill unless building the separate dashboard.
- Do not add purple AI-slop themes, card-heavy dashboards in the pill, or backdrop blur “glass”.
- Ask before deleting old Securely trees; build the new app in a clear new folder (e.g. `E:\MasterVault\Securely\securely-app\`) unless Kelly says overwrite.

---

## Definition of done

- [ ] New app runs as always-on-top Hooxie-like pill on Windows
- [ ] Quick / Timed / 24/7 scans work end-to-end with OCR + AI path
- [ ] Auto-pause, hitboxes, audit log, notifications, education, settings all present
- [ ] Visual chrome recognizably Hooxie (tokens, radii, circles, expand/collapse)
- [ ] No client-side hardcoded LLM keys
- [ ] Feature checklist above fully checked or explicitly waived by Kelly

Start by confirming the inventory (any missed features) and proposing the folder/tech layout, then scaffold the Hooxie-style shell.

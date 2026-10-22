# Feature checklist (rewrite)

Mark `[x]` only when working end-to-end in `securely-app`.

## Monitoring
- [ ] Quick Scan
- [ ] Timed scan (1m–1h; presets 5/15/30/60)
- [ ] 24/7 continuous + consent gate
- [ ] Primary monitor only
- [ ] Optional window target (HWND on primary) — advanced

## Pipeline
- [ ] Screenshot (GDI)
- [ ] Mask tray region (~bottom-right 15%×25%)
- [ ] OCR (Tesseract) + Securely/IDE noise filters
- [ ] LLM via `SECURELY_API_URL` (+ optional JWT); no client Groq keys
- [ ] Heuristics: URLs/domains, login/payment, soft-ignore dev
- [ ] Classes: Safe / Suspicious / Malicious / Unsure + LEGITIMATE_LOGIN / LEGITIMATE_PAYMENT
- [ ] Analysis cache / debounce
- [ ] Multi-key / rate-limit on **server**

## Safety UX
- [ ] Auto-pause ~180s on legitimate login/payment (skip Quick Scan)
- [ ] Consent before continuous
- [ ] Disclosure that screen content is analyzed
- [ ] Credential pre-flight before send (from Securely Project)

## Overlays & alerts
- [ ] Hitboxes (click-through topmost)
- [ ] Desktop toasts + optional sound
- [ ] Threat cooldown
- [ ] Test notification

## Modes / settings
- [ ] Hitboxes on/off
- [ ] Strict / keyword local scan
- [ ] Test Mode
- [ ] Notifications / sound
- [ ] Timed duration
- [ ] Widget opacity (`--glass`)
- [ ] Hide/show **Ctrl+\**
- [ ] Persist settings (JSON) — **new**

## Analysis & education
- [ ] Audit log + in-UI list
- [ ] Instant analysis view
- [ ] Threat education
- [ ] Training screenshot path (default off)

## Product / backend
- [ ] Server analyze API pattern
- [ ] Auth/license 401 / 402 (offline Test Mode still works)
- [x] No LockIn chat / TaskFlow branding in new app

## Shell (scaffold)
- [x] Borderless topmost WebView2 host
- [x] Glass pill / expand (no backdrop-filter)
- [x] Securely-mapped toolbar + threat stream chrome
- [x] Look opacity / swatches stub
- [x] First-run setup disclosure stub

## Missed features found in inventory (track)
- [ ] Console log viewer
- [ ] Credits / Guide / Store links (optional)
- [ ] Threat categorization labels for notifications
- [ ] API usage stats (optional; server-side preferred)

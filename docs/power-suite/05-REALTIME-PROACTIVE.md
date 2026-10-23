# Real-time + proactive — Securely-unique core

## Thesis

Disk AV and VPN are table stakes. Securely’s durable advantage is **screen-time security with privacy**: see phishing as the user sees it, gate sensitive text locally, then act.

## Existing foundation

| Piece | Location | Status |
|-------|----------|--------|
| Quick Scan capture + OCR | `securely-app/host` | Shipping |
| Local sensitive gate | `ui/public/sensitive.js` | Shipping (broad kinds) |
| AI classify | `Securely-Website/api/analyze.js` | Shipping |
| Modes (Quick / Timed / 24·7) | Pill + plan docs | Partial vs checklist |
| Audit / hitboxes | Planned in FEATURE_CHECKLIST | Incomplete |

## Deepen the wedge

### 1. Continuous monitoring with consent

- First-run + each enable of 24·7: plain disclosure (“Securely reads text from your primary monitor”)  
- Auto-pause on `LEGITIMATE_LOGIN` / `LEGITIMATE_PAYMENT` (~180s) — already in product dialect  
- Cooldown to cut toast spam  

### 2. Sensitive gate maturity

- Tunable kinds (user can disable “email” noise)  
- False-positive report → soften rules in updates  
- Reuse gate for Analyze file uploads and VPN “secure input” moments  

### 3. Proactive actions (not just labels)

| Signal | Action |
|--------|--------|
| Phishing / suspicious URL on screen | Highlight hitbox + “Open in Analyze” |
| New EXE in Downloads | Toast → Analyze / Quarantine |
| Clipboard URL while pill focused | Optional Analyze |
| Bank/login OCR + VPN off | Soft suggest connect |
| Malicious Analyze verdict | One-click quarantine + audit entry |

### 4. Real-time feature matrix

| Channel | Mechanism | Phase |
|---------|-----------|-------|
| Screen | Timed/24·7 OCR loop | Now → harden |
| Files | Download watcher | 1–2 |
| Network | VPN state + later DNS | 2–3 |
| Scripts | AMSI caller | 2 |
| Browser | Optional extension later | Later |

## UX principles (proactive without panic)

1. One primary action per alert  
2. Profiles control noise (Quiet / Balanced / Paranoid)  
3. Failed AI ≠ Safe (existing threat-model rule)  
4. Local heuristics can mark Suspicious before cloud returns  

## Cross-feature policy engine (light)

Store JSON policies in existing settings:

```json
{
  "profile": "balanced",
  "onPhishing": ["hitbox", "toast", "audit"],
  "onNewExe": ["analyzePrompt"],
  "onLoginScreen": ["pauseAiUpload", "suggestVpn"]
}
```

Host evaluates policies; UI only renders.

## Metrics of “feels powerful”

- Time from threat-on-screen → visible warning  
- % scans blocked by sensitive gate (privacy win)  
- Analyze completion rate from download toasts  
- False-positive dismiss rate (drive Quiet defaults)

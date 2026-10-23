# REA — bounded use policy for Securely

## What REA is

[REA](https://rea.tools/) ([`morluto/rea`](https://github.com/morluto/rea)) gives a coding agent tools to **inspect → explain → rebuild** software: native binaries, JS/Electron apps, and browser/runtime targets. Teaching demos on rea.tools (Calculator %, dinosaur speed) show the workflow: recover a rule from real code, then reimplement and test it.

[`morluto/awesome-reverse-engineering`](https://github.com/morluto/awesome-reverse-engineering) is a **learning index** (tools, formats, protocols) — use it for literacy, not as a license to attack closed vendors.

## Workflow summary (agent-assisted RE)

1. Ask about **one feature** of an allowed target  
2. Inspect with REA (code, references, runtime observations)  
3. Explain the rule; optionally rebuild a small test harness  
4. Apply lessons to **Securely’s own** design — never ship competitor code  

## Allowed targets (this project)

| Allowed | Examples |
|---------|----------|
| Securely binaries / UI | `SecurelyShell.exe`, `ui/public`, installer payload |
| Open-source AV/VPN demos | ClamAV, wireguard-windows samples, YARA test corpora |
| Explicit teaching targets | rea.tools Calculator / dinosaur labs, Microsoft-published open samples |
| Lab malware samples | Isolated VM only, legal sample sources, never on production hosts |

## Forbidden targets

| Forbidden | Why |
|-----------|-----|
| Norton, Bitdefender, Malwarebytes, NordVPN, etc. closed apps | Proprietary; ToS; not needed for Securely |
| VirusTotal / vendor update channels | Scraping / DB theft |
| DRM / license bypass of any third-party product | Illegal / disallowed |

If a task seems to need closed-product RE: **stop**, write the *capability goal*, and pick an open equivalent (see competitive map).

## Setup (human approval required)

Do **not** silently install. From [rea.tools](https://rea.tools/):

**Agent prompt to approve:**

> Install REA and connect it to this coding agent using `npx rea-agents@latest setup`. Show me the setup plan for approval, then verify the installation.

**Terminal:**

```powershell
npx rea-agents@latest setup
```

Approve the plan, then restart the agent.

## How we’d use REA to harden Securely (checklist)

- [ ] Trace SecurelyShell capture → OCR → postMessage path; confirm no unexpected network  
- [ ] Inspect sensitive.js / host redaction; fuzz with synthetic OCR fixtures  
- [ ] After Analyze ships: verify file bytes never leave host except via intended API  
- [ ] After VPN ships: inspect our helper’s WFP/kill-switch config (our code), compare behavior to WireGuard public docs  
- [ ] Rebuild a **mini** phishing-hitbox demo from our own rules for regression tests  
- [ ] Never point REA at a commercial AV/VPN installer “to see how they do X”

## Literacy without abuse

Use awesome-RE lists to learn PE, debugging, and protocol analysis skills that improve Securely’s **Analyze** static stage and our own binary QA — always on owned or open artifacts.

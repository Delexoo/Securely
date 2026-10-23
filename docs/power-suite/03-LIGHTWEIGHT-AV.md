# Lightweight antivirus — architecture

## Recommendation (ships quality fastest)

**Securely Protect = Defender companion + Securely signals**, not a second primary AV in v1.

Registering as a full antivirus forces Microsoft Defender into passive/disabled modes on consumer Windows ([compatibility docs](https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-antivirus-compatibility)). A small team cannot out-detect Defender + cloud ML. Competing there early hurts users and marketing honesty.

## Product promise (honest)

> Securely adds on-demand scanning, download watching, Analyze multi-engine lookups, and screen phishing protection — alongside Windows Security, not instead of it.

## Architecture layers

| Layer | v1 | v2 | v3+ |
|-------|----|----|-----|
| On-demand path scan | Yes | Yes | Yes |
| Archive / extension filters | Yes | Yes | Yes |
| Download / Desktop watcher | Yes | Yes | Yes |
| Quarantine folder + restore | Yes | Yes | Yes |
| Exclusions + schedules | Policy toggles | Full | Full |
| Quiet / Balanced / Paranoid | Yes | Yes | Yes |
| AMSI **caller** (scan buffers) | Optional | Yes | Yes |
| AMSI **provider** | No | Research | Maybe |
| Behavior / ETW | No | Light | Yes |
| Mini-filter + Security Center primary | No | No | Partner / major investment |

## On-demand scan

Host worker (C#) walks user-selected roots with:

- Extension allow/deny lists  
- Max file size / max archive depth  
- SHA-256 + local YARA + optional ClamAV IPC  
- Cloud hash lookup via Analyze APIs  
- Progress on pill + dashboard  

## Real-time (realistic for a small team)

**Do first (user-mode):**

1. Watch `%USERPROFILE%\Downloads` (and optional Desktop) with `FileSystemWatcher`  
2. On create/rename → hash → Analyze → toast “Open Analyze” / “Quarantine”  
3. Optional: scan attachments when Outlook/browser drop files (path heuristics)

**Do next:**

4. AMSI scan of PowerShell / script content Securely itself executes or observes  
5. Surface Defender RTP status via WMI / Windows Security deep-links  

**Defer:**

6. Filesystem mini-filter (needs attestation, signing, crash risk)  
7. Full ELAM / early-launch antimalware  

## Profiles (“Securely mode”)

| Profile | Behavior |
|---------|----------|
| Quiet | Downloads watch only; fewer toasts; screen Timed only |
| Balanced | Downloads + on-demand weekly; screen Timed default |
| Paranoid | Downloads + Desktop + Documents watch; prompt every new EXE; screen 24·7 with consent |

## Quarantine

- `%LocalAppData%\Securely\Quarantine\` encrypted container or rename+ACL deny  
- Metadata JSON: original path, hash, verdict, time  
- Restore / delete from dashboard  

## Signatures & updates

| Channel | Content |
|---------|---------|
| App update | YARA pack + sensitive rules |
| Cloud | Hash/URL reputation (Analyze) |
| Optional | ClamAV CVD if user enables |

No stolen vendor signature DBs.

## Coexistence checklist

- [ ] Never claim “disable Defender”  
- [ ] Dashboard tile: “Windows Security: On / Off / Unknown” with Open Settings  
- [ ] If user installs another primary AV, Securely stays companion mode  
- [ ] Document that limited periodic scanning is a Windows feature, not Securely  

## Open projects & docs to build from

- [AMSI](https://learn.microsoft.com/en-us/windows/win32/amsi/antimalware-scan-interface-portal)  
- ClamAV, YARA, pefile-class parsers  
- Microsoft Defender Antivirus scanning configuration (public)  

## Phase flags

Anything needing **kernel signing / HVCI / attestation** = **phase 3+**.

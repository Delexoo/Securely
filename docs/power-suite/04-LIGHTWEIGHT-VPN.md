# Lightweight VPN — architecture

## Goal

NordVPN-*class UX* (one-tap connect, kill switch, split tunnel, profiles) on **open WireGuard**, with **honest** trust and no-logs claims.

## Protocol choice

| Option | Verdict |
|--------|---------|
| **WireGuard** | Prefer — small codebase, fast, well documented |
| OpenVPN | Fallback for restrictive networks (later) |
| Proprietary clones of NordLynx | Don’t rebrand; implement WireGuard + optional double-NAT research later |

## Client architecture (Windows)

```
Dashboard VPN tab / pill quick-toggle
        │
        ▼
SecurelyShell host service (elevated helper)
        │
        ▼
wireguard-nt / embeddable tunnel (or official tunnel service)
        │
        ▼
WFP kill-switch when AllowedIPs = /0
```

Study (do not copy branding): official [wireguard-windows netquirk](https://git.zx2c4.com/wireguard-windows/about/docs/netquirk.md) — kill switch is WFP when peer has literal `/0` AllowedIPs; split default via `0.0.0.0/1` + `128.0.0.0/1` avoids kill-switch semantics.

## Feature set

| Feature | v1 client | Notes |
|---------|-----------|-------|
| Connect / disconnect | Yes | Profile list |
| Server / region list | Yes | From partner API or self-host inventory |
| Kill switch | Yes | System-level via WFP |
| Split tunnel (IP) | Yes | AllowedIPs editor + presets |
| Split tunnel (per-app) | Later | Harder on Windows; WFP app-ID rules |
| Always-On / reconnect | Yes | Service watchdog |
| Obfuscation / Double VPN | Later | After basic quality |
| DNS leak protection | Yes | Tunnel DNS + WFP DNS restrict pattern |

## Trust model (who runs servers)

| Model | Pros | Cons | Recommendation |
|-------|------|------|----------------|
| **Partner white-label** | Fast PoP coverage, ops handled | Cost share; depend on partner audit | **Best for v1.0 launch** |
| Self-host small fleet | Full control | Jurisdiction, abuse, uptime, export crypto | Lab / power users first |
| BYO WireGuard config | Honest power-user mode | No “Securely VPN network” marketing | Ship early as Advanced |

**Honest marketing rule:** never say “audited no-logs” until a real audit exists for the operator of the servers Securely connects to.

## UI integration

- Dashboard **VPN** page: map/list, latency, connect, kill switch toggle, split presets (Full / Split LAN / Custom)  
- Pill: small shield glyph or status color when tunnel up  
- Cross-feature policy ideas: “bank domain detected on screen → suggest VPN on” / “VPN off for local printer CIDR”

## Compliance notes

- VPN / crypto export: review US EAR and distribution of WireGuard binaries in installer  
- Jurisdiction of exit nodes must match claims  
- Abuse: exit-node ToS, port restrictions, DMCA contacts if self-hosting  

## Phased delivery

1. **BYO config** import (`.conf`) + connect/disconnect + kill switch  
2. Partner API server list + Securely account entitlement  
3. Split presets + Always-On  
4. Per-app rules / obfuscation  

## Non-goals early

Meshnet clones, dedicated IP marketplace, streaming-optimizer branding wars.

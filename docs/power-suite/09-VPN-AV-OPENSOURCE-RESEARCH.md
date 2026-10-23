# VPN & Antivirus — open-source research notes (Securely)

Research date: 2026-10-22. Used to shape Securely’s companion VPN + Protect channels.

## VPN — what real projects teach

| Project | License / role | Takeaway for Securely |
|---------|----------------|------------------------|
| [OpenVPN](https://github.com/OpenVPN/openvpn) | GPL-2 daemon | Keep as **fallback** for restrictive networks; WireGuard first for UX speed |
| [WireGuard Windows](https://git.zx2c4.com/wireguard-windows/) | Official client | Drive tunnels via `wireguard /installtunnelservice` + `WireGuardTunnel$name` |
| [Algo](https://github.com/trailofbits/algo) | Personal cloud VPN | Best **BYO** story: user deploys, pastes `.conf` into Securely |
| [PiVPN](https://github.com/pivpn/pivpn) | Home Pi WireGuard/OpenVPN | Same BYO path — home exit = real geo change |
| [hwdsl2/setup-ipsec-vpn](https://github.com/hwdsl2/setup-ipsec-vpn) + [docker-ipsec](https://github.com/hwdsl2/docker-ipsec-vpn-server) | IPsec/IKEv2 | Later Windows built-in VPN profile import |
| [Firezone](https://github.com/firezone/firezone) | WireGuard + identity | Enterprise pattern: policy + device trust — not v1 consumer |
| [Netmaker](https://github.com/gravitl/netmaker) | WireGuard mesh | Meshnet later; don’t fake “Securely network” without PoPs |
| [SoftEther](https://github.com/SoftEtherVPN/SoftEtherVPN) | Multi-protocol | Too heavy for embed; study UI patterns only |
| [Amnezia](https://github.com/amnezia-vpn/amnezia-client) | Self-host client | Gold standard UX: SSH deploy + obfuscation — long-term aspiration |

### Securely VPN v1 (shipped shape)

1. **Nord-class map UI** — IP overlay, city/secured state, pins, recents  
2. **Live IP/geo** via `/api/ip-geo` (ipify + ip-api) before/after connect  
3. **Real tunnel** — BYO WireGuard `.conf` through host `VpnTunnel`  
4. **Honest marketing** — location spoof works only when the user’s exit node is elsewhere; no fake fleet  

## Antivirus — what to use (and what to ignore)

### Legitimate open engines / patterns

| Project | Use |
|---------|-----|
| Windows Defender `MpCmdRun` | Primary on-demand engine on Windows |
| [ClamAV](https://github.com/Cisco-Talos/clamav) / gitavscan Action | Optional later CVD; CI scan pattern |
| [KicomAV](https://github.com/hanul93/kicomav) | Signature + disinfectant architecture study |
| [Jackal / static-malware-detector](https://github.com/Kayetan17/static-malware-detector) | PE ML + YARA static scan UX |
| VirusTotal / URLhaus APIs | Already in Analyze |

### Avoid

GitHub “Free Norton / AVG unlocked / lifetime license” repos under `free-antivirus-windows` and similar topics are **crackware / malware bait**. Securely must never ship or link those.

### Securely Protect v1

- Companion to Defender (never displace)  
- Host file pick + `MpCmdRun -Scan -ScanType 3`  
- SHA-256 → Analyze cloud reputation  
- Quiet / Balanced / Paranoid + Downloads watch  

## Structure summary

```
Dashboard VPN  →  host vpn connect/disconnect  →  WireGuard tunnel service
Dashboard AV   →  host av-scan pick/scan       →  MpCmdRun + hash → Analyze API
Map / IP       →  /api/ip-geo                  →  public IP + city
```

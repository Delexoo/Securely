<p align="center">
  <img src="Securely-Website/apple-touch-icon.png" width="96" height="96" alt="Securely">
</p>

<h1 align="center">Securely</h1>

<p align="center">
  <strong>AI-assisted screen threat monitoring for Windows</strong><br>
  Catch phishing and scam UI on the primary display before you click.
</p>

<p align="center">
  <a href="https://trysecurely.vercel.app"><img src="https://img.shields.io/badge/Website-trysecurely-1d4ed8?style=for-the-badge" alt="Website"></a>
  <a href="https://github.com/Delexoo/Securely/releases/latest"><img src="https://img.shields.io/github/v/release/Delexoo/Securely?style=for-the-badge&label=Latest%20release" alt="Latest release"></a>
  <a href="https://trysecurely.vercel.app/download/Securely-Setup.exe"><img src="https://img.shields.io/badge/Download-Windows-111827?style=for-the-badge&logo=windows&logoColor=white" alt="Download"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Securely-0f172a?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="https://trysecurely.vercel.app/#download">Download</a> ·
  <a href="https://trysecurely.vercel.app/pricing.html">Pricing</a> ·
  <a href="https://trysecurely.vercel.app/releases.html">Release notes</a> ·
  <a href="https://github.com/Delexoo/Securely/releases">GitHub Releases</a>
</p>

---

## What it is

Securely is a Windows desktop overlay that:

- Captures the **primary monitor**
- Runs **Windows OCR**
- Classifies risk through Securely’s **server-side analyze API** (OpenRouter)
- Shows **Idle / Scanning / Safe / Warning / Phishing** on a compact glass pill
- Unlocks with a **$3/month Stripe subscription** (activate by email — no Securely account)

It is a decision aid for phishing and scam UI — not a full antivirus replacement.

## Download

Always get the latest Windows installer from the site:

**[Download Securely for Windows](https://trysecurely.vercel.app/download/Securely-Setup.exe)**

Or open the [latest GitHub Release](https://github.com/Delexoo/Securely/releases/latest).

Promo for testing: enter `SECURELY-DEV` at checkout for 100% off (when configured).

## Product map

| Area | Path |
|------|------|
| WinForms + WebView2 host | `securely-app/host/` |
| Pill + dashboard UI | `securely-app/ui/public/` |
| Marketing site + APIs | `Securely-Website/` |
| Installer (Inno Setup) | `installer/` |
| Release notes source | `brain/log.json` |

## Develop

```bash
# Host (Windows)
dotnet run --project securely-app/host/SecurelyShell.csproj

# Release notes from brain/log.json
npm run notes

# Installer license RTF + Setup.exe (requires Inno Setup 6)
npm run license:rtf
npm run build:installer
```

Copy `.env.example` → `.env` and fill **Securely-only** secrets (Stripe, OpenRouter, GitHub, Vercel). Never commit `.env`.

## License

See [LICENSE](LICENSE) — the Securely License Agreement shown in the Windows installer.

## Support

- Email: [support@trysecurely.com](mailto:support@trysecurely.com)
- Site: [trysecurely.vercel.app](https://trysecurely.vercel.app)

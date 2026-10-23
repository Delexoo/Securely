/**
 * Public IP + coarse geolocation for the Securely VPN dashboard.
 * Uses free endpoints — no Securely VPN server fleet required.
 */
module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Cache-Control", "no-store");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "GET") return res.status(405).json({ error: "GET only" });

  try {
    const ipRes = await fetch("https://api.ipify.org?format=json", {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(8000),
    });
    const ipJson = await ipRes.json().catch(() => ({}));
    const ip = String(ipJson.ip || "").trim();
    if (!ip) return res.status(502).json({ error: "Could not resolve public IP." });

    // ip-api.com free tier — http only on free plan
    const geoRes = await fetch(
      `http://ip-api.com/json/${encodeURIComponent(ip)}?fields=status,message,country,countryCode,regionName,city,lat,lon,isp,query,timezone`,
      { signal: AbortSignal.timeout(8000) },
    );
    const geo = await geoRes.json().catch(() => ({}));
    if (geo.status !== "success") {
      return res.status(200).json({
        ok: true,
        ip,
        city: "",
        region: "",
        country: "",
        countryCode: "",
        lat: null,
        lon: null,
        isp: "",
        label: ip,
      });
    }

    const city = geo.city || "";
    const region = geo.regionName || "";
    const country = geo.country || "";
    const label = [city, country].filter(Boolean).join(", ") || ip;

    return res.status(200).json({
      ok: true,
      ip: geo.query || ip,
      city,
      region,
      country,
      countryCode: geo.countryCode || "",
      lat: typeof geo.lat === "number" ? geo.lat : null,
      lon: typeof geo.lon === "number" ? geo.lon : null,
      isp: geo.isp || "",
      timezone: geo.timezone || "",
      label,
    });
  } catch (err) {
    return res.status(502).json({ error: err.message || "IP lookup failed." });
  }
};

/** Redirect to the latest Securely Windows installer (website copy, then GitHub Release asset). */
export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.status(405).json({ error: "Method not allowed." });
    return;
  }

  // Prefer the static file shipped with the site (updated on each release).
  const host = req.headers["x-forwarded-host"] || req.headers.host;
  const proto = req.headers["x-forwarded-proto"] || "https";
  const siteFile = `${proto}://${host}/download/Securely-Setup.exe`;

  try {
    const head = await fetch(siteFile, { method: "HEAD", redirect: "manual" });
    if (head.ok) {
      res.status(302).setHeader("Location", siteFile);
      res.end();
      return;
    }
  } catch {
    /* fall through to GitHub */
  }

  const owner = process.env.GITHUB_OWNER || "Delexoo";
  const repo = process.env.GITHUB_REPO || "Securely";
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || "";
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": "Securely-Website",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/releases/latest`, {
      headers,
    });
    if (!response.ok) {
      res.status(502).json({ error: "Could not look up the latest Securely release." });
      return;
    }
    const release = await response.json();
    const assets = Array.isArray(release.assets) ? release.assets : [];
    const asset =
      assets.find((a) => /^Securely-Setup/i.test(a.name) && /\.exe$/i.test(a.name)) ||
      assets.find((a) => /\.exe$/i.test(a.name));
    if (asset?.browser_download_url) {
      res.status(302).setHeader("Location", asset.browser_download_url);
      res.end();
      return;
    }
    if (release.html_url) {
      res.status(302).setHeader("Location", release.html_url);
      res.end();
      return;
    }
  } catch {
    /* ignore */
  }

  res.status(404).json({
    error: "No Securely installer is published yet. Check GitHub Releases.",
    releases: `https://github.com/${owner}/${repo}/releases`,
  });
}

/**
 * Publish GitHub Releases from brain/releases.json.
 *
 * Usage:
 *   node scripts/publish-github-release.mjs
 *   node scripts/publish-github-release.mjs --all
 *   node scripts/publish-github-release.mjs --version 0.1.0
 *
 * Auth: GITHUB_TOKEN or GH_TOKEN. Loaded from .env when present. Never prints the token.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
loadEnv(path.join(root, ".env"));

const log = JSON.parse(fs.readFileSync(path.join(root, "brain", "log.json"), "utf8"));
const [defaultOwner, defaultRepo] = String(log.repo || "Delexoo/Securely").split("/");
const OWNER = process.env.GITHUB_OWNER || defaultOwner || "Delexoo";
const REPO = process.env.GITHUB_REPO || defaultRepo || "Securely";
const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;

if (!token) {
  console.error("Missing GITHUB_TOKEN / GH_TOKEN — cannot publish GitHub Releases.");
  process.exit(1);
}

const releasesDoc = JSON.parse(fs.readFileSync(path.join(root, "brain", "releases.json"), "utf8"));
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));

const args = process.argv.slice(2);
const all = args.includes("--all");
const versionArgIdx = args.indexOf("--version");
const onlyVersion = versionArgIdx >= 0 ? args[versionArgIdx + 1] : all ? null : pkg.version;

const targets = (releasesDoc.updates || []).filter((u) =>
  onlyVersion ? u.version === onlyVersion : true,
);

if (!targets.length) {
  console.error(
    onlyVersion
      ? `No brain release notes for version ${onlyVersion}.`
      : "brain/releases.json has no updates.",
  );
  process.exit(1);
}

const results = [];
for (const update of targets) {
  results.push(await publishOne(update));
}

console.log(
  JSON.stringify(
    {
      repo: `${OWNER}/${REPO}`,
      published: results.filter((r) => r.action === "created").map((r) => r.tag),
      existed: results.filter((r) => r.action === "exists").map((r) => r.tag),
      updated: results.filter((r) => r.action === "updated").map((r) => r.tag),
      failed: results.filter((r) => r.action === "error"),
    },
    null,
    2,
  ),
);
if (results.some((r) => r.action === "error")) process.exit(1);

async function publishOne(update) {
  const tag = update.tag || `v${update.version}`;
  const name = `${releasesDoc.product || "Securely"} ${update.version}: ${update.title}`;
  const body = formatReleaseBody(update);
  const targetCommitish = resolveTarget(process.env.GITHUB_RELEASE_TARGET || "main");

  const existing = await api("GET", `/repos/${OWNER}/${REPO}/releases/tags/${tag}`);
  if (existing.ok) {
    const release = await existing.json();
    const patch = await api("PATCH", `/repos/${OWNER}/${REPO}/releases/${release.id}`, {
      name,
      body,
      draft: false,
      prerelease: false,
    });
    if (!patch.ok) {
      const text = await patch.text();
      return { tag, action: "error", status: patch.status, detail: text.slice(0, 200) };
    }
    await uploadInstallerAssets(release);
    return { tag, action: "updated", url: release.html_url };
  }

  if (existing.status !== 404) {
    const text = await existing.text();
    return { tag, action: "error", status: existing.status, detail: text.slice(0, 200) };
  }

  const created = await api("POST", `/repos/${OWNER}/${REPO}/releases`, {
    tag_name: tag,
    target_commitish: targetCommitish,
    name,
    body,
    draft: false,
    prerelease: false,
    generate_release_notes: false,
  });
  if (!created.ok) {
    const text = await created.text();
    return { tag, action: "error", status: created.status, detail: text.slice(0, 300) };
  }
  const release = await created.json();
  await uploadInstallerAssets(release);
  return { tag, action: "created", url: release.html_url };
}

async function uploadInstallerAssets(release) {
  const version = String(release.tag_name || "").replace(/^v/, "");
  const candidates = [
    path.join(root, "dist-setup", `Securely-Setup-${version}.exe`),
    path.join(root, "dist-setup", "Securely-Setup.exe"),
    path.join(root, "Securely-Website", "download", "Securely-Setup.exe"),
  ];
  const file = candidates.find((p) => fs.existsSync(p));
  if (!file || !release.upload_url) return;
  const name = path.basename(file).startsWith("Securely-Setup")
    ? path.basename(file)
    : `Securely-Setup-${version}.exe`;
  const bytes = fs.readFileSync(file);
  const uploadUrl = String(release.upload_url).replace(/\{.*\}$/, `?name=${encodeURIComponent(name)}`);
  // Replace existing asset with same name when updating a release.
  const assets = Array.isArray(release.assets) ? release.assets : [];
  for (const asset of assets) {
    if (asset.name === name || asset.name === "Securely-Setup.exe") {
      await api("DELETE", `/repos/${OWNER}/${REPO}/releases/assets/${asset.id}`);
    }
  }
  const put = await fetch(uploadUrl, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/octet-stream",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "securely-release-bot",
    },
    body: bytes,
  });
  if (!put.ok) {
    const text = await put.text();
    console.error(`Asset upload failed for ${name}: ${put.status} ${text.slice(0, 180)}`);
  }
}

function formatReleaseBody(update) {
  const lines = [`## ${update.title}`, "", `_Shipped ${update.date}_`, ""];
  for (const section of update.sections || []) {
    lines.push(`### ${section.heading}`, "");
    if (section.added?.length) {
      lines.push("**Added**");
      for (const note of section.added) lines.push(`- ${note}`);
      lines.push("");
    }
    if (section.fixes?.length) {
      lines.push("**Fixes**");
      for (const note of section.fixes) lines.push(`- ${note}`);
      lines.push("");
    }
  }
  lines.push("---", "", "_Notes from `brain/log.json` via Securely release tooling._", "");
  return lines.join("\n");
}

async function api(method, apiPath, body) {
  return fetch(`https://api.github.com${apiPath}`, {
    method,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "securely-release-bot",
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

function resolveTarget(ref) {
  if (!ref || ref === "master" || ref === "main") return ref;
  try {
    return execSync(`git rev-parse ${ref}`, {
      cwd: root,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return ref;
  }
}

function loadEnv(file) {
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    if (!line || line.trim().startsWith("#")) continue;
    const i = line.indexOf("=");
    if (i < 0) continue;
    const k = line.slice(0, i).trim();
    let v = line.slice(i + 1).trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1);
    }
    if (!(k in process.env)) process.env[k] = v;
  }
}

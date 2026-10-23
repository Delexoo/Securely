/**
 * Stage SecurelyShell + UI, build Inno Setup, copy Securely-Setup.exe to the website download folder.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const version = pkg.version;
const dist = path.join(root, "dist-setup");
const stage = path.join(dist, "stage");
const hostProj = path.join(root, "securely-app", "host", "SecurelyShell.csproj");
const uiPublic = path.join(root, "securely-app", "ui", "public");
const iscc =
  process.env.ISCC_PATH ||
  "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe";

fs.rmSync(stage, { recursive: true, force: true });
fs.mkdirSync(stage, { recursive: true });

console.log("Building SecurelyShell (Release)…");
execSync(`dotnet publish "${hostProj}" -c Release -o "${path.join(stage, "bin")}" --self-contained false`, {
  stdio: "inherit",
});

// Flatten: Inno expects SecurelyShell.exe at app root; also ship UI next to it for ResolveUiPublic candidates.
const binDir = path.join(stage, "bin");
for (const name of fs.readdirSync(binDir)) {
  fs.renameSync(path.join(binDir, name), path.join(stage, name));
}
fs.rmSync(binDir, { recursive: true, force: true });

const uiDest = path.join(stage, "ui", "public");
fs.cpSync(uiPublic, uiDest, { recursive: true });

const iss = path.join(root, "installer", "securely.iss");
if (!fs.existsSync(iscc)) {
  console.error("Inno Setup ISCC.exe not found. Install Inno Setup 6 or set ISCC_PATH.");
  process.exit(1);
}

console.log(`Building installer ${version}…`);
execSync(`"${iscc}" "/DMyAppVersion=${version}" "${iss}"`, { stdio: "inherit" });

const versioned = path.join(dist, `Securely-Setup-${version}.exe`);
const latestName = "Securely-Setup.exe";
const websiteDownload = path.join(root, "Securely-Website", "download");
fs.mkdirSync(websiteDownload, { recursive: true });
const websiteLatest = path.join(websiteDownload, latestName);
fs.copyFileSync(versioned, websiteLatest);
fs.copyFileSync(versioned, path.join(dist, latestName));
console.log(`Wrote ${versioned}`);
console.log(`Copied ${websiteLatest}`);

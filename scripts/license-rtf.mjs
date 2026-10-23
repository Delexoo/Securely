import fs from "node:fs";

const source = fs.readFileSync(new URL("../LICENSE", import.meta.url), "utf8").replace(/\r\n/g, "\n");
const lines = source.split("\n");
const parts = [
  "{\\rtf1\\ansi\\ansicpg1252\\deff0",
  "{\\fonttbl{\\f0\\fswiss\\fcharset0 Segoe UI;}}",
  "\\viewkind4\\uc1\\pard\\f0\\fs22\\sa200\\sl276\\slmult1",
];

lines.forEach((line, index) => {
  if (!line.trim()) return;
  if (index === 0) {
    parts.push(`\\pard\\qc\\sb120\\sa80\\b\\fs36 ${escapeRtf(line)}\\b0\\par`);
    return;
  }
  if (/^(Effective date|Version):/.test(line)) {
    parts.push(`\\pard\\qc\\sa40\\fs18 ${escapeRtf(line)}\\par`);
    return;
  }
  if (isHeading(line)) {
    parts.push(`\\pard\\sb360\\sa80\\b\\fs26 ${escapeRtf(line)}\\b0\\par`);
    return;
  }
  if (line.startsWith("- ")) {
    parts.push(`\\pard\\li420\\fi-220\\sa80\\fs22 ${escapeRtf(line)}\\par`);
    return;
  }
  const strong = /^(READ THIS|BY INSTALLING|CLASS WAIVER)/.test(line);
  const numbered = line.match(/^(\d+\.\d+)\s+/);
  const body = numbered
    ? `\\b ${escapeRtf(numbered[1])}\\b0{} ${escapeRtf(line.slice(numbered[0].length))}`
    : escapeRtf(line);
  const weight = strong ? "\\b " : "";
  const end = strong ? "\\b0" : "";
  parts.push(`\\pard\\sa200\\fs22 ${weight}${body}${end}\\par`);
});

parts.push("}");
fs.mkdirSync(new URL("../installer", import.meta.url), { recursive: true });
fs.writeFileSync(new URL("../installer/license.rtf", import.meta.url), parts.join("\n"));
console.log("Wrote installer/license.rtf");

function isHeading(line) {
  if (line === "READING AID") return true;
  return /^\d+\.\s+[A-Z0-9][A-Z0-9 ,'/&\-]*$/.test(line);
}

function escapeRtf(text) {
  let out = "";
  for (const ch of text) {
    const code = ch.codePointAt(0);
    if (ch === "\\") out += "\\\\";
    else if (ch === "{") out += "\\{";
    else if (ch === "}") out += "\\}";
    else if (code < 128) out += ch;
    else out += `\\u${code > 32767 ? code - 65536 : code}?`;
  }
  return out;
}

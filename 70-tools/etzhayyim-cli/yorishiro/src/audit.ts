// audit.ts — Charter compliance audit across every yorishiro lexicon.
//
// Scans 00-contracts/lexicons/ai/etzhayyim/yorishiro/**/*.json and reports:
//   - missing x-yorishiro-external (must be true)
//   - missing x-yorishiro-kami / x-yorishiro-transport
//   - missing or invalid x-charter-purpose values
//   - presence of forbidden purposes (subscription / purchase / tip / internal-*)
//
// Exit code:
//   0 — all yorishiri compliant
//   1 — at least one violation, details printed to stderr

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import { FORBIDDEN_EXTERNAL_PURPOSES, VALID_EXTERNAL_PURPOSES } from "./purpose.js";

export interface AuditFinding {
  file: string;
  nsid: string;
  reason: string;
}

export function audit(repoRoot: string): AuditFinding[] {
  const root = join(repoRoot, "00-contracts/lexicons/ai/etzhayyim/yorishiro");
  if (!safeIsDir(root)) return [];
  const findings: AuditFinding[] = [];
  for (const file of walk(root)) {
    if (!file.endsWith(".json")) continue;
    let lex: any;
    try {
      lex = JSON.parse(readFileSync(file, "utf-8"));
    } catch (err) {
      findings.push({ file, nsid: "<unparseable>", reason: `json-parse: ${(err as Error).message}` });
      continue;
    }
    const nsid: string = lex.id ?? "<missing>";
    const main = lex?.defs?.main;
    if (!main || typeof main !== "object") {
      findings.push({ file, nsid, reason: "missing defs.main" });
      continue;
    }
    if (main["x-yorishiro-external"] !== true) {
      findings.push({ file, nsid, reason: "x-yorishiro-external must be true" });
    }
    if (typeof main["x-yorishiro-kami"] !== "string" || !main["x-yorishiro-kami"]) {
      findings.push({ file, nsid, reason: "x-yorishiro-kami missing" });
    }
    if (typeof main["x-yorishiro-transport"] !== "string" || !main["x-yorishiro-transport"]) {
      findings.push({ file, nsid, reason: "x-yorishiro-transport missing" });
    }
    const purposes = main["x-charter-purpose"];
    if (!Array.isArray(purposes) || purposes.length === 0) {
      findings.push({ file, nsid, reason: "x-charter-purpose missing or empty" });
    } else {
      for (const p of purposes) {
        if ((FORBIDDEN_EXTERNAL_PURPOSES as readonly string[]).includes(p)) {
          findings.push({ file, nsid, reason: `x-charter-purpose includes forbidden value: ${p}` });
        } else if (!(VALID_EXTERNAL_PURPOSES as readonly string[]).includes(p)) {
          findings.push({ file, nsid, reason: `x-charter-purpose includes unknown value: ${p}` });
        }
      }
    }
  }
  return findings;
}

function safeIsDir(p: string): boolean {
  try {
    return statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function walk(root: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(root)) {
    const full = join(root, name);
    const st = statSync(full);
    if (st.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

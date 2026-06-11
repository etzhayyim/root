#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const LEXICON_ROOTS = ["00-contracts/lexicons", "projects", "packages"].filter((dir) =>
  existsSync(path.join(ROOT, dir)),
);
const REGISTRATION_ROOTS = ["projects", "packages", "infra"]
  .filter((dir) => existsSync(path.join(ROOT, dir)));

function runRg(args, options = {}) {
  try {
    return execFileSync("rg", args, { cwd: ROOT, encoding: "utf8", ...options }).trim();
  } catch (error) {
    if (error?.status === 1) return "";
    const stderr = String(error?.stderr ?? "");
    if (error?.status === 2 && stderr.includes("No such file or directory")) {
      return String(error?.stdout ?? "").trim();
    }
    throw error;
  }
}

function listLexiconFiles() {
  const out = runRg(["-l", String.raw`"lexicon"\s*:\s*1`, "-g", "*.json", ...LEXICON_ROOTS]);
  return out ? out.split("\n").filter(Boolean).sort() : [];
}

function loadLexiconMainTypes() {
  const map = new Map();
  for (const rel of listLexiconFiles()) {
    const full = path.join(ROOT, rel);
    const json = JSON.parse(readFileSync(full, "utf8"));
    const id = json?.id;
    const mainType = json?.defs?.main?.type;
    if (typeof id === "string" && typeof mainType === "string") {
      map.set(id, { mainType, rel });
    }
  }
  return map;
}

function scanRegistrations() {
  const out = runRg(
    [
      "-n",
      String.raw`\.((?:command)|(?:query))\("([^"]+)"`,
      ...REGISTRATION_ROOTS,
      "--glob",
      "!**/node_modules/**",
      "--glob",
      "!**/.svelte-kit/**",
      "--glob",
      "!**/dist/**",
    ],
    { maxBuffer: 64 * 1024 * 1024 },
  );
  if (!out) return [];
  const rows = [];
  for (const line of out.split("\n")) {
    const m = line.match(/^([^:]+):(\d+):.*\.(command|query)\("([^"]+)"/);
    if (!m) continue;
    rows.push({
      file: m[1],
      line: Number(m[2]),
      kind: m[3],
      nsid: m[4],
    });
  }
  return rows;
}

function main() {
  const lexicons = loadLexiconMainTypes();
  const regs = scanRegistrations();
  const errors = [];

  for (const r of regs) {
    const lex = lexicons.get(r.nsid);
    if (!lex) continue;
    if (lex.mainType === "query" && r.kind !== "query") {
      errors.push(
        `${r.file}:${r.line} registers ${r.nsid} via .${r.kind} but lexicon main type is query (${lex.rel})`,
      );
    }
    if (lex.mainType === "procedure" && r.kind !== "command") {
      errors.push(
        `${r.file}:${r.line} registers ${r.nsid} via .${r.kind} but lexicon main type is procedure (${lex.rel})`,
      );
    }
  }

  if (errors.length > 0) {
    console.error("nsid-lexicon-registration: violations found");
    for (const e of errors) console.error(`- ${e}`);
    process.exit(1);
  }

  console.log(`nsid-lexicon-registration: OK (${regs.length} registrations scanned, ${lexicons.size} lexicons)`);
}

main();

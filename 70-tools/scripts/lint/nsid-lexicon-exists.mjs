#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const LEXICON_ROOTS = ["00-contracts/lexicons", "projects", "packages"].filter((dir) =>
  existsSync(path.join(ROOT, dir)),
);
const SCAN_ROOTS = ["10-protocol", "20-actors", "30-graph", "40-engine", "50-infra", "60-apps", "70-tools"]
  .filter((dir) => existsSync(path.join(ROOT, dir)));
const STATIC_PATTERNS = [
  { name: "atProcedure", regex: /\batProcedure[^(]*\(\s*["']([^"']+)["']/g },
  { name: "atQuery", regex: /\batQuery[^(]*\(\s*["']([^"']+)["']/g },
  { name: "api.call", regex: /\.api\.call\(\s*["']([^"']+)["']/g },
];
const IGNORE_GLOBS = [
  "--glob=!**/node_modules/**",
  "--glob=!**/.svelte-kit/**",
  "--glob=!**/dist/**",
  "--glob=!**/coverage/**",
  "--glob=!**/*.md",
  "--glob=!**/*.gen.ts",
  "--glob=!**/typecheck-shims/**",
];
const NSID_RE = /^[a-z0-9-]+(?:\.[a-z0-9-]+){2,}$/;

function runRg(args, options = {}) {
  try {
    return execFileSync("rg", args, { cwd: ROOT, encoding: "utf8", ...options }).trim();
  } catch (error) {
    if (error?.status === 1) return "";
    throw error;
  }
}

function listLexiconFiles() {
  const out = runRg(["-l", String.raw`"lexicon"\s*:\s*1`, "-g", "*.json", ...LEXICON_ROOTS]);
  return out ? out.split("\n").filter(Boolean).sort() : [];
}

function loadLexiconIds() {
  const ids = new Map();
  for (const rel of listLexiconFiles()) {
    const full = path.join(ROOT, rel);
    const json = JSON.parse(readFileSync(full, "utf8"));
    if (typeof json?.id === "string") ids.set(json.id, rel);
  }
  return ids;
}

function scanStaticNsidRefs() {
  const out = runRg(
    [
      "-n",
      String.raw`atProcedure|atQuery|\.api\.call\(`,
      ...SCAN_ROOTS,
      ...IGNORE_GLOBS,
    ],
    { maxBuffer: 64 * 1024 * 1024 },
  );
  if (!out) return [];

  const refs = [];
  for (const line of out.split("\n")) {
    const match = line.match(/^([^:]+):(\d+):(.*)$/);
    if (!match) continue;
    const [, file, lineNo, source] = match;
    for (const pattern of STATIC_PATTERNS) {
      for (const m of source.matchAll(pattern.regex)) {
        const nsid = m[1];
        if (!nsid) continue;
        if (!NSID_RE.test(nsid)) continue;
        refs.push({
          file,
          line: Number(lineNo),
          nsid,
          source: pattern.name,
        });
      }
    }
  }
  return refs;
}

function main() {
  const lexicons = loadLexiconIds();
  const refs = scanStaticNsidRefs();
  const missing = [];

  for (const ref of refs) {
    if (lexicons.has(ref.nsid)) continue;
    missing.push(ref);
  }

  if (missing.length > 0) {
    console.error("nsid-lexicon-exists: missing lexicons for referenced NSIDs");
    for (const ref of missing) {
      console.error(`- ${ref.file}:${ref.line} references ${ref.nsid} via ${ref.source}, but no lexicon file exists`);
    }
    process.exit(1);
  }

  console.log(`nsid-lexicon-exists: OK (${refs.length} static references, ${lexicons.size} lexicons)`);
}

main();

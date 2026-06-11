#!/usr/bin/env node
// ADR-2605111200: Strip the `hyperdrive` binding block from every wrangler.jsonc / wrangler.toml.
// CF Worker → RisingWave 接続は禁止。DB I/O は K8s pod / Granian / LangServer worker のみ。
//
// Usage: node 70-tools/scripts/migrations/2605111200-strip-hyperdrive-binding.mjs

import { readFileSync, writeFileSync } from "node:fs";
import { execSync } from "node:child_process";

const repoRoot = execSync("git rev-parse --show-toplevel", { encoding: "utf8" }).trim();
const grepCmd = `git grep -lE '"hyperdrive"[[:space:]]*:|^\\[\\[hyperdrive\\]\\]' -- '*wrangler.jsonc' '*wrangler.toml' '*wrangler.json'`;
let files;
try {
  files = execSync(grepCmd, { cwd: repoRoot, encoding: "utf8" }).trim().split("\n").filter(Boolean);
} catch (e) {
  if (e.status === 1) { files = []; } else { throw e; }
}

let touched = 0;
let skipped = 0;

for (const rel of files) {
  const path = `${repoRoot}/${rel}`;
  const src = readFileSync(path, "utf8");
  let out = src;

  if (rel.endsWith(".jsonc") || rel.endsWith(".json")) {
    // Strip `"hyperdrive": [ ... ],?` (multi-line array) — keep surrounding whitespace minimal.
    // Tolerant of trailing comma either side.
    out = out.replace(
      /(^|\n)([ \t]*)"hyperdrive"[ \t]*:[ \t]*\[[\s\S]*?\][ \t]*,?[ \t]*(?=\n)/,
      (m, lead) => lead,
    );
    // Drop now-stray comment lines that explained the binding (best-effort).
  } else if (rel.endsWith(".toml")) {
    // Strip `[[hyperdrive]]` table block (until next blank line or next `[`).
    out = out.replace(
      /(^|\n)\[\[hyperdrive\]\][\s\S]*?(?=\n\[|$)/,
      (m, lead) => lead,
    );
  }

  if (out !== src) {
    writeFileSync(path, out);
    touched += 1;
    console.log(`stripped: ${rel}`);
  } else {
    skipped += 1;
    console.log(`no-change: ${rel}`);
  }
}

console.log(`\nDone. stripped=${touched} no-change=${skipped} total=${files.length}`);

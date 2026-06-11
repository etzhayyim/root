#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const UPDATE = process.argv.includes("--update-baseline");
const BASELINE_PATH = "90-docs/rules/val-contains-baseline.txt";

const SEARCH_ROOTS = ["20-actors", "30-graph", "50-infra", "60-apps", "70-tools"];
const EXCLUDE_GLOBS = [
  "!**/node_modules/**",
  "!**/.git/**",
  "!**/.svelte-kit/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/coverage/**",
  "!**/.wrangler-out/**",
  "!**/*.min.*",
  "!**/*.map",
  "!**/*.md",
  "!**/*.txt",
  "!**/*.json",
  "!**/*.jsonld",
  "!90-docs/**",
  "!docs/**",
  "!**/*.test.*",
  "!**/test/**",
  "!**/tests/**",
  "!70-tools/scripts/lint/no-val-contains.mjs",
];

const INCLUDE_GLOB = "*.{ts,tsx,js,mjs,cjs,go,sh}";
const VAL_CONTAINS_RE = /\bval\s+CONTAINS\b/;

function listFiles() {
  const args = ["--files", "--hidden", "--glob", INCLUDE_GLOB];
  for (const glob of EXCLUDE_GLOBS) args.push("--glob", glob);
  args.push(...SEARCH_ROOTS);

  const result = spawnSync("rg", args, {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`rg --files failed (code=${result.status}): ${result.stderr?.trim() ?? ""}`);
  }
  const out = result.stdout.trim();
  return out ? out.split("\n").filter(Boolean) : [];
}

function collectEntries() {
  const entries = [];
  for (const file of listFiles()) {
    const text = fs.readFileSync(file, "utf8");
    const lines = text.split("\n");
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      if (!VAL_CONTAINS_RE.test(line)) continue;
      entries.push(`${file}:${i + 1}:val-contains:${line.trim()}`);
    }
  }
  return [...new Set(entries)].sort();
}

const current = collectEntries();

if (UPDATE) {
  fs.mkdirSync(path.dirname(BASELINE_PATH), { recursive: true });
  fs.writeFileSync(BASELINE_PATH, `${current.join("\n")}${current.length ? "\n" : ""}`);
  console.log(`updated baseline: ${BASELINE_PATH} (${current.length} entries)`);
  process.exit(0);
}

const baseline = fs.existsSync(BASELINE_PATH)
  ? fs.readFileSync(BASELINE_PATH, "utf8").split("\n").filter(Boolean)
  : [];
const baselineSet = new Set(baseline);

const added = current.filter((e) => !baselineSet.has(e));
if (added.length > 0) {
  console.error("New `val CONTAINS` patterns detected:");
  for (const entry of added.slice(0, 200)) console.error(`  ${entry}`);
  if (added.length > 200) console.error(`  ...and ${added.length - 200} more`);
  console.error("\nUse P10v2 promoted columns (e.g. dst_vid/convo_id/name/repo/did) instead of `val CONTAINS`.");
  console.error("If this is truly unavoidable, run: pnpm lint:sql:val-contains:update");
  process.exit(1);
}

console.log(`lint:sql:val-contains ok (current=${current.length}, baseline=${baselineSet.size})`);

#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";

const SEARCH_ROOTS = ["20-actors", "30-graph", "50-infra", "60-apps", "70-tools"];
const EXCLUDE_GLOBS = [
  "!**/node_modules/**",
  "!**/.git/**",
  "!**/.svelte-kit/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/coverage/**",
  "!**/static/assets/**",
  "!**/_app/**",
  "!**/.wrangler-out/**",
  "!**/*.min.*",
  "!**/*.map",
  "!90-docs/**",
  "!docs/**",
  "!**/*.md",
  "!**/*.txt",
  "!**/*.json",
  "!**/*.jsonld",
  "!**/*.test.*",
  "!**/test/**",
  "!**/tests/**",
  "!70-tools/scripts/lint/no-val-contains.mjs",
  "!70-tools/scripts/lint/no-sql-jsonish-contains.mjs",
];

const INCLUDE_GLOB = "*.{ts,tsx,js,mjs,cjs,go,sh}";

const ALLOW_INLINE_MARKER = "sql-contains-ok";

const RULES = [
  { kind: "val-contains", re: /\bval\s+CONTAINS\b/i },
  { kind: "json-field-contains", re: /\.[A-Za-z0-9_]*Json\s+CONTAINS\b/i },
  { kind: "json-field-contains", re: /\.[A-Za-z0-9_]*_json\s+CONTAINS\b/i },
  { kind: "topics-contains", re: /\.(topics|entities|platforms)\s+CONTAINS\b/i },
];

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

function collectViolations() {
  const entries = [];
  for (const file of listFiles()) {
    const text = fs.readFileSync(file, "utf8");
    const lines = text.split("\n");
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      const trimmed = line.trim();
      if (trimmed.startsWith("//") || trimmed.startsWith("*") || trimmed.startsWith("/*")) continue;
      if (!/\bCONTAINS\b/i.test(line)) continue;
      if (!/["'`]/.test(line)) continue;
      if (line.includes(ALLOW_INLINE_MARKER)) continue;
      for (const rule of RULES) {
        if (!rule.re.test(line)) continue;
        entries.push(`${file}:${i + 1}:${rule.kind}:${line.trim()}`);
      }
    }
  }
  return [...new Set(entries)].sort();
}

const violations = collectViolations();
if (violations.length > 0) {
  console.error("Forbidden SQL CONTAINS patterns detected:");
  for (const entry of violations.slice(0, 200)) console.error(`  ${entry}`);
  if (violations.length > 200) console.error(`  ...and ${violations.length - 200} more`);
  console.error("\nUse promoted columns + equality/prefix predicates instead of JSON-ish CONTAINS.");
  console.error(`If a line is truly unavoidable, add inline marker: ${ALLOW_INLINE_MARKER}`);
  process.exit(1);
}

console.log("lint:sql:jsonish-contains ok (no forbidden patterns)");

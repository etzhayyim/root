#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const UPDATE = process.argv.includes("--update-baseline");
const BASELINE_PATH = "90-docs/rules/count-mv-baseline.txt";
const ALLOW_INLINE_MARKER = "mv-count-ok";

const SEARCH_ROOTS = ["20-actors", "30-graph", "50-infra", "60-apps", "70-tools", "packages"]
  .filter((dir) => fs.existsSync(dir));
const EXCLUDE_GLOBS = [
  "!**/.git/**",
  "!**/node_modules/**",
  "!**/.svelte-kit/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/coverage/**",
  "!**/.wrangler-out/**",
  "!**/_app/**",
  "!**/static/assets/**",
  "!**/*.min.*",
  "!**/*.map",
  "!**/*.md",
  "!**/*.txt",
  "!**/*.json",
  "!**/*.jsonld",
  "!**/*.test.*",
  "!**/test/**",
  "!**/tests/**",
  "!70-tools/scripts/lint/count-mv-guard.mjs",
];
const INCLUDE_GLOB = "*.{ts,tsx,js,mjs,cjs,svelte,go,sh}";

const SQL_BASE_TABLE_COUNT_RE = /\bSELECT\s+COUNT\s*\(\s*\*\s*\)\s+AS\s+\w+\s+FROM\s+graphar\.(vertex_post(?!_live)\b|edge_follows\b|edge_likes\b|edge_reposts\b|vertex_actor\b|vertex_profile\b)/gi;
const SQL_BASE_COUNT_RE = /\bMATCH\s*\([^)]*:(Post|Follow|Like|Repost|Profile)\)\b[\s\S]{0,1600}?\bRETURN\s+count\s*\(/gi;

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

function lineNumberAt(text, index) {
  let line = 1;
  for (let i = 0; i < index; i += 1) {
    if (text.charCodeAt(i) === 10) line += 1;
  }
  return line;
}

function lineTextAt(lines, lineNo) {
  return lines[Math.max(0, lineNo - 1)] ?? "";
}

function collectEntries() {
  const entries = [];
  for (const file of listFiles()) {
    const text = fs.readFileSync(file, "utf8");
    const lines = text.split("\n");
    const checks = [
      { kind: "sql-base-count", re: SQL_BASE_TABLE_COUNT_RE },
      { kind: "sql-base-count", re: SQL_BASE_COUNT_RE },
    ];

    for (const { kind, re } of checks) {
      re.lastIndex = 0;
      let match;
      while ((match = re.exec(text)) !== null) {
        const idx = match.index ?? 0;
        const lineNo = lineNumberAt(text, idx);
        const line = lineTextAt(lines, lineNo);
        const trimmed = line.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith("//") || trimmed.startsWith("*") || trimmed.startsWith("/*")) continue;
        if (line.includes(ALLOW_INLINE_MARKER)) continue;
        entries.push(`${file}:${lineNo}:${kind}:${trimmed}`);
      }
    }
  }
  return [...new Set(entries)].sort();
}

const current = collectEntries();
if (UPDATE) {
  fs.mkdirSync(path.dirname(BASELINE_PATH), { recursive: true });
  fs.writeFileSync(BASELINE_PATH, current.length > 0 ? `${current.join("\n")}\n` : "");
  console.log(`updated baseline: ${BASELINE_PATH} (${current.length} entries)`);
  process.exit(0);
}

const baseline = fs.existsSync(BASELINE_PATH)
  ? fs.readFileSync(BASELINE_PATH, "utf8").split("\n").filter(Boolean)
  : [];
const baselineSet = new Set(baseline);
const added = current.filter((e) => !baselineSet.has(e));

if (added.length > 0) {
  console.error("New count queries bypassing MV policy detected:");
  for (const entry of added.slice(0, 200)) console.error(`  ${entry}`);
  if (added.length > 200) console.error(`  ...and ${added.length - 200} more`);
  console.error("\nUse MV-backed tables/views for count aggregation, or annotate line with marker: mv-count-ok");
  console.error("If intentional and reviewed, update baseline:");
  console.error("  pnpm lint:count:mv:update");
  process.exit(1);
}

console.log(`lint:count:mv ok (current=${current.length}, baseline=${baseline.length})`);

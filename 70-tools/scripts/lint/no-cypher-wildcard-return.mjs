#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const UPDATE = process.argv.includes("--update-baseline");
const BASELINE_PATH = "90-docs/rules/sql-wildcard-return-baseline.txt";

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
  "!**/*.test.*",
  "!**/test/**",
  "!**/tests/**",
  "!70-tools/scripts/lint/no-sql-wildcard-return.mjs",
];

const INCLUDE_GLOB = "*.{ts,tsx,js,mjs,cjs,json,jsonld,go}";

// Detect risky patterns:
// 1) RETURN * 
// 2) RETURN <alias> where alias is a bare identifier (no property), including RETURN n, RETURN n LIMIT, RETURN n, ...
//    Restrict to terminators (comma / LIMIT / ORDER / SKIP / UNION / EOL) to avoid
//    false positives like `RETURN CASE WHEN ...`.
const RETURN_STAR_RE = /\bRETURN\s+\*/i;
const RETURN_BARE_ALIAS_RE = /\bRETURN\s+([A-Za-z_]\w*)\b(?!\s*\.)(?=\s*(?:,|LIMIT\b|ORDER\b|SKIP\b|UNION\b|$))/ig;
const SQL_KEY_RE = /\bsql\b/i;

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

function classifyLine(line) {
  if (!SQL_KEY_RE.test(line)) return null;
  if (RETURN_STAR_RE.test(line)) return "return-star";

  RETURN_BARE_ALIAS_RE.lastIndex = 0;
  let m;
  while ((m = RETURN_BARE_ALIAS_RE.exec(line)) !== null) {
    const alias = m[1];
    // allow aggregate function calls etc. (e.g. RETURN count)
    if (["count", "sum", "avg", "min", "max", "distinct"].includes(alias.toLowerCase())) continue;
    // Only treat as risky wildcard if alias is declared as a MATCH node variable
    // on the same line, e.g. MATCH (n:Label) ... RETURN n
    const aliasDecl = new RegExp(`\\(\\s*${alias}\\s*[:\\)\\{]`, "i");
    if (!aliasDecl.test(line)) continue;
    return `return-bare-alias:${alias}`;
  }
  return null;
}

function collectEntries() {
  const entries = [];
  for (const file of listFiles()) {
    const text = fs.readFileSync(file, "utf8");
    const lines = text.split("\n");
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      const kind = classifyLine(line);
      if (!kind) continue;
      entries.push(`${file}:${i + 1}:${kind}:${line.trim()}`);
    }
  }
  return [...new Set(entries)].sort();
}

const current = collectEntries();

if (UPDATE) {
  fs.mkdirSync(path.dirname(BASELINE_PATH), { recursive: true });
  fs.writeFileSync(BASELINE_PATH, `${current.join("\n")}\n`);
  console.log(`updated baseline: ${BASELINE_PATH} (${current.length} entries)`);
  process.exit(0);
}

const baseline = fs.existsSync(BASELINE_PATH)
  ? fs.readFileSync(BASELINE_PATH, "utf8").split("\n").filter(Boolean)
  : [];
const baselineSet = new Set(baseline);

const added = current.filter((e) => !baselineSet.has(e));
if (added.length > 0) {
  console.error("New risky SQL wildcard patterns detected:");
  for (const entry of added.slice(0, 200)) console.error(`  ${entry}`);
  if (added.length > 200) console.error(`  ...and ${added.length - 200} more`);
  console.error("\nUse explicit RETURN columns instead of RETURN n / RETURN *.");
  console.error("If intentional, run: pnpm lint:sql:wildcard:update");
  process.exit(1);
}

console.log(`lint:sql:wildcard ok (current=${current.length}, baseline=${baselineSet.size})`);

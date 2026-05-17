#!/usr/bin/env node
/**
 * Lint: dangerous RisingWave query patterns.
 *
 * DSM danger categories:
 *   1. Pushdown破壊型 — LIKE '%...%', REGEXP, function-on-column, CONTAINS, STARTS WITH
 *   2. Scan増大型     — SELECT * FROM graphar
 *   3. Shuffle増大型  — function-on-join-key
 *
 * Baseline-aware: existing violations are tracked in baseline file.
 * New violations block commit/push. Run --update-baseline to accept.
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const UPDATE = process.argv.includes("--update-baseline");
const BASELINE_PATH = "90-docs/rules/dangerous-query-baseline.txt";

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
  "!**/_svelte/**",
  "!**/static/**",
  "!**/*.md",
  "!**/*.txt",
  "!**/*.json",
  "!**/*.jsonld",
  "!90-docs/**",
  "!docs/**",
  "!**/*.test.*",
  "!**/test/**",
  "!**/tests/**",
  "!**/test_*",
  // Exclude lint script itself
  "!70-tools/scripts/lint/no-dangerous-query.mjs",
  // Exclude query-builder/transpiler/plan source (prohibition definitions)
  "!30-graph/graph-planner/src/sql/transpile.ts",
  "!30-graph/graph-planner/src/sql/plan.ts",
  "!_archive/30-graph/kagami-live-260414/src/sql/transpile.ts",
  "!_archive/30-graph/kagami-live-260414/src/sql/plan.ts",
  "!_archive/30-graph/kagami-live-260414/src/sql/dialect.ts",
  "!30-graph/graph-planner/src/sql/dialect.ts",
];

const INCLUDE_GLOB = "*.{ts,tsx,js,mjs,cjs,svelte}";

// ── Patterns ──

/** @type {Array<{id: string, re: RegExp, severity: "S"|"A", category: string, message: string}>} */
const RULES = [
  // ── Pushdown破壊型 (S-rank) ──
  {
    id: "like-infix",
    re: /LIKE\s+'%[^']*%'/i,
    severity: "S",
    category: "pushdown破壊",
    message: "LIKE '%...%' bypasses all indexes → full segment scan → OOM. Use exact match or IVF vector search.",
  },
  {
    id: "like-suffix",
    re: /LIKE\s+'%[^']+'/i,
    severity: "S",
    category: "pushdown破壊",
    message: "LIKE '%...' suffix pattern bypasses bloom filter → full segment scan. Use exact match.",
  },
  {
    id: "like-template-infix",
    re: /LIKE\s+'%\$\{/i,
    severity: "S",
    category: "pushdown破壊",
    message: "LIKE '%${...}%' template bypasses bloom filter → full segment scan. Use exact match or IVF.",
  },
  {
    id: "like-template-backtick",
    re: /LIKE\s+`%\$/i,
    severity: "S",
    category: "pushdown破壊",
    message: "LIKE `%${}%` template bypasses bloom filter → full segment scan. Use exact match or IVF.",
  },
  {
    id: "contains-sql",
    re: /\b(?:WHERE|AND|OR)\s+\w+\.\w+\s+CONTAINS\b/i,
    severity: "S",
    category: "pushdown破壊",
    message: "SQL CONTAINS → INSTR/LIKE on RisingWave → full segment scan → OOM. Use exact match or IVF vector search.",
  },
  {
    id: "starts-with-sql",
    re: /\b(?:WHERE|AND|OR)\s+\w+\.\w+\s+STARTS\s+WITH\b/i,
    severity: "S",
    category: "pushdown破壊",
    message: "SQL STARTS WITH → LIKE on RisingWave, bypasses bloom filter → full segment scan. Use exact match.",
  },
  {
    id: "regexp-sql",
    re: /\bREGEXP\s+['"`$]/i,
    severity: "S",
    category: "pushdown破壊",
    message: "REGEXP bypasses all indexes → full segment scan + CPU-intensive regex evaluation → OOM.",
  },
  {
    id: "fn-where-cast",
    re: /\bWHERE\b.*\bCAST\s*\(/i,
    severity: "S",
    category: "pushdown破壊",
    message: "CAST() in WHERE destroys pushdown → full segment scan. Compare against raw columns.",
  },
  {
    id: "fn-where-date-format",
    re: /\bWHERE\b.*\bdate_format\s*\(/i,
    severity: "S",
    category: "pushdown破壊",
    message: "date_format() in WHERE destroys pushdown → full segment scan. Use raw timestamp comparison.",
  },
  {
    id: "fn-where-tolower",
    re: /\bWHERE\b.*\btoLower\s*\(/i,
    severity: "S",
    category: "pushdown破壊",
    message: "toLower() in WHERE destroys pushdown → full segment scan. Store normalized values at write time.",
  },
  {
    id: "fn-where-toupper",
    re: /\bWHERE\b.*\btoUpper\s*\(/i,
    severity: "S",
    category: "pushdown破壊",
    message: "toUpper() in WHERE destroys pushdown → full segment scan. Store normalized values at write time.",
  },

  // ── Scan増大型 (A-rank) ──
  {
    id: "select-star-graphar",
    re: /SELECT\s+\*\s+FROM\s+(?:graphar|kagami)\./i,
    severity: "A",
    category: "scan増大",
    message: "SELECT * FROM graphar reads all columns → kills late materialization. Specify needed columns.",
  },

  // ── Deprecated API calls ──
  {
    id: "call-whereLike",
    re: /\.whereLike\s*\(/,
    severity: "S",
    category: "pushdown破壊",
    message: ".whereLike() is prohibited. Use .where() (exact match) or .whereIn().",
  },
  {
    id: "call-whereRegexp",
    re: /\.whereRegexp\s*\(/,
    severity: "S",
    category: "pushdown破壊",
    message: ".whereRegexp() is prohibited. Use .where() or IVF vector search.",
  },
  {
    id: "call-whereContains",
    re: /\.whereContains\s*\(/,
    severity: "S",
    category: "pushdown破壊",
    message: ".whereContains() is prohibited. Use .where() or IVF vector search.",
  },
  {
    id: "call-whereStartsWith",
    re: /\.whereStartsWith\s*\(/,
    severity: "S",
    category: "pushdown破壊",
    message: ".whereStartsWith() is prohibited. Use .where() (exact match) or .whereIn().",
  },
  {
    id: "call-buildLabelSql",
    re: /\bbuildLabelSql\s*\(/,
    severity: "A",
    category: "deprecated",
    message: "buildLabelSql() is deprecated. Use G class query builder.",
  },
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
  if (result.status !== 0 && result.status !== 1) {
    throw new Error(`rg --files failed (code=${result.status}): ${result.stderr?.trim() ?? ""}`);
  }
  const out = (result.stdout ?? "").trim();
  return out ? out.split("\n").filter(Boolean) : [];
}

function collectEntries() {
  const entries = [];
  for (const file of listFiles()) {
    let text;
    try {
      text = fs.readFileSync(file, "utf8");
    } catch {
      continue;
    }
    const lines = text.split("\n");
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      // Skip comment-only lines
      if (/^\s*(?:\/\/|\/\*|\*)/.test(line)) continue;
      // Skip import lines
      if (/^\s*import\s/.test(line)) continue;
      // Skip lines in throw/error message strings (prohibition definitions)
      if (/throw new Error|PROHIBITED|is prohibited/.test(line)) continue;
      // Skip @deprecated JSDoc
      if (/@deprecated/.test(line)) continue;

      for (const rule of RULES) {
        if (!rule.re.test(line)) continue;
        entries.push(`${file}:${i + 1}:${rule.id}:${line.trim()}`);
      }
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
const removed = baseline.filter((e) => !current.includes(e));

if (removed.length > 0) {
  console.log(`${removed.length} baseline entries resolved (run --update-baseline to clean up)`);
}

if (added.length > 0) {
  console.error(`\n❌ ${added.length} new dangerous query pattern(s) detected:\n`);
  for (const entry of added.slice(0, 50)) {
    const [file, line, id, ...rest] = entry.split(":");
    const rule = RULES.find((r) => r.id === id);
    const sev = rule?.severity ?? "?";
    const cat = rule?.category ?? "?";
    console.error(`  [${sev}] ${file}:${line} (${cat}) ${id}`);
    console.error(`      ${rest.join(":").substring(0, 120)}`);
    if (rule) console.error(`      → ${rule.message}`);
    console.error();
  }
  if (added.length > 50) console.error(`  ...and ${added.length - 50} more\n`);
  console.error("Fix the violations above, or if truly unavoidable:");
  console.error("  node 70-tools/scripts/lint/no-dangerous-query.mjs --update-baseline\n");
  process.exit(1);
}

console.log(`lint:dangerous-query ok (current=${current.length}, baseline=${baselineSet.size})`);

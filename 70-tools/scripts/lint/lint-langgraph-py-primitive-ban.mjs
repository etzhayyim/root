#!/usr/bin/env node
/**
 * lint-langgraph-py-primitive-ban — ADR-2605082000 §2.5 enforcement.
 *
 * Forbids new `vertex_langgraph_assistant_node` rows with kind='py_primitive'.
 * py_primitive is the last code-island in the data-driven self-evolution
 * architecture: ref = arbitrary Python dotted path, which means new node
 * behavior requires a repo commit. ADR-2605082000 broadens the allowed
 * data-resolved kinds to {mcp_tool, sql_udf, py_ext_udf, llm} and stages
 * py_primitive out.
 *
 * What this lint does:
 *   - Scans SQL migrations under 30-graph/graph-schema/{sql_migrations,migrations}
 *     for the literal `'py_primitive'`.
 *   - Scans Python seed scripts under 30-graph/graph-schema/sql_migrations/_gen*.py
 *     for the same.
 *
 * What this lint does NOT do:
 *   - Touch the resolver/loader code itself — `make_*` functions and dispatcher
 *     branches must stay until Phase 2 of the deprecation plan.
 *   - Touch ADR documentation — we want to be able to discuss py_primitive there.
 *
 * Allow-list:
 *   - `_archive/**`, `__pycache__/**`, `node_modules/**` — never linted
 *   - inline marker `lint-py-primitive-ok` on the same line — surfaces an
 *     intentional bypass with a code review pin
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Resolve repo root from this script's location (70-tools/scripts/lint/...) so
// the lint runs identically from any cwd.
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const SEARCH_ROOTS = [
  path.join(REPO_ROOT, "30-graph/graph-schema/sql_migrations"),
  path.join(REPO_ROOT, "30-graph/graph-schema/migrations"),
];
const EXCLUDE_GLOBS = [
  "!**/_archive/**",
  "!**/node_modules/**",
  "!**/__pycache__/**",
  "!**/.git/**",
];
const INCLUDE_GLOB = "*.{sql,py,ts}";
const ALLOW_INLINE_MARKER = "lint-py-primitive-ok";
// File-level skip — set on a header comment line near the top of the file
// (within the first 20 lines) to grandfather an entire migration. Use only
// for bulk legacy imports tracked under deps.toml [[migrations]].
const ALLOW_FILE_MARKER = "lint-py-primitive-ok-file";
const FILE_HEADER_LOOKBACK = 20;
const FORBIDDEN = /'py_primitive'/;

function listFiles() {
  const args = ["--files", "--hidden", "--glob", INCLUDE_GLOB];
  for (const glob of EXCLUDE_GLOBS) args.push("--glob", glob);
  args.push(...SEARCH_ROOTS);
  const result = spawnSync("rg", args, {
    encoding: "utf8",
    maxBuffer: 32 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0 && result.status !== 1) {
    throw new Error(
      `rg --files failed (code=${result.status}): ${result.stderr?.trim() ?? ""}`,
    );
  }
  const out = (result.stdout || "").trim();
  return out ? out.split("\n").filter(Boolean) : [];
}

function collectViolations() {
  const entries = [];
  for (const file of listFiles()) {
    let text;
    try {
      text = fs.readFileSync(file, "utf8");
    } catch {
      continue;
    }
    const lines = text.split("\n");
    // File-level skip: scan the header for ALLOW_FILE_MARKER. The marker
    // must appear on a comment line within FILE_HEADER_LOOKBACK lines.
    const headerSlice = lines.slice(0, FILE_HEADER_LOOKBACK).join("\n");
    if (headerSlice.includes(ALLOW_FILE_MARKER)) continue;
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      if (!FORBIDDEN.test(line)) continue;
      if (line.includes(ALLOW_INLINE_MARKER)) continue;
      entries.push(`${file}:${i + 1}: ${line.trim()}`);
    }
  }
  return entries.sort();
}

const violations = collectViolations();
if (violations.length > 0) {
  console.error("ADR-2605082000 §2.5 violation: kind='py_primitive' is banned.");
  console.error("");
  console.error("py_primitive lets a node bind to an arbitrary Python dotted path,");
  console.error("which makes new graph behavior require a repo commit. Use one of");
  console.error("the data-resolved kinds instead:");
  console.error("");
  console.error("  mcp_tool   ref = mcp://<nsid>            (ADR-2605082000 §2.6)");
  console.error("  sql_udf    ref = SQL function name       (RisingWave catalog)");
  console.error("  py_ext_udf ref = External Python UDF     (Arrow Flight)");
  console.error("  llm        ref = tier or model id        (llm-model-registry)");
  console.error("");
  console.error("Violations:");
  for (const entry of violations.slice(0, 200)) console.error(`  ${entry}`);
  if (violations.length > 200) {
    console.error(`  ...and ${violations.length - 200} more`);
  }
  console.error("");
  console.error(
    `Bypass (audit trail): add the marker '${ALLOW_INLINE_MARKER}' to the line.`,
  );
  process.exit(1);
}

console.log("lint:langgraph:py-primitive-ban ok (no forbidden bindings)");

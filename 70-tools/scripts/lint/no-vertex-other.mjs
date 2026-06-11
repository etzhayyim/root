#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";

const SEARCH_ROOTS = ["20-actors", "40-engine", "50-infra", "60-apps", "70-tools"]
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
  "!70-tools/scripts/lint/no-vertex-other.mjs",
  "!40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/legacy-vertex-other.ts",
];

const INCLUDE_GLOB = "*.{ts,tsx,js,mjs,cjs,svelte,go,sh}";
const FORBIDDEN_RE = /\b(vertex_other|mv_vertex_other_count)\b/g;

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

function isCommentOnlyLine(line) {
  const trimmed = line.trim();
  return (
    trimmed.startsWith("//")
    || trimmed.startsWith("*")
    || trimmed.startsWith("/*")
    || trimmed.startsWith("*/")
    || trimmed.startsWith("#")
  );
}

function collectViolations() {
  const out = [];

  for (const file of listFiles()) {
    const text = fs.readFileSync(file, "utf8");
    const lines = text.split("\n");

    FORBIDDEN_RE.lastIndex = 0;
    let m;
    while ((m = FORBIDDEN_RE.exec(text)) !== null) {
      const idx = m.index ?? 0;
      const lineNo = lineNumberAt(text, idx);
      const line = lineTextAt(lines, lineNo);
      if (!line.trim()) continue;
      if (isCommentOnlyLine(line)) continue;
      out.push(`${file}:${lineNo}:${m[0]}:${line.trim()}`);
    }
  }

  return [...new Set(out)].sort();
}

const violations = collectViolations();
if (violations.length > 0) {
  console.error("vertex_other usage is forbidden. Use typed Kysely schema tables instead.");
  for (const v of violations.slice(0, 300)) console.error(`  ${v}`);
  if (violations.length > 300) console.error(`  ...and ${violations.length - 300} more`);
  process.exit(1);
}

console.log("lint:no-vertex-other ok (0 violations)");

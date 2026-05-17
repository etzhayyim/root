#!/usr/bin/env node
/**
 * Guard new RisingWave migrations against non-idempotent foreground DDL.
 *
 * Existing historical migrations include plain CREATE INDEX statements, so this
 * guard enforces the rule from the first migration created after the RW
 * stabilization incident.
 */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const migrationPrefix = "30-graph/graph-schema/migrations/";
const enforcedFrom = "20260430500000";

function gitFiles() {
  const out = execFileSync(
    "git",
    ["ls-files", "--cached", "--others", "--exclude-standard", "--", migrationPrefix],
    { cwd: repoRoot, encoding: "utf8" },
  );
  return out.split("\n").filter(Boolean);
}

function lineNumberForOffset(text, offset) {
  return text.slice(0, offset).split("\n").length;
}

const findings = [];

for (const file of gitFiles()) {
  const base = path.basename(file);
  const stamp = base.match(/^(\d{14})_/)?.[1];
  if (!stamp || stamp < enforcedFrom) continue;

  const text = readFileSync(path.join(repoRoot, file), "utf8");
  const createIndex = /\bCREATE\s+INDEX\b(?!\s+IF\s+NOT\s+EXISTS)/gi;
  for (const match of text.matchAll(createIndex)) {
    findings.push({
      file,
      line: lineNumberForOffset(text, match.index ?? 0),
      reason: "CREATE INDEX in RisingWave migrations must use IF NOT EXISTS.",
    });
  }
}

if (findings.length > 0) {
  console.error("[risingwave-ddl-safety-guard] unsafe RisingWave DDL found");
  for (const finding of findings) {
    console.error(`\n${finding.file}:${finding.line}`);
    console.error(`  ${finding.reason}`);
  }
  process.exit(1);
}

console.log("[risingwave-ddl-safety-guard] OK");

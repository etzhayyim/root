#!/usr/bin/env node
// ADR-0040 enforcement: every migration that creates a new `vertex_*`
// table must (a) declare its tier with a `// tier: A|B|C` comment and
// (b) appear in `30-graph/deps.toml [vertex_tier.tier_X.tables]`.
//
// Usage:
//   node scripts/lint-vertex-tier.mjs                # lint all migrations
//   node scripts/lint-vertex-tier.mjs <file> [...]   # lint specific files
//
// CI invocation passes only PR-changed migration files. Local invocation
// without args sweeps the whole tree.

import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const migrationsDir = path.resolve(__dirname, "..", "migrations");
const depsTomlPath = path.resolve(repoRoot, "30-graph", "deps.toml");

function loadTierMap() {
  // Minimal TOML extractor — pulls `tables = [ "name", ... ]` blocks under
  // [vertex_tier.tier_a|b|c]. Avoids a `tomllib` runtime dep in CI.
  const text = readFileSync(depsTomlPath, "utf8");
  const map = new Map();
  const sectionRe = /\[vertex_tier\.tier_([abc])\]\s*([\s\S]*?)(?=\n\[|$)/g;
  let m;
  while ((m = sectionRe.exec(text)) !== null) {
    const tier = m[1].toUpperCase();
    const body = m[2];
    const tablesMatch = body.match(/tables\s*=\s*\[([\s\S]*?)\]/);
    if (!tablesMatch) continue;
    const names = [...tablesMatch[1].matchAll(/"(vertex_[a-z0-9_]+)"/g)].map(
      (x) => x[1]
    );
    for (const name of names) map.set(name, tier);
  }
  return map;
}

function extractCreatedVertexTables(content) {
  // Match: CREATE TABLE [IF NOT EXISTS] [schema.]vertex_xxx
  const re = /CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[a-z_]+\.)?(vertex_[a-z0-9_]+)/gi;
  return [...new Set([...content.matchAll(re)].map((m) => m[1].toLowerCase()))];
}

function extractTierComments(content) {
  // Match: `// tier: A`  /  `// tier: B`  /  `// tier: C`
  // Also accept SQL comment form `-- tier: X` for embedded DDL.
  const re = /(?:\/\/|--)\s*tier\s*:\s*([ABC])\b/gi;
  return [...new Set([...content.matchAll(re)].map((m) => m[1].toUpperCase()))];
}

function lintFile(file, tierMap) {
  const content = readFileSync(file, "utf8");
  const created = extractCreatedVertexTables(content);
  if (created.length === 0) return []; // not a vertex-creating migration

  const declared = extractTierComments(content);
  const errs = [];

  if (declared.length === 0) {
    errs.push(
      `${file}: creates ${created.length} vertex table(s) but has no \`// tier: A|B|C\` comment (ADR-0040)`
    );
  }

  for (const name of created) {
    if (!tierMap.has(name)) {
      errs.push(
        `${file}: created table \`${name}\` is missing from \`30-graph/deps.toml [vertex_tier.tier_*]\` (ADR-0040)`
      );
    }
  }

  return errs;
}

function listMigrations() {
  return readdirSync(migrationsDir)
    .filter((f) => f.endsWith(".ts"))
    .map((f) => path.join(migrationsDir, f));
}

function main() {
  const argv = process.argv.slice(2);
  const enforce = argv.length > 0;
  const files = enforce ? argv.map((p) => path.resolve(p)) : listMigrations();

  const tierMap = loadTierMap();
  if (tierMap.size === 0) {
    console.error(
      `lint-vertex-tier: failed to parse [vertex_tier.tier_*] from ${depsTomlPath}`
    );
    process.exit(2);
  }

  const errs = [];
  for (const f of files) {
    if (!f.includes("/migrations/")) continue;
    if (!f.endsWith(".ts")) continue;
    errs.push(...lintFile(f, tierMap));
  }

  // CI mode: file args passed → enforce, exit 1 on violations.
  // Audit mode: no args → scan all, print summary, exit 0 (legacy migrations
  // pre-ADR-0040 are grandfathered; CI only checks PR-changed files).
  if (errs.length > 0) {
    const header = enforce
      ? "ADR-0040 vertex-tier lint failed:"
      : `ADR-0040 vertex-tier audit (legacy/grandfathered, ${errs.length} issue(s)):`;
    console.error(header);
    for (const e of errs) console.error("  - " + e);
    if (enforce) {
      console.error(
        `\nFix: add \`// tier: A|B|C\` to the migration and register the table\n` +
          `in \`30-graph/deps.toml [vertex_tier.tier_X.tables]\`.\n` +
          `Default tier is C (reference / classification / crawl / infra).`
      );
      process.exit(1);
    }
  }

  console.log(
    `lint-vertex-tier: ${enforce ? "OK (enforce)" : "audit done"} ` +
      `(scanned ${files.length} file(s), registry has ${tierMap.size} entries, ` +
      `${errs.length} issue(s))`
  );
}

main();

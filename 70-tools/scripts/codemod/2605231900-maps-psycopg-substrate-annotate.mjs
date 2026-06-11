#!/usr/bin/env node
// ADR-2605172000 — RW → MST substrate migration. This codemod tags
// every remaining `import psycopg2` line in 60-apps/etzhayyim-project-maps
// bulk-ingest workers (except the already-migrated openflights_dumper)
// with a one-line `# CHARTER-VIOLATION §substrate` marker so the
// substrate-boundary lint catches them on subsequent commits.
//
// It does NOT rewrite the psycopg call sites — the wholesale rewrite
// must be applied per-worker against `_etzhayyim_substrate.py`
// (`open_substrate_writer()`), as documented in
// `60-apps/etzhayyim-project-maps/bulk-ingest/workers/MIGRATION-TODO.md`.
//
// Idempotent. Re-runs only add the marker once per file.

import { readFileSync, writeFileSync } from "node:fs";
import { execSync } from "node:child_process";

const MARKER = "# CHARTER-VIOLATION §substrate (ADR-2605172000) — replace with _etzhayyim_substrate.open_substrate_writer()";

const repoRoot = execSync("git rev-parse --show-toplevel 2>/dev/null || pwd", {
  encoding: "utf8",
}).trim();

const root = `${repoRoot}/60-apps/etzhayyim-project-maps/bulk-ingest/workers`;
const targets = execSync(
  `grep -lE '^(import psycopg2?|from psycopg2? )' ${root}/*.py 2>/dev/null || true`,
  { encoding: "utf8" },
).split("\n").filter(Boolean);

let touched = 0;
let alreadyMarked = 0;

for (const path of targets) {
  if (path.endsWith("/openflights_dumper.py")) continue; // already migrated
  const src = readFileSync(path, "utf8");
  if (src.includes("CHARTER-VIOLATION §substrate")) {
    alreadyMarked += 1;
    continue;
  }
  const out = src.replace(
    /^(import psycopg2(?:\.\w+)?|from psycopg2(?:\.\w+)? import .+)$/m,
    `${MARKER}\n$1`,
  );
  if (out !== src) {
    writeFileSync(path, out);
    process.stdout.write(`annotated: ${path.replace(repoRoot + "/", "")}\n`);
    touched += 1;
  }
}

process.stdout.write(
  `\nSummary: ${touched} annotated, ${alreadyMarked} already-marked.\n`,
);

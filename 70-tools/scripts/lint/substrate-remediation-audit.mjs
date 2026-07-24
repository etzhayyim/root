#!/usr/bin/env node
/**
 * substrate-remediation-audit — the shrink-only ratchet for ADR-2606071800.
 *
 * The pre-commit `substrate-boundary.mjs` lint only inspects STAGED files, so the
 * large body of pre-guard legacy code that imports RisingWave/Postgres/Kysely directly
 * was never enforced. ADR-2606071800 opens a remediation wave with a **frozen allowlist**
 * (`substrate-frozen-allowlist.json`) of the legacy storage-rule violators, and this
 * script is the ratchet that keeps the list shrink-only.
 *
 * Full-tree scan (not just staged files) for the SAME storage-import patterns the lint
 * uses (kept in sync deliberately — this file is the audit SoT for the wave; the lint
 * imports the allowlist this writes). Three modes:
 *
 *   --write    (re)generate substrate-frozen-allowlist.json from the current tree.
 *              Use ONLY to seed the wave or after a legitimate review; never to launder
 *              new debt — `--audit` is what CI runs.
 *   --audit    (default) compare the current tree to the frozen allowlist:
 *                FAIL  if any file violates a storage rule and is NOT on the allowlist
 *                      (new debt or a regression — the boundary must hold for new code).
 *                WARN  if an allowlisted file no longer violates (graduated — remove it;
 *                      the list may only shrink).
 *              Exit 1 on any FAIL; exit 0 (with warnings) otherwise.
 *
 * Usage:
 *   node 70-tools/scripts/lint/substrate-remediation-audit.mjs [--write|--audit]
 *
 * Authoritative ADR: 90-docs/adr/2606071800-legacy-risingwave-kysely-to-kotoba-kqe-remediation-wave.md
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from "node:fs";
import path from "node:path";

const REPO_ROOT = process.cwd();
const ALLOWLIST_PATH = "70-tools/scripts/lint/substrate-frozen-allowlist.json";

// Roots to scan. Mirrors where app/actor/infra code lives.
const SCAN_ROOTS = ["20-actors", "60-apps", "50-infra", "30-graph", "40-engine"];

// ── Storage-import patterns — kept in lock-step with substrate-boundary.mjs ──
// (storagePatterns there). This script intentionally covers ONLY storage rules:
// the remediation wave is about the RisingWave/SQL read path, not payment/seam.
const STORAGE_PATTERNS = [
  /from\s+["']kysely["']/,
  /from\s+["']@kysely\//,
  /from\s+["']pg["']/,
  /from\s+["']postgres["']/,
  /from\s+["']mysql2?["']/,
  /from\s+["']mongodb["']/,
  /from\s+["']risingwave["']/,
  /from\s+["']@risingwavelabs\//,
  /^import\s+psycopg(2)?(\s|$)/m,
  /^from\s+psycopg(2)?\s+import/m,
  /^import\s+pg8000(\s|$)/m,
  // Hyperdrive is the RisingWave-over-Postgres-wire binding — a read-path tell the
  // pre-commit lint does not catch (it gates the client import, not the binding use).
  // The wave targets it explicitly, so the audit counts it.
  /createKyselyDb\s*\(/,
  /env\.HYPERDRIVE\b/,
];

// Path prefixes that legitimately use the substrate (mirrors lint allowedPrefixes,
// trimmed to the ones relevant under the scanned roots).
const ALLOWED_PREFIXES = [
  "orgs/etzhayyim/com-etzhayyim-sdk/",
  "50-infra/etzhayyim-sdk-checkpointer/",
  "50-infra/mst-projector/",
  "50-infra/anchor-cron/",
  "50-infra/etzhayyim-paymaster/",
  "50-infra/etzhayyim-membership-contract/",
  "50-infra/etzhayyim-chain-contracts/",
  "50-infra/etzhayyim-did-web/",
  "50-infra/etzhayyim-pds-did-web/",
  "50-infra/cloudflare/",
  "50-infra/vultr/",
  "50-infra/l2-anchor-contract/",
  "30-graph/graph-schema/migrations/",
  "30-graph/graph-schema/alembic/",
  "30-graph/graph-schema/sql_migrations/",
  "30-graph/graph-schema/sqlmesh/",
  "30-graph/graph-schema/scripts/",
];

const ALLOWED_PATH_PATTERNS = [
  /\/node_modules\//,
  /\/dist\//,
  /\/build\//,
  /\/\.svelte-kit\//,
  /\/__pycache__\//,
  /\/test\//,
  /\/tests\//,
  /\/__tests__\//,
  /\/__test__\//,
  /\.test\.(ts|tsx|js|mjs|cjs|jsx|py)$/,
  /\.spec\.(ts|tsx|js|mjs|cjs|jsx|py)$/,
  /\/_archive\//,
];

const SCANNED_EXTS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".svelte"];

function isAllowed(rel) {
  for (const p of ALLOWED_PATH_PATTERNS) if (p.test("/" + rel)) return true;
  for (const prefix of ALLOWED_PREFIXES) if (rel.startsWith(prefix)) return true;
  return false;
}

function isScanned(f) {
  return SCANNED_EXTS.some((e) => f.endsWith(e));
}

function hasProjectionMarker(content) {
  return /(?:\/\/|#)\s*kotoba-datomic-projection\b/.test(content);
}

function isNestedRepoRoot(dir) {
  // A populated git-submodule working tree carries a `.git` FILE (gitlink) at
  // its root. Its content belongs to another repository with its own gates
  // (e.g. 40-engine/kotoba, 40-engine/kami-engine), and the monorepo tracks
  // only the pointer — scanning it would make the audit verdict depend on
  // whether the submodule happens to be populated in this checkout
  // (non-deterministic across machines/worktrees; the frozen allowlist holds
  // zero submodule entries).
  try {
    return statSync(path.join(dir, ".git")).isFile();
  } catch {
    return false;
  }
}

function* walk(dir) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === "node_modules" || e.name === ".git" || e.name === "_archive") continue;
      if (isNestedRepoRoot(full)) continue;
      yield* walk(full);
    } else if (e.isFile() && isScanned(e.name)) {
      yield full;
    }
  }
}

function violatingFiles() {
  const out = [];
  for (const root of SCAN_ROOTS) {
    const abs = path.join(REPO_ROOT, root);
    if (!existsSync(abs)) continue;
    for (const full of walk(abs)) {
      const rel = path.relative(REPO_ROOT, full);
      if (isAllowed(rel)) continue;
      let content;
      try {
        content = readFileSync(full, "utf8");
      } catch {
        continue;
      }
      if (hasProjectionMarker(content)) continue; // ADR-2605231500 projection allowance
      if (STORAGE_PATTERNS.some((p) => p.test(content))) out.push(rel);
    }
  }
  return out.sort();
}

function loadAllowlist() {
  if (!existsSync(ALLOWLIST_PATH)) return { files: [] };
  return JSON.parse(readFileSync(ALLOWLIST_PATH, "utf8"));
}

const mode = process.argv.includes("--write") ? "write" : "audit";
const current = violatingFiles();

if (mode === "write") {
  const payload = {
    _comment:
      "Frozen legacy substrate-boundary (storage) violators — ADR-2606071800. " +
      "SHRINK-ONLY: remove a path once migrated to kotoba-kqe; never add new paths. " +
      "Regenerate with `node 70-tools/scripts/lint/substrate-remediation-audit.mjs --write` " +
      "ONLY to seed or after review. CI runs `--audit`.",
    adr: "2606071800",
    count: current.length,
    files: current,
  };
  writeFileSync(ALLOWLIST_PATH, JSON.stringify(payload, null, 2) + "\n");
  console.log(`wrote ${ALLOWLIST_PATH} with ${current.length} frozen legacy files`);
  process.exit(0);
}

// audit mode
const allow = new Set(loadAllowlist().files);
const newDebt = current.filter((f) => !allow.has(f));
const graduated = [...allow].filter((f) => !current.includes(f)).sort();

if (graduated.length > 0) {
  console.warn(`ℹ ${graduated.length} allowlisted file(s) no longer violate — remove from the frozen list (shrink-only):`);
  for (const f of graduated) console.warn(`    - ${f}`);
  console.warn("");
}

if (newDebt.length > 0) {
  console.error(`✘ substrate-remediation-audit: ${newDebt.length} NEW storage-boundary violation(s) not on the frozen allowlist (ADR-2606071800).`);
  console.error("  New code must use kotoba-kqe, not RisingWave/Hyperdrive/Kysely. Do NOT add these to the allowlist.");
  console.error("");
  for (const f of newDebt) console.error(`    ${f}`);
  process.exit(1);
}

console.log(`✔ substrate-remediation-audit: no new debt. ${current.length} frozen legacy file(s) remain (target: 0).`);
process.exit(0);

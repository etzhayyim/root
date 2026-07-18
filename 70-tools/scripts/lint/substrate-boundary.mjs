#!/usr/bin/env node
/**
 * substrate-boundary lint — enforce ADR-2605172000 + ADR-2605172100.
 *
 * Pre-commit gate that blocks new direct imports of:
 *   - centralised storage clients (RisingWave / Postgres / Kysely / …)
 *   - fiat payment processors (Stripe / PayPal / Square / …)
 *   - substrate clients that must go through @etzhayyim/sdk
 *     (@atproto/api / viem / @noble/ciphers / @signalapp/libsignal-client / …)
 *
 * The allowlist below carves out the canonical SDK seam and the
 * substrate infrastructure components that have a legitimate reason to
 * use the raw clients (mst-projector, paymaster, anchor-cron, did-web
 * worker, the SDK itself).
 *
 * Storage rules additionally honor the **kotoba-datomic-projection** allowance
 * per ADR-2605231500: a storage import is permitted when
 *   (a) the matched line has `// kotoba-datomic-projection` (or `# ...`) within
 *       3 lines above or below it, OR
 *   (b) the file's containing directory (walking up to repo root) has a
 *       `kotoba-datomic-projection.edn` manifest.
 * Payment and substrate-client rules do NOT honor this allowance — projection
 * is a state-store concept only.
 *
 * Usage:
 *   node 70-tools/scripts/lint/substrate-boundary.mjs <file1> [<file2> …]
 *
 * Exit code 0 on success, 1 on violation. Lefthook receives the
 * staged_files list automatically; see lefthook.yml `substrate-boundary`.
 *
 * Authoritative ADR: 90-docs/adr/2605191648-substrate-boundary-lefthook.md
 * Projection ADR:    ADR-2605231500
 */
import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
if (args.length === 0) {
  // No files passed — that's a successful no-op (lefthook may invoke
  // with an empty staged_files list on a no-op commit).
  process.exit(0);
}

/** Path prefixes that are allowed to import substrate clients directly.
 *  Anything else under `20-actors/` / `60-apps/` / `50-infra/` MUST go
 *  through `@etzhayyim/sdk`. */
const allowedPrefixes = [
  "orgs/etzhayyim/com-etzhayyim-sdk/",                  // the canonical seam
  "50-infra/etzhayyim-sdk-checkpointer/",      // sidecar wrapping the SDK
  "50-infra/mst-projector/",                   // substrate component
  "50-infra/anchor-cron/",                     // L2 anchor, uses viem
  "50-infra/etzhayyim-paymaster/",             // Solidity, but allow
  "50-infra/etzhayyim-membership-contract/",   // Solidity
  "50-infra/etzhayyim-chain-contracts/",       // Solidity
  "50-infra/etzhayyim-did-web/",               // CF Worker
  "50-infra/etzhayyim-pds-did-web/",           // CF Worker
  "50-infra/cloudflare/",                      // CF Workers stack
  "50-infra/vultr/",                           // etzhayyim.com legacy (ADR-2605191346 §2)
  "50-infra/l2-anchor-contract/",              // Solidity
  // graph-schema is the canonical home for migrations against the
  // RisingWave/Postgres-wire substrate. Kysely is the migration
  // framework (see `30-graph/graph-schema/CLAUDE.md` §Current Workflow);
  // Alembic is the SQLAlchemy successor for new DDL. These directories
  // import the substrate by definition — the lint should not flag
  // them. Source files under `30-graph/graph-schema/src/` still go
  // through the seam since they're consumed by app code.
  "30-graph/graph-schema/migrations/",         // Kysely TS migrations (historical)
  "30-graph/graph-schema/alembic/",            // Alembic SQLAlchemy migrations
  "30-graph/graph-schema/sql_migrations/",     // raw SQL bodies for Alembic
  "30-graph/graph-schema/sqlmesh/",            // SQLMesh derived views/materializations
  "30-graph/graph-schema/scripts/",            // one-shot DDL/INSERT apply scripts (same substrate-migration category)
  // Operator-only CLIs that bootstrap the substrate. They live in 70-tools/
  // and are run from a developer machine, never deployed. Same category
  // as 50-infra/mst-projector/emit.ts which uses @atproto/api directly.
  "70-tools/seed-post/",                       // ADR-2605231902 seed CLI
  // Tests + archives.
  "_archive/",
  "60-apps/etzhayyim-project-ameno/appview/etzhayyim-wasm-ameno-d94d27cb/_svelte/", // vite build output
  "60-apps/etzhayyim-project-bpmn/appview/etzhayyim-wasm-bpmn-bx7qm9p4/", // migrated BPMN substrate component; direct Hyperdrive writer tracked by ADR-2605181400
];

/** Path patterns that are always allowed regardless of import content. */
const allowedPathPatterns = [
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
  /\.example\.(ts|tsx|js|mjs|cjs|jsx|py|md|json|yaml|yml)$/,
];

/** File extensions we actually scan. */
const scannedExts = [
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".mjs",
  ".cjs",
  ".py",
  ".svelte",
];

/** ADR-2605172000 — centralised state substrate is prohibited. */
const storagePatterns = [
  { pattern: /from\s+["']kysely["']/, hint: "Kysely (use @etzhayyim/sdk read/write)" },
  { pattern: /from\s+["']@kysely\//, hint: "Kysely plugin" },
  { pattern: /from\s+["']pg["']/, hint: "node-postgres" },
  { pattern: /from\s+["']postgres["']/, hint: "postgres.js" },
  { pattern: /from\s+["']mysql2?["']/, hint: "mysql client" },
  { pattern: /from\s+["']mongodb["']/, hint: "MongoDB client" },
  { pattern: /from\s+["']risingwave["']/, hint: "RisingWave client" },
  { pattern: /from\s+["']@risingwavelabs\//, hint: "@risingwavelabs/*" },
  { pattern: /^import\s+psycopg(2)?(\s|$)/m, hint: "psycopg (Postgres)" },
  { pattern: /^from\s+psycopg(2)?\s+import/m, hint: "psycopg (Postgres)" },
  { pattern: /^import\s+pg8000(\s|$)/m, hint: "pg8000 (Postgres)" },
];

/** ADR-2605172100 — fiat payment processors are prohibited. */
const paymentPatterns = [
  { pattern: /from\s+["']stripe["']/, hint: "Stripe SDK" },
  { pattern: /from\s+["']@stripe\//, hint: "@stripe/*" },
  { pattern: /from\s+["']paypal-rest-sdk["']/, hint: "PayPal SDK" },
  { pattern: /from\s+["']@paypal\//, hint: "@paypal/*" },
  { pattern: /from\s+["']square["']/, hint: "Square SDK" },
  { pattern: /from\s+["']razorpay["']/, hint: "Razorpay SDK" },
  { pattern: /from\s+["']braintree["']/, hint: "Braintree SDK" },
  { pattern: /from\s+["']@braintree\//, hint: "@braintree/*" },
  { pattern: /from\s+["']@adyen\//, hint: "@adyen/*" },
  { pattern: /^import\s+stripe(\s|$)/m, hint: "stripe (Python)" },
];

/** ADR-2605172000 §SDK-seam — substrate clients must go through @etzhayyim/sdk. */
const substrateClientPatterns = [
  { pattern: /from\s+["']@atproto\/api["']/, hint: "@atproto/api (use @etzhayyim/sdk/pds)" },
  { pattern: /from\s+["']viem["']/, hint: "viem (use @etzhayyim/sdk/l2)" },
  { pattern: /from\s+["']@noble\/ciphers["']/, hint: "@noble/ciphers (use @etzhayyim/sdk/crypto)" },
  { pattern: /from\s+["']@signalapp\/libsignal-client["']/, hint: "libsignal-client (use @etzhayyim/sdk/signal)" },
  { pattern: /from\s+["']ipfs-http-client["']/, hint: "ipfs-http-client (use @etzhayyim/sdk/ipfs)" },
  { pattern: /from\s+["']helia["']/, hint: "helia (use @etzhayyim/sdk/ipfs)" },
];

const allRules = [
  { kind: "storage substrate (ADR-2605172000)", rules: storagePatterns },
  { kind: "payment substrate (ADR-2605172100)", rules: paymentPatterns },
  { kind: "substrate client seam (ADR-2605172000 §SDK seam)", rules: substrateClientPatterns },
];

function isAllowed(filePath) {
  const normal = filePath.replace(/^\.\//, "");
  for (const pat of allowedPathPatterns) if (pat.test(normal)) return true;
  for (const prefix of allowedPrefixes) if (normal.startsWith(prefix)) return true;
  return false;
}

function isScannedExtension(filePath) {
  return scannedExts.some((ext) => filePath.endsWith(ext));
}

// ─── kotoba-datomic-projection allowance (ADR-2605231500) ────────────────

/** Matches projection markers in TS/JS/Python comments.
 *  Trailing free-form text (e.g., rebuild path reference) is allowed. */
const PROJECTION_LINE_MARKER = /(?:\/\/|#)\s*kotoba-datomic-projection\b/;

/** Within 3 lines above or below the match, is there a projection marker? */
function hasProjectionLineMarker(content, matchLineNumber) {
  const lines = content.split("\n");
  const start = Math.max(0, matchLineNumber - 1 - 3);
  const end = Math.min(lines.length, matchLineNumber - 1 + 4);
  for (let i = start; i < end; i++) {
    if (PROJECTION_LINE_MARKER.test(lines[i])) return true;
  }
  return false;
}

/** Cache: directory -> bool (has projection manifest in self or any ancestor). */
const projectionManifestCache = new Map();

/** Walk up from the file's directory looking for a projection manifest.
 *  Stops at process.cwd() (assumed repo root for the lefthook invocation) or
 *  after 10 levels — whichever first. */
function hasProjectionManifest(filePath) {
  const repoRoot = process.cwd();
  let dir = path.dirname(path.resolve(filePath));
  const visited = [];
  for (let i = 0; i < 10; i++) {
    if (projectionManifestCache.has(dir)) {
      const cached = projectionManifestCache.get(dir);
      for (const v of visited) projectionManifestCache.set(v, cached);
      return cached;
    }
    visited.push(dir);
    if (existsSync(path.join(dir, "kotoba-datomic-projection.edn"))) {
      for (const v of visited) projectionManifestCache.set(v, true);
      return true;
    }
    if (dir === repoRoot) break;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  for (const v of visited) projectionManifestCache.set(v, false);
  return false;
}

function isStorageRule(groupKind) {
  return groupKind.startsWith("storage substrate");
}

// ─── frozen legacy allowlist (ADR-2606071800) ────────────────────────────
// Pre-guard legacy files that already import the storage substrate directly are
// grandfathered: a STORAGE violation in a frozen file is a warning (tracked debt being
// migrated to kotoba-kqe), not a hard failure — so unrelated edits to a legacy file are
// not blocked. New files (not on the list) are still blocked, and the shrink-only ratchet
// lives in substrate-remediation-audit.mjs (pre-push). The allowance covers storage rules
// ONLY — payment + seam rules are never grandfathered.
const FROZEN_ALLOWLIST_PATH = path.join(
  process.cwd(),
  "70-tools/scripts/lint/substrate-frozen-allowlist.json",
);
let frozenStorageFiles = new Set();
try {
  if (existsSync(FROZEN_ALLOWLIST_PATH)) {
    const j = JSON.parse(readFileSync(FROZEN_ALLOWLIST_PATH, "utf8"));
    frozenStorageFiles = new Set((j.files ?? []).map((f) => f.replace(/^\.\//, "")));
  }
} catch {
  /* missing/corrupt allowlist → behave as before (no grandfathering) */
}

function isFrozenStorageLegacy(filePath) {
  return frozenStorageFiles.has(filePath.replace(/^\.\//, ""));
}

const violations = [];
const grandfatheredWarnings = [];

for (const file of args) {
  if (!file) continue;
  if (!isScannedExtension(file)) continue;
  if (isAllowed(file)) continue;
  let content;
  try {
    const s = statSync(file);
    if (!s.isFile()) continue;
    content = readFileSync(file, "utf8");
  } catch {
    continue; // file vanished between stage and lint
  }

  // For storage rules we may also need the directory-level projection
  // manifest check; pre-compute once per file (cached across files).
  let fileHasManifest = null;

  for (const group of allRules) {
    for (const rule of group.rules) {
      const m = content.match(rule.pattern);
      if (!m) continue;
      // Find the line number for nicer reporting.
      const upToMatch = content.slice(0, m.index ?? 0);
      const line = upToMatch.split("\n").length;

      // ADR-2605231500: storage imports are allowed inside a projection cache.
      if (isStorageRule(group.kind)) {
        if (hasProjectionLineMarker(content, line)) continue;
        if (fileHasManifest === null) fileHasManifest = hasProjectionManifest(file);
        if (fileHasManifest) continue;
        // ADR-2606071800: grandfather frozen legacy storage violators → warn, don't block.
        if (isFrozenStorageLegacy(file)) {
          grandfatheredWarnings.push({ file, line, hint: rule.hint });
          continue;
        }
      }

      violations.push({
        file,
        line,
        kind: group.kind,
        hint: rule.hint,
        snippet: (m[0] ?? "").trim(),
      });
    }
  }
}

if (violations.length > 0) {
  console.error("✘ substrate-boundary lint failed — direct imports detected outside the SDK seam.");
  console.error("  These are prohibited by ADR-2605172000 / ADR-2605172100.");
  console.error("");
  for (const v of violations) {
    console.error(`  ${v.file}:${v.line}  ${v.kind}`);
    console.error(`    pattern: ${v.snippet}`);
    console.error(`    fix:     route through @etzhayyim/sdk (${v.hint})`);
    console.error("");
  }
  console.error("If this file genuinely IS a substrate component, add its");
  console.error("path prefix to `allowedPrefixes` in this script with a code");
  console.error("comment justifying the exception.");
  console.error("");
  console.error("If this is a kotoba-datomic-projection (derived read path, ADR-2605231500):");
  console.error("  - mark the line with `// kotoba-datomic-projection: <runbook ref>`");
  console.error("    (or `# kotoba-datomic-projection: ...` for Python), OR");
  console.error("  - add `kotoba-datomic-projection.edn` to the containing directory");
  console.error("    (template in ADR-2605231500 marking convention).");
  console.error("  Note: projection allowance covers storage rules only — payment");
  console.error("  and substrate-client seam rules are not projection-allowable.");
  process.exit(1);
}

if (grandfatheredWarnings.length > 0) {
  console.warn(
    `ℹ substrate-boundary: ${grandfatheredWarnings.length} staged frozen-legacy storage import(s) (ADR-2606071800 — tracked debt, not blocking):`,
  );
  for (const w of grandfatheredWarnings) {
    console.warn(`    ${w.file}:${w.line}  (${w.hint}) — migrate to kotoba-kqe + remove from frozen allowlist`);
  }
}

process.exit(0);

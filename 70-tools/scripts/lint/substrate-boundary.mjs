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
 * Usage:
 *   node 70-tools/scripts/lint/substrate-boundary.mjs <file1> [<file2> …]
 *
 * Exit code 0 on success, 1 on violation. Lefthook receives the
 * staged_files list automatically; see lefthook.yml `substrate-boundary`.
 *
 * Authoritative ADR: 90-docs/adr/2605191648-substrate-boundary-lefthook.md
 */
import { readFileSync, statSync } from "node:fs";

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
  "20-actors/etzhayyim-sdk/",                  // the canonical seam
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
  // Tests + archives.
  "_archive/",
  "60-apps/ai-gftd-project-ameno/appview/ai-gftd-wasm-ameno-d94d27cb/_svelte/", // vite build output
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

const violations = [];

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

  for (const group of allRules) {
    for (const rule of group.rules) {
      const m = content.match(rule.pattern);
      if (m) {
        // Find the line number for nicer reporting.
        const upToMatch = content.slice(0, m.index ?? 0);
        const line = upToMatch.split("\n").length;
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
  process.exit(1);
}

process.exit(0);

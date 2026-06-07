#!/usr/bin/env node
// no-external-purchase-purpose.mjs — lefthook pre-commit hook.
//
// Enforces ADR-2605211900 §D2 (yorishiro lexicon x-charter-purpose) +
// ADR-2605192115 §4 (no external write-side purchase / subscription /
// tip on external substrate calls).
//
// Scope: 00-contracts/lexicons/ai/etzhayyim/yorishiro/**/*.json
//
// A yorishiro lexicon with x-yorishiro-external: true must declare
// x-charter-purpose as a non-empty array whose values are all in the
// non-profit-only allow list:
//
//   ["donation", "kisha", "grant", "tithe", "escrow-refund"]
//
// Forbidden values (cause non-zero exit and refuse the commit):
//
//   "subscription", "purchase", "tip"          — bare third-party
//   "internal-purchase", "internal-subscription", "internal-promo"
//                                              — SBT↔SBT carveout (these
//                                                must NOT appear on
//                                                yorishiro lexicons; they
//                                                belong on internal apps)
//
// Run:
//   node 70-tools/scripts/lint/no-external-purchase-purpose.mjs <files>
// (lefthook passes {staged_files}; manual invocation can pass any list)

import { readFileSync } from "node:fs";

const ALLOW = new Set(["donation", "kisha", "grant", "tithe", "escrow-refund"]);
const FORBID = new Set([
  "subscription",
  "purchase",
  "tip",
  "internal-purchase",
  "internal-subscription",
  "internal-promo",
]);

const YORISHIRO_PREFIX = "00-contracts/lexicons/ai/etzhayyim/yorishiro/";

const files = process.argv.slice(2).filter((f) => f.includes(YORISHIRO_PREFIX) && f.endsWith(".json"));
if (files.length === 0) process.exit(0);

let violations = 0;
for (const file of files) {
  let lex;
  try {
    lex = JSON.parse(readFileSync(file, "utf-8"));
  } catch (err) {
    violations++;
    console.error(`✘ ${file}: parse error — ${err.message}`);
    continue;
  }

  const nsid = lex.id ?? "<missing>";
  const main = lex?.defs?.main;
  if (!main || typeof main !== "object") {
    violations++;
    console.error(`✘ ${file} [${nsid}]: defs.main missing`);
    continue;
  }

  if (main["x-yorishiro-external"] !== true) {
    violations++;
    console.error(`✘ ${file} [${nsid}]: x-yorishiro-external must be true`);
  }

  const purposes = main["x-charter-purpose"];
  if (!Array.isArray(purposes) || purposes.length === 0) {
    violations++;
    console.error(`✘ ${file} [${nsid}]: x-charter-purpose missing or empty`);
    continue;
  }

  for (const p of purposes) {
    if (FORBID.has(p)) {
      violations++;
      console.error(
        `✘ ${file} [${nsid}]: x-charter-purpose includes forbidden value '${p}' ` +
          `(ADR-2605192115 §4 — external write-side substrate calls cannot carry this purpose)`,
      );
    } else if (!ALLOW.has(p)) {
      violations++;
      console.error(
        `✘ ${file} [${nsid}]: x-charter-purpose includes unknown value '${p}'. ` +
          `Allowed: ${[...ALLOW].join(", ")}`,
      );
    }
  }
}

if (violations > 0) {
  console.error("");
  console.error(`no-external-purchase-purpose: ${violations} violation(s) across ${files.length} file(s).`);
  console.error("  Per ADR-2605211900 D2: external yorishiro lexicons must declare a non-profit");
  console.error("  Charter purpose (donation / kisha / grant / tithe / escrow-refund). SBT↔SBT");
  console.error("  internal-* carveouts belong on ordinary kotodama actors, not yorishiri.");
  process.exit(1);
}

process.exit(0);

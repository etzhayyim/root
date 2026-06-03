#!/usr/bin/env node
/**
 * no-purchase-purpose lint — enforce ADR-2605192115 §1.3 + §3.3 + ADR-2605192130.
 *
 * Pre-commit gate that blocks the legacy payment.sent.purpose enum values:
 *   - "subscription" / "purchase" / "tip" / "refund" / "offering" / "split"
 * (removed in v0 → v1 narrow per ADR-2605192115 §1.3).
 *
 * Allowed v1 purposes:
 *   external SBT→external: "donation" / "kisha" / "grant" / "tithe" / "escrow-refund"
 *   internal SBT↔SBT      : also "internal-purchase" / "internal-subscription" /
 *                                "internal-promo" (per §3.3)
 *
 * Detects literal `purpose: "X"` / `purpose: 'X'` and JSON enum entries.
 *
 * Exit code 0 on success, 1 on violation.
 *
 * Authoritative ADR: 90-docs/adr/2605192115-etzhayyim-non-profit-donation-only-no-ads.md
 */
import { readFileSync, statSync } from "node:fs";

const args = process.argv.slice(2);
if (args.length === 0) process.exit(0);

const FORBIDDEN_PURPOSES = ["subscription", "purchase", "tip", "refund", "offering", "split"];

/** Files / paths exempt from this check. */
const PATH_EXEMPTIONS = [
  /node_modules\//,
  /\.git\//,
  /(^|\/)target\//,
  /(^|\/)dist\//,
  /(^|\/)build\//,
  /(^|\/)coverage\//,
  /^_archive\//,
  // Lint scripts (this file)
  /^70-tools\/scripts\/lint\/no-purchase-purpose\.mjs$/,
  // ADR documents that necessarily reference the legacy enum
  /^90-docs\/adr\/2605192115/,
  /^90-docs\/adr\/2605192130/,
  /^90-docs\/adr\/2605172100/,
  /^CLAUDE\.md$/,
  // The Lexicon file itself describes the v0→v1 migration in its description
  /^00-contracts\/lexicons\/ai\/etzhayyim\/apps\/payment\/sent\.json$/,
];

let violations = 0;

for (const file of args) {
  if (PATH_EXEMPTIONS.some((re) => re.test(file))) continue;
  let content;
  try {
    if (!statSync(file).isFile()) continue;
    content = readFileSync(file, "utf8");
  } catch {
    continue;
  }

  const lines = content.split("\n");
  lines.forEach((line, idx) => {
    const stripped = line.replace(/\s*(\/\/|#).*$/, "");
    for (const p of FORBIDDEN_PURPOSES) {
      // literal `purpose: "X"` or `purpose: 'X'`
      const pat1 = new RegExp(`\\bpurpose\\s*[:=]\\s*["']${p}["']`);
      // JSON enum: `"purpose": "X"` (object key form)
      const pat2 = new RegExp(`"purpose"\\s*:\\s*"${p}"`);
      if (pat1.test(stripped) || pat2.test(stripped)) {
        console.error(
          `${file}:${idx + 1}: forbidden payment purpose "${p}" (ADR-2605192115 §1.3; removed in v0→v1)`,
        );
        violations++;
      }
    }
  });
}

if (violations > 0) {
  console.error("");
  console.error(`✘ no-purchase-purpose: ${violations} violation(s).`);
  console.error("  Per ADR-2605192115 §1.3 + ADR-2605192130 (10% Tithe Redistribution).");
  console.error("  Allowed external purposes:");
  console.error("    donation / kisha / grant / tithe / escrow-refund");
  console.error("  Allowed internal carve-out (SBT↔SBT only):");
  console.error("    internal-purchase / internal-subscription / internal-promo");
  process.exit(1);
}
process.exit(0);

#!/usr/bin/env node
/**
 * paywall-warn lint — surface paywall patterns for ADR-2605192115 §1.1 review.
 *
 * Non-blocking warning. Surfaces:
 *   - "paywall"
 *   - "premium_only" / "premiumOnly"
 *   - "pro_tier" / "proTier"
 *   - "subscription_required" / "subscriptionRequired"
 *   - "access_denied_unpaid" / "accessDeniedUnpaid"
 *
 * These are not auto-blocked (legitimate uses exist — e.g., describing
 * legacy systems, ADRs documenting prohibition). Council Lv6+ reviews case
 * by case per ADR-2605192115 §2.3.
 *
 * Always exits 0; output is informational. Lefthook can use `warn` keyword
 * or pipe to stderr.
 */
import { readFileSync, statSync } from "node:fs";

const args = process.argv.slice(2);
if (args.length === 0) process.exit(0);

const WARN_PATTERNS = [
  /\bpaywall\b/i,
  /\bpremium_only\b/i,
  /\bpremiumOnly\b/,
  /\bpro_tier\b/i,
  /\bproTier\b/,
  /\bsubscription_required\b/i,
  /\bsubscriptionRequired\b/,
  /\baccess_denied_unpaid\b/i,
  /\baccessDeniedUnpaid\b/,
];

const PATH_EXEMPTIONS = [
  /node_modules\//,
  /\.git\//,
  /(^|\/)target\//,
  /(^|\/)dist\//,
  /(^|\/)build\//,
  /(^|\/)coverage\//,
  /^_archive\//,
  /^70-tools\/scripts\/lint\/paywall-warn\.mjs$/,
  /^90-docs\/adr\/2605192115/,
  /^CLAUDE\.md$/,
];

let warnings = 0;

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
    for (const pat of WARN_PATTERNS) {
      if (pat.test(line)) {
        console.warn(
          `${file}:${idx + 1}: paywall-pattern detected (ADR-2605192115 §2.3 — Council review)`,
        );
        warnings++;
        break;  // one warning per line
      }
    }
  });
}

if (warnings > 0) {
  console.warn("");
  console.warn(`⚠ paywall-warn: ${warnings} warning(s).`);
  console.warn("  Per ADR-2605192115 §2.3. Council Lv6+ evaluates case-by-case.");
  console.warn("  Not blocking commit; documenting for review.");
}
process.exit(0);

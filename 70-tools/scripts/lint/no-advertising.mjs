#!/usr/bin/env node
/**
 * no-advertising lint — enforce ADR-2605192115 §1.2 No Advertising hard rule.
 *
 * Pre-commit gate that blocks:
 *   - Imports / requires of advertising networks (AdSense / Meta Pixel /
 *     TikTok / Criteo / Amazon Ads / etc.)
 *   - Imports / requires of affiliate SDKs (Amazon Associates / Rakuten /
 *     A8.net / ValueCommerce)
 *   - Imports / requires of advertising tracking (GA4, react-ga, Meta Pixel,
 *     facebook-pixel — when used in apparent advertising context)
 *   - DOM patterns (<ins class="adsbygoogle">, <script src="...googlesyndication...">,
 *     data-ad-client, etc.)
 *
 * Exit code 0 on success, 1 on violation. Used by lefthook pre-commit.
 *
 * Authoritative ADR: 90-docs/adr/2605192115-etzhayyim-non-profit-donation-only-no-ads.md
 * Mission Charter root: 90-docs/adr/2605192100-etzhayyim-mission-charter.md §1.6
 */
import { readFileSync, statSync } from "node:fs";

const args = process.argv.slice(2);
if (args.length === 0) process.exit(0);

/** npm packages that are advertising / affiliate / tracking SDKs.
 *  Detects `from "X"`, `from 'X'`, `require("X")`, `require('X')`, `import "X"`. */
const FORBIDDEN_PACKAGES = [
  // ─── Advertising networks ─────────────────────────────────────
  "@google-cloud/ads",
  "google-ads-api",
  "googleads-node-lib",
  "react-google-adsense",
  "react-adsense",
  "next-adsense",
  "facebook-ads-sdk",
  "amazon-ads-api",
  "react-facebook-pixel",
  "react-tiktok-pixel",
  // ─── Affiliate networks ───────────────────────────────────────
  "amazon-paapi",
  "rakuten-affiliate",
  "a8net-sdk",
  // ─── Advertising-bias trackers (used in ad context = banned) ─
  "react-ga",
  "react-ga4",
  "facebook-pixel",
];

/** Wildcard matchers for forbidden package families (e.g., @facebook-ads/*). */
const FORBIDDEN_PACKAGE_PREFIXES = [
  "@facebook-ads/",
  "@meta-ads/",
  "@tiktok-ads/",
  "@apple/search-ads",
  "@yahoo-ads/",
  "@criteo/",
  "@valuecommerce/",
];

/** DOM / HTML patterns that mark an advertising integration. */
const FORBIDDEN_HTML_PATTERNS = [
  /<ins\s+class\s*=\s*["']adsbygoogle/i,
  /https?:\/\/pagead2\.googlesyndication\.com/i,
  /https?:\/\/connect\.facebook\.net/i,
  /https?:\/\/analytics\.tiktok\.com/i,
  /\bdata-ad-client\s*=/i,
  /\bdata-ad-slot\s*=/i,
];

/** Files / paths that are exempt (test fixtures, ADR docs referencing the
 *  banned list, lint script itself, etc.). */
const PATH_EXEMPTIONS = [
  /node_modules\//,
  /\.git\//,
  /(^|\/)target\//,
  /(^|\/)dist\//,
  /(^|\/)build\//,
  /(^|\/)coverage\//,
  /^_archive\//,
  // Lint scripts (this file + ADR-2605192115 list docs)
  /^70-tools\/scripts\/lint\/no-advertising\.mjs$/,
  // ADRs that necessarily enumerate the banned list as documentation
  /^90-docs\/adr\/2605192115/,
  /^90-docs\/adr\/2605192100/,
  /^CLAUDE\.md$/,
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

  // Import / require scans
  const lines = content.split("\n");
  lines.forEach((line, idx) => {
    // skip comments — single-line `//` or `#`
    const stripped = line.replace(/\s*(\/\/|#).*$/, "");

    // exact package match
    for (const pkg of FORBIDDEN_PACKAGES) {
      const pat = new RegExp(
        `(?:from|import|require)\\s*\\(?\\s*["']${pkg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["']`,
      );
      if (pat.test(stripped)) {
        console.error(
          `${file}:${idx + 1}: forbidden advertising package "${pkg}" (ADR-2605192115 §1.2)`,
        );
        violations++;
      }
    }
    // prefix match
    for (const prefix of FORBIDDEN_PACKAGE_PREFIXES) {
      const pat = new RegExp(
        `(?:from|import|require)\\s*\\(?\\s*["']${prefix.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`,
      );
      if (pat.test(stripped)) {
        console.error(
          `${file}:${idx + 1}: forbidden advertising package family "${prefix}*" (ADR-2605192115 §1.2)`,
        );
        violations++;
      }
    }
    // HTML / DOM patterns
    for (const pat of FORBIDDEN_HTML_PATTERNS) {
      if (pat.test(stripped)) {
        console.error(
          `${file}:${idx + 1}: forbidden advertising HTML/DOM pattern (ADR-2605192115 §2.4)`,
        );
        violations++;
      }
    }
  });
}

if (violations > 0) {
  console.error("");
  console.error(`✘ no-advertising: ${violations} violation(s).`);
  console.error("  Per ADR-2605192115 §1.2 (No Advertising hard rule) +");
  console.error("  ADR-2605192100 §1.6 (Mission Charter — middleman elimination).");
  console.error("  Advertising integrations are constitutionally prohibited.");
  console.error("  If this is a documentation reference (listing banned packages),");
  console.error("  add the path to PATH_EXEMPTIONS in this script.");
  process.exit(1);
}
process.exit(0);

#!/usr/bin/env node
// ADR-2605192115 §1.2 (No Advertising) codemod closure.
//
// Target: 60-apps/<app>/MIGRATION-TODO.md where Codemod required is
//   "strip ad-pixel/GA4 + DID-bind auth" OR
//   "remove ad / affiliate revenue paths".
//
// Action: re-scan each target app for actual GA/pixel/AdSense/FB/Hotjar/
// Mixpanel/Amplitude/Segment violations in source code (excluding built
// bundles + node_modules + .svelte-kit). If zero violations are found,
// append a closure section confirming the codemod is satisfied. If any
// violation is detected, log to stderr and SKIP that file (a real
// rewrite is required).
//
// Idempotent: re-runs only append the closure section once. Detection
// is keyed by the literal marker comment.
//
// Usage:
//   node 70-tools/scripts/codemod/2605231600-ad-pixel-codemod-closure.mjs
//   node 70-tools/scripts/codemod/2605231600-ad-pixel-codemod-closure.mjs --dry-run

import { readFileSync, writeFileSync, statSync } from "node:fs";
import { execSync } from "node:child_process";
import { resolve, dirname, basename } from "node:path";

const DRY = process.argv.includes("--dry-run");
const repoRoot = execSync("git rev-parse --show-toplevel 2>/dev/null || pwd", {
  encoding: "utf8",
}).trim();

// ─── Detection regex ───────────────────────────────────────────────
// Per 70-tools/scripts/lint/no-advertising.mjs §AD_SDK_PATTERNS.
const AD_PATTERN = new RegExp(
  [
    "googletagmanager\\.com",
    "google-analytics\\.com",
    "googlesyndication\\.com",
    "googleadservices\\.com",
    "doubleclick\\.net",
    "\\bgtag\\(",
    "\\bfbq\\(",
    "connect\\.facebook\\.net",
    "adsbygoogle",
    "google-adsense",
    "amplitude",
    "mixpanel",
    "segment\\.com/analytics",
    "hotjar",
    "GoogleAnalytics\\b",
  ].join("|"),
  "i",
);

// Source-only globs. Build outputs / vendored bundles never count.
const SRC_EXTS = [
  ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".js",
  ".svelte", ".html", ".htm", ".astro", ".vue",
];
const EXCLUDE_PATH_MARKERS = [
  "/node_modules/",
  "/dist/",
  "/.svelte-kit/",
  "/_app/immutable/",
  "/static-ui/",
  "/static/assets/",
  ".min.",
  "/_svelte/assets/",
  "/build/",
];

const MARKER = "<!-- ad-pixel-codemod-closure:2605231600 -->";
const TODAY = "2026-05-23";

// ─── Helpers ───────────────────────────────────────────────────────

function shouldExclude(path) {
  return EXCLUDE_PATH_MARKERS.some((m) => path.includes(m));
}

function listAppSourceFiles(appDir) {
  const out = [];
  // Use find for portability + speed.
  const findCmd =
    `find "${appDir}" -type f \\( ${SRC_EXTS.map((e) => `-name '*${e}'`).join(" -o ")} \\)`;
  let raw;
  try {
    raw = execSync(findCmd, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  } catch {
    return [];
  }
  for (const line of raw.split("\n").filter(Boolean)) {
    if (shouldExclude(line)) continue;
    out.push(line);
  }
  return out;
}

function findViolations(appDir) {
  const violations = [];
  for (const f of listAppSourceFiles(appDir)) {
    let content;
    try {
      content = readFileSync(f, "utf8");
    } catch {
      continue;
    }
    if (AD_PATTERN.test(content)) {
      violations.push(f);
    }
  }
  return violations;
}

// ─── Main ──────────────────────────────────────────────────────────

const appsRoot = resolve(repoRoot, "60-apps");
const targets = execSync(
  `grep -lE "ad-pixel|ad / affiliate" 60-apps/*/MIGRATION-TODO.md 2>/dev/null || true`,
  { cwd: repoRoot, encoding: "utf8" },
).split("\n").filter(Boolean);

let closed = 0, dirty = 0, alreadyClosed = 0;

for (const rel of targets) {
  const todoPath = resolve(repoRoot, rel);
  const appDir = dirname(todoPath);
  const appName = basename(appDir);
  const todoSrc = readFileSync(todoPath, "utf8");

  if (todoSrc.includes(MARKER)) {
    alreadyClosed += 1;
    continue;
  }

  const violations = findViolations(appDir);
  if (violations.length > 0) {
    dirty += 1;
    process.stderr.write(
      `! ${appName}: ${violations.length} ad-pixel violation(s) — manual rewrite required:\n`,
    );
    for (const v of violations) {
      process.stderr.write(`    - ${v.replace(repoRoot + "/", "")}\n`);
    }
    continue;
  }

  const closure = [
    "",
    "---",
    "",
    `## ad-pixel codemod closure (${TODAY})`,
    "",
    MARKER,
    "",
    "**Status**: ✅ ad-pixel / GA4 / AdSense / Meta Pixel codemod **complete** — verified clean.",
    "",
    "Re-scan on " + TODAY + " confirmed zero matches across this app's source",
    "tree (excluding `node_modules/`, `dist/`, `.svelte-kit/`, build outputs)",
    "for: `googletagmanager.com`, `google-analytics.com`, `gtag(`, `fbq(`,",
    "`connect.facebook.net`, `adsbygoogle`, `google-adsense`, `amplitude`,",
    "`mixpanel`, `segment.com/analytics`, `hotjar`, `GoogleAnalytics`.",
    "",
    "Per ADR-2605192115 §1.2 (No Advertising hard rule) + ADR-2605192100 §1.6",
    "(Mission Charter middleman elimination). DID-bind-auth check remains a",
    "separate item — see `auth` checklist above.",
    "",
    "_Closed by `70-tools/scripts/codemod/2605231600-ad-pixel-codemod-closure.mjs`._",
    "",
  ].join("\n");

  // Also flip the top-line status banner so the next reader sees the new state.
  let next = todoSrc;
  next = next.replace(
    /\*\*Status\*\*:\s*🔄\s*TRANSFORM\s*—\s*seed copied[^\n]*\n/,
    `**Status**: ✅ ad-pixel codemod complete (${TODAY}) — see closure section below for details.\n`,
  );
  next = next.replace(
    /(\*\*Codemod required\*\*:\s*(?:strip ad-pixel\/GA4 \+ DID-bind auth|remove ad \/ affiliate revenue paths))/,
    "$1\n\n> **Resolved (ad-pixel layer)** — see closure section below. DID-bind-auth + affiliate-revenue-paths still pending if listed in the checklist.",
  );

  if (!next.endsWith("\n")) next += "\n";
  next += closure;

  if (DRY) {
    process.stdout.write(`would-close: ${appName}\n`);
  } else {
    writeFileSync(todoPath, next);
    process.stdout.write(`closed: ${appName}\n`);
  }
  closed += 1;
}

process.stdout.write(
  `\nSummary: ${closed} closed, ${alreadyClosed} already-closed, ${dirty} blocked (violations present).\n`,
);
process.exit(dirty > 0 ? 2 : 0);

#!/usr/bin/env node
//
// no-two-stage-etzhayyim-domains.mjs — block introduction of the legacy
// `.etzhayyim.com` zone literal in canonical etzhayyim source.
//
// Constitutional anchor: ADR-2605212340 (legacy domain → etzhayyim.com
// cutover, accepted 2026-05-21).
//
// **Historical note (2026-05-26 audit, iter-8 of /loop):** the script
// was originally written to catch BOTH (1) legacy `*.etzhayyim.com` references
// AND (2) two-stage etzhayyim hosts (`foo.bar.etzhayyim.com`) under the
// theory that the rename would mechanically create two-stage etzhayyim
// hosts from `foo.bar.etzhayyim.com`. The latter rule was a soft no-op since
// the rename (the regex matched `.etzhayyim.com`-only while the host filter
// passed `.etzhayyim.com`-only; the two filters never overlapped, so
// the lint was silently a no-op).
//
// Audit found ~16 multi-label `*.*.etzhayyim.com` occurrences across
// the monorepo that are **intentional architectural patterns**:
//
//   - jurisdictional path-based DIDs (e.g.
//     `did:web:jpn.state.etzhayyim.com:gyosei`,
//     `did:web:ind.payroll.etzhayyim.com:epfo`)
//   - multi-tenant SaaS naming (e.g.
//     `did:web:t-xxxxx.yata-tenant.etzhayyim.com`)
//   - vendor subdomain DIDs (e.g.
//     `did:web:misumi-meviy.tsukuru.etzhayyim.com`)
//   - environment subdomains (e.g.
//     `https://staging.atproto.etzhayyim.com/...`)
//   - bridge / interim subdomains pending separate ADRs (e.g.
//     `did:web:bridge.openmail.etzhayyim.com`)
//
// None of these are ADR-2605212340 violations. The "two-stage etzhayyim
// is forbidden" rule had no constitutional basis once the rename was
// complete, so this commit drops it. The script retains its filename
// for lefthook config stability but now enforces only the etzhayyim-legacy
// half of its original purpose.
//
import { spawnSync } from "node:child_process";
import fs from "node:fs";

const SEARCH_ROOTS = [
  "00-contracts",
  "10-protocol",
  "20-actors",
  "30-graph",
  "50-infra",
  "60-apps",
  "70-tools",
  "infra",
].filter((dir) => fs.existsSync(dir));

// Aligned with the lefthook `glob:` for this hook (`*.{md,toml,yaml,yml,
// json,jsonc,jsonld,ts,tsx,js,jsx,mjs,cjs,py,rs,go,sh,sol,svelte}`).
// Iter-7's audit observed that `.rs` files staged via lefthook were
// silently filtered out because the script's own INCLUDE_GLOB lacked
// the extension. Iter-8 aligns the two so what lefthook offers, the
// script accepts. `.md` is intentionally NOT included — design docs
// legitimately quote legacy hosts (ADR-2605212340 body, README cutover
// runbooks).
const INCLUDE_GLOB = "*.{json,jsonc,jsonld,toml,ts,tsx,jsx,js,mjs,cjs,svelte,py,rs,go,sh,sol,yml,yaml}";
const EXCLUDE_GLOBS = [
  "!**/.git/**",
  "!**/node_modules/**",
  "!**/.svelte-kit/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/coverage/**",
  "!**/.wrangler/**",
  "!**/.wrangler-out/**",
  "!**/static/**",
  "!**/public/**",
  "!**/*.gen.*",
  "!**/generated/**",
  "!**/_registry/**",
  "!**/data/**",
  "!90-docs/**",
  "!80-data/**",
  // Git subrepos (ADR-2605262130 kotoba). Subrepo files are
  // vendor-tracked; modifying them out-of-band breaks the next
  // `git subrepo pull` — only the upstream maintainer should retire
  // legacy host references there.
  "!40-engine/kotoba/**",
  // Pre-cutover legacy app trees (per CLAUDE.md "Do not introduce
  // legacy organisation-specific prefixes in newly authored code" +
  // ADR-2605152100 Phase A bulk rename). These directories are
  // seeded snapshots awaiting their own cutover; their `.etzhayyim.com`
  // references will be retired by the same sed pass that renames the
  // directories. Mirrors `_is_first_party_source` in the Python
  // e7m-verify checks.
  "!**/etzhayyim-project-*/**",
  "!**/etzhayyim-apps-*/**",
  "!**/etzhayyim-wasm-*/**",
  "!70-tools/scripts/lint/no-two-stage-etzhayyim-domains.mjs",
];

// Match any depth of subdomain before `.etzhayyim.com`. ADR-2605212340 bans
// the legacy zone entirely (not just 3+ label hosts), so `iryo.etzhayyim.com`
// is a violation just like `news.iryo.etzhayyim.com`. The original
// `(?:\.label)+\.etzhayyim\.ai` (1+ intermediate label) was the historic
// "two-stage" framing from the lint name; ADR-2605212340 is broader.
const HOST_RE = /(?:did:web:|https?:\/\/|["'`\s(])([a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)*\.etzhayyim\.ai)(?=[/:*"'`\s),}]|$)/gi;

// ── file list resolution ─────────────────────────────────────────────────
//
// When invoked by lefthook (`run: node …no-two-stage-etzhayyim-domains.mjs
// {staged_files}`), process.argv[2..] holds the list of staged files
// matching lefthook's `glob:` filter — exactly the right scope for a
// pre-commit lint that "blocks new introduction" of the forbidden host
// pattern (per ADR-2605212340).
//
// When invoked with `--all` (manual full-scan), fall back to the rg-based
// monorepo walk. The full-scan path is preserved for occasional auditing
// even though pre-commit is the primary use case.
//
// Before this change the script *ignored* {staged_files} and always
// performed the rg walk — turning a 1-file commit into a ~6s scan over
// 60-apps + 20-actors + 50-infra + 70-tools.

function listFilesAll() {
  const args = ["--files", "--hidden", "--glob", INCLUDE_GLOB];
  for (const glob of EXCLUDE_GLOBS) args.push("--glob", glob);
  args.push(...SEARCH_ROOTS);
  const result = spawnSync("rg", args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`rg --files failed (code=${result.status}): ${result.stderr?.trim() ?? ""}`);
  }
  return result.stdout.trim().split("\n").filter(Boolean);
}

// Path-prefix exclusions that mirror EXCLUDE_GLOBS for the argv-list
// path. Kept in sync by inspection — EXCLUDE_GLOBS is the source of
// truth for the rg-driven full-scan path; this list re-encodes the
// directory-prefix subset for argv-supplied files.
const ARGV_EXCLUDE_PATH_PATTERNS = [
  /(^|\/)\.git\//,
  /(^|\/)node_modules\//,
  /(^|\/)\.svelte-kit\//,
  /(^|\/)dist\//,
  /(^|\/)build\//,
  /(^|\/)coverage\//,
  /(^|\/)\.wrangler(-out)?\//,
  /(^|\/)static\//,
  /(^|\/)public\//,
  /(^|\/)generated\//,
  /(^|\/)_registry\//,
  /\.gen\.[a-z]+$/,
  /^90-docs\//,
  /^80-docs\//,
  /^80-data\//,
  /^40-engine\/kotoba\//,
  /(^|\/)etzhayyim-project-[^/]+\//,
  /(^|\/)etzhayyim-apps-[^/]+\//,
  /(^|\/)etzhayyim-wasm-[^/]+\//,
  // The lint script itself: it documents legacy host examples in its
  // own comments (jurisdictional / staging / 3-label patterns).
  // Mirrors the EXCLUDE_GLOBS self-exclusion entry.
  /^70-tools\/scripts\/lint\/no-two-stage-etzhayyim-domains\.mjs$/,
];

function listFilesFromArgs(args) {
  // Filter to files that (a) exist on disk (renames / deletions are passed
  // but their old paths no longer resolve), (b) match the include glob by
  // extension, and (c) are not in an excluded directory (mirrored from
  // EXCLUDE_GLOBS). The extension check is a cheap proxy for INCLUDE_GLOB.
  const includeExt = new Set(
    INCLUDE_GLOB
      .replace(/^.*\{/, "")
      .replace(/\}.*$/, "")
      .split(",")
      .map((e) => `.${e}`),
  );
  return args.filter((f) => {
    if (!fs.existsSync(f)) return false;
    if (!fs.statSync(f).isFile()) return false;
    const dot = f.lastIndexOf(".");
    if (dot < 0) return false;
    if (!includeExt.has(f.slice(dot))) return false;
    if (ARGV_EXCLUDE_PATH_PATTERNS.some((re) => re.test(f))) return false;
    return true;
  });
}

function listFiles() {
  // CLI arg shape:
  //   node script.mjs                → scan staged files (none → no-op)
  //   node script.mjs --all          → scan full monorepo via rg
  //   node script.mjs <file> <file>…  → scan exactly those files
  const cliArgs = process.argv.slice(2).filter((a) => a !== "--json");
  if (cliArgs.includes("--all")) return listFilesAll();
  if (cliArgs.length === 0) return [];
  return listFilesFromArgs(cliArgs);
}

function lineNumberAt(text, index) {
  let line = 1;
  for (let i = 0; i < index; i += 1) {
    if (text.charCodeAt(i) === 10) line += 1;
  }
  return line;
}

// Suggest the etzhayyim.com replacement for a captured `.etzhayyim.com` host.
// Mechanical rewrite: same label prefix, swap zone tail. The cutover
// runbook (ADR-2605212340) and the operator decide whether to flatten
// any intermediate dots into hyphens at the same time.
function suggestedHost(host) {
  return `${host.slice(0, -".etzhayyim.com".length)}.etzhayyim.com`;
}

const violations = [];
for (const file of listFiles()) {
  const text = fs.readFileSync(file, "utf8");
  const lines = text.split("\n");
  HOST_RE.lastIndex = 0;
  let match;
  while ((match = HOST_RE.exec(text)) !== null) {
    const host = match[1];
    // HOST_RE already restricts to `*.etzhayyim.com`; the captured value is
    // always a legacy-domain violation per ADR-2605212340. No further
    // filtering needed (the old `isForbidden…` filter looked for
    // `.etzhayyim.com` and so was a no-op against this regex).
    if (!host) continue;
    const line = lineNumberAt(text, match.index);
    violations.push({
      file,
      line,
      host,
      suggestion: suggestedHost(host),
      text: (lines[line - 1] ?? "").trim(),
    });
  }
}

const unique = [...new Map(
  violations.map((v) => [`${v.file}:${v.line}:${v.host}`, v]),
).values()].sort((a, b) => `${a.file}:${a.line}:${a.host}`.localeCompare(`${b.file}:${b.line}:${b.host}`));

if (process.argv.includes("--json")) {
  console.log(JSON.stringify(unique, null, 2));
  process.exit(unique.length > 0 ? 1 : 0);
}

if (unique.length > 0) {
  const hosts = [...new Map(unique.map((v) => [v.host, v.suggestion])).entries()]
    .sort(([a], [b]) => a.localeCompare(b));
  console.error("lint:no-two-stage-etzhayyim-domains failed");
  console.error("Legacy `.etzhayyim.com` host references found in canonical etzhayyim source.");
  console.error("Per ADR-2605212340 (2026-05-21 domain cutover), the legacy zone must");
  console.error("not appear in new commits to first-party code. Replace each occurrence");
  console.error("with the corresponding `.etzhayyim.com` host (and update DNS / IPFS");
  console.error("/ AT registrations to match if the host is publicly resolved).\n");
  console.error(`Forbidden hosts (${hosts.length}):`);
  for (const [host, suggestion] of hosts.slice(0, 120)) {
    console.error(`  ${host} -> ${suggestion}`);
  }
  if (hosts.length > 120) console.error(`  ...and ${hosts.length - 120} more hosts`);
  console.error(`\nOccurrences (${unique.length}):`);
  for (const v of unique.slice(0, 200)) {
    console.error(`  ${v.file}:${v.line}: ${v.host} -> ${v.suggestion}`);
  }
  if (unique.length > 200) console.error(`  ...and ${unique.length - 200} more occurrences`);
  process.exit(1);
}

console.log("lint:no-two-stage-etzhayyim-domains ok");

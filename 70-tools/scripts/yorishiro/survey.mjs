#!/usr/bin/env node
// survey.mjs — Phase 4 migration scanner (ADR-2605211900).
//
// Scans the repo (defaults: 60-apps/, flat west actors, 70-tools/) for direct
// `fetch("http(s)://…")` calls, cross-references the URL hosts against
// the registered yorishiri (70-tools/etzhayyim-cli/yorishiro/registry/*.json),
// and reports:
//
//   - matched : direct fetch to a host that an existing yorishiro covers
//               → recommended migration to ai.etzhayyim.yorishiro.<name>.*
//   - unmatched: direct fetch to a host with no yorishiro yet
//               → candidate for a new yorishiro (or, if commercial /
//                 payment, a Charter §4 violation — do NOT yorishiro it)
//   - allow-listed: fetches to known internal substrate hosts (PDS,
//                   atproto, etzhayyim.com), reported but not flagged
//
// Usage:
//   node 70-tools/scripts/yorishiro/survey.mjs                # human-readable
//   node 70-tools/scripts/yorishiro/survey.mjs --json         # machine output
//   node 70-tools/scripts/yorishiro/survey.mjs --paths PATHS  # comma-csv override
//
// Exit codes:
//   0 — no unflagged direct fetches
//   1 — at least one unmatched candidate or Charter violation present

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const REPO_ROOT = process.env.YORISHIRO_REPO_ROOT ?? process.cwd();
const REGISTRY = join(REPO_ROOT, "70-tools/etzhayyim-cli/yorishiro/registry");
const DEFAULT_PATHS = ["60-apps", "orgs/etzhayyim", "70-tools"];

const args = process.argv.slice(2);
const wantJson = args.includes("--json");
const pathsIdx = args.indexOf("--paths");
const scanPaths = pathsIdx >= 0 && args[pathsIdx + 1]
  ? args[pathsIdx + 1].split(",")
  : DEFAULT_PATHS;

const FILE_EXTS = new Set([".ts", ".tsx", ".mjs", ".cjs", ".js", ".jsx", ".py"]);
const SKIP_DIRS = new Set([
  ".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__", "_archive",
  // Build artefact directories — emitted output, not source. Including
  // these double-counts the same code and adds noise from URL fragments
  // that survived minification.
  "_svelte", "_app", ".svelte-kit", "assets", "fixtures",
]);

// Hosts that are part of the etzhayyim substrate and explicitly NOT
// yorishiri targets — they are internal infrastructure.
const SUBSTRATE_HOSTS = new Set([
  "atproto.etzhayyim.com",
  "atproto.etzhayyim.com",
  "etzhayyim.com",
  "auth.etzhayyim.com",
  "authn.etzhayyim.com",
  "authz.etzhayyim.com",
  "mcp.etzhayyim.com",
  "llm.etzhayyim.com",
  "etzhayyim.com",
  "api.cloudflare.com", // CF management; not user-facing
]);

// Suffix match: anything under *.etzhayyim.com is substrate by default.
const SUBSTRATE_SUFFIXES = [".etzhayyim.com", ".etzhayyim.com"];

// Hosts that are clearly noise (test fixtures, localhost, OAuth issuers
// that are infrastructure not data sources). Reported but not flagged.
const NOISE_HOSTS = new Set([
  "api.example.com", "example.com", "example.org",
  "localhost", "127.0.0.1",
  "oauth2.googleapis.com", "login.microsoftonline.com",
  "accounts.google.com",
]);

// Hosts that are KNOWN Charter Rider violations (ADR-2605192115 §4
// + ADR-2605192200 §2). These must NOT be wrapped with yorishiro
// — they should be removed entirely.
const CHARTER_VIOLATION_HOSTS = new Map([
  ["api.stripe.com", "ADR-2605192115 §1.3 — fiat payment processors are forbidden"],
  ["api.paypal.com", "ADR-2605192115 §1.3 — fiat payment processors are forbidden"],
  ["api.square.com", "ADR-2605192115 §1.3 — fiat payment processors are forbidden"],
  ["www.googletagmanager.com", "Charter Rider §2(a) — ad-tech kami are forbidden"],
  ["connect.facebook.net", "Charter Rider §2(a) — ad-tech kami are forbidden"],
]);

function loadRegistry() {
  let entries = [];
  try {
    entries = readdirSync(REGISTRY).filter((f) => f.endsWith(".json"));
  } catch {
    return [];
  }
  const out = [];
  for (const f of entries) {
    const cfg = JSON.parse(readFileSync(join(REGISTRY, f), "utf-8"));
    let host = null;
    if (cfg.baseUrl) {
      try { host = new URL(cfg.baseUrl).hostname; } catch { /* ignore */ }
    } else if (cfg.kami && cfg.kami.startsWith("browser:")) {
      try { host = new URL(cfg.base_url ?? cfg.baseUrl ?? "").hostname; } catch { /* ignore */ }
    }
    out.push({ name: cfg.name, kami: cfg.kami, host, mode: cfg.from, baseUrl: cfg.baseUrl, binary: cfg.binary });
  }
  return out;
}

function walk(root) {
  const out = [];
  let entries;
  try {
    entries = readdirSync(root);
  } catch {
    return out;
  }
  for (const name of entries) {
    if (SKIP_DIRS.has(name)) continue;
    const full = join(root, name);
    let st;
    try { st = statSync(full); } catch { continue; }
    if (st.isDirectory()) {
      out.push(...walk(full));
    } else {
      const dot = name.lastIndexOf(".");
      if (dot >= 0 && FILE_EXTS.has(name.slice(dot))) out.push(full);
    }
  }
  return out;
}

// Matches:
//   fetch("https://...")
//   fetch(`https://...`)
//   urlopen('https://...')  (Python stdlib)
//   urllib.request.Request("https://...")
//   requests.get("https://...")
//   requests.post(...
const FETCH_RE = /(?:fetch|urlopen|requests\.(?:get|post|put|delete|patch|head))\s*\(\s*[`"']?(?:Request\s*\(\s*[`"'])?(https?:\/\/[^\s"'`)]+)/g;

function scanFile(path) {
  let raw;
  try {
    raw = readFileSync(path, "utf-8");
  } catch {
    return [];
  }
  const hits = [];
  for (const m of raw.matchAll(FETCH_RE)) {
    const url = m[1];
    if (!url) continue;
    let host = null;
    try { host = new URL(url.replace(/\$\{[^}]+\}/g, "_")).hostname; } catch { continue; }
    const idx = m.index ?? 0;
    const line = raw.slice(0, idx).split("\n").length;
    hits.push({ url, host, line });
  }
  return hits;
}

const yorishiri = loadRegistry();
const yorishiroByHost = new Map();
for (const y of yorishiri) {
  if (y.host) yorishiroByHost.set(y.host, y);
}

const findings = { matched: [], unmatched: [], violation: [], substrate: [], noise: [] };

const isSubstrate = (host) =>
  SUBSTRATE_HOSTS.has(host) || SUBSTRATE_SUFFIXES.some((s) => host.endsWith(s));

// Files inside the yorishiro generator itself contain URL string
// literals in regex sources and templates that are not real fetch sites.
const SELF_FILES = new RegExp(
  "70-tools/(?:scripts/yorishiro/|etzhayyim-cli/yorishiro/)",
);

for (const p of scanPaths) {
  const root = join(REPO_ROOT, p);
  for (const file of walk(root)) {
    const rel = relative(REPO_ROOT, file);
    if (SELF_FILES.test(rel)) continue;
    const hits = scanFile(file);
    for (const h of hits) {
      if (!h.host || h.host === "_") continue;
      const where = { file: rel, line: h.line, url: h.url, host: h.host };
      if (CHARTER_VIOLATION_HOSTS.has(h.host)) {
        findings.violation.push({ ...where, reason: CHARTER_VIOLATION_HOSTS.get(h.host) });
      } else if (isSubstrate(h.host)) {
        findings.substrate.push(where);
      } else if (NOISE_HOSTS.has(h.host)) {
        findings.noise.push(where);
      } else if (yorishiroByHost.has(h.host)) {
        const y = yorishiroByHost.get(h.host);
        findings.matched.push({ ...where, yorishiro: y.name, kami: y.kami, mcp: `@etzhayyim/yorishiro-${y.name}-mcp` });
      } else {
        findings.unmatched.push(where);
      }
    }
  }
}

if (wantJson) {
  process.stdout.write(JSON.stringify(findings, null, 2) + "\n");
  const exit = findings.violation.length + findings.unmatched.length > 0 ? 1 : 0;
  process.exit(exit);
}

const banner = (s) => `\n=== ${s} ===\n`;

process.stdout.write(banner("yorishiro migration survey (ADR-2605211900 Phase 4)"));
process.stdout.write(`Scanned paths : ${scanPaths.join(", ")}\n`);
process.stdout.write(`Yorishiri     : ${yorishiri.length}\n`);
process.stdout.write(`Findings      : matched=${findings.matched.length}  unmatched=${findings.unmatched.length}  violation=${findings.violation.length}  substrate=${findings.substrate.length}  noise=${findings.noise.length}\n`);

if (findings.violation.length > 0) {
  process.stdout.write(banner("✘ Charter violations (do NOT wrap with yorishiro; remove entirely)"));
  for (const v of findings.violation) {
    process.stdout.write(`  ${v.file}:${v.line}\n    URL    : ${v.url}\n    reason : ${v.reason}\n\n`);
  }
}

if (findings.matched.length > 0) {
  process.stdout.write(banner("⇒ Migration candidates (yorishiro available)"));
  for (const m of findings.matched) {
    process.stdout.write(`  ${m.file}:${m.line}\n    URL       : ${m.url}\n    yorishiro : ${m.yorishiro} (${m.kami})\n    use MCP   : ${m.mcp}\n\n`);
  }
}

if (findings.unmatched.length > 0) {
  process.stdout.write(banner("? Unmatched vendor fetches (consider authoring a new yorishiro)"));
  const byHost = new Map();
  for (const u of findings.unmatched) {
    if (!byHost.has(u.host)) byHost.set(u.host, []);
    byHost.get(u.host).push(u);
  }
  for (const [host, list] of [...byHost.entries()].sort()) {
    process.stdout.write(`  ${host}  (${list.length} site${list.length > 1 ? "s" : ""})\n`);
    for (const u of list.slice(0, 3)) process.stdout.write(`    ${u.file}:${u.line}\n`);
    if (list.length > 3) process.stdout.write(`    … and ${list.length - 3} more\n`);
    process.stdout.write("\n");
  }
}

if (findings.substrate.length > 0) {
  process.stdout.write(banner("· Substrate fetches (allow-listed — not yorishiro targets)"));
  for (const s of findings.substrate.slice(0, 5)) process.stdout.write(`  ${s.file}:${s.line}  ${s.host}\n`);
  if (findings.substrate.length > 5) process.stdout.write(`  … and ${findings.substrate.length - 5} more\n`);
}

const exit = findings.violation.length + findings.unmatched.length > 0 ? 1 : 0;
process.exit(exit);

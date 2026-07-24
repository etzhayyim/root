#!/usr/bin/env node
/**
 * no-danjo-adjudication lint — enforce ADR-2605301600 §4 G4 + G8.
 *
 * Pre-commit gate for the danjo (弾正) public-accountability oversight
 * actor. danjo is the censor's EYE, never the censor's SWORD: it emits
 * FACTUAL, source-cited, NON-adjudicating discrepancy observations over
 * the open-government corpus (ADR-2605263900) and MUST NOT (a) render a
 * legal verdict that a crime / violation occurred, nor (b) integrate a
 * commercial government-intelligence terminal.
 *
 * Two precise checks (designed for ~zero false positives):
 *
 *   Check A — G8 commercial gov-intel terminal deny-list.
 *     Scans danjo CODE files (.py / .ts / .mjs / .js) for forbidden
 *     vendor hostnames + SDK import identifiers. The constitutional DOCS
 *     that ENUMERATE the prohibition (ADR / manifest.jsonld / README /
 *     CLAUDE.md) are out of scope by construction (code extensions only),
 *     exactly as sensor-no-active-probe exempts charter_rider.py.
 *
 *   Check B — G4 non-adjudication schema invariant.
 *     Parses the danjo Lexicon JSON and asserts, structurally:
 *       (1) discrepancyObservation + oversightReport carry
 *           `nonAdjudicatingNotice` with `const: true`;
 *       (2) the discrepancyObservation `category` knownValues enum
 *           contains NO verdict token (crime / violation / guilt /
 *           illegal / unlawful / 犯罪 / 違法 / 有罪) — a legal verdict
 *           must be UNREPRESENTABLE at the schema layer.
 *     Runs against the canonical lexicon paths whether or not they were
 *     passed as args, so `node no-danjo-adjudication.mjs` with no args
 *     still audits the constitutional anchor.
 *
 * Exit code 0 on success, 1 on violation.
 *
 * Authoritative ADR:
 *   90-docs/adr/2605301600-danjo-public-accountability-oversight-tier-b-actor-r0.md
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const args = process.argv.slice(2);

// ── Check A: G8 commercial gov-intel terminal deny-list ──────────────
// Scope to danjo-pathed CODE only; docs that enumerate the deny-list are
// excluded by extension (same discipline as charter_rider.py exemption).
const DANJO_CODE_RE =
  /(^|\/)(orgs\/etzhayyim\/com-etzhayyim-danjo\/|20-actors\/kotodama\/cells\/danjo_|.*danjo.*)\S*\.(py|ts|mjs|js)$/;

// Forbidden vendor hostnames (substring match, case-insensitive).
const GOV_INTEL_HOSTS = [
  "govwin.com",
  "govwiniq",
  "bgov.com",
  "bloomberggovernment",
  "politicopro",
  "pro.politico.com",
  "eenews.net",
  "fiscalnote.com",
  "cqrollcall",
  "cq.com",
];

// Forbidden SDK / package import identifiers (token match).
const GOV_INTEL_IMPORTS = [
  "govwin",
  "fiscalnote",
  "bgov",
  "bloomberg_government",
  "cqrollcall",
];

const HOST_LITERAL_RE = /https?:\/\/([^/\s"'`]+)/gi;
const IMPORT_RE =
  /(?:^\s*(?:import|from)\s+|require\(\s*["'`]|import\(\s*["'`])([\w.\-/@]+)/gm;

// ── Check B: G4 non-adjudication schema invariant ────────────────────
const LEX_DIR = "00-contracts/lexicons/com/etzhayyim/danjo";
const OBSERVATION_LEX = `${LEX_DIR}/discrepancyObservation.json`;
const REPORT_LEX = `${LEX_DIR}/oversightReport.json`;
const NON_ADJ_LEXICONS = [OBSERVATION_LEX, REPORT_LEX];

// Verdict tokens that may NEVER appear as an observation category value.
const VERDICT_TOKENS = [
  "crime",
  "criminal",
  "violation",
  "violat",
  "guilt",
  "illegal",
  "unlawful",
  "fraud",
  "犯罪",
  "違法",
  "有罪",
  "不正", // 不正 as a CATEGORY value is a verdict; descriptive prose elsewhere is fine
];

let violations = 0;

// ── Run Check A over staged danjo code files ─────────────────────────
for (const file of args) {
  if (!DANJO_CODE_RE.test(file)) continue;
  const abs = resolve(process.cwd(), file);
  if (!existsSync(abs)) continue;
  let content;
  try {
    content = readFileSync(abs, "utf8");
  } catch {
    continue;
  }
  const lower = content.toLowerCase();

  for (const match of content.matchAll(HOST_LITERAL_RE)) {
    const host = (match[1] || "").toLowerCase();
    if (GOV_INTEL_HOSTS.some((h) => host.includes(h))) {
      console.error(
        `[X] ${file}: commercial gov-intelligence terminal host '${host}' ` +
          `is PROHIBITED (ADR-2605301600 G8 / Charter Rider §2(e)).`,
      );
      violations += 1;
    }
  }
  for (const match of content.matchAll(IMPORT_RE)) {
    const mod = (match[1] || "").toLowerCase();
    if (GOV_INTEL_IMPORTS.some((m) => mod.includes(m))) {
      console.error(
        `[X] ${file}: import of commercial gov-intel SDK '${mod}' is ` +
          `PROHIBITED (ADR-2605301600 G8).`,
      );
      violations += 1;
    }
  }
  // belt-and-suspenders: catch bare hostname mentions in code strings
  for (const h of GOV_INTEL_HOSTS) {
    if (lower.includes(h)) {
      // already counted if it appeared as a URL host; only flag if not
      const asUrl = [...content.matchAll(HOST_LITERAL_RE)].some((m) =>
        (m[1] || "").toLowerCase().includes(h),
      );
      if (!asUrl) {
        console.error(
          `[X] ${file}: commercial gov-intel terminal token '${h}' in ` +
            `danjo code is PROHIBITED (ADR-2605301600 G8).`,
        );
        violations += 1;
      }
    }
  }
}

// ── Run Check B over the canonical lexicon files (always) ────────────
for (const lexPath of NON_ADJ_LEXICONS) {
  const abs = resolve(process.cwd(), lexPath);
  if (!existsSync(abs)) continue; // R0: skeletons may not all exist yet
  let doc;
  try {
    doc = JSON.parse(readFileSync(abs, "utf8"));
  } catch (e) {
    console.error(`[X] ${lexPath}: invalid JSON (${e.message}).`);
    violations += 1;
    continue;
  }
  const props = doc?.defs?.main?.record?.properties ?? {};

  // (1) nonAdjudicatingNotice must exist with const:true
  const notice = props.nonAdjudicatingNotice;
  if (!notice || notice.const !== true) {
    console.error(
      `[X] ${lexPath}: 'nonAdjudicatingNotice' MUST be present with ` +
        `\`const: true\` (ADR-2605301600 G4 — non-adjudication anchor).`,
    );
    violations += 1;
  }

  // (2) discrepancyObservation.category enum must carry no verdict token
  if (lexPath === OBSERVATION_LEX) {
    const known = props?.category?.knownValues ?? [];
    for (const v of known) {
      const lv = String(v).toLowerCase();
      const hit = VERDICT_TOKENS.find((t) => lv.includes(t.toLowerCase()));
      if (hit) {
        console.error(
          `[X] ${lexPath}: observation category '${v}' contains verdict ` +
            `token '${hit}'. A legal verdict MUST be unrepresentable at ` +
            `the schema layer (ADR-2605301600 G4).`,
        );
        violations += 1;
      }
    }
  }
}

if (violations > 0) {
  console.error(
    `\n${violations} no-danjo-adjudication violation(s). danjo is the ` +
      `censor's eye, never the censor's sword — see ADR-2605301600 §4 ` +
      `(G4 non-adjudication / G8 no commercial gov-intel terminals).`,
  );
  process.exit(1);
}
process.exit(0);

#!/usr/bin/env node
/**
 * no-kanae-adjudication lint — enforce ADR-2605302300 §4 G4 + G7 + G8 + G15.
 *
 * Pre-commit gate for the kanae (鼎) global government fiscal-flow
 * visualization actor. kanae weighs the public fiscal record OPENLY and
 * renders no verdict: danjo finds, kanae renders. It emits FACTUAL,
 * source-cited, NON-adjudicating fund-flow edges + Murakumo-only
 * narratives + aggregate-first kami-engine WASM visualizations, and MUST
 * NOT (a) render a legal verdict that a crime / 不正 / violation occurred,
 * (b) accept a vendor-LLM narrative origin, (c) integrate a commercial
 * government-intelligence terminal, nor (d) embed an ad / analytics SDK in
 * the render path.
 *
 * Four precise checks (designed for ~zero false positives):
 *
 *   Check A — G4 non-adjudication schema invariant.
 *     Parses the kanae Lexicon JSON and asserts, structurally:
 *       (1) flowNarrative carries `nonAdjudicatingNotice` with `const:true`;
 *       (2) the fundFlowEdge `flowClass` knownValues enum contains NO
 *           verdict token (crime / violation / guilt / illegal / unlawful
 *           / fraud / 犯罪 / 違法 / 有罪 / 不正) — a legal verdict must be
 *           UNREPRESENTABLE at the schema layer.
 *
 *   Check B — G7 Murakumo-only inference invariant.
 *     Asserts flowNarrative REQUIRES `murakumoInferenceAttestation`, and
 *     that its `inferenceSubstrate` is pinned to `const: "murakumo"` — a
 *     vendor-LLM origin must be UNREPRESENTABLE at the schema layer.
 *
 *   Check C — G8 commercial gov-intel terminal deny-list (code only).
 *   Check D — G15 ad / analytics SDK deny-list (render-path code only).
 *     Both scan kanae CODE files (.py / .ts / .mjs / .js) for forbidden
 *     vendor hostnames + SDK identifiers. Constitutional DOCS that
 *     ENUMERATE the prohibition are out of scope by construction (code
 *     extensions only), exactly as the danjo lint exempts its own docs.
 *
 * Runs Check A + B against the canonical lexicon paths whether or not they
 * were passed as args, so `node no-kanae-adjudication.mjs` with no args
 * still audits the constitutional anchors.
 *
 * Exit code 0 on success, 1 on violation.
 *
 * Authoritative ADR:
 *   90-docs/adr/2605302300-kanae-global-fiscal-flow-visualization-tier-b-actor-r0.md
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const args = process.argv.slice(2);

// ── Code-file scoping (Checks C + D) ─────────────────────────────────
// Scope to kanae-pathed CODE only; docs that enumerate the deny-lists are
// excluded by extension (same discipline as the danjo lint).
const KANAE_CODE_RE =
  /(^|\/)(20-actors\/kanae\/|20-actors\/kotodama\/cells\/kanae_|.*kanae.*)\S*\.(py|ts|mjs|js)$/;

// Check C: forbidden commercial gov-intel vendor hostnames (substring).
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
const GOV_INTEL_IMPORTS = [
  "govwin",
  "fiscalnote",
  "bgov",
  "bloomberg_government",
  "cqrollcall",
];

// Check D: forbidden ad / analytics SDK tokens in the render path (G15).
// Token match — kept tight to avoid FPs (e.g. plain "ga" is excluded).
const AD_ANALYTICS_TOKENS = [
  "googletagmanager",
  "google-analytics",
  "gtag(",
  "ga4",
  "connect.facebook.net",
  "fbq(",
  "meta pixel",
  "metapixel",
  "doubleclick",
];

const HOST_LITERAL_RE = /https?:\/\/([^/\s"'`]+)/gi;
const IMPORT_RE =
  /(?:^\s*(?:import|from)\s+|require\(\s*["'`]|import\(\s*["'`])([\w.\-/@]+)/gm;

// ── Lexicon paths (Checks A + B) ─────────────────────────────────────
const LEX_DIR = "orgs/etzhayyim/com-etzhayyim-kanae/wire/lexicons";
const EDGE_LEX = `${LEX_DIR}/fundFlowEdge.json`;
const NARRATIVE_LEX = `${LEX_DIR}/flowNarrative.json`;

// Verdict tokens that may NEVER appear as a fundFlowEdge flowClass value.
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
  "不正", // 不正 as a flowClass value is a verdict; descriptive prose elsewhere is fine
];

let violations = 0;

// ── Check A: G4 non-adjudication ─────────────────────────────────────
{
  const abs = resolve(process.cwd(), NARRATIVE_LEX);
  if (existsSync(abs)) {
    let doc;
    try {
      doc = JSON.parse(readFileSync(abs, "utf8"));
      const props = doc?.defs?.main?.record?.properties ?? {};
      const notice = props.nonAdjudicatingNotice;
      if (!notice || notice.const !== true) {
        console.error(
          `[X] ${NARRATIVE_LEX}: 'nonAdjudicatingNotice' MUST be present ` +
            `with \`const: true\` (ADR-2605302300 G4 — non-adjudication anchor).`,
        );
        violations += 1;
      }
    } catch (e) {
      console.error(`[X] ${NARRATIVE_LEX}: invalid JSON (${e.message}).`);
      violations += 1;
    }
  }
}
{
  const abs = resolve(process.cwd(), EDGE_LEX);
  if (existsSync(abs)) {
    let doc;
    try {
      doc = JSON.parse(readFileSync(abs, "utf8"));
      const props = doc?.defs?.main?.record?.properties ?? {};
      const known = props?.flowClass?.knownValues ?? [];
      for (const v of known) {
        const lv = String(v).toLowerCase();
        const hit = VERDICT_TOKENS.find((t) => lv.includes(t.toLowerCase()));
        if (hit) {
          console.error(
            `[X] ${EDGE_LEX}: flowClass '${v}' contains verdict token ` +
              `'${hit}'. A legal verdict MUST be unrepresentable at the ` +
              `schema layer (ADR-2605302300 G4).`,
          );
          violations += 1;
        }
      }
    } catch (e) {
      console.error(`[X] ${EDGE_LEX}: invalid JSON (${e.message}).`);
      violations += 1;
    }
  }
}

// ── Check B: G7 Murakumo-only inference ──────────────────────────────
{
  const abs = resolve(process.cwd(), NARRATIVE_LEX);
  if (existsSync(abs)) {
    try {
      const doc = JSON.parse(readFileSync(abs, "utf8"));
      const record = doc?.defs?.main?.record ?? {};
      const props = record.properties ?? {};
      const required = record.required ?? [];
      if (!required.includes("murakumoInferenceAttestation")) {
        console.error(
          `[X] ${NARRATIVE_LEX}: 'murakumoInferenceAttestation' MUST be a ` +
            `required field (ADR-2605302300 G7 — Murakumo-only anchor).`,
        );
        violations += 1;
      }
      const att = doc?.defs?.murakumoAttestation?.properties ?? {};
      const substrate = att.inferenceSubstrate;
      if (!substrate || substrate.const !== "murakumo") {
        console.error(
          `[X] ${NARRATIVE_LEX}: #murakumoAttestation.inferenceSubstrate ` +
            `MUST be \`const: "murakumo"\`. A vendor-LLM origin must be ` +
            `unrepresentable (ADR-2605302300 G7 / ADR-2605215000).`,
        );
        violations += 1;
      }
      void props;
    } catch {
      // JSON error already reported in Check A
    }
  }
}

// ── Checks C + D over staged kanae code files ────────────────────────
for (const file of args) {
  if (!KANAE_CODE_RE.test(file)) continue;
  const abs = resolve(process.cwd(), file);
  if (!existsSync(abs)) continue;
  let content;
  try {
    content = readFileSync(abs, "utf8");
  } catch {
    continue;
  }
  const lower = content.toLowerCase();

  // Check C — gov-intel hosts + imports
  for (const match of content.matchAll(HOST_LITERAL_RE)) {
    const host = (match[1] || "").toLowerCase();
    if (GOV_INTEL_HOSTS.some((h) => host.includes(h))) {
      console.error(
        `[X] ${file}: commercial gov-intelligence terminal host '${host}' ` +
          `is PROHIBITED (ADR-2605302300 G8 / Charter Rider §2(e)).`,
      );
      violations += 1;
    }
  }
  for (const match of content.matchAll(IMPORT_RE)) {
    const mod = (match[1] || "").toLowerCase();
    if (GOV_INTEL_IMPORTS.some((m) => mod.includes(m))) {
      console.error(
        `[X] ${file}: import of commercial gov-intel SDK '${mod}' is ` +
          `PROHIBITED (ADR-2605302300 G8).`,
      );
      violations += 1;
    }
  }
  for (const h of GOV_INTEL_HOSTS) {
    if (lower.includes(h)) {
      const asUrl = [...content.matchAll(HOST_LITERAL_RE)].some((m) =>
        (m[1] || "").toLowerCase().includes(h),
      );
      if (!asUrl) {
        console.error(
          `[X] ${file}: commercial gov-intel terminal token '${h}' in ` +
            `kanae code is PROHIBITED (ADR-2605302300 G8).`,
        );
        violations += 1;
      }
    }
  }

  // Check D — ad / analytics SDK tokens in the render path (G15)
  for (const t of AD_ANALYTICS_TOKENS) {
    if (lower.includes(t)) {
      console.error(
        `[X] ${file}: ad / analytics SDK token '${t}' in kanae render code ` +
          `is PROHIBITED (ADR-2605302300 G15 / Substrate boundary Advertising row).`,
      );
      violations += 1;
    }
  }
}

if (violations > 0) {
  console.error(
    `\n${violations} no-kanae-adjudication violation(s). kanae weighs the ` +
      `public fiscal record openly and renders no verdict — see ` +
      `ADR-2605302300 §4 (G4 non-adjudication / G7 Murakumo-only / ` +
      `G8 no commercial gov-intel / G15 no ad-analytics SDK).`,
  );
  process.exit(1);
}
process.exit(0);

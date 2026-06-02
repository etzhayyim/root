#!/usr/bin/env node
/**
 * lint-no-judge-profiling lint — enforce ADR-2605302345 §D5 G19.
 *
 * The etzhayyim global judiciary corpus ingests courts / decisions /
 * judge-reference from pre-published public records for FACTUAL reference
 * only (who presides where). It MUST NOT evaluate, analyse, compare,
 * score, rank or predict a named judge's practices or decisions. In
 * France this is a CRIME: loi n°2019-222 art. 33 prohibits reusing
 * magistrates' identity data to evaluate/analyse/compare/predict their
 * professional practices (Code pénal art. 226-18, up to 5y). The
 * prohibition is the GLOBAL default and is hard-locked for France.
 *
 * Two precise checks (designed for ~zero false positives):
 *
 *   Check A — schema invariant (always, over the canonical lexicon).
 *     com.etzhayyim.judiciary.judgeReference MUST, structurally:
 *       (1) carry `noAnalytics` with `const: true` and list it in the
 *           record `required` array;
 *       (2) contain NO analytics property (deny-list: winRate /
 *           rulingPrediction / reversalRate / leanScore /
 *           decisionTendency / judgeScore / predictedOutcome / ...) —
 *           judge analytics must be unrepresentable at the schema layer.
 *
 *   Check B — code marker deny-list (over staged judiciary code).
 *     Scans judiciary CODE for unambiguous judge-analytics markers
 *     (judgeWinRate / predictByJudge / rankJudges / scoreJudge /
 *     judgeLeaning / judgeAnalytics / reversalRateByJudge).
 *
 * Exit code 0 on success, 1 on violation.
 *
 * Authoritative ADR:
 *   90-docs/adr/2605302345-etzhayyim-legal-services-delivery-and-global-judiciary-corpus.md
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const args = process.argv.slice(2);

// ── Check A: schema invariant ────────────────────────────────────────
const JUDGE_LEX =
  "00-contracts/lexicons/com/etzhayyim/judiciary/judgeReference.json";
const COURT_LEX =
  "00-contracts/lexicons/com/etzhayyim/judiciary/court.json";
const DECISION_LEX =
  "00-contracts/lexicons/com/etzhayyim/judiciary/judicialDecision.json";

// Corpus-wide passive-ingestion (G3) + pseudonymization (D6) invariants:
// { lexPath: [ {prop, requiredToo} ... ] } — each MUST be const:true.
const CONST_TRUE_INVARIANTS = {
  [JUDGE_LEX]: [["noAnalytics", true], ["pseudonymizationApplied", true]],
  [COURT_LEX]: [["passiveIngestion", true]],
  [DECISION_LEX]: [
    ["passiveIngestion", true],
    ["pseudonymizationApplied", true],
  ],
};

// Analytics property/field names that may NEVER appear (schema or code).
const ANALYTICS_TOKENS = [
  "winrate",
  "rulingprediction",
  "reversalrate",
  "leanscore",
  "decisiontendency",
  "judgescore",
  "predictedoutcome",
  "judgewinrate",
  "predictbyjudge",
  "rankjudges",
  "scorejudge",
  "judgeleaning",
  "judgeanalytics",
  "reversalratebyjudge",
  "judgeprofiling",
];

// ── Check B: judiciary CODE scope ────────────────────────────────────
const JUDICIARY_CODE_RE =
  /(^|\/)(.*judiciary.*|.*\/sensors\/judiciary).*\.(py|ts|tsx|mjs|cjs|js|go|rs)$/;

let violations = 0;

// ── Run Check A over every judiciary lexicon (always) ────────────────
for (const [lexPath, invariants] of Object.entries(CONST_TRUE_INVARIANTS)) {
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
  const rec = doc?.defs?.main?.record ?? {};
  const required = rec?.required ?? [];
  const props = rec?.properties ?? {};

  // (1) each invariant flag must be required + const:true (G3/G19/D6)
  for (const [flag] of invariants) {
    if (!required.includes(flag)) {
      console.error(
        `[X] ${lexPath}: '${flag}' MUST be in the record \`required\` array ` +
          `(ADR-2605302345 G3/G19/D6).`,
      );
      violations += 1;
    }
    const p = props[flag];
    if (!p || p.const !== true) {
      console.error(
        `[X] ${lexPath}: '${flag}' MUST have \`const: true\` ` +
          `(passive-ingestion / pseudonymization / no-analytics invariant).`,
      );
      violations += 1;
    }
  }

  // (2) no judge-analytics property anywhere in the lexicon
  const blob = JSON.stringify(doc).toLowerCase();
  for (const t of ANALYTICS_TOKENS) {
    if (blob.includes(`"${t}"`) || blob.includes(`${t}:`)) {
      console.error(
        `[X] ${lexPath}: judge-analytics property '${t}' is PROHIBITED ` +
          `— judge profiling must be unrepresentable (G19; France art.33).`,
      );
      violations += 1;
    }
  }
}

// ── Run Check B over staged judiciary code ───────────────────────────
for (const file of args) {
  if (!JUDICIARY_CODE_RE.test(file)) continue;
  // the enforcement script itself + the ADR are out of scope by extension
  if (file.endsWith("lint-no-judge-profiling.mjs")) continue;
  const abs = resolve(process.cwd(), file);
  if (!existsSync(abs)) continue;
  let content;
  try {
    content = readFileSync(abs, "utf8");
  } catch {
    continue;
  }
  const lower = content.toLowerCase();
  for (const marker of ANALYTICS_TOKENS) {
    if (lower.includes(marker)) {
      console.error(
        `[X] ${file}: judge-analytics marker '${marker}' is PROHIBITED. ` +
          `The corpus reports facts (who presides where); it MUST NOT ` +
          `profile/score/predict judges (ADR-2605302345 G19; criminal in ` +
          `France, loi 2019-222 art.33).`,
      );
      violations += 1;
    }
  }
}

if (violations > 0) {
  console.error(
    `\n${violations} lint-no-judge-profiling violation(s). The judiciary ` +
      `corpus is factual reference, never a profile of the bench — see ` +
      `ADR-2605302345 §D5 (G19).`,
  );
  process.exit(1);
}

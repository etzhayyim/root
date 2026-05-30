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
 *     app.etzhayyim.judiciary.judgeReference MUST, structurally:
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
  "00-contracts/lexicons/app/etzhayyim/judiciary/judgeReference.json";

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

// ── Run Check A over the canonical lexicon (always) ──────────────────
{
  const abs = resolve(process.cwd(), JUDGE_LEX);
  if (existsSync(abs)) {
    let doc;
    try {
      doc = JSON.parse(readFileSync(abs, "utf8"));
    } catch (e) {
      console.error(`[X] ${JUDGE_LEX}: invalid JSON (${e.message}).`);
      violations += 1;
      doc = null;
    }
    if (doc) {
      const rec = doc?.defs?.main?.record ?? {};
      const required = rec?.required ?? [];
      const props = rec?.properties ?? {};

      // (1) noAnalytics const:true and required
      if (!required.includes("noAnalytics")) {
        console.error(
          `[X] ${JUDGE_LEX}: 'noAnalytics' MUST be in the record ` +
            `\`required\` array (ADR-2605302345 G19).`,
        );
        violations += 1;
      }
      const na = props.noAnalytics;
      if (!na || na.const !== true) {
        console.error(
          `[X] ${JUDGE_LEX}: 'noAnalytics' MUST have \`const: true\` ` +
            `(G19 — France loi 2019-222 art.33; judge profiling unrepresentable).`,
        );
        violations += 1;
      }

      // (2) no analytics property anywhere
      const blob = JSON.stringify(doc).toLowerCase();
      for (const t of ANALYTICS_TOKENS) {
        // skip tokens that are only meaningful in code, to keep schema
        // check focused on property-name leakage
        if (blob.includes(`"${t}"`) || blob.includes(`${t}:`)) {
          console.error(
            `[X] ${JUDGE_LEX}: judge-analytics property '${t}' is PROHIBITED ` +
              `— judge profiling must be unrepresentable (G19).`,
          );
          violations += 1;
        }
      }
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

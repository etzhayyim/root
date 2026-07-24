#!/usr/bin/env node
/**
 * no-legal-aid-consideration lint — enforce ADR-2605302200 §D2 G15
 * (+ ADR-2605302330 §D4 extension to certified-mediation matters).
 *
 * The free legal-aid lane charges the adherent NOTHING — no fee, no
 * nominal processing fee, no tithe attribution, no SBT-priced purchase,
 * and no indirect economic benefit. Donations flow only to the general
 * Public Fund and MUST NOT be coupled to a specific legal matter. This
 * is the central constitutional invariant of the whole legal-services
 * design (cash≡0 / donation-only, ADR-2605192115 + ADR-2605301020).
 *
 * Two precise checks (designed for ~zero false positives):
 *
 *   Check A — schema invariant (always, over the canonical lexicon).
 *     com.etzhayyim.chigiri.legalAidMatter MUST, structurally:
 *       (1) carry `zeroCompensation` with `const: true` and list it +
 *           `supervisingCounsel` in the record `required` array;
 *       (2) define `supervisingCounsel` requiring `counselDid` +
 *           `licenseJurisdiction` (G16 hook);
 *       (3) contain NO consideration property (deny-list: fee / price /
 *           amount / cost / tithe / sbtPrice / paymentRef / chargeable)
 *           — a charge against the adherent must be unrepresentable.
 *
 *   Check B — code marker deny-list (over staged chigiri legalAid code).
 *     Scans legalAid / adr-mediation CODE for tokens that couple a
 *     matter to consideration (legalAidFee / matterPrice / chargeForAdvice
 *     / titheForMatter / linkMatterToPayment / legalAidConsideration /
 *     billAdherent).
 *
 * Exit code 0 on success, 1 on violation.
 *
 * Authoritative ADRs:
 *   90-docs/adr/2605302200-chigiri-unpaid-legal-aid-lane-multijurisdiction.md
 *   90-docs/adr/2605302330-chigiri-japan-certified-adr-mediation-lane.md
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const args = process.argv.slice(2);

// ── Check A: schema invariant ────────────────────────────────────────
const CHIGIRI_ROOT =
  process.env.ETZHAYYIM_CHIGIRI_ROOT ?? "../com-etzhayyim-chigiri";
const MATTER_LEX = `${CHIGIRI_ROOT}/wire/legalAidMatter.json`;

// Property names that would represent a charge against the adherent.
const CONSIDERATION_PROPS = [
  "fee",
  "price",
  "amount",
  "cost",
  "tithe",
  "sbtprice",
  "paymentref",
  "chargeable",
  "invoice",
  "billing",
];

// ── Check B: chigiri legalAid CODE scope ─────────────────────────────
const LEGALAID_CODE_RE =
  /(^|\/)(orgs\/etzhayyim\/com-etzhayyim-chigiri\/|.*chigiri.*legalaid.*|.*legalaid.*|.*legal-aid.*|.*chigiri_legal_aid.*)\S*\.(py|ts|tsx|mjs|cjs|js|rs|clj|cljc|cljs)$/i;

// Unambiguous matter↔consideration coupling markers (case-insensitive).
const COUPLING_MARKERS = [
  "legalaidfee",
  "matterprice",
  "chargeforadvice",
  "titheformatter",
  "linkmattertopayment",
  "legalaidconsideration",
  "billadherent",
  "chargeadherent",
  "matterinvoice",
];

let violations = 0;

// ── Run Check A over the canonical lexicon (always) ──────────────────
{
  const abs = resolve(process.cwd(), MATTER_LEX);
  if (existsSync(abs)) {
    let doc;
    try {
      doc = JSON.parse(readFileSync(abs, "utf8"));
    } catch (e) {
      console.error(`[X] ${MATTER_LEX}: invalid JSON (${e.message}).`);
      violations += 1;
      doc = null;
    }
    if (doc) {
      const rec = doc?.defs?.main?.record ?? {};
      const required = rec?.required ?? [];
      const props = rec?.properties ?? {};

      // (1) zeroCompensation + supervisingCounsel required
      for (const must of ["zeroCompensation", "supervisingCounsel"]) {
        if (!required.includes(must)) {
          console.error(
            `[X] ${MATTER_LEX}: '${must}' MUST be in the record ` +
              `\`required\` array (ADR-2605302200 G15/G16).`,
          );
          violations += 1;
        }
      }
      const zc = props.zeroCompensation;
      if (!zc || zc.const !== true) {
        console.error(
          `[X] ${MATTER_LEX}: 'zeroCompensation' MUST have \`const: true\` ` +
            `(G15 — a charge against the adherent must be unrepresentable).`,
        );
        violations += 1;
      }

      // (2) supervisingCounsel def requires counselDid + licenseJurisdiction
      const sc = doc?.defs?.supervisingCounsel ?? {};
      const scReq = sc?.required ?? [];
      for (const must of ["counselDid", "licenseJurisdiction"]) {
        if (!scReq.includes(must)) {
          console.error(
            `[X] ${MATTER_LEX}: supervisingCounsel MUST require '${must}' ` +
              `(G16 — in-jurisdiction licensed lawyer).`,
          );
          violations += 1;
        }
      }

      // (3) no consideration property anywhere as a property KEY
      const propKeys = new Set();
      const walk = (o) => {
        if (!o || typeof o !== "object") return;
        for (const [k, v] of Object.entries(o)) {
          if (k === "properties" && v && typeof v === "object") {
            for (const pk of Object.keys(v)) propKeys.add(pk.toLowerCase());
          }
          walk(v);
        }
      };
      walk(doc);
      for (const p of CONSIDERATION_PROPS) {
        if (propKeys.has(p)) {
          console.error(
            `[X] ${MATTER_LEX}: consideration property '${p}' is PROHIBITED ` +
              `— the legal-aid lane charges the adherent nothing (G15).`,
          );
          violations += 1;
        }
      }
    }
  }
}

// ── Run Check B over staged chigiri legalAid code ────────────────────
for (const file of args) {
  if (!LEGALAID_CODE_RE.test(file)) continue;
  if (file.endsWith("no-legal-aid-consideration.mjs")) continue;
  const abs = resolve(process.cwd(), file);
  if (!existsSync(abs)) continue;
  let content;
  try {
    content = readFileSync(abs, "utf8");
  } catch {
    continue;
  }
  const lower = content.toLowerCase();
  for (const marker of COUPLING_MARKERS) {
    if (lower.includes(marker)) {
      console.error(
        `[X] ${file}: legal-aid consideration marker '${marker}' is ` +
          `PROHIBITED. A legal-aid matter MUST NOT be coupled to a fee / ` +
          `tithe / SBT-purchase / payment (ADR-2605302200 G15).`,
      );
      violations += 1;
    }
  }
}

if (violations > 0) {
  console.error(
    `\n${violations} no-legal-aid-consideration violation(s). Free legal ` +
      `aid is gratuitous — zero compensation, including indirect benefit ` +
      `(ADR-2605302200 §D2 G15; cash≡0 ADR-2605301020).`,
  );
  process.exit(1);
}

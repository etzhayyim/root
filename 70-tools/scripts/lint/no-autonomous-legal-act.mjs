#!/usr/bin/env node
/**
 * no-autonomous-legal-act lint — enforce ADR-2605302345 §D2 G18.
 *
 * The etzhayyim counsel-operated comms gateway (fax / email / e-filing)
 * may transmit a LEGAL ACT (court filing, pleading / 準備書面, formal
 * notice / 内容証明, demand / representation letter) ONLY when a human
 * lawyer licensed in the destination jurisdiction has actuated and signed
 * it with their OWN credential. etzhayyim holds no signing key, seal or
 * credential for any legal act (extends no-server-key ADR-2605231525).
 * The corp orchestrates; counsel acts. Autonomous (lawyer-absent)
 * drafting/filing/representation is UPL in every jurisdiction surveyed in
 * ADR-2605302200 and is structurally forbidden here.
 *
 * Two precise checks (designed for ~zero false positives):
 *
 *   Check A — schema invariant (always, over the canonical lexicon).
 *     com.etzhayyim.legal.outboundLegalAct MUST, structurally:
 *       (1) require `counselActuation` AND `actuatedByLicensedCounsel`
 *           in the record `required` array;
 *       (2) carry `actuatedByLicensedCounsel` with `const: true`;
 *       (3) define a `counselActuation` object requiring `counselDid` +
 *           `counselSignatureRef` (counsel signs with their own key);
 *       (4) carry NO corp-held-signing-key property (deny-list) — a
 *           platform signing capability must be unrepresentable.
 *
 *   Check B — code marker deny-list (over staged legal-comms code).
 *     Scans gateway CODE for unambiguous markers of autonomous legal
 *     acts (e.g. autonomousFiling / autoFileToCourt / selfSignPleading /
 *     platformAsCounsel / holdAttorneyCredential). These tokens only
 *     exist if someone is bypassing counsel actuation.
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
const LEGAL_ACT_LEX =
  "00-contracts/lexicons/com/etzhayyim/legal/outboundLegalAct.json";

// Property names that would represent a platform/corp-held signing
// capability for a legal act — must NEVER appear.
const CORP_SIGNING_PROPS = [
  "corpSigningKey",
  "platformSignature",
  "platformSigningKey",
  "selfActuated",
  "autonomousFiling",
  "serverHeldCredential",
  "courtCredentialHeld",
];

// ── Check B: legal-comms CODE marker deny-list ───────────────────────
const LEGAL_COMMS_CODE_RE =
  /(^|\/)(50-infra\/etzhayyim-legal-comms\/|.*legal-comms.*|.*legalComms.*)\S*\.(py|ts|tsx|mjs|cjs|js|go|rs)$/;

// Unambiguous autonomous-legal-act marker tokens (case-insensitive).
const AUTONOMOUS_MARKERS = [
  "autonomousfiling",
  "autofiletocourt",
  "selfsignpleading",
  "selfsignfiling",
  "platformascounsel",
  "holdattorneycredential",
  "filewithoutcounsel",
  "skipcounselactuation",
];

let violations = 0;

// ── Run Check A over the canonical lexicon (always) ──────────────────
{
  const abs = resolve(process.cwd(), LEGAL_ACT_LEX);
  if (existsSync(abs)) {
    let doc;
    try {
      doc = JSON.parse(readFileSync(abs, "utf8"));
    } catch (e) {
      console.error(`[X] ${LEGAL_ACT_LEX}: invalid JSON (${e.message}).`);
      violations += 1;
      doc = null;
    }
    if (doc) {
      const rec = doc?.defs?.main?.record ?? {};
      const required = rec?.required ?? [];
      const props = rec?.properties ?? {};

      // (1) required must include counselActuation + actuatedByLicensedCounsel
      for (const must of ["counselActuation", "actuatedByLicensedCounsel"]) {
        if (!required.includes(must)) {
          console.error(
            `[X] ${LEGAL_ACT_LEX}: '${must}' MUST be in the record ` +
              `\`required\` array (ADR-2605302345 G18).`,
          );
          violations += 1;
        }
      }

      // (2) actuatedByLicensedCounsel const:true
      const flag = props.actuatedByLicensedCounsel;
      if (!flag || flag.const !== true) {
        console.error(
          `[X] ${LEGAL_ACT_LEX}: 'actuatedByLicensedCounsel' MUST have ` +
            `\`const: true\` (G18 — autonomous legal act unrepresentable).`,
        );
        violations += 1;
      }

      // (3) counselActuation def requires counselDid + counselSignatureRef
      const ca = doc?.defs?.counselActuation ?? {};
      const caReq = ca?.required ?? [];
      for (const must of ["counselDid", "counselSignatureRef"]) {
        if (!caReq.includes(must)) {
          console.error(
            `[X] ${LEGAL_ACT_LEX}: counselActuation MUST require '${must}' ` +
              `(counsel signs with their own credential, G18).`,
          );
          violations += 1;
        }
      }

      // (4) no corp-held signing-key property anywhere in the lexicon
      const blob = JSON.stringify(doc).toLowerCase();
      for (const p of CORP_SIGNING_PROPS) {
        if (blob.includes(p.toLowerCase())) {
          console.error(
            `[X] ${LEGAL_ACT_LEX}: corp/platform signing property '${p}' is ` +
              `PROHIBITED — etzhayyim holds no legal-act signing key (G18 / ` +
              `no-server-key ADR-2605231525).`,
          );
          violations += 1;
        }
      }
    }
  }
}

// ── Run Check B over staged legal-comms code ─────────────────────────
for (const file of args) {
  if (!LEGAL_COMMS_CODE_RE.test(file)) continue;
  const abs = resolve(process.cwd(), file);
  if (!existsSync(abs)) continue;
  let content;
  try {
    content = readFileSync(abs, "utf8");
  } catch {
    continue;
  }
  const lower = content.toLowerCase();
  for (const marker of AUTONOMOUS_MARKERS) {
    if (lower.includes(marker)) {
      console.error(
        `[X] ${file}: autonomous-legal-act marker '${marker}' is PROHIBITED. ` +
          `Every legal act requires human licensed-counsel actuation ` +
          `(ADR-2605302345 G18).`,
      );
      violations += 1;
    }
  }
}

if (violations > 0) {
  console.error(
    `\n${violations} no-autonomous-legal-act violation(s). The corp ` +
      `orchestrates; licensed counsel acts. A legal act with no human ` +
      `counsel actuation is UPL — see ADR-2605302345 §D2 (G18).`,
  );
  process.exit(1);
}

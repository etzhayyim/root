#!/usr/bin/env node
/**
 * transparency-floor-and-gate lint — enforce ADR-2605310100 §4 + §5.
 *
 * Pre-commit gate for the Covenant Transparency Doctrine
 * (`com.etzhayyim.transparency.*`). The doctrine amends a constitutional
 * invariant (ADR-2605181100 confidentiality) and therefore MUST NOT
 * self-execute: nothing flips until Council Lv7+ unanimity (Charter §0.4)
 * is recorded on-chain (§5). This guard makes that gate — and the §4
 * non-waivable floor — machine-enforced rather than merely documented.
 *
 * Three precise checks (designed for ~zero false positives):
 *
 *   Check A — §5 ratification gate (schema anchor, runs always).
 *     Every `com.etzhayyim.transparency.*` Lexicon record MUST carry a
 *     `ratificationStatus` property with `const: "proposed-unratified"`.
 *     The doctrine cannot be flipped to a ratified state at the schema
 *     layer; flipping requires a deliberate edit this guard will catch.
 *
 *   Check B — §4 non-waivable floor (schema anchor, runs always).
 *     - accessLogPublication.secretsRedacted   → const: true
 *     - accessLogPublication.ingressConsentBasis → const: "ingress-act"
 *     - redactionMethodNote.failClosed          → const: true
 *     The floor (secrets/keys never published; consent is ingress-based)
 *     cannot be silently removed.
 *
 *   Check C — premature execution in code (runs over staged args).
 *     Any transparency-pathed CODE file (.py/.ts/.mjs/.js/.rs) that sets a
 *     `ratificationStatus` / `ratification_status` to anything other than
 *     "proposed-unratified" MUST also carry a `councilRatificationCid` in
 *     the same file — otherwise it is executing the gate without the
 *     Council proof (§5). The guard's own files are exempt by name.
 *
 * Exit code 0 on success, 1 on violation.
 *
 * Authoritative ADR:
 *   90-docs/adr/2605310100-covenant-transparency-doctrine-anti-anonymity-and-ingress-logging.md
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve, basename } from "node:path";

const args = process.argv.slice(2);

// ── Canonical lexicon anchors (Checks A + B, always) ─────────────────
const LEX_DIR = "00-contracts/lexicons/com/etzhayyim/transparency";
const INGRESS_LEX = `${LEX_DIR}/ingressDisclosureNotice.json`;
const ACCESSLOG_LEX = `${LEX_DIR}/accessLogPublication.json`;
const ATTEST_LEX = `${LEX_DIR}/covenantTransparencyAttestation.json`;
const REDACTION_LEX = `${LEX_DIR}/redactionMethodNote.json`;
const ALL_LEXICONS = [INGRESS_LEX, ACCESSLOG_LEX, ATTEST_LEX, REDACTION_LEX];

const PROPOSED = "proposed-unratified";

// ── Check C scope ────────────────────────────────────────────────────
const TRANSPARENCY_CODE_RE = /transparency\S*\.(py|ts|mjs|js|rs)$/;
const GUARD_SELF_RE = /transparency-floor-and-gate(\.test)?\.mjs$/;
const RATIFICATION_SET_RE =
  /ratification[_]?status\s*[:=]\s*["'`]([^"'`]+)["'`]/gi;

let violations = 0;

function props(doc) {
  return doc?.defs?.main?.record?.properties ?? {};
}

// ── Checks A + B over the canonical lexicon files (always) ───────────
for (const lexPath of ALL_LEXICONS) {
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
  const p = props(doc);

  // Check A — ratificationStatus const must be "proposed-unratified"
  const rs = p.ratificationStatus;
  if (!rs || rs.const !== PROPOSED) {
    console.error(
      `[X] ${lexPath}: 'ratificationStatus' MUST be present with ` +
        `\`const: "${PROPOSED}"\` (ADR-2605310100 §5 — the doctrine cannot ` +
        `self-execute before Council Lv7+ ratification).`,
    );
    violations += 1;
  }

  // Check B — §4 floor anchors
  if (lexPath === ACCESSLOG_LEX) {
    if (p.secretsRedacted?.const !== true) {
      console.error(
        `[X] ${lexPath}: 'secretsRedacted' MUST be \`const: true\` ` +
          `(ADR-2605310100 §4(1) — access-control material is never published).`,
      );
      violations += 1;
    }
    if (p.ingressConsentBasis?.const !== "ingress-act") {
      console.error(
        `[X] ${lexPath}: 'ingressConsentBasis' MUST be ` +
          `\`const: "ingress-act"\` (ADR-2605310100 §3 — consent is the act of access).`,
      );
      violations += 1;
    }
  }
  if (lexPath === REDACTION_LEX) {
    if (p.failClosed?.const !== true) {
      console.error(
        `[X] ${lexPath}: 'failClosed' MUST be \`const: true\` ` +
          `(ADR-2605310100 §4 — the redaction filter redacts on any uncertainty).`,
      );
      violations += 1;
    }
  }
}

// ── Check C over staged transparency code files ──────────────────────
for (const file of args) {
  if (!TRANSPARENCY_CODE_RE.test(file)) continue;
  if (GUARD_SELF_RE.test(basename(file))) continue; // the guard + its test are exempt
  const abs = resolve(process.cwd(), file);
  if (!existsSync(abs)) continue;
  let content;
  try {
    content = readFileSync(abs, "utf8");
  } catch {
    continue;
  }
  const hasCouncilProof = content.includes("councilRatificationCid");
  for (const m of content.matchAll(RATIFICATION_SET_RE)) {
    const value = m[1];
    if (value === PROPOSED) continue; // the inert default is always allowed
    if (!hasCouncilProof) {
      console.error(
        `[X] ${file}: sets ratificationStatus='${value}' without a ` +
          `'councilRatificationCid' in the file. The doctrine cannot be ` +
          `executed before Council Lv7+ ratification (ADR-2605310100 §5).`,
      );
      violations += 1;
    }
  }
}

if (violations > 0) {
  console.error(
    `\n${violations} transparency-floor-and-gate violation(s). The Covenant ` +
      `Transparency Doctrine stays \`proposed-unratified\` until Council Lv7+ ` +
      `unanimity is recorded — see ADR-2605310100 §4 (floor) + §5 (gate).`,
  );
  process.exit(1);
}
process.exit(0);

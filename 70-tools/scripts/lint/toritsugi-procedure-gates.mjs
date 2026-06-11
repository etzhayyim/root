#!/usr/bin/env node
/**
 * toritsugi-procedure-gates lint — enforce ADR-2605312030 §4 (G1..G15).
 *
 * Pre-commit gate for the 取次 (toritsugi) citizen-facing government-procedure
 * concierge (`com.etzhayyim.toritsugi.*` + `kotodama.cells.toritsugi_*`).
 * toritsugi is an R0 scaffold whose constitutional ceiling — 行政書士法/UPL
 * boundary (G5), verified-procedure-only submission (G14), member-self-submission
 * default (G15), PII-encrypted (G6), non-fabrication (G8) — MUST be machine
 * enforced rather than merely documented, so a future refactor cannot silently
 * weaken it.
 *
 * Node-standalone (no pytest dependency) so it can run under lefthook /
 * CI on every commit. Complements 70-tools/scripts/audit/test_toritsugi_invariants.py
 * (which adds Python import-raise coverage).
 *
 * Six precise checks (designed for ~zero false positives):
 *
 *   Check A — G5 行政書士法/UPL boundary (applicationDraft schema anchor).
 *     applicationDraft.assistMode.knownValues MUST be exactly ["input-assist"]
 *     — 作成代理 is unrepresentable at the schema layer.
 *
 *   Check B — G15 member-self-submission default (submissionRecord schema).
 *     submissionRecord.mode is required, knownValues exactly
 *     {member-self-submit, agent-on-behalf} with member-self-submit FIRST, and
 *     a councilGateRef property exists (the 代行 R3 gate).
 *
 *   Check C — G8 non-fabrication + G14 (procedure schema).
 *     procedure REQUIRES legalBasis + provenance + verificationStatus; the
 *     verificationStatus knownValues are exactly the three verification tiers.
 *
 *   Check D — G6 PII confidentiality (PII-bearing record schemas).
 *     Each PII-bearing record exposes ONLY an encrypted-envelope pointer
 *     (*Ref) and never an inline plaintext field (content/plaintext/rawForm/
 *     piiInline).
 *
 *   Check E — Lexicon v1 (no float).
 *     No `"type": "number"` anywhere in the toritsugi lexicons.
 *
 *   Check F — G15 structural double-gate (submit cell code anchor).
 *     toritsugi_submit/cell.py pins `DAIKOU_R3_GATE_TX: str | None = None`
 *     (代行 cannot be reached without a deliberate edit this guard catches).
 *
 * Exit code 0 on success, 1 on violation. Args are ignored (whole-tree anchors).
 *
 * Authoritative ADR:
 *   90-docs/adr/2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0.md
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const LEX_DIR = "00-contracts/lexicons/com/etzhayyim/toritsugi";
const PROCEDURE = `${LEX_DIR}/procedure.json`;
const DRAFT = `${LEX_DIR}/applicationDraft.json`;
const SUBMISSION = `${LEX_DIR}/submissionRecord.json`;
const BENEFIT = `${LEX_DIR}/benefitMatch.json`;
const STATUS = `${LEX_DIR}/statusTrack.json`;
const ALL_LEXICONS = [
  PROCEDURE,
  DRAFT,
  SUBMISSION,
  BENEFIT,
  STATUS,
  `${LEX_DIR}/procedureGuide.json`,
];

const SUBMIT_CELL = "40-engine/kotoba/crates/kotoba-kotodama/cells/toritsugi_submit/cell.py";

const FORBIDDEN_INLINE = ["content", "plaintext", "rawForm", "piiInline"];
const PII_RECORDS = {
  [DRAFT]: "encryptedDraftRef",
  [BENEFIT]: "encryptedDetailRef",
  [STATUS]: "resultRef",
  [SUBMISSION]: "receiptRef",
};

let violations = 0;
const fail = (msg) => {
  console.error(`✗ ${msg}`);
  violations++;
};

function load(path) {
  const abs = resolve(process.cwd(), path);
  if (!existsSync(abs)) return null;
  try {
    return JSON.parse(readFileSync(abs, "utf8"));
  } catch (e) {
    fail(`${path}: invalid JSON (${e.message})`);
    return undefined;
  }
}

function props(doc) {
  return doc?.defs?.main?.record?.properties ?? {};
}
function required(doc) {
  return doc?.defs?.main?.record?.required ?? [];
}
function arrEq(a, b) {
  return Array.isArray(a) && a.length === b.length && a.every((v, i) => v === b[i]);
}
function setEq(a, b) {
  return Array.isArray(a) && a.length === b.length && b.every((v) => a.includes(v));
}

// ── Check A — G5: applicationDraft.assistMode is exactly ["input-assist"] ──
{
  const doc = load(DRAFT);
  if (doc) {
    const km = props(doc).assistMode?.knownValues;
    if (!arrEq(km, ["input-assist"])) {
      fail(`${DRAFT}: G5 行政書士法/UPL — assistMode.knownValues MUST be exactly ["input-assist"] (作成代理 unrepresentable)`);
    }
    if (!required(doc).includes("memberConfirmed")) {
      fail(`${DRAFT}: G8 — memberConfirmed MUST be required (member confirms before submission)`);
    }
  }
}

// ── Check B — G15: submissionRecord.mode self-submit default + 代行 gate ──
{
  const doc = load(SUBMISSION);
  if (doc) {
    const p = props(doc);
    if (!required(doc).includes("mode")) {
      fail(`${SUBMISSION}: G15 — mode MUST be required`);
    }
    const modes = p.mode?.knownValues;
    if (!setEq(modes, ["member-self-submit", "agent-on-behalf"])) {
      fail(`${SUBMISSION}: G15 — mode.knownValues MUST be {member-self-submit, agent-on-behalf}`);
    } else if (modes[0] !== "member-self-submit") {
      fail(`${SUBMISSION}: G15 — member-self-submit MUST be the first (default) mode`);
    }
    if (!("councilGateRef" in p)) {
      fail(`${SUBMISSION}: G15 — councilGateRef MUST exist (代行/agent-on-behalf R3 gate)`);
    }
  }
}

// ── Check C — G8 + G14: procedure requires legalBasis/provenance/verificationStatus ──
{
  const doc = load(PROCEDURE);
  if (doc) {
    const req = required(doc);
    for (const f of ["legalBasis", "provenance", "verificationStatus"]) {
      if (!req.includes(f)) {
        fail(`${PROCEDURE}: G8/G14 — procedure MUST require ${f}`);
      }
    }
    const vs = props(doc).verificationStatus?.knownValues;
    if (!setEq(vs, ["unverified-seed", "maintainer-verified", "council-verified"])) {
      fail(`${PROCEDURE}: G14 — verificationStatus.knownValues MUST be the three verification tiers`);
    }
  }
}

// ── Check D — G6: PII records expose ONLY an encrypted pointer ──
for (const [path, ptr] of Object.entries(PII_RECORDS)) {
  const doc = load(path);
  if (!doc) continue;
  const p = props(doc);
  if (!(ptr in p)) {
    fail(`${path}: G6 — MUST expose encrypted-envelope pointer "${ptr}"`);
  }
  for (const bad of FORBIDDEN_INLINE) {
    if (bad in p) {
      fail(`${path}: G6 — MUST NOT inline PII (forbidden field "${bad}")`);
    }
  }
}

// ── Check E — Lexicon v1: no float ──
for (const path of ALL_LEXICONS) {
  const abs = resolve(process.cwd(), path);
  if (!existsSync(abs)) continue;
  if (readFileSync(abs, "utf8").includes('"type": "number"')) {
    fail(`${path}: Lexicon v1 — no "type": "number" (ADR-2605190900)`);
  }
}

// ── Check F — G15 structural double-gate: submit cell pins DAIKOU_R3_GATE_TX = None ──
{
  const abs = resolve(process.cwd(), SUBMIT_CELL);
  if (existsSync(abs)) {
    const txt = readFileSync(abs, "utf8");
    if (!txt.includes("DAIKOU_R3_GATE_TX: str | None = None")) {
      fail(`${SUBMIT_CELL}: G15 — 代行 R3 gate MUST pin "DAIKOU_R3_GATE_TX: str | None = None"`);
    }
  }
}

if (violations > 0) {
  console.error(`\n✗ toritsugi-procedure-gates: ${violations} violation(s)`);
  process.exit(1);
} else {
  console.log("✓ toritsugi-procedure-gates: clean");
}

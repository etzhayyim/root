#!/usr/bin/env node
/**
 * legal-jurisdiction-consistency lint — drift-guard for the legal-services
 * `enabled` jurisdiction set (ADR-2605302200 §D4).
 *
 * The set of jurisdictions whose free legal-aid lane is `enabled` (as opposed
 * to `verify-required`) is currently represented in THREE artifacts that must
 * never disagree:
 *
 *   (1) the standalone WASM intake gate — Rust const ENABLED_JURISDICTIONS
 *       orgs/etzhayyim/com-etzhayyim-legal-aid-wasm-guest/src/lib.rs
 *       (validated in that repository's CI)
 *   (2) the LangGraph cell port        — Python `enabled = {...}`
 *       40-engine/kotoba/crates/kotoba-kotodama/cells/chigiri_legal_aid_clinic/ports.py
 *   (3) the kotoba KG routing-table    — jurisdictionPolicy records with
 *       enableState=="enabled"
 *       90-docs/baien/kg-deploy/2605302200-jurisdiction-policy-kg-segment.ndjson
 *
 * If these drift, a matter could be opened (or refused) inconsistently across
 * the gate, the orchestrator, and the published policy data. This guard parses
 * all three and fails on any mismatch. Runs against the canonical paths whether
 * or not they were passed as args.
 *
 * Exit 0 on agreement, 1 on drift.
 *
 * Authoritative ADR:
 *   90-docs/adr/2605302200-chigiri-unpaid-legal-aid-lane-multijurisdiction.md
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const RUST = "../com-etzhayyim-legal-aid-wasm-guest/src/lib.rs";
const PORTS = "40-engine/kotoba/crates/kotoba-kotodama/cells/chigiri_legal_aid_clinic/ports.py";
const KG = "90-docs/baien/kg-deploy/2605302200-jurisdiction-policy-kg-segment.ndjson";

const read = (p) => {
  const abs = resolve(process.cwd(), p);
  return existsSync(abs) ? readFileSync(abs, "utf8") : null;
};

const setEq = (a, b) =>
  a.size === b.size && [...a].every((x) => b.has(x));

const fmt = (s) => `{${[...s].sort().join(", ")}}`;

let violations = 0;

// ── (1) Rust const ENABLED_JURISDICTIONS = &["jpn", "deu", ...]; ──
function rustEnabled(src) {
  const m = src.match(/ENABLED_JURISDICTIONS[^=]*=\s*&?\[([\s\S]*?)\]/);
  if (!m) return null;
  return new Set([...m[1].matchAll(/"([a-z0-9-]+)"/g)].map((x) => x[1]));
}

// ── (2) Python `enabled = {"jpn", "deu", ...}` ──
function pyEnabled(src) {
  const m = src.match(/enabled\s*=\s*\{([^}]*)\}/);
  if (!m) return null;
  return new Set([...m[1].matchAll(/"([a-z0-9-]+)"/g)].map((x) => x[1]));
}

// ── (3) KG ndjson: jurisdictionPolicy entities with enableState=="enabled" ──
function kgEnabled(src) {
  const out = new Set();
  for (const line of src.split("\n")) {
    const s = line.trim();
    if (!s) continue;
    let e;
    try {
      e = JSON.parse(s);
    } catch {
      continue;
    }
    const claims = e.claims ?? [];
    const state = claims.find((c) => c.pred === "enableState")?.value;
    if (state === "enabled") out.add(e.id.split("/").pop());
  }
  return out;
}

const srcRust = read(RUST);
const srcPorts = read(PORTS);
const srcKg = read(KG);

const sets = {};
if (srcRust) {
  const s = rustEnabled(srcRust);
  if (!s) {
    console.error(`[X] ${RUST}: could not parse ENABLED_JURISDICTIONS`);
    violations += 1;
  } else sets.rust = s;
}
if (srcPorts) {
  const s = pyEnabled(srcPorts);
  if (!s) {
    console.error(`[X] ${PORTS}: could not parse \`enabled = {...}\``);
    violations += 1;
  } else sets.ports = s;
}
if (srcKg) sets.kg = kgEnabled(srcKg);

// Compare every present pair against the first present set.
const names = Object.keys(sets);
if (names.length >= 2) {
  const ref = names[0];
  for (const n of names.slice(1)) {
    if (!setEq(sets[ref], sets[n])) {
      console.error(
        `[X] legal-services enabled-jurisdiction drift:\n` +
          `      ${ref}: ${fmt(sets[ref])}\n` +
          `      ${n}: ${fmt(sets[n])}\n` +
          `    All three (Rust guest / cell port / KG policy data) MUST agree ` +
          `(ADR-2605302200 §D4).`,
      );
      violations += 1;
    }
  }
}

if (violations > 0) {
  console.error(
    `\n${violations} legal-jurisdiction-consistency violation(s). The enabled ` +
      `jurisdiction set must be identical across the WASM gate, the cell port, ` +
      `and the kotoba policy data.`,
  );
  process.exit(1);
}

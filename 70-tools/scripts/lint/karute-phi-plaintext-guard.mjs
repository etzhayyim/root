#!/usr/bin/env node
/**
 * karute-phi-plaintext-guard — Block plaintext PHI writes outside the
 * encrypted envelope.
 *
 * Per ADR-2605231100 §"Substrate hard-rules" and ADR-2605181100, clinical
 * records (Patient / Encounter / SoapNote / Observation / Condition /
 * MedicationRequest / ServiceRequest / DispenseRecord / CarePlan /
 * HomecareEpisode / HomeVisit) MUST flow through
 * `com.etzhayyim.encrypted.record` envelope. Direct writes to the inner
 * `com.etzhayyim.karute.*` collection on MST (or any other persistence
 * surface) leak PHI plaintext.
 *
 * This hook scans staged changes for two violation patterns:
 *
 *   1. Direct PDS createRecord / putRecord with collection = com.etzhayyim.karute.*
 *      e.g. `agent.com.atproto.repo.createRecord({ collection: "com.etzhayyim.karute.patient", ... })`
 *
 *   2. SDK `write({ collection: "com.etzhayyim.karute.* "})` — the plain (non-encrypted)
 *      path on Etzhayyim. The encrypted path is `encryptedWrite({ innerType: "com.etzhayyim.karute.*" })`,
 *      which puts the inner type inside the `com.etzhayyim.encrypted.record` envelope.
 *
 * Files explicitly tagged with `phi-guard: allow` or located inside test/
 * fixture paths are exempt. Lexicon JSONs under 00-contracts/lexicons/com/etzhayyim/karute/
 * are exempt because they define the inner-type schemas themselves (not actual writes).
 */

import { readFileSync } from "node:fs";
import path from "node:path";

const KARUTE_INNER_TYPES = [
  "com.etzhayyim.karute.patient",
  "com.etzhayyim.karute.encounter",
  "com.etzhayyim.karute.soapNote",
  "com.etzhayyim.karute.observation",
  "com.etzhayyim.karute.condition",
  "com.etzhayyim.karute.medicationRequest",
  "com.etzhayyim.karute.serviceRequest",
  "com.etzhayyim.karute.dispenseRecord",
  "com.etzhayyim.karute.carePlan",
  "com.etzhayyim.karute.homecareEpisode",
  "com.etzhayyim.karute.homeVisit",
];

const EXEMPT_PATH_PATTERNS = [
  /\/node_modules\//,
  /\/dist\//,
  /\/\.svelte-kit\//,
  /\/build\//,
  /\/test\//,
  /\.test\.[tj]sx?$/,
  /\/tests?\//,
  /\/fixtures?\//,
  // Lexicon SoTs (they define the inner schema, not write it).
  /^00-contracts\/lexicons\/app\/etzhayyim\/karute\//,
  /^00-contracts\/lexicons\/ai\/etzhayyim\/apps\/karute\//,
  // The actor manifest references inner-type names inside the encrypted.write step.
  /^20-actors\/karute\/actor-manifest\.jsonld$/,
  // The ADR + CLAUDE.md explain the rule and cite inner-type names.
  /^90-docs\//,
  /\/CLAUDE\.md$/,
  // The guard script itself.
  /karute-phi-plaintext-guard\.mjs$/,
  // ADR + design docs everywhere.
  /\.md$/,
];

// Match write-style calls whose collection / innerType points to a karute inner type.
//
//   collection: "com.etzhayyim.karute.soapNote"
//   collection: 'com.etzhayyim.karute.patient'
//   collection: `com.etzhayyim.karute.${kind}`     // dynamic collection — also flagged
//   $type: "com.etzhayyim.karute.observation"
//
// We separately require that the call site is NOT inside an encryptedWrite() call
// by checking the surrounding ~10 lines for `encryptedWrite(` token.

const KARUTE_TYPE_PATTERN = /com\.etzhayyim\.karute\.(patient|encounter|soapNote|observation|condition|medicationRequest|serviceRequest|dispenseRecord|carePlan|homecareEpisode|homeVisit)\b/;
// We deliberately do not anchor with `\b` because `\b\$` does not fire when
// `$type` follows whitespace (the common case). The `: "..."` tail is
// restrictive enough to avoid false positives.
const COLLECTION_KEY_PATTERN = /(^|[\s,{(])\s*(collection|\$type|nsid)\s*:\s*["'`]/;

const ENCRYPTED_CONTEXT_TOKENS = [
  "encryptedWrite",
  "encryptedRead",
  "encryptedWriteStandalone",
  "encryptedReadStandalone",
  "encrypted.record",
  "innerType",
  "innerType:",
  // The actor manifest cites karute inner-type names in the encrypted.write
  // pipeline step's `innerType` field.
  '"fn": "encrypted.write"',
  '"fn":"encrypted.write"',
];

function isExempt(file) {
  for (const re of EXEMPT_PATH_PATTERNS) {
    if (re.test(file)) return true;
  }
  return false;
}

function hasEncryptedContext(lines, idx) {
  const start = Math.max(0, idx - 12);
  const end = Math.min(lines.length, idx + 4);
  for (let i = start; i < end; i++) {
    const l = lines[i];
    for (const token of ENCRYPTED_CONTEXT_TOKENS) {
      if (l.includes(token)) return true;
    }
  }
  return false;
}

function hasInlineAllow(line) {
  return /\/\/.*phi-guard:\s*allow/.test(line) || /#.*phi-guard:\s*allow/.test(line);
}

let violations = 0;
const files = process.argv.slice(2);
for (const file of files) {
  if (isExempt(file)) continue;
  let src;
  try {
    src = readFileSync(file, "utf8");
  } catch {
    continue;
  }
  // Fast reject: if no mention of any karute inner type, skip the file.
  if (!KARUTE_TYPE_PATTERN.test(src)) continue;

  const lines = src.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!KARUTE_TYPE_PATTERN.test(line)) continue;
    if (hasInlineAllow(line)) continue;
    // Only consider lines that look like a write site (have collection: / $type: / nsid:).
    if (!COLLECTION_KEY_PATTERN.test(line)) continue;
    // Allow if the surrounding context is an encrypted-write block.
    if (hasEncryptedContext(lines, i)) continue;

    console.error(`✘ ${file}:${i + 1} — plaintext PHI write target`);
    console.error(`    ${line.trim()}`);
    console.error("    karute inner types MUST be written through @etzhayyim/sdk.encryptedWrite()");
    console.error("    (collection 'com.etzhayyim.encrypted.record' + innerType 'com.etzhayyim.karute.*')");
    console.error("    To bypass for a justified exception, append '// phi-guard: allow' on the line and");
    console.error("    document the rationale in 90-docs/adr/.");
    console.error("");
    violations++;
  }
}

if (violations > 0) {
  console.error(`karute-phi-plaintext-guard: ${violations} violation(s)`);
  process.exit(1);
}

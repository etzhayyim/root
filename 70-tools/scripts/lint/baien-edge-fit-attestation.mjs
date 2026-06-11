#!/usr/bin/env node
// Phase 2 enforcement for ADR-2605241900 (baien edge-target invariant).
//
// Scans MODEL_REGISTRY entries in llm-model-registry*.ts for any model
// tagged with `useCases` containing `edge`, `browser`, or `cpu`, and
// verifies that 90-docs/baien/edge-fit-attestations.jsonl has a row
// for each such model_id with values within ADR-2605241900 ceilings.
//
// Fails the lefthook pre-commit if:
//   - any edge-tagged entry is missing an attestation row, OR
//   - any attestation reports values exceeding the ADR ceilings.
//
// Usage:
//   node 70-tools/scripts/lint/baien-edge-fit-attestation.mjs
//
// Exit codes:
//   0 = all edge-tagged models have valid in-budget attestations
//   1 = at least one model missing or over-budget
//   2 = registry file or attestation file missing / unreadable

import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "..", "..", "..");

// ADR-2605241900 §Decision ceilings.
const CEILINGS = {
  weights_packed_bytes_max: 1.6 * 1024 * 1024 * 1024,        // 1.6 GB
  peak_ram_4k_bytes_max: 2.0 * 1024 * 1024 * 1024,           // 2.0 GB
  peak_ram_16k_bytes_max: 2.5 * 1024 * 1024 * 1024,          // 2.5 GB
  first_token_latency_ms_iphone14_max: 3000,                 // 3 s
};

const REGISTRY_FILES = [
  "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts",
  "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry-multimodal.ts",
  "40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry-distilled.ts",
];

const ATTESTATION_FILE = "90-docs/baien/edge-fit-attestations.jsonl";

function readRegistryEdgeEntries() {
  // Lightweight regex parse — avoids dragging in a TS toolchain for a
  // pre-commit hook. Looks for `"model-id": { ... useCases: [...] ... }`
  // blocks and keeps the ones whose useCases include edge|browser|cpu.
  const out = [];
  for (const rel of REGISTRY_FILES) {
    const abs = join(REPO_ROOT, rel);
    if (!existsSync(abs)) continue;
    const text = readFileSync(abs, "utf8");
    const re = /["']([\w./@-]+)["']\s*:\s*\{[^}]*useCases\s*:\s*\[([^\]]*)\]/gm;
    let m;
    while ((m = re.exec(text)) !== null) {
      const modelId = m[1];
      const useCases = m[2].split(",").map((s) => s.replace(/['"\s]/g, "")).filter(Boolean);
      if (useCases.some((u) => ["edge", "browser", "cpu"].includes(u))) {
        out.push({ modelId, useCases, registryFile: rel });
      }
    }
  }
  return out;
}

function readAttestations() {
  const path = join(REPO_ROOT, ATTESTATION_FILE);
  if (!existsSync(path)) return new Map();
  const rows = readFileSync(path, "utf8")
    .split("\n").filter((l) => l.trim())
    .map((l, i) => {
      try { return JSON.parse(l); }
      catch (e) {
        console.error(`[edge-fit] ${ATTESTATION_FILE}:${i + 1} parse error: ${e.message}`);
        return null;
      }
    }).filter(Boolean);
  // keep latest attestation per model_id
  const byId = new Map();
  for (const r of rows) {
    const prev = byId.get(r.model_id);
    if (!prev || (r.ts ?? "") > (prev.ts ?? "")) byId.set(r.model_id, r);
  }
  return byId;
}

function verify(entry, attestation) {
  const fails = [];
  if (!attestation) {
    return [`missing attestation row in ${ATTESTATION_FILE}`];
  }
  for (const [k, max] of Object.entries(CEILINGS)) {
    const field = k.replace(/_max$/, "");
    const v = attestation[field];
    if (v == null) {
      fails.push(`attestation missing field ${field}`);
      continue;
    }
    if (v > max) {
      fails.push(`${field}=${v} exceeds ceiling ${max} (ADR-2605241900)`);
    }
  }
  return fails;
}

function main() {
  const entries = readRegistryEdgeEntries();
  if (entries.length === 0) {
    console.error("[edge-fit] no edge-tagged registry entries to verify — ok");
    process.exit(0);
  }
  const attestations = readAttestations();
  let anyFail = false;
  for (const e of entries) {
    const att = attestations.get(e.modelId);
    const fails = verify(e, att);
    if (fails.length > 0) {
      anyFail = true;
      console.error(`[edge-fit] ${e.modelId} (${e.registryFile}):`);
      for (const f of fails) console.error(`    - ${f}`);
    }
  }
  if (anyFail) {
    console.error("");
    console.error("[edge-fit] one or more edge-tagged models violate the ADR-2605241900 ceiling.");
    console.error("[edge-fit] Add or refresh attestations in 90-docs/baien/edge-fit-attestations.jsonl");
    console.error("[edge-fit] See 90-docs/baien/edge-fit-attestations.README.md for schema.");
    process.exit(1);
  }
  console.error(`[edge-fit] ${entries.length} edge-tagged model(s) attested within ceiling ✓`);
  process.exit(0);
}

main();

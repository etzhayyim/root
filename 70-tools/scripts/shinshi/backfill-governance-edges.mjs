#!/usr/bin/env node
// Thin driver for shinshi.backfillGovernanceEdges BPMN.
//
// Replaces: 60-apps/etzhayyim-project-shinshi/scripts/backfill-governance-edges.py
// That script iterated 247 models from the manifest and INSERTed 2 policy
// edges each via direct psycopg2. This driver just reads the manifest +
// POSTs the model list to the BPMN which does the diff + insert + audit.
//
// Usage:
//   MANIFEST_PATH=/path/to/models.json node 70-tools/scripts/shinshi/backfill-governance-edges.mjs
//
// Env:
//   DISPATCHER_URL  (default https://dispatcher.etzhayyim.com)
//   MANIFEST_PATH   required; the manifest belongs to the invoking standalone app/repository

import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const DISPATCHER = (process.env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/$/, "");
const MANIFEST = process.env.MANIFEST_PATH;
if (!MANIFEST) {
  throw new Error("MANIFEST_PATH is required; numbered-layer app paths are no longer operational inputs");
}

const raw = readFileSync(MANIFEST, "utf8");
const models = JSON.parse(raw);
if (!Array.isArray(models)) throw new Error("manifest must be an array");

// BPMN only needs {folder}; strip the rest to keep process variables small.
const body = { models: models.map((m) => ({ folder: m.folder })).filter((m) => m.folder) };
console.error(`driver: POSTing ${body.models.length} models → ${DISPATCHER}/xrpc/com.etzhayyim.apps.shinshi.backfillGovernanceEdges`);

const r = spawnSync("curl", [
  "-sS", "--max-time", "150",
  "-X", "POST", `${DISPATCHER}/xrpc/com.etzhayyim.apps.shinshi.backfillGovernanceEdges`,
  "-H", "Content-Type: application/json",
  "-d", JSON.stringify(body),
], { encoding: "utf8" });
if (r.status !== 0) {
  console.error(r.stderr);
  process.exit(1);
}

const out = JSON.parse(r.stdout);
const v = out?.variables ?? {};
console.log(JSON.stringify({
  ok: out.ok,
  latencyMs: out.latencyMs,
  models: body.models.length,
  candidates: v.candidateEdges ? v.candidateEdges.length : undefined,
  existing: Array.isArray(v.existingEdgeIds) ? v.existingEdgeIds.length : undefined,
  toInsert: Array.isArray(v.edgesToInsert) ? v.edgesToInsert.length : undefined,
  inserted: Array.isArray(v.insertResults)
    ? v.insertResults.reduce((s, x) => s + (x ?? 0), 0)
    : undefined,
}, null, 2));

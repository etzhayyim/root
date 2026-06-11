#!/usr/bin/env node
/**
 * Apply decided bindings (P2 gates) to the catalog graph.
 *
 * ADR-2605101000 §D3: P2 adapters refuse to run unless their target
 * binding is recorded in `edge_dataset_produces_vertex_type`. Training-
 * corpus emission additionally requires
 * `edge_dataset_allowed_for_training_task`. Both edges are
 * default-deny: their absence blocks projection / training. This script
 * is the only sanctioned write path for those two edges (apart from
 * direct SQL).
 *
 * JSON decision file is an array of records. Each record carries `kind`
 * = `produces_vertex` or `training_task`:
 *
 *   { "kind": "produces_vertex",
 *     "dataset_id": "bigquery-public-data:epa_historical_air_quality",
 *     "target_vertex_label": "vertex_air_quality_observation",
 *     "ingest_mode": "self_ingest",
 *     "scan_budget_tib": 0.1,
 *     "approved_by": "did:web:etzhayyim.com/jun@etzhayyim.com",
 *     "rationale": "EPA US-Public-Domain; partition_delta refresh" }
 *
 *   { "kind": "training_task",
 *     "dataset_id": "bigquery-public-data:epa_historical_air_quality",
 *     "training_task": "training.llm.text.curation",
 *     "license": "US-Public-Domain",
 *     "approved_by": "did:web:etzhayyim.com/jun@etzhayyim.com",
 *     "rationale": "License + PII clear; safe for text training" }
 *
 * Persistence: record-log semantics. Same `edge_id` re-INSERT = upsert.
 *
 * Usage:
 *   node 70-tools/scripts/bigquery-public-dataset-bindings-apply.mjs \
 *     --decisions /tmp/bq-allowlist/tier1-bindings.json \
 *     [--dry-run]
 */

import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";

const KOTOBA_URL = process.env.KOTOBA_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";
const COLLECTOR_DID = "did:web:bigquery.etzhayyim.com";

const args = process.argv.slice(2);
const arg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1];
};
const flag = (k) => args.includes(`--${k}`);

const DECISIONS = arg("decisions");
const DRY_RUN = flag("dry-run");

if (!DECISIONS) {
  console.error("[bq-bindings] ERROR: --decisions <file.json> required.");
  process.exit(1);
}

let _pgPool = null;
async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2 });
  return _pgPool;
}

function sha256(s) {
  return createHash("sha256").update(String(s)).digest("hex");
}

function vertexId(collection, rkey) {
  return `at://${COLLECTOR_DID}/${collection}/${rkey}`;
}

async function lookupCatalogVid(pool, datasetId) {
  const { rows } = await pool.query(
    `SELECT vertex_id FROM vertex_public_dataset_catalog WHERE dataset_id = $1 LIMIT 1`,
    [datasetId],
  );
  return rows[0]?.vertex_id ?? null;
}

async function applyProducesVertex(pool, d, observedAt) {
  const srcVid = await lookupCatalogVid(pool, d.dataset_id);
  if (!srcVid) return { ok: false, reason: "catalog_row_missing" };
  const target = d.target_vertex_label;
  const ingestMode = d.ingest_mode;
  if (!target || !ingestMode) return { ok: false, reason: "missing_target_or_mode" };
  const dstVid = `rw://${target}`; // virtual vertex id pointing at the target table label
  const edgeId = sha256(`produces|${srcVid}|${target}`);
  if (DRY_RUN) {
    return { ok: true, action: "dry-run", edgeId };
  }
  await pool.query(
    `INSERT INTO edge_dataset_produces_vertex_type (
       edge_id, src_vid, dst_vid, sensitivity_ord, owner_did,
       dataset_id, target_vertex_label, ingest_mode,
       approved_by, approved_at, scan_budget_tib,
       observed_at, actor_did, org_did, created_at
     ) VALUES (
       $1, $2, $3, 1, $4,
       $5, $6, $7,
       $8, $9, $10,
       $11, $12, $13, $14
     )`,
    [
      edgeId, srcVid, dstVid, COLLECTOR_DID,
      d.dataset_id, target, ingestMode,
      d.approved_by ?? null, observedAt, d.scan_budget_tib ?? null,
      observedAt, d.approved_by ?? COLLECTOR_DID, COLLECTOR_DID, observedAt,
    ],
  );
  return { ok: true, action: "applied", edgeId };
}

async function applyTrainingTask(pool, d, observedAt) {
  const srcVid = await lookupCatalogVid(pool, d.dataset_id);
  if (!srcVid) return { ok: false, reason: "catalog_row_missing" };
  const task = d.training_task;
  if (!task) return { ok: false, reason: "missing_training_task" };
  const dstVid = `task://${task}`;
  const edgeId = sha256(`training|${srcVid}|${task}`);
  if (DRY_RUN) {
    return { ok: true, action: "dry-run", edgeId };
  }
  await pool.query(
    `INSERT INTO edge_dataset_allowed_for_training_task (
       edge_id, src_vid, dst_vid, sensitivity_ord, owner_did,
       dataset_id, training_task, license,
       approved_by, approved_at,
       observed_at, actor_did, org_did, created_at
     ) VALUES (
       $1, $2, $3, 1, $4,
       $5, $6, $7,
       $8, $9,
       $10, $11, $12, $13
     )`,
    [
      edgeId, srcVid, dstVid, COLLECTOR_DID,
      d.dataset_id, task, d.license ?? null,
      d.approved_by ?? null, observedAt,
      observedAt, d.approved_by ?? COLLECTOR_DID, COLLECTOR_DID, observedAt,
    ],
  );
  return { ok: true, action: "applied", edgeId };
}

async function main() {
  const text = await readFile(DECISIONS, "utf8");
  const decisions = JSON.parse(text);
  if (!Array.isArray(decisions)) throw new Error("Decisions file must be an array.");

  const pool = await getRwPool();
  const observedAt = new Date().toISOString();
  const counts = { produces_vertex: 0, training_task: 0, skipped: 0, errors: 0 };
  const skipReasons = {};

  for (const d of decisions) {
    let r;
    try {
      if (d.kind === "produces_vertex") {
        r = await applyProducesVertex(pool, d, observedAt);
        if (r.ok) counts.produces_vertex += 1;
      } else if (d.kind === "training_task") {
        r = await applyTrainingTask(pool, d, observedAt);
        if (r.ok) counts.training_task += 1;
      } else {
        counts.skipped += 1;
        skipReasons[`unknown_kind:${d.kind}`] = (skipReasons[`unknown_kind:${d.kind}`] ?? 0) + 1;
        continue;
      }
      if (!r.ok) {
        counts.skipped += 1;
        skipReasons[r.reason] = (skipReasons[r.reason] ?? 0) + 1;
        console.warn(`[bq-bindings] skip ${d.kind} dataset=${d.dataset_id}: ${r.reason}`);
      } else if (DRY_RUN) {
        console.log(`[bq-bindings] dry-run ${d.kind} ${d.dataset_id} → ${d.target_vertex_label ?? d.training_task}`);
      }
    } catch (e) {
      counts.errors += 1;
      console.error(`[bq-bindings] ERROR ${d.kind} dataset=${d.dataset_id}: ${e.message}`);
    }
  }

  if (!DRY_RUN) {
    try { await pool.query("FLUSH"); } catch (e) { console.warn(`[bq-bindings] FLUSH failed: ${e.message}`); }
  }

  console.log(`[bq-bindings] applied produces_vertex=${counts.produces_vertex}`
    + ` training_task=${counts.training_task}`
    + ` skipped=${counts.skipped}`
    + ` errors=${counts.errors}`);
  if (counts.skipped > 0) {
    console.log(`[bq-bindings] skip_reasons=${JSON.stringify(skipReasons)}`);
  }

  await pool.end();
}

main().catch(async (e) => {
  console.error(`[bq-bindings] FATAL: ${e.stack ?? e.message ?? e}`);
  if (_pgPool) await _pgPool.end().catch(() => {});
  process.exit(1);
});

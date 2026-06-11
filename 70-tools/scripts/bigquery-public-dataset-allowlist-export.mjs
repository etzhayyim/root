#!/usr/bin/env node
/**
 * BigQuery public-dataset allowlist manifest export.
 *
 * Snapshot the current state of:
 *   - vertex_public_dataset_catalog WHERE review_status='approved'
 *   - edge_dataset_produces_vertex_type
 *   - edge_dataset_allowed_for_training_task
 *   - mv_training_source_eligibility (default-deny gate)
 *
 * into a single JSON manifest that downstream consumers (training corpus
 * builders, RW projection planners, dashboards) read instead of querying
 * RisingWave directly. The manifest is the canonical "who is approved
 * right now" surface.
 *
 * ADR-2605092700 §P1 acceptance criteria + ADR-2605101000 §D3 (decided-
 * binding gate). The manifest does NOT confer any access by itself; it is
 * a snapshot of decisions already recorded in RW. Treat it as a cache,
 * not a source of truth.
 *
 * Usage:
 *   node 70-tools/scripts/bigquery-public-dataset-allowlist-export.mjs \
 *     [--provider bigquery-public-data] \
 *     [--out /tmp/bq-allowlist/manifest.json] \
 *     [--minimal]      # omit per-table list and props
 */

import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

const KOTOBA_URL = process.env.KOTOBA_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";

const args = process.argv.slice(2);
const arg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1];
};
const flag = (k) => args.includes(`--${k}`);

const PROVIDER = arg("provider", "bigquery-public-data");
const OUT = arg("out", `/tmp/bq-allowlist/${PROVIDER}-${new Date().toISOString().slice(0, 10)}.json`);
const MINIMAL = flag("minimal");

let _pgPool = null;
async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2 });
  return _pgPool;
}

async function main() {
  const pool = await getRwPool();
  const generatedAt = new Date().toISOString();

  // Approved catalog rows (each is the "decision" snapshot)
  const catalogQ = `
    SELECT vertex_id, dataset_id, provider, bq_project, bq_dataset, description,
           homepage_url, marketplace_url, license, terms_url,
           pii_tier_guess, allowed_for_train_guess, allowed_for_embedding_guess,
           recommended_ingest_mode, candidate_vertex_targets_json,
           candidate_edge_targets_json, review_status, review_note,
           table_count, total_size_bytes_estimate, observed_at, props
    FROM vertex_public_dataset_catalog
    WHERE provider = $1 AND review_status = 'approved'
    ORDER BY bq_dataset
  `;
  const { rows: catalogRows } = await pool.query(catalogQ, [PROVIDER]);

  // Per-table detail (optional)
  let tablesByDataset = new Map();
  if (!MINIMAL) {
    const tableQ = `
      SELECT t.dataset_id, t.bq_table, t.bq_project, t.bq_dataset,
             t.row_count_estimate, t.size_bytes_estimate, t.last_modified_at,
             t.partitioning_json, t.clustering_json,
             t.estimated_full_scan_cost_usd
      FROM vertex_public_dataset_table t
      JOIN vertex_public_dataset_catalog c
        ON c.dataset_id = t.dataset_id
      WHERE c.provider = $1 AND c.review_status = 'approved'
      ORDER BY t.dataset_id, t.bq_table
    `;
    const { rows: tableRows } = await pool.query(tableQ, [PROVIDER]);
    for (const r of tableRows) {
      const list = tablesByDataset.get(r.dataset_id) ?? [];
      list.push({
        bq_table: r.bq_table,
        row_count_estimate: r.row_count_estimate,
        size_bytes_estimate: r.size_bytes_estimate,
        last_modified_at: r.last_modified_at,
        partitioning_json: r.partitioning_json ? safeParseJson(r.partitioning_json) : null,
        clustering_json: r.clustering_json ? safeParseJson(r.clustering_json) : null,
        estimated_full_scan_cost_usd: r.estimated_full_scan_cost_usd,
      });
      tablesByDataset.set(r.dataset_id, list);
    }
  }

  // Decided bindings
  const producesQ = `
    SELECT src_vid, dst_vid, dataset_id, target_vertex_label, ingest_mode,
           approved_by, approved_at, scan_budget_tib, observed_at
    FROM edge_dataset_produces_vertex_type
    ORDER BY dataset_id, target_vertex_label
  `;
  const { rows: producesRows } = await pool.query(producesQ);

  const trainingQ = `
    SELECT src_vid, dst_vid, dataset_id, training_task, license,
           approved_by, approved_at, observed_at
    FROM edge_dataset_allowed_for_training_task
    ORDER BY dataset_id, training_task
  `;
  const { rows: trainingRows } = await pool.query(trainingQ);

  const eligibilityQ = `
    SELECT dataset_id, training_task, license, dataset_review_status,
           dataset_ingest_mode, observed_at
    FROM mv_training_source_eligibility
    ORDER BY dataset_id, training_task
  `;
  const { rows: eligibilityRows } = await pool.query(eligibilityQ);

  // Decision graph normalized onto each catalog entry
  const datasets = catalogRows.map((c) => {
    const datasetId = c.dataset_id;
    const produces = producesRows.filter((p) => p.dataset_id === datasetId);
    const trainingTasks = trainingRows.filter((t) => t.dataset_id === datasetId);
    const eligibilities = eligibilityRows.filter((e) => e.dataset_id === datasetId);
    return {
      dataset_id: datasetId,
      provider: c.provider,
      bq_project: c.bq_project,
      bq_dataset: c.bq_dataset,
      description: c.description,
      homepage_url: c.homepage_url,
      marketplace_url: c.marketplace_url,
      license: c.license,
      terms_url: c.terms_url,
      pii_tier_guess: c.pii_tier_guess,
      allowed_for_train_guess: c.allowed_for_train_guess,
      allowed_for_embedding_guess: c.allowed_for_embedding_guess,
      recommended_ingest_mode: c.recommended_ingest_mode,
      review_status: c.review_status,
      review_note: c.review_note,
      table_count: c.table_count,
      total_size_bytes_estimate: c.total_size_bytes_estimate,
      observed_at: c.observed_at,
      props: c.props ? safeParseJson(c.props) : null,
      tables: MINIMAL ? null : (tablesByDataset.get(datasetId) ?? []),
      // P2 binding (one row per (dataset, target_vertex_label))
      produces_vertex_type: produces.map((p) => ({
        target_vertex_label: p.target_vertex_label,
        ingest_mode: p.ingest_mode,
        approved_by: p.approved_by,
        approved_at: p.approved_at,
        scan_budget_tib: p.scan_budget_tib,
        observed_at: p.observed_at,
      })),
      // Training-task allowlist (default-deny: empty array = no training allowed)
      allowed_for_training_task: trainingTasks.map((t) => ({
        training_task: t.training_task,
        license: t.license,
        approved_by: t.approved_by,
        approved_at: t.approved_at,
        observed_at: t.observed_at,
      })),
      // Convenience: filter `mv_training_source_eligibility` to this dataset
      eligibility_view: eligibilities.map((e) => ({
        training_task: e.training_task,
        license: e.license,
        dataset_review_status: e.dataset_review_status,
        dataset_ingest_mode: e.dataset_ingest_mode,
        observed_at: e.observed_at,
      })),
    };
  });

  const stats = {
    catalog_approved: datasets.length,
    by_recommended_ingest_mode: groupCount(datasets, "recommended_ingest_mode"),
    by_license: groupCount(datasets, "license"),
    bindings_total: producesRows.length,
    training_allowlist_total: trainingRows.length,
    eligibility_view_total: eligibilityRows.length,
  };

  const manifest = {
    schema: "com.etzhayyim.bigquery.public_dataset_allowlist.v1",
    generated_at: generatedAt,
    provider: PROVIDER,
    notes: [
      "This manifest is a CACHE of decisions already recorded in RisingWave",
      "(vertex_public_dataset_catalog, edge_dataset_produces_vertex_type,",
      "edge_dataset_allowed_for_training_task, mv_training_source_eligibility).",
      "Default-deny: a dataset is allowed for a training task only when",
      "`allowed_for_training_task` array contains a matching row.",
      "Run via: node 70-tools/scripts/bigquery-public-dataset-allowlist-export.mjs",
    ],
    stats,
    datasets,
  };

  await mkdir(dirname(OUT), { recursive: true });
  await writeFile(OUT, JSON.stringify(manifest, null, 2), "utf8");
  console.log(`[bq-allowlist] wrote ${OUT}`);
  console.log(`[bq-allowlist] approved=${stats.catalog_approved}`
    + ` produces_bindings=${stats.bindings_total}`
    + ` training_allowlist=${stats.training_allowlist_total}`
    + ` eligibility_view=${stats.eligibility_view_total}`);
  console.log(`[bq-allowlist] by_ingest_mode=${JSON.stringify(stats.by_recommended_ingest_mode)}`);
  console.log(`[bq-allowlist] by_license=${JSON.stringify(stats.by_license)}`);

  await pool.end();
}

function safeParseJson(s) {
  try { return JSON.parse(String(s)); } catch { return s; }
}

function groupCount(rows, key) {
  const out = {};
  for (const r of rows) {
    const v = r[key] ?? "(null)";
    out[v] = (out[v] ?? 0) + 1;
  }
  return out;
}

main().catch(async (e) => {
  console.error(`[bq-allowlist] FATAL: ${e.stack ?? e.message ?? e}`);
  if (_pgPool) await _pgPool.end().catch(() => {});
  process.exit(1);
});

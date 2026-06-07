#!/usr/bin/env node
/**
 * BigQuery public dataset license enricher.
 *
 * ADR 2605092700 §P0 Catalog (license/terms metadata).
 *
 * `datasets.get` REST returns no `labels.license` for the
 * `bigquery-public-data` project; the field is structurally absent. This
 * script applies the curated SSoT at
 * `00-contracts/catalogs/bigquery/public-dataset-licenses.json` to every
 * row in `vertex_public_dataset_catalog` and re-INSERTs it with
 * `license`, `terms_url`, `allowed_for_train_guess`,
 * `allowed_for_embedding_guess`, `recommended_ingest_mode`, and
 * `props` (rationale + matched-pattern + category).
 *
 * Persistence: record-log semantics. Same `vertex_id` re-INSERT = upsert
 * per CLAUDE.md "Record-log semantics".
 *
 * Important: `allowed_for_train_guess` is a HEURISTIC. The actual
 * training authorization edge (`edge_dataset_allowed_for_training_task`)
 * remains default-deny per ADR §P1; the guess only informs review.
 *
 * Usage:
 *   node 70-tools/scripts/bigquery-public-dataset-license-enrich.mjs \
 *     --provider bigquery-public-data \
 *     [--datasets ds1,ds2]    # restrict to these datasets
 *     [--dry-run]
 */

import { readFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";
const SSOT_PATH = "/Users/junkawasaki/github/etzhayyim-root/00-contracts/catalogs/bigquery/public-dataset-licenses.json";

// ── CLI args ────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
const arg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1];
};
const flag = (k) => args.includes(`--${k}`);

const PROVIDER = arg("provider", "bigquery-public-data");
const DATASET_FILTER = (arg("datasets", "") ?? "")
  .split(",").map((s) => s.trim()).filter(Boolean);
const DRY_RUN = flag("dry-run");

// ── RisingWave ─────────────────────────────────────────────────────────────

let _pgPool = null;
async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import(
    "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
  );
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2 });
  return _pgPool;
}

// ── Pattern matcher ────────────────────────────────────────────────────────

function buildMatcher(providerSpec) {
  const patterns = (providerSpec.patterns ?? []).map((p) => ({
    re: new RegExp(p.match),
    spec: p,
  }));
  const exact = providerSpec.datasets ?? {};
  const fallback = providerSpec.default;

  return function matchDataset(bqDataset) {
    if (Object.prototype.hasOwnProperty.call(exact, bqDataset)) {
      return { kind: "exact", spec: exact[bqDataset], match: bqDataset };
    }
    for (const { re, spec } of patterns) {
      if (re.test(bqDataset)) return { kind: "pattern", spec, match: spec.match };
    }
    return { kind: "default", spec: fallback, match: null };
  };
}

// ── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const ssot = JSON.parse(await readFile(SSOT_PATH, "utf8"));
  const providerSpec = ssot.providers?.[PROVIDER];
  if (!providerSpec) {
    console.error(`[bq-enrich] ERROR: provider '${PROVIDER}' not in SSoT (${SSOT_PATH}).`);
    process.exit(1);
  }
  const matcher = buildMatcher(providerSpec);

  const pool = await getRwPool();
  const where = ["c.provider = $1"];
  const params = [PROVIDER];
  if (DATASET_FILTER.length > 0) {
    const placeholders = DATASET_FILTER.map((_, i) => `$${params.length + i + 1}`).join(",");
    where.push(`c.bq_dataset IN (${placeholders})`);
    params.push(...DATASET_FILTER);
  }
  const sql = `
    SELECT vertex_id, dataset_id, provider, bq_project, bq_dataset,
           description, license, terms_url, recommended_ingest_mode,
           total_size_bytes_estimate, table_count, observed_at
    FROM vertex_public_dataset_catalog c
    WHERE ${where.join(" AND ")}
    ORDER BY bq_dataset
  `;
  const { rows } = await pool.query(sql, params);
  console.log(`[bq-enrich] provider=${PROVIDER} candidates=${rows.length} dry_run=${DRY_RUN}`);

  const counts = { exact: 0, pattern: 0, default: 0 };
  const byCategory = {};
  for (const r of rows) {
    const m = matcher(r.bq_dataset);
    counts[m.kind] += 1;
    const cat = m.spec?.category ?? "unknown";
    byCategory[cat] = (byCategory[cat] ?? 0) + 1;

    const observedAt = new Date().toISOString();
    const sizeBytes = Number(r.total_size_bytes_estimate ?? 0);
    let recommendedIngestMode = r.recommended_ingest_mode ?? "catalog_only";
    if (m.spec?.license_decision === "review") {
      recommendedIngestMode = "catalog_only";
    } else if (m.spec?.license && m.spec?.license !== null) {
      // size-aware default; review still required to advance review_status.
      if (sizeBytes > 100 * 1024 ** 3) recommendedIngestMode = "bigquery_stage";
      else if (sizeBytes > 1024 ** 3) recommendedIngestMode = "hybrid";
      else recommendedIngestMode = "self_ingest";
    }

    const props = JSON.stringify({
      enrichment: {
        source: "ssot.public-dataset-licenses.json",
        version: ssot.version,
        match_kind: m.kind,
        match: m.match,
        category: cat,
        rationale: m.spec?.rationale ?? null,
      },
    });

    if (DRY_RUN) continue;
    await pool.query(
      `INSERT INTO vertex_public_dataset_catalog (
         vertex_id, sensitivity_ord, owner_did,
         dataset_id, provider, bq_project, bq_dataset, description,
         homepage_url, marketplace_url, license, terms_url,
         pii_tier_guess, allowed_for_train_guess, allowed_for_embedding_guess,
         recommended_ingest_mode, candidate_vertex_targets_json, candidate_edge_targets_json,
         review_status, review_note, observed_at, props,
         actor_did, org_did, created_at,
         table_count, total_size_bytes_estimate
       ) VALUES (
         $1, 1, $2,
         $3, $4, $5, $6, $7,
         NULL, NULL, $8, $9,
         1, $10, $11,
         $12, NULL, NULL,
         'pending', $13, $14, $15,
         $16, $17, $18,
         $19, $20
       )`,
      [
        r.vertex_id,
        "did:web:bigquery.etzhayyim.com",
        r.dataset_id, r.provider, r.bq_project, r.bq_dataset, r.description,
        m.spec?.license ?? null, m.spec?.terms_url ?? null,
        m.spec?.allowed_for_train_guess ?? "false",
        m.spec?.allowed_for_embedding_guess ?? "false",
        recommendedIngestMode,
        m.spec?.rationale ?? null,
        observedAt, props,
        "did:web:bigquery.etzhayyim.com", "did:web:bigquery.etzhayyim.com", observedAt,
        r.table_count, r.total_size_bytes_estimate,
      ],
    );
  }

  if (!DRY_RUN) {
    try { await pool.query("FLUSH"); } catch (e) { console.warn(`[bq-enrich] FLUSH failed: ${e.message}`); }
  }

  console.log("[bq-enrich] === COMPLETE ===");
  console.log(`[bq-enrich] matched_exact=${counts.exact} matched_pattern=${counts.pattern} default_review=${counts.default}`);
  console.log(`[bq-enrich] by_category=${JSON.stringify(byCategory, null, 2)}`);

  await pool.end();
}

main().catch(async (e) => {
  console.error(`[bq-enrich] FATAL: ${e.stack ?? e.message ?? e}`);
  if (_pgPool) await _pgPool.end().catch(() => {});
  process.exit(1);
});

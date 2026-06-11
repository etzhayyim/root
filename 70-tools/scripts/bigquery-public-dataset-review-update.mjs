#!/usr/bin/env node
/**
 * Apply human-review decisions to vertex_public_dataset_catalog.
 *
 * ADR 2605092700 §P1 acceptance criteria step "every selected P0
 * candidate has a profile row" depends on someone flipping
 * `review_status` from `pending` to `approved` (or `rejected`) for the
 * datasets that should advance to P1. This script reads decisions from
 * a JSON or CSV file and re-INSERTs the matching catalog rows so
 * record-log semantics treat the new row as the latest decision.
 *
 * Decision file formats:
 *
 *   JSON: [
 *     { "dataset_id": "bigquery-public-data:github_repos",
 *       "review_status": "approved",
 *       "review_note": "MIT/Apache aggregate; per-row license filter required",
 *       "license": "Per-Repo-OSS",                // optional override
 *       "terms_url": "...",                       // optional override
 *       "allowed_for_train_guess": "false",       // optional override
 *       "recommended_ingest_mode": "bigquery_stage" // optional override
 *     }, ...
 *   ]
 *
 *   CSV (header required):
 *     dataset_id,review_status,review_note[,license,terms_url,allowed_for_train_guess,recommended_ingest_mode]
 *
 * Usage:
 *   node 70-tools/scripts/bigquery-public-dataset-review-update.mjs \
 *     --decisions /path/to/decisions.json \
 *     [--dry-run]
 */

import { readFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";
const COLLECTOR_DID = "did:web:bigquery.etzhayyim.com";
const VALID_STATUS = new Set(["pending", "approved", "rejected", "deferred"]);

const args = process.argv.slice(2);
const arg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1];
};
const flag = (k) => args.includes(`--${k}`);

const DECISIONS = arg("decisions");
const DRY_RUN = flag("dry-run");

if (!DECISIONS) {
  console.error("[bq-review] ERROR: --decisions <file.json|file.csv> required.");
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

function parseCSV(text) {
  // Minimal RFC4180-ish parser; quoted fields may contain commas.
  const lines = text.replace(/\r\n/g, "\n").split("\n").filter((l) => l.length > 0);
  if (lines.length === 0) return [];
  const splitLine = (line) => {
    const out = [];
    let i = 0;
    while (i < line.length) {
      if (line[i] === '"') {
        let j = i + 1;
        let v = "";
        while (j < line.length) {
          if (line[j] === '"' && line[j + 1] === '"') { v += '"'; j += 2; }
          else if (line[j] === '"') { j++; break; }
          else { v += line[j++]; }
        }
        out.push(v);
        if (line[j] === ",") j++;
        i = j;
      } else {
        const k = line.indexOf(",", i);
        if (k === -1) { out.push(line.slice(i)); break; }
        out.push(line.slice(i, k)); i = k + 1;
      }
    }
    return out;
  };
  const header = splitLine(lines[0]).map((c) => c.trim());
  const rows = [];
  for (let r = 1; r < lines.length; r++) {
    const cols = splitLine(lines[r]);
    const obj = {};
    for (let c = 0; c < header.length; c++) obj[header[c]] = cols[c] ?? "";
    rows.push(obj);
  }
  return rows;
}

async function main() {
  const text = await readFile(DECISIONS, "utf8");
  const decisions = DECISIONS.endsWith(".csv") ? parseCSV(text) : JSON.parse(text);
  if (!Array.isArray(decisions)) {
    throw new Error(`Decisions file must be an array (got ${typeof decisions}).`);
  }

  const pool = await getRwPool();
  let applied = 0, skipped = 0;
  for (const d of decisions) {
    const datasetId = d.dataset_id?.trim();
    const status = (d.review_status ?? "").trim();
    if (!datasetId) { skipped += 1; continue; }
    if (!VALID_STATUS.has(status)) {
      console.warn(`[bq-review] skip ${datasetId}: invalid review_status='${status}'`);
      skipped += 1; continue;
    }

    // Read current row — required to preserve untouched fields.
    const { rows } = await pool.query(
      `SELECT vertex_id, dataset_id, provider, bq_project, bq_dataset, description,
              homepage_url, marketplace_url, license, terms_url, last_modified_at,
              table_count, total_size_bytes_estimate,
              pii_tier_guess, allowed_for_train_guess, allowed_for_embedding_guess,
              recommended_ingest_mode, candidate_vertex_targets_json,
              candidate_edge_targets_json, props
         FROM vertex_public_dataset_catalog WHERE dataset_id = $1`,
      [datasetId],
    );
    if (rows.length === 0) {
      console.warn(`[bq-review] skip ${datasetId}: not in catalog`);
      skipped += 1; continue;
    }
    const r = rows[0];
    const observedAt = new Date().toISOString();
    const license = d.license ?? r.license;
    const termsUrl = d.terms_url ?? r.terms_url;
    const allowedTrain = d.allowed_for_train_guess ?? r.allowed_for_train_guess;
    const recommendedMode = d.recommended_ingest_mode ?? r.recommended_ingest_mode;
    const reviewNote = d.review_note ?? null;

    if (DRY_RUN) {
      console.log(`[bq-review] dry-run ${datasetId} → review_status=${status}`
        + (reviewNote ? ` (note=${reviewNote.slice(0, 60)})` : ""));
      applied += 1;
      continue;
    }

    await pool.query(
      `INSERT INTO vertex_public_dataset_catalog (
         vertex_id, sensitivity_ord, owner_did,
         dataset_id, provider, bq_project, bq_dataset, description,
         homepage_url, marketplace_url, license, terms_url, last_modified_at,
         table_count, total_size_bytes_estimate,
         pii_tier_guess, allowed_for_train_guess, allowed_for_embedding_guess,
         recommended_ingest_mode, candidate_vertex_targets_json, candidate_edge_targets_json,
         review_status, review_note, observed_at, props,
         actor_did, org_did, created_at
       ) VALUES (
         $1, 1, $2,
         $3, $4, $5, $6, $7,
         $8, $9, $10, $11, $12,
         $13, $14,
         $15, $16, $17,
         $18, $19, $20,
         $21, $22, $23, $24,
         $25, $26, $27
       )`,
      [
        r.vertex_id, COLLECTOR_DID,
        r.dataset_id, r.provider, r.bq_project, r.bq_dataset, r.description,
        r.homepage_url, r.marketplace_url, license, termsUrl, r.last_modified_at,
        r.table_count, r.total_size_bytes_estimate,
        r.pii_tier_guess, allowedTrain, r.allowed_for_embedding_guess,
        recommendedMode, r.candidate_vertex_targets_json, r.candidate_edge_targets_json,
        status, reviewNote, observedAt, r.props,
        process.env.USER ?? COLLECTOR_DID, COLLECTOR_DID, observedAt,
      ],
    );
    applied += 1;
  }

  if (!DRY_RUN) {
    try { await pool.query("FLUSH"); } catch (e) { console.warn(`[bq-review] FLUSH failed: ${e.message}`); }
  }

  console.log(`[bq-review] applied=${applied} skipped=${skipped}`);
  await pool.end();
}

main().catch(async (e) => {
  console.error(`[bq-review] FATAL: ${e.stack ?? e.message ?? e}`);
  if (_pgPool) await _pgPool.end().catch(() => {});
  process.exit(1);
});
